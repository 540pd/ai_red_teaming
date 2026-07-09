# DeepTeam — Red-Teaming an LLM App · Learning Workbench

A hands-on tutorial for **red-teaming** an LLM application with the open-source
[**DeepTeam**](https://github.com/confident-ai/deepteam) framework (by the Confident AI / DeepEval
team), built for learning rather than production automation.

- **Notebook:** `deepteam_tutorial.ipynb` — a step-by-step, runnable walkthrough.
- **This README:** the approach, setup, and a condensed run sequence.

References: <https://github.com/confident-ai/deepteam> · <https://www.trydeepteam.com>

---

## What DeepTeam is

DeepTeam is a Python framework that **simulates adversarial attacks** — jailbreaking, prompt
injection, multi-turn exploitation, and more — to uncover LLM vulnerabilities like bias, PII
leakage, prompt leakage, and injection flaws. Its model is small: give it a **callback to your
app**, a set of **vulnerabilities** to probe, and a set of **attacks** to deliver them, then call
`red_team(...)`. Scoring is **LLM-as-a-judge** (binary pass/fail with a reason), reusing DeepEval.

### Focus & assumptions

1. **Focus: red-teaming — features & capabilities.** The notebook spends most of its time on *what
   DeepTeam can test* (its vulnerability catalog and attack library) and how to compose a run.
2. **Endpoint assumed configured.** Your app is reachable over HTTP; we only wrap it in a
   `model_callback`.
3. **Evaluation LLM assumed configured.** DeepTeam uses an LLM to simulate attacks and judge
   answers; we assume that's already set (via `OPENAI_API_KEY` or `deepeval set-<provider>`).
