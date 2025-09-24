"""ClarifyFlow Pipeline Orchestrator.

Runs each task twice:
    1. Baseline (no clarifications)
    2. ClarifyFlow (planner -> clarify -> coder -> verifier)

This file is intentionally made executable both via:
        python -m src.pipeline
and
        python src/pipeline.py

When executed directly as a script, Python sets ``sys.path[0]`` to the *src* folder
so the project root (its parent) is not automatically importable as a package prefix.
We therefore inject the parent directory into ``sys.path`` early so ``import src.*``
works in either invocation style.
"""
from typing import Dict, List, Any
import os, sys, argparse, json, datetime

# ---- Ensure project root on sys.path for direct script execution ----
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)


# ---- Minimal .env loader (no external dependency) ----
def _load_env_files():
    candidates = [
        os.path.join(_PROJECT_ROOT, ".env"),
        os.path.join(_PROJECT_ROOT, "src", ".env"),
    ]
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # don't override existing environment variables
                    if key and (key not in os.environ or os.environ.get(key) == ""):
                        os.environ[key] = value
        except Exception:
            # Silent fail on dotenv load
            pass

from src.agents.planner_agent import PlannerAgent
from src.agents.clarifier_agent import ClarifyAgent
from src.agents.coder_agent import CoderAgent
from src.agents.verifier_agent import VerifierAgent
from tests.unit_tests import TASK_SPECS
from src.clarifycoder.kb import KnowledgeBase


class ClarifyFlowPipeline:
    def __init__(self, use_openai_planner: bool | None = None, use_gemini: bool | None = None, use_openai_coder: bool | None = None, interactive_clarify: bool | None = None):
        self.planner = PlannerAgent(use_llm=use_openai_planner)
        self.clarifier = ClarifyAgent(use_gemini=use_gemini, use_kb=None, use_interactive=interactive_clarify)
        self.coder = CoderAgent(use_llm=use_openai_coder)
        self.verifier = VerifierAgent()
        self.run_records: List[Dict[str, Any]] = []  # accumulate JSON export entries

    def run_task(self, task_name: str, spec: Dict):
        description: str = spec["description"]
        function_name: str = spec["function"]
        tests: List[Dict] = spec["tests"]

        print("=" * 80) # Separator
        print(f"Task: {task_name}")
        print(f"Description: {description}")

        # Baseline path
        print("\n--- Baseline Path ---")
        baseline_code = self.coder.generate_code(task_name, description, clarifications=None)
        baseline_results = self.verifier.run_tests(
            baseline_code, task_name, tests, function_name
        )
        print("Baseline Code:\n" + baseline_code)
        for r in baseline_results:
            print(r)
        baseline_pass = sum(r.passed for r in baseline_results)
        print(f"Baseline summary: {baseline_pass}/{len(baseline_results)} passed")

    # ClarifyFlow path
        print("\n--- ClarifyFlow Path ---")
        decision = self.planner.assess(task_name, description)
        print(f"Planner decision: needs_clarification={decision.needs_clarification} reason={decision.reason}")

        clarifications = {}
        if decision.needs_clarification:
            clarifications = self.clarifier.clarify(task_name, description)
            print("Clarifications collected:")
            for q, a in clarifications.items():
                print(f"  Q: {q}\n  A: {a}")
        else:
            print("No clarifications requested.")

        clarified_code = self.coder.generate_code(task_name, description, clarifications or None)
        print("ClarifyFlow Code:\n" + clarified_code)
        clarified_results = self.verifier.run_tests(
            clarified_code, task_name, tests, function_name
        )
        for r in clarified_results:
            print(r)
        clarified_pass = sum(r.passed for r in clarified_results)
        print(f"ClarifyFlow summary: {clarified_pass}/{len(clarified_results)} passed")

        improvement = clarified_pass - baseline_pass
        print(f"Improvement: {'+' if improvement >=0 else ''}{improvement} tests\n")

        self.run_records.append({
            "task": task_name,
            "description": description,
            "planner_decision": {
                "needs_clarification": decision.needs_clarification,
                "reason": decision.reason,
            },
            "clarifications": clarifications,
            "baseline": {
                "passed": baseline_pass,
                "total": len(baseline_results),
                "results": [r.to_dict() for r in baseline_results],
            },
            "clarifyflow": {
                "passed": clarified_pass,
                "total": len(clarified_results),
                "results": [r.to_dict() for r in clarified_results],
            },
            "improvement": improvement,
        })

    def run_all(self):
        for task_name, spec in TASK_SPECS.items():
            self.run_task(task_name, spec)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClarifyFlow agentic coding pipeline")
    parser.add_argument("--tasks", nargs="*", default=[], help="Subset of tasks to run (default: all)")
    parser.add_argument("--json", dest="json_path", help="Write JSON summary to path")
    # Flags default to None so agents can fall back to environment variables when not set
    parser.add_argument("--use-openai-planner", dest="use_openai_planner", action="store_true", help="Use OpenAI for planner ambiguity augmentation")
    parser.add_argument("--no-use-openai-planner", dest="use_openai_planner", action="store_false", help="Disable OpenAI planner explicitly")
    parser.add_argument("--use-gemini", dest="use_gemini", action="store_true", help="Use Gemini for clarification questions")
    parser.add_argument("--no-use-gemini", dest="use_gemini", action="store_false", help="Disable Gemini clarifier explicitly")
    parser.add_argument("--use-openai-coder", dest="use_openai_coder", action="store_true", help="Use OpenAI for code generation")
    parser.add_argument("--no-use-openai-coder", dest="use_openai_coder", action="store_false", help="Disable OpenAI coder explicitly")
    parser.add_argument("--interactive-clarify", dest="interactive_clarify", action="store_true", help="Prompt for user answers to clarification questions and store them in KB (provenance=user)")
    # KB management
    parser.add_argument("--kb-list", nargs="?", const="__ALL__", metavar="TASK", help="List KB entries (optionally filter by task)")
    parser.add_argument("--kb-clear", nargs="?", const="__ALL__", metavar="TASK", help="Clear KB (optionally filter by task)")

    parser.set_defaults(use_openai_planner=None, use_gemini=None, use_openai_coder=None, interactive_clarify=None)
    return parser.parse_args(argv)


