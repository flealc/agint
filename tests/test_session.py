from agint.session import create_session_id


def test_create_session_id_has_prefix():
    session_id = create_session_id("test")

    assert session_id.startswith("test-")
    assert len(session_id.split("-")) == 3
