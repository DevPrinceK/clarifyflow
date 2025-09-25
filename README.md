# ClarifyFlow Prototype

A minimal Python prototype demonstrating an agentic coding pipeline with clarification-aware code generation.

## Components

1. PlannerAgent (src/agents/planner_agent.py)  
   Heuristically detects ambiguity (missing negative handling, CSV quoting, or vague terms).

2. ClarifyAgent (src/agents/clarifier_agent.py)  
   Retrieves clarification questions from a mock ClarifyCoder and simulates developer answers.
   - Optional: reads/writes a JSON-backed Knowledge Base (`.clarifyflow/kb.json`).
   - Optional: interactive mode lets you type answers, stored with provenance=user.

3. CoderAgent (src/agents/coder_agent.py)  
   Generates deterministic Python code strings. Clarified path produces more robust implementations.

4. VerifierAgent (src/agents/verifier_agent.py)  
   Dynamically executes generated code and runs task-specific tests.

5. Orchestrator (src/pipeline.py)  
   Runs each task twice: baseline (no clarification) and ClarifyFlow (with clarification if needed).

6. LLM Adapters (llm/openai.py, llm/gemini.py)
   Optional connectors used by PlannerAgent/ClarifyAgent/CoderAgent when enabled.
   - OpenAI (llm/openai.py): used for planning and code generation when flags/env are set. Reads `OPENAI_API_KEY` and supports `OPENAI_MODEL`.
   - Gemini (llm/gemini.py): used by ClarifyAgent to propose clarification questions. Reads `GEMINI_API_KEY` and supports `GEMINI_MODEL`.
   - Both adapters are optional; if SDKs or keys are missing, the code falls back to deterministic stubs. Toggle via CLI flags or env vars (see Setup).

## Tasks & Tests

Defined in tests/unit_tests.py:

- factorial: Clarified behavior returns None for negative inputs (baseline raises).
- parse_csv_line: Clarified version supports quoted commas and trimming.
- is_anagram: Case/whitespace-insensitive anagram check.
- format_date: Normalize common date formats to YYYY-MM-DD in ClarifyFlow mode.

## Setup

Python 3.10+ recommended.

Clone the repository:

```bash
git clone https://github.com/DevPrinceK/clarifyflow.git
cd clarifyflow
```

Dependencies:
- `openai` (for planning & coding when flags enabled)
- `google-generativeai` (for Gemini clarification questions)

```bash
python -m venv .venv
cd .\venv\ # Windows PowerShell
.\Scripts\activate
pip install --upgrade pip
pip install openai google-generativeai # install deps manually
---or---
pip install -r requirements.txt # install from requirements file
```

Create and populate a .env file (for API keys & flags):

- The pipeline auto-loads environment variables from either project root `.env` (preferred) or `src/.env`.
- Do NOT commit real keys. Keep `.env` out of version control.

```
# API keys (required only if enabling LLMs)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optionally override models
OPENAI_MODEL=your-model-name
GEMINI_MODEL=your-model-name

# Feature flags (optional)
CLARIFYFLOW_USE_OPENAI_PLANNER=1
CLARIFYFLOW_USE_GEMINI_CLARIFIER=1
CLARIFYFLOW_USE_OPENAI_CODER=1

# Knowledge Base and interactivity (optional)
CLARIFYFLOW_USE_KB=1
CLARIFYFLOW_INTERACTIVE_CLARIFY=0

# Reduce import noise from missing SDKs (0/1)
CLARIFYFLOW_VERBOSE_IMPORTS=0

# Optional: custom KB path
# CLARIFYFLOW_KB_PATH=.clarifyflow/kb.json
```

Feature toggles (either CLI flags or env vars):
- Planner uses OpenAI: `--use-openai-planner` or `CLARIFYFLOW_USE_OPENAI_PLANNER=1`
- Clarifier uses Gemini: `--use-gemini` or `CLARIFYFLOW_USE_GEMINI_CLARIFIER=1`
- Coder uses OpenAI: `--use-openai-coder` or `CLARIFYFLOW_USE_OPENAI_CODER=1`
 - Interactive clarify: `--interactive-clarify` or `CLARIFYFLOW_INTERACTIVE_CLARIFY=1`
 - Use KB for caching clarifications: default ON; override with `CLARIFYFLOW_USE_KB=0`

## Run Pipeline

All tasks, heuristic only:
```bash
python -m src.pipeline
```

Alternative execution (script style):
```bash
python src/pipeline.py
```

Select specific tasks & export JSON summary:
```bash
python -m src.pipeline --tasks factorial parse_csv_line --json run_summary.json
```

Enable all LLM augmentations (requires API keys set):
```bash
python -m src.pipeline --use-openai-planner --use-gemini --use-openai-coder --json runs_llm.json
```

## LLM integrations

- OpenAI (planning and coding): `llm/openai.py`
   - Uses chat completions with temperature 0 for reproducibility.
   - Falls back to a deterministic stub (prints a stub note) if the package or API key is unavailable.
- Gemini (clarification questions): `llm/gemini.py`
   - Generates clarification questions only.
   - Falls back to a heuristic stub if the package or API key is unavailable.
- Clarifier resolution order: KnowledgeBase → Gemini (if enabled) → Mock (`src/clarifycoder/mock.py`).
- Planner can optionally consult OpenAI to flag latent ambiguities.

JSON file schema (top-level keys):
```json
{
   "generated_at": "2025-09-23T12:00:00Z",
   "openai_planner": true,
   "gemini_clarifier": true,
   "openai_coder": true,
   "interactive_clarify": false,
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

## Knowledge Base (KB)

- Location: `.clarifyflow/kb.json` (override via `CLARIFYFLOW_KB_PATH`).
- Structure: keyed by task and a hash of the description; stores `q_and_a`, `provenance`, `updated_at`, and a short `description_preview`.
- KB is read first; if present, questions are skipped and answers are reused.

Admin CLI:

- List entries for all tasks (or a specific task):
   - `python -m src.pipeline --kb-list`
   - `python -m src.pipeline --kb-list factorial`
- Clear entries for all tasks (or a specific task):
   - `python -m src.pipeline --kb-clear`
   - `python -m src.pipeline --kb-clear parse_csv_line`

Interactive clarify (store user answers):

- `python -m src.pipeline --interactive-clarify --tasks factorial`
- You'll be prompted per question; non-empty answers are stored in KB with `provenance=user`.

## Reproducibility notes

- Deterministic by default when LLMs are off (templates only).
- With LLMs enabled, temperature=0 is used; outputs are still subject to API-side variation.
- The pipeline prints explicit PASS/FAIL per test case, plus a baseline vs ClarifyFlow summary.

## Security notes

- Do not commit real API keys. Prefer environment variables or a local untracked `.env`.
- The VerifierAgent executes code in-process (not sandboxed).
- If you use a local `.env`, ensure it is git-ignored.

## Requirements

- Minimal run (no LLMs): standard library only.
- Optional LLMs: `pip install openai google-generativeai`.
- The provided `requirements.txt` may contain extras; install only what you need.

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

**Feel free to open a PR.**

## License

MIT (see LICENSE).