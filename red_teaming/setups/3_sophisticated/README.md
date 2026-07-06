# Setup 3 — Sophisticated (PyRIT + DeepEval)

The escalation tier. Reserved for what Setups 1 & 2 **cannot** express: custom
attack orchestration, adaptive multi-turn attacker-LLM loops, custom converter
chains, and deep RAG indirect-injection scenarios.

> **This is a skeleton to grow into, not a finished tool.** The value of Setup 3 is
> the custom orchestrators *you* add under `orchestrators/`. What's here is a
> working scaffold and two example orchestrators to build on.

## Layout

```
pyrit_target.py            # bridges the shared HttpTarget seam into a PyRIT target
orchestrators/
  single_turn.py           # send prompts through converter chains (encoding evasion)
  multi_turn.py            # ADAPTIVE attacker-LLM vs target loop — the crown jewel
scorers/
  deepeval_scorer.py       # grade PyRIT results with DeepEval metrics (reuses Setup 2)
run.py                     # entrypoint: --mode single | multi
```

## Prerequisites

```bash
# From repo root
cp .env.example .env       # target + attacker/judge key (e.g. OPENAI_API_KEY)
pip install -e .           # shared core
pip install pyrit deepeval
```

## Run

```bash
python setups/3_sophisticated/run.py --mode single   # converters + batch prompts
python setups/3_sophisticated/run.py --mode multi     # adaptive attacker-LLM loop
```

- **single** — sends objective prompts through a converter stack (Base64 / ROT13 /
  Leetspeak) at the target. Good for evasion coverage.
- **multi** — an attacker LLM converses with the target, adapting each turn, while a
  scorer judges whether the objective was achieved. Needs an attacker LLM key.

## When to reach for Setup 3

- Setup 1/2 attacks are exhausted and the target still needs deeper probing.
- You need **adaptive** attacks (attacker reacts to the target's replies).
- You want **custom attack chains** or novel strategies not shipped by other tools.
- Deep **RAG indirect-injection** scenarios via crafted retrieved content.

## Extending

- **New orchestrators:** add modules under `orchestrators/` and wire them into
  `run.py`'s `--mode`. This is where most of your work lives.
- **Custom converters:** compose any `pyrit.prompt_converter` in `single_turn.py`.
- **Live scoring:** implement `scorers/deepeval_scorer.py::to_pyrit_scorer()` to score
  each turn inside an orchestrator; otherwise use `score_pairs()` post-hoc.

## Version note

PyRIT's API changes across releases (orchestrator names, `run_attack_async`
signatures, target base classes). `pyrit_target.py` and the orchestrators follow
the documented patterns but are the **most version-sensitive** files in the repo —
if you hit an import/signature error, reconcile against your installed `pyrit`
version and the docs at https://azure.github.io/PyRIT.
