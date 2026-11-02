"""LLM-as-detector adapter using Claude. Requires `pip install prismark-bench[llm]`.

The model returns the exact substrings it considers private; we map them back
to offsets. Asking for substrings instead of offsets avoids scoring the model's
ability to count characters.

Refusal fallbacks are deliberately *not* enabled: a silent switch to another
model would attribute that model's output to the one under test. Refusals are
counted instead (``self.refusals``).
"""

from __future__ import annotations

import json

from prismark.adapters.base import Adapter, locate
from prismark.schema import Span
from prismark.taxonomy import LABELS, NEGATIVE_LABELS

SYSTEM_PROMPT = (
    "You are a privacy filter. Find every span in the user's text that exposes private information "
    "about a specific individual, using these categories:\n"
    + "\n".join(f"- {l.name}: {l.description}" for l in LABELS.values())
    + "\n\nDo NOT flag the following, which are outside the privacy boundary:\n"
    + "\n".join(f"- {name}: {desc}" for name, desc in NEGATIVE_LABELS.items())
    + "\n\nReturn each span as the exact substring copied from the text, with its category."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "spans": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "label": {"type": "string", "enum": sorted(LABELS)},
                },
                "required": ["text", "label"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["spans"],
    "additionalProperties": False,
}


class ClaudeAdapter(Adapter):
    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium") -> None:
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.name = f"claude:{model}"
        self.refusals = 0

    def detect(self, text: str) -> list[Span]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        )
        if response.stop_reason == "refusal":
            self.refusals += 1
            return []
        raw = next(b.text for b in response.content if b.type == "text")
        spans = []
        for item in json.loads(raw)["spans"]:
            spans.extend(Span(s, e, item["label"]) for s, e in locate(text, item["text"]))
        return spans
