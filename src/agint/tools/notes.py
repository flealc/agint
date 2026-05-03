from pathlib import Path


def require_vault_path(vault_path: Path | None) -> Path:
    if vault_path is None:
        raise ValueError("OBSIDIAN_VAULT_PATH is not configured")

    return vault_path.expanduser().resolve()


def resolve_note_path(vault_path: Path | None, relative_path: str) -> Path:
    vault = require_vault_path(vault_path)
    candidate = (vault / relative_path).expanduser().resolve()

    if not candidate.is_relative_to(vault):
        raise ValueError("Note path must stauy inside the Obsidian vault")

    if candidate.suffix != ".md":
        raise ValueError("Only Markdown .md files are supported")

    return candidate


def read_note(vault_path: Path | None, relative_path: str) -> dict:
    path = resolve_note_path(vault_path, relative_path)

    if not path.exists():
        raise FileNotFoundError(f"Note not found: {relative_path}")

    return {
        "path": relative_path,
        "content": path.read_text(encoding="utf-8"),
    }
