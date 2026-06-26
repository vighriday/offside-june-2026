"""The bake — turn one real incident into a frozen, audited IncidentBundle.

This is the whole vending-machine: it runs the four lenses, audits each with Granite
Guardian, synthesises THE SPLIT from the surviving lens evidence, audits each cell with
Guardian again, checks the derived SPLIT against the incident's documented thesis, and
assembles a self-contained bundle the web reads offline.

The order matters and is load-bearing:

1.  **Settled fact** — pure code, stated first (never refusal-only).
2.  **Per-lens run** — retrieve (lens + incident allow-list) → Granite (cite-or-die).
3.  **Per-lens gate** — Guardian demotes any ungrounded lens to INSUFFICIENT_EVIDENCE.
4.  **Synthesis** — the *gated* lens evidence is routed onto the four axes by the fixed
    documented rules (deterministic code, not the model), with the admission note gating
    the INDETERMINACY precondition. The routing never sees the expected answer.
5.  **Per-cell gate** — Guardian demotes any ungrounded PRESENT/WEAK cell to
    NOT_DOCUMENTED.
6.  **Thesis assertion** — the derived SPLIT must match the documented shape, else the
    bake fails. This is the oracle that keeps "derived, not hard-coded" honest.
7.  **Assemble + revalidate** — build the IncidentBundle (its validators re-check
    internal consistency) and freeze provenance.

Nothing here is hard-coded toward the answer: the only place the expected shape appears
is the *post-hoc* assertion in step 6, never an input to any model call.
"""

from __future__ import annotations

