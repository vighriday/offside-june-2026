"""Per-lens retrieval — the lens filter scopes results, hits trace to citations.

Builds a real LanceDB index (deterministic fake embeddings keyed by lens so each
lens's evidence clusters), then asserts a Referee query returns only Referee evidence.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import Citation
from offside_engine.index.build_lance import build_index
from offside_engine.index.embed import EMBED_DIM
from offside_engine.retrieve.lens_retrieve import LensRetriever


class _LensKeyedEmbedder:
    """Embeds so REFEREE/TACTICAL/FRAMING texts occupy distinct regions of space."""

    _BASIS = {"referee": 0, "handball": 0, "tactical": 1, "shot": 1, "framing": 2, "god": 2}

    def _vec(self, text: str):
        axis = 0
        for word, a in self._BASIS.items():
            if word in text.lower():
                axis = a
                break
        v = [0.0] * EMBED_DIM
        v[axis] = 1.0
        return v

    def embed(self, texts):
        return [self._vec(t) for t in texts]

    def embed_one(self, text):
        return self._vec(text)


def _citations():
    return [
        Citation(id="ifab-1", source_doc="ifab", doc_kind="IFAB_LAW", page=118,
                 extracted_text="referee handball deliberate denies goal"),
        Citation(id="sb-1", source_doc="statsbomb", doc_kind="STATSBOMB_EVENT", page=None,
                 extracted_text="tactical shot body_part Other minute 51"),
        Citation(id="fr-1", source_doc="framing", doc_kind="FRAMING_SOURCE", page=None,
                 extracted_text="framing the hand of god quote"),
    ]


def _retriever(tmp_path):
    emb = _LensKeyedEmbedder()
    build_index(_citations(), tmp_path / "lance", embedder=emb)
    return LensRetriever(tmp_path / "lance", embedder=emb)


def test_referee_query_returns_only_referee_evidence(tmp_path):
    r = _retriever(tmp_path)
    hits = r.retrieve(lens="REFEREE", query="handball offence", k=5)
    assert hits, "expected referee evidence"
    assert all(h.lens == "REFEREE" for h in hits)
    assert hits[0].citation_id == "ifab-1"
    assert hits[0].page == 118  # traceable to a real page


def test_lens_filter_excludes_other_lenses(tmp_path):
    r = _retriever(tmp_path)
    # A tactical query must never return the referee or framing rows.
    hits = r.retrieve(lens="TACTICAL", query="shot anomaly", k=5)
    assert {h.citation_id for h in hits} == {"sb-1"}


def test_empty_when_lens_has_no_evidence(tmp_path):
    # Build an index with only referee evidence, query the historical lens -> empty.
    emb = _LensKeyedEmbedder()
    build_index(_citations()[:1], tmp_path / "lance", embedder=emb)
    r = LensRetriever(tmp_path / "lance", embedder=emb)
    assert r.retrieve(lens="HISTORICAL", query="anything", k=3) == []


def test_allow_list_excludes_out_of_incident_evidence(tmp_path):
    # F-C: an allow-list naming only sb-1 must exclude every other tactical hit.
    r = _retriever(tmp_path)
    hits = r.retrieve(lens="TACTICAL", query="shot anomaly", k=5,
                      allowed_citation_ids={"sb-1"})
    assert {h.citation_id for h in hits} == {"sb-1"}
    # an allow-list that names nothing in this lens yields no hits
    none = r.retrieve(lens="REFEREE", query="handball", k=5, allowed_citation_ids={"nope"})
    assert none == []


def test_retrieval_order_is_deterministic(tmp_path):
    # F-D: same index, same query -> identical id order across calls.
    r = _retriever(tmp_path)
    a = [h.citation_id for h in r.retrieve(lens="REFEREE", query="handball offence", k=5)]
    b = [h.citation_id for h in r.retrieve(lens="REFEREE", query="handball offence", k=5)]
    assert a == b
