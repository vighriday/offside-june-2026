"""Docling extraction config — asserts the validated pipeline options, no model needed."""

from __future__ import annotations

from pathlib import Path

import pytest

from offside_engine.ingest.docling_extract import build_pipeline_options, extract_pages


def test_options_disable_ocr():
    # Born-digital PDF: OCR must stay off (determinism + reading order).
    assert build_pipeline_options().do_ocr is False


def test_options_keep_table_structure_accurate():
    from docling.datamodel.pipeline_options import TableFormerMode

    opts = build_pipeline_options()
    assert opts.do_table_structure is True
    assert opts.table_structure_options.mode == TableFormerMode.ACCURATE


def test_page_images_off_by_default_on_for_request():
    assert build_pipeline_options().generate_page_images is False
    assert build_pipeline_options(generate_page_images=True).generate_page_images is True


def test_extract_pages_validates_inputs():
    with pytest.raises(FileNotFoundError):
        extract_pages(Path("does-not-exist.pdf"), (1, 2))


def test_extract_pages_rejects_bad_range(tmp_path):
    pdf = tmp_path / "stub.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")  # existence is enough; range check runs first
    with pytest.raises(ValueError):
        extract_pages(pdf, (0, 3))
    with pytest.raises(ValueError):
        extract_pages(pdf, (5, 2))
