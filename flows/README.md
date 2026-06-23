# Orchestration — the OFFSIDE bake pipeline

The bake is orchestrated as an **executable LangGraph `StateGraph`**
([`engine/offside_engine/orchestrate/graph.py`](../engine/offside_engine/orchestrate/graph.py)):
four lens nodes fan out in parallel (each: retrieve → Granite reads → Granite Guardian
audits), converge on a deterministic `route` node, pass a per-cell Guardian `gate_cells`
node, and `assemble` the frozen bundle. It is not a diagram of the pipeline — it *is* the
pipeline: `run_bake_graph(spec, ...)` returns a real `IncidentBundle`, and a test
(`tests/test_orchestrate_graph.py`) asserts the graph produces the identical golden SPLIT as
the direct bake. The rendered graph below is generated from that compiled graph
([`bake_graph.mmd`](bake_graph.mmd)) — one source of truth for the picture and the behaviour.

```text
IBM Docling ─▶ Granite Embedding + LanceDB ─┬▶ Referee lens   (Granite) ─┐
                                            ├▶ Tactical lens  (Granite) ─┤
                                            ├▶ Historical lens(Granite) ─┼▶ Granite Guardian ─▶ THE SPLIT ─▶ Frozen fixture
                                            └▶ Framing lens   (Granite) ─┘   (groundedness gate)   (routing)
```

A Langflow canvas of the same stages is also provided as
[`offside_pipeline.json`](offside_pipeline.json) for visual import. Both mirror the exact
stages the engine runs at bake time:

```text
IBM Docling ─▶ Granite Embedding + LanceDB ─┬▶ Referee lens   (Granite) ─┐
                                            ├▶ Tactical lens  (Granite) ─┤
                                            ├▶ Historical lens(Granite) ─┼▶ Granite Guardian ─▶ THE SPLIT ─▶ Frozen fixture
                                            └▶ Framing lens   (Granite) ─┘   (groundedness gate)   (routing)
```

Every node is a real stage in the engine:

| Pipeline stage | LangGraph node | Engine code |
|----------------|----------------|-------------|
| IBM Docling — evidence extraction | (build-time, pre-graph) | `ingest/docling_extract.py`, `ingest/curate.py` |
| Granite Embedding + LanceDB | (build-time, pre-graph) | `index/embed.py`, `index/build_lance.py` |
| Four lens readings (Granite) + audit (Guardian) | `lens_referee` / `lens_tactical` / `lens_historical` / `lens_framing` | `analyze/lens_runner.py`, `analyze/guardian_gate.py` |
| THE SPLIT — deterministic routing | `route` | `bake/synthesize.py` |
| Per-cell groundedness gate (Guardian) | `gate_cells` | `analyze/guardian_gate.py` |
| Frozen IncidentBundle | `assemble` | `orchestrate/graph.py`, `bake/write_fixture.py` |

## Run / render it

```bash
python -m offside_engine.orchestrate.graph     # prints the Mermaid graph (no models needed)
```

`run_bake_graph(spec, deps=…, citations=…)` executes the full pipeline and returns a real
`IncidentBundle`. A Langflow canvas of the same stages imports from `offside_pipeline.json`
(**New Project → Import**). The deterministic bake (`engine/bake.ipynb`,
`scripts/analyze_live.py`) runs the same stages end to end at temperature 0.
