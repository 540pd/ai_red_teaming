# Seed corpora

Standard harmful-behavior prompt sets used to seed custom probes. Loaded via
`redteam_core.seeds.load_seeds("<name>")`.

Format: `.txt` (one prompt per line) or `.jsonl` (objects with a `"prompt"` field).

## Recommended sets

| Name | Source |
|---|---|
| `advbench` | AdvBench — adversarial harmful-behavior strings |
| `jailbreakbench` | JailbreakBench — jailbreak prompt benchmark |
| `harmbench` | HarmBench — standardized harmful-behavior set |

## Fetching (example)

These ship via HuggingFace `datasets`:

```python
from datasets import load_dataset

ds = load_dataset("walledai/AdvBench")["train"]
with open("seeds/advbench.txt", "w") as f:
    for row in ds:
        f.write(row["prompt"].replace("\n", " ") + "\n")
```

> Note: these corpora contain intentionally harmful prompts for **testing only**.
> They are **not** gitignored by default. If your policy disallows committing them,
> add `seeds/*.txt` and `seeds/*.jsonl` to `.gitignore`.
