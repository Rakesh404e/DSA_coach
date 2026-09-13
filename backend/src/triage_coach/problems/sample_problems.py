"""Sample coding problems for Test-Case Triage Coach.

Includes 5 high-signal DSA interview archetypes:
1. Two Sum (Hash Map / Array traversal)
2. Valid Parentheses (Stack / Boundary validation)
3. Binary Search (Logarithmic search / Off-by-one boundary bugs)
4. Longest Substring Without Repeating Characters (Sliding Window)
5. Merge Two Sorted Lists (Two Pointers / Edge-case handling)
"""

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


TWO_SUM_PROBLEM = {
    "problem_id": "two_sum",
    "title": "Two Sum",
    "category": "Hash Map & Arrays",
    "difficulty": "Easy",
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
        "edge_case": (
            "def two_sum(nums: list[int], target: int) -> list[int]:\n"
            "    # Bug: reuses the same element if target - num == num\n"
            "    for i in range(len(nums)):\n"
            "        for j in range(len(nums)):\n"
            "            if nums[i] + nums[j] == target:\n"
            "                return [i, j]\n"
            "    return []\n"
        ),
    },
}


VALID_PARENTHESES_PROBLEM = {
    "problem_id": "valid_parentheses",
    "title": "Valid Parentheses",
    "category": "Stack & State Validation",
    "difficulty": "Easy",
    "prompt": (
        "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', "
        "determine if the input string is valid. Open brackets must be closed by the same type "
        "of brackets in the correct order. Return True if valid, False otherwise."
    ),
    "starter_code": (
        "def is_valid(s: str) -> bool:\n"
        "    # Write your solution here\n"
        "    pass\n"
    ),
    "entrypoint": "is_valid",
    "test_cases": [
        {"input": "()", "expected_output": True},
        {"input": "()[]{}", "expected_output": True},
        {"input": "(]", "expected_output": False},
        {"input": "([)]", "expected_output": False},
        {"input": "{[]}", "expected_output": True},
        {"input": "", "expected_output": True},
        {"input": "]", "expected_output": False},
        {"input": "[", "expected_output": False},
    ],
    "canonical_solution": (
        "def is_valid(s: str) -> bool:\n"
        "    stack = []\n"
        "    mapping = {')': '(', '}': '{', ']': '['}\n"
        "    for char in s:\n"
        "        if char in mapping:\n"
        "            top = stack.pop() if stack else '#'\n"
        "            if mapping[char] != top:\n"
        "                return False\n"
        "        else:\n"
        "            stack.append(char)\n"
        "    return len(stack) == 0\n"
    ),
    "buggy_variants": {
        "wrong_data_structure": (
            "def is_valid(s: str) -> bool:\n"
            "    # Bug: counter-based approach fails on nested interleaving like '([)]'\n"
            "    return s.count('(') == s.count(')') and s.count('{') == s.count('}') and s.count('[') == s.count(']')\n"
        ),
        "off_by_one": (
            "def is_valid(s: str) -> bool:\n"
            "    stack = []\n"
            "    mapping = {')': '(', '}': '{', ']': '['}\n"
            "    for char in s:\n"
            "        if char in mapping:\n"
            "            if not stack or stack.pop() != mapping[char]:\n"
            "                return False\n"
            "        else:\n"
            "            stack.append(char)\n"
            "    return True  # Bug: misses check for leftover open brackets (len(stack) == 0)\n"
        ),
    },
}


