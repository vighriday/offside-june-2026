"""Run the REAL engine, live, on one incident — the "this is a system, not six frozen
answers" proof.

The deployed site reads frozen fixtures (no GPU on static hosting). This script is the
other half: it runs the *actual* four-model pipeline end to end on a chosen incident and
narrates every step, so a viewer watches the engine think rather than replay a recording:

  retrieve (per-lens, incident-scoped)  →  Granite reads each lens  →  Granite Guardian
  audits each reading  →  the gated evidence is routed onto THE SPLIT  →  Guardian audits
  each PRESENT/WEAK cell  →  the derived SPLIT prints, with the documented thesis as a
  post-hoc check (never an input).

It needs Ollama running with the three IBM models (granite3.3:8b, granite-embedding:30m,
granite3-guardian:2b). Point it at any of the committed incidents:

    python scripts/analyze_live.py --incident offside-margin
    python scripts/analyze_live.py --list

This is what you screen-record for the demo: pick an incident the engine has never been
"told" the answer to, and watch the four axes fall out of the evidence in real time.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.analyze.split_schema import Citation
from offside_engine.bake.bake import bake_incident
from offside_engine.bake.corpus_pool import assemble_pool
from offside_engine.bake.incident import INCIDENTS, IncidentSpec
from offside_engine.config import DEFAULT_EMBED_MODEL, DEFAULT_GUARDIAN_MODEL, load_granite_config
from offside_engine.eval.groundedness import score_bundle, write_report
from offside_engine.index.build_lance import build_index
from offside_engine.orchestrate.graph import GraphDeps, run_bake_graph
from offside_engine.retrieve.lens_retrieve import LensRetriever
from offside_engine.statsbomb.pull_aggregates import HandOfGodAggregate

_REPO = Path(__file__).resolve().parents[2]

# A frozen StatsBomb summary so the pool assembles fully offline (only the Hand of God
# tactical anomaly is real data; every other incident's tactical lens is insufficient).
_AGG = HandOfGodAggregate(
    match_id=3750191, scoreline="Argentina 2 - 1 England",
    maradona_total_shots=3, maradona_goals=2,
    hand_of_god_minute=50, hand_of_god_body_part="Other",
    second_goal_minute=54, second_goal_body_part="Left Foot",
    anomaly_present=True, three_sixty_available=False,
)

# ANSI for a readable live narration; degrade to plain if the terminal can't take it.
_BOLD, _DIM, _GRN, _YEL, _CYN, _RST = "\033[1m", "\033[2m", "\033[32m", "\033[33m", "\033[36m", "\033[0m"


def _say(msg: str = "") -> None:
    print(msg, flush=True)


def _corpus(slug: str) -> tuple[Path, Path]:
    return (
        _REPO / "corpus" / "framing" / slug / "sources.yaml",
        _REPO / "corpus" / "historical" / slug / "record.yaml",
    )


# An incident_id maps to its corpus folder slug (the fixture id carries a year suffix the
# corpus folder does not).
_SLUG = {
    "hand-of-god-1986": "hand-of-god",
    "suarez-handball-2010": "suarez-handball",
    "lampard-ghost-goal-2010": "lampard-ghost-goal",
    "handball-rewrite": "handball-rewrite",
    "offside-margin": "offside-margin",
    "pgmol-subjective": "pgmol-subjective",
}


def _full_pool() -> dict[str, Citation]:
    """Assemble the union of every incident's evidence into one pool to index against."""
    pool: dict[str, Citation] = {}
    for slug in dict.fromkeys(_SLUG.values()):
        fr, hist = _corpus(slug)
        for cid, c in assemble_pool(framing_yaml=fr, historical_yaml=hist, aggregate=_AGG).items():
            pool.setdefault(cid, c)
    return pool


