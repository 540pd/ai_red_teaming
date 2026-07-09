# garak — LLM Vulnerability Scanning · Learning Workbench

A hands-on tutorial for scanning an LLM for vulnerabilities with
[NVIDIA **garak**](https://github.com/NVIDIA/garak) (Generative AI Red-teaming & Assessment Kit),
built for learning rather than production automation.

- **Notebook:** `garak_tutorial.ipynb` — a step-by-step, runnable walkthrough.
- **This README:** the *why* behind the approach, plus a condensed run sequence.

It is a companion to the promptfoo workbench in `../promptfoo/`; the two tools do the same job with
different vocabulary, and a mapping table appears at the end.

References: <https://garak.ai> · <https://github.com/NVIDIA/garak>

---

## What garak is (and what it can do)

garak "checks if an LLM can be made to fail in a way we don't want." It probes a model or system
for **jailbreaks, prompt injection, data/training-data leakage, toxicity, malware generation,
encoding-smuggled instructions, glitch tokens, hallucination/snowballing**, and more — using
static, dynamic, and adaptive attacks. It is **open-source, Python-native, and friendly on the
command line**, actively maintained by NVIDIA and the community (Apache-2.0).

### Why this workbench looks the way it does

1. **Learning-first.** Every concept gets a plain-language explanation before any command.
2. **Python-native — so we use both surfaces.** Unlike promptfoo (a Node CLI), garak *is* a Python
   package. Its primary interface is `python -m garak ...`, and we also `import garak`, enumerate
   plugins, and parse its JSONL output natively with `pandas`.
3. **Target assumed configured.** You already have a **generator** (model interface) that garak can
   reach — a HuggingFace model, an OpenAI-compatible endpoint, a REST target, `nim`, `ggml`, etc.,
   with any API keys exported. The notebook only points at it.
4. **Open-source, local.** Runs on your machine; results are local files. No account or upload.

---

## The mental model — five plugin types

| Component | Role | Analogy (promptfoo) |
|-----------|------|---------------------|
| **Generator** *(configured)* | The model/system under test + how to reach it | target / provider |
| **Probe** | Attack module — generates prompts to elicit a specific failure | plugin + strategy |
| **Detector** | Judges each output; a flagged output is a **hit** | grader / assertion |
| **Buff** | Transforms probe prompts (paraphrase, encode, translate) to widen coverage | strategy |
| **Harness** | Orchestrates probe → generator → detector (`probewise` default, or `pxd`) | the eval runner |
| **Evaluator** | Turns detector scores into pass/fail via a threshold | pass/fail logic |

> **Scoring is inverted vs promptfoo.** In garak a **hit** means the attack **succeeded** — a
> vulnerability was found. Higher hit rate / lower pass rate is **worse**.

### Workflow

```
  choose probes (+buffs)  ->  run scan (probe -> generator -> detector)  ->  report
                                 = hits                                     .report.jsonl
                                                                            .hitlog.jsonl + summary
```

---

## Prerequisites (assumed already done)

- garak installed: `python -m pip install -U garak` (Python 3.10–3.12; a venv/conda env is wise).
- A configured **generator** — you know its `--model_type` and `--model_name`, and any API keys
  (`OPENAI_API_KEY`, `HF_TOKEN`, …) are exported.
- For the analysis cells: `pandas`.

---

## Condensed run sequence (copy-paste into a terminal)

```bash
# 0) Credentials for your configured generator (skip for local/test models).
# export OPENAI_API_KEY=sk-...

# 1) Work in a dedicated folder.
mkdir -p garak_run && cd garak_run

# 2) Confirm the install.
python -m garak --version

# 3) Discover what's available.
python -m garak --list_probes
python -m garak --list_detectors
python -m garak --list_buffs

# 4) SMOKE TEST — one probe, one generation, confirm the pipeline works.
python -m garak --model_type openai --model_name gpt-4o-mini \
    --probes dan.Dan_11_0 --generations 1 --report_prefix garak_smoke

# 5) A focused scan across a few probe families.
python -m garak --model_type openai --model_name gpt-4o-mini \
    --probes dan,encoding,promptinject \
    --generations 5 --seed 42 --parallel_attempts 8 \
    --report_prefix garak_scan

# 6) Review: read the end-of-run PASS/FAIL summary, then the outputs (below).
```

> The `test` generator (`--model_type test.Blank`) needs no real model — handy for a dry run of the
> tooling itself without spending tokens.

### Reproducible runs — a config file

```yaml
# garak_run.yaml  ->  run with: python -m garak --config garak_run.yaml
run:
  generations: 5
  seed: 42
  parallel_attempts: 8
plugins:
  model_type: openai            # your generator
  model_name: gpt-4o-mini       # your model id
  probe_spec: dan,encoding,promptinject
  # buff_spec: paraphrase       # optional: widen coverage
reporting:
  report_prefix: garak_cfg_scan
```

---

## Discovering & counting components

Ask garak, don't guess from docs — each list matches your installed version:

```bash
python -m garak --list_probes        # the attack menu (module.Class names)
python -m garak --list_detectors     # the judges
python -m garak --list_buffs         # prompt transforms
python -m garak --list_generators    # model interfaces
python -m garak --plugin_info probes.dan.Dan_11_0   # details for one plugin
```

The notebook also captures these into Python and **counts probes per family**, so you can pick a
focused subset instead of the (very long) `--probes all`.

---

## Referencing probes, detectors, buffs

```bash
--probes dan                 # all classes in the dan module
--probes dan.Dan_11_0        # one specific probe class
--probes dan,encoding,xss    # several modules/classes
--detectors toxicity.ToxicCommentModel   # override the probe's default judge
--extended_detectors mitigation.MitigationBypass
--buffs paraphrase,lowresource           # stack prompt transforms
--eval_threshold 0.5                     # score cutoff for a hit
```

**Notable probe families:** `dan` (jailbreaks), `promptinject`, `encoding`, `malwaregen`, `xss`,
`leakreplay`, `glitch`, `continuation`, `realtoxicityprompts`, `snowball`, `lmrc`,
`latentinjection`.

---

## Outputs and reporting

**Live:** progress bars, then a per-probe **PASS/FAIL** summary with `passing/total` counts and
failure rates — often enough for a quick read.

**On disk** (prefix = `--report_prefix`, else a UUID):

| File | Contents |
|------|----------|
| `*.report.jsonl` | Per-line JSON: config, every **attempt** (prompt+outputs+scores), and **eval** summaries per probe×detector. The canonical machine-readable result. |
| `*.hitlog.jsonl` | Only the **hits** — attempts judged vulnerable. Your concrete findings. |
| `garak.log` | Debug/errors (shared across runs). |

garak also ships a **built-in analysis helper** (`analyse/analyse_log.py` in the source tree) that
surfaces the probes and prompts producing the most hits. The notebook additionally parses the
`.report.jsonl` with pandas to compute hit rates per probe×detector and to dump the hitlog findings.

*(Some garak versions also emit an HTML summary; the JSONL files are the stable outputs this
workbench relies on.)*

---

## Command & flag cheat-sheet

```bash
# Discover
python -m garak --list_probes | --list_detectors | --list_buffs | --list_generators
python -m garak --plugin_info probes.dan.Dan_11_0

# Run
python -m garak --model_type <type> --model_name <name> \
    --probes dan,encoding --generations 5 --seed 42 \
    --parallel_attempts 8 --report_prefix myscan
python -m garak --config garak_run.yaml
```

```
--model_type / --model_name    generator + model (aka --target_type / --target_name)
--probes / --detectors / --buffs   what to run
--generations N                outputs per prompt
--probe_options / -P           per-probe configuration
--parallel_attempts N          concurrent probe attempts
--parallel_requests N          concurrent generator requests (rate limits)
--seed N                       reproducible sampling
--eval_threshold X             detector score cutoff for a hit
--report_prefix NAME           output filename prefix
--config FILE                  YAML run config
```

---

## garak ↔ promptfoo quick map

| Concept | garak | promptfoo |
|---------|-------|-----------|
| Target model | **generator** | target / provider |
| Attack generator | **probe** | plugin + strategy |
| Attack transform | **buff** | strategy |
| Pass/fail judge | **detector** (+ evaluator/threshold) | grader / assertion |
| "Bad" outcome | **hit** (attack succeeded) | **failed** probe |
| Machine results | `*.report.jsonl` / `*.hitlog.jsonl` | `results.json` |
| List components | `--list_probes` / `--list_detectors` / `--list_buffs` | `promptfoo redteam plugins` |

> Remember the inverted scoring: a garak **hit** == a promptfoo **fail** == a vulnerability.

---

## Troubleshooting

- **Detector fails to load a model** → an offline machine can't fetch a HuggingFace classifier; use
  a string-based detector or pre-download the models.
- **Run is huge / slow** → fewer probes, lower `--generations`, drop buffs; use `--probes all` only
  when you truly mean it.
- **Rate limits / target errors** → lower `--parallel_requests`; confirm API keys are exported.
- **"Hit rate looks inverted"** → correct: in garak a **hit is a vulnerability** (attack succeeded).

---

## Files

| File | What it is |
|------|-----------|
| `garak_tutorial.ipynb` | The full step-by-step learning notebook. |
| `README.md` | This overview: approach, workflow, run steps, outputs. |
