# AI Red-Teaming Asset — Design & Tooling Document

**Status:** Finalized (v1) — all three setups scaffolded
**Last updated:** 2026-07-06
**Owner:** babrik.kushwaha@gmail.com

> **Implementation status:** Setups 1–3 are scaffolded and the shared plumbing is
> verified end-to-end (target seam, env resolution, orchestrator degradation). The
> third-party tool APIs (promptfoo, garak, deepteam, giskard, deepeval, pyrit) are
> written to their docs but not yet executed against a live endpoint — expect minor
> version reconciliation on first real run. New contributors: see
> [ONBOARDING.md](ONBOARDING.md).

---

## 1. Purpose

This document defines the tools, architecture, and design decisions for our
**AI red-teaming asset** — a reusable workbench for security-testing AI
applications. It captures *what* tools we chose, *why*, and *how* they fit
together, so the setup is reproducible and the rationale is not lost.

The asset is:

- **Modular** — best-of-breed open-source components, each independently replaceable.
- **A workbench, not a shipped library** — we *point it at* an application's
  endpoint and run tests. It is not embedded inside the target app.
- **Tiered** — three setups of escalating power and effort, sharing one common layer.

---

## 2. Scope & Constraints

These constraints drove every tool decision below.

| Constraint | Decision |
|---|---|
| **Access model** | **Black-box** — API/endpoint only. No model weights. Rules out gradient-based (white-box) attacks. |
| **Integration meaning** | "Integration" = ability to **easily test against** an application, *not* to ship inside it. Workbench model. |
| **Target today** | Plain **chat endpoint** (send text → get text). |
| **Target future** | **RAG system** (retrieval-augmented). Must be supportable without re-architecture. |
| **Priority** | **Simple and easy to use**, with an escalation path for complex scenarios. |
| **Licensing** | Open-source tools only. |

---

## 3. The Three Setups

An escalation ladder: start simple, escalate only when a target demands it.

| | **Setup 1 — Easy** | **Setup 2 — Python** | **Setup 3 — Sophisticated** |
|---|---|---|---|
| **Core tools** | Promptfoo + Garak | DeepTeam + Giskard + DeepEval | PyRIT + DeepEval |
| **Config style** | YAML, no code | Python (light, declarative) | Python (full framework) |
| **Runtime** | Node + Python | Pure Python | Pure Python |
| **Effort to first result** | Minutes | ~An hour | Real engineering |
| **Attack depth** | Broad, prebuilt | Broad + multi-turn + audit | Custom, adaptive, unbounded |
| **RAG capability** | Basic (injection probes) | Yes (Giskard RAGET) | Yes (custom + RAGET) |
| **Who runs it** | Anyone | Python developer | Red-team engineer |
| **Best for** | Daily sweeps, CI, onboarding | Balanced Python automation | Hard targets, novel attacks, research |

### 3.1 Setup 1 — Easy (YAML, turnkey)

- **Tools:** Promptfoo (core, YAML) + Garak (breadth scanner).
- **How it works:** Declare an HTTP target and a list of attack plugins in
  `promptfooconfig.yaml`, run, read the generated HTML report. Garak adds a
  second, independent probe catalog via one CLI command.
- **Capabilities:** Prompt injection, jailbreak, PII/data leakage, toxicity,
  encoding attacks — all prebuilt. Some multi-turn.
- **Tradeoff:** Carries a **Node** runtime (promptfoo is JS). Ceiling is limited
  to shipped plugins — no deep custom logic.
- **Role:** The **default front door.** Run on every application first.

### 3.2 Setup 2 — Python (balanced)

- **Tools:** DeepTeam (attacks) + Giskard/RAGET (scan + report) + DeepEval (scoring).
- **How it works:** Wrap the endpoint in a `model_callback(prompt) -> response`.
  DeepTeam generates adversarial cases; Giskard runs an automated scan and
  produces a polished report; DeepEval scores custom metrics. Pure Python, no Node.
- **Capabilities:** Injection, jailbreak, encoding, **multi-turn (crescendo/linear)**,
  bias/toxicity/PII, hallucination detection, **RAG-specific testing (RAGET)**,
  native scoring + CI integration.
- **Role division (avoids redundancy):**
  - **DeepTeam** = offense (adversarial attack generation)
  - **Giskard** = audit (broad auto-scan + client-ready report)
  - **DeepEval** = measurement (custom pass/fail metrics, CI gating)
