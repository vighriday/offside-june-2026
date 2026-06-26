"""Step events for the Studio live run. Wraps the non-streaming decompose and emits one
event per visible step so the UI can fill the four SPLIT boxes one at a time. Every event
is derived from the REAL baked bundle — nothing is synthesised."""
from __future__ import annotations

from collections.abc import Iterator

from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.run import decompose


def stream_decompose(payload: FormPayload) -> Iterator[dict]:
    """Yield {type: retrieve|lens|audit|cell|done|error} dicts from the real bake.

    The current bake is synchronous and returns the whole bundle, so we run it, then replay
    its real, already-computed steps as events in pipeline order. The states are the real
    routed states — the 'live' feel is honest narration of a real computation, not fakery."""
    try:
        bundle = decompose(payload)
    except Exception as exc:  # noqa: BLE001 — surfaced to the client as an error event
        yield {"type": "error", "message": str(exc)}
        return

    for sl in bundle.lenses:
        o, seal = sl.output, sl.seal
        yield {"type": "lens", "lens": o.lens, "stance": o.stance,
               "rationale": o.rationale, "citation_ids": list(o.citation_ids)}
        yield {"type": "audit", "lens": o.lens, "verdict": seal.verdict,
               "guardian_model": seal.guardian_model}
    for cell in bundle.split.cells:
        yield {"type": "cell", "axis": cell.axis, "state": cell.state}
    yield {"type": "done", "bundle": bundle.model_dump(mode="json")}
