"""Scoring.

Tools use different label sets, so the headline metrics are label-agnostic:
the question is whether the private text was protected, not whether the tool
called it the same name we did. Per-label and per-tier breakdowns use the gold
label of each span.

Detection metrics (from predicted spans):
  protected_recall  - share of gold spans whose every non-space char is covered.
                      Partially masking "Avery Okafor" to "Avery ****" still leaks.
  overlap_recall    - share of gold spans touched by any prediction (lenient view;
                      the gap to protected_recall is the cost of partial masking).
  char_precision    - share of predicted chars that fall inside a gold span.
  char_recall       - share of gold chars covered by a prediction.
  exact_f1          - NER-style F1 on exact (start, end) boundaries.
  negative_fp_rate  - share of hard-negative spans touched by a prediction.

Redaction metrics (from output text):
  leakage_rate      - share of gold values that still appear whole in the output.
  fragment_leakage_rate - share of gold values with any distinctive word left
                      in the output (e.g. a surname after the first name was masked).
  negative_keep     - share of hard-negative values kept in the output.
  utility           - word-level similarity to the gold redaction.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from prismark.schema import Example, Span
from prismark.taxonomy import tier_of

PLACEHOLDER = "<PII>"
_PLACEHOLDER_RE = re.compile(r"\[[^\]\n]{1,40}\]|<[A-Za-z_ ]{1,40}>|\*{3,}|█+|X{4,}")


@dataclass
class Prediction:
    spans: list[Span] = field(default_factory=list)
    redacted: str | None = None


def _covered(spans: list[Span], length: int) -> list[bool]:
    mask = [False] * length
    for s in spans:
        for i in range(max(0, s.start), min(length, s.end)):
            mask[i] = True
    return mask


def redact_with_spans(text: str, spans: list[Span]) -> str:
    """Replace the union of spans with a placeholder."""
    mask = _covered(spans, len(text))
    out, i = [], 0
    while i < len(text):
        if mask[i]:
            while i < len(text) and mask[i]:
                i += 1
            out.append(PLACEHOLDER)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def value_leaked(value: str, output: str) -> bool:
    v = _norm(value)
    if re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", _norm(output)):
        return True
    # Catch reformatting such as "123-45-6789" -> "123 45 6789". Short values are
    # skipped because alnum-only matching would find them inside other words.
    a = _alnum(value)
    return len(a) >= 6 and a in _alnum(output)


def fragment_leaked(value: str, output: str, reference: str) -> bool:
    """True if the value, or any word of it, survives in the output.

    Words that also occur in the gold redaction (e.g. "the", "at") are
    ignored, since their presence says nothing about the private value.
    """
    if value_leaked(value, output):
        return True
    ref_words = set(re.findall(r"[a-z0-9]+", reference.lower()))
    out_words = set(re.findall(r"[a-z0-9]+", output.lower()))
    return any(w in out_words for w in re.findall(r"[a-z0-9]+", value.lower()) if len(w) >= 3 and w not in ref_words)


def _words(s: str) -> list[str]:
    return _PLACEHOLDER_RE.sub(PLACEHOLDER, s).split()


class _Counter:
    def __init__(self) -> None:
        self.hit = 0
        self.total = 0

    def add(self, ok: bool) -> None:
        self.total += 1
        self.hit += int(ok)

    @property
    def rate(self) -> float | None:
        return self.hit / self.total if self.total else None


def _f1(p: float | None, r: float | None) -> float | None:
    if p is None or r is None:
        return None
    return 2 * p * r / (p + r) if p + r else 0.0


def score(examples: list[Example], predictions: dict[str, Prediction]) -> dict:
    protected = _Counter()
    touched = _Counter()
    by_tier: dict[str, _Counter] = defaultdict(_Counter)
    by_label: dict[str, _Counter] = defaultdict(_Counter)
    by_tag: dict[str, _Counter] = defaultdict(_Counter)
    char_tp = char_pred = char_gold = 0
    exact_tp = exact_pred = exact_gold = 0
    neg_fp = _Counter()
    leaked = _Counter()
    fragment = _Counter()
    neg_keep = _Counter()
    utility_sum = 0.0

    for ex in examples:
        pred = predictions.get(ex.id, Prediction())
        n = len(ex.text)
        pmask = _covered(pred.spans, n)
        gmask = _covered(ex.spans, n)

        for s in ex.spans:
            chars = [i for i in range(s.start, s.end) if not ex.text[i].isspace()]
            ok = all(pmask[i] for i in chars)
            protected.add(ok)
            touched.add(any(pmask[i] for i in chars))
            by_tier[f"T{int(tier_of(s.label))}"].add(ok)
            by_label[s.label].add(ok)
            for tag in ex.tags:
                by_tag[tag].add(ok)

        for i in range(n):
            if ex.text[i].isspace():
                continue
            char_pred += pmask[i]
            char_gold += gmask[i]
            char_tp += pmask[i] and gmask[i]

        gold_bounds = {(s.start, s.end) for s in ex.spans}
        pred_bounds = {(s.start, s.end) for s in pred.spans}
        exact_tp += len(gold_bounds & pred_bounds)
        exact_pred += len(pred_bounds)
        exact_gold += len(gold_bounds)

        for s in ex.negatives:
            neg_fp.add(any(pmask[i] for i in range(s.start, s.end)))

        output = pred.redacted if pred.redacted is not None else redact_with_spans(ex.text, pred.spans)
        reference = redact_with_spans(ex.text, ex.spans)
        for s in ex.spans:
            leaked.add(value_leaked(s.text(ex.text), output))
            fragment.add(fragment_leaked(s.text(ex.text), output, reference))
        for s in ex.negatives:
            neg_keep.add(value_leaked(s.text(ex.text), output))
        utility_sum += SequenceMatcher(None, _words(reference), _words(output), autojunk=False).ratio()

    char_precision = char_tp / char_pred if char_pred else None
    exact_p = exact_tp / exact_pred if exact_pred else None
    exact_r = exact_tp / exact_gold if exact_gold else None

    return {
        "n_examples": len(examples),
        "n_spans": protected.total,
        "n_negatives": neg_fp.total,
        "protected_recall": protected.rate,
        "overlap_recall": touched.rate,
        "char_precision": char_precision,
        "char_recall": char_tp / char_gold if char_gold else None,
        "privacy_f1": _f1(char_precision, protected.rate),
        "exact_f1": _f1(exact_p, exact_r),
        "negative_fp_rate": neg_fp.rate,
        "leakage_rate": leaked.rate,
        "fragment_leakage_rate": fragment.rate,
        "negative_keep": neg_keep.rate,
        "utility": utility_sum / len(examples) if examples else None,
        "by_tier": {k: by_tier[k].rate for k in sorted(by_tier)},
        "by_label": {k: by_label[k].rate for k in sorted(by_label)},
        "by_tag": {k: by_tag[k].rate for k in sorted(by_tag)},
    }
