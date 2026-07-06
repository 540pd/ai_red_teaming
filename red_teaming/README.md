# AI Red-Teaming Asset

A modular, black-box **workbench** for security-testing AI applications exposed as
HTTP endpoints. Point it at an app's endpoint and run tiered red-team scans.

> **New here?** Start with **[ONBOARDING.md](ONBOARDING.md)** — clone to first scan in ~15 min.
> For the full rationale, see [AI_RedTeaming_Asset_Design.md](AI_RedTeaming_Asset_Design.md).

## Layout

```
redteam_core/     installable shared package — target seam, config loading, reporting
config/targets/   single source of truth: define each app-under-test once
seeds/            attack corpora (AdvBench, JailbreakBench, HarmBench)
examples/         local mock endpoint + smoke test (run the workbench with no real app)
setups/
  1_easy/         Promptfoo + Garak (YAML, no-code)          ← built
  2_python/       DeepTeam + Giskard + DeepEval              ← built
  3_sophisticated/ PyRIT + DeepEval (skeleton)               ← built
reports/          timestamped, tool-tagged run outputs
Makefile          common commands — run `make help`
```

## The three setups

| Setup | Tools | Config | Status |
|---|---|---|---|
| **1 — Easy** | Promptfoo + Garak | YAML | ✅ built |
| **2 — Python** | DeepTeam + Giskard + DeepEval | Python | ✅ built |
| **3 — Sophisticated** | PyRIT + DeepEval | Python | ✅ built (skeleton) |

## Quick start

```bash
# 1. Install the shared core
python -m venv .venv && source .venv/bin/activate
make install

# 2. Prove the plumbing works against the bundled mock (no real app/keys needed)
cp .env.example .env
make mock      # shell A
make smoke     # shell B  ->  expect "PASS — the target seam works."

# 3. Point at your real endpoint: edit .env + config/targets/chat_endpoint.yaml
#    (see ONBOARDING.md step 3)

# 4. Install a tier's tools and run it
make install-easy && make easy          # Setup 1
# make install-python && make python    # Setup 2
```

Run `make help` for all commands.

## The integration model

Everything reaches the app through **one seam**. Define an app once in
`config/targets/<name>.yaml`; every setup consumes it. Onboarding a new app = one file.

```python
from redteam_core.adapters import HttpTarget

target = HttpTarget.from_config("chat_endpoint")
print(target.send("Hello, who are you?"))
```

## Access model

**Black-box only** (API/endpoint, no model weights). Chat endpoint today; RAG-ready
via Giskard RAGET in Setup 2 when needed.
