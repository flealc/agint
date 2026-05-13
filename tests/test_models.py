import types

from agint.models import call_model


def test_call_model_accepts_extra_kwargs(monkeypatch):
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return "ok"

    fake_litellm = types.SimpleNamespace(completion=fake_completion)
    monkeypatch.setitem(__import__("sys").modules, "litellm", fake_litellm)

    result = call_model(
        [{"role": "user", "content": "hello"}],
        model_alias="default",
        response_format={"type": "json_object"},
    )

    assert result == "ok"
    assert captured["response_format"] == {"type": "json_object"}
