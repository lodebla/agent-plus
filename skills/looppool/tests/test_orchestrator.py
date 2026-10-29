import asyncio
import copy
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "looppool", Path(__file__).parents[1] / "orchestrator.py"
)
lp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lp)
PYTHON = shlex.quote(sys.executable)


class Handle:
    def __init__(self, value):
        self.value = value

    def wait(self, **kwargs):
        if isinstance(self.value, Exception):
            raise self.value
        return copy.deepcopy(self.value)


PASS = {"verdict": "PASS", "summary": "Verified", "findings": [], "dispositions": []}
IMPLEMENTED = {
    "status": "IMPLEMENTED",
    "summary": "done",
    "changed_files": [],
    "criteria_addressed": ["AC1"],
    "checks_run": [],
    "remaining_issues": [],
    "test_changes": [],
}


class RepositoryFixture(unittest.TestCase):
    def setUp(self):
        self.old = Path.cwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        self.old_bridge = os.environ.get("PI_TOOL_BRIDGE_SESSION")
        os.environ["PI_TOOL_BRIDGE_SESSION"] = (
            f"python:session:test:cwd:{Path(self.tmp.name).resolve()}"
        )
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        Path("app.py").write_text("value = 1\n")
        Path("test_existing.py").write_text("assert True\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")

    def tearDown(self):
        if self.old_bridge is None:
            os.environ.pop("PI_TOOL_BRIDGE_SESSION", None)
        else:
            os.environ["PI_TOOL_BRIDGE_SESSION"] = self.old_bridge
        os.chdir(self.old)
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(["git", *args], stderr=subprocess.STDOUT).decode()

    def config(self, **overrides):
        return {
            "task": "Preserve behavior",
            "task_type": "refactor",
            "spec": "Keep value equal to 1",
            "acceptance_criteria": ["value remains 1"],
            "required_checks": [
                {"name": "tests", "command": f'{PYTHON} -c "assert True"'}
            ],
            "max_iterations": 1,
            **overrides,
        }

    def run_loop(self, mutation=None, agent_hook=None, **overrides):
        def agent(prompt, **kwargs):
            label = kwargs.get("label", "")
            if agent_hook is not None:
                value = agent_hook(label, prompt, kwargs)
                if value is not None:
                    return Handle(value)
            if "implement iteration" in label:
                if mutation:
                    mutation()
                return Handle(IMPLEMENTED)
            return Handle(PASS)

        with patch.object(lp, "agent", agent, create=True):
            return asyncio.run(lp.looppool(self.config(**overrides)))