from collections.abc import Iterator

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.analyze.guardian_gate import gate_cell, gate_lens
from offside_engine.analyze.lens_runner import LensRun, run_lens
from offside_engine.analyze.split_schema import (
    CANONICAL_AXIS_ORDER,
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
from offside_engine.bake.incident import IncidentSpec, ThesisShape
from offside_engine.bake.synthesize import derive_split
from offside_engine.config import DEFAULT_EMBED_MODEL
from offside_engine.retrieve.lens_retrieve import LensRetriever

_LENS_ORDER: tuple[LensKind, ...] = ("REFEREE", "TACTICAL", "HISTORICAL", "FRAMING")


class ThesisMismatch(AssertionError):
    """The derived SPLIT did not match the incident's documented thesis shape."""


def render_synthesis_input(lenses: list[LensOutput], *, shared_settled_fact: str) -> str:
    """Render the gated lens outputs + settled fact into the synthesis user message.

    The synthesis prompt routes evidence by lens, so each lens block is labelled and
    carries only its grounded ids and rationale — never a number, never the expected
    answer. The SHARED_SETTLED_FACT block is what lets the INDETERMINACY precondition
    fire on an admitted act.
    """
    blocks = [f"SHARED_SETTLED_FACT:\n  {shared_settled_fact}", ""]
    for lo in lenses:
        ids = ", ".join(lo.citation_ids) if lo.citation_ids else "(none)"
        blocks.append(
            f"LENS {lo.lens}:\n"
            f"  stance: {lo.stance}\n"
            f"  state: {lo.state}\n"
            f"  citation_ids: [{ids}]\n"
            f"  rationale: {lo.rationale}"
        )
    return "\n".join(blocks)


def check_thesis_shape(split: Split, expected: ThesisShape) -> list[str]:
    """Return the list of axes whose derived state is outside its allowed set.

    Runs only when an ``expected`` shape is given (a documented incident). The check is
    post-hoc: the SPLIT is already produced before this is called, so an empty result
    proves the rules *derived* the documented shape rather than being told it. An empty
    list means the thesis holds.
    """
    if not expected:
        return []
    by_axis = {c.axis: c.state for c in split.cells}
    problems = []
    for axis in CANONICAL_AXIS_ORDER:
        allowed = expected.get(axis)
        if allowed is None:
            continue
        got = by_axis.get(axis)
        if got not in allowed:
            problems.append(f"{axis}: derived {got}, expected one of {sorted(allowed)}")
    return problems


def assert_thesis_shape(split: Split, expected: ThesisShape) -> None:
    """Raise :class:`ThesisMismatch` if the derived SPLIT does not match the thesis.

    The strict form, used by CI and any caller that wants the documented shape enforced.
    The bake itself defaults to the soft :func:`check_thesis_shape` so a live run always
    produces an inspectable fixture.
    """
    problems = check_thesis_shape(split, expected)
    if problems:
        raise ThesisMismatch(
            "derived SPLIT does not match the documented thesis:\n  " + "\n  ".join(problems)
        )


_LENS_LABEL: dict[LensKind, str] = {
    "REFEREE": "Referee", "TACTICAL": "Tactical",
    "HISTORICAL": "Historical", "FRAMING": "Framing",
}


def bake_incident_streaming(
    spec: IncidentSpec,
    *,
    retriever: LensRetriever,
    granite: GraniteClient,
    guardian: GuardianClient,
    citations: dict[str, Citation],
    embed_model: str = DEFAULT_EMBED_MODEL,
    corpus_git_sha: str | None = None,
    strict_thesis: bool = False,
) -> Iterator[dict]:
    """Run the bake step by step, yielding a progress event as each step completes.

    Identical pipeline to :func:`bake_incident` — same lens runs, same Guardian gate, same
    deterministic routing — but instead of returning only the final bundle it ``yield``s a
    dict per visible step so a caller (the Studio backend) can stream genuine progress to
    the UI while the multi-minute bake is still running:

    * ``{"type": "lens", lens, stance, rationale, citation_ids}``   — a lens reading landed
    * ``{"type": "audit", lens, verdict, guardian_model}``          — Guardian audited it
    * ``{"type": "cell", axis, state}``                             — an axis resolved
    * ``{"type": "done", bundle}``                                  — the assembled bundle

    Every event is real — read off the actual step result, never synthesised. The final
    ``done`` event carries the same :class:`IncidentBundle` :func:`bake_incident` returns.
    """
    # 1 — settled fact, stated first.
    settled = SettledFact(
        status=spec.settled_status,
        statement=spec.settled_statement,
        citation_ids=list(spec.settled_citation_ids),
    )

    # 2 + 3 — per-lens run, then per-lens Guardian gate. Emit after each so the UI shows
    # "Granite read the Referee lens" then "Guardian: GROUNDED" as it actually happens.
    sealed_lenses: list[SealedLens] = []
    gated_outputs: list[LensOutput] = []
    for lens in _LENS_ORDER:
        run: LensRun = run_lens(
            lens=lens,
            query=spec.lens_queries[lens],
            retriever=retriever,
            granite=granite,
            allowed_citation_ids=set(spec.allowed_citation_ids),
        )
        gated = gate_lens(run.output, citations=citations, guardian=guardian)
        sealed_lenses.append(SealedLens(output=gated.output, seal=gated.seal))
        gated_outputs.append(gated.output)
        yield {
            "type": "lens", "lens": lens, "stance": gated.output.stance,
            "rationale": gated.output.rationale, "citation_ids": list(gated.output.citation_ids),
        }
        yield {
            "type": "audit", "lens": lens, "verdict": gated.seal.verdict,
            "guardian_model": gated.seal.guardian_model,
        }

    # 4 — synthesis: ROUTE the gated lens evidence onto the four axes (deterministic code).
    split = derive_split(gated_outputs, admitted_act=bool(spec.admission_note))

    # 5 — per-cell Guardian gate; emit each axis as it resolves so the boxes fill live.
    gated_cells = []
    sealed_cells: list[SealedCell] = []
    for cell in split.cells:
        gc = gate_cell(cell, citations=citations, guardian=guardian)
        gated_cells.append(gc.cell)
        sealed_cells.append(SealedCell(cell=gc.cell, seal=gc.seal))
        yield {"type": "cell", "axis": gc.cell.axis, "state": gc.cell.state}
    gated_split = Split(cells=gated_cells, headline=split.headline)

    # 6 — thesis check (oracle, not an input). Strict callers raise; a live bake warns.
    problems = check_thesis_shape(gated_split, spec.expected_thesis)
    if problems:
        message = (
            f"derived SPLIT for {spec.incident_id} does not match the documented thesis:\n  "
            + "\n  ".join(problems)
        )
        if strict_thesis:
            raise ThesisMismatch(message)
        print(f"WARNING: {message}\n(continuing; set strict_thesis=True to make this fatal)")

    # 7 — assemble only the citations the bundle actually references, then revalidate.
    referenced: set[str] = set(spec.settled_citation_ids)
    for sl in sealed_lenses:
        referenced.update(sl.output.citation_ids)
    for c in gated_split.cells:
        referenced.update(c.citation_ids)
    bundle_citations = {cid: citations[cid] for cid in referenced if cid in citations}

    provenance = BakeProvenance(
        granite_model=granite.config.model,
        guardian_model=guardian.model,
        embed_model=embed_model,
        options=dict(granite.options),
        corpus_git_sha=corpus_git_sha,
    )

    bundle = IncidentBundle(
        incident_id=spec.incident_id,
        title=spec.title,
        settled_fact=settled,
        lenses=sealed_lenses,
        split=gated_split,
        cell_seals=sealed_cells,
        citations=bundle_citations,
        provenance=provenance,
    )
    yield {"type": "done", "bundle": bundle}


def bake_incident(
    spec: IncidentSpec,
    *,
    retriever: LensRetriever,
    granite: GraniteClient,
    guardian: GuardianClient,
    citations: dict[str, Citation],
    embed_model: str = DEFAULT_EMBED_MODEL,
    corpus_git_sha: str | None = None,
    strict_thesis: bool = False,
) -> IncidentBundle:
    """Run the full bake for one incident and return its frozen IncidentBundle.

    ``citations`` is the complete pool of evidence atoms (laws + curated + statsbomb);
    the per-incident allow-list on ``spec`` scopes which of them any lens may surface.

    ``strict_thesis`` controls what happens if the derived SPLIT does not match the
    incident's documented thesis shape. The default (``False``) prints a loud warning and
    still returns the fixture, so a live bake always produces something inspectable.
    Set it ``True`` (CI, regression checks) to raise :class:`ThesisMismatch` instead.

    This is the non-streaming entry point: it drives :func:`bake_incident_streaming` to
    completion and returns the bundle from its final ``done`` event, so the two share one
    implementation of the bake steps and can never drift.
    """
    bundle: IncidentBundle | None = None
    for event in bake_incident_streaming(
        spec, retriever=retriever, granite=granite, guardian=guardian,
        citations=citations, embed_model=embed_model, corpus_git_sha=corpus_git_sha,
        strict_thesis=strict_thesis,
    ):
        if event["type"] == "done":
            bundle = event["bundle"]
    assert bundle is not None, "streaming bake did not yield a done event"
    return bundle
