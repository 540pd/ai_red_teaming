# Giskard (open-source) — Red-Teaming an LLM App · Learning Workbench

A hands-on tutorial for **red-teaming / vulnerability-scanning** an LLM application with the
**open-source** [Giskard](https://github.com/Giskard-AI/giskard-oss) library, built for learning
rather than production automation.

- **Notebook:** `giskard_tutorial.ipynb` — a step-by-step, runnable walkthrough.
- **This README:** the approach, the setup, and a condensed run sequence.

Companion to the `../promptfoo/` and `../garak/` workbenches; a cross-tool mapping is at the end.

References: <https://github.com/Giskard-AI/giskard-oss> · <https://www.giskard.ai>

---

## What this workbench is (and its constraints)

Giskard is a Python library that **tests and red-teams** LLM apps: a single `giskard.scan()` call
auto-detects whole categories of vulnerabilities (jailbreaks, harmful content, hallucination, data
leakage, stereotypes, …), then lets you freeze findings into a **reusable test suite** for
regression gating.

This workbench is shaped by four choices:

1. **Focus: red-teaming + Giskard's capabilities.** The core is `giskard.scan` and the test suite.
   Giskard's **RAGET** (RAG evaluation) is included as a short *overview* only (Section 9).
2. **Open-source only.** The OSS library — **not** the paid Giskard Hub. Everything runs locally.
3. **Target = a FastAPI HTTP endpoint.** Your app is served over HTTP; we wrap that endpoint as the
   model under test (assumed running and reachable).
4. **Evaluator LLM = Gemini.** The scan is LLM-assisted; Gemini generates probes and judges answers
   (assumed you have working Gemini access). It is separate from the target.

> **Version note:** the mature OSS scan + RAGET features are **v2**. Per the project README, v2
> "remains available but unmaintained" while a **v3** agentic rewrite is underway. This tutorial
> targets v2 — install with `pip install "giskard[llm]>2,<3"`.

---

## The mental model

| Component | Role | Analogy (promptfoo / garak) |
|-----------|------|------------------------------|
| **`giskard.Model`** *(wraps your endpoint)* | Black-box wrapper around a predict function | target/provider · generator |
| **`giskard.Dataset`** | Optional seed inputs the scan probes/perturbs | test vars · probe prompts |
| **`giskard.scan()`** | Auto-detects vulnerability categories → **ScanReport** | `redteam run` · `garak` scan |
| **Detectors** | The capabilities checked (injection, harm, hallucination, …) | plugins+strategies · probes+detectors |
| **Test suite** | Findings turned into re-runnable pass/fail tests | *(no direct equivalent)* |
| **RAGET** *(overview)* | Q&A test set from a knowledge base + RAG scoring | *(no direct equivalent)* |

### Workflow

```
  wrap FastAPI endpoint  ->  giskard.scan()  ->  ScanReport (HTML)  ->  generate_test_suite()  ->  CI gate
   (giskard.Model)           (red-team scan)     (severity-ranked)      (regression)
```

---

## What Giskard's scan can detect (capabilities)

| Capability | Probes for |
|---|---|
| **Prompt injection / jailbreak** | Input overriding system instructions; known jailbreak templates |
| **Harmful content** | Toxic, dangerous, or inappropriate generation |
| **Stereotypes / discrimination** | Bias across gender, race, religion, age, … |
| **Hallucination / misinformation** | Fabricated facts, sycophancy, implausible/self-contradicting output |
| **Sensitive info disclosure** | Leaking secrets, PII, or system-prompt contents |
| **Robustness** | Output instability under typos/control-chars/rephrasings |
| **Output formatting** | Violating a required output format/schema |

Distinctive strengths to lean on: **automatic probe generation** from your model `description`
(no hand-maintained attack corpus), **severity-ranked issues** with the offending input/output,
**focused runs** via `only=[...]`, **custom requirement-based checks** in natural language, and
**auto-generated regression tests** so a fixed issue can't silently return.

---

## Prerequisites (assumed working)

- `pip install "giskard[llm]>2,<3"` (Python 3.10+).
- Your **FastAPI endpoint** running and reachable; you know its request/response JSON shape.
- **Gemini access** — `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) set.
- `pandas`, `requests`.

---

## Condensed run sequence (Python)

```python
# 1) Evaluator on Gemini
import giskard
giskard.llm.set_llm_model("gemini/gemini-1.5-pro")
giskard.llm.set_embedding_model("gemini/text-embedding-004")

# 2) Wrap your FastAPI endpoint as the model under test
import requests, pandas as pd
ENDPOINT = "http://localhost:8000/chat"        # <-- your URL

def model_predict(df: pd.DataFrame):
    out = []
    for q in df["question"]:
        r = requests.post(ENDPOINT, json={"question": q}, timeout=30)
        r.raise_for_status()
        out.append(r.json()["answer"])          # <-- match your response key
    return out

model = giskard.Model(
    model=model_predict,
    model_type="text_generation",
    name="My FastAPI LLM Application",
    description="Detailed description of the app, its users, data, and hard limits.",
    feature_names=["question"],
)

# 3) Scan (focused first, then full)
giskard.scan(model, only=["jailbreak", "harmfulness"])   # smoke
report = giskard.scan(model)                              # full red-team pass
report.to_html("giskard_scan_report.html")
print(report.has_vulnerabilities, len(report.issues), "issues")

# 4) Freeze findings into a regression suite
suite = report.generate_test_suite(name="LLM app vulnerability suite")
print("passed:", suite.run().passed)
```

### RAGET (overview only — for RAG apps)

```python
from giskard.rag import KnowledgeBase, generate_testset, evaluate
kb = KnowledgeBase.from_pandas(df, columns=["text"])
testset = generate_testset(kb, num_questions=60, agent_description="...")
rag = evaluate(my_rag_answer_fn, testset=testset, knowledge_base=kb)
rag.to_html("giskard_rag_report.html")     # correctness + per-component scores
```

Use RAGET when the target is a RAG pipeline and you want to know *which component* (retriever vs
generator) is failing. If your app isn't RAG, skip it.

---

## Outputs

| Output | How | Contents |
|--------|-----|----------|
| **Scan report (HTML)** | `report.to_html("scan.html")` | Interactive vulnerability dashboard, grouped by capability, with offending examples |
| **Scan issues (objects)** | `report.issues`, `report.has_vulnerabilities` | Programmatic list for CI gating |
| **Test suite** | `report.generate_test_suite()` | Re-runnable pass/fail regression tests |
| **RAG report (HTML)** | `evaluate(...).to_html("rag.html")` | Correctness + per-component scores (RAGET) |

All local files / Python objects — no Hub, no upload.

---

## Cross-tool component map

| Concept | Giskard (OSS) | promptfoo | garak |
|---------|---------------|-----------|-------|
| Target model | `giskard.Model` (FastAPI wrapper) | target / provider | generator |
| Attack generation | `giskard.scan` detectors | plugins + strategies | probes + buffs |
| Pass/fail judgment | LLM-assisted detectors (Gemini) | grader / assertion | detectors |
| Vulnerability report | ScanReport HTML | red-team report | `.report.jsonl` / summary |
| Regression tests | **test suite** | (CI via eval) | (CI via re-run) |
| RAG evaluation | **RAGET** (overview) | context-* assertions | (n/a) |
| "Bad" outcome | an **issue** | a **failed** probe | a **hit** |

Giskard's distinctive additions are the **auto-generated regression suite** and **RAGET**.

---

## Troubleshooting

- **Scan errors about the LLM client** → `set_llm_model`/`set_embedding_model` not set, or
  `GEMINI_API_KEY` missing.
- **Endpoint errors during the scan** → the scan sends many requests; verify the URL, the JSON
  request/response keys, timeouts, and that the service handles the load.
- **Scan slow/costly** → use `only=[...]` and a small seed dataset; scanning is LLM-assisted.
- **API differs from this notebook** → you may be on a different major version; this targets **v2**.

---

## Files

| File | What it is |
|------|-----------|
| `giskard_tutorial.ipynb` | The full step-by-step learning notebook. |
| `README.md` | This overview: approach, setup, run steps, capabilities, outputs. |
