"""DeepTeam — offense: generate adversarial attacks against the target.

Role in Setup 2: attack generation. Declares vulnerabilities to probe and attack
methods to deliver them, then runs a red-team pass and returns a risk assessment.

Needs a judge/attacker LLM key (e.g. OPENAI_API_KEY) in .env — DeepTeam uses an
LLM to synthesize attacks and grade responses.

Docs: https://www.trydeepteam.com
"""

from __future__ import annotations

from pathlib import Path

from target_bridge import get_target, make_deepteam_callback

# --- What to test for (vulnerabilities) and how to attack (methods) -----------
# Trim/extend these lists to shape the scan. Kept modest by default for speed.


def _config():
    from deepteam.vulnerabilities import Bias, Toxicity, PIILeakage, Misinformation
    from deepteam.attacks.single_turn import (
        PromptInjection,
        Roleplay,
        Base64,
        Leetspeak,
    )
    from deepteam.attacks.multi_turn import LinearJailbreaking

    vulnerabilities = [Bias(), Toxicity(), PIILeakage(), Misinformation()]
    attacks = [
        PromptInjection(),
        Roleplay(),
        Base64(),
        Leetspeak(),
        LinearJailbreaking(),  # multi-turn
    ]
    return vulnerabilities, attacks


def run(target_name: str = "chat_endpoint", run_dir: Path | None = None):
    """Run the DeepTeam red-team pass. Returns the risk assessment object."""
    from deepteam import red_team

    target = get_target(target_name)
    callback = make_deepteam_callback(target)
    vulnerabilities, attacks = _config()

    risk_assessment = red_team(
        model_callback=callback,
        vulnerabilities=vulnerabilities,
        attacks=attacks,
    )

    if run_dir is not None:
        out = Path(run_dir) / "deepteam_risk.txt"
        out.write_text(str(risk_assessment))
        print(f"[deepteam] wrote {out}")

    return risk_assessment


if __name__ == "__main__":
    run()