def main(argv: List[str] | None = None):
    _load_env_files()
    ns = parse_args(argv or sys.argv[1:])
    # KB management commands
    if ns.kb_list or ns.kb_clear:
        kb = KnowledgeBase()
        if ns.kb_list is not None:
            task = None if ns.kb_list == "__ALL__" else ns.kb_list
            listing = kb.list_entries(task)
            print(json.dumps(listing, indent=2))
        if ns.kb_clear is not None:
            task = None if ns.kb_clear == "__ALL__" else ns.kb_clear
            removed = kb.clear(task)
            print(f"Cleared {removed} KB entrie(s){' for task ' + task if task else ''}.")
        # If only KB operation(s) requested without tasks, exit early
        if not ns.tasks:
            return 0
    # If flags are None, agents will read environment variables
    pipeline = ClarifyFlowPipeline(
        use_openai_planner=ns.use_openai_planner,
        use_gemini=ns.use_gemini,
        use_openai_coder=ns.use_openai_coder,
        interactive_clarify=ns.interactive_clarify,
    )
    if ns.tasks:
        unknown = [t for t in ns.tasks if t not in TASK_SPECS]
        if unknown:
            print(f"Unknown tasks requested: {unknown}. Available: {list(TASK_SPECS.keys())}")
        selected = {k: v for k, v in TASK_SPECS.items() if k in ns.tasks}
        if not selected:
            print("No valid tasks selected; exiting.")
            return 1
        for name, spec in selected.items():
            pipeline.run_task(name, spec)
    else:
        pipeline.run_all()

    if ns.json_path:
        out = {
            "generated_at": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
            "openai_planner": ns.use_openai_planner,
            "gemini_clarifier": ns.use_gemini,
            "openai_coder": ns.use_openai_coder,
            "interactive_clarify": ns.interactive_clarify,
            "runs": pipeline.run_records,
        }
        with open(ns.json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"JSON summary written to {ns.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())