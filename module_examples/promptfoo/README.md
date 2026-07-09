# Promptfoo Red Teaming — Learning Workbench

A hands-on tutorial for red-teaming an LLM application with the **open-source**
[`promptfoo`](https://www.promptfoo.dev/docs/red-team/) CLI, built for learning rather than
production automation.

- **Notebook:** `promptfoo_redteam_tutorial.ipynb` — a step-by-step, runnable walkthrough.
- **This README:** the *why* behind the approach, plus a condensed run sequence you can follow
  straight from a terminal.

---

## Our approach and the constraints it's built around

This workbench was deliberately shaped by four choices. Understanding them explains why the
notebook looks the way it does.

1. **Open-source, no account, no email.** We use only the OSS CLI. Local evaluation and the local
   vulnerability report work fully offline. A promptfoo account/login is *only* needed for the
   optional hosted sharing dashboard, which we never use.

2. **Local / self-hosted attack generation.** By default some plugins and stronger strategies
   generate their attacks through promptfoo's remote inference API (free and accountless, but it
   sends prompts off-machine). We force generation onto a model *you* control — your own API key
   or a local model such as Ollama — so nothing leaves the laptop. The trade-off: local/open
   models produce weaker adversarial prompts than promptfoo's tuned remote generator.

3. **Target and LLM are already configured.** We assume you already have a working promptfoo
   *target* (HTTP endpoint, local model, custom provider, RAG/agent) and a generator model. The
   notebook only *points at* them — it never sets them up.

4. **Learning-first.** Every concept gets a plain-language explanation before any command. The CLI
   commands are written so you can **copy-paste them into a terminal**; you don't need the notebook
   to execute anything itself.

### The mental model everything hangs on

Red teaming in promptfoo is three composable parts:

| Part | Question | Examples |
|------|----------|----------|
| **Target** *(pre-configured)* | *Who* is under test? | your HTTP API / model / agent |
| **Plugins** | *What* do we attack with? | `harmful:hate`, `pii:direct`, `bola`, `sql-injection` |
| **Strategies** | *How* is it delivered? | `base64`, `rot13`, `jailbreak`, `crescendo`, `goat` |

**Plugins × Strategies = your attack matrix.** A plugin generates a malicious *intent*; a strategy
*wraps* that intent in an evasion technique.

### Why a notebook at all, if promptfoo is a CLI?

`promptfoo` is a **Node.js CLI**, not a Python library — there is no `import promptfoo` that does
the real work. The notebook is therefore an **orchestration + documentation layer**: markdown
teaches the concept, shell cells hold the exact command, and Python cells parse the JSON results
with `pandas` so you can inspect pass/fail rates inline. That's an ideal *learning* format —
concept, command, and result sit side by side — even though the CLI itself runs in a terminal.

---

## The workflow

```
  configure   ->    generate    ->      run / eval      ->     report
 (write YAML)     (make attacks)     (fire at target)      (read results)
```

- **generate** — expand `plugins × strategies × numTests` into concrete attacks (`redteam.yaml`).
  This is the step that uses your *local* generator. Nothing hits the target yet.
- **eval** — fire the generated attacks at the target and grade the responses; write JSON for
  analysis.
- **run** — generate + eval in a single command (convenience).
- **report** — open a local, offline vulnerability dashboard.

> **Scoring convention (important):** in red teaming a **passed** probe means the app **resisted**
> the attack; a **failed** probe is a **vulnerability**.

---

## Prerequisites (assumed already done on the target laptop)

- `promptfoo` installed and on `PATH` (`npm install -g promptfoo`, or use `npx promptfoo@latest`).
- A configured **target** (the system under test).
- A **local generator model** — either your own API key (e.g. `OPENAI_API_KEY`) or a local server
  (e.g. `ollama serve` with a pulled model like `llama3.3`).
- Optional, for the analysis cells: `python3` with `pandas` and `pyyaml`.

---

## Condensed run sequence (copy-paste into a terminal)

```bash
# 0) Force LOCAL attack generation and quiet the telemetry/update pings.
export PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true
export PROMPTFOO_DISABLE_TELEMETRY=true
export PROMPTFOO_DISABLE_UPDATE=true
# export OPENAI_API_KEY=sk-...        # if using your own key (skip for Ollama)

# 1) Work in a dedicated folder.
mkdir -p redteam_run && cd redteam_run

# 2) Create promptfooconfig.yaml (see the template below), then confirm it parses.
promptfoo --version

# 3) Build the attacks locally (nothing hits the target yet).
promptfoo redteam generate -c promptfooconfig.yaml -o redteam.yaml --delay 500 --force

# 4) Smoke-test on a handful before the full run.
promptfoo eval -c redteam.yaml -o results_smoke.json --filter-first-n 5 -j 2

# 5) Full run — fire every attack and write JSON for analysis.
promptfoo eval -c redteam.yaml -o redteam-results.json -j 3

# 6) Review findings in the local, offline dashboard (long-running server).
promptfoo redteam report          # http://localhost:15500
```

### Minimal `promptfooconfig.yaml`

