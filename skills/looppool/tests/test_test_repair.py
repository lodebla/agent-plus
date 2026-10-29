"""Writer-owned test repair and stagnation escalation regressions."""
import asyncio
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from test_orchestrator import Handle, IMPLEMENTED, PASS, PYTHON, RepositoryFixture, lp


def implemented(test_changes=None):
    value = copy.deepcopy(IMPLEMENTED)
    value["test_changes"] = list(test_changes or [])
    return value


BLOCKER = {
    "id": "WEAK_TEST",
    "title": "Test does not exercise the acceptance criterion",
    "severity": "high",
    "blocking": True,
    "root_cause": "weakened-test",
    "trigger": "the new test contains only assert True",
    "expected": "AC1 observes the exported value",
    "observed": "the test passes for every implementation",
    "evidence": "test_value.py contains assert True",
    "recommendation": "assert the public value required by AC1",
    "criterion": "AC1",
}


class WriterTestRepairTests(RepositoryFixture):
    def run_feature(self, hook, *, checks, max_iterations=3, **overrides):
        calls = []

        def agent(prompt, **kwargs):
            label = kwargs.get("label", "")
            calls.append((label, prompt, kwargs))
            value = hook(label, prompt, kwargs)
            return Handle(value if value is not None else PASS)

        config = self.config(
            task="Add exported value",
            task_type="feature",
            spec="Expose value 2",
            acceptance_criteria=["The public value equals 2"],
            required_checks=checks,
            max_iterations=max_iterations,
            **overrides,
        )
        with patch.object(lp, "agent", agent, create=True):
            result = asyncio.run(lp.looppool(config))
        return result, calls

    def test_new_module_reaches_writer_without_preimplementation_gate(self):
        def hook(label, _prompt, _kwargs):
            if "implement iteration" in label:
                self.assertFalse(Path("feature.py").exists())
                Path("feature.py").write_text("value = 2\n")
                Path("test_feature.py").write_text(
                    "from feature import value\nassert value == 2\n"
                )
                return implemented([
                    "test_feature.py: AC1 observes the new public export"
                ])
            return PASS

        result, calls = self.run_feature(hook, checks=[{
            "name": "focused", "command": f"{PYTHON} -B test_feature.py"
        }], max_iterations=1)

        self.assertEqual(result["status"], "DONE", result)
        self.assertTrue(calls[0][0].startswith("looppool implement iteration"))
        self.assertFalse(any("test writer" in row[0] or "validator" in row[0] for row in calls))

    def test_failed_test_is_corrected_by_the_next_writer(self):
        attempts = 0

        def hook(label, prompt, _kwargs):
            nonlocal attempts
            if "implement iteration" in label:
                attempts += 1
                Path("app.py").write_text("value = 2\n")
                if attempts == 1:
                    Path("test_value.py").write_text(
                        "from app import value\nassert value == 3\n"
                    )
                else:
                    self.assertIn("test_value.py", prompt)
                    self.assertIn("exit_code", prompt)
                    Path("test_value.py").write_text(
                        "from app import value\nassert value == 2\n"
                    )
                return implemented([
                    "test_value.py: AC1 asserts the required public value"
                ])
            return PASS

        result, calls = self.run_feature(hook, checks=[{
            "name": "focused", "command": f"{PYTHON} -B test_value.py"
        }], max_iterations=2)

        self.assertEqual(result["status"], "DONE", result)
        self.assertEqual(attempts, 2)
        self.assertEqual(
            [row[0] for row in calls if row[0].startswith("looppool review")],
            ["looppool review round 0 looppool-reviewer-a"],
        )

    def test_missing_test_rationale_becomes_next_cycle_feedback(self):
        attempts = 0

        def hook(label, prompt, _kwargs):
            nonlocal attempts
            if "implement iteration" in label:
                attempts += 1
                if attempts == 1:
                    Path("test_existing.py").write_text(
                        "from app import value\nassert value == 1\n"
                    )
                    return implemented()
                self.assertIn("test-change-rationale", prompt)
                self.assertIn("test_existing.py", prompt)
                return implemented([
                    "test_existing.py: AC1 preserves the existing public value"
                ])
            return PASS

        result, _ = self.run_feature(hook, checks=[{
            "name": "focused", "command": f"{PYTHON} -B test_existing.py"
        }], max_iterations=2)

        self.assertEqual(result["status"], "DONE", result)
        self.assertEqual(attempts, 2)
        self.assertIn("from app import value", Path("test_existing.py").read_text())

    def test_reviewer_blocks_weakened_test_then_writer_repairs_it(self):
        attempts = 0
        reviews = 0

        def hook(label, prompt, _kwargs):
            nonlocal attempts, reviews
            if "implement iteration" in label:
                attempts += 1
                if attempts == 1:
                    Path("test_value.py").write_text("assert True\n")
                else:
                    self.assertIn("WEAK_TEST", prompt)
                    Path("test_value.py").write_text(
                        "from app import value\nassert value == 1\n"
                    )
                return implemented([
                    "test_value.py: AC1 observes the public value"
                ])
            if label.startswith("looppool review"):
                reviews += 1
                if reviews == 1:
                    return {
                        "verdict": "FAIL",
                        "summary": "Behavioral coverage was weakened",
                        "findings": [copy.deepcopy(BLOCKER)],
                        "dispositions": [],
                    }
            return PASS

        result, _ = self.run_feature(hook, checks=[{
            "name": "focused", "command": f"{PYTHON} -B test_value.py"
        }], max_iterations=2)

        self.assertEqual(result["status"], "DONE", result)
        self.assertEqual(attempts, 2)
        self.assertIn("from app import value", Path("test_value.py").read_text())

    def test_repeated_failed_gate_triggers_one_multi_review(self):
        def hook(label, _prompt, _kwargs):
            if "implement iteration" in label:
                return implemented()
            return PASS

        result, calls = self.run_feature(hook, checks=[{
            "name": "focused", "command": f'{PYTHON} -c "raise SystemExit(1)"'
        }], max_iterations=3)

        labels = [(row[0], row[2]["agent"]) for row in calls]
        self.assertEqual(result["status"], "STOP_STAGNATION", result)
        self.assertEqual(result["escalations"], [{"iteration": 2, "reason": "stagnation"}])
        self.assertIn(
            ("looppool review round 0 looppool-reviewer-b", "looppool-reviewer-b"),
            labels,
        )
        self.assertIn(("final judge", "looppool-reviewer-strong"), labels)
        self.assertEqual(
            sum(label == "final judge" for label, _agent in labels), 1
        )
        self.assertEqual(
            sum(label.startswith("looppool implement iteration") for label, _agent in labels),
            3,
        )

    def test_changing_failure_evidence_does_not_false_trigger_stagnation(self):
        attempts = 0

        def hook(label, _prompt, _kwargs):
            nonlocal attempts
            if "implement iteration" in label:
                attempts += 1
                Path("app.py").write_text(f"value = {attempts + 1}\\n")
                return implemented()
            return PASS

        result, calls = self.run_feature(hook, checks=[{
            "name": "focused",
            "command": (
                f'{PYTHON} -c "import app; print(app.value); raise SystemExit(1)"'
            ),
        }], max_iterations=2)

        self.assertEqual(result["status"], "STOP_MAX_ITERATIONS", result)
        self.assertEqual(result["escalations"], [])
        self.assertFalse(any(row[0] == "final judge" for row in calls))

    def test_repeated_blocker_root_cause_escalates_then_reaches_writer(self):
        attempts = 0

        def failure():
            return {
                "verdict": "FAIL",
                "summary": "AC1 is still broken",
                "findings": [copy.deepcopy(BLOCKER)],
                "dispositions": [],
            }

        def hook(label, prompt, _kwargs):
            nonlocal attempts
            if "implement iteration" in label:
                attempts += 1
                Path("app.py").write_text(f"value = {attempts}\\n")
                if attempts == 3:
                    self.assertIn("WEAK_TEST", prompt)
                return implemented()
            if label == "final judge":
                canonical = {
                    **copy.deepcopy(BLOCKER),
                    "id": "looppool-reviewer-a:WEAK_TEST",
                }
                return {
                    "verdict": "FAIL",
                    "summary": "The blocker is verified",
                    "findings": [canonical],
                    "dispositions": [
                        {
                            "id": "looppool-reviewer-a:WEAK_TEST",
                            "status": "verified",
                            "evidence": "The observable defect remains",
                        },
                        {
                            "id": "looppool-reviewer-b:WEAK_TEST",
                            "status": "rejected",
                            "evidence": "Duplicate of reviewer A's finding",
                        },
                    ],
                }
            if label.startswith("looppool review") and attempts < 3:
                return failure()
            return PASS

        result, _ = self.run_feature(hook, checks=[{
            "name": "focused", "command": f'{PYTHON} -c "assert True"'
        }], max_iterations=3)

        self.assertEqual(result["status"], "DONE", result)
        self.assertEqual(result["escalations"], [{"iteration": 2, "reason": "stagnation"}])
        self.assertEqual(attempts, 3)

    def test_final_iteration_escalation_respects_writer_cap(self):
        def hook(label, _prompt, _kwargs):
            if "implement iteration" in label:
                return implemented()
            return PASS

        result, calls = self.run_feature(hook, checks=[{
            "name": "focused", "command": f'{PYTHON} -c "raise SystemExit(1)"'
        }], max_iterations=2)

        self.assertEqual(result["status"], "STOP_MAX_ITERATIONS", result)
        self.assertEqual(len(result["escalations"]), 1)
        self.assertEqual(
            sum(row[0] == "final judge" for row in calls), 1
        )


if __name__ == "__main__":
    unittest.main()
