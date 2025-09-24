"""
OpenAI client utilities for agentic tasks (planning, coding, verification assistance).
Falls back to a deterministic stub if the OpenAI package or API key is unavailable.

Environment:
  OPENAI_API_KEY - required for real calls.

Usage:
  response_text = openai_chat([
      {"role": "system", "content": "You are a helpful planner."},
      {"role": "user", "content": "Task: implement factorial edge cases."}
  ])
"""
from __future__ import annotations
import os
from typing import List, Dict, Optional, Any

try:
    from openai import OpenAI  # openai>=1.0.0 style
    _OPENAI_AVAILABLE = True
except Exception as e:
    # Suppress noisy import logs unless explicitly requested
    if os.getenv("CLARIFYFLOW_VERBOSE_IMPORTS", "").lower() in {"1", "true", "yes", "on"}:
        print(f"OpenAI import error: {e}")
    _OPENAI_AVAILABLE = False

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class OpenAIUnavailable(RuntimeError):
    pass


def _stub_response(messages: List[Dict[str, str]]) -> str:
    # Simple echo-style deterministic fallback.
    user_parts = [m["content"] for m in messages if m.get("role") == "user"]
    last = user_parts[-1] if user_parts else ""
    return f"[STUB OpenAI] Unable to call API. Echoing last user message truncated: {last[:160]}"


def openai_chat(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_output_tokens: int = 800,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Perform a chat completion. Returns assistant text.

    messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not (_OPENAI_AVAILABLE and key):
        print("[STUB OpenAI] Unable to call API. Falling back to stub response.")
        return _stub_response(messages)

    try:
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_output_tokens,
            **kwargs,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[STUB OpenAI] Exception during API call. Falling back to stub response. Error: {e}")
        return f"[STUB OpenAI Exception] {e}"


def plan_task(problem_description: str) -> str:
    """
    Example helper: ask model for potential ambiguities.
    """
    messages = [
        {"role": "system", "content": "You identify ambiguities in software task descriptions succinctly."},
        {"role": "user", "content": f"Analyze this task for ambiguities:\n\n{problem_description}\n\nList potential clarification points."}
    ]
    return openai_chat(messages)


def generate_code(spec: str, clarifications: Optional[dict] = None) -> str:
    """
    Example helper to produce code (not currently wired into pipeline, kept for future extension).
    """
    clar_block = ""
    if clarifications:
        clar_items = "\n".join(f"- {q} -> {a}" for q, a in clarifications.items())
        clar_block = f"\nClarifications:\n{clar_items}\n"
    messages = [
        {"role": "system", "content": "You write concise, clear Python functions with docstrings."},
        {"role": "user", "content": f"Write Python code for:\n{spec}{clar_block}"}
    ]
    return openai_chat(messages)


__all__ = [
    "openai_chat",
    "plan_task",
    "generate_code",
    "OpenAIUnavailable",
]