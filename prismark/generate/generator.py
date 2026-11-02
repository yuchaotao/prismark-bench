"""Template-based synthetic data generator.

Templates contain slots in braces:

* ``{SLOT}``     - a value for persona 1 (labels in ``SLOTS`` below).
* ``{SLOT@2}``   - the same slot for persona 2.
* ``{!NEG}``     - a hard negative (``NEGATIVES`` below).

Each example draws fresh personas, so values that refer to one person
(name, email, username, DOB, age) stay consistent within the example.
Offsets are tracked while filling, so gold spans are exact by construction.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import date
from typing import Callable

from prismark.generate import pools
from prismark.generate.templates import TEMPLATES, Template
from prismark.schema import Example, Span

REFERENCE_DATE = date(2026, 1, 1)

SLOT_RE = re.compile(r"\{(!?)([A-Z_]+)(?:@(\d+))?\}")


@dataclass
class Persona:
    first: str
    last: str
    dob: date
    city: tuple[str, str, str]
    rng: random.Random

    @property
    def age(self) -> int:
        years = REFERENCE_DATE.year - self.dob.year
        return years - ((REFERENCE_DATE.month, REFERENCE_DATE.day) < (self.dob.month, self.dob.day))


def _new_persona(rng: random.Random) -> Persona:
    dob = date(rng.randint(1950, 2004), rng.randint(1, 12), rng.randint(1, 28))
    return Persona(rng.choice(pools.FIRST_NAMES), rng.choice(pools.LAST_NAMES), dob, rng.choice(pools.CITIES), rng)


def _digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _luhn_complete(prefix: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(prefix)):
        d = int(ch)
        if i % 2 == 0:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
    return prefix + str((10 - total % 10) % 10)


def _email_local(p: Persona) -> str:
    return p.rng.choice([f"{p.first}.{p.last}", f"{p.first[0]}{p.last}", f"{p.first}{p.dob.year % 100:02d}"]).lower()


def _email(p: Persona) -> tuple[str, list[str]]:
    return f"{_email_local(p)}@{p.rng.choice(pools.EMAIL_DOMAINS)}", []


def _email_obfuscated(p: Persona) -> tuple[str, list[str]]:
    user, domain = _email_local(p), p.rng.choice(pools.EMAIL_DOMAINS)
    name, tld = domain.rsplit(".", 1)
    return p.rng.choice([f"{user} at {name} dot {tld}", f"{user} [at] {domain}", f"{user}(at){name}(dot){tld}"]), [
        "obfuscated"
    ]


def _phone(p: Persona) -> tuple[str, list[str]]:
    area, line = p.rng.randint(201, 989), f"01{p.rng.randint(0, 99):02d}"
    return p.rng.choice([f"({area}) 555-{line}", f"{area}-555-{line}", f"+1 {area} 555 {line}", f"{area}.555.{line}"]), []


def _phone_spelled(p: Persona) -> tuple[str, list[str]]:
    words = "zero one two three four five six seven eight nine".split()
    digits = f"{p.rng.randint(201, 989)}55501{p.rng.randint(0, 99):02d}"
    return " ".join(words[int(d)] for d in digits), ["obfuscated"]


def _ssn(p: Persona) -> tuple[str, list[str]]:
    area = p.rng.choice([n for n in range(100, 900) if n != 666])
    s = f"{area:03d}{p.rng.randint(10, 99)}{p.rng.randint(1000, 9999)}"
    return p.rng.choice([f"{s[:3]}-{s[3:5]}-{s[5:]}", f"{s[:3]} {s[3:5]} {s[5:]}", s]), []


def _credit_card(p: Persona) -> tuple[str, list[str]]:
    num = _luhn_complete("4" + _digits(p.rng, 14))
    return p.rng.choice([" ".join(num[i : i + 4] for i in range(0, 16, 4)), "-".join(num[i : i + 4] for i in range(0, 16, 4)), num]), []


def _iban(p: Persona) -> tuple[str, list[str]]:
    return f"DE{_digits(p.rng, 2)} {_digits(p.rng, 4)} {_digits(p.rng, 4)} {_digits(p.rng, 4)} {_digits(p.rng, 4)} {_digits(p.rng, 2)}", []


def _address(p: Persona) -> tuple[str, list[str]]:
    return f"{p.rng.randint(12, 9870)} {p.rng.choice(pools.STREETS)}", []


def _ip(p: Persona) -> tuple[str, list[str]]:
    block = p.rng.choice(["192.0.2", "198.51.100", "203.0.113"])
    return f"{block}.{p.rng.randint(1, 254)}", []


def _username(p: Persona) -> tuple[str, list[str]]:
    return p.rng.choice([f"{p.first.lower()}_{p.last.lower()[:4]}", f"{p.last.lower()}{p.rng.randint(1, 99)}", f"@{p.first.lower()}{p.dob.year}"]), []


def _dob(p: Persona) -> tuple[str, list[str]]:
    d = p.dob
    return p.rng.choice([d.strftime("%m/%d/%Y"), d.strftime("%B %d, %Y").replace(" 0", " "), d.isoformat()]), []


def _const(fn: Callable[[Persona], str], tags: list[str] | None = None) -> Callable[[Persona], tuple[str, list[str]]]:
    return lambda p: (fn(p), list(tags or []))


def _pick(pool: list[str]) -> Callable[[Persona], tuple[str, list[str]]]:
    return lambda p: (p.rng.choice(pool), [])


# slot name -> (taxonomy label, filler)
SLOTS: dict[str, tuple[str, Callable[[Persona], tuple[str, list[str]]]]] = {
    "PERSON_NAME": ("PERSON_NAME", _const(lambda p: f"{p.first} {p.last}")),
    "FIRST_NAME": ("PERSON_NAME", _const(lambda p: p.first)),
    "LAST_NAME": ("PERSON_NAME", _const(lambda p: p.last)),
    "NAME_LOWER": ("PERSON_NAME", _const(lambda p: f"{p.first} {p.last}".lower(), ["lowercase"])),
    "EMAIL": ("EMAIL", _email),
    "EMAIL_OBF": ("EMAIL", _email_obfuscated),
    "PHONE": ("PHONE", _phone),
    "PHONE_SPELLED": ("PHONE", _phone_spelled),
    "SSN": ("SSN", _ssn),
    "PASSPORT": ("PASSPORT", _const(lambda p: f"{p.rng.choice('ACEX')}{_digits(p.rng, 8)}")),
    "DRIVER_LICENSE": ("DRIVER_LICENSE", _const(lambda p: f"{p.last[0]}{_digits(p.rng, 3)}-{_digits(p.rng, 4)}-{_digits(p.rng, 4)}")),
    "CREDIT_CARD": ("CREDIT_CARD", _credit_card),
    "BANK_ACCOUNT": ("BANK_ACCOUNT", _iban),
    "STREET_ADDRESS": ("STREET_ADDRESS", _address),
    "IP_ADDRESS": ("IP_ADDRESS", _ip),
    "USERNAME": ("USERNAME", _username),
    "MRN": ("MEDICAL_RECORD_NUMBER", _const(lambda p: f"MRN-{_digits(p.rng, 7)}")),
    "DOB": ("DATE_OF_BIRTH", _dob),
    "AGE": ("AGE", _const(lambda p: str(p.age))),
    "ZIP_CODE": ("ZIP_CODE", _const(lambda p: f"{p.city[2]}{_digits(p.rng, 2)}")),
    "CITY": ("CITY", _const(lambda p: p.city[0])),
    "EMPLOYER": ("EMPLOYER", _pick(pools.EMPLOYERS)),
    "JOB_TITLE": ("JOB_TITLE", _pick(pools.JOB_TITLES)),
    "HEALTH": ("HEALTH_CONDITION", _pick(pools.HEALTH_CONDITIONS)),
    "MEDICATION": ("HEALTH_CONDITION", _pick(pools.MEDICATIONS)),
    "RELIGION": ("RELIGION", _pick(pools.RELIGIONS)),
    "ORIENTATION": ("SEXUAL_ORIENTATION", _pick(pools.ORIENTATIONS)),
    "POLITICAL": ("POLITICAL_AFFILIATION", _pick(pools.POLITICAL)),
    "ETHNICITY": ("ETHNICITY", _pick(pools.ETHNICITIES)),
    "CRIMINAL": ("CRIMINAL_RECORD", _pick(pools.CRIMINAL)),
    "INDIRECT": ("INDIRECT_IDENTIFIER", _pick(pools.INDIRECT)),
}

# negative slot name -> (negative label, filler)
NEGATIVES: dict[str, tuple[str, Callable[[random.Random], str]]] = {
    "PUBLIC_FIGURE": ("PUBLIC_FIGURE", lambda r: r.choice(pools.PUBLIC_FIGURES)),
    "ORGANIZATION": ("ORGANIZATION", lambda r: r.choice(pools.ORGANIZATIONS)),
    "PLACE": ("PLACE", lambda r: r.choice(pools.PLACES)),
    "GENERIC_ROLE": ("GENERIC_ROLE", lambda r: r.choice(pools.GENERIC_ROLES)),
    "ORDER_ID": ("DECOY_NUMBER", lambda r: f"{r.randint(100, 999)}-{r.randint(100, 999)}-{r.randint(1000, 9999)}"),
    "SKU": ("DECOY_NUMBER", lambda r: f"SKU-{_digits(r, 9)}"),
    "VERSION": ("DECOY_NUMBER", lambda r: f"{r.randint(1, 20)}.{r.randint(0, 99)}.{r.randint(0, 999)}"),
    "TRACKING": ("DECOY_NUMBER", lambda r: f"1Z{_digits(r, 16)}"),
}


def render(template: Template, rng: random.Random, example_id: str) -> Example:
    personas: dict[str, Persona] = {}
    # Within one example, a slot for the same persona always yields the same value.
    cache: dict[tuple[str, str], tuple[str, list[str]]] = {}
    out: list[str] = []
    spans: list[Span] = []
    negatives: list[Span] = []
    tags: set[str] = set(template.tags)
    pos = 0
    cursor = 0

    for m in SLOT_RE.finditer(template.text):
        literal = template.text[cursor : m.start()]
        out.append(literal)
        pos += len(literal)
        cursor = m.end()
        is_negative, slot, pid = m.group(1) == "!", m.group(2), m.group(3) or "1"

        if is_negative:
            label, neg_fill = NEGATIVES[slot]
            value = neg_fill(rng)
            negatives.append(Span(pos, pos + len(value), label))
            tags.add("hard_negative")
        else:
            label, fill = SLOTS[slot]
            persona = personas.setdefault(pid, _new_persona(rng))
            if (slot, pid) not in cache:
                cache[(slot, pid)] = fill(persona)
            value, slot_tags = cache[(slot, pid)]
            spans.append(Span(pos, pos + len(value), label))
            tags.update(slot_tags)

        out.append(value)
        pos += len(value)

    out.append(template.text[cursor:])
    return Example(
        id=example_id,
        text="".join(out),
        spans=spans,
        negatives=negatives,
        domain=template.domain,
        tags=sorted(tags),
    )


def generate(n_per_template: int = 10, seed: int = 0) -> list[Example]:
    rng = random.Random(seed)
    examples = []
    for t in TEMPLATES:
        for i in range(n_per_template):
            examples.append(render(t, rng, f"{t.id}-{i:03d}"))
    return examples
