# Onboarding — start here

A 15-minute path from clone to running red-team scans. No prior context needed.

## What this is

A **workbench** for red-teaming an AI application exposed as an **HTTP endpoint**.
You point it at the endpoint and run attacks in three tiers of increasing power.
You do **not** ship this inside the app — you run it *against* the app.

Read [README.md](README.md) for the map and
[AI_RedTeaming_Asset_Design.md](AI_RedTeaming_Asset_Design.md) for the full rationale.

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Node 18+** — only for Setup 1 (promptfoo). Skip if you only use Setups 2/3.
- A **judge/attacker LLM key** (e.g. `OPENAI_API_KEY`) — needed by Setups 2 & 3,
  and by promptfoo's graders in Setup 1. Not needed just to test the plumbing.

## Step 1 — Install the shared core

```bash
python -m venv .venv && source .venv/bin/activate     # recommended
make install                                          # = pip install -e .
```

This installs `redteam_core` (the shared target seam + config loading) in editable
mode. Every setup depends on it.

## Step 2 — Prove the plumbing works (no real app needed)

The repo ships a local mock endpoint so you can verify everything before you have
access to the real application.

```bash
cp .env.example .env          # defaults already point at the mock
make mock                     # shell A: starts the mock on :8811
make smoke                    # shell B: exercises the target seam end-to-end
```

Expected: `PASS — the target seam works.` If you see that, the plumbing is good and
any later error is tool- or endpoint-specific.

## Step 3 — Point it at YOUR endpoint

This is the one integration step. Two parts:

### 3a. Secrets → `.env`

```bash
# .env
TARGET_CHAT_URL=https://your-app.example.com/v1/chat
TARGET_CHAT_API_KEY=your-real-key
```

### 3b. Request/response *shape* → `config/targets/chat_endpoint.yaml`

The app is defined **once** here; every setup reads it. The default assumes an
OpenAI-style shape. **Adjust two fields to match your endpoint:**

- `request_template` — how to build the request body. `{{prompt}}` is replaced
  with the attack text (auto JSON-escaped).
- `response_path` — where the reply text lives in the JSON response.

**Example — a custom endpoint** that takes `{"query": "..."}` and returns
`{"data": {"answer": "..."}}`:

```yaml
request_template: |
  {"query": "{{prompt}}"}
response_path: data.answer
```

Then re-run `make smoke` (against your real endpoint) to confirm.

> Setup 1's promptfoo/garak configs mirror this same shape in
> `setups/1_easy/promptfooconfig.yaml` and `garak_rest.json` — if you change the
> shape, update those two to match (they can't read the YAML directly).

## Step 4 — Run a setup

Pick a tier (see the table in [README.md](README.md)). Install its tools, then run:

```bash
# Setup 1 — Easy (YAML, broadest, needs Node)
make install-easy && make easy

# Setup 2 — Python (DeepTeam + Giskard + DeepEval)
make install-python && make python

# Setup 3 — Sophisticated (PyRIT, custom orchestration)
make install-sophisticated && make sophisticated MODE=single
```

Results land in `reports/<timestamp>_.../`.

## How to add a new target (e.g. a second app, or the RAG endpoint later)

1. Copy `config/targets/chat_endpoint.yaml` to `config/targets/my_app.yaml`.
2. Set its `url`/`headers`/`request_template`/`response_path` and add any new
   `${VARS}` to `.env`.
3. Point a setup at it: `python setups/2_python/run.py --target my_app`.

That's the whole "integrate with another app" story — one file.

## Where things live

| Path | What |
|---|---|
| `redteam_core/` | Shared package: target seam, config loading, reporting. **Edit rarely.** |
| `config/targets/` | App definitions (single source of truth). **Edit per app.** |
| `setups/1_easy/` | promptfoo + garak configs. **Edit to tune attacks.** |
| `setups/2_python/` | DeepTeam/Giskard/DeepEval runners. **Edit to tune vulns/metrics.** |
| `setups/3_sophisticated/` | PyRIT orchestrators. **Extend with custom attacks.** |
| `seeds/` | Attack corpora (fetch per `seeds/README.md`). |
| `reports/` | Run outputs (gitignored). |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Environment variable '...' is not set` | Copy `.env.example` → `.env` and fill it in. |
| `smoke` fails to connect | Start the mock (`make mock`) or check your real URL is reachable. |
| Wrong/empty reply text | `response_path` doesn't match your endpoint's JSON — fix it in the target YAML. |
| `... unavailable (No module named ...)` | Install that tier's tools (`make install-python`, etc.). |
| Setup 2/3 auth or judge errors | Set `OPENAI_API_KEY` (or your provider key) in `.env`. |
| PyRIT import/signature error | PyRIT's API is version-sensitive — see `setups/3_sophisticated/README.md`. |

## Golden rule

**Define the app once in `config/targets/`. Never hardcode an endpoint inside a
setup.** That's what keeps all three tiers pointed at the same target.
