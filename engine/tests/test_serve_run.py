# engine/tests/test_serve_run.py
from unittest.mock import patch

from offside_engine.serve.form_models import FormPayload, Quote


def _payload() -> FormPayload:
    return FormPayload(
        title="A disputed penalty",
        settled_statement="A defender's arm blocked the ball; the contact is agreed.",
        historical_note="VAR reviewed a clear replay; the contact was fully visible.",
        quotes=[
            Quote(speaker="Home", source="post-match", text="clear penalty"),
            Quote(speaker="Away", source="post-match", text="never a penalty"),
        ],
        tactical_note=None,
    )


def test_decompose_calls_bake_with_form_sourced_spec_and_pool():
    # We don't run Ollama in CI; assert decompose wires the form-built spec+pool into the
    # real bake. The bake itself is exercised by its own tests against live models.
    from offside_engine.serve import run as run_mod

    captured = {}

    def fake_bake(spec, **kw):
        captured["spec"] = spec
        captured["citations"] = kw["citations"]
        # return a sentinel; decompose must pass it straight through
        return "BUNDLE_SENTINEL"

    with patch.object(run_mod, "bake_incident", side_effect=fake_bake), \
         patch.object(run_mod, "build_index", return_value=3), \
         patch.object(run_mod, "LensRetriever"), \
         patch.object(run_mod, "GraniteClient"), \
         patch.object(run_mod, "GuardianClient"), \
         patch.object(run_mod, "load_granite_config"):
        out = run_mod.decompose(_payload())

    assert out == "BUNDLE_SENTINEL"
    assert captured["spec"].title == "A disputed penalty"
    assert captured["spec"].expected_thesis == {}
    # pool carries IFAB + user atoms
    kinds = {c.doc_kind for c in captured["citations"].values()}
    assert {"IFAB_LAW", "FRAMING_SOURCE", "HISTORICAL_REPORT"} <= kinds
