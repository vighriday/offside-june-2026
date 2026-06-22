# OFFSIDE — Architecture

## One sentence

`engine/` (Python) runs Docling + per-lens retrieval + IBM Granite **at build time,
temperature 0**, and *writes* frozen JSON fixtures; `web/` (Next.js) *only reads*
those fixtures at runtime — no LLM, no Python, no vector store at deploy.

## The factory / vending-machine split

```
┌──────────────── BUILD TIME (one time, offline) ─────────────────┐
│  corpus/  ──▶  Docling ingest  ──▶  data/docling/ (page-cited)    │
│                       │                                          │
│                       ▼                                          │
│            granite-embedding ──▶ LanceDB (per-lens, frozen)      │
│                       │                                          │
│   StatsBomb (build-time pull, aggregates only) ──┐               │
│                       ▼                          ▼               │
│        4 lens agents ──▶ IBM Granite synthesis ──▶ THE SPLIT     │
│                       │   (temp 0, schema-locked, NO numbers)    │
│                       ▼                                          │
│              validate ──▶ fixtures/*.json  (frozen, dated, SHA)  │
└──────────────────────────────────────────────────────────────────┘
                                │   committed to the repo
                                ▼
┌──────────────── RUNTIME (Vercel, $0, reproducible) ──────────────┐
│   web/ (Next.js)  reads  fixtures/*.json  ──▶  renders THE SPLIT  │
│   No Ollama. No Granite. No Python. No LLM. Static + instant.     │
└──────────────────────────────────────────────────────────────────┘
```

## Why this shape

- **Reproducible.** The deployed app replays committed fixtures verbatim — re-running
  it produces byte-identical output. A judge can re-run it and get the same diagnostic
  every time. (Granite's local determinism is best-effort across machines, which is
  precisely *why* we freeze to disk rather than infer live.)
- **$0 at runtime.** No inference cost, no API keys, no cold-start model loads.
- **Trustworthy.** Every claim resolves to a page-numbered IFAB passage extracted by
  Docling. The reasoning schema cannot emit a number. Where evidence is absent, the
  diagnostic says `NOT_DOCUMENTED` rather than guessing.

## The evidence spine (click-to-source)

Docling extracts the IFAB Laws of the Game into structured JSON **preserving
`page_no` and bounding boxes** (not Markdown, which discards them). Each cited passage
becomes a `Citation { id, source_doc, page, bbox, extracted_text }`. In the UI, every
cell of THE SPLIT click-traces through its `citation_ids` to the exact source page —
rendered with the passage highlighted. This is the project's win condition, and it is
validated end-to-end in CI.

## The build host

The bake runs on a clean cloud machine (Google Colab) — Granite via Ollama,
Docling, and the embedding model all run there, once. The resulting fixtures + page
images are downloaded and committed. Nothing model-related is required on a
contributor's machine or on Vercel.

*This document expands with concrete module maps as each milestone lands.*
