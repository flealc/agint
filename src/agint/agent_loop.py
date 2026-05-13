import json
import traceback
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
    max_iterations: int = 5,
    store=None,
) -> str:
    for _ in range(max_iterations):
        response = call_model(
            messages=messages,
            tools=tool_schemas(tools),
            model_alias=model_alias,
        )

        assistant_message = extract_assistant_message(response)
        messages.append(assistant_message)

        if store is not None and assistant_message.get("content") is not None:
            store.add_message(
                session_id=session_id,
                role="assistant",
                content=assistant_message.get("content"),
            )

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

                    if store is not None:
                        store.record_approval(
                            session_id=session_id,
                            tool_name=tool_name,
                            tool_args_json=json.dumps(
                                tool_args, ensure_ascii=False, default=str
                            ),
                            approved=approved,
                        )

                    append_event(
                        event_log_path,
                        "approval",
                        {
                            "session_id": session_id,
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "approved": approved,
                        },
                    )

                if approved:
                    try:
                        tool_result = tool.handler(**tool_args)
                    except Exception as exc:
                        tool_result = {
                            "error": "tool_execution_failed",
                            "tool_name": tool_name,
                            "message": str(exc),
                        }

                        append_event(
                            event_log_path,
                            "tool_error",
                            {
                                "session_id": session_id,
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "error": str(exc),
                                "traceback": traceback.format_exc(),
                            },
                        )
                else:
                    tool_result = {
                        "approved": False,
                        "result": "User denied the tool call.",
                    }
            tool_content = summarize_tool_result(tool_result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                }
            )

            if store is not None:
                store.add_message(
                    session_id=session_id,
                    role="tool",
                    content=tool_content,
                    tool_call_id=tool_call.id,
                    tool_name=tool_name,
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
    append_event(
        event_log_path,
        "tool_loop_limit_reached",
        {
            "session_id": session_id,
            "max_iterations": max_iterations,
        },
    )

    return "I stopped because the tool loop reached its iteration limit."
