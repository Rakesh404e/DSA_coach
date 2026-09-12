"""Triage Coach Graph State definition."""

from typing import TypedDict


class TriageState(TypedDict):
    """Represents the complete state of a coaching triage session."""

    session_id: str
    problem_id: str
    code: str
    test_results: list
    failure_type: str | None
    hint_tier: int
    attempt_count: int
    hint_text: str | None
    resolved: bool
