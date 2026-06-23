# Langflow — the OFFSIDE pipeline

[`offside_pipeline.json`](offside_pipeline.json) is the OFFSIDE bake orchestration as a
Langflow graph. It mirrors the exact stages the engine runs at bake time:

```text
IBM Docling ─▶ Granite Embedding + LanceDB ─┬▶ Referee lens   (Granite) ─┐
                                            ├▶ Tactical lens  (Granite) ─┤
                                            ├▶ Historical lens(Granite) ─┼▶ Granite Guardian ─▶ THE SPLIT ─▶ Frozen fixture
                                            └▶ Framing lens   (Granite) ─┘   (groundedness gate)   (routing)
```

Every node is a real stage in [`engine/offside_engine/bake/`](../engine/offside_engine/bake/):

| Langflow node | Engine code |
|---------------|-------------|
| IBM Docling — Evidence Extraction | `ingest/docling_extract.py`, `ingest/curate.py` |
| Granite Embedding + LanceDB | `index/embed.py`, `index/build_lance.py` |
| Four lens readings (Granite) | `analyze/lens_runner.py`, `analyze/prompts.py` |
| Granite Guardian — Groundedness Gate | `analyze/guardian.py`, `analyze/guardian_gate.py` |
| THE SPLIT — Deterministic Routing | `bake/synthesize.py` |
| Frozen IncidentBundle | `bake/write_fixture.py` |

## Import it

In Langflow: **New Project → Import → upload `offside_pipeline.json`**. The canvas renders
the eight stages and their flow, left to right. It is a faithful visual of the pipeline;
the executable, tested implementation is the Python engine, run deterministically at bake
time (see `engine/bake.ipynb`).
