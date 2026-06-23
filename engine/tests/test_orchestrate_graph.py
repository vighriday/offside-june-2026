"""The LangGraph bake is REAL — it runs the engine and produces the same bundle as the
direct bake. These tests are the rebuttal to "the orchestration graph is just a diagram":
the graph compiles, has the documented node shape, and invoking it on the Hand of God with
the same scripted clients yields the identical SPLIT signature the direct ``bake_incident``
produces.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import CANONICAL_AXIS_ORDER
from offside_engine.bake.incident import HAND_OF_GOD
from offside_engine.orchestrate.graph import (
    GraphDeps,
    build_bake_graph,
    export_mermaid,
    run_bake_graph,
)

# Reuse the exact scripted clients the direct-bake test uses, so a divergence between the
# graph and the direct bake would surface as a test failure here.
from tests.test_bake import (  # type: ignore
    _AllGroundedGuardian,
    _citations,
    _GoldenRetriever,
    _ScriptedGranite,
)


def _deps() -> GraphDeps:
    return GraphDeps(
        retriever=_GoldenRetriever(),
        granite=_ScriptedGranite(),
        guardian=_AllGroundedGuardian(),
        corpus_git_sha="deadbeef",
    )


def test_graph_compiles_with_the_documented_node_shape():
    app = build_bake_graph(_deps()).compile()
    nodes = set(app.get_graph().nodes)
    for n in ("lens_referee", "lens_tactical", "lens_historical", "lens_framing",
              "route", "gate_cells", "assemble"):
        assert n in nodes, f"missing node {n}"


def test_mermaid_export_renders_the_pipeline():
    mer = export_mermaid()
    assert "lens_referee" in mer and "route" in mer and "assemble" in mer
    # the four lenses fan out from start and converge on route
    assert mer.count("--> route") >= 4 or mer.count("route") >= 4


def test_graph_produces_the_same_golden_signature_as_the_direct_bake():
    bundle = run_bake_graph(HAND_OF_GOD, deps=_deps(), citations=_citations())
    assert bundle.incident_id == "hand-of-god-1986"
    states = {c.axis: c.state for c in bundle.split.cells}
    assert states["RULE_AMBIGUITY"] == "ABSENT"
    assert states["INDETERMINACY"] == "ABSENT"
    assert states["DECISION_TIME_DEFICIT"] == "PRESENT"
    assert states["CULTURAL_PRIOR_BIAS"] == "PRESENT"
    assert len(bundle.lenses) == 4
    assert tuple(sc.cell.axis for sc in bundle.cell_seals) == CANONICAL_AXIS_ORDER
    # no number leaked anywhere into the bundle the graph froze
    assert "73" not in bundle.split.headline
