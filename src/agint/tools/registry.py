from dataclasses import dataclass
from typing import Any, Callable

from agint.memory.sqlite_store import SQLiteStore
from agint.tools.tasks import create_task, list_tasks
from agint.tools.notes import read_note, write_draft_note
from agint.tools.reminders import create_reminder, list_reminders
from agint.retrieval.qmd import qmd_search, format_qmd_results


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    approval_required: bool = False


def search_notes_with_qmd(query: str, limit: int = 5) -> dict[str, Any]:
    results = qmd_search(query, limit=limit)

    return {
        "query": query,
        "results": results,
        "formatted": format_qmd_results(results),
    }


def build_tools(store: SQLiteStore, vault_path) -> dict[str, Tool]:
    return {
        "tasks.create": Tool(
            name="tasks.create",
            description="Create a local task for the user",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The task title.",
                    },
                    "due_at": {
                        "type": ["string", "null"],
                        "description": "Optional ISO 8601 due date/time.",
                    },
                },
                "required": ["title"],
                "additionalProperties": False,
            },
            handler=lambda title, due_at=None: create_task(
                store,
                title=title,
                due_at=due_at,
                source="tool",
            ),
            approval_required=True,
        ),
        "tasks.list": Tool(
            name="tasks.list",
            description="List local tasks.",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": ["string", "null"],
                        "description": "Task status to filter by. Use null to list all tasks.",
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
            handler=lambda status="open": list_tasks(store, status=status),
            approval_required=False,
        ),
        "notes.read": Tool(
            name="notes.read",
            description="Read a Markdown note from the configured Obsidian vault relative path.",
            parameters={
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Path to a Markdown note relative to the Obsidian vault.",
                    },
                },
                "required": ["relative_path"],
                "additionalProperties": False,
            },
            handler=lambda relative_path: read_note(
                vault_path,
                relative_path=relative_path,
            ),
            approval_required=False,
        ),
        "notes.write_draft": Tool(
            name="notes.write_draft",
            description="Create a new Markdown draft note in drafts/agent drafts inside the Obsidian vault.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Draft note title.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown body content for the draft note.",
                    },
                },
                "required": ["title", "content"],
                "additionalProperties": False,
            },
            handler=lambda title, content: write_draft_note(
                vault_path,
                title=title,
                content=content,
            ),
            approval_required=True,
        ),
        "notes.search": Tool(
            name="notes.search",
            description="Search the Obsidian vault using QMD and return relevant Markdown note results.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for notes.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of search results.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            handler=lambda query, limit=5: search_notes_with_qmd(query, limit),
            approval_required=False,
        ),
        "reminders.create": Tool(
            name="reminders.create",
            description="Create a local reminder for the user.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Reminder title.",
                    },
                    "remind_at": {
                        "type": "string",
                        "description": "ISO 8601 reminder datetime.",
                    },
                },
                "required": ["title", "remind_at"],
                "additionalProperties": False,
            },
            handler=lambda title, remind_at: create_reminder(
                store,
                title=title,
                remind_at=remind_at,
                source="tool",
            ),
            approval_required=True,
        ),
        "reminders.list": Tool(
            name="reminders.list",
            description="List local reminders.",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": ["string", "null"],
                        "description": "Reminder status to filter by. Use null to list all reminders.",
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
            handler=lambda status="pending": list_reminders(store, status=status),
            approval_required=False,
        ),
    }


def tool_schemas(tools: dict[str, Tool]) -> list[dict[str, Any]]:
    schemas = []

    for tool in tools.values():
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
        )

    return schemas
