"""The PrisMark privacy taxonomy.

The taxonomy is the benchmark's definition of the privacy problem boundary:
which spans of text a privacy tool *should* act on, and which it should leave
alone. Every label belongs to a tier that reflects how directly it exposes a
person:

* Tier 1 (DIRECT)     - identifies a person on its own.
* Tier 2 (QUASI)      - identifies a person only in combination with others.
* Tier 3 (SENSITIVE)  - a special-category attribute about an identifiable person.
* Tier 4 (CONTEXTUAL) - identifies a person through description, not a token.

Hard negatives (``NEGATIVE_LABELS``) mark text that looks like PII but falls
outside the boundary. Flagging them counts as over-redaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Tier(IntEnum):
    DIRECT = 1
    QUASI = 2
    SENSITIVE = 3
    CONTEXTUAL = 4


@dataclass(frozen=True)
class Label:
    name: str
    tier: Tier
    description: str


LABELS: dict[str, Label] = {
    label.name: label
    for label in [
        # Tier 1: direct identifiers
        Label("PERSON_NAME", Tier.DIRECT, "Full or partial name of a private individual."),
        Label("EMAIL", Tier.DIRECT, "Personal email address, including obfuscated forms."),
        Label("PHONE", Tier.DIRECT, "Phone or fax number."),
        Label("SSN", Tier.DIRECT, "US Social Security Number."),
        Label("PASSPORT", Tier.DIRECT, "Passport number."),
        Label("DRIVER_LICENSE", Tier.DIRECT, "Driver's license number."),
        Label("CREDIT_CARD", Tier.DIRECT, "Payment card number."),
        Label("BANK_ACCOUNT", Tier.DIRECT, "Bank account number or IBAN."),
        Label("STREET_ADDRESS", Tier.DIRECT, "Street-level postal address."),
        Label("IP_ADDRESS", Tier.DIRECT, "IPv4 or IPv6 address tied to a person or device."),
        Label("USERNAME", Tier.DIRECT, "Account handle or login name."),
        Label("MEDICAL_RECORD_NUMBER", Tier.DIRECT, "Medical record or patient ID."),
        # Tier 2: quasi-identifiers
        Label("DATE_OF_BIRTH", Tier.QUASI, "Date of birth."),
        Label("AGE", Tier.QUASI, "Age of a specific person."),
        Label("ZIP_CODE", Tier.QUASI, "Postal code."),
        Label("CITY", Tier.QUASI, "City of residence or work of a specific person."),
        Label("EMPLOYER", Tier.QUASI, "Employer of a specific person."),
        Label("JOB_TITLE", Tier.QUASI, "Job title of a specific person."),
        # Tier 3: sensitive attributes (GDPR Art. 9 style special categories)
        Label("HEALTH_CONDITION", Tier.SENSITIVE, "Diagnosis, condition, medication, or treatment."),
        Label("RELIGION", Tier.SENSITIVE, "Religious belief or affiliation."),
        Label("SEXUAL_ORIENTATION", Tier.SENSITIVE, "Sexual orientation."),
        Label("POLITICAL_AFFILIATION", Tier.SENSITIVE, "Political opinion or party membership."),
        Label("ETHNICITY", Tier.SENSITIVE, "Racial or ethnic origin."),
        Label("CRIMINAL_RECORD", Tier.SENSITIVE, "Arrests, convictions, or offences."),
        # Tier 4: contextual identifiers
        Label("INDIRECT_IDENTIFIER", Tier.CONTEXTUAL, "A description that singles out one person."),
    ]
}

# Text that resembles PII but is outside the privacy boundary.
NEGATIVE_LABELS: dict[str, str] = {
    "PUBLIC_FIGURE": "A well-known person mentioned in their public role.",
    "ORGANIZATION": "An organization that is not tied to a specific private person.",
    "DECOY_NUMBER": "An order ID, SKU, version, or other number shaped like an identifier.",
    "GENERIC_ROLE": "A role or title that does not single out anyone.",
    "PLACE": "A place name that is not a person's location.",
    "GENERIC_ATTRIBUTE": "A sensitive topic (health, religion, politics) discussed without attaching it to a person.",
}


def tier_of(label: str) -> Tier:
    return LABELS[label].tier
