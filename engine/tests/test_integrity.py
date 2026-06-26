"""The integrity lock — proof the self-attack cannot be faked.

These assert that a probe is rejected unless its verdict came from a real Granite model and
its outcome matches what its kind claims. This is the gate that keeps the wow moment honest:
a hand-authored "UNGROUNDED" can never reach a fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from offside_engine.analyze.split_schema import IncidentBundle, Probe
from offside_engine.bake.integrity import (
    IntegrityError,
    assert_bundle_probes_authentic,
    assert_probes_authentic,
)

_FIXTURES = Path(__file__).resolve().parents[2] / "web" / "fixtures"


def _probe(**kw) -> Probe:
    base = dict(
        kind="FLIP",
        axis="INDETERMINACY",
        label="x",
        plain_question="x",
        injected_text="x",
        state_before="PRESENT",
        state_after="NOT_DOCUMENTED",
        guardian_verdict="GROUNDED",
        guardian_model="granite3-guardian:2b",
        outcome="x",
    )
    base.update(kw)
    return Probe(**base)


def test_real_flip_passes():
    assert_probes_authentic([_probe(kind="FLIP", state_before="PRESENT", state_after="ABSENT")])


def test_deterministic_router_verdict_is_rejected():
    # The exact failure the lock exists for: a seal that never ran a real model.
    with pytest.raises(IntegrityError, match="not a real Granite model"):
        assert_probes_authentic([_probe(guardian_model="deterministic-router")])


def test_blank_model_is_rejected():
    with pytest.raises(IntegrityError, match="not a real Granite model"):
        assert_probes_authentic([_probe(guardian_model="")])


def test_flip_that_did_not_move_is_rejected():
    with pytest.raises(IntegrityError, match="did not move"):
        assert_probes_authentic([_probe(kind="FLIP", state_before="PRESENT", state_after="PRESENT")])


def test_noise_that_moved_is_rejected():
    with pytest.raises(IntegrityError, match="negative control"):
        assert_probes_authentic([
            _probe(kind="NOISE", state_before="PRESENT", state_after="ABSENT"),
        ])


def test_overreach_not_overruled_is_rejected():
    # An OVERREACH probe that Guardian did NOT flag is no demonstration at all.
    with pytest.raises(IntegrityError, match="not overruled"):
        assert_probes_authentic([
            _probe(kind="OVERREACH", guardian_verdict="GROUNDED",
                   state_before="PRESENT", state_after="PRESENT"),
        ])


def test_real_overreach_overrule_passes():
    assert_probes_authentic([
        _probe(kind="OVERREACH", guardian_verdict="UNGROUNDED",
               state_before="PRESENT", state_after="PRESENT",
               guardian_model="granite3-guardian:2b"),
    ])


def test_every_shipped_fixture_with_probes_is_authentic():
    # The CI lock on real artifacts: any fixture that ships probes must have been baked live —
    # a hand-authored UNGROUNDED in a committed fixture fails the build here. Fixtures without
    # probes are a no-op (the centerpiece is opt-in per incident).
    for path in _FIXTURES.glob("*.json"):
        bundle = IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))
        assert_bundle_probes_authentic(bundle)  # raises IntegrityError if any probe is faked
