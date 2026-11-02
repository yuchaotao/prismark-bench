"""Hugging Face token-classification models (e.g. openai/privacy-filter, piiranha).

Requires `pip install prismark-bench[hf]`. Each model keeps its own label set;
the scorer is label-agnostic, so no mapping to the PrisMark taxonomy is needed.
"""

from __future__ import annotations

from prismark.adapters.base import Adapter
from prismark.schema import Span


class HFTokenClassifier(Adapter):
    def __init__(self, model: str, name: str | None = None, threshold: float = 0.0) -> None:
        import torch
        from transformers import pipeline

        self.pipe = pipeline(
            "token-classification",
            model=model,
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1,
        )
        self.name = name or model
        self.threshold = threshold

    def detect(self, text: str) -> list[Span]:
        spans = []
        for ent in self.pipe(text):
            if ent["score"] < self.threshold:
                continue
            start, end = ent["start"], ent["end"]
            # Some tokenizers include the leading space in the span.
            while start < end and text[start].isspace():
                start += 1
            spans.append(Span(start, end, ent["entity_group"]))
        return spans
