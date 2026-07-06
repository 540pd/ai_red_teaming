"""Target loading — the single source of truth for apps under test.

A "target" is defined once in config/targets/*.yaml and consumed by every setup.
This module loads that YAML, resolves ${ENV_VARS} from the environment (.env),
and returns a Target the HTTP adapter can drive.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Repo root = two levels up from this file (redteam_core/targets.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parent.parent
TARGETS_DIR = REPO_ROOT / "config" / "targets"

# Load .env once on import so ${VARS} resolve.
load_dotenv(REPO_ROOT / ".env")

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _resolve_env(value: Any) -> Any:
    """Recursively replace ${VAR} tokens with environment values."""
    if isinstance(value, str):
        def repl(match: re.Match) -> str:
            var = match.group(1)
            resolved = os.environ.get(var)
            if resolved is None:
                raise KeyError(
                    f"Environment variable '{var}' referenced in target config "
                    f"is not set. Add it to .env (see .env.example)."
                )
            return resolved
        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


@dataclass
class Target:
    """A configured app-under-test. Consumed by redteam_core.adapters.http_target."""

    name: str
    url: str
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    # Request body template; the literal token {{prompt}} is replaced at send time.
    request_template: str = '{"prompt": "{{prompt}}"}'
    # Dotted/indexed path into the JSON response to extract the model's text,
    # e.g. "choices[0].message.content".
    response_path: str = ""
    timeout: int = 60

    @property
    def raw(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "request_template": self.request_template,
            "response_path": self.response_path,
            "timeout": self.timeout,
        }


def load_target(name: str) -> Target:
    """Load config/targets/<name>.yaml into a Target, resolving env vars.

    >>> load_target("chat_endpoint")
    """
    path = TARGETS_DIR / f"{name}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in TARGETS_DIR.glob("*.yaml")) or "(none)"
        raise FileNotFoundError(
            f"Target '{name}' not found at {path}. Available: {available}"
        )
    data = yaml.safe_load(path.read_text()) or {}
    data = _resolve_env(data)
    known = {f for f in Target.__dataclass_fields__}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"Unknown keys in {path.name}: {sorted(unknown)}")
    return Target(**data)


def list_targets() -> list[str]:
    """Names of all defined targets."""
    return sorted(p.stem for p in TARGETS_DIR.glob("*.yaml"))
