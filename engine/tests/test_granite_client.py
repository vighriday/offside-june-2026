"""Granite client wrapper — deterministic regime and schema constraint, mocked.

No live model is needed: we assert the client sends the right deterministic options
and schema, and that it re-validates the model's content through Pydantic.
"""

from __future__ import annotations

import json

import pytest

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.split_schema import LensOutput
from offside_engine.config import GraniteConfig


class _FakeOllama:
    """Records the chat call and returns a canned, schema-valid content string."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.last_call: dict | None = None

    def chat(self, **kwargs):
        self.last_call = kwargs
        return {"message": {"content": self.content}}


@pytest.fixture
def client(monkeypatch):
    c = GraniteClient(config=GraniteConfig(model="granite3.3:8b", seed=42, num_ctx=8192))
    valid = LensOutput(
        lens="REFEREE",
        stance="SUPPORTS",
        state="GROUNDED",
        citation_ids=["ifab-law12-p152"],
        rationale="the cited clause governs deliberate handling",
    ).model_dump_json()
    fake = _FakeOllama(valid)
    monkeypatch.setattr(c, "_client", fake)
    return c, fake


def test_sends_deterministic_options(client):
    c, fake = client
    c.generate_structured(schema=LensOutput, system="sys", user="usr")
    opts = fake.last_call["options"]
    assert opts["temperature"] == 0.0
    assert opts["seed"] == 42
    assert opts["num_ctx"] == 8192
    assert "num_predict" in opts


def test_constrains_generation_to_the_schema(client):
    c, fake = client
    c.generate_structured(schema=LensOutput, system="sys", user="usr")
    # Ollama is handed the model's JSON Schema as the generation grammar.
    assert fake.last_call["format"] == LensOutput.model_json_schema()
    assert fake.last_call["model"] == "granite3.3:8b"


def test_revalidates_content_through_pydantic(client):
    c, fake = client
    out = c.generate_structured(schema=LensOutput, system="sys", user="usr")
    assert isinstance(out, LensOutput)
    assert out.lens == "REFEREE"


def test_rejects_content_that_breaks_the_schema(client):
    c, fake = client
    # A grounded lens with no citation must be rejected by the schema's own validator.
    fake.content = json.dumps(
        {"lens": "REFEREE", "stance": "SUPPORTS", "state": "GROUNDED",
         "citation_ids": [], "rationale": "ungrounded"}
    )
    with pytest.raises(Exception):
        c.generate_structured(schema=LensOutput, system="sys", user="usr")


def test_provenance_record_reflects_config(client):
    c, _ = client
    rec = c.record
    assert rec.model == "granite3.3:8b"
    assert rec.options["temperature"] == 0.0
    assert rec.options["seed"] == 42
