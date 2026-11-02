"""Local LLM-as-detector adapter via an Ollama server (no extra Python dependencies).

Uses the same prompt and schema as the Claude adapter. Ollama constrains the
output to the JSON schema. Thinking is off by default for speed; pass
``think=True`` to compare.
"""

from __future__ import annotations

import json
import os
import urllib.request

from prismark.adapters.base import Adapter
from prismark.adapters.prompt import SCHEMA, SYSTEM_PROMPT, spans_from_output
from prismark.schema import Span


class OllamaAdapter(Adapter):
    def __init__(self, model: str, host: str | None = None, think: bool = False) -> None:
        self.model = model
        self.host = host or os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
        self.think = think
        self.name = f"ollama:{model}"
        self.parse_errors = 0

    def detect(self, text: str) -> list[Span]:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
            "format": SCHEMA,
            "stream": False,
            "think": self.think,
            "options": {"temperature": 0, "seed": 0},
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            raw = json.loads(resp.read())["message"]["content"]
        try:
            return spans_from_output(text, raw)
        except (json.JSONDecodeError, KeyError, TypeError):
            self.parse_errors += 1
            return []
