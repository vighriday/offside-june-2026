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

  useEffect(() => { checkHealth().then((h) => setHealthy(!!h?.ok)); }, []);

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

      <StudioForm
        disabled={running || healthy === false}
        onRun={run}
        onExample={healthy === false ? loadExample : undefined}
      />
      {error && <p className="studio__error">{error}</p>}
      {(events.length > 0 || bundle) && <LiveSplit events={events} bundle={bundle} />}
    </section>
  );
}
