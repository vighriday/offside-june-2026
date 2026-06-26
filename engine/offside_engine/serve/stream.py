"""Step events for the Studio live run. Drives the streaming bake and forwards each step
event AS it happens, so the UI shows genuine progress across the multi-minute run — Granite
reading each lens, Guardian's verdict, each axis resolving — not a burst at the end. Every
event is read off the REAL bake step, nothing is synthesised."""
from __future__ import annotations

from collections.abc import Iterator

from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.run import decompose_streaming


def stream_decompose(payload: FormPayload) -> Iterator[dict]:
    """Yield {type: lens|audit|cell|done|error} dicts live from the streaming bake.

    Forwards the engine's real step events one by one as the bake runs. The only events this
    layer shapes are the terminal ones: it stamps the bundle's provenance ``live-user`` and
    JSON-dumps it on ``done``, and converts any exception into a single ``error`` event."""
    try:
        for event in decompose_streaming(payload):
            if event["type"] == "done":
                bundle = event["bundle"]
                bundle = bundle.model_copy(update={
                    "provenance": bundle.provenance.model_copy(update={"mode": "live-user"})
                })
                yield {"type": "done", "bundle": bundle.model_dump(mode="json")}
            else:
                yield event
    except Exception as exc:  # noqa: BLE001 — surfaced to the client as an error event
        yield {"type": "error", "message": str(exc)}
