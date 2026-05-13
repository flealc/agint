from agint.config import load_settings
from agint.events import append_event
from agint.approvals import request_approval

import json
from pathlib import Path

from agint.memory.sqlite_store import SQLiteStore
from agint.tools.tasks import create_task, list_tasks
from agint.tools.reminders import (
    create_reminder,
    list_reminders,
    parse_reminder_request,
)
from agint.tools.preferences import list_preferences, set_preference
from agint.tools.calendar import list_proposals, propose_event
from agint.tools.registry import build_tools
from agint.agent_loop import run_agent_turn
from agint.session import create_session_id
from agint.context import build_model_context, should_retrieve_notes
from agint.retrieval.qmd import format_qmd_results, qmd_search


QUIT_COMMANDS = {"exit", "quit", "/exit", "/quit"}


def print_help() -> None:
    print(
        """
Commands:
    /help                   Show this help message
    /messages               Show recent persisted messages for this session
    /tools                  List available model tools
    /tasks                  List open tasks
    /task <title>           Create a task manually with approval
    /reminders              List pending reminders
    /reminder <request>     Create a reminder from natural language
    /prefs                  List saved preferences
    /pref <key> <value>     Save a preference with approval
    /proposals              List calendar proposals
    /propose-event <start> <end> <title>
    /read-note <path>       Read a Markdown note by vault-relative path
    /draft <title>          Create a simple draft note with approval
    /search-notes <query>   Search notes with QMD
    /quit                   Exit
    
Anything else is sent to the assistant.
""".strip()
    )


