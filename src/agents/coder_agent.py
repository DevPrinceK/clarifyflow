"""
CoderAgent creates Python function source code strings based on task description and clarifications.
In a real system this would call an LLM. Here we use deterministic templates.
"""
from typing import Dict, Optional


class CoderAgent:
    def generate_code(self, task_name: str, description: str, clarifications: Optional[Dict[str, str]]) -> str:
        clarified = clarifications is not None and len(clarifications) > 0
        if task_name == "factorial":
            return self._code_factorial(clarified, clarifications)
        if task_name == "parse_csv_line":
            return self._code_parse_csv_line(clarified, clarifications)
        raise ValueError(f"Unknown task: {task_name}")

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
            return self._header("parse_csv_line", False, None) + r"""
def parse_csv_line(line: str):
    \"\"\"Naive CSV parser: simply splits on commas (baseline).\"\"\"
    return [part for part in line.split(',')]
"""
        return self._header("parse_csv_line", True, clarifications) + r"""
def parse_csv_line(line: str):
    \"\"\"Parse a single CSV line with support for:
    - Quoted fields using double quotes
    - Commas inside quotes retained within field
    - Surrounding quotes removed
    - Leading/trailing whitespace outside quotes trimmed
    Clarified behavior per developer answers.
    \"\"\"
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
"""