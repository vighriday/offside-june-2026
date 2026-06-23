"""The OFFSIDE bake as an executable LangGraph ``StateGraph``.

The pipeline used to be described as a Langflow diagram of sticky notes — a picture, not a
runnable flow. This is the real thing: a typed ``StateGraph`` whose nodes call the *same*
engine functions the bake uses (``run_lens`` → ``gate_lens`` per lens, then ``derive_split``
→ ``gate_cell`` → assemble), so the orchestration story is executable and tested, not an
annotation. ``build_bake_graph().compile()`` returns a graph you can ``.invoke(state)`` to
produce a real :class:`IncidentBundle`, and ``export_mermaid()`` renders the same graph to a
diagram for the README / Langflow canvas — one source of truth for picture and behaviour.

The graph is deliberately faithful to the documented division of labour: the four lens
nodes do the grounded NL reading (Granite) and each is audited (Granite Guardian); the
``route`` node applies the deterministic SPLIT rules; the ``gate_cells`` node runs the
per-cell Guardian audit; ``assemble`` freezes the bundle. Nothing here re-implements the
engine — it wires the existing, tested units into a graph.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.analyze.guardian_gate import gate_cell, gate_lens
from offside_engine.analyze.lens_runner import LensRun, run_lens
from offside_engine.analyze.split_schema import (
    BakeProvenance,
    Citation,
    IncidentBundle,
    LensKind,
    LensOutput,
    SealedCell,
    SealedLens,
    SettledFact,
    Split,
)
from offside_engine.bake.incident import IncidentSpec
from offside_engine.bake.synthesize import derive_split
from offside_engine.config import DEFAULT_EMBED_MODEL
from offside_engine.retrieve.lens_retrieve import LensRetriever

_LENS_ORDER: tuple[LensKind, ...] = ("REFEREE", "TACTICAL", "HISTORICAL", "FRAMING")


def _merge(a: dict, b: dict) -> dict:
    """Reducer for the parallel lens fan-out: merge each lens node's partial dict."""
    return {**a, **b}


class BakeState(TypedDict, total=False):
    """The state threaded through the bake graph.

    The four lens nodes run in parallel and each writes one entry into ``sealed`` and
    ``gated`` via the merge reducer; the downstream nodes read the merged result.
    """

    spec: IncidentSpec
    citations: dict[str, Citation]
    # per-lens results, keyed by lens; written concurrently, merged by the reducer
    sealed: Annotated[dict[str, SealedLens], _merge]
    gated: Annotated[dict[str, LensOutput], _merge]
    split: Split
    sealed_cells: list[SealedCell]
    bundle: IncidentBundle


class GraphDeps:
    """The live clients the graph nodes call — injected so the graph stays pure of config."""

    def __init__(
        self,
        *,
        retriever: LensRetriever,
        granite: GraniteClient,
        guardian: GuardianClient,
        embed_model: str = DEFAULT_EMBED_MODEL,
        corpus_git_sha: str | None = None,
    ) -> None:
        self.retriever = retriever
        self.granite = granite
        self.guardian = guardian
        self.embed_model = embed_model
        self.corpus_git_sha = corpus_git_sha


def _lens_node(lens: LensKind, deps: GraphDeps):
    """Build one lens node: retrieve → Granite read → Guardian audit, for ``lens``."""

    def node(state: BakeState) -> dict:
        spec = state["spec"]
        run: LensRun = run_lens(
            lens=lens,
            query=spec.lens_queries[lens],
            retriever=deps.retriever,
            granite=deps.granite,
            allowed_citation_ids=set(spec.allowed_citation_ids),
        )
        gated = gate_lens(run.output, citations=state["citations"], guardian=deps.guardian)
        return {
            "sealed": {lens: SealedLens(output=gated.output, seal=gated.seal)},
            "gated": {lens: gated.output},
        }

    return node


