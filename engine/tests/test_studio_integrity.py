# engine/tests/test_studio_integrity.py
from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.incident_from_form import build_studio_incident


def test_no_quotes_means_no_framing_atom_so_cultural_cannot_fire():
    # The honest property: with no quotes there is no framing evidence, so the Framing lens
    # has nothing to surface and Cultural bias cannot be PRESENT. The engine cannot invent it.
    p = FormPayload(title="t", settled_statement="s", historical_note="h", quotes=[], tactical_note=None)
    _spec, pool = build_studio_incident(p)
    assert not [c for c in pool.values() if c.doc_kind == "FRAMING_SOURCE"]


def test_user_atoms_are_all_in_the_allow_list():
    # No user atom can leak unscoped; every id we created is explicitly allowed, nothing else.
    p = FormPayload(
        title="t", settled_statement="s", historical_note="h",
        quotes=[{"speaker": "a", "source": "s", "text": "x"}], tactical_note="data",
    )
    spec, pool = build_studio_incident(p)
    user_atoms = {cid for cid, c in pool.items() if c.source_doc == "studio-user-input"}
    assert user_atoms <= spec.allowed_citation_ids
