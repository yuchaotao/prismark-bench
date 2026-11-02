"""Templates for the synthetic dataset. See generator.py for the slot syntax."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Template:
    id: str
    domain: str
    text: str
    tags: tuple[str, ...] = field(default_factory=tuple)


TEMPLATES: list[Template] = [
    # --- email ------------------------------------------------------------
    Template(
        "email-intro", "email",
        "Hi team,\n\nPlease welcome {PERSON_NAME}, our new {JOB_TITLE}. You can reach {FIRST_NAME} at "
        "{EMAIL} or {PHONE}. {FIRST_NAME} is relocating from {CITY} next week.\n\nThanks,\n{PERSON_NAME@2}",
        ("multi_person",),
    ),
    Template(
        "email-obfuscated", "email",
        "hey, it's {FIRST_NAME}. my new address is {EMAIL_OBF} - don't post it anywhere public. "
        "or just call me: {PHONE_SPELLED}.",
    ),
    Template(
        "email-payment", "email",
        "Dear {PERSON_NAME},\n\nWe could not process order {!ORDER_ID}. The card on file, "
        "{CREDIT_CARD}, was declined. Your package tracking number {!TRACKING} is on hold.\n\n"
        "Customer Care, {!ORGANIZATION}",
    ),
    # --- medical -----------------------------------------------------------
    Template(
        "medical-note", "medical",
        "Patient: {PERSON_NAME} ({MRN}), DOB {DOB}, {AGE}-year-old {JOB_TITLE}.\n"
        "Assessment: {HEALTH}. Continue {MEDICATION}. Follow up in 6 weeks. "
        "Emergency contact: {PERSON_NAME@2}, {PHONE@2}.",
        ("multi_person",),
    ),
    Template(
        "medical-referral", "medical",
        "Referring {FIRST_NAME} {LAST_NAME} to psychiatry. Pt reports history of {HEALTH} and "
        "{CRIMINAL}. Lives at {STREET_ADDRESS}, {CITY} {ZIP_CODE}. Insurance verified by {!GENERIC_ROLE}.",
    ),
    Template(
        "medical-public", "medical",
        "Lecture notes: {!PUBLIC_FIGURE} is often cited in discussions of scientific ethics. "
        "{!ORGANIZATION} published new guidance on vaccine storage, and {!GENERIC_ROLE} should review it.",
        ("no_pii",),
    ),
    # --- chat / social ------------------------------------------------------
    Template(
        "chat-coming-out", "chat",
        "[{USERNAME}] honestly I haven't told anyone at {EMPLOYER} that I'm {ORIENTATION}\n"
        "[{USERNAME@2}] your secret is safe with me {FIRST_NAME}",
        ("multi_person",),
    ),
    Template(
        "chat-faith", "chat",
        "{FIRST_NAME} can't come to the Friday lunch - they're a {RELIGION} and it's during prayer. "
        "Also they're {POLITICAL}, so maybe skip the election talk.",
    ),
    Template(
        "chat-indirect", "chat",
        "Guess who got arrested last night - {INDIRECT}! Apparently it was {CRIMINAL}.",
    ),
    Template(
        "chat-lowercase", "chat",
        "lol {NAME_LOWER} just texted me from {PHONE}, says they're at {!PLACE} with {!PUBLIC_FIGURE}'s biography",
    ),
    Template(
        "social-public", "social",
        "Visited {!PLACE} this weekend and read a quote by {!PUBLIC_FIGURE} on the visitor center wall. "
        "Shoutout to {!ORGANIZATION} for keeping it open.",
        ("no_pii",),
    ),
    # --- HR / finance --------------------------------------------------------
    Template(
        "hr-onboarding", "hr",
        "New hire form\nName: {PERSON_NAME}\nSSN: {SSN}\nDate of birth: {DOB}\nHome address: "
        "{STREET_ADDRESS}, {CITY} {ZIP_CODE}\nDirect deposit IBAN: {BANK_ACCOUNT}\nPassport: {PASSPORT}",
        ("form",),
    ),
    Template(
        "hr-complaint", "hr",
        "Confidential: {PERSON_NAME} ({JOB_TITLE}) reported that a coworker mocked their {ETHNICITY} "
        "heritage and disclosed their {HEALTH} diagnosis to the team. Escalated to {!GENERIC_ROLE}.",
    ),
    Template(
        "finance-kyc", "finance",
        "KYC check failed for applicant {PERSON_NAME}: driver's license {DRIVER_LICENSE} does not match "
        "SSN {SSN}. Applicant age {AGE}, employer {EMPLOYER}.",
        ("form",),
    ),
    # --- support / logs ------------------------------------------------------
    Template(
        "support-ticket", "support",
        "Ticket #{!ORDER_ID}: User {USERNAME} ({EMAIL}) cannot log in after upgrading to v{!VERSION}. "
        "Last login from {IP_ADDRESS}. Ordered item {!SKU}.",
    ),
    Template(
        "log-auth", "log",
        "2026-03-14T08:22:51Z WARN auth failed user={USERNAME} src_ip={IP_ADDRESS} "
        "client=app/{!VERSION} reason=bad_password",
        ("structured",),
    ),
    Template(
        "log-decoys", "log",
        "2026-03-14T08:22:51Z INFO shipment={!TRACKING} order={!ORDER_ID} sku={!SKU} build={!VERSION}",
        ("structured", "no_pii"),
    ),
    # --- legal ---------------------------------------------------------------
    Template(
        "legal-affidavit", "legal",
        "I, {PERSON_NAME}, residing at {STREET_ADDRESS}, {CITY}, being {AGE} years of age, state that "
        "{PERSON_NAME@2} has {CRIMINAL} and should not have custody.",
        ("multi_person",),
    ),
]
