# PrisMark design

Status: v0 draft. Sections marked **Open question** are not settled.

## 1. Scope

PrisMark evaluates tools that find and remove private information from text.

In scope for v0:

- PII detection tools (span output), e.g. Presidio, cloud DLP APIs, NER models.
- PII redaction tools (text output), e.g. anonymizers and LLM-based rewriters.
- English only.

Out of scope for v0, candidates for later versions:

- LLM guardrails that filter prompts and responses in a live conversation.
- Agent contextual privacy: whether an agent shares information with the wrong party.
- Structured-data anonymization (k-anonymity, differential privacy).
- Non-English text.

## 2. Defining the boundary

A privacy benchmark is only as useful as its definition of "private". PrisMark defines it
along two axes.

**What is private (positives).** Four tiers, ordered by how directly the text exposes a person:

| Tier | Rule | Why it matters |
|---|---|---|
| T1 Direct | The token alone points to one person. | Classic PII, regulated almost everywhere. |
| T2 Quasi | The token narrows the set of people; several together can identify one. | Sweeney showed ZIP + DOB + sex identifies most Americans. |
| T3 Sensitive | A special-category fact about an identifiable person. | Harm comes from disclosure, even if the name is already known. |
| T4 Contextual | A description, not a token, singles out a person. | Pattern-based tools cannot see it; this is where tools differ most. |

**What is not private (hard negatives).** Text that a naive tool would flag but should not:

- Public figures mentioned in their public role ("a quote by Marie Curie").
- Organizations and places not tied to a private person.
- Identifier-shaped numbers: order IDs, SKUs, tracking numbers, version strings.
- Generic roles ("a pharmacist", "the landlord").

Hard negatives make over-redaction measurable. A tool that masks everything gets perfect
recall and is useless; the negatives expose that.

### Boundary rules used for annotation

1. A T2 or T3 span is private only when it attaches to a specific person in the text.
   "Diabetes is common" has no private span; "Avery has diabetes" does.
2. A span is protected only if all of it is masked. Partial masking still counts as a miss.
3. Obfuscated forms ("jane at gmail dot com", spelled-out digits) carry the same label as
   the plain form.
4. A public figure is a negative only in a public-role context.

**Open question:** should a public figure's private facts (e.g. a politician's medical
record) be positive? v0 avoids generating such cases.

**Open question:** should a T3 span count as protected when the person it attaches to is
already masked? Today it does not: the span itself must be masked.

## 3. Data

v0 uses template-based synthetic data ([prismark/generate](../prismark/generate)):

- Templates across 9 domains: email, medical, chat, social, HR, finance, support, logs, legal.
- Fictional value pools; numbers use reserved ranges (555-01xx phones, documentation IP
  blocks, Luhn-valid test card numbers).
- Values about the same person stay consistent within an example (name, email, DOB, age).
- Gold spans are exact by construction, so no human annotation is needed.
- Tags mark difficulty: `obfuscated`, `lowercase`, `multi_person`, `form`, `structured`, `no_pii`.

Synthetic data is safe to publish and cheap to scale, but templates are narrow. Planned:

- LLM-written free-form examples, annotated by the generating model and verified by a
  second model plus human spot checks.
- A held-out private test split, to limit tuning to the public set.

## 4. Metrics

See the [README](../README.md#metrics) for definitions. Design choices:

- **Label-agnostic headline.** Every tool has its own label set. Mapping labels loses
  information and rewards matching our naming. The headline asks only whether private
  text was protected; per-label breakdowns use the gold label.
- **Full coverage.** Protected recall requires the whole span to be masked, because a
  surviving surname or the last four digits of an SSN is still a leak.
- **Two leakage measures.** Verbatim leakage catches values left whole; fragment leakage
  catches pieces of them.
- **Utility.** Word-level similarity to the gold redaction penalizes both missed spans and
  over-redaction, and works for tools that rewrite text instead of returning spans.

**Open question:** one headline number. Candidates: Privacy F1 (current), a tier-weighted
recall (T1 > T3 > T2 > T4?), or a combination of leakage and utility.

## 5. Tools under test

| Tool | Type | Status |
|---|---|---|
| Regex baseline | span | done |
| Microsoft Presidio | span | done |
| Claude (LLM as detector) | span | adapter written, not yet run |
| Google Cloud DLP, AWS Comprehend, Azure AI Language PII | span | planned |
| spaCy / GLiNER / fine-tuned NER models | span | planned |
| Private AI, Tonic Textual, other commercial redactors | span or text | planned |

The LLM adapter's system prompt includes the taxonomy and the negative rules, so it is
tested against the same boundary definition the benchmark publishes. Refusal fallbacks
are off so results are never silently produced by a different model.

## 6. Roadmap

- v0.1: run Presidio and Claude; publish the first leaderboard.
- v0.2: LLM-generated free-form data; cloud DLP adapters; latency and cost columns.
- v0.3: re-identification attacks on redacted output (can a model recover the person?).
- v1: expand scope to guardrails and agent contextual privacy.
