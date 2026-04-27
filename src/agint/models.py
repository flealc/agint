from litellm import completion

from agint.config import MODEL_ALIASES


def call_model(messages, tools=None, model_alias: str = "default"):
  model = MODEL_ALIASES[model_alias]

  return completion(
    model=model,
    messages=messages,
    tools=tools,
  )