- **Tradeoff:** It is code — but light, declarative code, one Python ecosystem.
- **Role:** The **pure-Python option.** Also **RAG-capable on its own** via RAGET.

### 3.3 Setup 3 — Sophisticated Python (max power)

- **Tools:** PyRIT (orchestration) + DeepEval (scoring). Giskard/RAGET reusable here too.
- **How it works:** Author custom **orchestrators** — attacker-LLM vs. target
  loops, adaptive multi-turn strategies, custom converters/attack chains, agent
  tool-abuse scenarios.
- **Capabilities:** Everything above **plus** anything expressible in code —
  novel attacks, adaptive conversations, deep RAG indirect-injection, research-grade experiments.
- **Tradeoff:** Real build-and-maintain effort; steepest learning curve.
- **Role:** **Escalation only** — reserved for what Setups 1–2 cannot express.

---

## 4. Architecture

```
                 ┌─────────────────────────────────────────┐
                 │        config/  (targets + seeds)         │
                 │   shared across all three setups          │
                 └───────────────────┬──────────────────────┘
                                     │
   ┌─────────────────────────────────┼─────────────────────────────────┐
   ▼                                 ▼                                 ▼
┌─────────────────┐        ┌──────────────────────┐        ┌────────────────────┐
│ SETUP 1 — EASY  │        │  SETUP 2 — PYTHON     │        │ SETUP 3 — SOPHIST. │
│ Promptfoo+Garak │        │ DeepTeam+Giskard+     │        │ PyRIT + DeepEval   │
│ (YAML)          │        │ DeepEval (Python)     │        │ (Python framework) │
└────────┬────────┘        └──────────┬───────────┘        └─────────┬──────────┘
         │                            │                              │
         └──────── all reach the same TARGET SEAM ───────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │    TARGET SEAM      │  ← the one integration point
                          │  send(prompt)->resp │
                          └──────────┬──────────┘
                                     │  HTTP
                          ┌──────────▼──────────┐
                          │  AI APP UNDER TEST  │  chat endpoint (→ RAG later)
                          └─────────────────────┘

  results (JSON) ──► runner ──► unified report (HTML/JSON)
```

### The one abstraction that matters: the Target Seam

"Integration = easily test against any app" reduces to **one seam** — the point
where a tool is told the app's endpoint and how to send/receive. Every tier
already provides this:

| Setup | Target seam |
|---|---|
| 1 — Easy | HTTP target block in YAML |
| 2 — Python | a `model_callback(prompt) -> response` function |
| 3 — Sophisticated | a `PromptTarget` class |

**Onboarding a new app = configure the target once, rerun.** Nothing downstream
(attacks, scoring, reports) changes.

---

## 5. Repository Layout

```
ai-redteam-asset/
├── redteam_core/               # shared logic, as an INSTALLABLE package (pip install -e .)
│   ├── __init__.py
│   ├── adapters/
│   │   └── http_target.py        # send(prompt)->resp
│   ├── targets.py                # loads config/targets/*.yaml → objects
│   ├── seeds.py                  # loads seed corpora
│   └── report.py                 # merges tool outputs → unified report
│
├── config/                     # SINGLE SOURCE OF TRUTH for app definitions
│   ├── targets/
│   │   ├── chat_endpoint.yaml     # the app under test (now) — URL, headers, req/resp shape
│   │   └── rag_endpoint.yaml      # (later)
│   └── settings.yaml             # global defaults
│
├── seeds/                        # attack corpora (JailbreakBench, AdvBench, HarmBench)
│
├── examples/                     # onboarding aids — run the workbench with no real app
│   ├── mock_endpoint.py          # local OpenAI-shaped chat server for testing
│   └── smoke_test.py             # verifies the target seam end-to-end
│
├── setups/
│   ├── 1_easy/                   # Promptfoo + Garak (YAML)
│   │   ├── promptfooconfig.yaml
│   │   ├── garak_rest.json
│   │   └── run.sh
│   ├── 2_python/                 # DeepTeam + Giskard + DeepEval
│   │   ├── attacks_deepteam.py
│   │   ├── scan_giskard.py
│   │   ├── scorers_deepeval.py
│   │   └── run.py
│   └── 3_sophisticated/          # PyRIT + DeepEval
│       ├── orchestrators/          # PyRIT custom attack logic
│       ├── scorers/                # DeepEval metrics
│       └── run.py
│
├── reports/                      # timestamped, per-run, tool-tagged (e.g. 2026-07-06_chat/)
│
├── .env.example                  # endpoint URLs / API keys (NEVER commit real .env)
├── .gitignore
├── Makefile                      # common commands (make help)
├── ONBOARDING.md                 # 15-min start-here guide for new contributors
├── pyproject.toml                # defines redteam_core as an installable package
├── setup.py                      # shim for editable install on older pip
├── requirements.txt              # Python deps
├── package.json                  # promptfoo (Node) — isolated to setup 1
└── README.md
```

