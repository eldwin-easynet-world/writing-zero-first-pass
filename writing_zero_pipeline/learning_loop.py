from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schemas import LearningLoopReport, MemoryEvent, PairwiseSample


MEMORY_KINDS = ("fact", "episodic", "procedural", "skill", "agent", "workflow")


def _event_id(kind: str, payload: dict[str, Any]) -> str:
    body = json.dumps({"kind": kind, "payload": payload}, sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def _sample_hash(sample: PairwiseSample) -> str:
    body = json.dumps(sample.to_jsonable(), sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def memory_events_for_sample(sample: PairwiseSample) -> list[MemoryEvent]:
    sample_hash = _sample_hash(sample)
    common_provenance = {
        "sample_id": sample.id,
        "sample_hash": sample_hash,
        "source": sample.provenance["source"],
        "labeler": sample.provenance["labeler"],
    }
    winner = sample.response_a if sample.preferred == "a" else sample.response_b
    return [
        MemoryEvent(
            id=_event_id(
                "fact",
                {
                    "sample_id": sample.id,
                    "rubric_id": sample.rubric_id,
                    "preferred": sample.preferred,
                },
            ),
            kind="fact",
            source_sample_id=sample.id,
            confidence=0.95,
            payload={
                "rubric_id": sample.rubric_id,
                "preferred_response": sample.preferred,
                "preferred_response_hash": hashlib.sha256(winner.encode("utf-8")).hexdigest()[:16],
            },
            provenance=common_provenance,
        ),
        MemoryEvent(
            id=_event_id("episodic", {"sample_id": sample.id, "run": "zero_spend_seed"}),
            kind="episodic",
            source_sample_id=sample.id,
            confidence=0.9,
            payload={
                "observation": "A deterministic seed sample was generated and labeled before any paid compute.",
                "prompt": sample.prompt,
            },
            provenance=common_provenance,
        ),
        MemoryEvent(
            id=_event_id(
                "procedural",
                {
                    "command": "generate-evaluate-handoff-learning-loop",
                    "schema": "pairwise_sample_v0",
                },
            ),
            kind="procedural",
            source_sample_id=sample.id,
            confidence=0.92,
            payload={
                "procedure": "Generate pairwise samples, evaluate labels, emit compute handoff, then emit memory learning report.",
                "gate": "Only promote the procedure after schema, provenance, and offline validation pass.",
            },
            provenance=common_provenance,
        ),
        MemoryEvent(
            id=_event_id("skill", {"name": "rubric_grounded_pairwise_labeling", "version": "v0"}),
            kind="skill",
            source_sample_id=sample.id,
            confidence=0.88,
            payload={
                "skill": "rubric_grounded_pairwise_labeling",
                "inputs": ["prompt", "rubric", "candidate_a", "candidate_b"],
                "outputs": ["preferred_response", "label_provenance"],
            },
            provenance=common_provenance,
        ),
        MemoryEvent(
            id=_event_id("agent", {"name": "compute_gate_reviewer", "version": "v0"}),
            kind="agent",
            source_sample_id=sample.id,
            confidence=0.84,
            payload={
                "agent": "compute_gate_reviewer",
                "role": "reject paid-compute escalation until artifacts are reproducible and reviewer-readable",
            },
            provenance=common_provenance,
        ),
        MemoryEvent(
            id=_event_id("workflow", {"name": "zero_spend_to_compute_gate", "version": "v0"}),
            kind="workflow",
            source_sample_id=sample.id,
            confidence=0.93,
            payload={
                "workflow": "zero_spend_to_compute_gate",
                "steps": ["seed data", "mock scorer", "eval artifact", "handoff artifact", "learning report"],
                "dedup_key": "workflow:name:version",
            },
            provenance=common_provenance,
        ),
    ]


def build_learning_loop_report(samples: list[PairwiseSample]) -> LearningLoopReport:
    raw_events = [event for sample in samples for event in memory_events_for_sample(sample)]
    deduped = {event.id: event for event in raw_events}
    events = sorted(deduped.values(), key=lambda event: (event.kind, event.id))
    update_candidates = [
        event.id
        for event in events
        if event.confidence >= 0.9 and event.kind in {"fact", "episodic", "procedural", "workflow"}
    ]
    rejected_updates = [event.id for event in events if event.id not in update_candidates]
    return LearningLoopReport(
        raw_event_count=len(raw_events),
        deduped_event_count=len(events),
        memory_kinds=sorted({event.kind for event in events}),
        update_candidate_ids=update_candidates,
        rejected_update_ids=rejected_updates,
        events=events,
    )


def write_learning_loop_report(samples: list[PairwiseSample], path: Path) -> LearningLoopReport:
    report = build_learning_loop_report(samples)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_jsonable(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
