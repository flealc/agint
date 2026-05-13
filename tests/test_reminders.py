import pytest

from agint.tools import reminders
from agint.tools.reminders import (
    current_date_for_timezone,
    extract_json_object,
    parse_reminder_request,
)


def test_current_date_for_timezone_returns_iso_date():
    current_date = current_date_for_timezone("America/Chicago")

    assert len(current_date) == 10
    assert current_date[4] == "-"
    assert current_date[7] == "-"


def test_extract_json_object_from_plain_json():
    assert extract_json_object('{"title": "Call Luis"}') == {"title": "Call Luis"}


def test_extract_json_object_from_markdown_fence():
    content = """```json
{"title": "Call Luis"}
```"""

    assert extract_json_object(content) == {"title": "Call Luis"}


def test_extract_json_object_from_surrounding_text():
    content = 'Here is the JSON: {"title": "Call Luis"}'

    assert extract_json_object(content) == {"title": "Call Luis"}


def test_extract_json_object_rejects_empty_response():
    with pytest.raises(ValueError, match="empty response"):
        extract_json_object("")


def test_parse_reminder_request_requests_json_output(monkeypatch):
    captured = {}

    class FakeMessage:
        content = '{"title": "Call Luis", "remind_at": null, "needs_clarification": true, "clarification_question": "When?"}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    def fake_call_model(messages, model_alias, **kwargs):
        captured["messages"] = messages
        captured["model_alias"] = model_alias
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(reminders, "call_model", fake_call_model)

    parsed = parse_reminder_request(
        "Call Luis",
        current_date="2026-05-13",
        timezone="America/Chicago",
    )

    assert parsed["needs_clarification"] is True
    assert captured["model_alias"] == "fast"
    assert captured["response_format"] == {"type": "json_object"}