**Key principles:**

1. **`redteam_core/` is an installable package** — `pip install -e .` once, then any
   setup does `from redteam_core.targets import load_target`. Editable install means
   changes take effect immediately. This makes reuse real, not relative-path hacks.
2. **`config/targets/` is the single source of truth** — an app is defined *once*.
   Promptfoo reads the YAML natively; setups 2/3 read the *same* YAML via
   `redteam_core.targets`. Onboarding a new app = one file, not three edits.
3. **Setups differ only in engine, not in how they reach the app** — all share the
   target seam.
4. **Node is isolated to `setups/1_easy/`** — Python-only users never touch npm.
5. **Secrets live in `.env`, not in committed YAML** — target YAML holds structure
   and references `${VARS}`; real URLs/keys come from `.env` (gitignored).
6. **Reports are centralized and tagged** by run + target, so findings are comparable
   across setups.

---

## 6. Tool Reference

### Setup 1

**Promptfoo** — primary red-team harness
- *What:* Provider-agnostic red-team + eval tool. Generates adversarial cases
  from plugins (injection, jailbreak, PII leak, toxicity, hijacking), runs them
  at your endpoint, grades with built-in graders.
- *Install:* `npm install -g promptfoo` (Node ≥18)
- *Config:* `promptfooconfig.yaml` — declare target, pick `redteam.plugins`, run `promptfoo redteam run`.
- *Output:* JSON + browsable HTML report.

**Garak** (NVIDIA) — breadth scanner
- *What:* "nmap for LLMs." Large independent probe catalog; complements promptfoo.
- *Install:* `pip install garak`
- *Config:* CLI, e.g. `garak --model_type rest -G garak_rest.json --probes promptinject,encoding,leakreplay`
- *Output:* JSONL report + hit log.

### Setup 2

**DeepTeam** — pure-Python red-team framework (offense)
- *What:* Attack layer built on DeepEval. Define vulnerabilities + attack methods
  (injection, jailbreak, leetspeak/ROT13, multi-turn crescendo/linear); auto-generates and scores.
- *Install:* `pip install deepteam`
- *Config:* Python; wrap endpoint in a `model_callback`.

**Giskard** (+ RAGET) — audit scanner + report
- *What:* `giskard.scan()` auto-detects hallucination, injection, harmfulness with
  polished reports. **RAGET** (RAG Evaluation Toolkit) tests retrieval-specific failures.
- *Install:* `pip install giskard`
- *Config:* Python; wrap endpoint in a `giskard.Model`.
- *Role:* Broad audit + client-ready report; RAG testing when RAG lands.

**DeepEval** — scoring / measurement
- *What:* Pytest-style LLM metrics; red-team checks in CI, regression tracking.
- *Install:* `pip install deepeval`
- *Config:* Python test files; endpoint via callback.

### Setup 3

**PyRIT** (Microsoft) — orchestration framework
- *What:* Python framework to *build* attack orchestration. Swappable
  `PromptTarget` / `PromptConverter` / `Scorer` + orchestrators for adaptive,
  multi-turn, attacker-LLM-driven campaigns.
- *Install:* `pip install pyrit`
- *Config:* Python code (classes, orchestrators).
- *Use when:* you outgrow the framework tools and need custom/adaptive logic.

---

## 7. Attack Coverage Matrix

