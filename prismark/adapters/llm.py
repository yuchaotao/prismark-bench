"""LLM-as-detector adapter using Claude. Requires `pip install prismark-bench[llm]`.

Refusal fallbacks are deliberately *not* enabled: a silent switch to another
model would attribute that model's output to the one under test. Refusals are
counted instead (``self.refusals``).
"""

from __future__ import annotations

from prismark.adapters.base import Adapter
from prismark.adapters.prompt import SCHEMA, SYSTEM_PROMPT, spans_from_output
from prismark.schema import Span


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
        return spans_from_output(text, raw)
