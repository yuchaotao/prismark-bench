# PrisMark Bench

PrisMark is a benchmark for **privacy tools**. It has two goals:

1. **Define the privacy problem boundary.** A tiered taxonomy states which text a privacy
   tool should act on, and a set of *hard negatives* states what it should leave alone.
2. **Measure how well real tools respect that boundary.** Tools are scored on what they
   protect, what they leak, and what they destroy along the way.

The current version (v1) focuses on **PII detection and redaction in English text**, using
fully synthetic data from hand-written and LLM-written templates, with dev and test splits.
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
prismark generate                 # writes data/v1/{dev,test}.jsonl (fixed seed)
prismark run --tool regex         # dependency-free baseline
prismark report                   # leaderboard from results/v1/test/*.json
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

## Current results (v1 test: 385 examples, 77 templates, 2,120 private spans, 300 hard negatives)

Sorted by Privacy F1. Archived v0 results are in [results/v0](results/v0/test).

| Tool | Type | Protected recall ↑ | Overlap recall ↑ | Char precision ↑ | Privacy F1 ↑ | Hard-neg FP ↓ | Leakage ↓ | Fragment leakage ↓ | Utility ↑ | ms / example |
|---|---|---|---|---|---|---|---|---|---|---|
| ollama:gemma4:12b | local LLM | **0.936** | **0.956** | **0.983** | **0.959** | **0.063** | **0.044** | **0.062** | **0.972** | 1255 |
| ollama:qwen3.5:9b | local LLM | 0.873 | 0.902 | 0.952 | 0.911 | 0.163 | 0.102 | 0.140 | 0.946 | 1251 |
| gliner-nvidia | GLiNER | 0.879 | 0.943 | 0.884 | 0.882 | 0.510 | 0.059 | 0.122 | 0.927 | 30 |
| privacy-filter | token classifier | 0.669 | 0.690 | 0.846 | 0.747 | 0.507 | 0.319 | 0.343 | 0.883 | 559 |
| piiranha | token classifier | 0.563 | 0.626 | 0.904 | 0.694 | 0.397 | 0.386 | 0.438 | 0.871 | 17 |
| gliner-urchade | GLiNER | 0.577 | 0.615 | 0.845 | 0.686 | 0.350 | 0.402 | 0.455 | 0.892 | 21 |
| presidio | rules + NER | 0.565 | 0.633 | 0.730 | 0.637 | 0.557 | 0.402 | 0.481 | 0.852 | 14 |
| regex | rules | 0.144 | 0.144 | 0.903 | 0.248 | 0.150 | 0.856 | 0.864 | 0.829 | 0 |

Protected recall by tier:

| Tool | T1 Direct | T2 Quasi | T3 Sensitive | T4 Contextual |
|---|---|---|---|---|
| ollama:gemma4:12b | 0.971 | 0.918 | 0.861 | 0.160 |
| ollama:qwen3.5:9b | 0.942 | 0.792 | 0.735 | 0.000 |
| gliner-nvidia | 0.917 | 0.949 | 0.690 | 0.000 |
| privacy-filter | 0.921 | 0.328 | 0.016 | 0.000 |
| piiranha | 0.735 | 0.410 | 0.029 | 0.000 |
| gliner-urchade | 0.470 | 0.918 | 0.681 | 0.000 |
| presidio | 0.697 | 0.482 | 0.119 | 0.000 |
| regex | 0.219 | 0.000 | 0.000 | 0.000 |

Hard negatives flagged, by type:

| Tool | Decoy number | Generic attribute | Generic role | Organization | Place | Public figure |
|---|---|---|---|---|---|---|
| ollama:gemma4:12b | 3/175 | 12/40 | 0/20 | 0/20 | 4/25 | 0/20 |
| ollama:qwen3.5:9b | 27/175 | 8/40 | 0/20 | 1/20 | 5/25 | 8/20 |
| gliner-nvidia | 78/175 | 39/40 | 11/20 | 2/20 | 10/25 | 13/20 |
| privacy-filter | 140/175 | 0/40 | 0/20 | 1/20 | 0/25 | 11/20 |
| piiranha | 96/175 | 0/40 | 0/20 | 0/20 | 22/25 | 1/20 |
| gliner-urchade | 41/175 | 34/40 | 13/20 | 14/20 | 3/25 | 0/20 |
| presidio | 114/175 | 12/40 | 0/20 | 0/20 | 21/25 | 20/20 |
| regex | 45/175 | 0/40 | 0/20 | 0/20 | 0/25 | 0/20 |

Protected recall is about the same on hand-written and LLM-written templates for every tool
(e.g. gemma4 0.929 vs 0.938, gliner-nvidia 0.888 vs 0.876), so the LLM templates are not an
easier or harder subset.

Setup: one RTX 4070 Ti SUPER (16 GB), WSL2 Ubuntu 22.04. Timings are single-example, unbatched.

- presidio 2.2.365, `en_core_web_lg` 3.8.0, default recognizers, score threshold 0.35.
- privacy-filter, piiranha: transformers 5.20.2 `token-classification` pipeline, `aggregation_strategy="simple"`, no score threshold.
- gliner-nvidia, gliner-urchade: gliner 0.2.30, threshold 0.5, prompted with the PrisMark labels
  ([gliner_adapter.py](prismark/adapters/gliner_adapter.py)). gliner-urchade runs under transformers 4.57.6,
  because its mDeBERTa tokenizer fails to load under transformers 5.
- ollama models: Ollama 0.40.13, default quantization, temperature 0, thinking off, JSON-schema output,
  shared prompt ([prompt.py](prismark/adapters/prompt.py)).

Caveats: all data is synthetic. GLiNER results depend on the label wording (gliner-urchade
finds few names with the label "person name"). Token classifiers cannot be told about the
taxonomy, so they are judged on a boundary they were not trained on. Most decoy numbers are
case and claim numbers, whose status is an open question (see [docs/design.md](docs/design.md)).

## Adding a tool

Subclass `prismark.adapters.base.Adapter` and implement `detect(text) -> list[Span]`,
`redact(text) -> str`, or both; then register it in
[prismark/adapters/\_\_init\_\_.py](prismark/adapters/__init__.py).

## Repository layout

```
prismark/
  taxonomy.py         the privacy boundary: labels, tiers, hard negatives
  schema.py           Example / Span data model, JSONL I/O
  generate/           synthetic data: value pools, templates, generator, LLM template author
  adapters/           tool wrappers: regex, Presidio, HF token classifiers, GLiNER, Ollama, Claude
  metrics.py          scoring
  cli.py              `prismark generate | run | rescore | report`
data/v1/              current dev and test sets
data/v0/              archived v0 test set
results/<version>/<split>/   one JSON per tool: scores and raw predictions
docs/design.md        design rationale and roadmap
```

## License

MIT
