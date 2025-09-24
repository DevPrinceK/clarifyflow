# ClarifyFlow Prototype

A minimal Python prototype demonstrating an agentic coding pipeline with clarification-aware code generation.

## Components

1. PlannerAgent (src/agents/planner.py)  
   Heuristically detects ambiguity (missing negative handling, CSV quoting, or vague terms).

2. ClarifyAgent (src/agents/clarify.py)  
   Retrieves clarification questions from a mock ClarifyCoder and simulates developer answers.

3. CoderAgent (src/agents/coder.py)  
   Generates deterministic Python code strings. Clarified path produces more robust implementations.

4. VerifierAgent (src/agents/verifier.py)  
   Dynamically executes generated code and runs task-specific tests.

5. Orchestrator (src/pipeline.py)  
   Runs each task twice: baseline (no clarification) and ClarifyFlow (with clarification if needed).

## Tasks & Tests

Defined in tests/unit_tests.py:

- factorial: Clarified behavior returns None for negative inputs (baseline raises).
- parse_csv_line: Clarified version supports quoted commas and trimming.

## Setup

Python 3.9+ recommended.

Core prototype has no hard dependency on external LLM libraries. To enable real API calls:

Optional dependencies:
- `openai` (for planning & coding when flags enabled)
- `google-generativeai` (for Gemini clarification questions)

```bash
python -m venv .venv
".venv\\Scripts\\activate"  # Windows PowerShell
pip install --upgrade pip
pip install openai google-generativeai  # optional
```

Environment variables (only needed if using LLM calls):
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- Optionally override models via `OPENAI_MODEL`, `GEMINI_MODEL`.

Feature toggles (either CLI flags or env vars):
- Planner uses OpenAI: `--use-openai-planner` or `CLARIFYFLOW_USE_OPENAI_PLANNER=1`
- Clarifier uses Gemini: `--use-gemini` or `CLARIFYFLOW_USE_GEMINI_CLARIFIER=1`
- Coder uses OpenAI: `--use-openai-coder` or `CLARIFYFLOW_USE_OPENAI_CODER=1`

## Run Pipeline

All tasks, heuristic only:
```bash
python -m src.pipeline
```

Select specific tasks & export JSON summary:
```bash
python -m src.pipeline --tasks factorial parse_csv_line --json run_summary.json
```

Enable all LLM augmentations (requires API keys set):
```bash
python -m src.pipeline --use-openai-planner --use-gemini --use-openai-coder --json runs_llm.json
```

JSON file schema (top-level keys):
```json
{
   "generated_at": "2025-09-23T12:00:00Z",
   "openai_planner": true,
   "gemini_clarifier": true,
   "openai_coder": true,
   "runs": [
      {
         "task": "factorial",
         "description": "...",
         "planner_decision": {"needs_clarification": true, "reason": "..."},
         "clarifications": {"Question": "Answer"},
         "baseline": {"passed": 2, "total": 3, "results": [{"name": "factorial::case_1", "passed": true, "detail": ""}]},
         "clarifyflow": {"passed": 3, "total": 3, "results": [...]},
         "improvement": 1
      }
   ]
}
```

## Example Output (abridged)

```
================================================================================
Task: factorial
Description: Implement factorial(n) returning n! for a non-negative integer n.

--- Baseline Path ---
[FAIL] factorial::case_3 - Exception: Negative not supported in baseline ...
Baseline summary: 2/3 passed

--- ClarifyFlow Path ---
Planner decision: needs_clarification=True reason=Factorial task lacks negative input spec.
Clarifications collected:
  Q: Should the function handle negative numbers?
  A: Return None for negative inputs instead of raising errors.
[PASS] factorial::case_1
[PASS] factorial::case_2
[PASS] factorial::case_3
ClarifyFlow summary: 3/3 passed
Improvement: +1 tests

================================================================================
Task: parse_csv_line
Description: Implement parse_csv_line(line) to split a CSV line into fields.

--- Baseline Path ---
[FAIL] parse_csv_line::case_1 - Expected=['a', 'b,c', 'd'] Got=['a', '"b', 'c"', 'd']
[FAIL] parse_csv_line::case_2 - Expected=['x, y', 'z'] Got=['  "x', ' y" ', 'z ']
Baseline summary: 0/2 passed

--- ClarifyFlow Path ---
Planner decision: needs_clarification=True reason=CSV parsing task lacks quoted comma specification.
Clarifications collected:
  Q: Should commas inside double quotes be treated as separators?
  A: Treat commas inside double quotes as part of the field; strip surrounding quotes and trim whitespace.
[PASS] parse_csv_line::case_1
[PASS] parse_csv_line::case_2
ClarifyFlow summary: 2/2 passed
Improvement: +2 tests
```

## Extending

Add new tasks in `tests/unit_tests.py` and update `CoderAgent` with generation templates (or rely on LLM path). When adding a new task for LLM usage, ensure the generated function name matches the test spec.

## License

MIT (see LICENSE).