"use client";

import { useState } from "react";
import type { IncidentBundle } from "@/types/contract";
import { SettledFact } from "./SettledFact";
import { SplitView } from "./SplitView";
import { LensPanels } from "./LensPanels";
import { ProvenanceFooter } from "./ProvenanceFooter";

export interface LoadedBundle {
  bundle: IncidentBundle;
  isSample: boolean;
}

interface IncidentExplorerProps {
  incidents: LoadedBundle[];
}

// Lets a judge switch between incidents and SEE the diagnostic change. The contrast is
// the proof OFFSIDE is derived, not hard-coded: the same engine gives the Hand of God a
// cultural-bias cell that is PRESENT, and Lampard's ghost goal one that is ruled out.
export function IncidentExplorer({ incidents }: IncidentExplorerProps) {
  const [active, setActive] = useState(0);
  const current = incidents[active];
  const { bundle, isSample } = current;

  return (
    <main className="incident">
      {isSample && (
        <p className="incident__sample-banner">
          Pre-bake sample fixture — the audited bundle replaces this once the bake runs.
        </p>
      )}

      <div className="incident__inner">
        {incidents.length > 1 && (
          <nav className="incident-switch" aria-label="Choose an incident">
            {incidents.map((it, i) => (
              <button
                key={it.bundle.incident_id}
                type="button"
                className="incident-switch__tab"
                data-active={i === active}
                aria-pressed={i === active}
                onClick={() => setActive(i)}
              >
                {it.bundle.title}
              </button>
            ))}
          </nav>
        )}

        {/* Re-key on incident id so the inner staged reveals replay on switch. The
            wrapper itself does not fade (its children stage their own entrances), so the
            first paint is never doubly dimmed. */}
        <div key={bundle.incident_id}>
          <SettledFact fact={bundle.settled_fact} title={bundle.title} />
          <SplitView bundle={bundle} />
          <LensPanels lenses={bundle.lenses} citations={bundle.citations} />
          <ProvenanceFooter
            provenance={bundle.provenance}
            citations={bundle.citations}
          />
        </div>
      </div>
    </main>
  );
}
