import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from agint.memory.sqlite_store import SQLiteStore
from agint.models import call_model


def current_date_for_timezone(timezone: str = "America/Chicago") -> str:
    return datetime.now(ZoneInfo(timezone)).date().isoformat()


def extract_json_object(content: str | None) -> dict[str, Any]:
    if not content:
        raise ValueError("Reminder parser returned an empty response")

    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])

        preview = cleaned[:200]
        raise ValueError(f"Reminder parser did not return JSON. Response: {preview!r}")


def parse_reminder_request(
    text: str,
    current_date: str | None = None,
    timezone: str = "America/Chicago",
) -> dict[str, Any]:
    current_date = current_date or current_date_for_timezone(timezone)
    messages = [
        {
            "role": "system",
            "content": f"""Extract a reminder from the user's request.

Return only JSON with this shape:
{{
  "title": "short reminder title",
  "remind_at": "ISO 8601 datetime with timezone offset, or null",
  "needs_clarification": true or false,
  "clarification_question": "question to ask, or null"
}}

Rules:
- Current date: {current_date}
- Timezone: {timezone}
- If date or time is missing or ambiguous, set needs_clarification to true.
- If the request says "tomorrow", calculate it from the current date.
- Do not include markdown.
- Do not include extra text.
""",
        },
        {"role": "user", "content": text},
    ]

    response = call_model(messages, model_alias="fast")
    content = response.choices[0].message.content
    return extract_json_object(content)


def create_reminder(
    store: SQLiteStore,
    title: str,
    remind_at: str,
    source: str | None = "manual",
) -> dict[str, Any]:
    return store.create_reminder(
        title=title,
        remind_at=remind_at,
        source=source,
    )


def list_reminders(
    store: SQLiteStore,
    status: str | None = "pending",
) -> list[dict[str, Any]]:
    return store.list_reminders(status=status)
