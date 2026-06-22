"""Persist layer — Citation building and JSON round-trip, with lightweight fakes.

These tests do not load Docling models. They exercise the provenance→Citation logic
against minimal fakes shaped like Docling items, and the JSON persistence against the
real schema. A full round-trip over the actual IFAB PDF is exercised by the ingest CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from offside_engine.analyze.split_schema import Bbox, Citation
from offside_engine.ingest.persist import iter_citations, save_citations


# ── Fakes shaped like the bits of DoclingDocument that iter_citations touches ──


@dataclass
class _FakeBbox:
    # field names mirror Docling's real BoundingBox attributes (l/t/r/b)
    l: float  # noqa: E741
    t: float
    r: float
    b: float

    def to_top_left_origin(self, page_height):
        # mimic Docling: flip vertically about the page height
        return _FakeBbox(self.l, page_height - self.t, self.r, page_height - self.b)


@dataclass
class _FakeProv:
    page_no: int
    bbox: _FakeBbox | None = None


@dataclass
class _FakeItem:
    text: str
    prov: list = field(default_factory=list)
    label: str = "text"


@dataclass
class _FakeSize:
    height: float


@dataclass
class _FakePage:
    size: _FakeSize


class _FakeDoc:
    def __init__(self, items, pages):
        self._items = items
        self.pages = pages

    def iterate_items(self):
        for it in self._items:
            yield it, 0


def _doc():
    return _FakeDoc(
        items=[
            _FakeItem("OFFSIDE", prov=[_FakeProv(74, _FakeBbox(10, 700, 200, 680))]),
            _FakeItem("A handball offence is committed if a player deliberately touches the ball",
                      prov=[_FakeProv(152, _FakeBbox(60, 500, 380, 470))]),
            _FakeItem("", prov=[_FakeProv(152)]),                 # empty text -> skipped
            _FakeItem("no provenance", prov=[]),                  # no prov -> skipped
        ],
        pages={74: _FakePage(_FakeSize(792)), 152: _FakePage(_FakeSize(792))},
    )


def test_iter_citations_skips_empty_and_unprovenanced():
    cites = list(iter_citations(_doc(), source_doc="ifab-laws-2025-26"))
    assert len(cites) == 2  # the empty and the no-prov items are skipped


def test_citation_ids_are_stable_and_readable():
    cites = list(iter_citations(_doc(), source_doc="ifab-laws-2025-26", id_prefix="ifab"))
    ids = [c.id for c in cites]
    assert ids == ["ifab-p74-0", "ifab-p152-0"]


def test_citation_carries_page_text_and_bbox():
    cites = list(iter_citations(_doc(), source_doc="ifab-laws-2025-26"))
    law12 = next(c for c in cites if c.page == 152)
    assert "handball offence" in law12.extracted_text
    assert isinstance(law12.bbox, Bbox)
    # top-left conversion flipped about page height 792
    assert law12.bbox.top == 792 - 500


def test_save_citations_writes_id_keyed_index(tmp_path):
    cites = [
        Citation(id="ifab-law12-p152", source_doc="ifab-laws-2025-26", doc_kind="IFAB_LAW",
                 page=152, extracted_text="handball"),
    ]
    out = save_citations(cites, tmp_path / "citations.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "ifab-law12-p152" in payload
    assert payload["ifab-law12-p152"]["page"] == 152
