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

    def create_reminder(
        self,
        title: str,
        remind_at: str,
        source: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reminders (title, remind_at, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, remind_at, source, now, now),
            )

            reminder_id = cursor.lastrowid

            row = conn.execute(
                """
                SELECT id, title, remind_at, status, source, created_at, updated_at
                FROM reminders
                WHERE id = ?
                """,
                (reminder_id,),
            ).fetchone()

        return dict(row)

    def list_reminders(
        self,
        status: str | None = "pending",
    ) -> list[dict[str, Any]]:
        query = """
            SELECT id, title, remind_at, status, source, created_at, updated_at
            FROM reminders
        """
        params: tuple[Any, ...] = ()

        if status is not None:
            query += " WHERE status = ?"
            params = (status,)

        query += " ORDER BY remind_at ASC"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def set_preference(self, key: str, value: str) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            existing = conn.execute(
                """
                SELECT created_at
                FROM preferences
                WHERE key = ?
                """,
                (key,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now

            conn.execute(
                """
                INSERT INTO preferences (key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, created_at, now),
            )

            row = conn.execute(
                """
                SELECT key, value, created_at, updated_at
                FROM preferences
                WHERE key = ?
                """,
                (key,),
            ).fetchone()

        return dict(row)

    def get_preference(self, key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT key, value, created_at, updated_at
                FROM preferences
                WHERE key = ?
                """,
                (key,),
            ).fetchone()

        return dict(row) if row else None

    def list_preferences(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT key, value, created_at, updated_at
                FROM preferences
                ORDER BY key ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def record_approval(
        self,
        session_id: str,
        tool_name: str,
        tool_args_json: str,
        approved: bool,
    ) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO approvals (
                    session_id, tool_name, tool_args_json, approved, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, tool_name, tool_args_json, int(approved), now),
            )
            approval_id = cursor.lastrowid

            row = conn.execute(
                """
                SELECT id, session_id, tool_name, tool_args_json, approved, created_at
                FROM approvals
                WHERE id = ?
                """,
                (approval_id,),
            ).fetchone()

        return dict(row)

    def create_calendar_proposal(
        self,
        title: str,
        start_at: str,
        end_at: str,
        notes: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO calendar_proposals (
                    title, start_at, end_at, notes, source, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (title, start_at, end_at, notes, source, now, now),
            )
            proposal_id = cursor.lastrowid

            row = conn.execute(
                """
                SELECT id, title, start_at, end_at, notes, status, source, created_at, updated_at
                FROM calendar_proposals
                WHERE id = ?
                """,
                (proposal_id,),
            ).fetchone()

        return dict(row)

    def list_calendar_proposals(
        self,
        status: str | None = "proposed",
    ) -> list[dict[str, Any]]:
        query = """
            SELECT id, title, start_at, end_at, notes, status, source, created_at, updated_at
            FROM calendar_proposals
        """
        params: tuple[Any, ...] = ()

        if status is not None:
            query += " WHERE status = ?"
            params = (status,)

        query += " ORDER BY start_at ASC"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def create_session(self, session_id: str) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, summary, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, None, now, now),
            )

            row = conn.execute(
                """
                SELECT id, summary, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()

        return dict(row)

    def end_session(self, session_id: str) -> dict[str, Any] | None:
        now = utc_now()

        with self.connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET updated_at = ?
                WHERE ID = ?
                """,
                (now, session_id),
            )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, summary, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()

        return dict(row) if row else None

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str | None,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages (
                    session_id, role, content, tool_call_id, tool_name, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, tool_call_id, tool_name, now),
            )

            message_id = cursor.lastrowid

            row = conn.execute(
                """
                SELECT id, session_id, role, content, tool_call_id, tool_name, created_at
                FROM messages
                WHERE id = ?
                """,
                (message_id,),
            ).fetchone()

        return dict(row)

    def list_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT id, session_id, role, content, tool_call_id, tool_name, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
        """
        params: list[Any] = [session_id]

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, tool_call_id
                FROM messages
                WHERE session_id = ?
                AND role IN ('user', 'assistant')
                AND content IS NOT NULL
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        messages = [dict(row) for row in rows]
        messages.reverse()

        model_messages = []

        for message in messages:
            item = {
                "role": message["role"],
                "content": message["content"],
            }

            if message["tool_call_id"] is not None:
                item["tool_call_id"] = message["tool_call_id"]

            model_messages.append(item)

        return model_messages
