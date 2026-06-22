"""Assemble the full evidence pool — the single source of truth a bake reads from.

A bake needs every evidence atom in one place: the curated IFAB Law passages, the
curated Historical and Framing citations, and the license-safe StatsBomb tactical
citation. This module gathers them into one ``{id: Citation}`` pool, deterministically
and with a duplicate-id guard, so both the LanceDB index and ``bake_incident`` read from
exactly the same evidence.

The StatsBomb aggregate is the only source that touches the network, and only when
``aggregate`` is not supplied — every other source is a committed file, so a pool built
from a frozen ``aggregate`` is fully offline and reproducible.
"""

from __future__ import annotations

from pathlib import Path

from offside_engine.analyze.split_schema import Citation
from offside_engine.ingest.curate import build_curated_citations
from offside_engine.ingest.curated_lenses import (
    load_framing_citations,
    load_historical_citations,
)
from offside_engine.statsbomb.pull_aggregates import (
    HandOfGodAggregate,
    to_tactical_citation,
)


def _add(pool: dict[str, Citation], citations: list[Citation], *, where: str) -> None:
    """Insert citations into the pool, refusing any id collision across sources.

    A duplicate id would make retrieval ambiguous and could let one source's text be
    served under another's id — so a collision fails the bake rather than silently
    overwriting.
    """
    for c in citations:
        if c.id in pool:
            raise ValueError(
                f"duplicate citation id '{c.id}' (adding from {where}); ids must be unique "
                f"across all evidence sources"
            )
        pool[c.id] = c


def assemble_pool(
    *,
    framing_yaml: Path,
    historical_yaml: Path,
    aggregate: HandOfGodAggregate,
) -> dict[str, Citation]:
    """Build the complete ``{id: Citation}`` evidence pool from every source.

    ``aggregate`` is passed in (not fetched) so the pool is built from a frozen
    StatsBomb summary — keeping the assembly offline and the result reproducible.
    """
    pool: dict[str, Citation] = {}
    _add(pool, build_curated_citations(), where="curated IFAB laws")
    _add(pool, load_historical_citations(historical_yaml), where="historical YAML")
    _add(pool, load_framing_citations(framing_yaml), where="framing YAML")
    _add(pool, [to_tactical_citation(aggregate)], where="statsbomb tactical")
    return pool
