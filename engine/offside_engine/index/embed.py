"""Embedding via IBM granite-embedding on Ollama.

A thin wrapper over Ollama's embed endpoint, pinned to the IBM embedding model so the
per-lens retrieval index is built entirely with the IBM stack. Runs on the build host
only; the resulting vectors are frozen into LanceDB and committed.
"""

from __future__ import annotations

import ollama

from offside_engine.config import DEFAULT_EMBED_MODEL, DEFAULT_HOST

# granite-embedding:30m emits 384-dim vectors with a 512-token window, so chunks must
# stay small (~300-400 tokens). Recorded here so the index builder and any test agree.
EMBED_DIM = 384


class Embedder:
    """Embeds text with a fixed IBM granite-embedding model."""

    def __init__(self, model: str = DEFAULT_EMBED_MODEL, host: str = DEFAULT_HOST) -> None:
        self.model = model
        self._client = ollama.Client(host=host)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returning one vector per input in order."""
        if not texts:
            return []
        response = self._client.embed(model=self.model, input=texts)
        return list(response["embeddings"])

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text (e.g. a query)."""
        return self.embed([text])[0]
