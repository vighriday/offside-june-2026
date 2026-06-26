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

export function LiveSplit({ events, bundle }: {
  events: StudioStreamEvent[];
  bundle: IncidentBundle | null;
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

  // Live: the four boxes fill in one at a time as cell events arrive.
  return (
    <div className="live-split" aria-live="polite">
      {AXES.map((axis) => (
        <div key={axis} className="live-split__cell" data-state={filled[axis] ?? "pending"}>
          <p className="live-split__q">{AXIS_LABEL[axis]}</p>
          <p className="live-split__state">{filled[axis] ?? "…computing"}</p>
        </div>
      ))}
    </div>
  );
}
