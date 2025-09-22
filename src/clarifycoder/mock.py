"""
Mock ClarifyCoder component that returns deterministic clarification questions.
"""
from typing import List


class ClarifyCoderMock:
    def get_questions(self, task_name: str, description: str) -> List[str]:
        if task_name == "factorial":
            return ["Should the function handle negative numbers?"]
        if task_name == "parse_csv_line":
            return ["Should commas inside double quotes be treated as separators?"]
        return ["Any edge cases to consider?"]