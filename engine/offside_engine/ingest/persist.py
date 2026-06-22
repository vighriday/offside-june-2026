"""Persist Docling output losslessly and turn its provenance into Citations.

Two responsibilities:

1. **Lossless round-trip.** Save a ``DoclingDocument`` as JSON and load it back without
   going through Markdown — Markdown would discard ``page_no`` and bounding boxes, which
   are the click-to-source spine.
2. **Provenance → Citation.** Walk the document's items and emit typed
   :class:`~offside_engine.analyze.split_schema.Citation` atoms, each carrying a stable
   id, page number, bounding box, and the extracted text of the passage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from docling_core.types.doc import DoclingDocument

from offside_engine.analyze.split_schema import Bbox, Citation, DocKind


def save_document_json(doc: DoclingDocument, out_path: Path) -> Path:
    """Persist a DoclingDocument as lossless JSON (never Markdown)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def load_document_json(path: Path) -> DoclingDocument:
    """Reload a DoclingDocument from its lossless JSON, no model reload required."""
    return DoclingDocument.model_validate_json(path.read_text(encoding="utf-8"))


def _bbox_top_left(prov, page_height: float | None) -> Bbox | None:
    """Convert a Docling provenance bbox to a top-left-origin Bbox for the web viewer.

    Docling stores bboxes bottom-left-origin by default; the UI overlays top-left, so
    we flip vertically when the page height is known.
    """
    raw = getattr(prov, "bbox", None)
    if raw is None:
        return None
    converted = raw.to_top_left_origin(page_height) if page_height else raw
    return Bbox(left=converted.l, top=converted.t, right=converted.r, bottom=converted.b)


def _page_heights(doc: DoclingDocument) -> dict[int, float]:
    heights: dict[int, float] = {}
    for page_no, page in getattr(doc, "pages", {}).items():
        size = getattr(page, "size", None)
        if size is not None:
            heights[page_no] = size.height
    return heights


def iter_citations(
    doc: DoclingDocument,
    *,
    source_doc: str,
    doc_kind: DocKind = "IFAB_LAW",
    id_prefix: str | None = None,
) -> Iterator[Citation]:
    """Yield a Citation for every text-bearing, provenanced item in the document.

    Citation ids are stable and human-readable: ``<prefix>-p<page>-<n>`` so a reviewer
    can read where a citation points from its id alone.
    """
    prefix = id_prefix or source_doc
    heights = _page_heights(doc)
    per_page_counter: dict[int, int] = {}

    for item, _level in doc.iterate_items():
        text = (getattr(item, "text", "") or "").strip()
        if not text:
            continue
        provs = getattr(item, "prov", []) or []
        if not provs:
            continue
        prov = provs[0]
        page = getattr(prov, "page_no", None)
        if page is None:
            continue

        n = per_page_counter.get(page, 0)
        per_page_counter[page] = n + 1
        label = getattr(item, "label", "")
        kind: DocKind = "TABLE_CELL" if label == "table" else doc_kind

        yield Citation(
            id=f"{prefix}-p{page}-{n}",
            source_doc=source_doc,
            doc_kind=kind,
            page=page,
            bbox=_bbox_top_left(prov, heights.get(page)),
            extracted_text=text,
        )


def save_citations(citations: list[Citation], out_path: Path) -> Path:
    """Persist a list of Citations as a JSON index keyed by id."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {c.id: c.model_dump(mode="json") for c in citations}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
