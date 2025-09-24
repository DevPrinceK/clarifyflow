"""
Gemini client specialized for generating clarification questions (ClarifyCoder proxy).

Environment:
  GEMINI_API_KEY - required for real calls.

Falls back to heuristic / template questions if the google.generativeai
package or API key is missing.

Primary entrypoint:
  generate_clarification_questions(task_name, description, max_questions=3)
"""
from __future__ import annotations
import os
from typing import List, Any

try:
    from importlib import import_module
    genai: Any = import_module("google.generativeai")
    _GEMINI_AVAILABLE = True
except Exception as e:
    if os.getenv("CLARIFYFLOW_VERBOSE_IMPORTS", "").lower() in {"1", "true", "yes", "on"}:
        print(f"Gemini import error: {e}")
    genai = None
    _GEMINI_AVAILABLE = False

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _heuristic_questions(task_name: str, description: str) -> List[str]:
    desc_lower = description.lower()
    q: List[str] = []
    if "factorial" in desc_lower:
        q.append("Should negative inputs be handled gracefully (e.g., return None) or raise an error?")
        q.append("Is recursion allowed or should an iterative approach be preferred?")
    if "csv" in desc_lower:
        q.append("Should commas inside quoted fields be preserved instead of splitting?")
        q.append("Should surrounding quotes be stripped from fields?")
    if not q:
        q.append("What edge cases or constraints (size limits, invalid inputs) should be considered?")
    return q


def generate_clarification_questions(
    task_name: str,
    description: str,
    max_questions: int = 3,
    api_key: str | None = None,
) -> List[str]:
    """
    Returns a list of clarifying questions produced by Gemini or heuristics fallback.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")

    if not (_GEMINI_AVAILABLE and key):
        print("[STUB Gemini] Unable to call API. Falling back to heuristics.")
        # Fallback
        return _heuristic_questions(task_name, description)[:max_questions]

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(DEFAULT_MODEL)
        prompt = (
            "You are a senior engineer acting as a clarification assistant.\n"
            "Given the software task below, produce ONLY clarification questions (no answers), "
            "each on a new line, prioritized by impact. Avoid redundancy.\n\n"
            f"Task Name: {task_name}\nDescription:\n{description}\n\nQuestions:"
        )
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", "") or ""
        lines = [ln.strip("- ").strip() for ln in text.splitlines()]
        questions = [ln for ln in lines if ln and not ln.lower().startswith("question")]
        if not questions:
            questions = _heuristic_questions(task_name, description)
        # Deduplicate while preserving order
        seen = set()
        ordered: List[str] = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                ordered.append(q)
        return ordered[:max_questions]
    except Exception as e:
        print(f"[STUB Gemini] Exception during API call. Falling back to heuristics. Error: {e}")
        return _heuristic_questions(task_name, description)[:max_questions]


__all__ = ["generate_clarification_questions"]