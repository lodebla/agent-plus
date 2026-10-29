"""Adversarial integration tests against disposable Git repositories."""
import asyncio
from pathlib import Path
from unittest.mock import patch

from test_orchestrator import Handle, IMPLEMENTED, PASS, PYTHON, RepositoryFixture, lp


class AdversarialTests(RepositoryFixture):
    def run_with(self, hook, **overrides):
        calls = []

        def agent(prompt, **kwargs):
            label = kwargs.get("label", "")
            calls.append((label, prompt, kwargs))
            value = hook(label, prompt, kwargs)
            if value is None:
                value = IMPLEMENTED if "implement iteration" in label else PASS
            return Handle(value)

        with patch.object(lp, "agent", agent, create=True):
            result = asyncio.run(lp.looppool(self.config(**overrides)))
        return result, calls

    def test_feature_and_fix_begin_with_the_writer(self):
        for task_type in ("feature", "fix"):
            with self.subTest(task_type=task_type):
                def hook(label, _prompt, _kwargs):
                    if "implement iteration" in label:
                        Path("feature.py").write_text("value = 2\n")
                        return IMPLEMENTED
                    return PASS

                result, calls = self.run_with(hook, task_type=task_type)
                self.assertEqual(result["status"], "DONE", result)
                self.assertTrue(calls[0][0].startswith("looppool implement iteration"))
                self.assertFalse(any("probe" in row[0] or "test writer" in row[0] for row in calls))
                self.git("reset", "--hard", "HEAD")
                self.git("clean", "-fd")

    def test_readonly_reviewer_mutation_is_detected_and_restored(self):
        def hook(label, _prompt, _kwargs):
            if "implement iteration" in label:
                Path("app.py").write_text("value = 2\n")
                return IMPLEMENTED
            if label.startswith("looppool review round"):
                Path("test_existing.py").write_text("assert False\n")
            return PASS

        result, _ = self.run_with(hook)
        self.assertEqual(result["status"], "STOP_UNEXPECTED_MUTATION", result)
        self.assertEqual(Path("test_existing.py").read_text(), "assert True\n")
        self.assertEqual(Path("app.py").read_text(), "value = 2\n")

    def test_writer_failure_restores_only_its_partial_pass(self):
        def agent(prompt, **kwargs):
            if "implement iteration" in kwargs.get("label", ""):
                Path("app.py").write_text("partial\n")
                return Handle(RuntimeError("writer crashed"))
            return Handle(PASS)

        with patch.object(lp, "agent", agent, create=True):
            result = asyncio.run(lp.looppool(self.config()))

        self.assertEqual(result["status"], "STOP_RUNTIME_ERROR", result)
        self.assertEqual(Path("app.py").read_text(), "value = 1\n")
        self.assertTrue(result["initial_checkpoint"])
        self.assertTrue(result["current_checkpoint"])

    def test_writer_usage_limit_restores_then_resumes_cleanly(self):
        attempts = 0
        clock = [1000.0]
        sleeps = []
        notices = []

        def agent(prompt, **kwargs):
            nonlocal attempts
            if "implement iteration" in kwargs.get("label", ""):
                attempts += 1
                if attempts == 1:
                    Path("app.py").write_text("partial\n")
                    error = RuntimeError(
                        "Codex error event: usage limit reached (code=usage_limit_reached)"
                    )
                    error.resets_at = 1002
                    return Handle(error)
                self.assertEqual(Path("app.py").read_text(), "value = 1\n")
                Path("app.py").write_text("value = 2\n")
                return Handle(IMPLEMENTED)
            return Handle(PASS)

        def sleep(seconds):
            sleeps.append(seconds)
            clock[0] += seconds

        with patch.object(lp, "agent", agent, create=True), patch.object(
            lp, "_quota_now", lambda: clock[0]
        ), patch.object(lp, "_quota_sleep", sleep), patch.object(
            lp, "log", notices.append, create=True
        ):
            result = asyncio.run(lp.looppool(self.config(
                quota_usage_db="", quota_reset_grace_seconds=0
            )))

        self.assertEqual(result["status"], "DONE", result)
        self.assertEqual(attempts, 2)
        self.assertEqual(sleeps, [2.0])
        self.assertIn("Automatic resume", notices[0])

    def test_refactor_failing_baseline_stops_before_writer(self):
        calls = []

        def agent(*args, **kwargs):
            calls.append(kwargs)
            return Handle(IMPLEMENTED)

        with patch.object(lp, "agent", agent, create=True):
            result = asyncio.run(lp.looppool(self.config(required_checks=[{
                "name": "tests", "command": f'{PYTHON} -c "raise SystemExit(1)"'
            }])))

        self.assertEqual(result["status"], "STOP_BASELINE_NOT_GREEN", result)
        self.assertEqual(calls, [])
        self.assertTrue(result["initial_checkpoint"])


if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)
