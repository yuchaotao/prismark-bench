"""Prompt and output schema shared by all LLM-as-detector adapters.

Every LLM gets the same boundary definition, so differences in score come from
the model, not the prompt. The model returns the exact substrings it considers
private; ``spans_from_output`` maps them back to offsets. Asking for substrings
instead of offsets avoids scoring the model's ability to count characters.
"""

from __future__ import annotations

import json

from prismark.adapters.base import locate
from prismark.schema import Span
from prismark.taxonomy import LABELS, NEGATIVE_LABELS

SYSTEM_PROMPT = (
    "You are a privacy filter. Find every span in the user's text that exposes private information "
    "about a specific individual, using these categories:\n"
    + "\n".join(f"- {l.name}: {l.description}" for l in LABELS.values())
    + "\n\nDo NOT flag the following, which are outside the privacy boundary:\n"
    + "\n".join(f"- {name}: {desc}" for name, desc in NEGATIVE_LABELS.items())
    + "\n\nReturn each span as the exact substring copied from the text, with its category. "
    "Include every mention, including repeated mentions and partial ones such as a first name used alone."
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


def spans_from_output(text: str, raw: str) -> list[Span]:
    spans = []
    for item in json.loads(raw)["spans"]:
        spans.extend(Span(s, e, item["label"]) for s, e in locate(text, item["text"]))
    return spans
