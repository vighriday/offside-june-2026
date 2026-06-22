"""Fixture writer — deterministic bytes and a clean round-trip.

The web reads these files verbatim, so the writer must be reproducible: the same bundle
must serialize to identical bytes, and the file must load straight back into a valid
bundle. Reuses the golden bundle builder from the IncidentBundle tests.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import IncidentBundle
from offside_engine.bake.write_fixture import bundle_to_json, write_fixture
from tests.test_incident_bundle import _bundle


def test_serialization_is_deterministic():
    b = _bundle()
    assert bundle_to_json(b) == bundle_to_json(b)
    assert bundle_to_json(b).endswith("\n")


def test_keys_are_sorted_for_a_stable_diff():
    text = bundle_to_json(_bundle())
    # incident_id sorts before settled_fact before title at the top level
    assert text.index('"incident_id"') < text.index('"settled_fact"') < text.index('"title"')


def test_write_fixture_names_the_file_by_incident_id(tmp_path):
    out = write_fixture(_bundle(), tmp_path / "fixtures")
    assert out.name == "hand-of-god-1986.json"
    assert out.parent.name == "fixtures"


def test_written_fixture_round_trips_to_a_valid_bundle(tmp_path):
    b = _bundle()
    out = write_fixture(b, tmp_path / "fixtures")
    reloaded = IncidentBundle.model_validate_json(out.read_text(encoding="utf-8"))
    assert reloaded == b
