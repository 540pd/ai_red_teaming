"""Setup 2 (Python) orchestrator — DeepTeam + Giskard + DeepEval.

Run from the repo root:
    python setups/2_python/run.py                 # all three tools
    python setups/2_python/run.py --only giskard  # one tool
    python setups/2_python/run.py --target chat_endpoint

Each tool runs independently: if one is not installed or errors, the others
still run. Outputs land in reports/<timestamp>_<target>_python/.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback

# Make sibling modules (target_bridge, attacks_deepteam, ...) importable when
# this file is run as a script. Directory names starting with a digit can't be
# imported as packages, so we run as a script and add our own dir to the path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redteam_core import report  # noqa: E402

TOOLS = {
    "deepteam": ("attacks_deepteam", "pip install deepteam"),
    "giskard": ("scan_giskard", "pip install giskard"),
    "deepeval": ("scorers_deepeval", "pip install deepeval"),
}


def _run_tool(key: str, target: str, run_dir) -> bool:
    module_name, install_hint = TOOLS[key]
    print(f"\n==> {key}")
    try:
        module = __import__(module_name)
        module.run(target_name=target, run_dir=run_dir)
        return True
    except ImportError as exc:
        print(f"!! {key} unavailable ({exc}). Install with: {install_hint}")
        return False
    except Exception:
        print(f"!! {key} failed:")
        traceback.print_exc()
        return False


def main():
    ap = argparse.ArgumentParser(description="Setup 2 (Python) red-team run")
    ap.add_argument("--target", default="chat_endpoint", help="target config name")
    ap.add_argument(
        "--only",
        choices=list(TOOLS),
        help="run a single tool instead of all three",
    )
    args = ap.parse_args()

    run_dir = report.new_run_dir(f"{args.target}_python")
    print(f"Run directory: {run_dir}")

    keys = [args.only] if args.only else list(TOOLS)
    results = {k: _run_tool(k, args.target, run_dir) for k in keys}

    print("\n==> Summary")
    for k, ok in results.items():
        print(f"   {k:9s} {'ok' if ok else 'skipped/failed'}")
    print(f"\nOutputs in {run_dir}")


if __name__ == "__main__":
    main()