BINARY_SEARCH_PROBLEM = {
    "problem_id": "binary_search",
    "title": "Binary Search",
    "category": "Logarithmic Search",
    "difficulty": "Easy",
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


LONGEST_SUBSTRING_PROBLEM = {
    "problem_id": "longest_substring",
    "title": "Longest Substring Without Repeating Characters",
    "category": "Sliding Window",
    "difficulty": "Medium",
    "prompt": (
        "Given a string s, find the length of the longest substring without duplicate characters."
    ),
    "starter_code": (
        "def length_of_longest_substring(s: str) -> int:\n"
        "    # Write your solution here\n"
        "    pass\n"
    ),
    "entrypoint": "length_of_longest_substring",
    "test_cases": [
        {"input": "abcabcbb", "expected_output": 3},
        {"input": "bbbbb", "expected_output": 1},
        {"input": "pwwkew", "expected_output": 3},
        {"input": "dvdf", "expected_output": 3},
        {"input": "", "expected_output": 0},
        {"input": "a", "expected_output": 1},
        {"input": "au", "expected_output": 2},
        {"input": "abba", "expected_output": 2},
    ],
    "canonical_solution": (
        "def length_of_longest_substring(s: str) -> int:\n"
        "    char_index_map = {}\n"
        "    max_len = 0\n"
        "    left = 0\n"
        "    for right, char in enumerate(s):\n"
        "        if char in char_index_map and char_index_map[char] >= left:\n"
        "            left = char_index_map[char] + 1\n"
        "        char_index_map[char] = right\n"
        "        max_len = max(max_len, right - left + 1)\n"
        "    return max_len\n"
    ),
    "buggy_variants": {
        "wrong_data_structure": (
            "def length_of_longest_substring(s: str) -> int:\n"
            "    seen = set()\n"
            "    max_len = 0\n"
            "    for char in s:\n"
            "        if char in seen:  # Bug: resetting window on duplicate loses substring\n"
            "            seen = {char}\n"
            "        else:\n"
            "            seen.add(char)\n"
            "        max_len = max(max_len, len(seen))\n"
            "    return max_len\n"
        ),
        "off_by_one": (
            "def length_of_longest_substring(s: str) -> int:\n"
            "    char_index_map = {}\n"
            "    max_len = 0\n"
            "    left = 0\n"
            "    for right, char in enumerate(s):\n"
            "        if char in char_index_map and char_index_map[char] >= left:\n"
            "            left = char_index_map[char] + 1\n"
            "        char_index_map[char] = right\n"
            "        max_len = max(max_len, right - left)  # Bug: off-by-one missing +1\n"
            "    return max_len\n"
        ),
    },
}


MERGE_TWO_SORTED_LISTS_PROBLEM = {
    "problem_id": "merge_two_sorted_lists",
    "title": "Merge Two Sorted Lists",
    "category": "Two Pointers & Arrays",
    "difficulty": "Easy",
    "prompt": (
        "You are given two sorted integer lists list1 and list2. "
        "Merge the two lists into one sorted list and return it."
    ),
    "starter_code": (
        "def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:\n"
        "    # Write your solution here\n"
        "    pass\n"
    ),
    "entrypoint": "merge_two_lists",
    "test_cases": [
        {"input": ([1, 2, 4], [1, 3, 4]), "expected_output": [1, 1, 2, 3, 4, 4]},
        {"input": ([], []), "expected_output": []},
        {"input": ([], [0]), "expected_output": [0]},
        {"input": ([5], [1, 2, 3]), "expected_output": [1, 2, 3, 5]},
        {"input": ([2], [1]), "expected_output": [1, 2]},
    ],
    "canonical_solution": (
        "def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:\n"
        "    i, j = 0, 0\n"
        "    result = []\n"
        "    while i < len(list1) and j < len(list2):\n"
        "        if list1[i] <= list2[j]:\n"
        "            result.append(list1[i])\n"
        "            i += 1\n"
        "        else:\n"
        "            result.append(list2[j])\n"
        "            j += 1\n"
        "    result.extend(list1[i:])\n"
        "    result.extend(list2[j:])\n"
        "    return result\n"
    ),
    "buggy_variants": {
        "edge_case": (
            "def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:\n"
            "    i, j = 0, 0\n"
            "    result = []\n"
            "    while i < len(list1) and j < len(list2):\n"
            "        if list1[i] <= list2[j]:\n"
            "            result.append(list1[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            result.append(list2[j])\n"
            "            j += 1\n"
            "    # Bug: forgets remaining elements when one list exhausts\n"
            "    return result\n"
        ),
        "off_by_one": (
            "def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:\n"
            "    i, j = 0, 0\n"
            "    result = []\n"
            "    while i < len(list1) - 1 and j < len(list2) - 1:  # Bug: off-by-one loop limit\n"
            "        if list1[i] <= list2[j]:\n"
            "            result.append(list1[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            result.append(list2[j])\n"
            "            j += 1\n"
            "    result.extend(list1[i:])\n"
            "    result.extend(list2[j:])\n"
            "    return result\n"
        ),
    },
}


PROBLEMS = ProblemList([
    TWO_SUM_PROBLEM,
    VALID_PARENTHESES_PROBLEM,
    BINARY_SEARCH_PROBLEM,
    LONGEST_SUBSTRING_PROBLEM,
    MERGE_TWO_SORTED_LISTS_PROBLEM,
])
