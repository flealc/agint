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
