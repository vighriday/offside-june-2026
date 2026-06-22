"""Export the IncidentBundle contract to TypeScript — one source of truth, no drift.

The Pydantic models in :mod:`offside_engine.analyze.split_schema` define the JSON the
engine freezes and the web reads. Rather than hand-maintain a parallel TypeScript copy
(which would silently drift), this module derives the TS types from the same enums and
models, so a change to the contract is a one-line regeneration away from the web types.

Run ``python -m offside_engine.export_types <out.ts>`` (the Colab notebook and a future
CI step call it) to write ``web/types/contract.ts``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import get_args

from offside_engine.analyze.split_schema import (
    CellState,
    GuardianVerdict,
    LensKind,
    LensStance,
    LensState,
    ResolutionStatus,
    SplitAxis,
)

_HEADER = """\
// AUTO-GENERATED from offside_engine/analyze/split_schema.py — do not edit by hand.
// Regenerate with: python -m offside_engine.export_types web/types/contract.ts
//
// This is the single contract between the engine and the web. The Granite-facing
// shapes carry NO numeric field by construction; numbers live only on code-owned
// types (Citation.page, Bbox) populated after Granite runs.
"""


def _union(name: str, literal_type: object) -> str:
    """Render a Python Literal[...] as a TS string-literal union."""
    members = " | ".join(f'"{v}"' for v in get_args(literal_type))
    return f"export type {name} = {members};"


def build_ts() -> str:
    """Build the full TypeScript contract source."""
    enums = [
        _union("CellState", CellState),
        _union("SplitAxis", SplitAxis),
        _union("ResolutionStatus", ResolutionStatus),
        _union("LensKind", LensKind),
        _union("LensStance", LensStance),
        _union("LensState", LensState),
        _union("GuardianVerdict", GuardianVerdict),
    ]

    interfaces = """\
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

export interface IncidentBundle {
  incident_id: string;
  title: string;
  settled_fact: SettledFact;
  lenses: SealedLens[];
  split: Split;
  cell_seals: SealedCell[];
  citations: Record<string, Citation>;
  provenance: BakeProvenance;
}

// The four axes in the canonical order the SPLIT always renders them.
export const CANONICAL_AXIS_ORDER: SplitAxis[] = [
  "RULE_AMBIGUITY",
  "INDETERMINACY",
  "DECISION_TIME_DEFICIT",
  "CULTURAL_PRIOR_BIAS",
];
"""

    return _HEADER + "\n" + "\n".join(enums) + "\n\n" + interfaces


def write_ts(out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_ts(), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/types/contract.ts")
    written = write_ts(target)
    print(f"wrote {written}")
