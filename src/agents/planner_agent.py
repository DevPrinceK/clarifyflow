"""
PlannerAgent decides if a coding problem description is ambiguous enough to require clarification.
Heuristics are intentionally simple for prototype purposes.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import os

try:
    from llm.openai import plan_task as _openai_plan_task  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover - soft failure
    _OPENAI_AVAILABLE = False


@dataclass
class PlannerDecision:
    needs_clarification: bool
    reason: str


class PlannerAgent:
    """
    Determines whether a task needs clarification.
    Heuristics:
      - factorial task missing 'negative' handling mention
      - csv parsing missing mention of quotes or embedded commas
      - presence of vague words: 'maybe', 'possibly', 'might'
    """

    VAGUE_TOKENS = {"maybe", "possibly", "might", "ambiguous"}

    def __init__(self, use_llm: Optional[bool] = None):
        """Create a planner.

        use_llm: if True, attempt to augment heuristic decision using OpenAI (plan_task).
                 If None, will read CLARIFYFLOW_USE_OPENAI_PLANNER env var ("1"/"true").
        """
        if use_llm is None:
            env_flag = os.getenv("CLARIFYFLOW_USE_OPENAI_PLANNER", "false").lower()
            use_llm = env_flag in {"1", "true", "yes", "on"}
        self.use_llm = use_llm and _OPENAI_AVAILABLE

    def assess(self, task_name: str, description: str) -> PlannerDecision:
        lower = description.lower()
        if any(tok in lower for tok in self.VAGUE_TOKENS):
            return PlannerDecision(True, "Detected vague wording.")
        if "factorial" in lower and "negative" not in lower:
            return PlannerDecision(True, "Factorial task lacks negative input spec.")
        if "csv" in lower and ("quote" not in lower and "embedded" not in lower):
            return PlannerDecision(True, "CSV parsing task lacks quoted comma specification.")
        if "anagram" in lower and ("case" not in lower and "space" not in lower and "whitespace" not in lower):
            return PlannerDecision(True, "Anagram task lacks case/whitespace rules.")
        if ("format_date" in lower or ("format" in lower and "date" in lower)) and ("yyyy" not in lower and "iso" not in lower and "yyyy-mm-dd" not in lower):
            return PlannerDecision(True, "Date formatting task lacks target output format (e.g., YYYY-MM-DD).")
        # If heuristics say no, optionally consult LLM for latent ambiguities
        if self.use_llm:
            try:
                llm_feedback = _openai_plan_task(description)
                # Very light signal extraction: if response has at least one question mark, treat as ambiguous.
                if "?" in llm_feedback:
                    return PlannerDecision(True, "LLM suggested potential ambiguities.")
            except Exception:  # pragma: no cover
                pass
        return PlannerDecision(False, "No ambiguity detected by heuristics.")