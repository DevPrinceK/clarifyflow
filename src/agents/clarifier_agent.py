"""
ClarifyAgent uses a (mock) ClarifyCoder module to obtain clarification questions and
simulates developer answers.
"""
from typing import Dict, List
from src.clarifycoder.mock import ClarifyCoderMock


class ClarifyAgent:
    def __init__(self):
        self.clarifycoder = ClarifyCoderMock()

    def clarify(self, task_name: str, description: str) -> Dict[str, str]:
        """
        Returns a dict of clarification question -> answer (simulated).
        """
        questions: List[str] = self.clarifycoder.get_questions(task_name, description)
        answers: Dict[str, str] = {}
        for q in questions:
            # Simulated developer answers (hardcoded for prototype)
            if task_name == "factorial":
                ans = "Return None for negative inputs instead of raising errors."
            elif task_name == "parse_csv_line":
                ans = "Treat commas inside double quotes as part of the field; strip surrounding quotes and trim whitespace."
            else:
                ans = "Default: follow Pythonic conventions."
            answers[q] = ans
        return answers