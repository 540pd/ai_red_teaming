"""redteam_core — shared layer for the AI red-teaming asset.

Exposes the target seam (adapters + config loading) and reporting helpers used
across all three setups. See AI_RedTeaming_Asset_Design.md for the full design.
"""

from redteam_core.targets import Target, load_target

__all__ = ["Target", "load_target"]
__version__ = "0.1.0"
