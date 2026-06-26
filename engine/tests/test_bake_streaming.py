"""The streaming bake yields real per-step events in pipeline order, ending with the bundle.

These prove the generator emits one event as each lens runs, one as each lens is audited,
one as each cell resolves, and finally the assembled bundle — all derived from the SAME
unchanged bake steps, with mocked model clients so no Ollama is needed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from offside_engine.analyze.guardian_gate import GatedCell, GatedLens
from offside_engine.analyze.lens_runner import LensRun
from offside_engine.analyze.split_schema import (
    Citation,
    LensOutput,
    Split,
    SplitCell,
    TrustSeal,
)
from offside_engine.bake import bake as bake_mod


def _lens_output(lens: str) -> LensOutput:
    return LensOutput(
        lens=lens, stance="SUPPORTS", state="GROUNDED",
        citation_ids=["c1"], rationale="r",
    )


def _seal() -> TrustSeal:
    return TrustSeal(verdict="GROUNDED", guardian_model="granite3-guardian:2b",
                     checked_context_citation_ids=["c1"])


def test_streaming_bake_yields_lens_audit_cell_then_done(monkeypatch):
    spec = MagicMock()
    spec.incident_id = "studio-x"
    spec.title = "X"
    spec.settled_status = "ADJUDICATED_CONTESTED"
    spec.settled_statement = "agreed"
    spec.settled_citation_ids = ()
    spec.admission_note = ""
    spec.lens_queries = {k: "q" for k in ("REFEREE", "TACTICAL", "HISTORICAL", "FRAMING")}
    spec.allowed_citation_ids = frozenset({"c1"})
    spec.expected_thesis = {}

    # Stub every model-touching step the generator calls, so it runs with no Ollama.
    monkeypatch.setattr(bake_mod, "run_lens",
                        lambda **kw: LensRun(output=_lens_output(kw["lens"]), hits=()))
    monkeypatch.setattr(bake_mod, "gate_lens",
                        lambda output, **kw: GatedLens(output=output, seal=_seal()))
    monkeypatch.setattr(bake_mod, "gate_cell",
                        lambda cell, **kw: GatedCell(cell=cell, seal=_seal()))
    # derive_split returns a real four-cell Split so the cell loop has something to emit.
    cells = [SplitCell(axis=a, state="ABSENT", citation_ids=[], rationale="r")
             for a in ("RULE_AMBIGUITY", "INDETERMINACY", "DECISION_TIME_DEFICIT", "CULTURAL_PRIOR_BIAS")]
    monkeypatch.setattr(bake_mod, "derive_split",
                        lambda gated, **kw: Split(cells=cells, headline="h"))

    citations = {"c1": Citation(id="c1", source_doc="studio-user-input", doc_kind="FRAMING_SOURCE",
                                extracted_text="x")}
    events = list(bake_mod.bake_incident_streaming(
        spec, retriever=MagicMock(), granite=_fake_granite(), guardian=_fake_guardian(),
        citations=citations,
    ))

    kinds = [e["type"] for e in events]
    assert kinds.count("lens") == 4
    assert kinds.count("audit") == 4
    assert kinds.count("cell") == 4
    assert kinds[-1] == "done"
    # lens events precede the cell events (genuine pipeline order)
    assert kinds.index("lens") < kinds.index("cell")
    # the done event carries the real IncidentBundle object (the serve layer JSON-dumps it)
    done = events[-1]
    assert done["bundle"].incident_id == "studio-x"
    # each audit event carries the real guardian model + verdict
    audit = next(e for e in events if e["type"] == "audit")
    assert audit["verdict"] == "GROUNDED"
    assert audit["guardian_model"] == "granite3-guardian:2b"


def _fake_granite():
    g = MagicMock()
    g.config.model = "granite3.3:8b"
    g.options = {}
    return g


def _fake_guardian():
    g = MagicMock()
    g.model = "granite3-guardian:2b"
    return g
