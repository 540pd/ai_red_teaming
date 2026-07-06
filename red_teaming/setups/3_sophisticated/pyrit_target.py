"""PyRIT custom target — bridges the shared HttpTarget seam into PyRIT.

PyRIT orchestrators drive a `PromptTarget`. This wraps our config-defined
HttpTarget as one, so Setup 3 tests the SAME app definition as Setups 1 & 2.

NOTE: PyRIT's API moves fast between releases. This follows the documented
custom-target pattern (subclass PromptChatTarget, implement send_prompt_async);
if you hit an import/signature error, check it against your installed pyrit
version — this is the most version-sensitive file in the repo.

Docs: https://azure.github.io/PyRIT
"""

from __future__ import annotations

from redteam_core.adapters import HttpTarget

# Imported lazily inside the class so the module imports even without pyrit installed.


def build_target(target_name: str = "chat_endpoint"):
    """Construct a PyRIT target wrapping config/targets/<target_name>.yaml."""
    from pyrit.prompt_target import PromptChatTarget
    from pyrit.models import PromptRequestResponse, construct_response_from_request

    class RedTeamHttpTarget(PromptChatTarget):
        """Adapts redteam_core.HttpTarget to PyRIT's PromptChatTarget interface."""

        def __init__(self, name: str):
            super().__init__()
            self._target = HttpTarget.from_config(name)

        async def send_prompt_async(
            self, *, prompt_request: PromptRequestResponse
        ) -> PromptRequestResponse:
            piece = prompt_request.request_pieces[0]
            response_text = self._target.send(piece.converted_value)
            return construct_response_from_request(
                request=piece, response_text_pieces=[response_text]
            )

        def _validate_request(self, *, prompt_request: PromptRequestResponse) -> None:
            if len(prompt_request.request_pieces) != 1:
                raise ValueError("RedTeamHttpTarget supports one prompt piece at a time.")

        def is_json_response_supported(self) -> bool:
            return False

    return RedTeamHttpTarget(target_name)
