import json

from agint.events import append_event


def test_append_event_writes_jsonl(tmp_path):
    log_path = tmp_path / "logs" / "events.jsonl"

    append_event(log_path, "test_event", {"session_id": "s1"})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[0])

    assert event["type"] == "test_event"
    assert event["session_id"] == "s1"
    assert "created_at" in event
