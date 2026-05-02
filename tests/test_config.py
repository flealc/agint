import pytest

from agint.config import choose_model


def test_choose_model_block_secrets():
    with pytest.raises(ValueError):
        choose_model("classification", sensitivity="secrets")


def test_choose_model_routes_extraction_to_fast():
    assert choose_model("extraction") == "fast"


def test_choose_model_routes_private_to_sensitive():
    assert choose_model("planning", sensitivity="private") == "sensitive"


def test_choose_model_defaults_to_default():
    assert choose_model("chat") == "default"
