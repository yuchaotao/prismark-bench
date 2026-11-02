"""Data model shared by the generator, the adapters, and the scorer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Iterator


@dataclass
class Span:
    start: int
    end: int
    label: str

    def text(self, source: str) -> str:
        return source[self.start : self.end]


@dataclass
class Example:
    id: str
    text: str
    # Spans a privacy tool should act on (labels from taxonomy.LABELS).
    spans: list[Span] = field(default_factory=list)
    # Hard negatives a privacy tool should leave alone (taxonomy.NEGATIVE_LABELS).
    negatives: list[Span] = field(default_factory=list)
    domain: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Example":
        return cls(
            id=d["id"],
            text=d["text"],
            spans=[Span(**s) for s in d.get("spans", [])],
            negatives=[Span(**s) for s in d.get("negatives", [])],
            domain=d.get("domain", ""),
            tags=list(d.get("tags", [])),
        )


def read_jsonl(path: str | Path) -> Iterator[Example]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield Example.from_dict(json.loads(line))


def write_jsonl(path: str | Path, examples: Iterable[Example]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for ex in examples:
            f.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")
