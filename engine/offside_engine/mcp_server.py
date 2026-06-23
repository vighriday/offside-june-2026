"""OFFSIDE as an MCP server — the engine, callable by any agent through IBM Context Forge.

This makes OFFSIDE a *tool*, not just a website: an external agent (or the IBM
mcp-context-forge gateway) can ask it to decompose a contested decision and get back the
structured SPLIT — the four axes, their states, and the page-cited evidence behind each —
with the no-numbers contract intact (the response carries states, never scores).

Two tools are exposed:

* ``list_incidents()`` — the incidents OFFSIDE can decompose.
* ``decompose_disagreement(incident_id)`` — the SPLIT for one incident: per-axis state +
  rationale + the citation ids and source pages that ground each live axis.

The server reads the frozen, audited fixtures (the same artifacts the site renders), so it
is fast, deterministic, and needs no GPU — the honest production surface. Registering it
behind IBM Context Forge (the MCP gateway/registry) is a one-line entry; see
``flows/context_forge.md``.

Run:  python -m offside_engine.mcp_server         # stdio transport (what Context Forge speaks)
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from offside_engine.analyze.split_schema import IncidentBundle

_FIXTURES = Path(__file__).resolve().parents[2] / "web" / "fixtures"

mcp = FastMCP("offside")


def _load(incident_id: str) -> IncidentBundle | None:
    """Load a frozen, audited fixture (preferring the real bake over a sample)."""
    for name in (f"{incident_id}.json", f"{incident_id}.sample.json"):
        path = _FIXTURES / name
        if path.exists():
            return IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))
    return None


def _available() -> list[IncidentBundle]:
    out: list[IncidentBundle] = []
    seen: set[str] = set()
    for path in sorted(_FIXTURES.glob("*.json")):
        iid = path.name.replace(".sample.json", "").replace(".json", "")
        if iid in seen:
            continue
        bundle = _load(iid)
        if bundle is not None:
            seen.add(iid)
            out.append(bundle)
    return out


@mcp.tool()
def list_incidents() -> str:
    """List the contested decisions OFFSIDE can decompose, with their one-line settled fact."""
    items = [
        {"incident_id": b.incident_id, "title": b.title,
         "settled_status": b.settled_fact.status}
        for b in _available()
    ]
    return json.dumps({"incidents": items}, ensure_ascii=False, indent=2)


@mcp.tool()
def decompose_disagreement(incident_id: str) -> str:
    """Return THE SPLIT for one incident: why the disagreement persists, decomposed across the
    four axes, with each live axis grounded to real source pages. Carries states, never numbers.

    Args:
        incident_id: one of the ids from ``list_incidents`` (e.g. "offside-margin").
    """
    bundle = _load(incident_id)
    if bundle is None:
        ids = [b.incident_id for b in _available()]
        return json.dumps(
            {"error": f"unknown incident '{incident_id}'", "available": ids},
            ensure_ascii=False, indent=2,
        )

    def cell_view(cell) -> dict:
        sources = []
        for cid in cell.citation_ids:
            c = bundle.citations.get(cid)
            if c is not None:
                sources.append({
                    "citation_id": cid,
                    "source_doc": c.source_doc,
                    "doc_kind": c.doc_kind,
                    "page": c.page,
                })
        return {
            "axis": cell.axis,
            "state": cell.state,  # PRESENT / WEAK / ABSENT / NOT_DOCUMENTED — never a number
            "rationale": cell.rationale,
            "sources": sources,
        }

    payload = {
        "incident_id": bundle.incident_id,
        "title": bundle.title,
        "settled_fact": {
            "status": bundle.settled_fact.status,
            "statement": bundle.settled_fact.statement,
        },
        "split": {
            "headline": bundle.split.headline,
            "cells": [cell_view(c) for c in bundle.split.cells],
        },
        "lenses": [
            {"lens": sl.output.lens, "stance": sl.output.stance,
             "guardian_verdict": sl.seal.verdict}
            for sl in bundle.lenses
        ],
        "provenance": {
            "granite_model": bundle.provenance.granite_model,
            "guardian_model": bundle.provenance.guardian_model,
            "corpus_git_sha": bundle.provenance.corpus_git_sha,
        },
        "contract": "no-numbers: this response communicates with states, never scores.",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run()  # stdio transport — what Context Forge / MCP clients speak


if __name__ == "__main__":
    main()
