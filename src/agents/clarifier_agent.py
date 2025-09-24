"""
ClarifyAgent uses a (mock) ClarifyCoder module to obtain clarification questions and
simulates developer answers.
"""
from typing import Dict, List, Optional
import os
from src.clarifycoder.mock import ClarifyCoderMock

try:
    from llm.gemini import generate_clarification_questions  # type: ignore
    _GEMINI_AVAILABLE = True
except Exception:  # pragma: no cover
    _GEMINI_AVAILABLE = False


class ClarifyAgent:
    def __init__(self, use_gemini: Optional[bool] = None):
        if use_gemini is None:
            env_flag = os.getenv("CLARIFYFLOW_USE_GEMINI_CLARIFIER", "false").lower()
            use_gemini = env_flag in {"1", "true", "yes", "on"}
        self.use_gemini = use_gemini and _GEMINI_AVAILABLE
        self.clarifycoder = ClarifyCoderMock()

    def clarify(self, task_name: str, description: str) -> Dict[str, str]:
        """
        Returns a dict of clarification question -> answer (simulated).
        """
        if self.use_gemini:
            try:
                questions = generate_clarification_questions(task_name, description)
            except Exception:  # pragma: no cover
                questions = self.clarifycoder.get_questions(task_name, description)
        else:
            questions = self.clarifycoder.get_questions(task_name, description)
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