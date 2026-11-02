"""Microsoft Presidio adapter. Requires `pip install prismark-bench[presidio]` and a spaCy model."""

from __future__ import annotations

from prismark.adapters.base import Adapter
from prismark.schema import Span

# Presidio entity -> PrisMark label (used only for per-label breakdowns).
LABEL_MAP = {
    "PERSON": "PERSON_NAME",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "US_SSN": "SSN",
    "US_PASSPORT": "PASSPORT",
    "US_DRIVER_LICENSE": "DRIVER_LICENSE",
    "CREDIT_CARD": "CREDIT_CARD",
    "IBAN_CODE": "BANK_ACCOUNT",
    "US_BANK_NUMBER": "BANK_ACCOUNT",
    "IP_ADDRESS": "IP_ADDRESS",
    "LOCATION": "CITY",
    "DATE_TIME": "DATE_OF_BIRTH",
    "NRP": "ETHNICITY",
    "MEDICAL_LICENSE": "MEDICAL_RECORD_NUMBER",
}


class PresidioAdapter(Adapter):
    name = "presidio"

    def __init__(self, score_threshold: float = 0.35) -> None:
        from presidio_analyzer import AnalyzerEngine

        self.engine = AnalyzerEngine()
        self.score_threshold = score_threshold

    def detect(self, text: str) -> list[Span]:
        results = self.engine.analyze(text=text, language="en", score_threshold=self.score_threshold)
        return [Span(r.start, r.end, LABEL_MAP.get(r.entity_type, r.entity_type)) for r in results]
