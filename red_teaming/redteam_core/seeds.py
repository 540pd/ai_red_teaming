"""Seed corpus loading — shared attack prompt sets used across setups.

Place corpora under seeds/ as .txt (one prompt per line) or .jsonl (objects with
a "prompt" field). Standard sets: JailbreakBench, AdvBench, HarmBench (see
seeds/README.md for how to fetch them).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEEDS_DIR = REPO_ROOT / "seeds"


def load_seeds(name: str) -> list[str]:
    """Load a seed corpus by filename stem, e.g. load_seeds('advbench').

    Supports .txt (one prompt per line) and .jsonl (objects with a 'prompt' key).
    """
    txt = SEEDS_DIR / f"{name}.txt"
    jsonl = SEEDS_DIR / f"{name}.jsonl"
    if txt.exists():
        return [ln.strip() for ln in txt.read_text().splitlines() if ln.strip()]
    if jsonl.exists():
        prompts = []
        for line in jsonl.read_text().splitlines():
            if line.strip():
                prompts.append(json.loads(line)["prompt"])
        return prompts
    available = ", ".join(sorted(p.name for p in SEEDS_DIR.glob("*"))) or "(none)"
    raise FileNotFoundError(
        f"Seed corpus '{name}' not found in {SEEDS_DIR}. Available: {available}"
    )


def list_seeds() -> list[str]:
    return sorted(
        {p.stem for p in SEEDS_DIR.glob("*.txt")}
        | {p.stem for p in SEEDS_DIR.glob("*.jsonl")}
    )
