# OFFSIDE Engine

The build-time half of OFFSIDE. Python. Runs **once, offline**, on a clean build host
(Google Colab) — never on Vercel, never required to view the deployed app.

## What it does

1. **Ingest** — Docling extracts the IFAB Laws of the Game PDF into structured JSON,
   preserving page numbers and bounding boxes (the click-to-source spine).
2. **Index** — chunks are embedded with `granite-embedding` into a per-lens LanceDB
   index.
3. **Retrieve** — each lens (Referee, Tactical, Historical, Framing) pulls only its
   own evidence via metadata-filtered retrieval.
4. **Synthesize** — IBM Granite (`granite3.3:8b`, temperature 0) maps the lens
   evidence into THE SPLIT — four dimensions, each `PRESENT` / `WEAK` / `ABSENT` /
   `NOT_DOCUMENTED`, **never a number**, every claim citing a real page.
5. **Bake** — validated, dated, SHA-stamped JSON is written to `../fixtures/` and
   committed. The web app reads these verbatim.

## Setup

```bash
cd engine
uv sync                      # creates .venv, installs pinned deps
uv run pytest                # runs the contract + no-numbers tests
```

Granite runs via a local Ollama server on the build host:

```bash
ollama pull granite3.3:8b
ollama pull granite-embedding:30m
```

## The contract

The schema in `offside_engine/analyze/split_schema.py` is the single source of truth
shared with the web app (exported to TypeScript). Its defining property: the
Granite-facing models contain **no numeric field**, proven by
`tests/test_no_numbers_in_granite_schema.py`. Page numbers live only on `Citation`,
joined in by code after Granite runs.
