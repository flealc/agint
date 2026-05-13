from typing import Any

from agint.memory.sqlite_store import SQLiteStore


def set_preference(store: SQLiteStore, key: str, value: str) -> dict[str, Any]:
    return store.set_preference(key=key, value=value)


def get_preference(store: SQLiteStore, key: str) -> dict[str, Any] | None:
    return store.get_preference(key)


def list_preferences(store: SQLiteStore) -> list[dict[str, Any]]:
    return store.list_preferences()
