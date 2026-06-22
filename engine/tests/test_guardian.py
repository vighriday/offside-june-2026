"""Granite Guardian client — token parsing, fail-closed, and the IBM message shape.

Guardian is mocked: these assert the client sends the IBM cookbook message structure
(system='groundedness', then user/context/assistant) and maps the single Yes/No token
to a verdict, failing closed on anything it cannot read as a clean 'No'.
"""

from __future__ import annotations

import pytest

from offside_engine.analyze.guardian import GuardianClient


class _FakeOllama:
    def __init__(self, content: str):
        self.content = content
        self.last_call: dict | None = None

    def chat(self, **kwargs):
        self.last_call = kwargs
        return {"message": {"content": self.content}}


def _client(content: str) -> tuple[GuardianClient, _FakeOllama]:
    c = GuardianClient(model="granite3-guardian:2b")
    fake = _FakeOllama(content)
    c._client = fake
    return c, fake


@pytest.mark.parametrize(
    "token,expected",
    [
        ("No", "GROUNDED"),
        ("no", "GROUNDED"),
        ("No.", "GROUNDED"),
        ("Yes", "UNGROUNDED"),
        ("yes", "UNGROUNDED"),
        ("Yes, risk present", "UNGROUNDED"),
        ("", "UNGROUNDED"),          # empty -> fail closed
        ("maybe", "UNGROUNDED"),     # unparseable -> fail closed
    ],
)
def test_token_maps_to_verdict_and_fails_closed(token, expected):
    c, _ = _client(token)
    v = c.check_groundedness(query="q", context_passages=["a passage"], response="r")
    assert v == expected


def test_no_context_fails_closed_without_a_model_call():
    c, fake = _client("No")  # even a "grounded" token must not be reachable
    v = c.check_groundedness(query="q", context_passages=[], response="r")
    assert v == "UNGROUNDED"
    assert fake.last_call is None  # never called the model


def test_sends_the_ibm_cookbook_message_shape():
    c, fake = _client("No")
    c.check_groundedness(query="the task", context_passages=["p1", "p2"], response="reading")
    roles = [m["role"] for m in fake.last_call["messages"]]
    assert roles == ["system", "user", "context", "assistant"]
    msgs = {m["role"]: m["content"] for m in fake.last_call["messages"]}
    assert msgs["system"] == "groundedness"  # risk selected via system content
    assert msgs["user"] == "the task"
    assert "p1" in msgs["context"] and "p2" in msgs["context"]
    assert msgs["assistant"] == "reading"


def test_sends_deterministic_options():
    c, fake = _client("No")
    c.check_groundedness(query="q", context_passages=["p"], response="r")
    opts = fake.last_call["options"]
    assert opts["temperature"] == 0
    assert opts["seed"] == 42
