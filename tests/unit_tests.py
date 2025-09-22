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
            {"input": [-3], "expected": None},  # Clarified behavior
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
}