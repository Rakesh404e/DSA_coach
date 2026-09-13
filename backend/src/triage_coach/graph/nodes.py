"""Graph node functions for test evaluation, failure classification, and hint generation."""

import json
from typing import Any

from triage_coach.clients import bedrock_client
from triage_coach.graph.sandbox import run_against_tests
from triage_coach.graph.state import TriageState
from triage_coach.problems.sample_problems import PROBLEMS


def run_tests_node(state: TriageState) -> dict[str, Any]:
    """Execute code against problem test cases in sandbox and record results.

    Supports both canned problems in PROBLEMS and dynamic custom problems.
    """
    problem_id = state.get("problem_id", "")
    code = state.get("code", "")
    custom_problem = state.get("custom_problem")

    if custom_problem and (problem_id == "custom" or not problem_id):
        test_cases = custom_problem.get("test_cases", [])
        entrypoint = custom_problem.get("entrypoint")
        if not test_cases:
            return {
                "test_results": [{
                    "test_case": {},
                    "passed": False,
                    "actual_output": None,
                    "error": "No test cases provided for custom problem.",
                }],
                "resolved": False,
            }
    else:
        problem = PROBLEMS.get(problem_id)
        if not problem:
            return {
                "test_results": [{
                    "test_case": {},
                    "passed": False,
                    "actual_output": None,
                    "error": f"Unknown problem_id: {problem_id}",
                }],
                "resolved": False,
            }

        test_cases = problem.get("test_cases", [])
        entrypoint = problem.get("entrypoint")

    test_results = run_against_tests(code, test_cases, entrypoint=entrypoint)
    resolved = bool(test_results and all(r.get("passed", False) for r in test_results))

    result: dict[str, Any] = {
        "test_results": test_results,
        "resolved": resolved,
    }
    if resolved:
        result["hint_text"] = None
        result["failure_type"] = None

    return result


def classify_failure_node(
    state: TriageState,
    llm_invoke: Any = None,
) -> dict[str, Any]:
    """Classify failure root cause into one of:

    'off_by_one' | 'wrong_data_structure' | 'edge_case' | 'passed' | 'other'.
    Uses pattern checks for obvious cases (e.g. IndexError -> off_by_one),
    and LLM via bedrock_client for ambiguous cases.
    """
    if llm_invoke is None:
        llm_invoke = bedrock_client.invoke

    test_results = state.get("test_results", [])
    if not test_results or all(r.get("passed", False) for r in test_results):
        return {"failure_type": "passed"}

    # Pattern check for obvious cases
    has_index_error = False
    for r in test_results:
        err = r.get("error") or ""
        if "IndexError" in err:
            has_index_error = True
            break

    if has_index_error:
        return {"failure_type": "off_by_one"}

    # For ambiguous cases, invoke LLM
    failing_summary = []
    for i, r in enumerate(test_results):
        if not r.get("passed"):
            failing_summary.append(
                f"Test {i+1}: input={r.get('test_case', {}).get('input')}, "
                f"expected={r.get('test_case', {}).get('expected_output')}, "
                f"actual={r.get('actual_output')}, error={r.get('error')}"
            )

    problem_name = state.get("problem_id", "")
    if problem_name == "custom" and state.get("custom_problem"):
        problem_name = state.get("custom_problem", {}).get("prompt", "custom problem")

    prompt = (
        f"Problem: {problem_name}\n"
        f"Submitted Code:\n{state.get('code')}\n\n"
        f"Failing Test Results:\n" + "\n".join(failing_summary) + "\n\n"
        "Classify the failure root cause into exactly one of these categories:\n"
        "- off_by_one\n"
        "- wrong_data_structure\n"
        "- edge_case\n"
        "- other\n\n"
        "Reply with ONLY the category name."
    )

    try:
        response = llm_invoke(prompt)
        resp_clean = response.strip().lower()

        if "off_by_one" in resp_clean:
            return {"failure_type": "off_by_one"}
        elif "wrong_data_structure" in resp_clean:
            return {"failure_type": "wrong_data_structure"}
        elif "edge_case" in resp_clean:
            return {"failure_type": "edge_case"}
        elif "passed" in resp_clean:
            return {"failure_type": "passed"}
        else:
            return {"failure_type": "other"}
    except Exception:
        # Fallback to 'other' if LLM cannot be reached or fails
        return {"failure_type": "other"}


