from agint.agent_loop import parse_tool_args, summarize_tool_result, has_tool_calls


def test_parse_tool_args_from_json_string():
    assert parse_tool_args('{"title": "Buy coffee"}') == {"title": "Buy coffee"}


def test_parse_tools_args_none_is_empty_dict():
    assert parse_tool_args(None) == {}


def test_summarize_tools_result_returns_json():
    assert summarize_tool_result({"ok": True}) == '{"ok": true}'


def test_has_tool_calls():
    assert has_tool_calls({"tool_calls": ["call"]}) is True
    assert has_tool_calls({"tool_calls": None}) is False
