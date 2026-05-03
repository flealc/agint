from pathlib import Path
from datetime import datetime, timezone
import re


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


def slugify_title(title: str) -> str:
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "untitled"


def write_draft_note(
    vault_path: Path | None,
    title: str,
    content: str,
) -> dict:
    vault = require_vault_path(vault_path)

    draft_dir = vault / "drafts" / "agent drafts"
    draft_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{timestamp}-{slugify_title(title)}.md"
    path = draft_dir / filename

    if path.exists():
        raise FileExistsError(f"Draft already exists: {path.name}")

    markdown = f"# {title.strip()}\n\n{content.strip()}\n"
    path.write_text(markdown, encoding="utf-8")

    return {
        "path": str(path.relative_to(vault)),
        "title": title,
        "status": "draft_created",
    }
