"""The integrity lock — the rule that makes the self-attack impossible to fake.

The falsification centerpiece is only worth anything if every verdict in it came from a real
Granite Guardian token. A hand-authored "UNGROUNDED" seal would turn the wow moment into a
fabricated audit — strictly worse than an honest "deterministic-router". So this module is a
hard gate, run in CI and at the end of any probed bake:

* every probe's ``guardian_model`` must be a real ``granite*`` id — never the deterministic
  router and never an empty/placeholder string;
* a ``FLIP`` probe must actually have moved its axis (``state_before != state_after``);
* a ``NOISE`` probe must NOT have moved its axis (the negative control held);
* an ``OVERREACH`` probe must have a real ``UNGROUNDED`` Guardian verdict — the second model
  must have actually overruled the first.

If any check fails, the bake raises :class:`IntegrityError` and no fixture is written. There
is no flag to bypass it: bake the probes live, or do not ship them.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import IncidentBundle, Probe

# A real model id starts with "granite" (e.g. "granite3-guardian:2b"). The deterministic
# router and any blank/placeholder value are rejected.
_REAL_MODEL_PREFIX = "granite"


class IntegrityError(AssertionError):
    """A probe's outcome was not produced by a real, live pipeline run."""


def _check_probe(p: Probe) -> list[str]:
    problems: list[str] = []
    model = (p.guardian_model or "").strip().lower()
    if not model.startswith(_REAL_MODEL_PREFIX):
        problems.append(
            f"{p.kind} probe on {p.axis}: guardian_model {p.guardian_model!r} is not a real "
            f"Granite model — a verdict must come from a live token, never a hand-authored seal."
        )

    if p.kind == "FLIP" and p.state_before == p.state_after:
        problems.append(
            f"FLIP probe on {p.axis} did not move the axis ({p.state_before} -> {p.state_after}); "
            f"a FLIP must demonstrably change the reading or it proves nothing."
        )
    if p.kind == "NOISE" and p.state_before != p.state_after:
        problems.append(
            f"NOISE probe on {p.axis} moved the axis ({p.state_before} -> {p.state_after}); "
            f"the negative control must hold — irrelevant evidence may not change the answer."
        )
    if p.kind == "OVERREACH" and p.guardian_verdict != "UNGROUNDED":
        problems.append(
            f"OVERREACH probe on {p.axis} was not overruled (Guardian said {p.guardian_verdict}); "
            f"the second model must actually flag the over-claim, or there is no audit to show."
        )
    return problems


def assert_probes_authentic(probes: list[Probe]) -> None:
    """Raise :class:`IntegrityError` if any probe is not a real, consistent live result."""
    problems: list[str] = []
    for p in probes:
        problems.extend(_check_probe(p))
    if problems:
        raise IntegrityError(
            "probe integrity lock failed — the self-attack must be baked live, not faked:\n  "
            + "\n  ".join(problems)
        )


def assert_bundle_probes_authentic(bundle: IncidentBundle) -> None:
    """Convenience: enforce the lock on a whole bundle's probes (no-op if it has none)."""
    if bundle.probes:
        assert_probes_authentic(bundle.probes)