def _canned_fallback_hint(problem_id: str, failure_type: str | None, tier: int) -> str:
    """Generate deterministic fallback hints if LLM is unavailable."""
    if tier == 0:
        if failure_type == "off_by_one":
            return "Consider the boundary conditions of your iteration: verify where your search starts, ends, and updates."
        elif failure_type == "wrong_data_structure":
            return "Consider whether your chosen data structure retains all necessary associations (such as original indices or frequencies)."
        elif failure_type == "edge_case":
            return "Consider extreme or edge inputs, such as empty collections or single-element inputs."
        return "Review the core invariants of your algorithm and trace how intermediate values change."

    if tier == 1:
        if failure_type == "off_by_one":
            return "Check your loop condition (`<` vs `<=`) or pointer steps (`+ 1` / `- 1`). You may be skipping the final valid element."
        elif failure_type == "wrong_data_structure":
            return "Consider if a hash map (dictionary) or stack better suits the ordering or lookup guarantees needed instead of a simple set or counter."
        elif failure_type == "edge_case":
            return "Verify how the code handles boundary cases, like target values at the extreme ends or empty lists."
        return "Trace the failing test case line by line to see where the actual value deviates from expected."

    # Tier 2 - Full patch
    problem = PROBLEMS.get(problem_id)
    canonical = problem.get("canonical_solution") if problem else ""
    if canonical:
        return (
            f"Here is the corrected solution with explanation:\n\n"
            f"```python\n{canonical}\n```"
        )
    return (
        "Here is the corrected logic pattern:\n\n"
        "Carefully review the algorithm requirements and verify all invariants and corner cases."
    )


def generate_hint_node(
    state: TriageState,
    llm_invoke: Any = None,
) -> dict[str, Any]:
    """Produce hint_text according to hint_tier:

    Tier 0: Conceptual nudge
    Tier 1: Specific pointer to failing logic
    Tier 2: Full patch
    Rule: Never generate a tier-2 patch if hint_tier < 2.
    """
    if llm_invoke is None:
        llm_invoke = bedrock_client.invoke
    tier = state.get("hint_tier", 0)
    failure_type = state.get("failure_type", "other")
    problem_id = state.get("problem_id", "")

    if failure_type == "passed" or state.get("resolved"):
        return {"hint_text": "All tests passed! Great job!"}

    tier_labels = {
        0: "Tier 0 (Conceptual nudge: High-level invariant, NO code or line specifics)",
        1: "Tier 1 (Specific pointer: Direct attention to the failing logic/structure, NO full patch)",
        2: "Tier 2 (Full patch: Explain the fix and provide the corrected code patch)",
    }
    tier_desc = tier_labels.get(min(tier, 2), tier_labels[2])

    problem_desc = problem_id
    if problem_id == "custom" and state.get("custom_problem"):
        problem_desc = state.get("custom_problem", {}).get("prompt", "custom problem")

    prompt = (
        f"Problem: {problem_desc}\n"
        f"Code:\n{state.get('code')}\n"
        f"Failure type: {failure_type}\n"
        f"Hint tier: {tier}\n\n"
        f"Instruction: {tier_desc}\n"
        "Generate coaching feedback for the student:"
    )

    hint_text = ""
    try:
        response = llm_invoke(prompt)
        hint_text = response.strip()
    except Exception:
        hint_text = _canned_fallback_hint(problem_id, failure_type, tier)

    # Strict enforcement: Never generate a tier-2 patch if hint_tier < 2
    if tier < 2 and ("```" in hint_text or "def " in hint_text):
        hint_text = _canned_fallback_hint(problem_id, failure_type, tier)

    return {"hint_text": hint_text}


def escalate_check_node(state: TriageState) -> dict[str, Any]:
    """Increment hint_tier by 1 when user requests escalation (still stuck)."""
    current_tier = state.get("hint_tier", 0)
    current_attempts = state.get("attempt_count", 0)
    return {
        "hint_tier": current_tier + 1,
        "attempt_count": current_attempts + 1,
    }


def synthesize_problem_from_prompt(prompt_text: str, llm_invoke: Any = None) -> dict[str, Any]:
    """Use Bedrock to synthesize starter code, entrypoint, and test cases from a raw problem prompt."""
    if llm_invoke is None:
        llm_invoke = bedrock_client.invoke

    instructions = (
        "You are an expert algorithm challenge author. Given the following programming problem description, "
        "synthesize a Python challenge configuration formatted as valid JSON ONLY.\n\n"
        "Return a JSON object with exactly these keys:\n"
        "- title: Short title string\n"
        "- entrypoint: The Python function name string (e.g. 'rotate_array')\n"
        "- starter_code: Python function definition stub string with type hints and 'pass'\n"
        "- test_cases: Array of 5 to 7 test objects, each with 'input' (tuple of arguments if multi-arg, or single value) and 'expected_output'\n\n"
        f"Problem Description:\n{prompt_text}\n\n"
        "Output ONLY the JSON object, no Markdown code blocks or explanation."
    )

    try:
        raw = llm_invoke(instructions).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        parsed = json.loads(raw)
        return {
            "problem_id": "custom",
            "title": parsed.get("title", "Custom Problem"),
            "prompt": prompt_text,
            "entrypoint": parsed.get("entrypoint", "solution"),
            "starter_code": parsed.get("starter_code", "def solution():\n    pass\n"),
            "test_cases": parsed.get("test_cases", []),
        }
    except Exception as e:
        return _smart_synthesize_fallback(prompt_text, e)


