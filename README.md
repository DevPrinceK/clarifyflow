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

```bash
python -m venv .venv
# On Linux/macOS: source .venv/bin/activate
# On Windows: .venv\\Scripts\\activate
pip install --upgrade pip
# (No external dependencies required)
```

## Run Pipeline

```bash
python -m src.pipeline
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

Add new tasks in tests/unit_tests.py and update CoderAgent with generation templates.

## License

MIT (see LICENSE).