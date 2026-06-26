"use client";

import type { CellState, IncidentBundle, SplitAxis, StudioStreamEvent } from "@/types/contract";
import { SplitView } from "../SplitView";
import { LensPanels } from "../LensPanels";
import { SettledFact } from "../SettledFact";
import { ProvenanceFooter } from "../ProvenanceFooter";

const AXES: SplitAxis[] = [
  "RULE_AMBIGUITY", "INDETERMINACY", "DECISION_TIME_DEFICIT", "CULTURAL_PRIOR_BIAS",
];
const AXIS_LABEL: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Is the rule unclear?",
  INDETERMINACY: "Is the truth unknowable?",
  DECISION_TIME_DEFICIT: "Could the ref see it in time?",
  CULTURAL_PRIOR_BIAS: "Do the sides just want their own way?",
};
const LENS_LABEL: Record<string, string> = {
  REFEREE: "Referee", TACTICAL: "Tactical", HISTORICAL: "Historical", FRAMING: "Framing",
};
const STATE_LABEL: Record<CellState, string> = {
  PRESENT: "Present", WEAK: "Weak", ABSENT: "Ruled out", NOT_DOCUMENTED: "Not documented",
};

// Turn the real SSE events into a human activity trail — exactly the steps the engine took,
// in order, so the user watches it think rather than staring at a spinner. Every line is a
// real event (Granite read a lens, Guardian returned a verdict), never a fake progress bar.
function activityLines(events: StudioStreamEvent[]): string[] {
  const lines: string[] = [];
  for (const e of events) {
    if (e.type === "lens") {
      lines.push(`Granite read the ${LENS_LABEL[e.lens] ?? e.lens} lens — ${e.stance.toLowerCase()}.`);
    } else if (e.type === "audit") {
      const ok = e.verdict === "GROUNDED";
      lines.push(`${LENS_LABEL[e.lens] ?? e.lens} — Granite Guardian: ${ok ? "grounded ✓" : "could not confirm — held back"}.`);
    } else if (e.type === "cell") {
      lines.push(`${AXIS_LABEL[e.axis]} → ${STATE_LABEL[e.state]}.`);
    }
  }
  return lines;
}

export function LiveSplit({ events, bundle, elapsedSeconds }: {
  events: StudioStreamEvent[];
  bundle: IncidentBundle | null;
  /** Seconds since the run started, shown while it is still computing. */
  elapsedSeconds?: number;
}) {
  const filled: Partial<Record<SplitAxis, CellState>> = {};
  for (const e of events) if (e.type === "cell") filled[e.axis] = e.state;

  if (bundle) {
    // Final result — reuse the exact Explore renderer so the user recognises it.
    return (
      <div>
        <SettledFact fact={bundle.settled_fact} title={bundle.title} incidentId={bundle.incident_id} />
        <SplitView bundle={bundle} />
        <LensPanels lenses={bundle.lenses} citations={bundle.citations} />
        <ProvenanceFooter provenance={bundle.provenance} citations={bundle.citations} />
      </div>
    );
  }

  const lines = activityLines(events);
  const mm = Math.floor((elapsedSeconds ?? 0) / 60);
  const ss = String((elapsedSeconds ?? 0) % 60).padStart(2, "0");

  // Live: the four boxes fill as cell events arrive, with a real activity trail + a timer
  // so the multi-minute run never looks hung.
  return (
    <div className="live-split" aria-live="polite">
      <div className="live-split__status">
        <span className="live-split__spinner" aria-hidden />
        <span>
          Decomposing with the real Granite models — this takes a few minutes.
          {elapsedSeconds !== undefined && <strong> elapsed {mm}:{ss}</strong>}
        </span>
      </div>

      <div className="live-split__grid">
        {AXES.map((axis) => (
          <div key={axis} className="live-split__cell" data-state={filled[axis] ?? "pending"}>
            <p className="live-split__q">{AXIS_LABEL[axis]}</p>
            <p className="live-split__state">
              {filled[axis] ? STATE_LABEL[filled[axis]!] : "…computing"}
            </p>
          </div>
        ))}
      </div>

      {lines.length > 0 && (
        <ol className="live-split__log">
          {lines.map((line, i) => (
            <li key={i} className="live-split__log-line">{line}</li>
          ))}
        </ol>
      )}
    </div>
  );
}
