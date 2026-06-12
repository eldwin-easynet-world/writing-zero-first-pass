from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .genrm import score_response
from .rubrics import DEFAULT_RUBRICS
from .schemas import PairwiseSample, Rubric


DEFAULT_PROMPTS = (
    "Explain why reproducible evaluation matters for AI training.",
    "Write a concise critique of a rushed benchmark submission.",
    "Describe a safe first milestone for an expensive training project.",
)

def stable_id(*parts: str) -> str:
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def candidate_pair(prompt: str, rubric: Rubric) -> tuple[str, str]:
    strong = (
        f"{prompt} A strong plan names the artifact, the verification command, "
        f"the metric, and one caveat before moving to compute."
    )
    weak = (
        f"{prompt} This should work because the approach is obvious and the "
        f"result is guaranteed if we try it later."
    )
    if int(stable_id(prompt, rubric.id), 16) % 2 == 0:
        return strong, weak
    return weak, strong


def generate_samples(
    prompts: tuple[str, ...] = DEFAULT_PROMPTS,
    rubrics: tuple[Rubric, ...] = DEFAULT_RUBRICS,
) -> list[PairwiseSample]:
    samples: list[PairwiseSample] = []
    for prompt in prompts:
        for rubric in rubrics:
            response_a, response_b = candidate_pair(prompt, rubric)
            score_a = score_response(response_a, rubric)
            score_b = score_response(response_b, rubric)
            preferred = "a" if score_a >= score_b else "b"
            samples.append(
                PairwiseSample(
                    id=stable_id(prompt, rubric.id, response_a, response_b),
                    prompt=prompt,
                    rubric_id=rubric.id,
                    response_a=response_a,
                    response_b=response_b,
                    preferred=preferred,
                    provenance={
                        "source": "deterministic_mock_generator",
                        "labeler": "mock_genrm_reference_scorer",
                    },
                )
            )
    return samples


def write_jsonl(samples: list[PairwiseSample], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(json.dumps(sample.to_jsonable(), sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[PairwiseSample]:
    samples: list[PairwiseSample] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        samples.append(PairwiseSample(**data))
    return samples
