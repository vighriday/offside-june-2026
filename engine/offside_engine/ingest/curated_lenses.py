"""Load curated Historical and Framing evidence into typed Citations.

The Historical and Framing lenses have no live source — their evidence is hand-curated
into YAML under ``corpus/``. This module turns those files into the same
:class:`~offside_engine.analyze.split_schema.Citation` shape the rest of the pipeline
uses, so curated evidence flows through retrieval and THE SPLIT identically to the
Docling-extracted Laws.

The Framing loader enforces the anti-stereotyping rule structurally: it carries each
framing's named ``speaker``, ``date``, and an ``is_from`` vs ``characterizes`` relation,
and never a "what a nation believes" field.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from offside_engine.analyze.split_schema import Citation


def load_framing_citations(sources_yaml: Path) -> list[Citation]:
    """Load named-source framings into Citations (doc_kind FRAMING_SOURCE)."""
    data = yaml.safe_load(sources_yaml.read_text(encoding="utf-8"))
    citations: list[Citation] = []
    for f in data.get("framings", []):
        speaker = f["speaker"]
        date = f.get("date", "")
        quote = " ".join(f.get("quote", "").split())
        text = f"{speaker} ({date}) — {f.get('stance','')}: {quote}"
        citations.append(
            Citation(
                id=f["id"],
                source_doc=f.get("source", "framing"),
                doc_kind="FRAMING_SOURCE",
                page=None,
                extracted_text=text,
                attribution=f"{speaker}, {f.get('source','')} ({date})",
            )
        )
    return citations


def load_historical_citations(record_yaml: Path) -> list[Citation]:
    """Load curated historical facts into Citations (doc_kind HISTORICAL_REPORT)."""
    data = yaml.safe_load(record_yaml.read_text(encoding="utf-8"))
    title = data.get("title", "")
    citations: list[Citation] = []
    for fact in data.get("facts", []):
        text = " ".join(fact["statement"].split())
        citations.append(
            Citation(
                id=fact["id"],
                source_doc="curated-historical",
                doc_kind="HISTORICAL_REPORT",
                page=None,
                extracted_text=text,
                attribution=f"Curated historical record — {title}",
            )
        )
    return citations
