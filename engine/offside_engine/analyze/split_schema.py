"""THE SPLIT — the data contract shared between the engine and the web app.

This module is the single source of truth for the JSON that flows
``engine ──▶ fixtures/ ──▶ web``. It is exported to TypeScript for the web side.

The defining property of OFFSIDE
--------------------------------
The **Granite-facing** models (:class:`LensOutput`, :class:`SplitCell`, :class:`Split`)
contain **no numeric field, anywhere in their transitive schema**. They are built only
from string-literal enums, ``list[str]``, and ``str``. When passed to Ollama as
``format=<model>.model_json_schema()``, the grammar makes it *structurally impossible*
for Granite to emit a percentage, a confidence, or any magnitude. There is no
``73%`` to fabricate because there is no number-shaped hole to fill.

Numbers (page numbers, counts) live exclusively on the **code-owned** models
(:class:`Citation` and friends), which are populated by our own code from Docling
provenance *after* Granite runs — never by the model. The two families are kept
strictly disjoint, and ``tests/test_no_numbers_in_granite_schema.py`` enforces it.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# Shared enums — string literals only. A state can never become a number.
# ─────────────────────────────────────────────────────────────────────────────

CellState = Literal["PRESENT", "WEAK", "ABSENT", "NOT_DOCUMENTED"]
"""Per-dimension evidence state. ``NOT_DOCUMENTED`` renders as a distinct hatched
cell — never silently collapsed into the other three."""

SplitAxis = Literal[
    "RULE_AMBIGUITY",
    "INDETERMINACY",
    "DECISION_TIME_DEFICIT",
    "CULTURAL_PRIOR_BIAS",
]
"""The four fixed, MECE dimensions disagreement is decomposed across."""

ResolutionStatus = Literal["SETTLED_FACT", "ADJUDICATED_CONTESTED", "UNRESOLVABLE"]
"""State the fact first, then decompose the residual. Pure refusal reads as evasion."""

LensKind = Literal["REFEREE", "TACTICAL", "HISTORICAL", "FRAMING"]

LensStance = Literal["SUPPORTS", "DISPUTES", "MIXED", "INSUFFICIENT_EVIDENCE"]

LensState = Literal["GROUNDED", "INSUFFICIENT_EVIDENCE"]
"""``GROUNDED`` requires at least one citation. Cite or say "insufficient evidence" —
the lens never free-generates."""

DocKind = Literal[
    "IFAB_LAW",
    "VAR_PROTOCOL",
    "STATSBOMB_EVENT",
    "HISTORICAL_REPORT",
    "FRAMING_SOURCE",
    "TABLE_CELL",
]

FramingRole = Literal["IS_FROM_X", "CHARACTERIZES_X"]
"""A framing source either *is from* a market, or *characterizes* one from outside.
A market lens only renders when it holds at least one ``IS_FROM_X`` source — the
structural guard against stereotyping."""

CANONICAL_AXIS_ORDER: tuple[SplitAxis, ...] = (
    "RULE_AMBIGUITY",
    "INDETERMINACY",
    "DECISION_TIME_DEFICIT",
    "CULTURAL_PRIOR_BIAS",
)


# ─────────────────────────────────────────────────────────────────────────────
# GRANITE-FACING models — enums + list[str] + str ONLY. No numeric field, ever.
# These schemas are what Granite is constrained to emit.
# ─────────────────────────────────────────────────────────────────────────────


class LensOutput(BaseModel):
    """One lens's grounded reading of the incident. Granite-facing.

    Either ``GROUNDED`` with one or more citations, or ``INSUFFICIENT_EVIDENCE`` with
    none — there is no middle ground and no confidence score.
    """

    model_config = ConfigDict(extra="forbid")

    lens: LensKind
    stance: LensStance
    state: LensState
    citation_ids: list[str] = Field(default_factory=list)
    rationale: str

    @model_validator(mode="after")
    def _cite_or_die(self) -> "LensOutput":
        if self.state == "INSUFFICIENT_EVIDENCE":
            if self.citation_ids or self.stance != "INSUFFICIENT_EVIDENCE":
                raise ValueError(
                    "INSUFFICIENT_EVIDENCE must carry no citations and stance=INSUFFICIENT_EVIDENCE"
                )
        elif not self.citation_ids:
            raise ValueError("a GROUNDED lens requires at least one citation_id")
        return self


class SplitCell(BaseModel):
    """One of the four dimensions of THE SPLIT. Granite-facing.

    There is deliberately **no numeric field**: a cell's width never encodes a
    quantity. It carries a qualitative state and the citations behind it.
    """

    model_config = ConfigDict(extra="forbid")

    axis: SplitAxis
    state: CellState
    citation_ids: list[str] = Field(default_factory=list)
    rationale: str

    @model_validator(mode="after")
    def _grounded_states_cite(self) -> "SplitCell":
        # PRESENT / WEAK assert a tension and must point at evidence.
        # ABSENT / NOT_DOCUMENTED assert no/unknown tension and need no citation.
        if self.state in ("PRESENT", "WEAK") and not self.citation_ids:
            raise ValueError(f"{self.state} cell on {self.axis} requires at least one citation_id")
        return self


class Split(BaseModel):
    """THE SPLIT — the disagreement diagnostic. Granite-facing.

    Exactly four cells, one per axis, in canonical order. A headline, no number.
    """

    model_config = ConfigDict(extra="forbid")

    cells: Annotated[list[SplitCell], Field(min_length=4, max_length=4)]
    headline: str

    @model_validator(mode="after")
    def _one_cell_per_axis_in_order(self) -> "Split":
        axes = tuple(c.axis for c in self.cells)
        if axes != CANONICAL_AXIS_ORDER:
            raise ValueError(
                f"Split.cells must be the four axes in canonical order {CANONICAL_AXIS_ORDER}, got {axes}"
            )
        return self


# The set of Granite-facing models. The no-numbers test walks exactly these.
GRANITE_FACING_MODELS: tuple[type[BaseModel], ...] = (LensOutput, SplitCell, Split)


# ─────────────────────────────────────────────────────────────────────────────
# CODE-OWNED models — populated by our own code AFTER Granite runs, never by it.
# These are NOT passed to Granite as a generation schema, so they may carry
# whatever types our code needs. They are deliberately excluded from
# GRANITE_FACING_MODELS and therefore from the no-numbers guarantee.
# ─────────────────────────────────────────────────────────────────────────────

GuardianVerdict = Literal["GROUNDED", "UNGROUNDED"]
"""IBM Granite Guardian's groundedness verdict for a single claim. Note this is a
verdict *flagged by a model*, recorded at build time — never asserted as ground truth."""


class TrustSeal(BaseModel):
    """The frozen result of auditing one cell's rationale with IBM Granite Guardian.

    Granite proposes a grounded reading; Granite Guardian *disposes* of any reading
    the cited page does not actually support. This seal records that audit. It is
    attached to a cell by our code after Granite runs — Granite never emits it — so
    it lives outside the Granite-facing family and does not touch the no-numbers rule.

    The seal carries no numeric score: a verdict is qualitative, and it is frozen at
    build time (temperature 0, with the checked model and citations recorded), so a
    reviewer re-running the bake gets the identical seal. It is *evidence that an IBM
    safety model flagged the rationale as grounded against its cited page*, never a
    claim that the rationale is true.
    """

    model_config = ConfigDict(extra="forbid")

    verdict: GuardianVerdict
    guardian_model: str  # e.g. "granite-guardian3:2b"
    checked_context_citation_ids: list[str]


# Code-owned models, kept explicitly disjoint from the Granite-facing set.
CODE_OWNED_MODELS: tuple[type[BaseModel], ...] = (TrustSeal,)
