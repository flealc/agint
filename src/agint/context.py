from typing import Any

SYSTEM_PROMPT = """You are a local personal assistant.
You help with notes, tasks, reminders, calendar planning, and summaries.
You may use available tools when they are relevant.
For write actions, the app will ask the user for approval before committing 
changes.
Do not claim that you created, updated, or listed something unless you used a 
tool or the user explicitly provided that information.
"""


def initial_messages() -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]


def append_user_message(
    messages: list[dict[str, Any]],
    content: str,
) -> None:
    messages.append({"role": "user", "content": content})
