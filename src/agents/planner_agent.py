"""
PlannerAgent decides if a coding problem description is ambiguous enough to require clarification.
Heuristics are intentionally simple for prototype purposes.
"""

from dataclasses import dataclass
from typing import Tuple


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

    def assess(self, task_name: str, description: str) -> PlannerDecision:
        lower = description.lower()
        if any(tok in lower for tok in self.VAGUE_TOKENS):
            return PlannerDecision(True, "Detected vague wording.")
        if "factorial" in lower and "negative" not in lower:
            return PlannerDecision(True, "Factorial task lacks negative input spec.")
        if "csv" in lower and ("quote" not in lower and "embedded" not in lower):
            return PlannerDecision(True, "CSV parsing task lacks quoted comma specification.")
        return PlannerDecision(False, "No ambiguity detected by heuristics.")