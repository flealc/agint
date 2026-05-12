from pathlib import Path

from agint.memory.sqlite_store import SQLiteStore


def test_create_and_list_tasks(tmp_path):
    db_path = tmp_path / "assistant.db"
    schema_path = Path("src/agint/memory/schema.sql")

    store = SQLiteStore(db_path)
    store.init_schema(schema_path)

    task = store.create_task("Buy coffee", source="test")
    tasks = store.list_tasks()

    assert task["title"] == "Buy coffee"
    assert task["status"] == "open"
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Buy coffee"


def test_create_get_and_end_session(tmp_path):
    db_path = tmp_path / "assistant.db"
    schema_path = Path("src/agint/memory/schema.sql")

    store = SQLiteStore(db_path)
    store.init_schema(schema_path)

    created = store.create_session("test-session")
    fetched = store.get_session("test-session")

    assert created["id"] == "test-session"
    assert fetched is not None
    assert fetched["id"] == "test-session"
    assert fetched["summary"] is None

    store.end_session("test-session")
    ended = store.get_session("test-session")

    assert ended is not None
    assert ended["updated_at"] >= fetched["updated_at"]


def test_add_and_list_messages(tmp_path):
    db_path = tmp_path / "assistant.db"
    schema_path = Path("src/agint/memory/schema.sql")

    store = SQLiteStore(db_path)
    store.init_schema(schema_path)
    store.create_session("test-session")

    store.add_message(
        session_id="test-session",
        role="user",
        content="Hello",
    )
    store.add_message(
        session_id="test-session",
        role="assistant",
        content="Hi there",
    )

    messages = store.list_messages("test-session")

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there"


def test_get_recent_messages_returns_oldest_to_newest(tmp_path):
    db_path = tmp_path / "assistant.db"
    schema_path = Path("src/agint/memory/schema.sql")

    store = SQLiteStore(db_path)
    store.init_schema(schema_path)
    store.create_session("test-session")

    for index in range(5):
        store.add_message(
            session_id="test-session",
            role="user",
            content=f"message {index}",
        )

    messages = store.get_recent_messages("test-session", limit=3)

    assert [message["content"] for message in messages] == [
        "message 2",
        "message 3",
        "message 4",
    ]


def test_get_recent_messages_excludes_tool_protocol_messages(tmp_path):
    db_path = tmp_path / "assistant.db"
    schema_path = Path("src/agint/memory/schema.sql")

    store = SQLiteStore(db_path)
    store.init_schema(schema_path)
    store.create_session("test-session")

    store.add_message(
        session_id="test-session",
        role="user",
        content="Find my notes about agents",
    )
    store.add_message(
        session_id="test-session",
        role="assistant",
        content=None,
    )
    store.add_message(
        session_id="test-session",
        role="tool",
        content='{"results": []}',
        tool_call_id="call_123",
        tool_name="notes.search",
    )
    store.add_message(
        session_id="test-session",
        role="assistant",
        content="I could not find matching notes.",
    )

    raw_messages = store.list_messages("test-session")
    recent_messages = store.get_recent_messages("test-session", limit=10)

    assert len(raw_messages) == 4
    assert [message["role"] for message in recent_messages] == [
        "user",
        "assistant",
    ]
    assert recent_messages[1]["content"] == "I could not find matching notes."
