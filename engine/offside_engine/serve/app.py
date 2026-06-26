"""The Studio backend: GET /health and POST /decompose (SSE). Thin — all real work is in
the unchanged bake, reached via stream_decompose. Runs locally (author's machine) or via
self-host; the public Vercel site never reaches it (it falls back to the example fixture)."""
from __future__ import annotations

import json

import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from offside_engine.config import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_GUARDIAN_MODEL,
    load_granite_config,
)
from offside_engine.serve.form_models import FormPayload
from offside_engine.serve.stream import stream_decompose

app = FastAPI(title="OFFSIDE Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://offside-june-2026.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ollama_up() -> bool:
    try:
        ollama.list()
        return True
    except Exception:  # noqa: BLE001
        return False


@app.get("/health")
def health() -> dict:
    up = _ollama_up()
    have = set()
    if up:
        try:
            have = {m["model"] for m in ollama.list().get("models", [])}
        except Exception:  # noqa: BLE001
            have = set()
    cfg = load_granite_config()
    models = {
        "granite": cfg.model in have,
        "embed": DEFAULT_EMBED_MODEL in have,
        "guardian": DEFAULT_GUARDIAN_MODEL in have,
    }
    return {"ok": up and all(models.values()), "ollama": up, "models": models}


@app.post("/decompose")
async def decompose_route(payload: FormPayload) -> EventSourceResponse:
    def gen():
        for event in stream_decompose(payload):
            yield {"data": json.dumps(event)}
    return EventSourceResponse(gen())
