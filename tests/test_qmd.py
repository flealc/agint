from agint.retrieval.qmd import format_qmd_results


def test_format_qmd_results_handles_path_and_text():
    results = [
        {
            "path": "drafts/agent drafts/note.md",
            "text": "personal assistant note",
        }
    ]

    formatted = format_qmd_results(results)

    assert "1. drafts/agent drafts/note.md" in formatted
    assert "personal assistant note" in formatted


def test_format_qmd_results_truncates():
    results = [
        {
            "path": "note.md",
            "text": "x" * 100,
        }
    ]

    formatted = format_qmd_results(results, max_chars=20)

    assert formatted.endswith("[truncated]")
