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

pip install -e ".[hf]"            # open-source PII models (GPU recommended)
prismark run --tool privacy-filter               # openai/privacy-filter
prismark run --tool gliner-nvidia                # nvidia/gliner-pii
prismark run --tool gliner-urchade               # urchade/gliner_multi_pii-v1
prismark run --tool piiranha                     # iiiorg/piiranha-v1-detect-personal-information

ollama pull qwen3.5:9b            # local LLMs via a running Ollama server
prismark run --tool ollama:qwen3.5:9b

pip install -e ".[llm]"           # needs ANTHROPIC_API_KEY or `ant auth login`
prismark run --tool claude                       # default model
prismark run --tool claude:claude-haiku-5-5      # any model id
```

## Metrics

| Metric | Meaning |
|---|---|
| Protected recall ↑ | Share of private spans fully covered by the tool. Masking only the first name of "Avery Okafor" does not count. |
| Overlap recall ↑ | Share of private spans the tool touched at all. The gap to protected recall is the cost of partial masking. |
| Char precision ↑ | Share of masked characters that were actually private. |
| Privacy F1 ↑ | Harmonic mean of the two above. |
| Hard-neg FP ↓ | Share of hard negatives the tool flagged (over-redaction). |
| Leakage ↓ | Share of private values still present verbatim (or reformatted) in the output. |
| Fragment leakage ↓ | Share of private values with any distinctive word left in the output. |
| Utility ↑ | Word-level similarity between the tool's output and the gold redaction. |

Scores are also broken down by tier, by label, and by tag (`obfuscated`, `lowercase`, `multi_person`, ...).

## Current results (v0 data, 180 examples)

Sorted by Privacy F1.

| Tool | Type | Protected recall ↑ | Overlap recall ↑ | Char precision ↑ | Privacy F1 ↑ | Hard-neg FP ↓ | Leakage ↓ | Fragment leakage ↓ | Utility ↑ | ms / example |
|---|---|---|---|---|---|---|---|---|---|---|
| ollama:gemma4:12b | local LLM | 0.920 | 0.986 | 0.974 | **0.946** | **0.043** | **0.014** | **0.068** | **0.969** | 1075 |
| gliner-nvidia | GLiNER | 0.883 | 0.977 | 0.880 | 0.881 | 0.381 | 0.023 | 0.101 | 0.925 | 36 |
| ollama:qwen3.5:9b | local LLM | 0.823 | 0.888 | 0.941 | 0.878 | 0.129 | 0.112 | 0.186 | 0.929 | 973 |
| gliner-urchade | GLiNER | 0.668 | 0.712 | 0.841 | 0.745 | 0.252 | 0.290 | 0.341 | 0.873 | 46 |
| privacy-filter | token classifier | 0.649 | 0.667 | 0.788 | 0.712 | 0.319 | 0.336 | 0.359 | 0.822 | 533 |
| piiranha | token classifier | 0.567 | 0.630 | 0.868 | 0.686 | 0.281 | 0.371 | 0.409 | 0.819 | 17 |
| presidio | rules + NER | 0.596 | 0.684 | 0.691 | 0.640 | 0.357 | 0.328 | 0.410 | 0.794 | 9 |
| regex | rules | 0.136 | 0.136 | 0.800 | 0.233 | 0.143 | 0.864 | 0.870 | 0.772 | 0 |

Protected recall by tier:

| Tool | T1 Direct | T2 Quasi | T3 Sensitive | T4 Contextual |
|---|---|---|---|---|
| ollama:gemma4:12b | 0.976 | 0.969 | 0.691 | 0.400 |
| gliner-nvidia | 0.937 | 0.963 | 0.645 | 0.000 |
| ollama:qwen3.5:9b | 0.893 | 0.838 | 0.618 | 0.000 |
| gliner-urchade | 0.541 | 0.969 | 0.764 | 0.000 |
| privacy-filter | 0.905 | 0.481 | 0.000 | 0.000 |
| piiranha | 0.759 | 0.500 | 0.000 | 0.000 |
| presidio | 0.739 | 0.562 | 0.164 | 0.000 |
| regex | 0.229 | 0.000 | 0.000 | 0.000 |

Setup: one RTX 4070 Ti SUPER (16 GB), WSL2 Ubuntu 22.04. Timings are single-example, unbatched.

- presidio 2.2.365, `en_core_web_lg` 3.8.0, default recognizers, score threshold 0.35.
- privacy-filter, piiranha: transformers 5.20.2 `token-classification` pipeline, `aggregation_strategy="simple"`, no score threshold.
- gliner-nvidia, gliner-urchade: gliner 0.2.30, threshold 0.5, prompted with the PrisMark labels
  ([gliner_adapter.py](prismark/adapters/gliner_adapter.py)). gliner-urchade runs under transformers 4.57.6,
  because its mDeBERTa tokenizer fails to load under transformers 5.
- ollama models: Ollama 0.40.13, default quantization, temperature 0, thinking off, JSON-schema output,
  shared prompt ([prompt.py](prismark/adapters/prompt.py)).

Caveats: v0 data is template-based and small. GLiNER results depend on the label wording
(gliner-urchade finds only 17% of names with the label "person name"). Token classifiers
cannot be told about the taxonomy, so they are judged on a boundary they were not trained on.

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
