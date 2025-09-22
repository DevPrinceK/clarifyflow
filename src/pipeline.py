"""
Orchestrator for ClarifyFlow prototype.
Runs each task twice:
  1. Baseline (no clarifications)
  2. ClarifyFlow (planner -> clarify -> coder -> verifier)
"""
from typing import Dict, List
from src.agents.planner_agent import PlannerAgent
from src.agents.clarifier_agent import ClarifyAgent
from src.agents.coder_agent import CoderAgent
from src.agents.verifier_agent import VerifierAgent
from tests.unit_tests import TASK_SPECS


class ClarifyFlowPipeline:
    def __init__(self):
        self.planner = PlannerAgent()
        self.clarifier = ClarifyAgent()
        self.coder = CoderAgent()
        self.verifier = VerifierAgent()

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

    def run_all(self):
        for task_name, spec in TASK_SPECS.items():
            self.run_task(task_name, spec)


def main():
    pipeline = ClarifyFlowPipeline()
    pipeline.run_all()


if __name__ == "__main__":
    main()