"""HTTP target adapter — the single integration seam.

Wraps an app-under-test behind one method: send(prompt) -> response text.
Setups 2 and 3 use this directly; Setup 1 (promptfoo/garak) points at the same
endpoint via its own YAML/JSON config, but the *definition* lives in the same
config/targets/*.yaml file (see redteam_core.targets).
"""

from __future__ import annotations

import json
import re
from typing import Any

import requests

from redteam_core.targets import Target, load_target


def _extract(data: Any, path: str) -> str:
    """Follow a dotted/indexed path like 'choices[0].message.content' into JSON."""
    if not path:
        return data if isinstance(data, str) else json.dumps(data)
    current = data
    for token in path.split("."):
        for part in re.findall(r"[^\[\]]+", token):
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]
    return current if isinstance(current, str) else json.dumps(current)


class HttpTarget:
    """Drives an HTTP app-under-test defined in config/targets/<name>.yaml."""

    def __init__(self, target: Target):
        self.target = target

    @classmethod
    def from_config(cls, name: str) -> "HttpTarget":
        return cls(load_target(name))

    def _build_body(self, prompt: str) -> str:
        # Escape the prompt so it is safe to inject into the JSON template.
        safe = json.dumps(prompt)[1:-1]
        return self.target.request_template.replace("{{prompt}}", safe)

    def send(self, prompt: str) -> str:
        """Send one prompt to the target and return the extracted response text."""
        t = self.target
        body = self._build_body(prompt)
        resp = requests.request(
            method=t.method,
            url=t.url,
            headers=t.headers,
            data=body.encode("utf-8"),
            timeout=t.timeout,
        )
        resp.raise_for_status()
        try:
            payload = resp.json()
        except ValueError:
            return resp.text
        return _extract(payload, t.response_path)


if __name__ == "__main__":
    # Quick smoke test: python -m redteam_core.adapters.http_target
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "chat_endpoint"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Hello, who are you?"
    target = HttpTarget.from_config(name)
    print(f"[target] {target.target.name} -> {target.target.url}")
    print(f"[prompt] {prompt}")
    print(f"[reply ] {target.send(prompt)}")
