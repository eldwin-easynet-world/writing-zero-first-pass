from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class HandoffPlan:
    milestone: str
    inputs: list[str]
    commands: list[str]
    metrics: list[str]
    artifacts: list[str]
    failure_modes: list[str]
    compute_gate: str

    def to_jsonable(self) -> dict[str, object]:
        return asdict(self)


def build_handoff_plan() -> HandoffPlan:
    return HandoffPlan(
        milestone="replace-mock-genrm-with-agreed-public-sources",
        inputs=[
            "public writing prompts or agreed benchmark prompts",
            "rubric principles derived from the Writing-Zero paper",
            "two candidate responses per prompt from agreed source models",
            "pairwise preference labels from agreed evaluator process",
        ],
        commands=[
            "python3 -m writing_zero_pipeline.cli generate --out artifacts/samples.jsonl",
            "python3 -m writing_zero_pipeline.cli evaluate --samples artifacts/samples.jsonl --out artifacts/eval.json",
            "python3 -m unittest discover -s tests",
        ],
        metrics=[
            "pairwise label agreement",
            "mock-to-real scorer parity on seed slice",
            "GenRM validation accuracy",
            "reward hacking checks: length bias and over-explanation rate",
            "main-model win rate on held-out writing prompts",
        ],
        artifacts=[
            "artifacts/samples.jsonl",
            "artifacts/eval.json",
            "artifacts/compute_handoff.json",
            "training logs and model card for real GenRM run",
        ],
        failure_modes=[
            "rubric labels collapse to length preference",
            "candidate responses are too homogeneous for pairwise learning",
            "GenRM overfits the seed prompts",
            "main model optimizes evaluator phrasing instead of writing quality",
            "compute run lacks enough provenance to reproduce labels",
        ],
        compute_gate=(
            "Do not request paid compute until sample schema, rubric source, "
            "label provenance, and offline validation are accepted."
        ),
    )


def write_handoff_plan(path: Path) -> HandoffPlan:
    plan = build_handoff_plan()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.to_jsonable(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return plan

