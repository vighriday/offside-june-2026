# Contributing to OFFSIDE

## Repository shape

OFFSIDE is a monorepo with a hard one-way boundary:

```
engine/  ──writes──▶  fixtures/ + data/  ──reads──▶  web/
```

- **`engine/`** (Python) runs Docling, per-lens retrieval, and IBM Granite **once, at
  build time, at temperature 0**, and *writes* frozen JSON fixtures.
- **`web/`** (Next.js) *only reads* those committed fixtures at runtime. There is no
  LLM, no Python, and no vector store at deploy time.

The engine never imports the web; the web never imports the engine. They are coupled
only by the versioned JSON contract in `fixtures/`. This is what makes the deployed
app reproducible and $0 to run.

## The bake is offline and frozen

Granite output is generated on a build host (a clean cloud machine), validated,
dated, SHA-stamped, and committed. The deployed app replays these fixtures verbatim —
re-running it produces byte-identical output every time. Do not wire any live model
call into `web/`.

## Two rules that are never bent

1. **Granite may never emit a number.** The reasoning schema contains no numeric
   field; a CI test proves it structurally. Confidence, magnitude, and percentage are
   all banned. State is qualitative (`PRESENT` / `WEAK` / `ABSENT` / `NOT_DOCUMENTED`)
   and every claim cites a real source.
2. **Raw StatsBomb data is never committed.** Pull it at build time, keep only derived
   aggregates, and show the StatsBomb attribution wherever Tactical evidence renders.
   See LICENSES.md.

## Commit convention

[Conventional Commits](https://www.conventionalcommits.org/). Types in use:
`feat`, `fix`, `docs`, `chore`, `build`, `ci`, `test`, `refactor`. Optional scope in
parentheses (`feat(engine):`, `feat(web):`, `feat(fixtures):`).

Each commit is atomic, carries a clear message, and leaves the repository in a
building state.

## Local setup

- **Engine:** [uv](https://docs.astral.sh/uv/) + Python 3.12 — `cd engine && uv sync`.
- **Web:** Node 22 — `cd web && npm install && npm run dev`.

Detailed setup lands in the README as each half comes online.
