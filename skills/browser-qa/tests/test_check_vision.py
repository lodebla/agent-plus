import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import check_vision  # noqa: E402
from check_vision import (  # noqa: E402
    choose_model,
    find_recent_kilo_model,
    parse_kilo_config,
    parse_kilo_verbose,
    resolve_vision,
)


class VisionResolutionTests(unittest.TestCase):
    def test_explicit_model_precedes_environment_model(self):
        self.assertEqual(
            choose_model("provider/explicit", {"BROWSER_QA_MODEL": "provider/environment"}),
            "provider/explicit",
        )

    def test_environment_model_is_used_when_no_model_is_passed(self):
        self.assertEqual(
            choose_model(None, {"BROWSER_QA_MODEL": "provider/environment"}),
            "provider/environment",
        )

    def test_missing_model_returns_unknown(self):
        self.assertEqual(resolve_vision(None, [], {}), "unknown")

    def test_image_input_returns_yes(self):
        catalog = [
            {
                "id": "vision-model",
                "providerID": "provider",
                "capabilities": {"input": {"image": True}},
            }
        ]
        self.assertEqual(resolve_vision("provider/vision-model", catalog, {}), "yes")

    def test_text_only_input_returns_no(self):
        catalog = [
            {
                "id": "text-model",
                "providerID": "provider",
                "capabilities": {"input": {"image": False}},
            }
        ]
        self.assertEqual(resolve_vision("provider/text-model", catalog, {}), "no")

    def test_input_array_metadata_supports_generic_catalogs(self):
        catalog = [{"id": "array-model", "providerID": "provider", "input": ["text", "image"]}]
        self.assertEqual(resolve_vision("provider/array-model", catalog, {}), "yes")

    def test_missing_model_metadata_returns_unknown(self):
        self.assertEqual(resolve_vision("provider/unknown", [], {}), "unknown")

    def test_model_match_uses_provider_and_full_id(self):
        catalog = [
            {
                "id": "same-name",
                "providerID": "other-provider",
                "capabilities": {"input": {"image": True}},
            }
        ]
        self.assertEqual(resolve_vision("provider/same-name", catalog, {}), "unknown")

    def test_explicit_environment_modalities_are_harness_neutral(self):
        self.assertEqual(
            resolve_vision("provider/model", [], {}, input_modalities=["text", "image"]),
            "yes",
        )
        self.assertEqual(
            resolve_vision("provider/model", [], {}, input_modalities=["text"]),
            "no",
        )

    def test_explicit_modalities_are_sufficient_without_a_model(self):
        self.assertEqual(
            resolve_vision(None, [], {}, input_modalities=["text", "image"]),
            "yes",
        )

    def test_explicit_text_only_modalities_are_sufficient_without_a_model(self):
        self.assertEqual(resolve_vision(None, [], {}, input_modalities=["text"]), "no")


class VisionProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        (self.workspace / ".artifacts").mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("check_vision.Path.cwd", return_value=self.workspace):
            with patch.dict(os.environ, {}, clear=True):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = check_vision.main(list(args))
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def create_probe(self):
        with patch("check_vision.secrets.choice", return_value="2"):
            exit_code, stdout, stderr = self.run_cli("--create-probe", ".artifacts/browser-qa/vision")
        self.assertEqual(exit_code, 0, stderr)
        return stdout

    def probe_path(self, output):
        line = next(line for line in output.splitlines() if line.startswith("PROBE_DIRECTORY="))
        return line.split("=", 1)[1]

    def test_create_probe_writes_png_and_salted_metadata_without_answer(self):
        output = self.create_probe()
        probe_dir = self.workspace / self.probe_path(output)
        images = list(probe_dir.rglob("*.png"))
        metadata_files = list(probe_dir.rglob("*.json"))
        self.assertEqual(len(images), 1)
        self.assertEqual(len(metadata_files), 1)
        self.assertTrue(images[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        metadata_text = metadata_files[0].read_text(encoding="utf-8")
        metadata = json.loads(metadata_text)
        self.assertIn("salt", metadata)
        self.assertIn("hash", metadata)
        self.assertNotIn("22222222", metadata_text)
        self.assertNotIn("22222222", output)
        self.assertIn(str(images[0]), output)

    def test_correct_image_answer_confirms_current_session_vision(self):
        probe = self.probe_path(self.create_probe())
        exit_code, stdout, stderr = self.run_cli(
            "--verify-probe", probe, "--answer", "22222222"
        )
        self.assertEqual(exit_code, 0, stderr)
        self.assertIn("VISION=yes", stdout)
        self.assertNotIn("22222222", stdout + stderr)

    def test_mismatched_image_answer_returns_unknown_not_no(self):
        probe = self.probe_path(self.create_probe())
        exit_code, stdout, stderr = self.run_cli(
            "--verify-probe", probe, "--answer", "ABCDEFGH"
        )
        self.assertEqual(exit_code, 2)
        self.assertIn("VISION=unknown", stdout)
        self.assertNotIn("VISION=no", stdout)
        self.assertNotIn("ABCDEFGH", stdout + stderr)

    def test_missing_or_malformed_probe_returns_unknown_without_traceback(self):
        exit_code, stdout, stderr = self.run_cli(
            "--verify-probe", ".artifacts/missing", "--answer", "ABCDEFGH"
        )
        self.assertEqual(exit_code, 2)
        self.assertIn("VISION=unknown", stdout)
        self.assertNotIn("Traceback", stdout + stderr)

        probe_dir = self.workspace / ".artifacts" / "vision" / "broken"
        probe_dir.mkdir(parents=True)
        (probe_dir / "probe.json").write_text("{", encoding="utf-8")
        exit_code, stdout, stderr = self.run_cli(
            "--verify-probe", ".artifacts/browser-qa/vision/broken", "--answer", "ABCDEFGH"
        )
        self.assertEqual(exit_code, 2)
        self.assertIn("VISION=unknown", stdout)
        self.assertNotIn("Traceback", stdout + stderr)

    def test_corrupt_png_returns_unknown(self):
        probe = self.probe_path(self.create_probe())
        image_path = self.workspace / probe / "probe.png"
        image = bytearray(image_path.read_bytes())
        image[-1] ^= 0x01
        image_path.write_bytes(image)

        exit_code, stdout, stderr = self.run_cli(
            "--verify-probe", probe, "--answer", "22222222"
        )
        self.assertEqual(exit_code, 2)
        self.assertIn("VISION=unknown", stdout)
        self.assertNotIn("Traceback", stdout + stderr)

    def test_probe_expires_after_five_minutes(self):
        with patch("check_vision.Path.cwd", return_value=self.workspace):
            with patch("check_vision.secrets.choice", return_value="2"):
                challenge_dir, _, _ = check_vision.create_probe(".artifacts/browser-qa/vision", now=1000)
            self.assertTrue(check_vision.verify_probe(challenge_dir, "22222222", now=1299))
            self.assertFalse(check_vision.verify_probe(challenge_dir, "22222222", now=1300))

    def test_malformed_boolean_timestamp_is_not_accepted_as_an_integer(self):
        with patch("check_vision.Path.cwd", return_value=self.workspace):
            with patch("check_vision.secrets.choice", return_value="2"):
                challenge_dir, _, metadata_path = check_vision.create_probe(
                    ".artifacts/browser-qa/vision", now=100
                )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["created_at"] = True
            metadata["expires_at"] = 301
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            self.assertFalse(check_vision.verify_probe(challenge_dir, "22222222", now=100))

    def test_existing_probe_is_not_overwritten_on_identifier_collision(self):
        with patch("check_vision.Path.cwd", return_value=self.workspace):
            with patch("check_vision.secrets.token_hex", side_effect=lambda size: "a" * (size * 2)):
                with patch("check_vision.secrets.choice", return_value="2"):
                    first = check_vision.create_probe(".artifacts/browser-qa/vision")
                    before = {path.name: path.read_bytes() for path in first[0].iterdir()}
                    with self.assertRaises(ValueError):
                        check_vision.create_probe(".artifacts/browser-qa/vision")
                    after = {path.name: path.read_bytes() for path in first[0].iterdir()}
        self.assertEqual(before, after)

    def test_artifact_paths_outside_root_traversal_and_symlinks_are_rejected(self):
        outside = self.workspace / "outside"
        outside.mkdir()
        symlink = self.workspace / ".artifacts" / "linked"
        symlink.symlink_to(outside, target_is_directory=True)

        for unsafe_path in (str(outside), ".artifacts/../outside", ".artifacts/linked"):
            with self.subTest(path=unsafe_path):
                exit_code, stdout, stderr = self.run_cli("--create-probe", unsafe_path)
                self.assertEqual(exit_code, 2)
                self.assertIn("VISION=unknown", stdout)
                self.assertNotIn("Traceback", stdout + stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_explicit_cli_modalities_work_without_model_or_kilo_runtime(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("check_vision.Path.cwd", return_value=self.workspace):
            with patch.dict(os.environ, {}, clear=True):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = check_vision.main(["--input-modalities", "text,image"])
        self.assertEqual(exit_code, 0, stderr.getvalue())
        self.assertIn("VISION=yes", stdout.getvalue())

    def test_environment_modalities_work_without_model_or_kilo_runtime(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("check_vision.Path.cwd", return_value=self.workspace):
            with patch.dict(
                os.environ, {"BROWSER_QA_MODEL_INPUT_MODALITIES": "text,image"}, clear=True
            ):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = check_vision.main([])
        self.assertEqual(exit_code, 0, stderr.getvalue())
        self.assertIn("VISION=yes", stdout.getvalue())


class KiloMetadataTests(unittest.TestCase):
    def test_parses_verbose_model_records(self):
        output = '''kilo/provider/vision-model
{
  "id": "provider/vision-model",
  "providerID": "kilo",
  "capabilities": {"input": {"image": true}}
}
'''
        self.assertEqual(
            resolve_vision("kilo/provider/vision-model", parse_kilo_verbose(output), {}),
            "yes",
        )

    def test_parses_custom_model_modalities_from_jsonc(self):
        text = '''{
          // custom provider model declaration
          "provider": {
            "custom": {
              "models": {
                "vision-model": {
                  "modalities": {"input": ["text", "image"], "output": ["text"]},
                },
              },
            },
          },
        }'''
        configured_models = parse_kilo_config(text)
        self.assertEqual(resolve_vision("custom/vision-model", [], configured_models), "yes")


class KiloDatabasePathTests(unittest.TestCase):
    def test_uses_standard_database_path_before_spawning_cli(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            database = home / ".local" / "share" / "kilo" / "kilo.db"
            database.parent.mkdir(parents=True)
            database.touch()
            with patch("check_vision.Path.home", return_value=home):
                with patch("check_vision.subprocess.run") as run:
                    self.assertEqual(check_vision._kilo_database_path({}), database)
                    run.assert_not_called()


class KiloSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "kilo.db"
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "CREATE TABLE session (id TEXT, directory TEXT, model TEXT, time_updated INTEGER)"
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_session(self, session_id, directory, model, updated):
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "INSERT INTO session (id, directory, model, time_updated) VALUES (?, ?, ?, ?)",
                (session_id, directory, json.dumps(model), updated),
            )

    def test_reads_model_from_one_recent_workspace_session(self):
        self.add_session(
            "ses_current",
            "/workspace/project",
            {"providerID": "kilo", "id": "provider/model"},
            1000,
        )
        self.assertEqual(
            find_recent_kilo_model(self.database, "/workspace/project", now=1000),
            "kilo/provider/model",
        )

    def test_ambiguous_recent_sessions_return_unknown(self):
        self.add_session(
            "ses_one", "/workspace/project", {"providerID": "p", "id": "one"}, 1000
        )
        self.add_session(
            "ses_two", "/workspace/project", {"providerID": "p", "id": "two"}, 995
        )
        self.assertIsNone(find_recent_kilo_model(self.database, "/workspace/project", now=1000))

    def test_stale_session_returns_unknown(self):
        self.add_session(
            "ses_old", "/workspace/project", {"providerID": "p", "id": "old"}, 100
        )
        self.assertIsNone(
            find_recent_kilo_model(self.database, "/workspace/project", now=5000)
        )

    def test_recently_started_session_stays_valid_during_a_long_turn(self):
        self.add_session(
            "ses_long_turn",
            "/workspace/project",
            {"providerID": "p", "id": "current"},
            500000,
        )
        self.assertEqual(
            find_recent_kilo_model(self.database, "/workspace/project", now=500600),
            "p/current",
        )

    def test_session_from_another_workspace_is_ignored(self):
        self.add_session(
            "ses_other", "/workspace/other", {"providerID": "p", "id": "other"}, 1000
        )
        self.assertIsNone(
            find_recent_kilo_model(self.database, "/workspace/project", now=1000)
        )

    def test_recent_session_without_model_keeps_result_unknown(self):
        self.add_session(
            "ses_with_model", "/workspace/project", {"providerID": "p", "id": "one"}, 1000
        )
        self.add_session("ses_without_model", "/workspace/project", None, 995)
        self.assertIsNone(
            find_recent_kilo_model(self.database, "/workspace/project", now=1000)
        )


if __name__ == "__main__":
    unittest.main()
