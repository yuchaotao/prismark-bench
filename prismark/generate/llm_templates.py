"""Author templates with a local LLM, then validate them.

The LLM writes *templates*, not data: every piece of person-specific
information must be a slot placeholder, which the generator later fills with
fictional values. Gold spans therefore stay exact, while the surrounding text
gets far more variety than hand-written templates.

The authoring model should not be a tool under test, or the data would be
written in that model's own style. The default is gpt-oss:20b via Ollama.

Every template passes three checks before it is kept:

1. Syntax: only known slots, required slots present, at least two private slots.
2. Pattern check: the literal text (slots removed) has no email, phone, card,
   SSN, or IP pattern and no long digit runs.
3. Leak judge: a second model call reads the literal text with slots masked
   and must find no private information outside the placeholders. Literal PII
   would be unlabeled and would wrongly penalize tools that catch it.
4. Coherence judge: the template is filled once and a model call checks that
   every value sits where it makes sense.
5. Negative judge: each hard-negative value is marked in a filled sample, and a
   model call checks it is not actually about a private person (e.g. a generic
   disease that the text attaches to a named person). Such a value would be
   scored as a negative while it is really private.

Usage:
    python -m prismark.generate.llm_templates --n 160 --out prismark/generate/llm_templates.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
import urllib.request
from pathlib import Path

from prismark.adapters.regex_baseline import PATTERNS
from prismark.generate.generator import NEGATIVES, SLOT_RE, SLOTS, render
from prismark.generate.templates import LLM_TEMPLATES_PATH, Template
from prismark.taxonomy import NEGATIVE_LABELS

DOMAINS = [
    ("email", "a workplace email"),
    ("chat", "a group chat or text message thread"),
    ("medical", "a clinical note, referral, or discharge summary"),
    ("hr", "an HR record, complaint, or performance review"),
    ("finance", "a bank, loan, or KYC document"),
    ("legal", "a court filing, deposition excerpt, or legal letter"),
    ("support", "a customer support ticket or call transcript"),
    ("social", "a social media post or forum comment"),
    ("education", "a school counselor note or parent-teacher email"),
    ("government", "a benefits application or caseworker note"),
    ("real_estate", "a rental application or landlord message"),
    ("travel", "a booking confirmation or travel itinerary"),
    ("insurance", "an insurance claim or adjuster note"),
    ("code", "an application log, config file, or CSV export"),
    ("news", "a local news comment section or neighborhood forum post"),
]

# Each spec must use one of these private-slot groups, so rare labels get coverage.
REQUIRED_GROUPS = [
    ["PERSON_NAME", "HEALTH"],
    ["FIRST_NAME", "ORIENTATION"],
    ["PERSON_NAME", "POLITICAL"],
    ["INDIRECT", "CRIMINAL"],
    ["INDIRECT", "HEALTH"],
    ["USERNAME", "IP_ADDRESS"],
    ["PERSON_NAME", "SSN", "DOB"],
    ["PERSON_NAME", "EMPLOYER", "JOB_TITLE"],
    ["FIRST_NAME", "RELIGION"],
    ["PERSON_NAME", "ETHNICITY"],
    ["PERSON_NAME", "STREET_ADDRESS", "CITY", "ZIP_CODE"],
    ["PERSON_NAME", "CREDIT_CARD"],
    ["PERSON_NAME", "BANK_ACCOUNT"],
    ["PERSON_NAME", "PASSPORT"],
    ["PERSON_NAME", "DRIVER_LICENSE"],
    ["PERSON_NAME", "MRN", "MEDICATION"],
    ["FIRST_NAME", "EMAIL_OBF"],
    ["FIRST_NAME", "PHONE_SPELLED"],
    ["FIRST_NAME", "AGE", "CITY"],
    ["PERSON_NAME", "EMAIL", "PHONE"],
    ["PERSON_NAME", "PERSON_NAME@2", "CRIMINAL"],
    ["NAME_LOWER", "HEALTH"],
]

NEGATIVE_GROUPS = [
    [], [], ["!PUBLIC_FIGURE"], ["!GENERIC_HEALTH"], ["!ORDER_ID"], ["!ORGANIZATION"], ["!PLACE"],
    ["!GENERIC_ROLE"], ["!GENERIC_POLITICS"], ["!CASE_NUMBER"], ["!GENERIC_RELIGION"], ["!TRACKING"],
]

SLOT_HELP = {
    "PERSON_NAME": "full name", "FIRST_NAME": "first name alone", "LAST_NAME": "last name alone",
    "NAME_LOWER": "full name written in lowercase", "EMAIL": "email address",
    "EMAIL_OBF": "email written to dodge filters (e.g. 'x at y dot com')", "PHONE": "phone number",
    "PHONE_SPELLED": "phone number spelled out in words", "SSN": "social security number",
    "SSN_LAST4": "last four digits of an SSN", "PASSPORT": "passport number",
    "DRIVER_LICENSE": "driver's license number", "CREDIT_CARD": "credit card number",
    "BANK_ACCOUNT": "IBAN bank account", "STREET_ADDRESS": "street address (number and street only)",
    "IP_ADDRESS": "IP address", "USERNAME": "account handle", "MRN": "medical record number",
    "DOB": "date of birth", "AGE": "age as a number", "ZIP_CODE": "zip code", "CITY": "city name",
    "EMPLOYER": "employer company name", "JOB_TITLE": "job title (lowercase noun phrase)",
    "HEALTH": "medical condition (noun phrase)", "MEDICATION": "medication name",
    "RELIGION": "religious identity noun without article, e.g. 'practicing Muslim' (write 'a {RELIGION}')",
    "ORIENTATION": "sexual orientation adjective, e.g. 'bisexual'",
    "POLITICAL": "complete phrase WITH its article, e.g. 'a Libertarian Party volunteer'; write 'they are {POLITICAL}', never 'a {POLITICAL}'",
    "ETHNICITY": "ethnic group adjective, e.g. 'Hmong'",
    "CRIMINAL": "complete phrase WITH its article, e.g. 'a 2019 DUI conviction'; write 'has {CRIMINAL}', never 'a {CRIMINAL}' or '{CRIMINAL} record'",
    "INDIRECT": "complete phrase WITH its article that singles out one person, e.g. 'the only nurse on the night shift'; use it where a person is the subject or object",
}
NEG_HELP = {
    "!PUBLIC_FIGURE": "a famous historical figure mentioned in their public role",
    "!ORGANIZATION": "a well-known organization", "!PLACE": "a famous landmark or natural place",
    "!GENERIC_ROLE": "a generic role such as 'a pharmacist'", "!ORDER_ID": "an order number",
    "!TRACKING": "a shipping tracking number", "!CASE_NUMBER": "a case or ticket number",
    "!GENERIC_HEALTH": "a disease discussed in general, not about a person",
    "!GENERIC_RELIGION": "a religion discussed in general", "!GENERIC_POLITICS": "a political topic in general",
}

AUTHOR_PROMPT = """Write one realistic piece of text: {kind}.

