from typing import Any

from agint.config import MODEL_ALIASES


def call_model(
    messages: list[dict[str, Any]],
    tools=None,
    model_alias: str = "default",
    **kwargs,
):
    # this is imported here to avoid delay and load it lazily on first model call.
    # TODO: do this more cleanly later to configure litellm cost-map download behavior
    from litellm import completion

    model = MODEL_ALIASES[model_alias]

    return completion(
        model=model,
        messages=messages,
        tools=tools,
        **kwargs,
    )
