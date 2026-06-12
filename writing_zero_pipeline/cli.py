from __future__ import annotations

import argparse
from pathlib import Path

from .genrm import evaluate_samples, write_eval
from .handoff import write_handoff_plan
from .sample_generator import generate_samples, read_jsonl, write_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Writing-Zero first-pass pipeline")
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate = subcommands.add_parser("generate", help="Generate deterministic pairwise samples")
    generate.add_argument("--out", default="artifacts/samples.jsonl", help="Output JSONL path")

    evaluate = subcommands.add_parser("evaluate", help="Evaluate samples with mock GenRM scorer")
    evaluate.add_argument("--samples", default="artifacts/samples.jsonl", help="Input JSONL path")
    evaluate.add_argument("--out", default="artifacts/eval.json", help="Output JSON path")

    handoff = subcommands.add_parser("handoff", help="Write compute handoff plan")
    handoff.add_argument("--out", default="artifacts/compute_handoff.json", help="Output JSON path")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        samples = generate_samples()
        write_jsonl(samples, Path(args.out))
        print(f"wrote {len(samples)} samples to {args.out}")
        return 0
    if args.command == "evaluate":
        samples = read_jsonl(Path(args.samples))
        result = evaluate_samples(samples)
        write_eval(result, Path(args.out))
        print(f"accuracy={result.accuracy:.3f} samples={result.sample_count} out={args.out}")
        return 0
    if args.command == "handoff":
        plan = write_handoff_plan(Path(args.out))
        print(f"milestone={plan.milestone} out={args.out}")
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
