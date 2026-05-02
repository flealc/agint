from agint.config import load_settings
from agint.events import append_event
from agint.approvals import request_approval

from pathlib import Path

from agint.memory.sqlite_store import SQLiteStore
from agint.tools.tasks import create_task, list_tasks
from agint.tools.registry import build_tools
from agint.agent_loop import run_agent_turn
from agint.context import initial_messages, append_user_message


def print_help() -> None:
    print(
        """
Commands:
    /help           Show this help message
    /tools          List available model tools
    /tasks          List open tasks
    /task <title>   Create a task manually with approval
    /quit           Exit
    
Anything else is sent to the assistant.
""".strip()
    )


def main():
    settings = load_settings()

    store = SQLiteStore(settings.database_path)
    schema_path = Path(__file__).parent / "memory" / "schema.sql"
    store.init_schema(schema_path)
    tools = build_tools(store)

    session_id = "local-cli"

    messages = initial_messages()

    print("agint local assistant")
    print(f"default model alias: {settings.default_model_alias}")
    print("Type '/help' for commands, or '/quit' to stop.")

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() in {"exit", "quit", "/exit", "/quit"}:
            break

        if not user_message:
            continue

        if user_message == "/help":
            print_help()
            continue

        if user_message.startswith("/task "):
            title = user_message.removeprefix("/task").strip()

            approved = request_approval(
                "tasks.create",
                {
                    "title": title,
                    "source": "manual",
                },
            )

            append_event(
                settings.event_log_path,
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
                continue

            task = create_task(store, title=title)
            print(f"\nCreated task #{task['id']}: {task['title']}")
            continue

        if user_message == "/tasks":
            tasks = list_tasks(store)

            if not tasks:
                print("\nNo open tasks.")
            else:
                print("\nOpen tasks:")
                for task in tasks:
                    print(f"- #{task['id']}: {task['title']}")
            continue

        if user_message == "/tools":
            print("\nAvailable tools:")
            for tool in tools.values():
                approval = "approval required" if tool.approval_required else "safe"
                print(f"- {tool.name}: {approval}")
            continue

        if user_message.startswith("/"):
            print(f"\nUnknown command: {user_message}")
            print("Type /help to see available commands.")
            continue

        append_event(
            settings.event_log_path,
            "user_message",
            {
                "session_id": session_id,
                "content": user_message,
            },
        )

        append_user_message(messages, user_message)

        append_event(
            settings.event_log_path,
            "model_call",
            {
                "session_id": session_id,
                "model_alias": settings.default_model_alias,
                "message_count": len(messages),
                "tool_count": len(tools),
            },
        )

        assistant_message = run_agent_turn(
            session_id=session_id,
            event_log_path=settings.event_log_path,
            messages=messages,
            tools=tools,
            model_alias=settings.default_model_alias,
        )

        print(f"\nAssistant: {assistant_message}")


if __name__ == "__main__":
    main()
