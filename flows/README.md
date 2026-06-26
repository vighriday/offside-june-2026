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
[`offside_pipeline.json`](offside_pipeline.json) — a **visual reference** you can import
(**New Project → Import**) to see the orchestration as a labelled board. The *executable*
orchestration is the LangGraph `StateGraph` above (it runs and is tested); the Langflow
canvas is the human-readable map of the same stages:

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
| Live falsification probes (self-attack) | (post-assemble, centerpiece incident) | `bake/probe.py`, `bake/probe_specs.py`, `bake/integrity.py` |
| Frozen IncidentBundle | `assemble` | `orchestrate/graph.py`, `bake/write_fixture.py` |

After assembly, the centerpiece incident (the millimetre offside line) is re-run through
three **live falsification probes** through the same Granite + Granite Guardian models —
**FLIP** (new evidence moves the axis), **NOISE** (irrelevant input does nothing), and
**OVERREACH** (Granite Guardian returns a real `UNGROUNDED` and overrules the first model).
A CI integrity lock ([`bake/integrity.py`](../engine/offside_engine/bake/integrity.py)) fails
the build if any probe verdict is hand-authored or did not behave as its kind requires, so the
self-attack cannot be faked. This is the engine proving — on camera, through the second IBM
model — that its diagnosis is reasoned, not a stored lookup.

## Run / render it

```bash
python -m offside_engine.orchestrate.graph     # prints the Mermaid graph (no models needed)
```

`run_bake_graph(spec, deps=…, citations=…)` executes the full pipeline and returns a real
`IncidentBundle`. A Langflow canvas of the same stages imports from `offside_pipeline.json`
(**New Project → Import**). The deterministic bake (`engine/bake.ipynb`,
`scripts/analyze_live.py`) runs the same stages end to end at temperature 0.
