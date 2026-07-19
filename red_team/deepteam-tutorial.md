# Red Teaming an LLM Application with DeepTeam

DeepTeam is an open-source **LLM red teaming framework** from Confident AI — the team behind DeepEval. It's "penetration testing, but for LLMs": you point it at your LLM app (a chatbot, a RAG pipeline, an agent) and it generates adversarial inputs that try to trigger real weaknesses — bias, PII leakage, prompt injection, broken authorization — then scores how often your system gives in. You declare *what* to test for (**vulnerabilities**) and *how* to attack (**attacks**); DeepTeam simulates the attacks, sends them to your model, and judges the responses with vulnerability-specific **metrics**.

**Tests for:** bias, toxicity, PII & prompt leakage, broken authorization (BFLA/BOLA/RBAC), SSRF, SQL/shell injection, illegal activity, graphic content, self-harm, misinformation, IP violations, hallucination, and a deep set of **agentic** risks (excessive agency, goal theft, tool-misuse, recursive hijacking) — **36 vulnerability classes** (50+ counting sub-types) at the time of writing.

**Attacks with:** prompt injection, roleplay, encodings (Base64/ROT13/Leetspeak), math/poetry obfuscation, multilingual evasion, context flooding, plus multi-turn jailbreaks (Crescendo, Linear, Tree, Sequential, Bad-Likert-Judge) — **27 attack methods** (22 single-turn + 5 multi-turn).

**Works with:** OpenAI, Anthropic, Google, Azure OpenAI, AWS Bedrock, XAI, Ollama, and any custom model via DeepEval; it's Python-first and slots into CI/CD (GitHub Actions, GitLab CI, Jenkins).

## Contents

