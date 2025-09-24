"""
VerifierAgent executes provided tests against dynamically generated code objects.
"""
from typing import List, Dict, Any, Callable
import traceback


class TestResult:
    def __init__(self, name: str, passed: bool, detail: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name} {('- ' + self.detail) if self.detail else ''}"

    def to_dict(self):  # For JSON export
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


class VerifierAgent:
    def run_tests(
        self,
        code_str: str,
        task_name: str,
        test_specs: List[Dict[str, Any]],
        function_name: str,
    ) -> List[TestResult]:
        local_ns: Dict[str, Any] = {}
        try:
            exec(code_str, {}, local_ns)
        except Exception as e:
            return [TestResult(f"{task_name}::code_load", False, f"Error exec code: {e}")]
        if function_name not in local_ns:
            return [TestResult(f"{task_name}::missing_function", False, f"{function_name} not defined")]
        fn: Callable = local_ns[function_name]
        results: List[TestResult] = []
        for idx, spec in enumerate(test_specs):
            test_name = f"{task_name}::case_{idx+1}"
            args = spec.get("input", [])
            expected = spec.get("expected")
            try:
                output = fn(*args)
                if output == expected:
                    results.append(TestResult(test_name, True))
                else:
                    results.append(
                        TestResult(
                            test_name,
                            False,
                            f"Expected={expected} Got={output} Args={args}",
                        )
                    )
            except Exception as e:
                tb = traceback.format_exc(limit=1)
                results.append(TestResult(test_name, False, f"Exception: {e} {tb}"))
        return results