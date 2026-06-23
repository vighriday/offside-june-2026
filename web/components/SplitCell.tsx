"use client";

import { motion } from "motion/react";
import type { CellState, SplitAxis, SplitCell as SplitCellData } from "@/types/contract";

// Human-facing axis labels and the one-line question each axis answers. The enum value
// is the contract; these are the presentation copy, kept in the component layer.
const AXIS_LABEL: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Rule ambiguity",
  INDETERMINACY: "Indeterminacy",
  DECISION_TIME_DEFICIT: "Decision-time deficit",
  CULTURAL_PRIOR_BIAS: "Cultural prior bias",
};

const AXIS_QUESTION: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Are the Laws themselves unclear or in conflict?",
  INDETERMINACY: "Does a fact stay contested even with all current technology?",
  DECISION_TIME_DEFICIT: "Knowable now, but not available at the moment of the call?",
  CULTURAL_PRIOR_BIAS: "Agreement on facts and rules, divergence on acceptable outcome?",
};

// What each state means on the cell face. ABSENT is a *positive* finding ("ruled out"),
// never an empty cell; NOT_DOCUMENTED is explicitly unknown, never silently absent.
const STATE_FACE: Record<CellState, { tag: string; meaning: string }> = {
  PRESENT: { tag: "Present", meaning: "This tension is live" },
  WEAK: { tag: "Weak", meaning: "A faint tension" },
  ABSENT: { tag: "Ruled out", meaning: "Not why it stays contested" },
  NOT_DOCUMENTED: { tag: "Not documented", meaning: "No evidence either way" },
};

interface SplitCellProps {
  cell: SplitCellData;
  /** Position in the staged reveal (0–3); drives the entrance delay. */
  index: number;
  selected: boolean;
  onSelect: (axis: SplitAxis) => void;
}

export function SplitCell({ cell, index, selected, onSelect }: SplitCellProps) {
  const face = STATE_FACE[cell.state];
  const isAssertive = cell.state === "PRESENT" || cell.state === "WEAK";

  return (
    <motion.button
      type="button"
      data-state={cell.state}
      data-selected={selected}
      onClick={() => onSelect(cell.axis)}
      className="split-cell"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      // Carbon "productive" entrance easing; cells resolve in quick sequence (~0.6s total
      // for four) so the diagnostic is readable fast, not a slow load.
      transition={{
        duration: 0.34,
        delay: 0.09 * index,
        ease: [0.4, 0.14, 0.3, 1],
      }}
      whileHover={{ y: -2 }}
      aria-pressed={selected}
      aria-label={`${AXIS_LABEL[cell.axis]}: ${face.tag}. ${face.meaning}.`}
    >
      <span className="split-cell__axis">{AXIS_LABEL[cell.axis]}</span>
      <span className="split-cell__question">{AXIS_QUESTION[cell.axis]}</span>

      <span className="split-cell__state" data-assertive={isAssertive}>
        {face.tag}
      </span>
      <span className="split-cell__meaning">{face.meaning}</span>

      {isAssertive && cell.citation_ids.length > 0 && (
        <span className="split-cell__trace">
          Traces to {cell.citation_ids.length}{" "}
          {cell.citation_ids.length === 1 ? "source" : "sources"} →
        </span>
      )}

      {/* A ruled-out / undocumented cell carries its earned rationale on its own face,
          so the empty cell reads as a finding rather than a blank. */}
      {!isAssertive && cell.rationale && (
        <span className="split-cell__earned">{cell.rationale}</span>
      )}
    </motion.button>
  );
}
