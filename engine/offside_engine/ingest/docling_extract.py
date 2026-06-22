"""Docling extraction of the IFAB Laws PDF — the evidence spine.

Configuration here is not arbitrary; each setting was validated against the real IFAB
single-pages PDF during the ingest spike:

* ``do_ocr=False`` — the PDF is born-digital. OCR adds non-determinism and worsens the
  reading order, and we never want it for a text-layer document.
* ``TableFormerMode.ACCURATE`` — the Laws contain disciplinary tables whose structure
  must survive.
* ``page_range`` — converting all ~230 pages at once exhausts memory on a modest
  machine. We only ever need the handful of pages a Law is cited from, so extraction
  is scoped to a page range. This is also the curated-pages pattern: process exactly
  what is cited, nothing more.

The output keeps Docling's provenance (``page_no`` + bounding box) on every item,
which is the spine the click-to-source feature resolves against. We never go through
Markdown, which would discard that provenance.
"""

from __future__ import annotations

from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DoclingDocument


def build_pipeline_options(
    *, generate_page_images: bool = False, images_scale: float = 2.0
) -> PdfPipelineOptions:
    """The OFFSIDE-validated Docling pipeline options for the IFAB PDF.

    Exposed separately so the configuration can be asserted without constructing a
    full converter (which would load Docling's models).
    """
    options = PdfPipelineOptions(
        do_ocr=False,
        do_table_structure=True,
        generate_page_images=generate_page_images,
        images_scale=images_scale,
    )
    options.table_structure_options.mode = TableFormerMode.ACCURATE
    return options


def build_converter(*, generate_page_images: bool = False, images_scale: float = 2.0) -> DocumentConverter:
    """Construct a DocumentConverter with the OFFSIDE-validated pipeline options.

    ``generate_page_images`` is off by default — page images are rendered separately,
    only for the cited pages, to keep memory bounded. Turn it on for a small page
    range when you need the rendered page for the click-to-source viewer.
    """
    options = build_pipeline_options(
        generate_page_images=generate_page_images, images_scale=images_scale
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def extract_pages(
    pdf_path: Path,
    page_range: tuple[int, int],
    *,
    generate_page_images: bool = False,
) -> DoclingDocument:
    """Extract a 1-indexed, inclusive page range from a PDF into a DoclingDocument.

    Scoping to a page range keeps memory bounded and matches how the engine actually
    cites the Laws — by a specific Law on a specific page.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"source PDF not found: {pdf_path}")
    start, end = page_range
    if start < 1 or end < start:
        raise ValueError(f"invalid page_range {page_range}: expected 1 <= start <= end")

    converter = build_converter(generate_page_images=generate_page_images)
    result = converter.convert(str(pdf_path), page_range=page_range)
    return result.document
