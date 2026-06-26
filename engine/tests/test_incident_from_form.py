from offside_engine.serve.form_models import FormPayload, Quote
from offside_engine.serve.incident_from_form import build_studio_incident


def _payload() -> FormPayload:
    return FormPayload(
        title="A disputed penalty",
        settled_statement="A defender's arm blocked the ball in the box. The arm contact is agreed.",
        historical_note="VAR reviewed it on a clear replay; the contact was fully visible.",
        quotes=[
            Quote(speaker="Home manager", source="post-match", text="clear penalty, the arm was out"),
            Quote(speaker="Away manager", source="post-match", text="never a penalty, ball to hand"),
        ],
        tactical_note=None,
    )


def test_build_studio_incident_returns_spec_and_pool():
    spec, pool = build_studio_incident(_payload())
    # spec has no thesis oracle for a user incident
    assert spec.expected_thesis == {}
    assert spec.title == "A disputed penalty"
    # the four lens queries are present so every lens can retrieve
    assert set(spec.lens_queries) == {"REFEREE", "TACTICAL", "HISTORICAL", "FRAMING"}
    # the pool carries IFAB law atoms (for Referee retrieval) AND the user's atoms
    kinds = {c.doc_kind for c in pool.values()}
    assert "IFAB_LAW" in kinds
    assert "FRAMING_SOURCE" in kinds
    assert "HISTORICAL_REPORT" in kinds
    # every user atom id is in the allow-list, and the allow-list ⊆ pool ids
    assert spec.allowed_citation_ids <= set(pool)


def test_two_opposed_quotes_produce_two_framing_atoms():
    spec, pool = build_studio_incident(_payload())
    framing = [c for c in pool.values() if c.doc_kind == "FRAMING_SOURCE"]
    assert len(framing) == 2


def test_thin_evidence_still_builds_but_yields_no_framing():
    p = FormPayload(
        title="x", settled_statement="y", historical_note="z", quotes=[], tactical_note=None
    )
    spec, pool = build_studio_incident(p)
    framing = [c for c in pool.values() if c.doc_kind == "FRAMING_SOURCE"]
    assert framing == []  # no quotes → no framing atoms → Cultural bias cannot fire (honest)
