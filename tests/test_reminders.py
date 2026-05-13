import pytest

from agint.tools.reminders import current_date_for_timezone, extract_json_object


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
