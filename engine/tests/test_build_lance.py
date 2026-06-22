"""Per-lens index building — lens assignment and a real LanceDB round-trip (mocked embed)."""

from __future__ import annotations

import pytest

from offside_engine.analyze.split_schema import Citation
from offside_engine.index.build_lance import (
    TABLE_NAME,
    build_index,
    rows_from_citations,
)
from offside_engine.index.embed import EMBED_DIM


class _FakeEmbedder:
    def embed(self, texts):
        return [[0.1] * EMBED_DIM for _ in texts]


def _citations():
    return [
        Citation(id="ifab-1", source_doc="ifab", doc_kind="IFAB_LAW", page=118,
                 extracted_text="deliberate handball denies a goal"),
        Citation(id="sb-1", source_doc="statsbomb", doc_kind="STATSBOMB_EVENT", page=None,
                 extracted_text="shot body_part Other at minute 51"),
        Citation(id="fr-1", source_doc="framing", doc_kind="FRAMING_SOURCE", page=None,
                 extracted_text="the hand of God"),
    ]


def test_each_citation_maps_to_the_right_lens():
    rows = {r.citation_id: r.lens for r in rows_from_citations(_citations())}
    assert rows == {"ifab-1": "REFEREE", "sb-1": "TACTICAL", "fr-1": "FRAMING"}


def test_var_protocol_is_dropped_not_routed_to_referee():
    # F-B: the 2026 VAR review procedure says nothing about whether a Law is clear,
    # so it must NOT feed the Referee lens. It maps to None and produces no row.
    c = Citation(id="x", source_doc="s", doc_kind="VAR_PROTOCOL", page=1, extracted_text="t")
    assert rows_from_citations([c]) == []


def test_build_index_writes_a_queryable_table(tmp_path):
    n = build_index(_citations(), tmp_path / "lance", embedder=_FakeEmbedder())
    assert n == 3

    import lancedb

    db = lancedb.connect(str(tmp_path / "lance"))
    tbl = db.open_table(TABLE_NAME)
    assert tbl.count_rows() == 3
    # the lens + citation_id metadata is present for retrieval filtering
    cols = set(tbl.schema.names)
    assert {"vector", "citation_id", "lens", "page", "text"} <= cols


def test_build_index_rejects_empty(tmp_path):
    with pytest.raises(ValueError):
        build_index([], tmp_path / "lance", embedder=_FakeEmbedder())
