"""Sample coding problems for Test-Case Triage Coach."""

from typing import Any


class ProblemList(list):
    """List of problems that can also be accessed by problem_id key or get()."""

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            for problem in self:
                if problem.get("problem_id") == item:
                    return problem
            raise KeyError(f"Problem with id '{item}' not found.")
        return super().__getitem__(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default

    def keys(self) -> list[str]:
        return [p["problem_id"] for p in self]

    def values(self) -> list[dict[str, Any]]:
        return list(self)


BINARY_SEARCH_PROBLEM = {
    "problem_id": "binary_search",
    "prompt": (
        "Implement binary search to find the index of a target integer in a sorted list of unique integers. "
        "Return the index if found, or -1 if the target is not present in the list."
    ),
    "starter_code": (
        "def binary_search(nums: list[int], target: int) -> int:\n"
        "    # Write your solution here\n"
        "    pass\n"
    ),
    "entrypoint": "binary_search",
    "test_cases": [
        {"input": ([1, 2, 3, 4, 5], 3), "expected_output": 2},
        {"input": ([1, 2, 3, 4, 5], 1), "expected_output": 0},
        {"input": ([1, 2, 3, 4, 5], 5), "expected_output": 4},
        {"input": ([1, 2, 3, 4, 5], 6), "expected_output": -1},
        {"input": ([], 1), "expected_output": -1},
    ],
    "canonical_solution": (
        "def binary_search(nums: list[int], target: int) -> int:\n"
        "    left, right = 0, len(nums) - 1\n"
        "    while left <= right:\n"
        "        mid = (left + right) // 2\n"
        "        if nums[mid] == target:\n"
        "            return mid\n"
        "        elif nums[mid] < target:\n"
        "            left = mid + 1\n"
        "        else:\n"
        "            right = mid - 1\n"
        "    return -1\n"
    ),
    "buggy_variants": {
        "off_by_one": (
            "def binary_search(nums: list[int], target: int) -> int:\n"
            "    left, right = 0, len(nums) - 1\n"
            "    while left < right:  # Bug: off-by-one misses single element / last check\n"
            "        mid = (left + right) // 2\n"
            "        if nums[mid] == target:\n"
            "            return mid\n"
            "        elif nums[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
        ),
        "off_by_one_index_error": (
            "def binary_search(nums: list[int], target: int) -> int:\n"
            "    left, right = 0, len(nums)  # Bug: index out of range\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if nums[mid] == target:\n"
            "            return mid\n"
            "        elif nums[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
        ),
    },
}

TWO_SUM_PROBLEM = {
    "problem_id": "two_sum",
    "prompt": (
        "Given an array of integers nums and an integer target, return the indices of the two numbers such that "
        "they add up to target. Return an empty list [] if no such pair exists."
    ),
    "starter_code": (
        "def two_sum(nums: list[int], target: int) -> list[int]:\n"
        "    # Write your solution here\n"
        "    pass\n"
    ),
    "entrypoint": "two_sum",
    "test_cases": [
        {"input": ([2, 7, 11, 15], 9), "expected_output": [0, 1]},
        {"input": ([3, 2, 4], 6), "expected_output": [1, 2]},
        {"input": ([3, 3], 6), "expected_output": [0, 1]},
        {"input": ([1, 5, 8], 10), "expected_output": []},
    ],
    "canonical_solution": (
        "def two_sum(nums: list[int], target: int) -> list[int]:\n"
        "    seen = {}\n"
        "    for i, num in enumerate(nums):\n"
        "        complement = target - num\n"
        "        if complement in seen:\n"
        "            return [seen[complement], i]\n"
        "        seen[num] = i\n"
        "    return []\n"
    ),
    "buggy_variants": {
        "wrong_data_structure": (
            "def two_sum(nums: list[int], target: int) -> list[int]:\n"
            "    seen = set()  # Bug: wrong data structure (set instead of dict)\n"
            "    for i, num in enumerate(nums):\n"
            "        complement = target - num\n"
            "        if complement in seen:\n"
            "            return [complement, num]  # Returns values instead of indices\n"
            "        seen.add(num)\n"
            "    return []\n"
        ),
    },
}

PROBLEMS = ProblemList([BINARY_SEARCH_PROBLEM, TWO_SUM_PROBLEM])