def _smart_synthesize_fallback(prompt_text: str, err: Any) -> dict[str, Any]:
    """Provide rich domain-specific fallback when Bedrock LLM is unavailable."""
    lower = prompt_text.lower()

    if "palindrome" in lower:
        return {
            "problem_id": "custom",
            "title": "Palindrome Number",
            "prompt": prompt_text,
            "entrypoint": "is_palindrome",
            "starter_code": "def is_palindrome(x: int) -> bool:\n    # Return True if x is a palindrome integer, False otherwise.\n    pass\n",
            "test_cases": [
                {"input": 121, "expected_output": True},
                {"input": -121, "expected_output": False},
                {"input": 10, "expected_output": False},
                {"input": 0, "expected_output": True},
                {"input": 12321, "expected_output": True},
            ],
            "note": f"Domain fallback active ({err})",
        }

    if "roman" in lower:
        return {
            "problem_id": "custom",
            "title": "Roman to Integer",
            "prompt": prompt_text,
            "entrypoint": "roman_to_int",
            "starter_code": "def roman_to_int(s: str) -> int:\n    # Convert Roman numeral string to integer\n    pass\n",
            "test_cases": [
                {"input": "III", "expected_output": 3},
                {"input": "LVIII", "expected_output": 58},
                {"input": "MCMXCIV", "expected_output": 1994},
                {"input": "IV", "expected_output": 4},
                {"input": "IX", "expected_output": 9},
            ],
            "note": f"Domain fallback active ({err})",
        }

    if "overlap" in lower or ("img1" in lower and "img2" in lower):
        return {
            "problem_id": "custom",
            "title": "Image Overlap",
            "prompt": prompt_text,
            "entrypoint": "largest_overlap",
            "starter_code": "def largest_overlap(img1: list[list[int]], img2: list[list[int]]) -> int:\n    # Return the largest possible overlap\n    pass\n",
            "test_cases": [
                {
                    "input": [[[1, 1, 0], [0, 1, 0], [0, 1, 0]], [[0, 0, 0], [0, 1, 1], [0, 0, 1]]],
                    "expected_output": 3,
                },
                {"input": [[[1]], [[1]]], "expected_output": 1},
                {"input": [[[0]], [[0]]], "expected_output": 0},
            ],
            "note": f"Domain fallback active ({err})",
        }

    if "rotate" in lower:
        return {
            "problem_id": "custom",
            "title": "Rotate Array",
            "prompt": prompt_text,
            "entrypoint": "rotate",
            "starter_code": "def rotate(nums: list[int], k: int) -> list[int]:\n    # Write your solution here\n    pass\n",
            "test_cases": [
                {"input": [[1, 2, 3, 4, 5, 6, 7], 3], "expected_output": [5, 6, 7, 1, 2, 3, 4]},
                {"input": [[-1, -100, 3, 99], 2], "expected_output": [3, 99, -1, -100]},
                {"input": [[1], 0], "expected_output": [1]},
            ],
            "note": f"Domain fallback active ({err})",
        }

    if "substring" in lower or "repeating" in lower:
        return {
            "problem_id": "custom",
            "title": "Longest Substring Without Repeating Characters",
            "prompt": prompt_text,
            "entrypoint": "length_of_longest_substring",
            "starter_code": "def length_of_longest_substring(s: str) -> int:\n    # Write your solution here\n    pass\n",
            "test_cases": [
                {"input": "abcabcbb", "expected_output": 3},
                {"input": "bbbbb", "expected_output": 1},
                {"input": "pwwkew", "expected_output": 3},
                {"input": "", "expected_output": 0},
            ],
            "note": f"Domain fallback active ({err})",
        }

    return {
        "problem_id": "custom",
        "title": "Custom Problem",
        "prompt": prompt_text,
        "entrypoint": "solution",
        "starter_code": "def solution(data):\n    # Write your solution here\n    pass\n",
        "test_cases": [
            {"input": [1, 2, 3, 4], "expected_output": 4},
            {"input": [5, 4, 3, 2, 1], "expected_output": 5},
            {"input": [], "expected_output": 0},
        ],
        "note": f"Fallback synthesis active ({err})",
    }
