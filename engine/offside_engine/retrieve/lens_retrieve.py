"""Per-lens, metadata-filtered retrieval.

Each lens sees only its own evidence: retrieval filters the shared index on the
``lens`` column before scoring. Disagreement between lenses therefore emerges because
the *retrieved evidence differs*, not because a prompt's tone differs.

A retrieved hit carries the metadata needed to resolve straight back to a click-to-source
Citation (``citation_id`` + ``page``), so a lens claim always points at a real passage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import lancedb

from offside_engine.analyze.split_schema import LensKind
from offside_engine.index.build_lance import TABLE_NAME
from offside_engine.index.embed import Embedder


@dataclass(frozen=True)
class RetrievedHit:
    """One retrieved evidence passage, traceable to its source citation."""

    citation_id: str
    lens: str
    page: int | None
    text: str
    score: float


class LensRetriever:
    """Retrieves evidence for one lens at a time from the frozen LanceDB index."""

    def __init__(self, db_dir: Path, *, embedder: Embedder | None = None) -> None:
        self._table = lancedb.connect(str(db_dir)).open_table(TABLE_NAME)
        self._embedder = embedder or Embedder()

    def retrieve(
        self,
        *,
        lens: LensKind,
        query: str,
        k: int = 3,
        allowed_citation_ids: set[str] | None = None,
    ) -> list[RetrievedHit]:
        """Return up to ``k`` hits for ``lens``, scoped by the lens metadata filter.

        If the lens has no evidence above the index, the result is empty — the caller
        is expected to emit "insufficient evidence" rather than free-generate.

        ``allowed_citation_ids`` is a per-incident allow-list (F-C): when given, only
        evidence on that list may surface, so a lens can never cite a passage that does
        not belong to the incident being baked.

        Results are sorted deterministically by ``(rounded score, citation_id)`` (F-D)
        so two index rebuilds inject the same evidence in the same order — a
        prerequisite for byte-identical frozen fixtures.
        """
        qvec = self._embedder.embed_one(query)
        # Over-fetch then filter+sort+trim in code, so the allow-list cannot starve k.
        results = (
            self._table.search(qvec)
            .where(f"lens = '{lens}'")
            .limit(max(k * 4, k))
            .to_list()
        )
        hits: list[RetrievedHit] = []
        for r in results:
            cid = r["citation_id"]
            if allowed_citation_ids is not None and cid not in allowed_citation_ids:
                continue
            page = r.get("page")
            hits.append(
                RetrievedHit(
                    citation_id=cid,
                    lens=r["lens"],
                    page=None if page in (None, -1) else int(page),
                    text=r["text"],
                    score=float(r.get("_distance", 0.0)),
                )
            )
        hits.sort(key=lambda h: (round(h.score, 6), h.citation_id))
        return hits[:k]