def _route_node(state: BakeState) -> dict:
    """Deterministic SPLIT routing over the gated lens outputs (in canonical lens order)."""
    spec = state["spec"]
    ordered = [state["gated"][lens] for lens in _LENS_ORDER if lens in state["gated"]]
    split = derive_split(ordered, admitted_act=bool(spec.admission_note))
    return {"split": split}


def _gate_cells_node(deps: GraphDeps):
    def node(state: BakeState) -> dict:
        split = state["split"]
        gated_cells = []
        sealed_cells: list[SealedCell] = []
        for cell in split.cells:
            gc = gate_cell(cell, citations=state["citations"], guardian=deps.guardian)
            gated_cells.append(gc.cell)
            sealed_cells.append(SealedCell(cell=gc.cell, seal=gc.seal))
        return {
            "split": Split(cells=gated_cells, headline=split.headline),
            "sealed_cells": sealed_cells,
        }

    return node


def _assemble_node(deps: GraphDeps):
    def node(state: BakeState) -> dict:
        spec = state["spec"]
        split = state["split"]
        sealed = [state["sealed"][lens] for lens in _LENS_ORDER if lens in state["sealed"]]

        settled = SettledFact(
            status=spec.settled_status,
            statement=spec.settled_statement,
            citation_ids=list(spec.settled_citation_ids),
        )
        referenced: set[str] = set(spec.settled_citation_ids)
        for sl in sealed:
            referenced.update(sl.output.citation_ids)
        for c in split.cells:
            referenced.update(c.citation_ids)
        bundle_citations = {
            cid: state["citations"][cid] for cid in referenced if cid in state["citations"]
        }
        provenance = BakeProvenance(
            granite_model=deps.granite.config.model,
            guardian_model=deps.guardian.model,
            embed_model=deps.embed_model,
            options=dict(deps.granite.options),
            corpus_git_sha=deps.corpus_git_sha,
        )
        bundle = IncidentBundle(
            incident_id=spec.incident_id,
            title=spec.title,
            settled_fact=settled,
            lenses=sealed,
            split=split,
            cell_seals=state["sealed_cells"],
            citations=bundle_citations,
            provenance=provenance,
        )
        return {"bundle": bundle}

    return node


def build_bake_graph(deps: GraphDeps) -> StateGraph:
    """Wire the bake into a ``StateGraph``: four parallel lens nodes → route → gate → assemble."""
    g: StateGraph = StateGraph(BakeState)

    for lens in _LENS_ORDER:
        g.add_node(f"lens_{lens.lower()}", _lens_node(lens, deps))
    g.add_node("route", _route_node)
    g.add_node("gate_cells", _gate_cells_node(deps))
    g.add_node("assemble", _assemble_node(deps))

    # fan out to the four lenses from START, then converge on route
    for lens in _LENS_ORDER:
        g.add_edge(START, f"lens_{lens.lower()}")
        g.add_edge(f"lens_{lens.lower()}", "route")
    g.add_edge("route", "gate_cells")
    g.add_edge("gate_cells", "assemble")
    g.add_edge("assemble", END)
    return g


def run_bake_graph(spec: IncidentSpec, *, deps: GraphDeps,
                   citations: dict[str, Citation]) -> IncidentBundle:
    """Compile and invoke the graph for one incident, returning its frozen bundle."""
    app = build_bake_graph(deps).compile()
    final: dict[str, Any] = app.invoke({"spec": spec, "citations": citations})
    return final["bundle"]


def export_mermaid() -> str:
    """Render the compiled graph to a Mermaid diagram string (no live clients needed).

    Uses a stub deps object — only the graph *shape* is needed to draw it, so no model is
    called. This is the single source of truth behind the README orchestration diagram.
    """
    stub = GraphDeps.__new__(GraphDeps)  # shape-only; nodes are never invoked here
    app = build_bake_graph(stub).compile()
    return app.get_graph().draw_mermaid()


if __name__ == "__main__":
    print(export_mermaid())
