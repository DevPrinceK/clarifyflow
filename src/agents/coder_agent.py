"""
CoderAgent creates Python function source code strings based on task description and clarifications.
In a real system this would call an LLM. Here we use deterministic templates.
"""
from typing import Dict, Optional
import os
import ast
try:
    from llm.openai import generate_code as _openai_generate_code  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover
    _OPENAI_AVAILABLE = False


class CoderAgent:
    def __init__(self, use_llm: Optional[bool] = None):
        if use_llm is None:
            env_flag = os.getenv("CLARIFYFLOW_USE_OPENAI_CODER", "false").lower()
            use_llm = env_flag in {"1", "true", "yes", "on"}
        self.use_llm = use_llm and _OPENAI_AVAILABLE

    def generate_code(self, task_name: str, description: str, clarifications: Optional[Dict[str, str]]) -> str:
        clarified = clarifications is not None and len(clarifications) > 0
        if self.use_llm:
            # Build a spec description for the LLM; fallback to templates if it fails.
            spec = f"Task: {task_name}\nDescription: {description}\n" + (
                "Clarifications:\n" + "\n".join(f"- {q}: {a}" for q, a in clarifications.items()) if clarified and clarifications else ""
            )
            try:
                raw = _openai_generate_code(spec, clarifications if clarified else None)
                code = self._sanitize_llm_code(raw)
                # Validate function signature strictly via AST
                expected = self._expected_signature(task_name)
                if expected and not self._validate_signature(code, expected):
                    raise ValueError("LLM output failed signature validation")
                return code
            except Exception:
                pass  # revert to deterministic template
        if task_name == "factorial":
            return self._code_factorial(clarified, clarifications)
        if task_name == "parse_csv_line":
            return self._code_parse_csv_line(clarified, clarifications)
        if task_name == "is_anagram":
            return self._code_is_anagram(clarified, clarifications)
        raise ValueError(f"Unknown task: {task_name}")

    def _sanitize_llm_code(self, text: str) -> str:
        """Strip Markdown code fences and language tags, return plain Python code."""
        if not text:
            return text
        t = text.strip()
        # Extract code inside triple backticks if present
        if t.startswith("```"):
            # remove first fence line
            lines = t.splitlines()
            # drop first line like ```python or ```
            lines = lines[1:]
            # drop trailing fence if present
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            t = "\n".join(lines)
        # Also remove stray ``` occurrences
        t = t.replace("```python", "").replace("```py", "").replace("```", "")
        return t.strip()

    # ---- Signature validation helpers ----
    def _expected_signature(self, task_name: str):
        # map: task -> (function_name, arg_names_len)
        mapping = {
            "factorial": ("factorial", 1),
            "parse_csv_line": ("parse_csv_line", 1),
            "is_anagram": ("is_anagram", 2),
        }
        return mapping.get(task_name)

    def _validate_signature(self, code: str, expected: tuple) -> bool:
        try:
            tree = ast.parse(code)
        except Exception:
            return False
        fn_name, arg_count = expected
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == fn_name:
                # Count only positional args (excluding *args/**kwargs and self)
                pos_args = [a.arg for a in node.args.args]
                # allow optional type hints; ensure count matches
                return len(pos_args) == arg_count
        return False

    def _code_is_anagram(self, clarified: bool, clarifications: Optional[Dict[str, str]]) -> str:
        if not clarified:
            return self._header("is_anagram", False, None) + '''
def is_anagram(a: str, b: str) -> bool:
    """Baseline: case-insensitive and ignores spaces by removing whitespace and comparing sorted chars."""
    s1 = "".join(a.split()).lower()
    s2 = "".join(b.split()).lower()
    return sorted(s1) == sorted(s2)
'''
        return self._header("is_anagram", True, clarifications) + '''
def is_anagram(a: str, b: str) -> bool:
    """Clarified: ignore case and whitespace; treat only alphanumeric characters.
    This avoids punctuation affecting results (e.g., "Dormitory!" vs "Dirty room").
    """
    import string
    allowed = set(string.ascii_lowercase + string.digits)
    s1 = "".join(ch for ch in a.lower() if ch in allowed)
    s2 = "".join(ch for ch in b.lower() if ch in allowed)
    return sorted(s1) == sorted(s2)
'''

    def _header(self, task: str, clarified: bool, clarifications: Optional[Dict[str, str]]) -> str:
        clarif_block = ""
        if clarified and clarifications:
            clarif_lines = "\n".join([f"# Q: {q}\n# A: {a}" for q, a in clarifications.items()])
            clarif_block = f"\n# Clarifications Applied:\n{clarif_lines}\n"
        return (
            f"# Auto-generated solution for task: {task}\n"
            f"# Mode: {'ClarifyFlow' if clarified else 'Baseline'}\n"
            f"{clarif_block}"
        )

    def _code_factorial(self, clarified: bool, clarifications: Optional[Dict[str, str]]) -> str:
        if not clarified:
            return self._header("factorial", False, None) + """
def factorial(n: int) -> int:
    \"\"\"Compute factorial of n (assumes n is a non-negative integer).\"\"\"
    if n < 0:
        # Baseline: does not handle negative gracefully (will raise)
        raise ValueError("Negative not supported in baseline")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
"""
        return self._header("factorial", True, clarifications) + """
from typing import Optional

def factorial(n: int) -> Optional[int]:
    \"\"\"Compute factorial of n.
    Clarified behavior: return None for negative inputs instead of raising.
    Uses iterative multiplication to avoid recursion limits.
    \"\"\"
    if n < 0:
        return None
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
"""

    def _code_parse_csv_line(self, clarified: bool, clarifications: Optional[Dict[str, str]]) -> str:
        if not clarified:
            return self._header("parse_csv_line", False, None) + '''
def parse_csv_line(line: str):
    """Naive CSV parser: simply splits on commas (baseline)."""
    return [part for part in line.split(',')]
'''
        return self._header("parse_csv_line", True, clarifications) + '''
def parse_csv_line(line: str):
    """Parse a single CSV line with support for:
    - Quoted fields using double quotes
    - Commas inside quotes retained within field
    - Surrounding quotes removed
    - Leading/trailing whitespace outside quotes trimmed
    Clarified behavior per developer answers.
    """
    fields = []
    buf = []
    in_quotes = False
    i = 0
    line_len = len(line)
    while i < line_len:
        ch = line[i]
        if ch == '"':
            # Toggle quote state (no escape handling for prototype)
            in_quotes = not in_quotes
            i += 1
            continue
        if ch == ',' and not in_quotes:
            field = "".join(buf).strip()
            fields.append(field)
            buf = []
        else:
            buf.append(ch)
        i += 1
    # last field
    field = "".join(buf).strip()
    fields.append(field)
    return fields
'''