It is a TEMPLATE. Every piece of information about a specific person MUST be a placeholder in braces.
Never write a real or made-up name, contact detail, number, date of birth, or address as plain text.
Write the template so that the sentence still reads naturally once each placeholder is replaced.

Placeholders you MUST use, each at least once: {required}
Placeholders you MAY also use (persona 1): {optional}
To refer to a second person, add @2, e.g. {{PERSON_NAME@2}}.
{negatives}
Use ONLY the placeholders listed above; do not invent new ones such as {{DATE}}.
Non-personal details (event dates, amounts, product names) may be written as plain text.
Put each placeholder only where a value of its meaning fits:
{help}

Length: 2 to 6 sentences, or the natural length for the format. Use a fresh, specific scenario.
Return JSON: {{"text": "<the template>"}}"""

COHERENCE_PROMPT = """The personal values in this text (names, numbers, conditions, jobs, descriptions) were filled in
at random, so ignore whether they are realistic together (e.g. a medication that does not match the
condition, or a job that seems odd). Judge only whether each value is the right KIND of thing for its
position and the sentence stays grammatical. Answer false only for clear errors, e.g. a description of a
person used as a date, a phone number someone is asked to "bring", or doubled words like "a a".

Text:
{text}

Return JSON: {{"coherent": true or false, "problem": "<short reason, or empty>"}}"""

JUDGE_PROMPT = """Below is a text in which private details were replaced by [X].
Outside the [X] markers, does the text still contain any information that identifies or describes a
specific private individual: a personal name, contact detail, ID number, address, or a sensitive fact
about a specific person? Famous historical figures, organizations, landmarks, and generic roles do NOT count.

