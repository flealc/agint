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
