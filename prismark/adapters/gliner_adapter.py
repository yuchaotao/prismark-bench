"""GLiNER zero-shot span models (e.g. nvidia/gliner-pii, urchade/gliner_multi_pii-v1).

Requires `pip install prismark-bench[hf]`. GLiNER takes entity types as free
text, so the model is prompted with the PrisMark taxonomy itself: the same
boundary definition the LLM adapters get.
"""

from __future__ import annotations

from prismark.adapters.base import Adapter
from prismark.schema import Span

# PrisMark label -> natural-language entity type for GLiNER.
ENTITY_TYPES = {
    "PERSON_NAME": "person name",
    "EMAIL": "email address",
    "PHONE": "phone number",
    "SSN": "social security number",
    "PASSPORT": "passport number",
    "DRIVER_LICENSE": "driver's license number",
    "CREDIT_CARD": "credit card number",
    "BANK_ACCOUNT": "bank account number",
    "STREET_ADDRESS": "street address",
    "IP_ADDRESS": "ip address",
    "USERNAME": "username",
    "MEDICAL_RECORD_NUMBER": "medical record number",
    "DATE_OF_BIRTH": "date of birth",
    "AGE": "age",
    "ZIP_CODE": "zip code",
    "CITY": "city",
    "EMPLOYER": "employer",
    "JOB_TITLE": "job title",
    "HEALTH_CONDITION": "medical condition",
    "RELIGION": "religion",
    "SEXUAL_ORIENTATION": "sexual orientation",
    "POLITICAL_AFFILIATION": "political affiliation",
    "ETHNICITY": "ethnicity",
    "CRIMINAL_RECORD": "criminal record",
    "INDIRECT_IDENTIFIER": "description that identifies a specific person",
}
_TO_LABEL = {v: k for k, v in ENTITY_TYPES.items()}


class GLiNERAdapter(Adapter):
    def __init__(self, model: str, name: str | None = None, threshold: float = 0.5) -> None:
        import torch
        from gliner import GLiNER

        self.model = GLiNER.from_pretrained(model)
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
        self.name = name or model
        self.threshold = threshold

    def detect(self, text: str) -> list[Span]:
        ents = self.model.predict_entities(text, list(ENTITY_TYPES.values()), threshold=self.threshold)
        return [Span(e["start"], e["end"], _TO_LABEL.get(e["label"], e["label"])) for e in ents]
