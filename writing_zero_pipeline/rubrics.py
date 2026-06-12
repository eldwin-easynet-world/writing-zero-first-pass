from __future__ import annotations

from .schemas import Rubric


DEFAULT_RUBRICS = (
    Rubric(
        id="clarity_evidence",
        instruction="Prefer clear writing with concrete evidence and caveats.",
        positive_terms=("evidence", "specific", "verify", "caveat", "metric"),
        negative_terms=("obvious", "guaranteed", "magic", "trust me"),
    ),
    Rubric(
        id="actionability",
        instruction="Prefer answers with steps, artifacts, and handoff criteria.",
        positive_terms=("step", "artifact", "command", "handoff", "criteria"),
        negative_terms=("someday", "maybe", "unclear", "later"),
    ),
)