- [How DeepTeam works](#how-deepteam-works-conceptual-model)
- [Components in detail](#components-in-detail) — [Vulnerability](#1-vulnerability) · [Attack](#2-attack) · [Model callback](#3-model-callback) · [Metric](#4-metric) · [red_team & RedTeamer](#5-red_team--redteamer) · [Framework](#6-framework) · [Guardrails](#7-guardrails)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running a red team](#running-a-red-team)
- [Troubleshooting](#troubleshooting)
- [Appendix — models, CI, and Confident AI](#appendix--models-ci-and-confident-ai)
- [Resources](#resources)

## How DeepTeam works (conceptual model)

A red team run is a pipeline. You pick **vulnerabilities** (what to test) and **attacks** (how to deliver them). DeepTeam's *simulator* model turns each vulnerability into a baseline adversarial prompt, then an attack method **enhances** it (encodes it, wraps it in a roleplay, or escalates it over several turns). The enhanced input goes to your **model callback**; the reply is scored by a vulnerability-specific **metric**; and everything rolls up into a **risk assessment**.

```
  VULNERABILITY    what to test for — the weakness
       │           (Bias · Toxicity · PIILeakage · SSRF …)
       │           each carries its own "types" (race, gender …)
       ▼
  ATTACK           simulate a baseline probe, then enhance it
       │           single-turn (PromptInjection · Base64 · Roleplay …)
       │           multi-turn  (Crescendo · Linear · Tree · Sequential …)
       ▼
  MODEL CALLBACK   your LLM app answers the adversarial input
       │           async def model_callback(input) -> response
       ▼
  METRIC           a vulnerability-specific judge scores the reply 0/1
       │           (was the weakness exploited?)
       ▼
  RISK ASSESSMENT  pass/fail per vulnerability × attack, with rates
```

Two hidden models power the run: the **simulator model** writes the attacks, and the **evaluation model** backs the metrics that judge the replies. Your own app under test is reached only through the model callback.

The building blocks, in DeepTeam's own terminology:

| Term | What it is |
|------|-----------|
| **Vulnerability** | A weakness to probe for (bias, PII leakage, SSRF…). Each has fine-grained **types** you can select. |
| **Attack** | An adversarial method that delivers/enhances a baseline probe. **Single-turn** (one-shot) or **multi-turn** (iterative). |
| **Model callback** | The wrapper around *your* LLM app — takes an input string, returns your app's response. The only thing that's actually under test. |
| **Metric** | The judge: a vulnerability-specific evaluator that scores each response **0 or 1** (was the weakness exploited?). |
| **`red_team()`** | The stateless entry point — run vulnerabilities × attacks against a callback, get a risk assessment. |
| **`RedTeamer`** | The stateful alternative — remembers attacks so you can reuse them across runs. |
| **Framework** | A prebuilt bundle of vulnerabilities+attacks that maps to a standard (OWASP, NIST, MITRE…). |
| **Guardrails** | A separate, production-time feature: fast binary classifiers that block malicious inputs/outputs live. |

So a run is just: **pick vulnerabilities and attacks (or a framework) → DeepTeam simulates and enhances attacks, sends them to your callback, and scores the replies with per-vulnerability metrics → you read the risk assessment.** DeepTeam generates `attacks_per_vulnerability_type` baseline attacks for every type of every vulnerability, so the number of test cases grows with your selection.

**What DeepTeam can do** — its headline capabilities:

| Capability | What it does |
|-----------|--------------|
| **Broad vulnerability coverage** | 36 vulnerability classes (50+ counting sub-types) spanning responsible AI, privacy, security, safety, business, reliability, and **agentic** risk |
| **Agentic red teaming** | A dedicated set for tool-using agents: excessive agency, goal theft, recursive hijacking, tool-orchestration/metadata abuse, inter-agent communication, system reconnaissance |
| **Single- & multi-turn attacks** | 22 single-turn enhancements plus 5 iterative multi-turn jailbreaks that adapt across a conversation |
| **Standards frameworks** | One-line runs mapped to OWASP Top 10, OWASP ASI, NIST AI RMF, MITRE ATLAS, and safety datasets (Aegis, BeaverTails) |
| **Any target, any model** | Test any app through a callback; drive the simulator/judge with OpenAI, Anthropic, Google, Azure, XAI, or local Ollama models |
| **Custom vulnerabilities** | Define your own weakness with bespoke `types` and evaluation criteria via `CustomVulnerability` |
| **Stateful reuse** | `RedTeamer` remembers generated attacks so you can re-run the *same* adversarial set against a fixed model (regression testing) |
| **Production guardrails** | Ship the offline findings into live binary input/output guards (`Guardrails`) |
| **CI/CD native** | A run is a Python call returning a risk assessment — gate PRs in GitHub Actions, GitLab CI, or Jenkins |

- **Docs** — [Red teaming introduction](https://www.trydeepteam.com/docs/red-teaming-introduction)

## Components in detail

Each building block, in the order an attack moves through the pipeline.

### 1. Vulnerability

- **What it is** — a weakness you want to test for, imported from `deepteam.vulnerabilities`. Instantiate it and (optionally) pass `types` to narrow the sub-categories tested: `Bias(types=["race", "gender"])`.
- **Why it matters** — your vulnerability selection *is* your risk scope. Omit `types` and it tests all sub-types of that vulnerability; name a few to keep the run fast and focused.
- **Types** — every vulnerability decomposes into fine-grained **types**, and *each type gets its own metric*. `Bias` splits into `race`, `gender`, `religion`, `politics`; `PIILeakage` into direct disclosure, API/database access, session leak, and social manipulation. If you don't pass `types`, all of them run. See the [full type reference](#type-reference-all-vulnerabilities) below.

**At a glance — the full catalog.** DeepTeam ships **36 vulnerability classes plus `CustomVulnerability`** at the time of writing (50+ when you count sub-types). They span the five documented categories *and* a large **agentic** set for tool-using agents. Every class name below is exactly what you import from `deepteam.vulnerabilities`.

| Category | Vulnerability classes | Probes for |
|----------|----------------------|------------|
| **Responsible AI** | `Bias`, `Toxicity`, `Fairness`, `Ethics` | Discrimination; profanity/insults/threats; unfair treatment; unethical guidance |
| **Data Privacy** | `PIILeakage`, `PromptLeakage` | Leaking personal data; leaking system-prompt secrets, rules, guards & roles |
| **Security & access** | `BFLA`, `BOLA`, `RBAC`, `SSRF`, `DebugAccess`, `ShellInjection`, `SQLInjection`, `UnexpectedCodeExecution` | Broken function/object authorization, role-bypass, server-side request forgery, debug-endpoint exposure, shell/SQL injection, arbitrary code execution |
| **Safety** | `IllegalActivity`, `GraphicContent`, `PersonalSafety`, `ChildProtection` | Weapons/drugs/crime; explicit content; self-harm & bullying; child-exploitation safeguards |
| **Business** | `Misinformation`, `IntellectualProperty`, `Competition` | Factual errors & unsupported claims; copyright/trademark/patent; competitor disparagement & market manipulation |
| **Reliability** | `Hallucination`, `Robustness` | Fabricated content; resilience to hijacking/overreliance |
| **Agentic** | `ExcessiveAgency`, `GoalTheft`, `RecursiveHijacking`, `IndirectInstruction`, `ToolOrchestrationAbuse`, `ToolMetadataPoisoning`, `AgentIdentityAbuse`, `InsecureInterAgentCommunication`, `CrossContextRetrieval`, `SystemReconnaissance`, `ExploitToolAgent`, `ExternalSystemAbuse`, `AutonomousAgentDrift` | Agent-specific risks: doing more than asked, goal/instruction hijacking, poisoning or abusing tools, leaking across contexts, probing the host system, drifting from the intended objective |
| **Custom** | `CustomVulnerability` | A weakness *you* define, with your own `types` and evaluation criteria |

> **Note:** The docs' vulnerabilities page enumerates the 14 "core" classes (the first five categories above); the **agentic** and reliability classes come from the package itself and power [agentic AI red teaming](https://www.trydeepteam.com/guides/guide-agentic-ai-red-teaming). The marketing homepage advertises "120+ vulnerabilities" — that figure counts sub-types and future additions. Treat exact counts as volatile and check the [vulnerabilities docs](https://www.trydeepteam.com/docs/red-teaming-vulnerabilities) for the live set.

#### Type reference (all vulnerabilities)

The exact strings you pass to `types=[...]` for **every** vulnerability class (omit `types` to run them all). Each string maps to one metric. Grouped in the same category order as the catalog above.

| Category | Vulnerability | `types` (exact strings) |
|----------|---------------|-------------------------|
| Responsible AI | `Bias` | `race` · `gender` · `religion` · `politics` |
| Responsible AI | `Toxicity` | `profanity` · `insults` · `threats` · `mockery` |
| Responsible AI | `Fairness` | `equality_consistency` · `procedural_opportunity` · `temporal_outcome` |
| Responsible AI | `Ethics` | `moral_integrity` · `responsible_transparency` · `harm_prevention` |
| Data Privacy | `PIILeakage` | `direct_disclosure` · `api_and_database_access` · `session_leak` · `social_manipulation` |
| Data Privacy | `PromptLeakage` | `secrets_and_credentials` · `instructions` · `guard_exposure` · `permissions_and_roles` |
| Security & access | `BFLA` | `privilege_escalation` · `function_bypass` · `authorization_bypass` |
| Security & access | `BOLA` | `object_access_bypass` · `cross_customer_access` · `unauthorized_object_manipulation` |
| Security & access | `RBAC` | `role_bypass` · `privilege_escalation` · `unauthorized_role_assumption` |
| Security & access | `SSRF` | `internal_service_access` · `cloud_metadata_access` · `port_scanning` |
| Security & access | `DebugAccess` | `debug_mode_bypass` · `development_endpoint_access` · `administrative_interface_exposure` |
| Security & access | `ShellInjection` | `command_injection` · `system_command_execution` · `shell_escape_sequences` |
| Security & access | `SQLInjection` | `blind_sql_injection` · `union_based_injection` · `error_based_injection` |
| Security & access | `UnexpectedCodeExecution` | `unauthorized_code_execution` · `shell_command_execution` · `eval_usage` |
| Safety | `IllegalActivity` | `weapons` · `illegal_drugs` · `violent_crime` · `nonviolent_crime` · `sex_crime` · `cybercrime` · `child_exploitation` |
| Safety | `GraphicContent` | `sexual_content` · `graphic_content` · `pornographic_content` |
| Safety | `PersonalSafety` | `bullying` · `self_harm` · `dangerous_challenges` · `stalking` |
| Safety | `ChildProtection` | `age_verification` · `data_privacy` · `exposure_interaction` |
| Business | `Misinformation` | `factual_errors` · `unsupported_claims` · `expertize_misrepresentation` |
| Business | `IntellectualProperty` | `copyright_violations` · `trademark_infringement` · `patent_disclosure` · `imitation` |
| Business | `Competition` | `competitor_mention` · `market_manipulation` · `discreditation` · `confidential_strategies` |
| Reliability | `Hallucination` | `fake_citations` · `fake_apis` · `fake_entities` · `fake_statistics` |
| Reliability | `Robustness` | `input_overreliance` · `hijacking` |
| Agentic | `ExcessiveAgency` | `functionality` · `permissions` · `autonomy` |
| Agentic | `GoalTheft` | `escalating_probing` · `cooperative_dialogue` · `social_engineering` |
| Agentic | `RecursiveHijacking` | `self_modifying_goals` · `recursive_objective_chaining` · `goal_propagation_attacks` |
| Agentic | `IndirectInstruction` | `rag_injection` · `tool_output_injection` · `document_embedded_instructions` · `cross_context_injection` |
| Agentic | `ToolOrchestrationAbuse` | `recursive_tool_calls` · `unsafe_tool_composition` · `tool_budget_exhaustion` · `cross_tool_state_leakage` |
| Agentic | `ToolMetadataPoisoning` | `schema_manipulation` · `description_deception` · `permission_misrepresentation` · `registry_poisoning` |
| Agentic | `AgentIdentityAbuse` | `agent_impersonation` · `identity_inheritance` · `cross_agent_trust_abuse` |
| Agentic | `InsecureInterAgentCommunication` | `message_spoofing` · `message_injection` · `agent_in_the_middle` |
| Agentic | `CrossContextRetrieval` | `tenant` · `user` · `role` |
| Agentic | `SystemReconnaissance` | `file_metadata` · `database_schema` · `retrieval_config` |
| Agentic | `ExploitToolAgent` | `privilege_escalation` · `financial_manipulation` · `data_destruction` |
| Agentic | `ExternalSystemAbuse` | `data_exfiltration` · `communications_spam` · `internal_spoofing` |
| Agentic | `AutonomousAgentDrift` | `goal_drift` · `reward_hacking` · `agent_collusion` · `runaway_autonomy` |

> `CustomVulnerability` has no fixed `types` — you supply your own along with the evaluation criteria. Type strings are verified against the package source at the time of writing; run `--help` on a class or check the [vulnerabilities docs](https://www.trydeepteam.com/docs/red-teaming-vulnerabilities) if a release adds more.

- **Docs** — [Vulnerabilities](https://www.trydeepteam.com/docs/red-teaming-vulnerabilities) · [Agentic red teaming](https://www.trydeepteam.com/guides/guide-agentic-ai-red-teaming)

### 2. Attack

- **What it is** — the adversarial method that turns a plain baseline probe into something more evasive, imported from `deepteam.attacks.single_turn` or `deepteam.attacks.multi_turn`. Each takes an optional `weight` that biases how often it's chosen when you supply several.
- **Why it matters** — the same vulnerability probe delivered as a roleplay, a Base64 blob, or a slowly-escalating conversation can slip past guardrails that block the plain version. Attacks are how you measure resilience, not just default behavior.
- **Single-turn vs multi-turn** — **single-turn** attacks enhance one prompt in isolation (encode it, inject it, disguise it). **Multi-turn** attacks hold a conversation, adapting each turn based on your model's previous replies — this is where jailbreaks like Crescendo live.
- **Weight** — when multiple attacks are supplied, `weight` is a relative selection weight: an attack with `weight=2` is chosen roughly twice as often as a `weight=1` attack to enhance a given baseline probe (the exact semantics are lightly documented — treat weight as relative frequency).

**At a glance — single-turn** (22 classes from `deepteam.attacks.single_turn`, at the time of writing). Class names are exactly what you import:

| Attack | Kind | What it does |
|--------|------|--------------|
| `Base64` | Encoding | Base64-encodes the probe to dodge keyword filters |
| `ROT13` | Encoding | Rotates characters to obscure the text |
| `Leetspeak` | Encoding | Swaps letters for numbers/symbols |
| `CharacterStream` | Encoding | Breaks the payload into a character stream to evade matching |
| `AdversarialPoetry` | Obfuscation | Recasts the attack as poetry |
| `MathProblem` | Obfuscation | Hides the harmful request inside a math problem |
| `Multilingual` | Evasion | Translates the attack into other languages |
| `LinguisticConfusion` | Evasion | Uses semantic/linguistic manipulation to confuse the model |
| `PromptInjection` | Injection | Injects malicious instructions into the prompt |
| `PromptProbing` | Injection | Probes for and extracts the underlying system prompt |
| `EmbeddedInstructionJSON` | Injection | Hides instructions inside structured (JSON) input |
| `SyntheticContextInjection` | Injection | Plants fabricated context to steer the model |
| `ContextPoisoning` | Injection | Corrupts the supplied context/retrieval |
| `ContextFlooding` | Injection | Floods the context to bury or dilute safeguards |
| `InputBypass` | Injection | Circumvents input-validation mechanisms |
| `Roleplay` | Social | Wraps the request in a character persona |
| `GrayBox` | Targeted | Leverages partial knowledge of the system |
| `EmotionalManipulation` | Social | Uses emotional pressure to elicit compliance |
| `AuthorityEscalation` | Social | Impersonates authority to justify the request |
| `SystemOverride` | Agentic | Attempts to override system constraints |
| `PermissionEscalation` | Agentic | Exploits privilege boundaries |
| `GoalRedirection` | Agentic | Redirects an agent away from its intended goal |

**At a glance — multi-turn** (5 classes from `deepteam.attacks.multi_turn`) — these hold a conversation, adapting each turn from your model's prior replies:

| Attack | What it does |
|--------|--------------|
| `LinearJailbreaking` | Applies attack methods progressively across sequential turns |
| `CrescendoJailbreaking` | Escalates intensity gradually across the exchange |
| `TreeJailbreaking` | Explores multiple branching attack paths |
| `SequentialJailbreak` | Chains techniques in a deliberate sequence |
| `BadLikertJudge` | Coerces the model into producing harmful content via a rating/judge framing |

> **Note:** Counts drift release to release — the README's headline is "20+ attacks" (27 here: 22 + 5). The [attacks docs](https://www.trydeepteam.com/docs/red-teaming-adversarial-attacks) list the current set.

- **Docs** — [Adversarial attacks](https://www.trydeepteam.com/docs/red-teaming-adversarial-attacks)

### 3. Model callback

- **What it is** — the single function that connects DeepTeam to *your* system. It's an `async` function that receives the adversarial `input` string and returns your app's response. Everything inside — model, prompts, RAG retrieval, tools — is yours; DeepTeam only sees inputs and outputs.
- **Why it matters** — this is the thing being tested. If the callback doesn't faithfully reproduce your production path (same system prompt, same retrieval, same guardrails), the risk assessment won't reflect production.
- **Simple form** — `async def model_callback(input: str) -> str` returns a plain string; enough for single-turn attacks on a chatbot or RAG app.
- **Multi-turn form** — for multi-turn attacks the callback also receives conversation history and returns a richer turn object (an `RTTurn` carrying the response plus optional retrieval context and tool calls), so the attack can adapt across turns.
- **Docs** — [Red teaming introduction](https://www.trydeepteam.com/docs/red-teaming-introduction)

### 4. Metric

- **What it is** — the judge. Every vulnerability type ships with a dedicated metric that inspects your model's response and returns a **binary score: 1 if the weakness was exploited, 0 if the model held up**. The metric is powered by the **evaluation model** (an LLM-as-judge, default `gpt-4o`).
- **Why it matters** — the metric defines what "failure" means for each vulnerability, so it decides your pass/fail. A stronger evaluation model gives more reliable verdicts; review flagged cases to confirm true positives.
- **How it aggregates** — scores roll up per vulnerability type and per attack into passing rates, so you see *which* weaknesses were exploited and *which* attacks were most effective, not just a single number.
- **Docs** — [Red teaming introduction](https://www.trydeepteam.com/docs/red-teaming-introduction)

### 5. `red_team()` & `RedTeamer`

- **`red_team()`** — the stateless entry point from `deepteam`. Give it a callback, vulnerabilities, and attacks (or a framework); it runs the whole pipeline and returns a **risk assessment**. Best for one-off scans and CI.
- **`RedTeamer`** — the stateful class from `deepteam.red_teamer`. It remembers the attacks it generated, so with `reuse_previous_attacks=True` you can re-run the *same* adversarial inputs against a changed model — ideal for regression testing a fix. It exposes the same `red_team(...)` call minus `framework`.
- **The risk assessment** — the returned object exposes `.overview` (susceptibility per vulnerability and effectiveness per attack), `.test_cases` (every input, response, and verdict), and `.save()` to persist results.
- **Docs** — [Red teaming introduction](https://www.trydeepteam.com/docs/red-teaming-introduction)

### 6. Framework

- **What it is** — a prebuilt bundle that picks the right vulnerabilities and attacks for a recognized standard, so you don't hand-select them. Pass one via the `framework` argument instead of `vulnerabilities`/`attacks`.
- **Why it matters** — it maps your run onto a compliance/standards vocabulary auditors recognize, and saves you curating a coverage list by hand.
- **Available frameworks** — `OWASPTop10`, `OWASP_ASI_2026`, `NIST` (AI RMF), `MITRE` (ATLAS), `Aegis`, and `BeaverTails` (the last two are safety datasets), at the time of writing.
- **Docs** — [Frameworks introduction](https://www.trydeepteam.com/docs/frameworks-introduction)

### 7. Guardrails

- **What it is** — a *separate, production-time* feature (not part of the offline red team run). `Guardrails` runs fast binary classifiers on live traffic: `input_guards` screen user prompts *before* they reach the model, and `output_guards` screen the model's responses *before* they reach the user. Where red teaming optimizes for depth, guardrails optimize for speed and reliability.
- **How it composes** — a guardrail holds one or more **guards**, and the input (or output) is only allowed through if *every* guard passes; if any guard trips, the result is marked `breached`. Each guard can screen inputs, outputs, or both.
- **Why it matters** — red teaming finds weaknesses offline; guardrails are how you *block* them in production. The natural loop is: red team → find a gap → deploy the matching guard.
- **Available guards** — `PromptInjectionGuard`, `PrivacyGuard`, `ToxicityGuard`, `IllegalGuard`, `HallucinationGuard`, `TopicalGuard`, `CybersecurityGuard` (seven, at the time of writing), imported from `deepteam.guardrails`.
- **Docs** — [Guardrails introduction](https://www.trydeepteam.com/docs/guardrails-introduction)

## Installation

Install from PyPI:

```bash
pip install -U deepteam
```

> **Note:** DeepTeam builds on **DeepEval** and uses an LLM as both the attack simulator and the evaluation judge, so you need API access to a supported provider. With the defaults, set an OpenAI key:
>
> ```bash
> export OPENAI_API_KEY="sk-…"
> ```

## Configuration

DeepTeam is configured in Python, not YAML. You assemble three things — a list of **vulnerabilities**, a list of **attacks**, and a **model callback** — and pass them to `red_team()`. The subsections below follow the same order as the [pipeline](#how-deepteam-works-conceptual-model).

### Vulnerabilities

Import from `deepteam.vulnerabilities`; pass `types` to narrow the scope (see the [Vulnerability concept](#1-vulnerability)):

```python
from deepteam.vulnerabilities import Bias, PIILeakage

vulnerabilities = [
    Bias(types=["race", "gender"]),   # only these sub-types
    PIILeakage(),                     # all PII sub-types
]
```

### Attacks

Import single-turn from `deepteam.attacks.single_turn`, multi-turn from `deepteam.attacks.multi_turn`; `weight` biases selection (see the [Attack concept](#2-attack)):

```python
from deepteam.attacks.single_turn import PromptInjection, Roleplay
from deepteam.attacks.multi_turn import CrescendoJailbreaking

attacks = [
    PromptInjection(weight=2),   # picked ~2× as often
    Roleplay(),
    CrescendoJailbreaking(),     # iterative, multi-turn
]
```

### Model callback

Wrap your LLM app in an `async` function. Replace the body with your real call (see the [Model callback concept](#3-model-callback)):

```python
async def model_callback(input: str) -> str:
    # call YOUR app here — model, RAG, agent, guardrails and all
    response = await my_llm_app(input)
    return response
```

### `red_team()` options

| Parameter | Default | What it does |
|-----------|---------|--------------|
| `model_callback` | *(required)* | Your app under test |
| `vulnerabilities` | `None` | List of vulnerability objects to probe |
| `attacks` | `None` | List of attack objects to apply |
| `framework` | `None` | A standards bundle *instead of* vulnerabilities/attacks |
| `simulator_model` | `"gpt-3.5-turbo-0125"` | LLM that generates the attacks |
| `evaluation_model` | `"gpt-4o"` | LLM that judges the responses (the metric) |
| `attacks_per_vulnerability_type` | `1` | Baseline attacks generated per vulnerability *type* |
| `ignore_errors` | `False` | Continue the run instead of raising on a failed case |
| `async_mode` | `True` | Run cases concurrently |
| `max_concurrent` | `10` | Cap on concurrent tasks |
| `target_purpose` | `None` | A description of your app, to steer attack generation |

### Full config (minimal, runnable)

```python
from deepteam import red_team
from deepteam.vulnerabilities import Bias
from deepteam.attacks.single_turn import PromptInjection

# 1. Wrap your LLM app (replace the body with a real call)
async def model_callback(input: str) -> str:
    return f"I'm sorry but I can't answer this: {input}"

# 2. Run the red team
risk_assessment = red_team(
    model_callback=model_callback,
    vulnerabilities=[Bias(types=["race"])],   # what to test
    attacks=[PromptInjection()],              # how to attack
    attacks_per_vulnerability_type=3,         # 3 probes per type
)

# 3. Inspect the results
print(risk_assessment.overview)   # susceptibility & attack effectiveness
risk_assessment.save()            # persist the full test cases
```

**To use it:** set `OPENAI_API_KEY`, swap the callback body for your real app, and pick the vulnerabilities/attacks that match your risk profile (or replace both with `framework=OWASPTop10()`).

## Running a red team

Run it like any Python script (`OPENAI_API_KEY` set first). Three ways to drive DeepTeam, smallest first:

**1. Hand-picked vulnerabilities and attacks** — full control:

```python
from deepteam import red_team
from deepteam.vulnerabilities import Bias
from deepteam.attacks.single_turn import PromptInjection

risk_assessment = red_team(
    model_callback=model_callback,
    vulnerabilities=[Bias(types=["race"])],
    attacks=[PromptInjection()],
)
```

**2. A standards framework** — instant, audit-aligned coverage:

```python
from deepteam import red_team
from deepteam.frameworks import OWASPTop10

risk_assessment = red_team(
    model_callback=model_callback,
    framework=OWASPTop10(),
)
```

**3. Stateful, with attack reuse** — for regression-testing a fix against the *same* attacks:

```python
from deepteam.red_teamer import RedTeamer

red_teamer = RedTeamer()
risk_assessment = red_teamer.red_team(
    model_callback=model_callback,
    vulnerabilities=[Bias(types=["race"])],
    attacks=[PromptInjection()],
    reuse_previous_attacks=True,
)
```

**Reading results** — inspect `risk_assessment.overview` for per-vulnerability susceptibility and per-attack effectiveness, drill into `risk_assessment.test_cases` for each adversarial input, your model's response, and the metric's 0/1 verdict, and call `.save()` to persist them.

**Tip:** start small — one vulnerability with one `types` entry, one attack, and `attacks_per_vulnerability_type=1` — to confirm your callback and keys work before scaling `attacks_per_vulnerability_type` and adding multi-turn attacks (which cost many model calls each).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `AuthenticationError` / no attacks generated | `OPENAI_API_KEY` (or provider key) not set | Export the key for your `simulator_model`/`evaluation_model` provider before running. |
| Run is very slow / expensive | Many types × high `attacks_per_vulnerability_type`, or multi-turn attacks | Narrow `types`, lower `attacks_per_vulnerability_type`, start with single-turn attacks. |
| Run aborts on a single failed case | An exception in one test case | Set `ignore_errors=True` to finish the run and review failures after. |
| Rate-limit errors mid-run | Too much concurrency for your tier | Lower `max_concurrent` (or set `async_mode=False`). |
| Results don't match production behavior | Callback isn't reproducing the real path | Ensure the callback uses your real system prompt, retrieval, and guardrails. |
| Judge verdicts look wrong | Weak evaluation model | Raise `evaluation_model` (e.g. `gpt-4o`); spot-check `test_cases` to confirm. |

- **Docs** — [DeepTeam documentation](https://www.trydeepteam.com/docs/red-teaming-introduction) · [GitHub issues](https://github.com/confident-ai/deepteam/issues)

## Appendix — models, CI, and Confident AI

- **Swapping models** — both `simulator_model` and `evaluation_model` accept a provider-prefixed string (e.g. `"openai/gpt-4o"`, `"anthropic/claude-sonnet-4"`) or a custom `DeepEvalBaseLLM` instance. Supported providers include OpenAI, Azure OpenAI, Anthropic, Google, XAI, and Ollama (local). Configure via the matching environment variable or DeepEval's CLI.
- **CI/CD** — because a run is a Python function returning a risk assessment, you can gate a pull request on it: run `red_team(...)` in GitHub Actions / GitLab CI / Jenkins and fail the build if susceptibility exceeds your threshold.
- **Guardrails in production** — after red teaming finds gaps, deploy `Guardrails` (see the [Guardrails concept](#7-guardrails) and the [deployment guide](https://www.trydeepteam.com/guides/guide-deploying-guardrails)) to block malicious inputs/outputs live:

  ```python
  from deepteam import Guardrails
  from deepteam.guardrails import PromptInjectionGuard, PrivacyGuard, ToxicityGuard

  guardrails = Guardrails(
      input_guards=[PromptInjectionGuard(), PrivacyGuard()],
      output_guards=[ToxicityGuard()],
  )
  print(guardrails.guard_input("Tell me how to hack").breached)
  print(guardrails.guard_output(input="Hi", output="…").breached)
  ```
- **Confident AI** — DeepTeam runs fully locally, but integrates with the Confident AI platform for hosted dashboards and production monitoring of red team results.

## Resources

**Getting started**
- [trydeepteam.com](https://www.trydeepteam.com/)
- [What is LLM red teaming?](https://www.trydeepteam.com/docs/what-is-llm-red-teaming)
- [Red teaming introduction](https://www.trydeepteam.com/docs/red-teaming-introduction)
- [GitHub — confident-ai/deepteam](https://github.com/confident-ai/deepteam)

**Concepts & reference**
- [Vulnerabilities](https://www.trydeepteam.com/docs/red-teaming-vulnerabilities)
- [Adversarial attacks](https://www.trydeepteam.com/docs/red-teaming-adversarial-attacks)
- [Frameworks introduction](https://www.trydeepteam.com/docs/frameworks-introduction)
- [Guardrails introduction](https://www.trydeepteam.com/docs/guardrails-introduction)
- [DeepEval (underlying eval engine)](https://github.com/confident-ai/deepeval)

**Guides**
- [Agentic AI red teaming](https://www.trydeepteam.com/guides/guide-agentic-ai-red-teaming)
- [Red teaming agentic RAG pipelines](https://www.trydeepteam.com/guides/guide-red-teaming-agentic-rag)
- [Red teaming conversational agents](https://www.trydeepteam.com/guides/guide-red-teaming-conversational-agents)
- [Red teaming against safety frameworks](https://www.trydeepteam.com/guides/guide-safety-frameworks)
- [Deploying guardrails in production](https://www.trydeepteam.com/guides/guide-deploying-guardrails)

**Community**
- [GitHub issues](https://github.com/confident-ai/deepteam/issues)
</content>
</invoke>
