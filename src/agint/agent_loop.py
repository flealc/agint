import json
from typing import Any

from agint.approvals import request_approval
from agint.events import append_event
from agint.models import call_model
from agint.tools.registry import Tool, tool_schemas


def extract_assistant_message(response) -> dict[str, Any]:
    message = response.choices[0].message

    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": getattr(message, "tool_calls", None),
    }


def has_tool_calls(message: dict[str, Any]) -> bool:
    return bool(message.get("tool_calls"))


def parse_tool_args(raw_args: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw_args is None:
        return {}

    if isinstance(raw_args, dict):
        return raw_args

    return json.loads(raw_args)


def summarize_tool_result(result: Any) -> str:
    return json.dumps(result, ensure_ascii=False, default=str)


def run_agent_turn(
    *,
    session_id: str,
    event_log_path,
    messages: list[dict[str, Any]],
    tools: dict[str, Tool],
    model_alias: str,
) -> str:
    while True:
        response = call_model(
            messages=messages,
            tools=tool_schemas(tools),
            model_alias=model_alias,
        )

        assistant_message = extract_assistant_message(response)
        messages.append(assistant_message)

        append_event(
            event_log_path,
            "assistant_message",
            {
                "session_id": session_id,
                "content": assistant_message.get("content"),
                "has_tool_calls": has_tool_calls(assistant_message),
            },
        )

        if not has_tool_calls(assistant_message):
            return assistant_message.get("content") or ""

        for tool_call in assistant_message["tool_calls"]:
            tool_name = tool_call.function.name
            tool_args = parse_tool_args(tool_call.function.arguments)

            append_event(
                event_log_path,
                "tool_call",
                {
                    "session_id": session_id,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                },
            )

            tool = tools.get(tool_name)

            if tool is None:
                tool_result = {
                    "error": f"Unknown tool: {tool_name}",
                }
            else:
                approved = True

                if tool.approval_required:
                    approved = request_approval(tool_name, tool_args)

                    append_event(
                        event_log_path,
                        "approval",
                        {
                            "session_id": session_id,
                            "tool_name": tool_name,
                            "approved": approved,
                        },
                    )

                if approved:
                    tool_result = tool.handler(**tool_args)
                else:
                    tool_result = {
                        "approved": False,
                        "result": "User denied the tool call.",
                    }

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": summarize_tool_result(tool_result),
                }
            )

            append_event(
                event_log_path,
                "tool_result",
                {
                    "session_id": session_id,
                    "tool_name": tool_name,
                    "result": tool_result,
                },
            )