def record_approval(
    *,
    store,
    event_log_path,
    session_id: str,
    tool_name: str,
    tool_args: dict,
    approved: bool,
) -> None:
    store.record_approval(
        session_id=session_id,
        tool_name=tool_name,
        tool_args_json=json.dumps(tool_args, ensure_ascii=False),
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


def handle_manual_task_command(
    user_message, *, store, session_id, event_log_path
) -> bool:
    if not user_message.startswith("/task "):
        return False

    title = user_message.removeprefix("/task ").strip()

    approved = request_approval(
        "tasks.create",
        {
            "title": title,
            "source": "manual",
        },
    )

    record_approval(
        store=store,
        event_log_path=event_log_path,
        session_id=session_id,
        tool_name="tasks.create",
        tool_args={
            "title": title,
            "source": "manual",
        },
        approved=approved,
    )

    if not approved:
        print("\nTask creation cancelled.")
        return True

    task = create_task(store, title=title)
    print(f"\nCreated task #{task['id']}: {task['title']}")
    return True


def handle_tasks_command(user_message, *, store) -> bool:
    if user_message != "/tasks":
        return False

    tasks = list_tasks(store)

    if not tasks:
        print("\nNo open tasks.")
    else:
        print("\nOpen tasks:")
        for task in tasks:
            print(f"- #{task['id']}: {task['title']}")

    return True


def handle_tools_command(user_message, *, tools) -> bool:
    if user_message != "/tools":
        return False

    print("\nAvailable tools:")
    for tool in tools.values():
        approval = "approval required" if tool.approval_required else "safe"
        print(f"- {tool.name}: {approval}")

    return True


def handle_reminders_command(user_message, *, store) -> bool:
    if user_message != "/reminders":
        return False

    reminders = list_reminders(store)

    if not reminders:
        print("\nNo pending reminders.")
    else:
        print("\nPending reminders:")
        for reminder in reminders:
            print(
                f"- #{reminder['id']}: {reminder['remind_at']} - {reminder['title']}"
            )

    return True


def handle_manual_reminder_command(
    user_message, *, store, session_id, event_log_path
) -> bool:
    if not user_message.startswith("/reminder "):
        return False

    reminder_text = user_message.removeprefix("/reminder ").strip()

    try:
        parsed = parse_reminder_request(reminder_text)
    except Exception as exc:
        print(f"\nCould not parse reminder: {exc}")
        return True

    if parsed.get("needs_clarification"):
        print(f"\n{parsed.get('clarification_question')}")
        return True

    title = parsed["title"]
    remind_at = parsed["remind_at"]

    approved = request_approval(
        "reminders.create",
        {
            "title": title,
            "remind_at": remind_at,
            "source": "manual",
            "original_text": reminder_text,
        },
    )

    record_approval(
        store=store,
        event_log_path=event_log_path,
        session_id=session_id,
        tool_name="reminders.create",
        tool_args={
            "title": title,
            "remind_at": remind_at,
            "source": "manual",
            "original_text": reminder_text,
        },
        approved=approved,
    )

    if not approved:
        print("\nReminder creation cancelled.")
        return True

    reminder = create_reminder(
        store,
        title=title,
        remind_at=remind_at,
    )

    print(f"\nCreated reminder #{reminder['id']}: {reminder['title']}")
    print(f"At: {reminder['remind_at']}")
    return True


def handle_preferences_command(
    user_message, *, store, session_id, event_log_path
) -> bool:
    if user_message == "/prefs":
        preferences = list_preferences(store)

        if not preferences:
            print("\nNo saved preferences.")
        else:
            print("\nSaved preferences:")
            for preference in preferences:
                print(f"- {preference['key']}: {preference['value']}")

        return True

    if not user_message.startswith("/pref "):
        return False

    rest = user_message.removeprefix("/pref ").strip()
    parts = rest.split(" ", 1)

    if len(parts) != 2:
        print("\nUsage: /pref <key> <value>")
        return True

    key, value = parts
    tool_args = {"key": key, "value": value}
    approved = request_approval("preferences.set", tool_args)
    record_approval(
        store=store,
        event_log_path=event_log_path,
        session_id=session_id,
        tool_name="preferences.set",
        tool_args=tool_args,
        approved=approved,
    )

    if not approved:
        print("\nPreference update cancelled.")
        return True

    preference = set_preference(store, key=key, value=value)
    print(f"\nSaved preference: {preference['key']} = {preference['value']}")
    return True


def handle_calendar_command(
    user_message, *, store, session_id, event_log_path
) -> bool:
    if user_message == "/proposals":
        proposals = list_proposals(store)

        if not proposals:
            print("\nNo calendar proposals.")
        else:
            print("\nCalendar proposals:")
            for proposal in proposals:
                print(
                    f"- #{proposal['id']}: {proposal['start_at']} - "
                    f"{proposal['end_at']} | {proposal['title']}"
                )

        return True

    if not user_message.startswith("/propose-event "):
        return False

    rest = user_message.removeprefix("/propose-event ").strip()
    parts = rest.split(" ", 2)

    if len(parts) != 3:
        print("\nUsage: /propose-event <start ISO> <end ISO> <title>")
        return True

    start_at, end_at, title = parts
    tool_args = {
        "title": title,
        "start_at": start_at,
        "end_at": end_at,
        "notes": None,
        "source": "manual",
    }
    approved = request_approval("calendar.propose_event", tool_args)
    record_approval(
        store=store,
        event_log_path=event_log_path,
        session_id=session_id,
        tool_name="calendar.propose_event",
        tool_args=tool_args,
        approved=approved,
    )

    if not approved:
        print("\nCalendar proposal cancelled.")
        return True

    proposal = propose_event(
        store,
        title=title,
        start_at=start_at,
        end_at=end_at,
        source="manual",
    )
    print(f"\nCreated calendar proposal #{proposal['id']}: {proposal['title']}")
    return True


def run_chat_turn(
    *,
    user_message: str,
    session_id: str,
    event_log_path,
    default_model_alias: str,
    tools,
    store,
) -> None:
    append_event(
        event_log_path,
        "user_message",
        {
            "session_id": session_id,
            "content": user_message,
        },
    )

    store.add_message(
        session_id=session_id,
        role="user",
        content=user_message,
    )

    retrieved_context = None

    if should_retrieve_notes(user_message):
        try:
            results = qmd_search(user_message, limit=5)
            retrieved_context = format_qmd_results(results)

            append_event(
                event_log_path,
                "notes_retrieved",
                {
                    "session_id": session_id,
                    "query": user_message,
                    "result_count": len(results),
                },
            )
        except Exception as exc:
            append_event(
                event_log_path,
                "notes_retrieval_failed",
                {
                    "session_id": session_id,
                    "query": user_message,
                    "error": str(exc),
                },
            )

    recent_messages = store.get_recent_messages(session_id, limit=10)
    model_messages = build_model_context(
        recent_messages,
        retrieved_context=retrieved_context,
    )

    append_event(
        event_log_path,
        "model_call",
        {
            "session_id": session_id,
            "model_alias": default_model_alias,
            "message_count": len(model_messages),
            "tool_count": len(tools),
        },
    )

    assistant_message = run_agent_turn(
        session_id=session_id,
        event_log_path=event_log_path,
        messages=model_messages,
        tools=tools,
        model_alias=default_model_alias,
        store=store,
    )

    print(f"\nAssistant: {assistant_message}")


# dispatcher
def handle_command(user_message, *, store, tools, session_id, event_log_path) -> bool:
    if user_message == "/help":
        print_help()
        return True

    if handle_manual_task_command(
        user_message,
        store=store,
        session_id=session_id,
        event_log_path=event_log_path,
    ):
        return True

    if handle_tasks_command(user_message, store=store):
        return True

    if handle_reminders_command(user_message, store=store):
        return True

    if handle_manual_reminder_command(
        user_message,
        store=store,
        session_id=session_id,
        event_log_path=event_log_path,
    ):
        return True

    if handle_tools_command(user_message, tools=tools):
        return True

    if handle_preferences_command(
        user_message,
        store=store,
        session_id=session_id,
        event_log_path=event_log_path,
    ):
        return True

    if handle_calendar_command(
        user_message,
        store=store,
        session_id=session_id,
        event_log_path=event_log_path,
    ):
        return True

    # temp debug command
    if user_message == "/messages":
        messages = store.get_recent_messages(session_id, limit=10)

        if not messages:
            print("\nNo persisted messages for this session")
        else:
            print("\nRecent persisted messages:")
            for message in messages:
                content = message.get("content") or ""
                print(f"- {message['role']}: {content[:120]}")

        return True

    if user_message.startswith("/read-note "):
        relative_path = user_message.removeprefix("/read-note ").strip()

        try:
            result = tools["notes.read"].handler(relative_path=relative_path)
        except Exception as exc:
            print(f"\nCould not read note: {exc}")
            return True

        print(f"\nNote: {result['path']}")
        print(result["content"][:2000])
        return True

    if user_message.startswith("/draft "):
        title = user_message.removeprefix("/draft ").strip()

        approved = request_approval(
            "notes.write_draft",
            {"title": title, "content": "Manual draft created from /draft command."},
        )

        record_approval(
            store=store,
            event_log_path=event_log_path,
            session_id=session_id,
            tool_name="notes.write_draft",
            tool_args={
                "title": title,
                "content": "Manual draft created from /draft command.",
            },
            approved=approved,
        )

        if not approved:
            print("\nDraft creation cancelled.")
            return True

        try:
            result = tools["notes.write_draft"].handler(
                title=title,
                content="Manual draft created from /draft command.",
            )
        except Exception as exc:
            print(f"\nCould not create draft: {exc}")
            return True

        print(f"\nCreated draft:\n {result['path']}")
        return True

    if user_message.startswith("/search-notes "):
        query = user_message.removeprefix("/search-notes ").strip()

        try:
            result = tools["notes.search"].handler(query=query, limit=5)
        except Exception as exc:
            print(f"\nCould not search notes: {exc}")
            return True

        print("\nSearch results:\n")
        print(result["formatted"] or "No results.")
        return True

    if user_message.startswith("/"):
        print(f"\nUnknown command: {user_message}")
        print("Type /help to see available commands.")
        return True

    return False


def should_quit(user_message: str) -> bool:
    return user_message.lower() in QUIT_COMMANDS


def log_session_start(
    event_log_path, store, session_id: str, default_model_alias: str
) -> None:
    store.create_session(session_id)

    append_event(
        event_log_path,
        "session_start",
        {
            "session_id": session_id,
            "default_model_alias": default_model_alias,
        },
    )


def log_session_end(event_log_path, store, session_id: str) -> None:
    store.end_session(session_id)

    append_event(
        event_log_path,
        "session_end",
        {
            "session_id": session_id,
        },
    )


def main():
    settings = load_settings()
    event_log_path = settings.event_log_path
    default_model_alias = settings.default_model_alias
    obsidian_vault_path = settings.obsidian_vault_path

    store = SQLiteStore(settings.database_path)
    schema_path = Path(__file__).parent / "memory" / "schema.sql"
    store.init_schema(schema_path)
    tools = build_tools(store, obsidian_vault_path)

    session_id = create_session_id()

    print("agint local assistant")
    print(f"default model alias: {default_model_alias}")
    print(f"session id: {session_id}")
    print("Type '/help' for commands, or '/quit' to stop.")

    log_session_start(event_log_path, store, session_id, default_model_alias)

    while True:
        user_message = input("\nYou: ").strip()

        if should_quit(user_message):
            log_session_end(event_log_path, store, session_id)
            break

        if not user_message:
            continue

        if handle_command(
            user_message,
            store=store,
            tools=tools,
            session_id=session_id,
            event_log_path=event_log_path,
        ):
            continue

        run_chat_turn(
            user_message=user_message,
            session_id=session_id,
            event_log_path=event_log_path,
            default_model_alias=default_model_alias,
            tools=tools,
            store=store,
        )


if __name__ == "__main__":
    main()
