"use client";

import { useState } from "react";
import { motion } from "motion/react";
import type { RuleEvolution as RuleEvolutionData, SplitAxis } from "@/types/contract";

const AXIS_LABEL: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Rule ambiguity",
  INDETERMINACY: "Indeterminacy",
  DECISION_TIME_DEFICIT: "Decision-time deficit",
  CULTURAL_PRIOR_BIAS: "Cultural prior bias",
};

const STATE_LABEL: Record<string, string> = {
  PRESENT: "Present",
  WEAK: "Weak",
  ABSENT: "Resolved",
  NOT_DOCUMENTED: "Not documented",
};

// Rule Evolution — the verdict-free temporal counterfactual. For Lampard, toggling the era
// flips the Decision-Time-Deficit cell from PRESENT (2010, no goal-line tech) to RESOLVED
// (2026, automatic detection). It never claims the *call* would change — only that what was
// undetectable in the moment is automatic now. The fact was always settled.
export function RuleEvolution({ evo }: { evo: RuleEvolutionData }) {
  const [future, setFuture] = useState(false);
  const era = future ? evo.to_era : evo.from_era;
  const state = future ? evo.to_state : evo.from_state;

  return (
    <section className="rule-evo" aria-label="Rule evolution">
      <div className="rule-evo__head">
        <p className="rule-evo__eyebrow">▸ Rule evolution — what changed with the technology</p>
        <div className="rule-evo__toggle" role="group" aria-label="Choose an era">
          <button
            type="button"
            data-active={!future}
            aria-pressed={!future}
            onClick={() => setFuture(false)}
          >
            {evo.from_era}
          </button>
          <button
            type="button"
            data-active={future}
            aria-pressed={future}
            onClick={() => setFuture(true)}
          >
            {evo.to_era}
          </button>
        </div>
      </div>

      <div className="rule-evo__body">
        <span className="rule-evo__axis">{AXIS_LABEL[evo.axis]}</span>
        <motion.span
          key={state}
          className="rule-evo__state"
          data-state={state}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.32, ease: [0.4, 0.14, 0.3, 1] }}
        >
          {STATE_LABEL[state] ?? state}
        </motion.span>
        <span className="rule-evo__era">{era}</span>
      </div>

      <p className="rule-evo__note">{evo.note}</p>
    </section>
  );
}
