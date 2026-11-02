"""Templates for the synthetic dataset. See generator.py for the slot syntax.

Hand-written templates live in this file. LLM-written templates live in
llm_templates.jsonl, produced by llm_templates.py and committed, so the
dataset can be regenerated without running a model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

LLM_TEMPLATES_PATH = Path(__file__).with_name("llm_templates.jsonl")


@dataclass(frozen=True)
class Template:
    id: str
    domain: str
    text: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    source: str = "hand"


def load_llm_templates(path: Path = LLM_TEMPLATES_PATH) -> list[Template]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return [Template(r["id"], r["domain"], r["text"], tuple(r.get("tags", [])) + ("llm_template",), r["source"]) for r in rows]


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
    # --- added in v1: boundary cases ---------------------------------------
    Template(
        "medical-bulletin", "medical",
        "Public health bulletin: cases of {!GENERIC_HEALTH} rose 12% this year near {!PLACE}. "
        "{!ORGANIZATION} recommends that {!GENERIC_ROLE} offer free screening.",
        ("no_pii", "generic_attribute"),
    ),
    Template(
        "support-group", "medical",
        "Our support group discusses {!GENERIC_HEALTH} every Tuesday. This week {FIRST_NAME} shared that "
        "they were diagnosed with {HEALTH} last spring and now take {MEDICATION}.",
        ("generic_attribute",),
    ),
    Template(
        "hr-policy", "hr",
        "Policy reminder: employees who observe {!GENERIC_RELIGION} holidays may request leave through "
        "{!GENERIC_ROLE}. Requests are confidential.",
        ("no_pii", "generic_attribute"),
    ),
    Template(
        "hr-religion", "hr",
        "{PERSON_NAME} asked for Fridays off because they are a {RELIGION}. Their manager, {PERSON_NAME@2}, "
        "said the team should be told it is for a medical appointment.",
        ("multi_person",),
    ),
    Template(
        "board-politics", "email",
        "Please don't bring up the election with {PERSON_NAME} at the {EMPLOYER} board dinner - they are "
        "{POLITICAL} and the donors would not take it well.",
    ),
    Template(
        "debate-notes", "social",
        "Tonight's debate covered {!GENERIC_POLITICS}, housing costs, and a long quote from {!PUBLIC_FIGURE}.",
        ("no_pii", "generic_attribute"),
    ),
    Template(
        "gossip-indirect", "chat",
        "Keep this between us: {INDIRECT} was just diagnosed with {HEALTH}.",
    ),
    Template(
        "review-indirect", "support",
        "Store feedback: {INDIRECT} was rude to customers again on Saturday. Order {!ORDER_ID} was refunded.",
    ),
    Template(
        "intern-hero", "chat",
        "Our new intern {PERSON_NAME} says {!PUBLIC_FIGURE} is their hero and wants to study at {!ORGANIZATION}.",
    ),
    Template(
        "call-transcript", "support",
        "Agent: For verification, can I get the last four of your social?\nCaller: Sure, it's {SSN_LAST4}.\n"
        "Agent: Thanks, {FIRST_NAME}. I see a case number {!CASE_NUMBER} on your account.",
        ("partial_identifier",),
    ),
    Template(
        "config-file", "code",
        "# deploy.env\nDB_USER={USERNAME}\nADMIN_EMAIL={EMAIL}\nADMIN_PHONE={PHONE}\nAPP_VERSION={!VERSION}\n"
        "ALLOWED_IP={IP_ADDRESS}",
        ("structured",),
    ),
    Template(
        "csv-export", "code",
        "patient_id,name,dob,zip,diagnosis\n{MRN},{PERSON_NAME},{DOB},{ZIP_CODE},{HEALTH}\n"
        "{MRN@2},{PERSON_NAME@2},{DOB@2},{ZIP_CODE@2},{HEALTH@2}",
        ("structured", "multi_person"),
    ),
    Template(
        "insurance-claim", "finance",
        "Claim summary\n\nThe claimant, {PERSON_NAME}, a {AGE}-year-old {JOB_TITLE} at {EMPLOYER}, reported "
        "water damage at {STREET_ADDRESS}, {CITY} {ZIP_CODE} on March 3. The adjuster noted that the claimant "
        "had {CRIMINAL}, which does not affect eligibility. Reimbursement will go to account {BANK_ACCOUNT}. "
        "Questions can be sent to {EMAIL} or {PHONE}. Reference: {!CASE_NUMBER}.",
        ("long",),
    ),
    Template(
        "dating-profile", "social",
        "{FIRST_NAME}, {AGE}, {CITY}. {ORIENTATION} {ETHNICITY} {JOB_TITLE} who loves hiking near {!PLACE}. "
        "Message me at {USERNAME}.",
    ),
    Template(
        "moving-story", "social",
        "I moved into {STREET_ADDRESS} after my divorce. My neighbor {NAME_LOWER} keeps asking about my "
        "{HEALTH} treatment, which is none of their business.",
        ("lowercase",),
    ),
]
