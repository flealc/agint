from typing import Any

from agint.memory.sqlite_store import SQLiteStore

def create_task(
    store: SQLiteStore,
    title: str,
    due_at: str | None = None,
    source: str | None = "manual",
) -> dict[str, Any]:
  return store.create_task(title=title, due_at=due_at, source=source)

def list_tasks(
    store: SQLiteStore,
    status: str | None = "open",
) -> list[dict[str, Any]]:
  return store.list_tasks(status=status)
