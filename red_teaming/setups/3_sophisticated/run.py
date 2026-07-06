"""Setup 3 (Sophisticated) entrypoint — PyRIT custom orchestration.

Run from the repo root:
    python setups/3_sophisticated/run.py --mode single   # converters, batch
    python setups/3_sophisticated/run.py --mode multi     # adaptive attacker-LLM loop

This is a skeleton to grow: the value of Setup 3 is the custom orchestrators you
add under orchestrators/. Needs pyrit installed and (for --mode multi) an attacker
LLM key such as OPENAI_API_KEY in .env.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Make sibling modules (pyrit_target, orchestrators/, scorers/) importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def _main(mode: str, target_name: str):
    from pyrit.common import initialize_pyrit, IN_MEMORY

    import pyrit_target

    initialize_pyrit(memory_db_type=IN_MEMORY)
    target = pyrit_target.build_target(target_name)

    if mode == "single":
        from orchestrators import single_turn

        await single_turn.run(target)
    elif mode == "multi":
        from orchestrators import multi_turn

        await multi_turn.run(target)


def main():
    ap = argparse.ArgumentParser(description="Setup 3 (Sophisticated) PyRIT run")
    ap.add_argument("--mode", choices=["single", "multi"], default="single")
    ap.add_argument("--target", default="chat_endpoint", help="target config name")
    args = ap.parse_args()

    try:
        asyncio.run(_main(args.mode, args.target))
    except ImportError as exc:
        print(f"!! Setup 3 needs PyRIT: {exc}\n   Install with: pip install pyrit")
        sys.exit(1)


if __name__ == "__main__":
    main()
