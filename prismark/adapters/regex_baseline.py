"""A dependency-free regex baseline. It sets the floor every real tool should beat."""

from __future__ import annotations

import re

from prismark.adapters.base import Adapter
from prismark.schema import Span

PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "PHONE": re.compile(r"(?:\+1[ .-]?)?\(?\b\d{3}\)?[ .-]?\d{3}[ .-]\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "BANK_ACCOUNT": re.compile(r"\b[A-Z]{2}\d{2}(?: ?\d{4}){4}(?: ?\d{1,4})?\b"),
}


class RegexBaseline(Adapter):
    name = "regex"

    def detect(self, text: str) -> list[Span]:
        return [Span(m.start(), m.end(), label) for label, pat in PATTERNS.items() for m in pat.finditer(text)]
