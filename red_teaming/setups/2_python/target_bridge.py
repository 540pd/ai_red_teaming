"""Bridges the shared HttpTarget seam to each Setup 2 tool's expected interface.

One target definition (config/targets/<name>.yaml) → three tool-shaped adapters:
  - DeepTeam wants an async  model_callback(input:str) -> str
  - Giskard  wants a sync    predict(pd.DataFrame) -> list[str]
  - DeepEval consumes plain  target.send(prompt) -> str  (used directly)

This keeps all three setups pointed at the SAME app definition — change the
endpoint once in config/, everything follows.
"""

from __future__ import annotations

from redteam_core.adapters import HttpTarget

DEFAULT_TARGET = "chat_endpoint"


def get_target(name: str = DEFAULT_TARGET) -> HttpTarget:
    return HttpTarget.from_config(name)


def make_deepteam_callback(target: HttpTarget):
    """DeepTeam expects an async callback returning the model's response text."""

    async def model_callback(input: str) -> str:
        return target.send(input)

    return model_callback


def make_giskard_predict(target: HttpTarget, feature: str = "question"):
    """Giskard expects a function taking a DataFrame and returning a list of strings."""

    def predict(df):
        return [target.send(q) for q in df[feature]]

    return predict
