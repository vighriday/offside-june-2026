"""Run the real bake on a user-supplied Studio incident and return the IncidentBundle.

This mirrors analyze_live.py's non-graph path exactly — index the pool, build the three
real clients, bake — but the evidence comes from the form (Task 2) instead of a corpus
folder. strict_thesis is False (a user incident has no oracle); no probes, no rule
evolution. The bake is unchanged: same cite-or-die, same Guardian gate, same no-numbers."""
from __future__ import annotations

import tempfile
from pathlib import Path

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.bake.bake import bake_incident
from offside_engine.config import DEFAULT_GUARDIAN_MODEL, load_granite_config
from offside_engine.index.build_lance import build_index
from offside_engine.retrieve.lens_retrieve import LensRetriever
from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.incident_from_form import build_studio_incident


def decompose(payload: FormPayload):
    """Bake the user incident with the real Granite + Guardian models. Returns IncidentBundle."""
    spec, pool = build_studio_incident(payload)
    cfg = load_granite_config()
    with tempfile.TemporaryDirectory() as tmp:
        db_dir = Path(tmp) / "lance"
        build_index(list(pool.values()), db_dir)
        retriever = LensRetriever(db_dir)
        granite = GraniteClient(cfg)
        guardian = GuardianClient(host=cfg.host, model=DEFAULT_GUARDIAN_MODEL)
        return bake_incident(
            spec,
            retriever=retriever,
            granite=granite,
            guardian=guardian,
            citations=pool,
            corpus_git_sha=None,
            strict_thesis=False,
        )
