"""Turn a Studio FormPayload into the SAME (IncidentSpec, citation pool) shape the corpus
folders produce — so the unchanged bake can decompose a user-supplied incident exactly as
it does a curated one. The user brings the human evidence (settled facts, historical note,
named quotes); the IFAB law atoms are reused from the curated corpus so the Referee lens
retrieves the matching Law itself. No thesis oracle is attached: a user incident has no
documented answer to check against, so the SPLIT is whatever the evidence routes to."""
from __future__ import annotations

import re

from offside_engine.analyze.split_schema import Citation
from offside_engine.bake.incident import IncidentSpec
from offside_engine.ingest.curate import build_curated_citations
from offside_engine.serve.form_models import FormPayload


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "incident"


_LENS_QUERIES = {
    "REFEREE": "Which Law governs this act, and is it a clear single offence clause or are clauses in conflict?",
    "TACTICAL": "Is there event-data context for this incident?",
    "HISTORICAL": "Could the officials see or review the decisive fact at the moment of the call, and is the truth recoverable now?",
    "FRAMING": "How did named figures describe the same agreed fact afterwards?",
}


def build_studio_incident(payload: FormPayload) -> tuple[IncidentSpec, dict[str, Citation]]:
    incident_id = f"studio-{_slug(payload.title)}"
    pool: dict[str, Citation] = {}

    # IFAB law atoms — reused verbatim so the Referee lens can retrieve the real Law page.
    law_atoms = build_curated_citations()
    for c in law_atoms:
        pool[c.id] = c

    user_ids: set[str] = set()

    # Historical atom (one), if supplied.
    if payload.historical_note.strip():
        hid = f"{incident_id}-hist"
        pool[hid] = Citation(
            id=hid,
            source_doc="studio-user-input",
            doc_kind="HISTORICAL_REPORT",
            extracted_text=payload.historical_note.strip(),
        )
        user_ids.add(hid)

    # Framing atoms — one per quote. Two in opposed valence are what fire Cultural bias.
    for i, q in enumerate(payload.quotes):
        qid = f"{incident_id}-framing-{i}"
        pool[qid] = Citation(
            id=qid,
            source_doc="studio-user-input",
            doc_kind="FRAMING_SOURCE",
            extracted_text=f"{q.speaker} ({q.source}): {q.text}",
        )
        user_ids.add(qid)

    # Tactical atom (optional, one).
    if payload.tactical_note and payload.tactical_note.strip():
        tid = f"{incident_id}-tactical"
        pool[tid] = Citation(
            id=tid,
            source_doc="studio-user-input",
            doc_kind="STATSBOMB_EVENT",
            extracted_text=payload.tactical_note.strip(),
        )
        user_ids.add(tid)

    # The Referee lens may surface any IFAB law atom; the human lenses may surface only the
    # user's own atoms. So the allow-list is the user's atoms plus every law atom.
    allowed = frozenset(user_ids | {c.id for c in law_atoms})

    spec = IncidentSpec(
        incident_id=incident_id,
        title=payload.title,
        settled_status="ADJUDICATED_CONTESTED",
        settled_statement=payload.settled_statement,
        settled_citation_ids=(),  # the settled fact is the user's prose; no forced citation
        admission_note="",
        lens_queries=dict(_LENS_QUERIES),
        allowed_citation_ids=allowed,
        expected_thesis={},  # no oracle for a user incident
    )
    return spec, pool
