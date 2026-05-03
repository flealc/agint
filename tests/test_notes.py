import pytest

from agint.tools.notes import read_note, resolve_note_path


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
