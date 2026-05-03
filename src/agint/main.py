from agint.config import load_settings
from agint.events import append_event
from agint.approvals import request_approval

from pathlib import Path

from agint.memory.sqlite_store import SQLiteStore
from agint.tools.tasks import create_task, list_tasks
from agint.tools.registry import build_tools
from agint.agent_loop import run_agent_turn
from agint.session import create_session_id
from agint.context import build_model_context


QUIT_COMMANDS = {"exit", "quit", "/exit", "/quit"}


def print_help() -> None:
    print(
        """
Commands:
    /help               Show this help message
    /messages           Show recent persisted messages for this session
    /tools              List available model tools
    /tasks              List open tasks
    /task <title>       Create a task manually with approval
    /read-note <path>   Read a Markdown note by vault-relative path
    /draft <title>      Create a simple draft note with approval
    /quit               Exit
    
Anything else is sent to the assistant.
""".strip()
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

    append_event(
        event_log_path,
        "approval",
        {
            "session_id": session_id,
            "tool_name": "tasks.create",
            "tool_args": {
                "title": title,
                "source": "manual",
            },
            "approved": approved,
        },
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

    recent_messages = store.get_recent_messages(session_id, limit=10)
    model_messages = build_model_context(recent_messages)

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

    if handle_tools_command(user_message, tools=tools):
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

        append_event(
            event_log_path,
            "approval",
            {
                "session_id": session_id,
                "tool_name": "notes.write_draft",
                "tool_args": {
                    "title": title,
                    "content": "Manual draft creeated from /draft command.",
                },
                "approved": approved,
            },
        )

        if not approved:
            print("\nDraft creation cancelled.")
            return True

        try:
            result = tools["notes.write_draft"].handler(
                title=title,
                content="Manual draft creeated from /draft command.",
            )
        except Exception as exc:
            print(f"\nCould not create draft: {exc}")
            return True

        print(f"\nCreated draft: {result['path']}")
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
