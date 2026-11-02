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
   Leading articles ("a", "an", "the") are not part of the span.
3. Obfuscated forms ("jane at gmail dot com", spelled-out digits) carry the same label as
   the plain form.
4. A public figure is a negative only in a public-role context.

**Open question:** should a public figure's private facts (e.g. a politician's medical
record) be positive? v0 avoids generating such cases.

**Open question:** should a T3 span count as protected when the person it attaches to is
already masked? Today it does not: the span itself must be masked.

**Open question:** are case, claim, and ticket numbers private? Today they are decoys. But a
case number attached to a person's claim links back to that person, the way an MRN does.
privacy-filter flags 80% of them in v1. Options: keep them as decoys only when not tied to a
person (an order number in a log), or move person-linked ones into T1 as record identifiers.

## 3. Data

All data is synthetic and template-based ([prismark/generate](../prismark/generate)):

- Fictional value pools; numbers use reserved ranges (555-01xx phones, documentation IP
  blocks, Luhn-valid test card numbers, IBANs with valid check digits).
- Values about the same person stay consistent within an example (name, email, DOB, age).
- Gold spans are exact by construction, so no human annotation is needed.
- Tags mark difficulty: `obfuscated`, `lowercase`, `multi_person`, `form`, `structured`,
  `partial_identifier`, `long`, `generic_attribute`, `no_pii`, `llm_template`.

### Versions

| Version | Templates | Splits | Status |
|---|---|---|---|
| v0 | 18 hand-written | test (180 examples) | archived in `data/v0`; no longer reproducible from the current generator |
| v1 | 33 hand-written + 83 LLM-written | dev (195 examples, 39 templates) / test (385 examples, 77 templates) | current |

### LLM-written templates (v1)

Hand-written templates are narrow. v1 adds templates written by a local LLM
([llm_templates.py](../prismark/generate/llm_templates.py)). The key design choice: **the LLM
writes templates, not data.** Every person-specific detail must be a placeholder, which the
generator fills with fictional values. So the text gets the variety of free-form writing,
while the gold spans stay exact and no model output is ever trusted as a label.

The authoring model is gpt-oss:20b, which is not a tool under test. Using a tool under test
would bias the data toward that tool's own style.

Each template passes five checks before it is kept:

1. **Syntax**: only known placeholders, required ones present, at least two private ones,
   and no article in front of phrase placeholders ("a {POLITICAL}" would render "a a ...").
2. **Patterns**: no email, phone, card, SSN, IP, street address, or long number in the
   literal text. Literal PII would be unlabeled and would penalize tools that catch it.
3. **Leak judge**: a model call reads the literal text with placeholders masked and must find
   no private information outside them.
4. **Coherence judge**: the template is filled once; a model call checks that every value is
   the right kind of thing for its position.
5. **Negative judge**: each hard negative is marked in a filled sample; a model call checks
   it is not actually about a private person ("{FIRST_NAME} has a history of
   {!GENERIC_HEALTH}" would turn a negative into a private fact).

After the automatic checks, every template was also reviewed by hand (by Claude, reading all
of them). Of 140 authored templates, 57 were removed, almost all for a placeholder used with
the wrong meaning: a criminal record as a claim number, a person's name as a car model,
sexual orientation as a class topic. Such a template mislabels its spans, and the judges
missed these. Removed templates and reasons are kept in `llm_templates_rejected.jsonl`.
In v1 the authoring run took 368 model attempts for 140 automatic passes, and 83 survived review.

Accepted templates are committed in `llm_templates.jsonl`, so the dataset regenerates without
a model.

### Splits

Templates, not examples, are assigned to dev or test (by a hash of the template id), so no
template appears in both. Each template has its own seeded RNG, so adding a template never
changes the examples of another.

Planned: a held-out private test split, to limit tuning to the public set.

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

**Open question:** full coverage is strict for long descriptive spans. A model that masks
"arrest for shoplifting" but not "in 2021" gets no credit. Options: annotate a required
core inside each T3/T4 span, or accept a coverage threshold for those tiers.
Overlap recall is reported alongside so the size of the gap stays visible.

**Open question:** one headline number. Candidates: Privacy F1 (current), a tier-weighted
recall (T1 > T3 > T2 > T4?), or a combination of leakage and utility.

## 5. Tools under test

| Tool | Type | Status |
|---|---|---|
| Regex baseline | span | done |
| Microsoft Presidio | span | done |
| openai/privacy-filter | span (token classifier) | done |
| nvidia/gliner-pii, urchade/gliner_multi_pii-v1 | span (zero-shot, prompted with the taxonomy) | done |
| piiranha-v1 | span (token classifier) | done |
| Local LLMs via Ollama (Qwen 3.5 9B, Gemma 4 12B) | span (LLM as detector) | done |
| Claude (LLM as detector) | span | adapter written, not yet run |
| Google Cloud DLP, AWS Comprehend, Azure AI Language PII | span | planned |
| Private AI, Tonic Textual, other commercial redactors | span or text | planned |

All LLM adapters (Claude and local models) share one system prompt that includes the
taxonomy and the negative rules ([prismark/adapters/prompt.py](../prismark/adapters/prompt.py)),
so they are tested against the same boundary definition the benchmark publishes. GLiNER
models get the taxonomy labels as their entity types. Token classifiers (privacy-filter,
piiranha) run with their own fixed label sets, since they cannot be prompted.
Claude refusal fallbacks are off so results are never silently produced by a different model.

## 6. Roadmap

- v0.1: run Presidio and open-source models; publish the first leaderboard. (done)
- v0.2: LLM-written templates, dev/test splits (done); cloud DLP adapters; Claude.
- v0.3: re-identification attacks on redacted output (can a model recover the person?).
- v1: expand scope to guardrails and agent contextual privacy.
