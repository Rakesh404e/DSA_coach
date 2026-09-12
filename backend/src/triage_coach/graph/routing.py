"""Conditional edge routing functions for the triage coach StateGraph."""

from typing import Literal

from triage_coach.graph.state import TriageState


def route_after_tests(
    state: TriageState,
) -> Literal["classify_failure", "resolved"]:
    """Determine whether to proceed to classification or terminate as resolved."""
    if state.get("resolved") is True:
        return "resolved"

    test_results = state.get("test_results", [])
    if test_results and all(r.get("passed", False) for r in test_results):
        return "resolved"

    return "classify_failure"


def route_after_classification(
    state: TriageState,
) -> Literal["generate_hint", "end"]:
    """Determine whether to generate a hint or end the evaluation session."""
    failure_type = state.get("failure_type")
    if failure_type == "passed" or state.get("resolved") is True:
        return "end"

    return "generate_hint"
