# Setup 2 — Python (DeepTeam + Giskard + DeepEval)

Pure-Python tier. Three tools, three distinct roles, one shared target seam:

| Tool | Role | File |
|---|---|---|
| **DeepTeam** | **Offense** — generate adversarial attacks (injection, jailbreak, multi-turn) | `attacks_deepteam.py` |
| **Giskard** | **Audit** — auto-scan + polished HTML report (+ RAGET for RAG later) | `scan_giskard.py` |
| **DeepEval** | **Measurement** — custom pass/fail metrics, CI gating | `scorers_deepeval.py` |

All three reach the app through `redteam_core` via `target_bridge.py`, so the app
is still defined once in `config/targets/`.

## Prerequisites

```bash
# From repo root
cp .env.example .env          # fill in target + a judge LLM key (e.g. OPENAI_API_KEY)
pip install -e .              # shared core
pip install deepteam giskard deepeval datasets
```

> These tools use a **judge/attacker LLM** to synthesize attacks and grade
> responses, so you need a provider key (e.g. `OPENAI_API_KEY`) in `.env`.

## Run

```bash
python setups/2_python/run.py                 # all three
python setups/2_python/run.py --only giskard  # just one
python setups/2_python/run.py --target chat_endpoint
```

Each tool runs independently — if one isn't installed or errors, the others still
run. Outputs land in `reports/<timestamp>_<target>_python/`:
- `deepteam_risk.txt` — risk assessment
- `giskard_scan.html` — audit report
- `deepeval_results.txt` — metric scores

## Customizing

- **Vulnerabilities / attacks:** edit the lists in `attacks_deepteam.py::_config()`.
- **Scan focus:** improve `MODEL_DESCRIPTION` in `scan_giskard.py` — better description → sharper probes.
- **Metrics / probes:** edit `PROBE_PROMPTS` and `metrics` in `scorers_deepeval.py`, or
  load larger sets via `redteam_core.seeds.load_seeds(...)`.

## RAG later

When the target becomes RAG, add RAGET in `scan_giskard.py` (Giskard's
retrieval-specific toolkit) and point at `config/targets/rag_endpoint.yaml`. No
changes needed to the offense or scoring files.