Text:
{text}

Return JSON: {{"leak": true or false, "evidence": "<quote, or empty>"}}"""


STREET_RE = re.compile(
    r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Place|Pl)\b"
)

NEGATIVE_ROLE_PROMPT = """In the text below, the phrase between ⟦ and ⟧ is meant to be NON-private: {meaning}.
Is that phrase, as used here, actually information about a specific private individual (for example, a
disease that a named person has, or a famous name used for a private person)? If so, it is private.

Text:
{text}

Return JSON: {{"private": true or false, "reason": "<short reason>"}}"""


def _mark_negatives(template: str, rng: random.Random) -> list[tuple[str, str]]:
    """For each negative slot, render the template with that one value wrapped in ⟦ ⟧."""
    out = []
    example = render(Template("check", "", template), rng, "check")
    for span in example.negatives:
        marked = example.text[: span.start] + "⟦" + example.text[span.start : span.end] + "⟧" + example.text[span.end :]
        out.append((span.label, marked))
    return out


def _chat(host: str, model: str, prompt: str, schema: dict) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": schema,
        "stream": False,
        "think": "low",
        "options": {"temperature": 0.9},
    }
    req = urllib.request.Request(f"{host}/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(json.loads(resp.read())["message"]["content"])


def _slot_name(m: re.Match) -> str:
    return ("!" if m.group(1) else "") + m.group(2)


def literal_text(template: str, mask: str = "") -> str:
    return SLOT_RE.sub(mask, template)


def check_syntax(template: str, required: list[str]) -> str | None:
    if "{" in literal_text(template) or "}" in literal_text(template) or re.search(r"\}@\d", template):
        return "malformed braces"
    found = list(SLOT_RE.finditer(template))
    for m in found:
        name = _slot_name(m)
        if name.startswith("!") and name[1:] not in NEGATIVES:
            return f"unknown negative {name}"
        if not name.startswith("!") and name not in SLOTS:
            return f"unknown slot {name}"
    used = {_slot_name(m) + (f"@{m.group(3)}" if m.group(3) else "") for m in found}
    missing = [r for r in required if r not in used]
    if missing:
        return f"missing {missing}"
    if sum(1 for m in found if not m.group(1)) < 2:
        return "fewer than two private slots"
    # These slots are complete noun phrases that start with an article ("a 2019 DUI conviction").
    if re.search(r"\b(?:a|an|the|no|any)\s+\{(?:POLITICAL|CRIMINAL|INDIRECT)(?:@\d+)?\}", template, re.IGNORECASE):
        return "article before a phrase slot"
    if re.search(r"\{(?:POLITICAL|CRIMINAL)(?:@\d+)?\}\s+(?:record|supporter|member|history|charge)\b", template):
        return "phrase slot used as a modifier"
    return None


def check_patterns(template: str) -> str | None:
    lit = literal_text(template, " ")
    for label, pat in PATTERNS.items():
        if pat.search(lit):
            return f"literal {label}"
    if re.search(r"\d{5,}", lit):
        return "literal long number"
    if STREET_RE.search(lit):
        return "literal street address"
    return None


def author(n: int, model: str, host: str, seed: int) -> list[dict]:
    rng = random.Random(seed)
    kept: list[dict] = []
    seen: set[str] = set()
    counts: dict[str, int] = {}
    attempt = 0
    while len(kept) < n and attempt < n * 8:
        attempt += 1
        domain, kind = rng.choice(DOMAINS)
        required = rng.choice(REQUIRED_GROUPS)
        negatives = rng.choice(NEGATIVE_GROUPS)
        optional = [s for s in SLOTS if s not in required and rng.random() < 0.25]
        neg_line = f"You MUST also include: {', '.join('{' + x + '}' for x in negatives)}\n" if negatives else ""
        help_keys = set(required) | set(optional)
        prompt = AUTHOR_PROMPT.format(
            kind=kind,
            required=", ".join("{" + r + "}" for r in required),
            optional=", ".join("{" + o + "}" for o in optional) or "(none)",
            negatives=neg_line,
            help="\n".join(f"- {{{k}}}: {SLOT_HELP[k.split('@')[0]]}" for k in sorted(help_keys))
            + "".join(f"\n- {{{k}}}: {NEG_HELP[k]}" for k in negatives),
        )
        try:
            text = _chat(host, model, prompt, {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]})["text"].strip()
        except Exception as e:  # network or JSON error: skip this attempt
            print(f"[{attempt}] error: {e}")
            continue

        reason = check_syntax(text, required + negatives) or check_patterns(text)
        key = re.sub(r"\W+", " ", literal_text(text).lower()).strip()
        if not reason and key in seen:
            reason = "duplicate"
        if not reason:
            verdict = _chat(
                host, model, JUDGE_PROMPT.format(text=literal_text(text, "[X]")),
                {"type": "object", "properties": {"leak": {"type": "boolean"}, "evidence": {"type": "string"}}, "required": ["leak", "evidence"]},
            )
            if verdict.get("leak"):
                reason = f"leak judge: {verdict.get('evidence', '')[:80]}"
        if not reason:
            sample = render(Template("check", domain, text), random.Random(attempt), "check").text
            verdict = _chat(
                host, model, COHERENCE_PROMPT.format(text=sample),
                {"type": "object", "properties": {"coherent": {"type": "boolean"}, "problem": {"type": "string"}}, "required": ["coherent", "problem"]},
            )
            if not verdict.get("coherent"):
                reason = f"coherence judge: {verdict.get('problem', '')[:80]}"
        if not reason:
            for label, marked in _mark_negatives(text, random.Random(attempt)):
                verdict = _chat(
                    host, model, NEGATIVE_ROLE_PROMPT.format(meaning=NEGATIVE_LABELS[label], text=marked),
                    {"type": "object", "properties": {"private": {"type": "boolean"}, "reason": {"type": "string"}}, "required": ["private", "reason"]},
                )
                if verdict.get("private"):
                    reason = f"negative judge ({label}): {verdict.get('reason', '')[:70]}"
                    break
        if reason:
            print(f"[{attempt}] rejected ({reason})")
            continue

        seen.add(key)
        counts[domain] = counts.get(domain, 0) + 1
        kept.append({"id": f"llm-{domain}-{counts[domain]:03d}", "domain": domain, "text": text, "source": f"ollama:{model}"})
        print(f"[{attempt}] kept {kept[-1]['id']} ({len(kept)}/{n})")
    return kept


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=160)
    ap.add_argument("--model", default="gpt-oss:20b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(LLM_TEMPLATES_PATH))
    args = ap.parse_args()
    rows = author(args.n, args.model, args.host, args.seed)
    with open(Path(args.out), "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} templates to {args.out}")


if __name__ == "__main__":
    main()
