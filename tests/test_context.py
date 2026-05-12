from agint.context import build_model_context, should_retrieve_notes


def test_should_retrieve_notes_for_note_request():
    assert should_retrieve_notes("Find my notes about agents") is True


def test_should_not_retrieve_notes_for_regular_chat():
    assert should_retrieve_notes("What tasks do I have open?") is False


def test_build_model_context_includes_retrieved_context():
    messages = build_model_context(
        [{"role": "user", "content": "Find my notes about agents"}],
        retrieved_context="1. agents_v1.md\nPlan content,",
    )

    assert messages[0]["role"] == "system"
    assert "Relevant retrieved notes" in messages[1]["content"]
    assert messages[-1]["content"] == "Find my notes about agents"
