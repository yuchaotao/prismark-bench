"""Command line: `prismark generate | run | report`."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from prismark import adapters
from prismark.generate.generator import SPLITS, generate
from prismark.metrics import Prediction, score
from prismark.schema import Span, read_jsonl, write_jsonl

DEFAULT_DATA_DIR = "data/v1"
DEFAULT_DATA = f"{DEFAULT_DATA_DIR}/test.jsonl"
HEADLINE = [
    ("protected_recall", "Protected recall ↑"),
    ("overlap_recall", "Overlap recall ↑"),
    ("char_precision", "Char precision ↑"),
    ("privacy_f1", "Privacy F1 ↑"),
    ("negative_fp_rate", "Hard-neg FP ↓"),
    ("leakage_rate", "Leakage ↓"),
    ("fragment_leakage_rate", "Fragment leakage ↓"),
    ("utility", "Utility ↑"),
]


def results_dir(data: str) -> Path:
    """data/v1/test.jsonl -> results/v1/test"""
    p = Path(data)
    return Path("results") / p.parent.name / p.stem


def cmd_generate(args: argparse.Namespace) -> None:
    for split in SPLITS:
        examples = generate(split, n_per_template=args.n, seed=args.seed)
        out = Path(args.out_dir) / f"{split}.jsonl"
        write_jsonl(out, examples)
        print(f"wrote {len(examples)} examples ({len({e.id.rsplit('-', 1)[0] for e in examples})} templates) to {out}")


def cmd_run(args: argparse.Namespace) -> None:
    examples = list(read_jsonl(args.data))
    if args.limit:
        examples = examples[: args.limit]
    tool = adapters.load(args.tool)
    predictions = {}
    start = time.perf_counter()
    for ex in examples:
        predictions[ex.id] = tool.predict(ex.text)
    elapsed = time.perf_counter() - start

    result = {
        "tool": tool.name,
        "data": args.data,
        "seconds_per_example": elapsed / len(examples) if examples else None,
        "scores": score(examples, predictions),
        "predictions": {k: asdict(v) for k, v in predictions.items()},
    }
    for counter in ("refusals", "parse_errors"):
        if hasattr(tool, counter):
            result[counter] = getattr(tool, counter)
    out = Path(args.out) if args.out else results_dir(args.data) / f"{tool.name.replace(':', '_')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(_table([result]))
    print(f"\nsaved to {out}")


def _fmt(v: float | None) -> str:
    return "-" if v is None else f"{v:.3f}"


def _table(results: list[dict]) -> str:
    lines = ["| Tool | " + " | ".join(h for _, h in HEADLINE) + " |", "|---" * (len(HEADLINE) + 1) + "|"]
    for r in results:
        lines.append(f"| {r['tool']} | " + " | ".join(_fmt(r["scores"][k]) for k, _ in HEADLINE) + " |")
    tiers = sorted({t for r in results for t in r["scores"]["by_tier"]})
    lines += ["", "Protected recall by tier:", "", "| Tool | " + " | ".join(tiers) + " |", "|---" * (len(tiers) + 1) + "|"]
    for r in results:
        lines.append(f"| {r['tool']} | " + " | ".join(_fmt(r["scores"]["by_tier"].get(t)) for t in tiers) + " |")
    return "\n".join(lines)


def cmd_rescore(args: argparse.Namespace) -> None:
    """Recompute scores from saved predictions, e.g. after a metric or gold-span change."""
    for path in args.results or sorted(results_dir(DEFAULT_DATA).glob("*.json")):
        result = json.loads(Path(path).read_text(encoding="utf-8"))
        # Score only the examples the tool was run on (a run may have used --limit).
        examples = [ex for ex in read_jsonl(result["data"]) if ex.id in result["predictions"]]
        predictions = {
            k: Prediction(spans=[Span(**s) for s in v["spans"]], redacted=v["redacted"])
            for k, v in result["predictions"].items()
        }
        result["scores"] = score(examples, predictions)
        Path(path).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"rescored {path}")


def cmd_report(args: argparse.Namespace) -> None:
    paths = args.results or sorted(results_dir(DEFAULT_DATA).glob("*.json"))
    print(_table([json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="prismark")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="generate the synthetic dataset")
    g.add_argument("--out-dir", default=DEFAULT_DATA_DIR)
    g.add_argument("--n", type=int, default=5, help="examples per template")
    g.add_argument("--seed", type=int, default=0)
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("run", help="run a tool on the dataset and score it")
    r.add_argument("--tool", required=True, help=f"one of: {', '.join(adapters.AVAILABLE)}")
    r.add_argument("--data", default=DEFAULT_DATA)
    r.add_argument("--out")
    r.add_argument("--limit", type=int, help="only run the first N examples")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("rescore", help="recompute scores from saved predictions")
    s.add_argument("results", nargs="*")
    s.set_defaults(func=cmd_rescore)

    p = sub.add_parser("report", help="print a leaderboard from result files")
    p.add_argument("results", nargs="*")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
