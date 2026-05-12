from typing import Any

SYSTEM_PROMPT = """You are a local personal assistant.
You help with notes, tasks, reminders, calendar planning, and summaries.

You may use available tools when they are relevant.
You may summarize, rewrite, organize, and explain note content after reading it with a tool.

For write actions, the app will ask the user for approval before committing 
changes.

Do not claim that you created, updated, or listed something unless:
    - you used a tool successfully, or 
    - the user explicitly provided that information in the conversation.

When a user asks you to read and summarize a note:
    1. Use the note-reading tool.
    2. Summarize the note content directly.
    3. Do not say you are unable to summarize unless the tool failed or the content is unavailable
"""

NOTE_RETRIEVAL_TRIGGERS = [
    "search my notes",
    "search notes",
    "find notes",
    "find my notes",
    "look in my notes",
    "look in my vault",
    "what did i write",
    "what have i written",
    "summarize my notes",
    "notes about",
    "note about",
]


def initial_messages() -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]


def build_model_context(
    recent_messages: list[dict[str, Any]],
    retrieved_context: str | None = None,
) -> list[dict[str, Any]]:
    messages = initial_messages()

    if retrieved_context:
        messages.append(
            {
                "role": "system",
                "content": f"Relevant retrieved notes: \n{retrieved_context}",
            }
        )

    messages.extend(recent_messages)
    return messages


def should_retrieve_notes(user_message: str) -> bool:
    normalized = user_message.lower()
    return any(trigger in normalized for trigger in NOTE_RETRIEVAL_TRIGGERS)