def _print_split(bundle) -> None:
    _say(f"\n{_BOLD}THE SPLIT — {bundle.title}{_RST}")
    _say(f"{_DIM}{bundle.split.headline}{_RST}\n")
    for cell in bundle.split.cells:
        mark = {"PRESENT": f"{_GRN}● PRESENT{_RST}", "WEAK": f"{_YEL}◐ WEAK{_RST}",
                "ABSENT": f"{_DIM}○ ruled out{_RST}",
                "NOT_DOCUMENTED": f"{_DIM}· not documented{_RST}"}[cell.state]
        _say(f"  {cell.axis:<22} {mark}")
        _say(f"  {_DIM}{cell.rationale}{_RST}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the real OFFSIDE engine live on one incident.")
    ap.add_argument("--incident", help="incident id (see --list)")
    ap.add_argument("--list", action="store_true", help="list available incidents and exit")
    ap.add_argument("--graph", action="store_true",
                    help="run through the executable LangGraph StateGraph (same engine)")
    ap.add_argument("--ragas", action="store_true",
                    help="also score lens groundedness with RAGAS (needs the [eval] extra)")
    args = ap.parse_args()

    if args.list or not args.incident:
        _say(f"{_BOLD}Available incidents:{_RST}")
        for iid, spec in INCIDENTS.items():
            _say(f"  {iid:<24} {spec.title}")
        if not args.incident:
            _say("\nrun: python scripts/analyze_live.py --incident <id>")
        return

    spec: IncidentSpec | None = INCIDENTS.get(args.incident)
    if spec is None:
        sys.exit(f"unknown incident '{args.incident}' — run --list")

    cfg = load_granite_config()
    _say(f"{_CYN}OFFSIDE — live engine{_RST}")
    _say(f"{_DIM}Granite {cfg.model}  ·  Guardian {DEFAULT_GUARDIAN_MODEL}  ·  host {cfg.host}{_RST}")
    _say(f"\nIncident: {_BOLD}{spec.title}{_RST}")
    _say(f"{_DIM}The engine has NOT been told the answer — it reads the evidence and routes it.{_RST}\n")

    _say(f"{_DIM}· assembling the evidence pool and building the per-lens index "
         f"(granite-embedding)…{_RST}")
    pool = _full_pool()
    with tempfile.TemporaryDirectory() as tmp:
        db_dir = Path(tmp) / "lance"
        n = build_index(list(pool.values()), db_dir)
        _say(f"{_DIM}· indexed {n} evidence atoms across four lenses{_RST}")

        retriever = LensRetriever(db_dir)
        granite = GraniteClient(cfg)
        guardian = GuardianClient(host=cfg.host, model=DEFAULT_GUARDIAN_MODEL)

        try:
            sha = subprocess.check_output(
                ["git", "-C", str(_REPO), "rev-parse", "HEAD"]
            ).decode().strip()
        except Exception:
            sha = None

        if args.graph:
            _say(f"\n{_DIM}· running the LangGraph StateGraph "
                 f"(4 lens nodes → route → gate → assemble)…{_RST}")
            deps = GraphDeps(retriever=retriever, granite=granite, guardian=guardian,
                             embed_model=DEFAULT_EMBED_MODEL, corpus_git_sha=sha)
            bundle = run_bake_graph(spec, deps=deps, citations=pool)
        else:
            _say(f"\n{_DIM}· running four lenses (Granite reads each, Guardian audits each)…{_RST}")
            bundle = bake_incident(
                spec, retriever=retriever, granite=granite, guardian=guardian,
                citations=pool, corpus_git_sha=sha, strict_thesis=False,
            )

    # Narrate the audited lens readings, then the routed SPLIT.
    _say(f"\n{_BOLD}Lens readings (each audited by Granite Guardian):{_RST}")
    for sl in bundle.lenses:
        o, seal = sl.output, sl.seal
        verdict = f"{_GRN}GROUNDED{_RST}" if seal.verdict == "GROUNDED" else f"{_YEL}{seal.verdict}{_RST}"
        cited = ", ".join(o.citation_ids) if o.citation_ids else "—"
        _say(f"  {o.lens:<11} {o.stance:<22} Guardian: {verdict}")
        _say(f"  {_DIM}cites: {cited}{_RST}")

    _print_split(bundle)
    _say(f"{_DIM}Every PRESENT/WEAK cell above survived a Granite Guardian groundedness "
         f"audit against its cited source. No number was produced anywhere.{_RST}")

    # Build-time audit: score how grounded each lens reading is, written to a report. These
    # numbers are an external audit of the pipeline — they never enter THE SPLIT or the UI.
    rows = score_bundle(bundle, use_ragas=args.ragas)
    out_dir = _REPO / "engine" / "data" / "eval"
    jp, mp = write_report(rows, out_dir)
    grounded = sum(1 for r in rows if r.groundedness >= 0.999)
    backend = rows[0].backend if rows else "deterministic"
    _say(f"\n{_DIM}· groundedness audit ({backend}): {grounded}/{len(rows)} lens readings "
         f"fully grounded → {mp}{_RST}")


if __name__ == "__main__":
    main()
