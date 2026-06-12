from __future__ import annotations

import json
from pathlib import Path

from .rubrics import DEFAULT_RUBRICS
from .schemas import EvalResult, PairwiseSample, Rubric


def rubric_by_id(rubric_id: str) -> Rubric:
    for rubric in DEFAULT_RUBRICS:
        if rubric.id == rubric_id:
            return rubric
    raise KeyError(f"Unknown rubric_id: {rubric_id}")


def score_response(response: str, rubric: Rubric) -> int:
    text = response.lower()
    score = 0
    for term in rubric.positive_terms:
        score += 2 if term.lower() in text else 0
    for term in rubric.negative_terms:
        score -= 2 if term.lower() in text else 0
    score += min(len(response.split()) // 12, 3)
    return score


def predict_preference(sample: PairwiseSample) -> str:
    rubric = rubric_by_id(sample.rubric_id)
    score_a = score_response(sample.response_a, rubric)
    score_b = score_response(sample.response_b, rubric)
    return "a" if score_a >= score_b else "b"


def evaluate_samples(samples: list[PairwiseSample]) -> EvalResult:
    correct = sum(1 for sample in samples if predict_preference(sample) == sample.preferred)
    accuracy = correct / len(samples) if samples else 0.0
    return EvalResult(
        sample_count=len(samples),
        correct_count=correct,
        accuracy=accuracy,
        scorer="mock_keyword_genrm_v0",
    )


def write_eval(result: EvalResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_jsonable(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
