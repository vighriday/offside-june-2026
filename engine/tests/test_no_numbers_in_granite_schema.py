"""THE MOAT, as an executable invariant.

OFFSIDE's central trust claim is that IBM Granite *structurally cannot* emit a
number — no fabricated percentage, no confidence score, no magnitude. This test
proves it by walking the full JSON Schema of every Granite-facing model and failing
on any numeric type.

If someone adds ``confidence: float`` to ``SplitCell`` (or any numeric field, however
nested), this test goes red and the build breaks. That is the point: the guarantee is
enforced by CI, not by good intentions.
"""

from __future__ import annotations

import pytest

from offside_engine.analyze.split_schema import GRANITE_FACING_MODELS

# JSON Schema "type" values that represent a number. ``minItems`` / ``maxItems`` /
# ``minLength`` are *constraints*, not emittable fields, so they are not numeric types
# and never appear as a "type" — they are intentionally not in this set.
NUMERIC_JSON_TYPES = {"integer", "number"}


def _walk_for_numeric_types(node: object, path: str = "$"):
    """Yield (path, type) for every place the schema declares a numeric type."""
    if isinstance(node, dict):
        t = node.get("type")
        if isinstance(t, str) and t in NUMERIC_JSON_TYPES:
            yield (path, t)
        elif isinstance(t, list):  # e.g. ["integer", "null"]
            for sub in t:
                if sub in NUMERIC_JSON_TYPES:
                    yield (path, sub)
        for key, value in node.items():
            yield from _walk_for_numeric_types(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_for_numeric_types(item, f"{path}[{i}]")


@pytest.mark.parametrize("model", GRANITE_FACING_MODELS, ids=lambda m: m.__name__)
def test_granite_facing_model_has_no_numeric_field(model):
    """No Granite-facing model may declare an integer/number anywhere in its schema."""
    schema = model.model_json_schema()
    offenders = list(_walk_for_numeric_types(schema, f"${model.__name__}"))
    assert not offenders, (
        f"{model.__name__} exposes numeric type(s) to Granite — the model could emit a "
        f"fabricated number. Offending paths: {offenders}"
    )


def test_at_least_the_three_known_models_are_guarded():
    """Guard against someone silently shrinking the guarded set."""
    names = {m.__name__ for m in GRANITE_FACING_MODELS}
    assert {"LensOutput", "SplitCell", "Split"} <= names


def test_code_owned_models_are_not_granite_facing():
    """Code-owned models (e.g. TrustSeal) are populated after Granite runs and must
    never be in the Granite-facing set — that is what keeps the no-numbers guarantee
    scoped to exactly what Granite emits."""
    from offside_engine.analyze.split_schema import CODE_OWNED_MODELS, TrustSeal

    granite_facing = set(GRANITE_FACING_MODELS)
    assert all(m not in granite_facing for m in CODE_OWNED_MODELS)
    assert TrustSeal in CODE_OWNED_MODELS
