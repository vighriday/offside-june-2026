// AUTO-GENERATED from offside_engine/analyze/split_schema.py — do not edit by hand.
// Regenerate with: python -m offside_engine.export_types web/types/contract.ts
//
// This is the single contract between the engine and the web. The Granite-facing
// shapes carry NO numeric field by construction; numbers live only on code-owned
// types (Citation.page, Bbox) populated after Granite runs.

export type CellState = "PRESENT" | "WEAK" | "ABSENT" | "NOT_DOCUMENTED";
export type SplitAxis = "RULE_AMBIGUITY" | "INDETERMINACY" | "DECISION_TIME_DEFICIT" | "CULTURAL_PRIOR_BIAS";
export type ResolutionStatus = "SETTLED_FACT" | "ADJUDICATED_CONTESTED" | "UNRESOLVABLE";
export type LensKind = "REFEREE" | "TACTICAL" | "HISTORICAL" | "FRAMING";
export type LensStance = "SUPPORTS" | "DISPUTES" | "MIXED" | "INSUFFICIENT_EVIDENCE";
export type LensState = "GROUNDED" | "INSUFFICIENT_EVIDENCE";
export type GuardianVerdict = "GROUNDED" | "UNGROUNDED";
export type ProbeKind = "FLIP" | "NOISE" | "OVERREACH";

export interface Bbox {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface Citation {
  id: string;
  source_doc: string;
  doc_kind: string;
  page: number | null;
  bbox: Bbox | null;
  extracted_text: string;
  attribution: string | null;
}

export interface TrustSeal {
  verdict: GuardianVerdict;
  guardian_model: string;
  checked_context_citation_ids: string[];
}

export interface LensOutput {
  lens: LensKind;
  stance: LensStance;
  state: LensState;
  citation_ids: string[];
  rationale: string;
}

export interface SplitCell {
  axis: SplitAxis;
  state: CellState;
  citation_ids: string[];
  rationale: string;
}

export interface Split {
  cells: SplitCell[];
  headline: string;
}

export interface SettledFact {
  status: ResolutionStatus;
  statement: string;
  citation_ids: string[];
}

export interface SealedLens {
  output: LensOutput;
  seal: TrustSeal;
}

export interface SealedCell {
  cell: SplitCell;
  seal: TrustSeal;
}

export interface BakeProvenance {
  granite_model: string;
  guardian_model: string;
  embed_model: string;
  options: Record<string, number>;
  corpus_git_sha: string | null;
}

export interface RuleEvolution {
  axis: SplitAxis;
  from_era: string;
  to_era: string;
  from_state: CellState;
  to_state: CellState;
  note: string;
}

export interface Probe {
  kind: ProbeKind;
  axis: SplitAxis;
  label: string;
  plain_question: string;
  injected_text: string;
  state_before: CellState;
  state_after: CellState;
  guardian_verdict: GuardianVerdict;
  guardian_model: string;
  outcome: string;
}

export interface IncidentBundle {
  incident_id: string;
  title: string;
  settled_fact: SettledFact;
  lenses: SealedLens[];
  split: Split;
  cell_seals: SealedCell[];
  citations: Record<string, Citation>;
  provenance: BakeProvenance;
  rule_evolution: RuleEvolution | null;
  probes: Probe[];
}

// The four axes in the canonical order the SPLIT always renders them.
export const CANONICAL_AXIS_ORDER: SplitAxis[] = [
  "RULE_AMBIGUITY",
  "INDETERMINACY",
  "DECISION_TIME_DEFICIT",
  "CULTURAL_PRIOR_BIAS",
];
