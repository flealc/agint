from dataclasses import dataclass
from typing import Any, Callable

from agint.memory.sqlite_store import SQLiteStore
from agint.tools.tasks import create_task, list_tasks


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    approval_required: bool = False


def build_tools(store: SQLiteStore) -> dict[str, Tool]:
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

