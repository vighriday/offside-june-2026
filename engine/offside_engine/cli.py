"""The ``offside`` command-line interface for the build-time engine.

Each subcommand is one step of the bake. They are designed to be run in order on the
build host, writing intermediate artifacts that the next step reads.
"""

from __future__ import annotations

from pathlib import Path

import typer

from offside_engine.ingest.docling_extract import extract_pages
from offside_engine.ingest.persist import iter_citations, save_citations, save_document_json

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="OFFSIDE build-time engine — ingest evidence and bake frozen fixtures.",
)


@app.callback()
def _main() -> None:
    """OFFSIDE build-time engine.

    A callback keeps this a multi-command app, so each bake step is its own named
    subcommand (``ingest-laws``, and more to come) even while only one exists.
    """

# Repo-root-relative defaults (engine/ is one level below the repo root).
_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_PDF = _REPO / "corpus" / "ifab" / "ifab-laws-2025-26-single-pages.pdf"
_DEFAULT_OUT = _REPO / "data" / "docling"


@app.command("ingest-laws")
def ingest_laws(
    pdf: Path = typer.Option(_DEFAULT_PDF, help="Path to the IFAB Laws PDF."),
    start: int = typer.Option(..., help="First page to extract (1-indexed, inclusive)."),
    end: int = typer.Option(..., help="Last page to extract (1-indexed, inclusive)."),
    source_doc: str = typer.Option("ifab-laws-2025-26", help="Stable source-doc id."),
    out_dir: Path = typer.Option(_DEFAULT_OUT, help="Where to write the JSON artifacts."),
) -> None:
    """Extract a page range of the IFAB Laws into the evidence spine.

    Writes a lossless DoclingDocument JSON and a Citation index for the range. Scoping
    to a page range keeps memory bounded and matches how the Laws are actually cited.
    """
    typer.echo(f"Extracting {pdf.name} pages {start}-{end} ...")
    doc = extract_pages(pdf, (start, end), generate_page_images=True)

    doc_path = save_document_json(doc, out_dir / f"{source_doc}.p{start}-{end}.json")
    typer.echo(f"  wrote document  -> {doc_path.relative_to(_REPO)}")

    citations = list(iter_citations(doc, source_doc=source_doc, id_prefix=source_doc))
    cite_path = save_citations(citations, out_dir / f"{source_doc}.p{start}-{end}.citations.json")
    typer.echo(f"  wrote {len(citations):>3} citations -> {cite_path.relative_to(_REPO)}")

    pages = sorted({c.page for c in citations if c.page is not None})
    typer.echo(f"  pages with evidence: {pages}")


if __name__ == "__main__":  # pragma: no cover
    app()
