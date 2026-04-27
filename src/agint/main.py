from agint.config import load_settings
from agint.models import call_model
from agint.events import append_event

SYSTEM_PROMPT = """You are a local personal assistant.
You help with notes tasks, reminders, calendar planning, and summaries.
For now, you cannot take actions. You can only chat and explain what you would do.
"""

def main():
  settings = load_settings()
  session_id = "local-cli"

  messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
  ]

  print("agint local assistant")
  print(f"default model alias: {settings.default_model_alias}")
  print("Type 'exit' or 'quit' to stop.")

  while True:
    user_message = input("\nYou: ").strip()

    if user_message.lower() in {"exit", "quit"}:
      break

    if not user_message:
      continue

    append_event(
      settings.event_log_path,
      "user_message",
      {
        "session_id": session_id,
        "content": user_message,
      }
    )
    
    messages.append({"role": "user", "content": user_message})

    append_event(
      settings.event_log_path,
      "model_call",
      {
        "session_id": session_id,
        "model_alias": settings.default_model_alias,
        "message_count": len(messages),
      },
    )
    response = call_model(
      messages=messages,
      model_alias=settings.default_model_alias
    )

    assistant_message = response.choices[0].message.content
    append_event(
      settings.event_log_path,
      "assistant_message",
      {
        "session_id": session_id,
        "contnent": assistant_message,
      },
    )
    messages.append({"role": "assistant", "content": assistant_message})

    print(f"\nAssistant: {assistant_message}")


if __name__ == "__main__":
  main()