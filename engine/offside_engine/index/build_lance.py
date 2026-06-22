"""Build the per-lens LanceDB index from curated evidence.

Each citation becomes a row carrying its vector plus the metadata retrieval filters on:
``lens`` (which lens may see this evidence), ``page`` and ``citation_id`` (so a hit
resolves straight back to a click-to-source Citation). The index is built once on the
build host and committed frozen, so retrieval at bake time is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import lancedb

from offside_engine.analyze.split_schema import Citation, LensKind
from offside_engine.index.embed import EMBED_DIM, Embedder

TABLE_NAME = "evidence"

# Which lens each kind of source document belongs to. Referee evidence is the IFAB Laws.
LENS_BY_DOC_KIND: dict[str, LensKind] = {
    "IFAB_LAW": "REFEREE",
    "VAR_PROTOCOL": "REFEREE",
    "TABLE_CELL": "REFEREE",
    "STATSBOMB_EVENT": "TACTICAL",
    "HISTORICAL_REPORT": "HISTORICAL",
    "FRAMING_SOURCE": "FRAMING",
}


@dataclass
class EvidenceRow:
    """One indexed evidence row — vector plus the metadata retrieval depends on."""

    citation_id: str
    lens: str
    page: int | None
    text: str
    source_doc: str


def rows_from_citations(citations: list[Citation]) -> list[EvidenceRow]:
    """Map citations to indexed rows, assigning each to its lens by document kind."""
    rows: list[EvidenceRow] = []
    for c in citations:
        lens = LENS_BY_DOC_KIND.get(c.doc_kind)
        if lens is None:
            continue
        rows.append(
            EvidenceRow(
                citation_id=c.id,
                lens=lens,
                page=c.page,
                text=c.extracted_text,
                source_doc=c.source_doc,
            )
        )
    return rows


def build_index(
    citations: list[Citation],
    db_dir: Path,
    *,
    embedder: Embedder | None = None,
) -> int:
    """Embed the citations and write the per-lens LanceDB table. Returns row count."""
    rows = rows_from_citations(citations)
    if not rows:
        raise ValueError("no indexable citations (none mapped to a lens)")

    embedder = embedder or Embedder()
    vectors = embedder.embed([r.text for r in rows])

    records = [
        {
            "vector": vec,
            "citation_id": r.citation_id,
            "lens": r.lens,
            "page": r.page if r.page is not None else -1,
            "text": r.text,
            "source_doc": r.source_doc,
        }
        for r, vec in zip(rows, vectors)
    ]

    db_dir.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(db_dir))
    db.create_table(TABLE_NAME, data=records, mode="overwrite")
    return len(records)


__all__ = ["EMBED_DIM", "TABLE_NAME", "EvidenceRow", "rows_from_citations", "build_index"]
