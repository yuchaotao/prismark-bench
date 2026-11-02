"""Adapter interface for privacy tools under test.

An adapter wraps one tool. It implements ``detect`` (span output), ``redact``
(text output), or both. The scorer derives a redaction from spans when a tool
only detects, so every tool is scored on both detection and redaction where
possible.
"""

from __future__ import annotations

import re

from prismark.metrics import Prediction
from prismark.schema import Span


class Adapter:
    name: str = "base"

    def detect(self, text: str) -> list[Span] | None:
        return None

    def redact(self, text: str) -> str | None:
        return None

    def predict(self, text: str) -> Prediction:
        return Prediction(spans=self.detect(text) or [], redacted=self.redact(text))


def locate(text: str, needle: str) -> list[tuple[int, int]]:
    """All non-overlapping occurrences of needle in text (for tools that return strings, not offsets)."""
    if not needle:
        return []
    return [(m.start(), m.end()) for m in re.finditer(re.escape(needle), text)]
