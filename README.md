# PrisMark Bench

PrisMark is a benchmark for **privacy tools**. It has two goals:

1. **Define the privacy problem boundary.** A tiered taxonomy states which text a privacy
   tool should act on, and a set of *hard negatives* states what it should leave alone.
2. **Measure how well real tools respect that boundary.** Tools are scored on what they
   protect, what they leak, and what they destroy along the way.

v0 focuses on **PII detection and redaction in English text**, using fully synthetic data.
See [docs/design.md](docs/design.md) for the design and the open questions.

## The boundary at a glance

| Tier | What it covers | Examples |
|---|---|---|
| T1 Direct | Identifies a person on its own | name, email, phone, SSN, card number, address, IP, username |
| T2 Quasi | Identifies a person in combination | date of birth, age, ZIP code, city, employer, job title |
| T3 Sensitive | Special-category attribute of a person | health condition, religion, sexual orientation, politics, ethnicity, criminal record |
| T4 Contextual | Identifies a person by description | "the only pediatric neurosurgeon at Riverside General" |
| Hard negatives | Looks like PII, is not | public figures in a public role, organizations, places, order IDs / SKUs / versions |

Full definitions live in [prismark/taxonomy.py](prismark/taxonomy.py).

## Quick start

```bash
pip install -e ".[dev]"
prismark generate                 # writes data/v0/test.jsonl (fixed seed)
prismark run --tool regex         # dependency-free baseline
prismark report                   # leaderboard from results/*.json
```

Other tools:

```bash
pip install -e ".[presidio]" && python -m spacy download en_core_web_lg
prismark run --tool presidio

pip install -e ".[llm]"           # needs ANTHROPIC_API_KEY or `ant auth login`
prismark run --tool claude                       # default model
prismark run --tool claude:claude-haiku-5-5      # any model id
```

## Metrics

| Metric | Meaning |
|---|---|
| Protected recall ↑ | Share of private spans fully covered by the tool. Masking only the first name of "Avery Okafor" does not count. |
| Char precision ↑ | Share of masked characters that were actually private. |
| Privacy F1 ↑ | Harmonic mean of the two above. |
| Hard-neg FP ↓ | Share of hard negatives the tool flagged (over-redaction). |
| Leakage ↓ | Share of private values still present verbatim (or reformatted) in the output. |
| Fragment leakage ↓ | Share of private values with any distinctive word left in the output. |
| Utility ↑ | Word-level similarity between the tool's output and the gold redaction. |

Scores are also broken down by tier, by label, and by tag (`obfuscated`, `lowercase`, `multi_person`, ...).

## Current results (v0 data, 180 examples)

| Tool | Protected recall ↑ | Char precision ↑ | Privacy F1 ↑ | Hard-neg FP ↓ | Leakage ↓ | Fragment leakage ↓ | Utility ↑ |
|---|---|---|---|---|---|---|---|
| regex | 0.145 | 0.807 | 0.246 | 0.143 | 0.855 | 0.862 | 0.766 |

## Adding a tool

Subclass `prismark.adapters.base.Adapter` and implement `detect(text) -> list[Span]`,
`redact(text) -> str`, or both; then register it in
[prismark/adapters/\_\_init\_\_.py](prismark/adapters/__init__.py).

## Repository layout

```
prismark/
  taxonomy.py         the privacy boundary: labels, tiers, hard negatives
  schema.py           Example / Span data model, JSONL I/O
  generate/           synthetic data: value pools, templates, generator
  adapters/           tool wrappers: regex baseline, Presidio, Claude
  metrics.py          scoring
  cli.py              `prismark generate | run | report`
data/v0/test.jsonl    the generated v0 test set
docs/design.md        design rationale and roadmap
```

## License

MIT