```yaml
description: "Red-team scan (local generation)"

# TARGET — replace with YOUR already-configured target.
targets:
  - id: openai:chat:gpt-4o-mini      # placeholder
    label: target-under-test

prompts:
  - "{{prompt}}"                     # attack text is injected here

redteam:
  purpose: >
    Describe the app in detail: what it does, who its users are, what data and
    tools it can access, and what it must never do. This is the single biggest
    lever on attack quality.

  # LOCAL generator + grader. Pick ONE:
  provider:
    id: openai:chat:gpt-4o-mini      # (A) your own key
  # provider: ollama:chat:llama3.3   # (B) fully offline via Ollama
  # provider:                        # (C) OpenAI-compatible local server
  #   id: openai:chat:my-local-model
  #   config:
  #     apiBaseUrl: http://localhost:8000/v1
  #     apiKey: "{{ env.LOCAL_API_KEY }}"

  numTests: 5                        # attacks per plugin

  plugins:                           # WHAT to attack with
    - harmful:hate
    - pii:direct
    - contracts

  strategies:                        # HOW to deliver it
    - basic                          # raw, unmodified
    - base64                         # static encoding (fully local)
    - rot13                          # static encoding (fully local)
```

---

## Plugins and strategies at a glance

**Plugins (~157, six families)** — reference by single id (`harmful:hate`), object with
`numTests`, or a **collection** (`harmful`, `pii`, `default`, `owasp:llm`, `nist:ai`,
`mitre:atlas`). Framework collections double as compliance groupings in the report.

**Strategies — three tiers of increasing power and cost:**

| Tier | Type | Local? | Examples |
|------|------|--------|----------|
| 1 | Static / deterministic | ✅ fully local | `basic`, `base64`, `hex`, `rot13`, `leetspeak`, `morse`, `homoglyph` |
| 2 | Single-turn, LLM-driven | ⚠️ uses your `redteam.provider`; some want remote | `jailbreak`, `jailbreak:composite`, `best-of-n`, `math-prompt` |
| 3 | Multi-turn agents | ⚠️ heaviest; some want remote | `crescendo`, `goat`, `hydra`, `mischievous-user` |

With remote generation disabled, prefer **Tier 1** for guaranteed-offline runs and use iterative
**Tier 2** `jailbreak`/`crescendo` driven by your own model. If a strategy errors demanding remote
access, it isn't available offline — drop it.

---

## Discovering components & sizing your attack set

Before choosing what to run, enumerate what your installed version supports:

```bash
promptfoo redteam plugins             # full plugin catalog (ids + descriptions)
promptfoo redteam plugins --ids-only  # just ids — paste straight into a config
promptfoo redteam plugins --default   # only the default plugin set
```

There is **no `redteam strategies` command**. Enumerate strategies either from the package
internals (best-effort, version-dependent) or the curated catalog baked into the notebook:

```bash
node -e 'const c=require("promptfoo/dist/src/redteam/constants");console.log(c.ALL_STRATEGIES.join("\n"))'
```

**Counting per plugin/strategy.** promptfoo has *no fixed prompt count per plugin* — each plugin
generates `numTests` cases (your choice), and every non-`basic` strategy transforms those into
more cases, so:

```
total ≈ (num_plugins × numTests) × num_strategies
```

Multi-turn strategies still produce one test case per base attack but run several turns (far more
time/tokens); a few *dataset* plugins draw from fixed pools instead of generating. The notebook
gives you both a **pre-generation estimate** (budget before committing) and, after `generate`, an
**exact plugin × strategy count matrix** read from `redteam.yaml` — your map for subsetting the
attack (drop heavy cells, or re-run with `--plugins` / `--strategies` / `-n` overrides).

## Command cheat-sheet

```
promptfoo redteam generate -c cfg.yaml -o redteam.yaml --force   # build attacks
promptfoo eval -c redteam.yaml -o redteam-results.json           # fire + grade (JSON)
promptfoo redteam run -c cfg.yaml                                # generate + eval in one
promptfoo redteam report                                        # local dashboard
promptfoo view -y                                               # eval results UI
```

Handy flags: `-n` attacks-per-plugin · `-j` concurrency (lower for rate limits) · `--delay <ms>`
pause between calls · `--no-cache` fresh calls · `--filter-first-n N` / `--filter-metadata k=v`
run a subset · `--strict` (on `redteam run`) fail on plugin errors for CI.

Env vars: `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` (force local),
`PROMPTFOO_DISABLE_TELEMETRY`, `PROMPTFOO_DISABLE_UPDATE`, `OPENAI_API_KEY` / `LOCAL_API_KEY`.

---

## Troubleshooting

- **Strategy demands remote access** → not available offline; drop it or give it a usable provider.
- **Local model rate-limits / stalls** → add `--delay 1000` and set `-j 1`.
- **Zero or weak attacks generated** → `purpose` too vague, or the local generator is too small;
  enrich `purpose` or use a stronger model behind your own key.
- **"passed" looks inverted** → correct: passed = app defended, failed = vulnerability.

---

## Files

| File | What it is |
|------|-----------|
| `promptfoo_redteam_tutorial.ipynb` | The full step-by-step learning notebook. |
| `README.md` | This overview: approach, workflow, condensed run steps. |

## References

- Red-team overview — https://www.promptfoo.dev/docs/red-team/
- Configuration — https://www.promptfoo.dev/docs/red-team/configuration/
- Plugins — https://www.promptfoo.dev/docs/red-team/plugins/
- Strategies — https://www.promptfoo.dev/docs/red-team/strategies/
- CLI reference — https://www.promptfoo.dev/docs/usage/command-line/
