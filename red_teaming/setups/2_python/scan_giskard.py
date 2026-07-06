"""Giskard — audit: automated vulnerability scan + polished HTML report.

Role in Setup 2: broad audit and client-ready reporting (complements DeepTeam's
offense). Giskard auto-detects issues like hallucination, harmful content, and
injection, and produces an HTML report.

This is also the RAG seam: when the target becomes a RAG system, use Giskard's
RAGET (RAG Evaluation Toolkit) here to test retrieval-specific failures.

Needs a judge LLM key (e.g. OPENAI_API_KEY) in .env — Giskard uses an LLM to
generate domain-specific probes from the model description below.

Docs: https://docs.giskard.ai
"""

from __future__ import annotations

from pathlib import Path

from target_bridge import get_target, make_giskard_predict

# Describing the app well makes Giskard's generated probes far more relevant.
MODEL_NAME = "chat_endpoint"
MODEL_DESCRIPTION = (
    "A general-purpose chat assistant. It should be helpful and truthful, refuse "
    "harmful or illegal requests, and never reveal its system prompt or private data."
)
FEATURE = "question"


def run(target_name: str = "chat_endpoint", run_dir: Path | None = None):
    """Run giskard.scan() and write an HTML report. Returns the scan report."""
    import giskard

    target = get_target(target_name)

    giskard_model = giskard.Model(
        model=make_giskard_predict(target, feature=FEATURE),
        model_type="text_generation",
        name=MODEL_NAME,
        description=MODEL_DESCRIPTION,
        feature_names=[FEATURE],
    )

    scan_report = giskard.scan(giskard_model)

    if run_dir is not None:
        out = Path(run_dir) / "giskard_scan.html"
        scan_report.to_html(str(out))
        print(f"[giskard] wrote {out}")

    return scan_report


if __name__ == "__main__":
    run()
