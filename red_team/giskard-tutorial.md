# Red-Teaming an LLM with Giskard's LLM Scan

Giskard is an open-source Python library (Apache-2.0) for testing and evaluating LLM applications. This tutorial covers its **LLM Scan**: you wrap your model, call `giskard.scan()`, and it automatically red-teams the model for **vulnerabilities** — then reports what it found, grouped by category and severity.

**Scans for:** Hallucination and Misinformation · Harmful Content Generation · Prompt Injection · Robustness · Output Formatting · Information Disclosure · Stereotypes and Discrimination.

**Works with:** any LLM or RAG app you can call from Python (LangChain, LlamaIndex, OpenAI, local models, …) — you just provide a prediction function.

> **Note:** This covers the established **LLM Scan** API (`giskard.scan`), documented on `legacy-docs.giskard.ai`. Giskard is evolving a newer v3 in the `giskard-oss` repo; see [Resources](#resources).

## Contents

- [How the LLM Scan works](#how-the-llm-scan-works-conceptual-model)
- [Components in detail](#components-in-detail) — [Model](#1-model) · [Dataset](#2-dataset) · [Scan](#3-scan) · [Detector](#4-detector) · [Report](#5-report)
- [Installation & setup](#installation--setup)
- [Scanning an LLM](#scanning-an-llm)
- [Reading the report](#reading-the-report)
- [Troubleshooting](#troubleshooting)
- [Appendix — categories, test suites & v3](#appendix--categories-test-suites--v3)
- [Resources](#resources)

## How the LLM Scan works (conceptual model)

You wrap your LLM app as a **Model**, point **Scan** at it, and Giskard runs its **detectors** — some heuristic, some using a **judge LLM** — then returns a **report** of vulnerabilities. The diagram traces the flow:

```
  MODEL       wrap your LLM app: predict fn + description
     │        (the description drives which tests are generated)
     ▼
  DATASET     example inputs (optional — auto-generated if omitted)
     │
     ▼
  SCAN        giskard.scan(model, dataset) runs the detectors
     │
     ▼
  DETECTORS   probe each vulnerability category
     │        (heuristic checks + an LLM judge)
     ▼
  REPORT      vulnerabilities by category & severity → HTML / test suite
```

The building blocks, in Giskard's own terminology:

| Term | What it is |
|------|-----------|
| **Model** | Your LLM app wrapped as `giskard.Model` — a predict function plus metadata; the **`description`** drives which tests get generated. |
| **Dataset** | Optional example inputs wrapped as `giskard.Dataset`; Giskard auto-generates cases if you omit it. |
| **Scan** | `giskard.scan(model, dataset)` — runs the detectors and returns the report. |
| **Detector** | A vulnerability check. Two kinds: **traditional** (heuristics) and **LLM-assisted** (a judge LLM probes your model). |
| **Report** | The scan results — vulnerabilities by category and severity; view in a notebook or export with `to_html()`; can generate a test suite. |

So a run is just: **wrap your model → call `giskard.scan()` → read the report.** Because some detectors use a judge LLM, you also configure an LLM provider (see [setup](#installation--setup)).

- **Docs** — [LLM Scan](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html)

## Components in detail

Each building block, in the order the scan uses them.

### 1. Model

- **What it is** — your LLM app wrapped with `giskard.Model`: an inference entry point plus metadata (`model_type="text_generation"`, `name`, `description`, `feature_names`).
- **Why the description matters** — the scan reads `name` and `description` to **generate domain-specific probes**, so this metadata is your biggest lever on test quality. Treat the `description` as the model's spec — what it does, who it's for, and what it must never do. Vague descriptions yield generic attacks; specific ones yield relevant attacks.
- **What you can scan** — any text-generation system callable from Python (chatbots, Q&A, RAG pipelines, agents/chains, or a raw model endpoint). The **target** you scan is independent of the **judge** LLM the scan uses to generate probes — they can be different models.
- **Ways to wrap** — pick the integration that matches your app:

| Approach | Use it for |
|----------|-----------|
| **Prediction function** | Anything callable from Python (API models, custom pipelines): a `DataFrame` in, a list of strings out |
| **LangChain** | Wrap an `LLMChain` directly — no custom function needed |
| **Custom subclass** | Subclass `giskard.Model` and implement `model_predict` / `save_model` / `load_model` for RAG systems and multi-step agents |

- **Docs** — [Scan your model](https://legacy-docs.giskard.ai/en/stable/open_source/scan/index.html)

### 2. Dataset

- **What it is** — an optional set of example inputs wrapped with `giskard.Dataset` (a DataFrame plus `target=None` for generative models).
- **Why it matters** — it seeds the scan with realistic prompts. **If you omit it, Giskard auto-generates inputs** from the model's `description` — handy for a first pass, but a few real examples improve relevance.
- **What it enables** — seeding with real traffic makes probes realistic and results reproducible, and the same dataset can be reused across scans to compare model versions.
- **Docs** — [Datasets](https://legacy-docs.giskard.ai/en/stable/open_source/scan/index.html)

### 3. Scan

- **What it is** — `giskard.scan(model, dataset)` runs the detectors against your model and returns the results. It's built for **in-depth assessment of domain-specific apps** (chatbots, QA, RAG), not for benchmarking foundation models.
- **What a scan can do** — a single call spans several kinds of testing:

| Capability | What it does |
|-----------|--------------|
| **Automated red-teaming** | Runs all 7 vulnerability categories in one call — no manual attack writing |
| **Adaptive (LLM-assisted) probes** | A **judge LLM** generates domain-specific attacks from your model's `name`/`description`, then grades the responses — most detectors work this way |
| **Heuristic & library attacks** | **Traditional** detectors apply documented injection and robustness techniques — model-agnostic and cheap |
| **Requirement-based testing** | Checks the model against explicit safety requirements — harmful content, information disclosure, and bias |
| **Scoped runs** | `only=` limits the scan to one category (e.g. `only="hallucination"`) for fast, cheap iteration |
| **Findings → tests** | Converts detected vulnerabilities into a reproducible test suite for CI |

- **Judge LLM required** — because most detectors are LLM-assisted, a judge provider must be configured before scanning (see [setup](#installation--setup)).
- **Privacy** — LLM-assisted detectors send your dataset, the model's generated text, and its metadata to the configured LLM provider — unless you point the judge at a self-hosted model.
- **Docs** — [Scan API](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html)

### 4. Detector

- **What it is** — the checks the scan runs, one or more per vulnerability category. Each is either **traditional** (heuristics / curated libraries) or **LLM-assisted** (a judge LLM generates and grades context-aware adversarial inputs from your model's `name` + `description`).
- **The 7 categories and how their detectors work:**

| Category | Detector | Type | How it works |
|----------|----------|------|--------------|
| **Hallucination and Misinformation** | `LLMBasicSycophancyDetector` | LLM-assisted | Asks the same question in differently-biased forms and flags when the answers aren't coherent |
| | `LLMImplausibleOutputDetector` | LLM-assisted | Generates ad-hoc adversarial inputs to elicit implausible or controversial statements |
| **Harmful Content Generation** | `LLMHarmfulContentDetector` | LLM-assisted | Generates harmful requests, then checks the outputs against safety criteria |
| **Prompt Injection** | `LLMPromptInjectionDetector` | Traditional | Runs a large library of known prompt-injection techniques drawn from security research |
| **Robustness** | `LLMCharsInjectionDetector` | Traditional | Appends control characters (`\r`, `\b`, up to ~1000×) and checks the output isn't derailed |
| **Output Formatting** | `LLMOutputFormattingDetector` | LLM-assisted | Checks the output obeys the format stated in the model description |
| **Information Disclosure** | `LLMInformationDisclosureDetector` | LLM-assisted | Probes for PII / credential leakage and verifies nothing sensitive is revealed |
| **Stereotypes and Discrimination** | `LLMStereotypesDetector` | LLM-assisted | Probes for biased or discriminatory content and grades against fairness criteria |

- **Requirement-based detectors** — the harmful-content, information-disclosure, and stereotypes detectors share a `RequirementBasedDetector` design: they turn a safety requirement into targeted adversarial inputs and then verify the output meets it — which is why a sharp model `description` sharpens them.
- **Docs** — [LLM detectors reference](https://legacy-docs.giskard.ai/en/stable/reference/scan/llm_detectors.html)

### 5. Report

- **What it is** — the `scan_results` object returned by `giskard.scan()`: the **vulnerabilities** found, grouped by category and **severity (major / medium / minor)**, each with the exact prompts and outputs that triggered it so you can confirm true positives.
- **Viewing & exporting** — `display(scan_results)` renders an interactive widget inline in a notebook; `scan_results.to_html("scan_report.html")` writes a shareable standalone report.
- **From findings to tests** — `scan_results.generate_test_suite("…")` converts detected vulnerabilities into a reproducible **test suite** you can `run()` and wire into pytest/CI, so fixes stay fixed (see [Appendix](#appendix--categories-test-suites--v3)).
- **Docs** — [Scan results](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html)

## Installation & setup

Install the LLM extra:

```bash
pip install "giskard[llm]" --upgrade
```

> **Note:** Giskard supports **Python 3.9–3.12**. A fresh virtual environment (`venv` or `conda`) is recommended.

Because the LLM-assisted detectors need a **judge LLM**, configure a provider before scanning:

```python
import os
import giskard

os.environ["OPENAI_API_KEY"] = "sk-…"
giskard.llm.set_llm_model("gpt-4o")                       # judge model
giskard.llm.set_embedding_model("text-embedding-3-small") # for similarity-based checks
```

> Giskard routes judge-model calls through **LiteLLM**, so any LiteLLM-supported provider works — for example a local model:
> ```python
> giskard.llm.set_llm_model("ollama/qwen2.5", api_base="http://localhost:11434")
> ```
> See the [LLM setup docs](https://legacy-docs.giskard.ai/en/stable/open_source/setting_up/index.html) for Azure OpenAI, Mistral, Bedrock, Gemini, and Groq.

## Scanning an LLM

```python
import giskard
import pandas as pd

# 1. your LLM app as a plain function: DataFrame in, list of strings out
def predict(df: pd.DataFrame):
    return [answer(question) for question in df["question"]]

# 2. wrap it — the description drives which tests get generated
model = giskard.Model(
    model=predict,
    model_type="text_generation",
    name="Climate QA bot",
    description="Answers questions about climate change based on IPCC reports. "
                "Must stay on topic and refuse unrelated or unsafe requests.",
    feature_names=["question"],
)

# 3. (optional) seed with a few real inputs; omit to let Giskard generate them
dataset = giskard.Dataset(
    pd.DataFrame({"question": ["What causes sea-level rise?", "Summarise IPCC AR6."]}),
    target=None,
)

# 4. scan (use only="…" to limit to one category)
scan_results = giskard.scan(model, dataset)

# 5. results
scan_results.to_html("scan_report.html")
```

**Tip:** start with `giskard.scan(model, only="hallucination")` on a couple of examples to confirm your setup and judge-LLM key before running the full scan.

## Reading the report

The report groups **vulnerabilities by category and severity (major / medium / minor)**, each with the prompts and outputs that triggered it. To act on a scan:

1. **Triage by severity** — start with *major* findings and open the examples to confirm each is a true positive rather than a grading artifact.
2. **Fix and re-scan** — patch the prompt, add a guardrail or filter, then re-run the scan to confirm the vulnerability is gone.
3. **Lock it in** — promote confirmed findings into a **test suite** (`scan_results.generate_test_suite(...)`, then `suite.run()`) and run it in CI so regressions are caught.

- **Docs** — [Scan results](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html)

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Scan errors with no/invalid LLM client | Judge LLM not configured | Set `OPENAI_API_KEY` (or `giskard.llm.set_llm_model(...)` for another provider). |
| Tests feel generic or off-topic | Vague model `description` | Write a specific description — Giskard generates tests from it. |
| Scan is slow or expensive | LLM-assisted detectors call the judge many times | Limit with `only="…"`, scan fewer examples, or use a cheaper judge model. |
| `predict` raises errors | Wrong function shape | It must take a `DataFrame` and return a list of strings; columns must match `feature_names`. |
| Rate-limit errors mid-scan | Judge or target throttling | Reduce volume, add retries/backoff, or use a higher-tier key. |

- **Docs** — [LLM Scan](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html) · [GitHub issues](https://github.com/Giskard-AI/giskard-oss/issues)

## Appendix — categories, test suites & v3

- **Scan one category:** `giskard.scan(model, only="hallucination")` narrows the run to a single category; see the [LLM Scan docs](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html) for the available category tags.
- **Test suites:** `suite = scan_results.generate_test_suite("My suite")` then `suite.run()` turns detected vulnerabilities into reproducible tests you can re-run in CI.
- **RAG apps:** Giskard's **RAGET** (RAG Evaluation Toolkit) generates question/answer test sets from a knowledge base for business-logic failures — complementary to the security-focused LLM Scan.
- **Beyond LLMs:** the same `giskard.scan()` also tests **tabular ML** models (classification/regression) for performance bias, robustness, overconfidence, and more — out of scope for this LLM-focused tutorial, but the workflow (wrap → scan → report → test suite) is identical.
- **v3 landscape:** the linked [`giskard-oss`](https://github.com/Giskard-AI/giskard-oss) repo is moving to a modular v3 (`giskard-scan`, `giskard-checks`); the `giskard.scan` API here is the established, most-documented path.

## Resources

**Getting started**
- [Giskard documentation](https://docs.giskard.ai/)
- [GitHub — Giskard-AI/giskard-oss](https://github.com/Giskard-AI/giskard-oss)
- [LLM Quickstart](https://legacy-docs.giskard.ai/en/stable/getting_started/quickstart/quickstart_llm.html)

**LLM Scan reference**
- [LLM Scan](https://legacy-docs.giskard.ai/en/stable/open_source/scan/scan_llm/index.html)
- [LLM vulnerability categories](https://docs.giskard.ai/en/latest/knowledge/llm_vulnerabilities/index.html)
- [LLM detectors reference](https://legacy-docs.giskard.ai/en/stable/reference/scan/llm_detectors.html)
- [Setting up the LLM client](https://legacy-docs.giskard.ai/en/stable/open_source/setting_up/index.html)

**Community**
- [GitHub issues](https://github.com/Giskard-AI/giskard-oss/issues)
