"""Unit tests for the sandbox code execution engine."""

import sys
from pathlib import Path

# Ensure backend/src is on sys.path
backend_src = Path(__file__).resolve().parents[2] / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from triage_coach.graph.sandbox import run_against_tests
from triage_coach.problems.sample_problems import BINARY_SEARCH_PROBLEM, TWO_SUM_PROBLEM


def test_correct_code_passes_all_tests():
    code = (
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
    )
    test_cases = [
        {"input": (2, 3), "expected_output": 5},
        {"input": (-1, 1), "expected_output": 0},
        {"input": (0, 0), "expected_output": 0},
    ]

    results = run_against_tests(code, test_cases)
    assert len(results) == 3
    for r in results:
        assert r["passed"] is True
        assert r["error"] is None
    assert results[0]["actual_output"] == 5
    assert results[1]["actual_output"] == 0
    assert results[2]["actual_output"] == 0


def test_runtime_error_caught_and_reported_not_raised():
    code = (
        "def buggy(items: list) -> int:\n"
        "    return items[10]\n"
    )
    test_cases = [
        {"input": ([1, 2],), "expected_output": 1},
    ]

    # Must never raise an exception out of run_against_tests
    results = run_against_tests(code, test_cases)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert results[0]["error"] is not None
    assert "IndexError" in results[0]["error"]


def test_infinite_loop_killed_by_timeout():
    code = (
        "def infinite_loop(n: int) -> int:\n"
        "    while True:\n"
        "        pass\n"
        "    return n\n"
    )
    test_cases = [
        {"input": (1,), "expected_output": 1},
    ]

    # Enforce a small timeout to keep test fast
    results = run_against_tests(code, test_cases, timeout=0.5)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert results[0]["error"] is not None
    assert "timed out" in results[0]["error"].lower()


def test_import_os_blocked():
    code = (
        "import os\n"
        "def dangerous(x: int) -> int:\n"
        "    return 42\n"
    )
    test_cases = [
        {"input": (1,), "expected_output": 42},
    ]

    results = run_against_tests(code, test_cases)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert results[0]["error"] is not None
    assert "import" in results[0]["error"].lower()


def test_open_file_blocked():
    code = (
        "def read_file(name: str) -> str:\n"
        "    with open(name) as f:\n"
        "        return f.read()\n"
    )
    test_cases = [
        {"input": ("test.txt",), "expected_output": "data"},
    ]

    results = run_against_tests(code, test_cases)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert results[0]["error"] is not None
    assert "NameError" in results[0]["error"] or "open" in results[0]["error"]


def test_syntax_error_reported():
    code = "def broken(\n"
    test_cases = [{"input": (1,), "expected_output": 1}]

    results = run_against_tests(code, test_cases)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert results[0]["error"] is not None
    assert "SyntaxError" in results[0]["error"]


def test_sample_problems_binary_search_canonical():
    results = run_against_tests(
        BINARY_SEARCH_PROBLEM["canonical_solution"],
        BINARY_SEARCH_PROBLEM["test_cases"],
    )
    assert len(results) == len(BINARY_SEARCH_PROBLEM["test_cases"])
    assert all(r["passed"] for r in results)


def test_sample_problems_binary_search_off_by_one_fails():
    results = run_against_tests(
        BINARY_SEARCH_PROBLEM["buggy_variants"]["off_by_one"],
        BINARY_SEARCH_PROBLEM["test_cases"],
    )
    # The off-by-one misses single elements/edges
    assert any(not r["passed"] for r in results)


def test_sample_problems_two_sum_canonical():
    results = run_against_tests(
        TWO_SUM_PROBLEM["canonical_solution"],
        TWO_SUM_PROBLEM["test_cases"],
    )
    assert len(results) == len(TWO_SUM_PROBLEM["test_cases"])
    assert all(r["passed"] for r in results)


def test_sample_problems_two_sum_wrong_data_structure_fails():
    results = run_against_tests(
        TWO_SUM_PROBLEM["buggy_variants"]["wrong_data_structure"],
        TWO_SUM_PROBLEM["test_cases"],
    )
    assert any(not r["passed"] for r in results)
