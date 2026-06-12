from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Rubric:
    id: str
    instruction: str
    positive_terms: tuple[str, ...]
    negative_terms: tuple[str, ...]


@dataclass(frozen=True)
class PairwiseSample:
    id: str
    prompt: str
    rubric_id: str
    response_a: str
    response_b: str
    preferred: str
    provenance: dict[str, str]

    def to_jsonable(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvalResult:
    sample_count: int
    correct_count: int
    accuracy: float
    scorer: str

    def to_jsonable(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MemoryEvent:
    id: str
    kind: str
    source_sample_id: str
    confidence: float
    payload: dict[str, Any]
    provenance: dict[str, str]
    supersedes: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningLoopReport:
    raw_event_count: int
    deduped_event_count: int
    memory_kinds: list[str]
    update_candidate_ids: list[str]
    rejected_update_ids: list[str]
    events: list[MemoryEvent]

    def to_jsonable(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [event.to_jsonable() for event in self.events]
        return data
