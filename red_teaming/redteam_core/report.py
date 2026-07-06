"""Reporting helpers — normalize and merge tool outputs into one place.

Each setup writes its raw tool output into a timestamped run directory under
reports/. This module provides a small normalized record so results from
different engines (promptfoo, garak, deepteam, ...) are comparable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"


@dataclass
class Finding:
    """One normalized red-team finding, tool-agnostic."""

    tool: str            # e.g. "promptfoo", "garak"
    target: str          # target name, e.g. "chat_endpoint"
    attack: str          # attack/probe class, e.g. "prompt-injection"
    passed: bool         # True = target resisted; False = attack succeeded
    prompt: str = ""
    response: str = ""
    detail: str = ""


def new_run_dir(target: str) -> Path:
    """Create reports/<UTC-date>_<target>/ for this run."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    run_dir = REPORTS_DIR / f"{stamp}_{target}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_findings(run_dir: Path, tool: str, findings: list[Finding]) -> Path:
    """Write normalized findings as JSON into the run directory."""
    out = run_dir / f"{tool}_findings.json"
    out.write_text(json.dumps([asdict(f) for f in findings], indent=2))
    return out


def summarize(findings: list[Finding]) -> dict:
    """Quick pass/fail tally for a set of findings."""
    total = len(findings)
    failed = sum(1 for f in findings if not f.passed)
    return {
        "total": total,
        "attacks_succeeded": failed,
        "attacks_resisted": total - failed,
        "resist_rate": round((total - failed) / total, 3) if total else None,
    }
