"""
ClarifyAgent uses a (mock) ClarifyCoder module to obtain clarification questions and
simulates developer answers.
"""
from typing import Dict, List, Optional
import os
from src.clarifycoder.mock import ClarifyCoderMock
from src.clarifycoder.kb import KnowledgeBase

try:
    from llm.gemini import generate_clarification_questions  # type: ignore
    _GEMINI_AVAILABLE = True
except Exception:  # pragma: no cover
    _GEMINI_AVAILABLE = False


class ClarifyAgent:
    def __init__(self, use_gemini: Optional[bool] = None, use_kb: Optional[bool] = None, use_interactive: Optional[bool] = None):
        if use_gemini is None:
            env_flag = os.getenv("CLARIFYFLOW_USE_GEMINI_CLARIFIER", "false").lower()
            use_gemini = env_flag in {"1", "true", "yes", "on"}
        self.use_gemini = use_gemini and _GEMINI_AVAILABLE
        if use_kb is None:
            kb_flag = os.getenv("CLARIFYFLOW_USE_KB", "true").lower()  # default on
            use_kb = kb_flag in {"1", "true", "yes", "on"}
        self.use_kb = use_kb
        if use_interactive is None:
            inter_flag = os.getenv("CLARIFYFLOW_INTERACTIVE_CLARIFY", "false").lower()
            use_interactive = inter_flag in {"1", "true", "yes", "on"}
        self.use_interactive = bool(use_interactive)
        self.kb = KnowledgeBase() if self.use_kb else None
        self.clarifycoder = ClarifyCoderMock()

    def clarify(self, task_name: str, description: str) -> Dict[str, str]:
        """
        Returns a dict of clarification question -> answer (simulated).
        """
        # 1) Try KB first
        if self.kb:
            cached = self.kb.get(task_name, description)
            if cached:
                return cached

        # 2) Generate fresh questions via Gemini or mock
        if self.use_gemini:
            try:
                questions = generate_clarification_questions(task_name, description)
            except Exception:  # pragma: no cover
                questions = self.clarifycoder.get_questions(task_name, description)
        else:
            questions = self.clarifycoder.get_questions(task_name, description)
        answers: Dict[str, str] = {}
        user_provided_any = False
        for q in questions:
            # Interactive prompt branch
            if self.use_interactive:
                try:
                    user_in = input(f"Clarification needed for '{task_name}'.\nQ: {q}\nEnter your answer (leave blank to skip): ")
                except EOFError:
                    user_in = ""
                if user_in and user_in.strip():
                    answers[q] = user_in.strip()
                    user_provided_any = True
                    continue
            # Non-interactive or skipped: use simulated defaults
            if task_name == "factorial":
                ans = "Return None for negative inputs instead of raising errors."
            elif task_name == "parse_csv_line":
                ans = "Treat commas inside double quotes as part of the field; strip surrounding quotes and trim whitespace."
            else:
                ans = "Default: follow Pythonic conventions."
            answers[q] = ans
        # 3) Save to KB
        if self.kb and answers:
            try:
                provenance = "user" if user_provided_any else "mock"
                self.kb.put(task_name, description, answers, provenance=provenance)
            except Exception:
                pass
        return answers