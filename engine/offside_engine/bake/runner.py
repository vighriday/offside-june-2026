"""The single bake entry point the Colab notebook calls.

Everything the notebook needs in one function, so the notebook stays a thin, readable
shell and the orchestration lives in tested code: assemble the evidence pool, build the
per-lens index, construct the Granite + Guardian clients, bake the incident, and freeze
the fixture. Returns the bundle and the path written.

The only inputs are paths and an aggregate, so a caller can run it fully offline from a
frozen StatsBomb aggregate, or let the notebook fetch a fresh one — the function does
not care which.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.analyze.split_schema import Citation, IncidentBundle
from offside_engine.bake.bake import bake_incident
from offside_engine.bake.corpus_pool import assemble_pool
from offside_engine.bake.incident import IncidentSpec
from offside_engine.bake.write_fixture import write_fixture
from offside_engine.config import DEFAULT_EMBED_MODEL, load_granite_config
from offside_engine.index.build_lance import build_index
from offside_engine.index.embed import Embedder
from offside_engine.retrieve.lens_retrieve import LensRetriever
from offside_engine.statsbomb.pull_aggregates import HandOfGodAggregate


@dataclass(frozen=True)
class BakeResult:
    """What one bake produced: the bundle, the fixture path, and the evidence pool size."""

    bundle: IncidentBundle
    fixture_path: Path
    pool_size: int


def run_bake(
    spec: IncidentSpec,
    *,
    framing_yaml: Path,
    historical_yaml: Path,
    aggregate: HandOfGodAggregate,
    db_dir: Path,
    fixtures_dir: Path,
    corpus_git_sha: str | None = None,
    embedder: Embedder | None = None,
    granite: GraniteClient | None = None,
    guardian: GuardianClient | None = None,
) -> BakeResult:
    """Assemble → index → bake → freeze, returning the bundle and fixture path.

    The clients default to the deterministic config (temperature 0, fixed seed) pointed
    at the local Ollama host — which on Colab is the in-VM Ollama server. They can be
    injected for testing.
    """
    pool: dict[str, Citation] = assemble_pool(
        framing_yaml=framing_yaml,
        historical_yaml=historical_yaml,
        aggregate=aggregate,
    )

    embedder = embedder or Embedder()
    build_index(list(pool.values()), db_dir, embedder=embedder)
    retriever = LensRetriever(db_dir, embedder=embedder)

    granite = granite or GraniteClient(load_granite_config())
    guardian = guardian or GuardianClient()

    bundle = bake_incident(
        spec,
        retriever=retriever,
        granite=granite,
        guardian=guardian,
        citations=pool,
        embed_model=DEFAULT_EMBED_MODEL,
        corpus_git_sha=corpus_git_sha,
    )

    fixture_path = write_fixture(bundle, fixtures_dir)
    return BakeResult(bundle=bundle, fixture_path=fixture_path, pool_size=len(pool))
