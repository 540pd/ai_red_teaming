# Setup 1 — Easy (Promptfoo + Garak)

Broad, black-box, no-code red-team scan of the chat endpoint. Config-driven (YAML/JSON),
fastest path to a report. This is the **default front door** — run it on every app first.

## Prerequisites

```bash
# From repo root
cp .env.example .env          # then fill in TARGET_CHAT_URL + TARGET_CHAT_API_KEY
npm install                   # installs promptfoo (Node >= 18)
pip install garak
```

## Run everything

```bash
./setups/1_easy/run.sh
```

This runs both tools against the endpoint and drops results into `reports/<timestamp>_chat_easy/`.

## Run tools individually

```bash
# promptfoo only
npx promptfoo redteam run -c setups/1_easy/promptfooconfig.yaml
npx promptfoo redteam report            # open the HTML report

# garak only
garak --model_type rest -G setups/1_easy/garak_rest.json \
      --probes promptinject,encoding,leakreplay
```

## What each tool covers

| Tool | Config | Covers |
|---|---|---|
| **promptfoo** | `promptfooconfig.yaml` | harmful content, PII leak, prompt extraction, hijacking, excessive agency — via jailbreak / injection / base64 strategies |
| **garak** | `garak_rest.json` | prompt injection, encoding evasion, training-data/leak replay probes |

## Customizing

- **More attacks:** add plugins/strategies in `promptfooconfig.yaml`, or more `--probes` for garak.
- **Deeper scan:** raise `numTests` in `promptfooconfig.yaml`.
- **Different app:** the endpoint shape is defined here and in `config/targets/chat_endpoint.yaml`.
  Keep them in sync (both mirror the same request/response format).
