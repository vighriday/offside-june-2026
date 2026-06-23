"""Lens runner — render, short-circuit, and the hallucinated-citation guard.

Granite is mocked: these tests assert the *wiring* (evidence rendering, the no-call
short-circuit, and rejection of citations the lens was never shown), never model
behaviour.
"""

from __future__ import annotations


from offside_engine.analyze.lens_runner import (
    LensRun,
    render_evidence,
    run_lens,
)
from offside_engine.analyze.split_schema import LensOutput
from offside_engine.retrieve.lens_retrieve import RetrievedHit


def _hit(cid: str, text: str, lens: str = "REFEREE") -> RetrievedHit:
    return RetrievedHit(citation_id=cid, lens=lens, page=118, text=text, score=0.1)


class _FakeRetriever:
    """Returns a fixed hit list and records the call args for assertion."""

    def __init__(self, hits):
        self._hits = hits
        self.calls = []

    def retrieve(self, *, lens, query, k=3, allowed_citation_ids=None):
        self.calls.append((lens, query, k, allowed_citation_ids))
        return list(self._hits)


class _FakeGranite:
    """Returns a pre-baked LensOutput and records the system/user it was sent."""

    def __init__(self, output: LensOutput):
        self._output = output
        self.last_system = None
        self.last_user = None

    def generate_structured(self, *, schema, system, user):
        self.last_system = system
        self.last_user = user
        return self._output


def test_render_evidence_labels_each_hit_with_its_id():
    block = render_evidence("REFEREE", [_hit("ifab-1", "handball denies a goal")])
    assert "RETRIEVED LAW:" in block
    assert "[ifab-1] handball denies a goal" in block


def test_render_evidence_marks_empty_lens():
    block = render_evidence("TACTICAL", [])
    assert "RETRIEVED DATA:" in block
    assert "no evidence retrieved" in block


def test_no_evidence_short_circuits_without_calling_granite():
    retr = _FakeRetriever([])

    class _Boom:
        def generate_structured(self, **_):
            raise AssertionError("Granite must not be called with no evidence")

    run = run_lens(lens="HISTORICAL", query="q", retriever=retr, granite=_Boom())
    assert isinstance(run, LensRun)
    assert run.output.state == "INSUFFICIENT_EVIDENCE"
    assert run.output.stance == "INSUFFICIENT_EVIDENCE"
    assert run.output.citation_ids == []
    assert run.hits == ()


def test_happy_path_returns_output_and_the_hits_it_saw():
    hits = [_hit("ifab-1", "a clear offence clause")]
    retr = _FakeRetriever(hits)
    out = LensOutput(
        lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
        citation_ids=["ifab-1"], rationale="The clause covers it (ifab-1).",
    )
    gran = _FakeGranite(out)

    run = run_lens(lens="REFEREE", query="handball", retriever=retr, granite=gran)

    assert run.output is out
    assert [h.citation_id for h in run.hits] == ["ifab-1"]
    # the rendered user message carried the id the lens then cited
    assert "[ifab-1] a clear offence clause" in gran.last_user


def test_allow_list_is_passed_through_to_retrieval():
    retr = _FakeRetriever([_hit("ifab-1", "clause")])
    out = LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
                     citation_ids=["ifab-1"], rationale="ok (ifab-1).")
    run_lens(lens="REFEREE", query="q", retriever=retr, granite=_FakeGranite(out),
             allowed_citation_ids={"ifab-1"}, k=5)
    lens, query, k, allow = retr.calls[0]
    assert allow == {"ifab-1"}
    assert k == 5


class _SequenceGranite:
    """Returns a scripted sequence of outputs (or raises), one per call — to drive retry."""

    def __init__(self, outputs):
        self._outputs = list(outputs)
        self.calls = 0
        self.last_system = None

    def generate_structured(self, *, schema, system, user):
        self.last_system = system
        item = self._outputs[min(self.calls, len(self._outputs) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


def test_persistently_hallucinated_citation_degrades_not_crashes():
    # A lens that keeps citing an id it was never shown must NOT crash the bake; after a
    # retry it degrades to INSUFFICIENT_EVIDENCE so the run continues.
    retr = _FakeRetriever([_hit("ifab-1", "clause")])
    out = LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
                     citation_ids=["ifab-999"], rationale="invented (ifab-999).")
    run = run_lens(lens="REFEREE", query="q", retriever=retr, granite=_FakeGranite(out))
    assert run.output.state == "INSUFFICIENT_EVIDENCE"
    assert run.output.citation_ids == []


def test_retry_recovers_after_one_bad_output():
    # First call cites a stray id; the corrective retry returns a clean reading.
    retr = _FakeRetriever([_hit("ifab-1", "clause")])
    bad = LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
                     citation_ids=["ifab-999"], rationale="invented (ifab-999).")
    good = LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
                      citation_ids=["ifab-1"], rationale="grounded (ifab-1).")
    gran = _SequenceGranite([bad, good])
    run = run_lens(lens="REFEREE", query="q", retriever=retr, granite=gran)
    assert run.output.state == "GROUNDED"
    assert run.output.citation_ids == ["ifab-1"]
    assert gran.calls == 2  # took the retry
    assert "CORRECTION" in gran.last_system  # the nudge was applied


def test_validation_error_on_first_call_is_retried_then_degrades():
    # The model returns content the schema rejects (e.g. GROUNDED with no citation).
    # The runner must catch the ValidationError, retry, and degrade if it persists.
    from pydantic import ValidationError

    retr = _FakeRetriever([_hit("ifab-1", "clause")])

    def _make_err():
        try:
            LensOutput(lens="FRAMING", stance="MIXED", state="GROUNDED",
                       citation_ids=[], rationale="no citation")
        except ValidationError as e:
            return e
        raise AssertionError("expected a ValidationError")

    gran = _SequenceGranite([_make_err(), _make_err()])
    run = run_lens(lens="FRAMING", query="q", retriever=retr, granite=gran)
    assert run.output.state == "INSUFFICIENT_EVIDENCE"
    assert gran.calls == 2  # retried once before degrading
