"""Integration tests for end-to-end graph evaluation across sample problems."""

import sys
from pathlib import Path
from unittest.mock import patch

from langgraph.types import Command

# Ensure backend/src is on sys.path
backend_src = Path(__file__).resolve().parents[2] / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from triage_coach.graph.build_graph import graph
from triage_coach.problems.sample_problems import BINARY_SEARCH_PROBLEM, TWO_SUM_PROBLEM


def test_binary_search_canonical_produces_resolved_no_hint():
    """Correct code for binary search should resolve all tests with no hint generated."""
    initial_state = {
        "session_id": "session_bs_canonical",
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
    assert result["hint_text"] is None
    assert len(result["test_results"]) == len(BINARY_SEARCH_PROBLEM["test_cases"])
    assert all(r["passed"] for r in result["test_results"])


def test_binary_search_buggy_produces_failure_type_and_hint():
    """Buggy binary search code should produce non-empty failure_type and hint_text."""
    initial_state = {
        "session_id": "session_bs_buggy",
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
    assert len(result["hint_text"].strip()) > 0
    # Tier 0 should never contain full solution patch
    assert "```python" not in result["hint_text"]


def test_two_sum_canonical_produces_resolved_no_hint():
    """Correct code for two sum should resolve with no hint generated."""
    initial_state = {
        "session_id": "session_ts_canonical",
        "problem_id": "two_sum",
        "code": TWO_SUM_PROBLEM["canonical_solution"],
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    result = graph.invoke(initial_state)

    assert result["resolved"] is True
    assert result["hint_text"] is None
    assert len(result["test_results"]) == len(TWO_SUM_PROBLEM["test_cases"])
    assert all(r["passed"] for r in result["test_results"])


def test_two_sum_buggy_produces_failure_type_and_hint():
    """Buggy two sum (wrong data structure) should produce failure_type and hint."""
    initial_state = {
        "session_id": "session_ts_buggy",
        "problem_id": "two_sum",
        "code": TWO_SUM_PROBLEM["buggy_variants"]["wrong_data_structure"],
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    with patch("triage_coach.clients.bedrock_client.invoke", return_value="wrong_data_structure"):
        result = graph.invoke(initial_state)

    assert result["resolved"] is False
    assert result["failure_type"] == "wrong_data_structure"
    assert result["hint_text"] is not None
    assert len(result["hint_text"].strip()) > 0
    # Tier 0 should never contain full solution patch
    assert "```python" not in result["hint_text"]


def test_escalation_sequence_across_hint_tiers():
    """End-to-end hint escalation sequence from Tier 0 to Tier 2."""
    state = {
        "session_id": "session_escalate",
        "problem_id": "two_sum",
        "code": TWO_SUM_PROBLEM["buggy_variants"]["wrong_data_structure"],
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    # Step 1: Initial submission -> Tier 0 hint
    with patch("triage_coach.clients.bedrock_client.invoke", return_value="wrong_data_structure"):
        state = graph.invoke(state)

    assert state["resolved"] is False
    assert state["hint_tier"] == 0
    tier0_hint = state["hint_text"]
    assert tier0_hint is not None
    assert "```python" not in tier0_hint

    # Step 2: User requests escalation -> jump to escalate_check
    with patch("triage_coach.clients.bedrock_client.invoke", return_value="Focus on mapping numbers to indices with a dictionary"):
        state = graph.invoke(Command(goto="escalate_check", update=state))

    assert state["hint_tier"] == 1
    assert state["attempt_count"] == 2
    tier1_hint = state["hint_text"]
    assert tier1_hint is not None
    assert "```python" not in tier1_hint

    # Step 3: User still stuck -> escalate again to Tier 2
    with patch("triage_coach.clients.bedrock_client.invoke", return_value="```python\n# Full patch\n```"):
        state = graph.invoke(Command(goto="escalate_check", update=state))

    assert state["hint_tier"] == 2
    assert state["attempt_count"] == 3
    tier2_hint = state["hint_text"]
    assert tier2_hint is not None
    assert "```python" in tier2_hint

    # Step 4: User submits correct solution -> resolved
    state["code"] = TWO_SUM_PROBLEM["canonical_solution"]
    state = graph.invoke(state)
    assert state["resolved"] is True
    assert state["hint_text"] is None
