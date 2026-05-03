import pytest

from agint.tools.notes import (
    read_note,
    resolve_note_path,
    slugify_title,
    write_draft_note,
)


def test_resolve_note_path_stays_inside_vault(tmp_path):
    note = tmp_path / "folder" / "note.md"
    note.parent.mkdir()
    note.write_text(
        "hello",
        encoding="utf-8",
    )

    resolved = resolve_note_path(tmp_path, "folder/note.md")

    assert resolved == note.resolve()


def test_resolve_note_path_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        resolve_note_path(tmp_path, "../secret.md")


def test_resolve_note_path_requires_markdown(tmp_path):
    with pytest.raises(ValueError):
        resolve_note_path(tmp_path, "note.txt")


def test_read_node_reads_markdown(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("# Hello", encoding="utf-8")

    result = read_note(tmp_path, "note.md")

    assert result["path"] == "note.md"
    assert result["content"] == "# Hello"


def test_slugify_titile():
    assert slugify_title("My Draft Note!") == "my-draft-note"


def test_write_draft_note_creates_markdown_draft(tmp_path):
    result = write_draft_note(
        tmp_path,
        title="My Draft",
        content="Hello world",
    )

    draft_path = tmp_path / result["path"]

    assert result["status"] == "draft_created"
    assert result["path"].startswith("drafts/agent drafts/")
    assert draft_path.exists()
    assert draft_path.read_text(encoding="utf-8") == "# My Draft\n\nHello world\n"
