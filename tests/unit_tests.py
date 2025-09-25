"""
Defines task specifications and tests consumed by pipeline.
Each task spec:
  description: textual problem statement
  function: function name expected in generated code
  tests: list of {input: [...], expected: value}
"""
TASK_SPECS = {
    "factorial": {
        "description": "Implement factorial(n) returning n! for a non-negative integer n.",
        "function": "factorial",
        "tests": [
            {"input": [0], "expected": 1},
            {"input": [5], "expected": 120},
            {"input": [-3], "expected": None},  # for Clarified behavior
        ],
    },
    "parse_csv_line": {
        "description": "Implement parse_csv_line(line) to split a CSV line into fields.",
        "function": "parse_csv_line",
        "tests": [
            {"input": ['a,"b,c",d'], "expected": ["a", "b,c", "d"]},
            {"input": ['  "x, y" ,z '], "expected": ["x, y", "z"]},
        ],
    },
    "is_anagram": {
        "description": "Implement is_anagram(a, b) to return True if two strings are anagrams. Ignore case and whitespace.",
        "function": "is_anagram",
        "tests": [
            {"input": ["listen", "silent"], "expected": True},
            {"input": ["Triangle", "Integral"], "expected": True},
            {"input": ["Dormitory", "Dirty room"], "expected": True},
            {"input": ["Hello", "World"], "expected": False},
            # Clarified behavior: ignore spaces & case; treat only letters by default
        ],
    },
    "format_date": {
        "description": "Implement format_date(s) to normalize common date strings to YYYY-MM-DD.",
        "function": "format_date",
        "tests": [
            {"input": ["2024/01/09"], "expected": "2024-01-09"},
            {"input": ["01-09-2024"], "expected": "2024-01-09"},  # MM-DD-YYYY
            {"input": ["9 Jan 2024"], "expected": "2024-01-09"},
            {"input": ["Jan 9, 2024"], "expected": "2024-01-09"},
        ],
    },
}