class RepositoryTests(RepositoryFixture):
    def test_new_file_is_reviewed_and_changes_snapshot_hash(self):
        before = lp._diff_hash()
        Path("new.py").write_text("new_behavior = 2\n")

        self.assertIn("new_behavior", lp._diff_text(10_000))
        self.assertNotEqual(before, lp._diff_hash())

    def test_nested_untracked_paths_are_in_snapshot(self):
        Path("new").mkdir()
        Path("new/test_x.py").write_text("assert True")
        self.assertIn("new/test_x.py", lp._changed_paths())

    def test_explicit_protected_test_is_immutable_and_restored(self):
        result = self.run_loop(
            lambda: Path("test_existing.py").write_text("assert False\n"),
            protected_paths=["./test_existing.py"],
        )

        self.assertEqual(result["status"], "STOP_PROTECTED_PATH_VIOLATION", result)
        self.assertEqual(Path("test_existing.py").read_text(), "assert True\n")

    def test_mutating_check_is_restored(self):
        result = self.run_loop(
            required_checks=[{
                "name": "bad",
                "command": (
                    f"{PYTHON} -c \"from pathlib import Path; "
                    "Path('app.py').write_text('changed')\""
                ),
            }]
        )

        self.assertEqual(result["status"], "STOP_UNEXPECTED_MUTATION", result)
        self.assertEqual(Path("app.py").read_text(), "value = 1\n")

    def test_clean_default_loop_succeeds(self):
        self.assertEqual(self.run_loop()["status"], "DONE")

    def test_required_checks_cannot_be_nonblocking(self):
        with self.assertRaises(lp.ConfigError):
            lp.normalize_config(self.config(required_checks=[{
                "name": "test", "command": "false", "blocking": False
            }]))

    def test_empty_required_checks_need_an_inspection_reason(self):
        with self.assertRaises(lp.ConfigError):
            lp.normalize_config(self.config(required_checks=[]))

        normalized = lp.normalize_config(self.config(
            required_checks=[], no_required_checks_reason="No executable project checks exist"
        ))
        self.assertEqual(normalized["required_checks"], [])

    def test_optional_checks_require_approval_or_local_attestation(self):
        cfg = self.config(optional_checks=[{
            "name": "format", "command": "true", "local_read_only": True
        }])
        self.assertTrue(lp.normalize_config(cfg)["optional_checks"][0]["local_read_only"])
        with self.assertRaises(lp.ConfigError):
            lp.normalize_config(self.config(optional_checks=[{
                "name": "audit", "command": "true", "approved": "false"
            }]))

    def test_deleted_configuration_keys_fail_preflight(self):
        obsolete = {
            "test_writer_agent": "writer",
            "test_repair_rounds": 2,
            "test_support_allowlist": [],
            "simplicity_model": "slow",
            "simplicity_fallback_models": [],
            "max_fixes_per_iteration": 1,
            "debate_rounds": 1,
            "adaptive_debate": True,
            "strong_discussion": False,
        }
        for key, value in obsolete.items():
            with self.subTest(key=key), self.assertRaisesRegex(lp.ConfigError, "Unknown config keys"):
                lp.normalize_config(self.config(**{key: value}))

    def test_agent_timeout_cannot_reintroduce_a_deadline(self):
        with self.assertRaisesRegex(lp.ConfigError, "Unknown config keys"):
            lp.normalize_config(self.config(agent_timeout=1))

    def test_agent_handles_are_not_given_a_looppool_deadline(self):
        waits = []

        class RecordingHandle(Handle):
            def wait(self, **kwargs):
                waits.append(dict(kwargs))
                return super().wait(**kwargs)

        def agent(prompt, **kwargs):
            value = IMPLEMENTED if "implement iteration" in kwargs.get("label", "") else PASS
            return RecordingHandle(value)

        with patch.object(lp, "agent", agent, create=True):
            result = asyncio.run(lp.looppool(self.config()))

        self.assertEqual(result["status"], "DONE", result)
        self.assertTrue(waits)
        self.assertTrue(all("timeout" not in kwargs for kwargs in waits), waits)

    def test_eval_bridge_bound_to_other_worktree_stops_before_agents(self):
        def unexpected(*args, **kwargs):
            raise AssertionError("no agent may run with a mismatched session worktree")

        marker = f"python:session:test:cwd:{self.old.resolve()}"
        with patch.dict(os.environ, {"PI_TOOL_BRIDGE_SESSION": marker}), patch.object(
            lp, "agent", unexpected, create=True
        ):
            result = asyncio.run(lp.looppool(self.config()))

        self.assertEqual(result["status"], "STOP_CONFIGURATION", result)
        self.assertIn("session", result["message"].lower())

    def test_missing_eval_bridge_binding_stops_before_agents(self):
        def unexpected(*args, **kwargs):
            raise AssertionError("no agent may run without a verifiable session worktree")

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PI_TOOL_BRIDGE_SESSION", None)
            with patch.object(lp, "agent", unexpected, create=True):
                result = asyncio.run(lp.looppool(self.config()))

        self.assertEqual(result["status"], "STOP_CONFIGURATION", result)
        self.assertIn("binding", result["message"].lower())


class EvidenceTests(RepositoryFixture):
    def test_checkpoint_includes_new_and_deleted_contents(self):
        import base64
        import json

        Path("app.py").unlink()
        Path("nested").mkdir()
        Path("nested/new.bin").write_bytes(b"\x00\xff\x01")
        checkpoint = lp._capture_checkpoint(1)
        payload = json.loads(Path(checkpoint["files"]).read_text())

        self.assertIsNone(payload["files"]["app.py"])
        self.assertEqual(
            base64.b64decode(payload["files"]["nested/new.bin"]["data"]),
            b"\x00\xff\x01",
        )

    def test_snapshot_restores_symlink_and_executable_mode(self):
        Path("alias").symlink_to("app.py")
        Path("app.py").chmod(0o755)
        before = lp._snapshot_paths(["app.py", "alias"])
        Path("alias").unlink()
        Path("alias").symlink_to("test_existing.py")
        Path("app.py").chmod(0o644)

        lp._restore_snapshot(before)

        self.assertEqual(os.readlink("alias"), "app.py")
        self.assertEqual(Path("app.py").stat().st_mode & 0o777, 0o755)

    def test_hash_ignores_ignored_build_artifact(self):
        Path(".gitignore").write_text("build/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "ignore build")
        before = lp._diff_hash()
        Path("build").mkdir()
        Path("build/generated.js").write_text("output")
        self.assertEqual(before, lp._diff_hash())

    def test_fingerprints_follow_root_cause_not_wording_or_location(self):
        first = {
            "blocking": True,
            "root_cause": "token-reuse",
            "file": "a",
            "line": 1,
            "title": "first",
        }
        second = {**first, "line": 22, "title": "paraphrased"}
        self.assertEqual(
            lp.finding_fingerprints([first]), lp.finding_fingerprints([second])
        )



if __name__ == "__main__":
    unittest.main()
