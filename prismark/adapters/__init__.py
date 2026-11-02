"""Registry of tool adapters. Optional dependencies are imported lazily."""

from __future__ import annotations

from prismark.adapters.base import Adapter


def load(name: str) -> Adapter:
    if name == "regex":
        from prismark.adapters.regex_baseline import RegexBaseline

        return RegexBaseline()
    if name == "presidio":
        from prismark.adapters.presidio import PresidioAdapter

        return PresidioAdapter()
    if name == "claude" or name.startswith("claude:"):
        from prismark.adapters.llm import ClaudeAdapter

        _, _, model = name.partition(":")
        return ClaudeAdapter(model=model) if model else ClaudeAdapter()
    raise ValueError(f"unknown tool {name!r}; available: {', '.join(AVAILABLE)}")


AVAILABLE = ["regex", "presidio", "claude[:<model>]"]
