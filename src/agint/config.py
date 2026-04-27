from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

MODEL_ALIASES = {
  "fast": "gemini/gemini-2.5-flash-lite",
  "default": "gemini/gemini-2.5-flash",
  "smart_low_sensitivity": "openrouter/moonshotai/kimi-k2-thinking",
  "sensitive": "anthropic/claude-sonnet-4.6",
  "final_review": "openai/gpt-5.4",
}

@dataclass(frozen=True)
class Settings:
  default_model_alias: str
  obsidian_value_path: Path | None
  database_path: Path
  event_log_path: Path

def load_settings() -> Settings:
  vault = os.getenv("OBSIDIAN_VAULT_PATH")

  return Settings(
    default_model_alias=os.getenv("DEFAULT_MODEL_ALIAS", "default"),
    obsidian_value_path=Path(vault).expanduser() if vault else None,
    database_path=Path(os.getenv("DATABASE_PATH", "data/assistant.db")),
    event_log_path=Path(os.getenv("EVENT_LOG_PATH", "logs/events.jsonl")),
  )

def choose_model(task_type: str, sensitivity: str = "low") -> str:
  if sensitivity in {"secrets", "credentials"}:
    raise ValueError("Do not send secrets or credentials to any model")
  
  if sensitivity in {"high", "private"}:
    return "sensitive"
  
  if task_type in {"classification", "exctraction", "reminder_parse"}:
    return "fast"
  
  if task_type in {"note_synthesis", "weekly_review", "planning"}:
    return "smart_low_sensitivity"

  return "default"
 