export interface TestCase {
  input: string;
  expected: string;
}

export interface Problem {
  id: string;
  title: string;
  category: string;
  difficulty: "Easy" | "Medium" | "Hard";
  prompt: string;
  entrypoint: string;
  starterCode: string;
  canonicalSolution: string;
  buggyVariants: {
    id: string;
    label: string;
    code: string;
  }[];
  sampleTestCases: TestCase[];
}

export const PROBLEMS: Record<string, Problem> = {
  two_sum: {
    id: "two_sum",
    title: "Two Sum",
    category: "Hash Map & Arrays",
    difficulty: "Easy",
    prompt:
      "Given an array of integers nums and an integer target, return the indices of the two numbers such that they add up to target. Return an empty list [] if no such pair exists.",
    entrypoint: "two_sum",
    starterCode: `def two_sum(nums: list[int], target: int) -> list[int]:
    # Write your solution here
    pass
`,
    canonicalSolution: `def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
`,
    buggyVariants: [
      {
        id: "wrong_data_structure",
        label: "Wrong Data Structure (Set loses indices)",
        code: `def two_sum(nums: list[int], target: int) -> list[int]:
    seen = set()  # Bug: wrong data structure (set stores values, not indices)
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [complement, num]  # Returns values instead of indices
        seen.add(num)
    return []
`,
      },
      {
        id: "edge_case",
        label: "Edge Case (Reusing same element)",
        code: `def two_sum(nums: list[int], target: int) -> list[int]:
    # Bug: nested loops reuse the same index when target - num == num
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
`,
      },
    ],
    sampleTestCases: [
      { input: "nums = [2, 7, 11, 15], target = 9", expected: "[0, 1]" },
      { input: "nums = [3, 2, 4], target = 6", expected: "[1, 2]" },
      { input: "nums = [3, 3], target = 6", expected: "[0, 1]" },
      { input: "nums = [1, 5, 8], target = 10", expected: "[]" },
    ],
  },
  valid_parentheses: {
    id: "valid_parentheses",
    title: "Valid Parentheses",
    category: "Stack & State Validation",
    difficulty: "Easy",
    prompt:
      "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. Open brackets must be closed by the same type of brackets in the correct order. Return True if valid, False otherwise.",
    entrypoint: "is_valid",
    starterCode: `def is_valid(s: str) -> bool:
    # Write your solution here
    pass
`,
    canonicalSolution: `def is_valid(s: str) -> bool:
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return len(stack) == 0
`,
    buggyVariants: [
      {
        id: "wrong_data_structure",
        label: "Wrong Data Structure (Counter fails on '([)]')",
        code: `def is_valid(s: str) -> bool:
    # Bug: counter checks quantity but ignores nesting order
    return s.count('(') == s.count(')') and s.count('{') == s.count('}') and s.count('[') == s.count(']')
`,
      },
      {
        id: "off_by_one",
        label: "Off-by-One / Boundary (Misses remaining open brackets)",
        code: `def is_valid(s: str) -> bool:
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            if not stack or stack.pop() != mapping[char]:
                return False
        else:
            stack.append(char)
    return True  # Bug: returns True without verifying len(stack) == 0
`,
      },
    ],
    sampleTestCases: [
      { input: 's = "()"', expected: "True" },
      { input: 's = "()[]{}"', expected: "True" },
      { input: 's = "(]"', expected: "False" },
      { input: 's = "([)]"', expected: "False" },
      { input: 's = "{[]}"', expected: "True" },
    ],
  },
  binary_search: {
    id: "binary_search",
    title: "Binary Search",
    category: "Logarithmic Search",
    difficulty: "Easy",
    prompt:
      "Implement binary search to find the index of a target integer in a sorted list of unique integers. Return the index if found, or -1 if the target is not present in the list.",
    entrypoint: "binary_search",
    starterCode: `def binary_search(nums: list[int], target: int) -> int:
    # Write your solution here
    pass
`,
    canonicalSolution: `def binary_search(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
`,
    buggyVariants: [
      {
        id: "off_by_one",
        label: "Off-by-One Bug Variant (left < right)",
        code: `def binary_search(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left < right:  # Bug: misses single element or final check
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
`,
      },
    ],
    sampleTestCases: [
      { input: "nums = [1, 2, 3, 4, 5], target = 3", expected: "2" },
      { input: "nums = [1, 2, 3, 4, 5], target = 1", expected: "0" },
      { input: "nums = [1, 2, 3, 4, 5], target = 5", expected: "4" },
      { input: "nums = [1, 2, 3, 4, 5], target = 6", expected: "-1" },
      { input: "nums = [], target = 1", expected: "-1" },
    ],
  },
  longest_substring: {
    id: "longest_substring",
    title: "Longest Substring Without Repeating Characters",
    category: "Sliding Window",
    difficulty: "Medium",
    prompt:
      "Given a string s, find the length of the longest substring without duplicate characters.",
    entrypoint: "length_of_longest_substring",
    starterCode: `def length_of_longest_substring(s: str) -> int:
    # Write your solution here
    pass
`,
    canonicalSolution: `def length_of_longest_substring(s: str) -> int:
    char_index_map = {}
    max_len = 0
    left = 0
    for right, char in enumerate(s):
        if char in char_index_map and char_index_map[char] >= left:
            left = char_index_map[char] + 1
        char_index_map[char] = right
        max_len = max(max_len, right - left + 1)
    return max_len
`,
    buggyVariants: [
      {
        id: "wrong_data_structure",
        label: "Wrong Data Structure (Set-reset drops earlier valid window)",
        code: `def length_of_longest_substring(s: str) -> int:
    seen = set()
    max_len = 0
    for char in s:
        if char in seen:
            seen = {char}  # Bug: resetting window completely loses overlapping substrings like 'dvdf'
        else:
            seen.add(char)
        max_len = max(max_len, len(seen))
    return max_len
`,
      },
      {
        id: "off_by_one",
        label: "Off-by-One Length (right - left instead of right - left + 1)",
        code: `def length_of_longest_substring(s: str) -> int:
    char_index_map = {}
    max_len = 0
    left = 0
    for right, char in enumerate(s):
        if char in char_index_map and char_index_map[char] >= left:
            left = char_index_map[char] + 1
        char_index_map[char] = right
        max_len = max(max_len, right - left)  # Bug: off-by-one misses +1
    return max_len
`,
      },
    ],
    sampleTestCases: [
      { input: 's = "abcabcbb"', expected: "3" },
      { input: 's = "bbbbb"', expected: "1" },
      { input: 's = "pwwkew"', expected: "3" },
      { input: 's = "dvdf"', expected: "3" },
      { input: 's = ""', expected: "0" },
    ],
  },
  merge_two_sorted_lists: {
    id: "merge_two_sorted_lists",
    title: "Merge Two Sorted Lists",
    category: "Two Pointers & Arrays",
    difficulty: "Easy",
    prompt:
      "You are given two sorted integer lists list1 and list2. Merge the two lists into one sorted list and return it.",
    entrypoint: "merge_two_lists",
    starterCode: `def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:
    # Write your solution here
    pass
`,
    canonicalSolution: `def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:
    i, j = 0, 0
    result = []
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    result.extend(list2[j:])
    return result
`,
    buggyVariants: [
      {
        id: "edge_case",
        label: "Edge Case (Drops remainder of longer list)",
        code: `def merge_two_lists(list1: list[int], list2: list[int]) -> list[int]:
    i, j = 0, 0
    result = []
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    # Bug: forgets result.extend(...) when lists are unequal length
    return result
`,
      },
    ],
    sampleTestCases: [
      { input: "list1 = [1, 2, 4], list2 = [1, 3, 4]", expected: "[1, 1, 2, 3, 4, 4]" },
      { input: "list1 = [], list2 = []", expected: "[]" },
      { input: "list1 = [], list2 = [0]", expected: "[0]" },
      { input: "list1 = [5], list2 = [1, 2, 3]", expected: "[1, 2, 3, 5]" },
    ],
  },
};
