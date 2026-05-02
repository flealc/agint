from agint.main import should_quit


def test_should_quit_accepts_quit_commands():
    assert should_quit("quit") is True
    assert should_quit("/quit") is True
    assert should_quit("exit") is True
    assert should_quit("/exit") is True


def test_should_quit_rejects_normal_text():
    assert should_quit("what tasks do I have open?") is False
