from typing import Any

from agint.memory.sqlite_store import SQLiteStore


def propose_event(
    store: SQLiteStore,
    title: str,
    start_at: str,
    end_at: str,
    notes: str | None = None,
    source: str | None = "manual",
) -> dict[str, Any]:
    return store.create_calendar_proposal(
        title=title,
        start_at=start_at,
        end_at=end_at,
        notes=notes,
        source=source,
    )


def list_proposals(
    store: SQLiteStore,
    status: str | None = "proposed",
) -> list[dict[str, Any]]:
    return store.list_calendar_proposals(status=status)
