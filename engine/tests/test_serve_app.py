from unittest.mock import patch

from fastapi.testclient import TestClient

from offside_engine.serve.app import app

client = TestClient(app)


def test_health_reports_structure():
    with patch("offside_engine.serve.app._ollama_up", return_value=False):
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"ok", "ollama", "models"}


def test_decompose_streams_events_ending_in_done():
    fake_events = [
        {"type": "cell", "axis": "RULE_AMBIGUITY", "state": "ABSENT"},
        {"type": "done", "bundle": {"incident_id": "studio-x"}},
    ]

    def fake_stream(payload):
        yield from fake_events

    payload = {
        "title": "x", "settled_statement": "y", "historical_note": "z",
        "quotes": [
            {"speaker": "a", "source": "s", "text": "t"},
            {"speaker": "b", "source": "s", "text": "u"},
        ],
        "tactical_note": None,
    }
    with patch("offside_engine.serve.app.stream_decompose", side_effect=fake_stream):
        r = client.post("/decompose", json=payload)
    assert r.status_code == 200
    text = r.text
    assert '"type": "cell"' in text or '"type":"cell"' in text
    assert "done" in text
