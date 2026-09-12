"""Unit tests for conditional edge routing and StateGraph assembly."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure backend/src is on sys.path
backend_src = Path(__file__).resolve().parents[2] / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from triage_coach.graph.build_graph import graph
from triage_coach.graph.routing import (
    route_after_classification,
    route_after_tests,
)
from triage_coach.problems.sample_problems import BINARY_SEARCH_PROBLEM


def test_route_after_tests_when_resolved():
    state_resolved_flag = {
        "session_id": "s1",
        "problem_id": "binary_search",
        "code": "",
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": True,
    }
    assert route_after_tests(state_resolved_flag) == "resolved"

    state_all_passed = {
        "session_id": "s1",
        "problem_id": "binary_search",
        "code": "",
        "test_results": [{"passed": True}, {"passed": True}],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }
    assert route_after_tests(state_all_passed) == "resolved"


def test_route_after_tests_when_failed():
    state = {
        "session_id": "s1",
        "problem_id": "binary_search",
        "code": "",
        "test_results": [{"passed": True}, {"passed": False}],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }
    assert route_after_tests(state) == "classify_failure"


def test_route_after_classification_when_passed():
    state_passed = {
        "session_id": "s1",
        "problem_id": "binary_search",
        "code": "",
        "test_results": [],
        "failure_type": "passed",
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": True,
    }
    assert route_after_classification(state_passed) == "end"


def test_route_after_classification_when_failed():
    for f_type in ["off_by_one", "wrong_data_structure", "edge_case", "other"]:
        state = {
            "session_id": "s1",
            "problem_id": "binary_search",
            "code": "",
            "test_results": [],
            "failure_type": f_type,
            "hint_tier": 0,
            "attempt_count": 1,
            "hint_text": None,
            "resolved": False,
        }
        assert route_after_classification(state) == "generate_hint"


def test_graph_compiled_object():
    """Verify that build_graph compiles graph without errors."""
    assert graph is not None
    # Check that required nodes exist in the graph
    node_names = set(graph.nodes.keys())
    assert {"run_tests", "classify_failure", "generate_hint", "escalate_check"}.issubset(node_names)


def test_graph_execution_resolved():
    """Submitting correct canonical code routes directly to END with resolved=True."""
    initial_state = {
        "session_id": "s_canonical",
        "problem_id": "binary_search",
        "code": BINARY_SEARCH_PROBLEM["canonical_solution"],
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    result = graph.invoke(initial_state)
    assert result["resolved"] is True
    assert result["hint_text"] is None  # no hint generated because it resolved after tests


def test_graph_execution_buggy_routes_to_hint():
    """Submitting buggy code routes through classify_failure and generate_hint."""
    initial_state = {
        "session_id": "s_buggy",
        "problem_id": "binary_search",
        "code": BINARY_SEARCH_PROBLEM["buggy_variants"]["off_by_one"],
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    with patch("triage_coach.clients.bedrock_client.invoke", return_value="off_by_one"):
        result = graph.invoke(initial_state)

    assert result["resolved"] is False
    assert result["failure_type"] == "off_by_one"
    assert result["hint_text"] is not None
    assert len(result["hint_text"]) > 0
