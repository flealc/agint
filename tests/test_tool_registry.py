from agint.memory.sqlite_store import SQLiteStore
from agint.tools.registry import build_tools, tool_schemas


def test_build_tools_includes_notes_read(tmp_path):
    store = SQLiteStore(tmp_path / "assistant.db")

    tools = build_tools(store, tmp_path)

    assert "notes.read" in tools
    assert tools["notes.read"].approval_required is False


def test_tools_schemas_include_notes_read(tmp_path):
    store = SQLiteStore(tmp_path / "assistant.db")

    schemas = tool_schemas(build_tools(store, tmp_path))
    names = {schema["function"]["name"] for schema in schemas}

    assert "notes.read" in names


def test_build_tools_includes_reminders(tmp_path):
    store = SQLiteStore(tmp_path / "assistant.db")

    tools = build_tools(store, tmp_path)

    assert "reminders.create" in tools
    assert tools["reminders.create"].approval_required is True
    assert "reminders.list" in tools
    assert tools["reminders.list"].approval_required is False
