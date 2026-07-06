"""Target adapters — the one integration seam: send(prompt) -> response."""

from redteam_core.adapters.http_target import HttpTarget

__all__ = ["HttpTarget"]
