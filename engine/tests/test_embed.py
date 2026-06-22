"""granite-embedding wrapper — batching and order, mocked (no model needed)."""

from __future__ import annotations

import pytest

from offside_engine.index.embed import EMBED_DIM, Embedder


class _FakeOllama:
    def __init__(self):
        self.calls = []

    def embed(self, model, input):
        self.calls.append((model, list(input)))
        # one deterministic 384-dim vector per input, order preserved
        return {"embeddings": [[float(i)] * EMBED_DIM for i, _ in enumerate(input)]}


@pytest.fixture
def embedder(monkeypatch):
    e = Embedder(model="granite-embedding:30m")
    fake = _FakeOllama()
    monkeypatch.setattr(e, "_client", fake)
    return e, fake


def test_embed_returns_one_vector_per_input(embedder):
    e, _ = embedder
    out = e.embed(["a", "b", "c"])
    assert len(out) == 3
    assert all(len(v) == EMBED_DIM for v in out)


def test_embed_uses_the_pinned_ibm_model(embedder):
    e, fake = embedder
    e.embed(["x"])
    assert fake.calls[0][0] == "granite-embedding:30m"


def test_embed_empty_is_noop(embedder):
    e, fake = embedder
    assert e.embed([]) == []
    assert fake.calls == []


def test_embed_one_returns_a_single_vector(embedder):
    e, _ = embedder
    v = e.embed_one("query")
    assert len(v) == EMBED_DIM