| Attack class | Setup 1 | Setup 2 | Setup 3 |
|---|:---:|:---:|:---:|
| Prompt injection (direct) | ✅ | ✅ | ✅ |
| Jailbreak (role-play, DAN, etc.) | ✅ | ✅ | ✅ |
| Encoding attacks (base64, ROT13, leetspeak) | ✅ | ✅ | ✅ |
| PII / data leakage | ✅ | ✅ | ✅ |
| Toxicity / harmful content | ✅ | ✅ | ✅ |
| Multi-turn / adaptive | partial | ✅ | ✅ |
| Hallucination / misinformation | partial | ✅ (Giskard) | ✅ |
| Indirect injection (RAG) | probes | ✅ (RAGET) | ✅ |
| Custom / novel attack chains | ❌ | limited | ✅ (PyRIT) |
| Adaptive attacker-LLM loops | ❌ | ❌ | ✅ (PyRIT) |

---

## 8. Attack Seed Datasets

Standard harmful-behavior corpora to feed custom probes. Pulled via HuggingFace
`datasets` (`pip install datasets`), stored in `shared/seeds/`.

- **JailbreakBench** — jailbreak prompt benchmark.
- **AdvBench** — adversarial harmful-behavior strings.
- **HarmBench** — standardized harmful-behavior evaluation set.

---

## 9. RAG Upgrade Path (no re-architecture)

When the target becomes a RAG system:

1. Add `shared/config/targets/rag_endpoint.yaml` pointing at the RAG endpoint.
2. **Setup 1:** enable promptfoo/garak indirect-injection probes.
3. **Setup 2:** enable Giskard **RAGET** (retrieval faithfulness, wrong-context
   answers, retrieval quality) — Setup 2 is RAG-capable on its own.
4. **Setup 3:** author deep indirect-injection orchestrators in PyRIT if needed.

Attack, scoring, and report layers are untouched. You add configuration, not architecture.

---

## 10. Installation

```bash
# Python side (all setups) — install deps + the shared package (editable)
pip install garak deepteam giskard deepeval datasets pyyaml
pip install -e .              # installs redteam_core so setups can import it

# Node side (Setup 1 only — promptfoo)
npm install -g promptfoo      # or: npx promptfoo@latest
```

`requirements.txt`
```
garak
deepteam
giskard
deepeval
datasets
pyyaml
```

`package.json` → dependency: `promptfoo`

---

## 11. Deliberately Excluded (with rationale)

| Tool / approach | Why excluded |
|---|---|
| **BlackICE** (Databricks container) | Requires Docker; heavy multi-GB image. Great as a sandbox / shopping list, but not adopted. See §12. |
| **llm-attacks / GCG** | Gradient-based; requires model **weights**. We are black-box. |
| **TextAttack** | Aimed at classifiers / NLP perturbation, not chat-endpoint red-teaming. |
| **LLM Guard / NeMo Guardrails / Rebuff** | Defensive guardrails. Add only if/when we want to test guardrail *bypass* — deferred. |

---

## 12. Note on BlackICE (considered, not adopted)

**BlackICE** is an open-source **containerized** red-teaming toolkit from
Databricks (CAMLIS 2025) — "Kali Linux for AI security." One Docker image bundles
14 tools (incl. Promptfoo, Garak, Giskard, PyRIT, FuzzyAI, Fickling) behind a
unified CLI, split into *static* (CLI) and *dynamic* (Python) tools.

- **Why relevant:** Its tool selection validates ours — the spine (Promptfoo,
  Garak, Giskard, PyRIT) matches. Useful as a **reference/shopping list** and a
  zero-setup **exploration sandbox**.
- **Why not adopted:** It requires **Docker** and is a heavy environment you work
  *inside*, not a lean, modular workbench. Excluded per our no-Docker constraint.
- **Worth revisiting later:** Two tools it bundles fill gaps we currently don't
  cover — **FuzzyAI** (dynamic fuzzing) and **Fickling** (scanning model/pickle
  files for malicious code — a supply-chain angle).

**References:**
- Paper: https://arxiv.org/abs/2510.11823
- Databricks blog: https://www.databricks.com/blog/announcing-blackice-containerized-red-teaming-toolkit-ai-security-testing

---

## 13. Summary

- **Model:** black-box workbench, point-at-app, chat now → RAG later.
- **Three tiers:** Easy (Promptfoo + Garak, YAML) → Python (DeepTeam + Giskard +
  DeepEval) → Sophisticated (PyRIT + DeepEval).
- **Shared layer:** one target seam + seed corpora, reused everywhere.
- **RAG-ready:** Giskard RAGET in Setup 2; no re-architecture needed.
- **Escalation ladder:** run Setup 1 on everything; escalate only when a target demands it.
```
