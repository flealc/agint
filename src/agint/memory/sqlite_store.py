import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self, schema_path: Path) -> None:
        with self.connect() as conn:
            conn.executescript(schema_path.read_text(encoding="utf-8"))

    def create_task(
        self,
        title: str,
        due_at: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            cursor = conn.execute(
                """
        INSERT INTO tasks (title, due_at, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
                (title, due_at, source, now, now),
            )

            task_id = cursor.lastrowid

            row = conn.execute(
                """
        SELECT id, title, status, due_at, source, created_at, updated_at
        FROM tasks
        WHERE id = ?
        """,
                (task_id,),
            ).fetchone()

        return dict(row)

    def list_tasks(self, status: str | None = "open") -> list[dict[str, Any]]:
        query = """
      SELECT id, title, status, due_at, source, created_at, updated_at
      FROM tasks
    """
        params: tuple[Any, ...] = ()

        if status is not None:
            query += " WHERE status = ?"
            params = (status,)

        query += " ORDER BY created_at DESC"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

