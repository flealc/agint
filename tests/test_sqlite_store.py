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
