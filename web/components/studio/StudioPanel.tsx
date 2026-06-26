"use client";

import { useEffect, useState } from "react";
import type { IncidentBundle, StudioStreamEvent } from "@/types/contract";
import { checkHealth, decomposeStream, loadExampleBundle, type StudioFormPayload } from "@/lib/studioClient";
import { StudioForm } from "./StudioForm";
import { LiveSplit } from "./LiveSplit";

export function StudioPanel() {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [events, setEvents] = useState<StudioStreamEvent[]>([]);
  const [bundle, setBundle] = useState<IncidentBundle | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => { checkHealth().then((h) => setHealthy(!!h?.ok)); }, []);

  // Tick an elapsed-seconds counter only while a live run is in flight, so the multi-minute
  // bake shows visible progress and never reads as hung.
  useEffect(() => {
    if (!running) return;
    const started = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, [running]);

  // When the backend is unreachable, "Load an example" loads the pre-baked fixture
  // and sets it as bundle directly so LiveSplit renders the complete real result.
  async function loadExample() {
    setEvents([]); setBundle(null); setError(null);
    try {
      const b = await loadExampleBundle();
      setBundle(b);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function run(payload: StudioFormPayload) {
    setEvents([]); setBundle(null); setError(null); setRunning(true);
    try {
      await decomposeStream(payload, (e) => {
        setEvents((prev) => [...prev, e]);
        if (e.type === "done") setBundle(e.bundle);
        if (e.type === "error") setError(e.message);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="studio" aria-label="Studio">
      <header className="studio__head">
        <h2>Decompose your own controversy</h2>
        <p>You bring the evidence — the facts and the named quotes. OFFSIDE retrieves the
        matching Law itself, has Granite read each lens, lets Granite Guardian audit each,
        and fills THE SPLIT live.</p>
      </header>

      {healthy === false && (
        <div className="studio__banner" role="note">
          Live decomposition runs the real Granite models on <strong>your machine</strong> —
          not on this $0 static host. Start it locally in one command (see the README
          &ldquo;Run the Studio yourself&rdquo;), then this form goes live. Meanwhile, &ldquo;Load an example&rdquo;
          shows a complete real result.
        </div>
      )}

      {healthy === true && !running && !bundle && (
        <p className="studio__notice" role="note">
          Heads up: a live decomposition runs the real Granite models four times over (one per
          lens), each audited by Granite Guardian — it <strong>takes a few minutes</strong>.
          You&rsquo;ll see each step appear as it happens.
        </p>
      )}

      <StudioForm
        disabled={running}
        liveEnabled={healthy === true}
        onRun={run}
        onExample={healthy !== true ? loadExample : undefined}
      />
      {error && <p className="studio__error">{error}</p>}
      {(events.length > 0 || bundle) && (
        <LiveSplit
          events={events}
          bundle={bundle}
          elapsedSeconds={running ? elapsed : undefined}
        />
      )}
    </section>
  );
}
