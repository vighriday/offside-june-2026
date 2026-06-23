"use client";

import type { IncidentBundle, SplitAxis } from "@/types/contract";

const AXIS_SHORT: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Rule",
  INDETERMINACY: "Indeterminacy",
  DECISION_TIME_DEFICIT: "Decision-time",
  CULTURAL_PRIOR_BIAS: "Cultural bias",
};

// The incidents drawn from the CURRENT Laws and season — the ones that make OFFSIDE a
// rule-maker's instrument rather than a quiz about famous goals. Marked live in the chain.
const CURRENT_INCIDENTS = new Set([
  "handball-rewrite",
  "offside-margin",
  "pgmol-subjective",
]);

// The dominant axes of an incident = the cells that are PRESENT/WEAK (the live tensions).
function dominantAxes(bundle: IncidentBundle): SplitAxis[] {
  return bundle.split.cells
    .filter((c) => c.state === "PRESENT" || c.state === "WEAK")
    .map((c) => c.axis);
}

interface DivergenceLineageProps {
  incidents: IncidentBundle[];
  activeId: string;
  onSelect: (index: number) => void;
}

// Divergence Lineage — the curated chain Hand of God → Suárez → Lampard, grouped not by
// embeddings but by their SHARED dominant divergence axis (reusing THE SPLIT's own output).
// Each adjacent pair shares exactly one axis, which is the answer to "why grouped?":
// HoG & Suárez both turn on Cultural bias; HoG & Lampard both on the Decision-time moment.
export function DivergenceLineage({ incidents, activeId, onSelect }: DivergenceLineageProps) {
  if (incidents.length < 2) return null;

  return (
    <section className="lineage" aria-label="Choose an incident">
      <p className="lineage__eyebrow">
        ▸ Pick an incident — watch the diagnosis change (same engine, different answer).
        The <span className="lineage__live-key">live</span> ones are unsettled right now.
      </p>
      <ol className="lineage__chain">
        {incidents.map((b, i) => {
          const axes = dominantAxes(b);
          // the axis this incident shares with the previous one in the chain
          const shared =
            i > 0
              ? dominantAxes(incidents[i - 1]).filter((a) => axes.includes(a))
              : [];
          return (
            <li key={b.incident_id} className="lineage__node-wrap">
              {i > 0 && (
                <span className="lineage__link" aria-hidden>
                  <span className="lineage__link-line" />
                  <span className="lineage__link-axis">
                    {shared.length ? `shares ${AXIS_SHORT[shared[0]]}` : "—"}
                  </span>
                </span>
              )}
              <button
                type="button"
                className="lineage__node"
                data-active={b.incident_id === activeId}
                data-current={CURRENT_INCIDENTS.has(b.incident_id)}
                aria-pressed={b.incident_id === activeId}
                onClick={() => onSelect(i)}
              >
                <span className="lineage__node-title">
                  {b.title}
                  {CURRENT_INCIDENTS.has(b.incident_id) && (
                    <span className="lineage__live" title="A current, unsettled dispute">
                      live
                    </span>
                  )}
                </span>
                <span className="lineage__node-axes">
                  {axes.map((a) => (
                    <span key={a} className="lineage__tag">
                      {AXIS_SHORT[a]}
                    </span>
                  ))}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
