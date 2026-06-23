"""Run one lens: retrieve its evidence, render it, ask Granite, guard the answer.

This is the wire between :mod:`offside_engine.retrieve.lens_retrieve` (which decides
*what evidence a lens may see*) and :mod:`offside_engine.analyze.granite_client` (which
constrains *what Granite may emit*). The runner adds the two things neither half can do
alone:

* **Render** the retrieved hits into the labelled evidence block the prompt expects
  (``[citation_id] text``), so a lens can only cite an id it was actually shown.
* **Guard** Granite's answer against the evidence it was given — a returned
  ``citation_id`` that was not in the retrieved set is a hallucinated citation and is
  rejected here, before it can ever reach a fixture.

If a lens has no in-incident evidence, the runner short-circuits to a structurally
valid ``INSUFFICIENT_EVIDENCE`` answer *without calling Granite* — there is nothing to
ground against, so there is nothing to generate.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.prompts import LENS_SYSTEM
from offside_engine.analyze.split_schema import LensKind, LensOutput
from offside_engine.retrieve.lens_retrieve import LensRetriever, RetrievedHit

# The header each lens prompt uses to introduce its evidence block. Keeping the label
# per-lens keeps the worked examples in the prompts consistent with what the model sees.
_EVIDENCE_HEADER: dict[LensKind, str] = {
    "REFEREE": "RETRIEVED LAW",
    "TACTICAL": "RETRIEVED DATA",
    "HISTORICAL": "RETRIEVED HISTORY",
    "FRAMING": "RETRIEVED QUOTES",
}


def render_evidence(lens: LensKind, hits: list[RetrievedHit]) -> str:
    """Render retrieved hits as the labelled evidence block a lens prompt consumes.

    Each hit becomes ``[citation_id] text`` on its own line, under the lens's header.
    The id in brackets is the ONLY id the lens is permitted to cite, so the rendering
    and the cite-or-die guard share one source of truth.
    """
    header = _EVIDENCE_HEADER[lens]
    if not hits:
        return f"{header}:\n  (no evidence retrieved for this lens)"
    lines = [f"  [{h.citation_id}] {h.text}" for h in hits]
    return f"{header}:\n" + "\n".join(lines)


def _insufficient(lens: LensKind) -> LensOutput:
    """The one valid empty answer: nothing to ground against, so nothing generated."""
    return LensOutput(
        lens=lens,
        stance="INSUFFICIENT_EVIDENCE",
        state="INSUFFICIENT_EVIDENCE",
        citation_ids=[],
        rationale="No evidence was retrieved for this lens on this incident.",
    )


@dataclass(frozen=True)
class LensRun:
    """A lens answer plus the evidence it was allowed to see — frozen for provenance.

    Carrying ``hits`` next to ``output`` lets the bake (and the Guardian gate) audit a
    lens against exactly the passages it was shown, with no second retrieval.
    """

    output: LensOutput
    hits: tuple[RetrievedHit, ...]


def run_lens(
    *,
    lens: LensKind,
    query: str,
    retriever: LensRetriever,
    granite: GraniteClient,
    allowed_citation_ids: set[str] | None = None,
    k: int = 3,
) -> LensRun:
    """Retrieve, render, generate, and guard one lens.

    The flow is: scope evidence to this lens (and this incident, via
    ``allowed_citation_ids``) → render it into the prompt → constrain Granite to
    :class:`LensOutput` → reject any citation the lens was not shown.

    A lens with no retrieved evidence returns ``INSUFFICIENT_EVIDENCE`` without a model
    call. A lens that cites an id outside its retrieved set raises — a hallucinated
    citation must never reach a fixture.
    """
    hits = retriever.retrieve(
        lens=lens, query=query, k=k, allowed_citation_ids=allowed_citation_ids
    )
    if not hits:
        return LensRun(output=_insufficient(lens), hits=())

    shown = {h.citation_id for h in hits}
    user = render_evidence(lens, hits)

    # The model occasionally slips — e.g. emits a GROUNDED reading with no citation_ids,
    # cites an id it was not shown, or mislabels the lens. The schema rightly rejects the
    # first; the latter two we reject here. None of these should crash the whole bake: we
    # retry once with a corrective nudge, and if the model still cannot produce a clean
    # reading we degrade THIS lens to INSUFFICIENT_EVIDENCE (a valued answer) and carry
    # on. A single fumbled lens never costs the run.
    last_error = ""
    for attempt in range(2):
        system = LENS_SYSTEM[lens]
        if attempt > 0:
            system = system + "\n\nCORRECTION: " + last_error + (
                " Either return a GROUNDED reading that cites at least one of the exact "
                "ids shown above, or return INSUFFICIENT_EVIDENCE with no citations."
            )
        try:
            output = granite.generate_structured(
                schema=LensOutput, system=system, user=user
            )
        except ValidationError as e:
            last_error = f"the previous output was not a valid lens reading ({e.error_count()} errors)."
            continue

        stray = [cid for cid in output.citation_ids if cid not in shown]
        if stray:
            last_error = (
                f"you cited ids you were not shown ({stray}); cite only: {sorted(shown)}."
            )
            continue
        if output.lens != lens:
            last_error = f"you labelled the output {output.lens}; it must be {lens}."
            continue

        return LensRun(output=output, hits=tuple(hits))

    # Both attempts failed cleanly — degrade rather than crash the bake.
    return LensRun(output=_insufficient(lens), hits=tuple(hits))
