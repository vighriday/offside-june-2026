"use client";

import type { CellState, SplitAxis, SplitCell as SplitCellData } from "@/types/contract";

// Human-facing axis labels and the one-line question each axis answers. The enum value
// is the contract; these are the presentation copy, kept in the component layer.
const AXIS_LABEL: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Rule ambiguity",
  INDETERMINACY: "Indeterminacy",
  DECISION_TIME_DEFICIT: "Decision-time deficit",
  CULTURAL_PRIOR_BIAS: "Cultural prior bias",
};

// The plain-English version of each axis — the human translation under the formal name,
// so the box is understood without a glossary.
const AXIS_PLAIN: Record<SplitAxis, string> = {
  RULE_AMBIGUITY: "Is the rulebook itself unclear?",
  INDETERMINACY: "Is the truth impossible to ever know?",
  DECISION_TIME_DEFICIT: "Could the ref see it in the moment — even if we can now?",
  CULTURAL_PRIOR_BIAS: "Same facts agreed, but each side wants its own outcome?",
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
    <button
      type="button"
      data-state={cell.state}
      data-selected={selected}
      onClick={() => onSelect(cell.axis)}
      // The cell is fully visible by default; `split-cell--enter` adds a one-shot CSS
      // fade/rise that can never leave the cell stuck dim (the prior Motion opacity-0
      // initial could, on a slow first paint). The per-cell delay staggers the entrance.
      className="split-cell split-cell--enter"
      style={{ animationDelay: `${0.08 * index}s` }}
      aria-pressed={selected}
      aria-label={`${AXIS_LABEL[cell.axis]}: ${face.tag}. ${face.meaning}.`}
    >
      <span className="split-cell__axis">{AXIS_LABEL[cell.axis]}</span>
      <span className="split-cell__question">{AXIS_PLAIN[cell.axis]}</span>

      <span className="split-cell__state" data-assertive={isAssertive}>
        {face.tag}
      </span>
      <span className="split-cell__meaning">{face.meaning}</span>

      {isAssertive && cell.citation_ids.length > 0 && (
        <span className="split-cell__trace">
          Click to see {cell.citation_ids.length}{" "}
          {cell.citation_ids.length === 1 ? "source" : "sources"} →
        </span>
      )}

      {/* A ruled-out / undocumented cell carries its earned rationale on its own face,
          so the empty cell reads as a finding rather than a blank. */}
      {!isAssertive && cell.rationale && (
        <span className="split-cell__earned">{cell.rationale}</span>
      )}
    </button>
  );
}
