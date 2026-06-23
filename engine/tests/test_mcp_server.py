"""The MCP surface is real and honours the no-numbers contract.

These tests call the tool functions directly (no transport) and assert: the incident list
matches the shipped fixtures, decompose returns a well-formed SPLIT with grounded sources on
its live axes, an unknown id fails gracefully, and no score/percentage leaks into the agent
payload — the moat must hold across the MCP boundary, not only in the UI.
"""

from __future__ import annotations

import json
import re

from offside_engine.mcp_server import decompose_disagreement, list_incidents


def test_list_incidents_matches_shipped_fixtures():
    data = json.loads(list_incidents())
    ids = {i["incident_id"] for i in data["incidents"]}
    # the six shipped incidents must all be callable
    for expected in (
        "hand-of-god-1986", "handball-rewrite", "offside-margin",
        "pgmol-subjective", "suarez-handball-2010", "lampard-ghost-goal-2010",
    ):
        assert expected in ids


def test_decompose_returns_grounded_split_for_a_live_axis():
    d = json.loads(decompose_disagreement("offside-margin"))
    assert d["title"] == "The millimetre offside line"
    cells = {c["axis"]: c for c in d["split"]["cells"]}
    assert set(cells) == {
        "RULE_AMBIGUITY", "INDETERMINACY", "DECISION_TIME_DEFICIT", "CULTURAL_PRIOR_BIAS"
    }
    # the live axis for this incident is INDETERMINACY, and it must carry grounded sources
    indet = cells["INDETERMINACY"]
    assert indet["state"] == "PRESENT"
    assert len(indet["sources"]) >= 1


def test_unknown_incident_fails_gracefully():
    d = json.loads(decompose_disagreement("not-an-incident"))
    assert "error" in d and "available" in d


def test_no_numbers_leak_across_the_mcp_boundary():
    for iid in ("hand-of-god-1986", "handball-rewrite", "offside-margin"):
        payload = decompose_disagreement(iid)
        # no percentage and no confidence-shaped score in the agent-facing payload
        assert not re.search(r"\d+\s*%", payload)
        assert not re.search(r"\b0?\.\d+\b", payload)  # no bare 0.xx confidence floats