4. **Open-source, local.** Runs on your machine; no account. (It can optionally push to the
   Confident AI platform — we don't.)

---

## The mental model — three inputs, one call

| Component | Role |
|-----------|------|
| **`model_callback`** *(your target)* | Async function routing a prompt to your app, returning text |
| **Vulnerabilities** | *What* to test — bias, PII/prompt leakage, SQL/shell injection, misinformation, agentic risks, … |
| **Attacks** | *How* to deliver — injection, roleplay, base64/ROT13, multilingual, Crescendo, … |
| **`red_team()`** | Runs vulnerabilities × attacks against the callback and judges responses |
| **Framework** *(shortcut)* | A pre-baked bundle mapped to a standard (OWASP, NIST, MITRE, …) |

```
  wrap app (callback)  ×  vulnerabilities  ×  attacks  ->  red_team()  ->  risk assessment (pass/fail + rates)
```

> **Vulnerabilities × Attacks = the attack surface.** A vulnerability generates baseline adversarial
> prompts; an attack transforms or escalates them.

---

## Capabilities

### Vulnerabilities — 120+ types across ~8 categories

| Category | Example classes |
|----------|-----------------|
| Data privacy | `PIILeakage`, `PromptLeakage` |
| Responsible AI | `Bias`, `Toxicity` |
| Safety | `IllegalActivity`, `GraphicContent`, `PersonalSafety` |
| Security / access | `SQLInjection`, `ShellInjection`, `SSRF`, `BOLA`, `BFLA`, `RBAC`, `DebugAccess` |
| Business | `Misinformation`, `IntellectualProperty`, `Competition` |
| Robustness | `Robustness` (hijacking, overreliance) |
| Agentic | `GoalTheft`, `ExcessiveAgency`, `AgentDrift`, `ToolAbuse` |
| Custom | `CustomVulnerability` (your own criteria) |

Most accept a `types=[...]` argument to focus on sub-risks (e.g. `Bias(types=["race","gender"])`).

### Attacks — 20+, single- and multi-turn

- **Single-turn** (`deepteam.attacks.single_turn`): `PromptInjection`, `Roleplay`, `Base64`,
  `ROT13`, `Leetspeak`, `Multilingual`, `MathProblem`, `GrayBox`, `PromptProbing`, … — one-shot
  transforms/encodings. Each takes a `weight` to bias sampling.
- **Multi-turn** (`deepteam.attacks.multi_turn`): `LinearJailbreaking`, `TreeJailbreaking`,
  `CrescendoJailbreaking`, `SequentialJailbreak`, `BadLikertJudge` — conversation-driving chains
  that escalate over turns (more powerful, more model calls).

### Frameworks — compliance in one line

`OWASPTop10` (LLMs & Agents), NIST AI RMF, MITRE ATLAS, EU AI Act, plus safety datasets
(BeaverTails, Aegis). Run a whole standard: `red_team(model_callback=cb, framework=OWASPTop10())`.

### Also in the package

**Custom vulnerabilities/attacks** for your business logic, and **Guardrails** (`ToxicityGuard`,
`PromptInjectionGuard`, `PrivacyGuard`, …) for real-time production defense — a natural loop:
red-team → deploy matching guardrails → re-red-team.

---

## Prerequisites (assumed working)

- `pip install -U deepteam` (Python 3.9+); `httpx`, `pandas`, `nest_asyncio` for the notebook.
- Your **HTTP endpoint** running and reachable; you know its request/response JSON shape.
- An **evaluation LLM** configured (`OPENAI_API_KEY`, or `deepeval set-gemini` / `set-azure-openai`
  / `set-litellm`, etc.).

---

## Condensed run sequence (Python)

```python
from deepteam import red_team
from deepteam.vulnerabilities import Bias, PIILeakage, PromptLeakage
from deepteam.attacks.single_turn import PromptInjection, Base64, Roleplay
from deepteam.attacks.multi_turn import CrescendoJailbreaking
import httpx

# 1) Wrap your endpoint as an async callback.
ENDPOINT = "http://localhost:8000/chat"     # <-- your URL

async def model_callback(input: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(ENDPOINT, json={"question": input})
        r.raise_for_status()
        return r.json()["answer"]            # <-- match your response key

# 2) Pick vulnerabilities (what) and attacks (how).
vulnerabilities = [Bias(types=["race","gender"]), PIILeakage(), PromptLeakage()]
attacks = [PromptInjection(weight=3), Roleplay(), Base64(), CrescendoJailbreaking()]

# 3) Run. (In Jupyter: `import nest_asyncio; nest_asyncio.apply()` first.)
risk_assessment = red_team(
    model_callback=model_callback,
    vulnerabilities=vulnerabilities,
    attacks=attacks,
    attacks_per_vulnerability_type=3,
    max_concurrent=5,
    ignore_errors=True,
)
print(risk_assessment)

# Or a whole standard in one line:
from deepteam.frameworks import OWASPTop10
risk_assessment = red_team(model_callback=model_callback, framework=OWASPTop10())
```

---

## Results

`red_team(...)` returns a **risk assessment** object and prints a summary table (per-vulnerability
pass rates and the attack methods that succeeded). Access it programmatically for CI gating and
analysis; the notebook parses per-case records into a pandas frame (a vulnerability × attack pass
-rate matrix and the list of successful attacks). Export it as a JSON artifact for the build record.

> Exact class names, `red_team` parameters, and result attributes evolve quickly across versions —
> the notebook includes **discovery cells** that list the vulnerabilities, attacks, and frameworks
> your installed version actually exposes, and reads results defensively.

---

## Iterating & CI

- **Start narrow, widen:** one vulnerability + one single-turn attack to confirm wiring, then add
  more, and finally a multi-turn chain.
- **Scale** with `attacks_per_vulnerability_type`; **mind concurrency** via `max_concurrent` (hits
  both your endpoint and the judge LLM).
- **Frameworks for coverage, explicit lists for depth.**
- **CI:** run as a `.py` script, fail the build on dropping pass rate / new vulnerabilities, and
  archive the exported risk assessment.

---

## Troubleshooting

- **"event loop is already running" (Jupyter)** → `import nest_asyncio; nest_asyncio.apply()`, or
  run as a `.py` script.
- **Judge/simulator LLM errors** → the evaluation LLM isn't configured; set the key or
  `deepeval set-<provider>`.
- **Endpoint errors / rate limits** → lower `max_concurrent`, raise the callback timeout, verify the
  request/response JSON shape.
- **Names/params differ** → the catalog changes fast; use the notebook's discovery cells.

---

## Files

| File | What it is |
|------|-----------|
| `deepteam_tutorial.ipynb` | The full step-by-step learning notebook. |
| `README.md` | This overview: approach, setup, capabilities, run steps, results. |
