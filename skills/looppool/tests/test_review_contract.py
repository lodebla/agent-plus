"""Exercise the single-review, multi-review, schema, and quota contracts."""
import copy
import json
import sqlite3
import unittest
from unittest.mock import patch

from test_orchestrator import Handle, PASS, RepositoryFixture, lp


FINDING = {
    "id": "F1",
    "title": "Lost update",
    "severity": "high",
    "blocking": True,
    "root_cause": "unserialized-write",
    "trigger": "two concurrent writes",
    "expected": "both changes persist",
    "observed": "one change is lost",
    "evidence": "app.py writes without serialization",
    "recommendation": "serialize writes",
}


def prompt_schema(prompt):
    marker = "\nOUTPUT JSON SCHEMA\n"
    if marker not in prompt:
        raise ValueError("agent cannot see its output schema")
    return json.loads(prompt.rsplit(marker, 1)[1])


class ReviewContractTests(RepositoryFixture):
    def test_default_native_review_calls_only_first_reviewer(self):
        cfg = lp.normalize_config(self.config(
            reviewer_agents=["review-a", "review-b"],
            strong_reviewer_agent="strong",
        ))
        calls = []

        def reviewer(prompt, **kwargs):
            self.assertEqual(prompt_schema(prompt), kwargs["schema"])
            calls.append((kwargs["label"], kwargs["agent"]))
            return Handle(PASS)

        with patch.object(lp, "agent", reviewer, create=True):
            bundle = lp._run_native_review(cfg, "candidate evidence")

        self.assertEqual(bundle["mode"], "single")
        self.assertEqual(bundle["decision"]["verdict"], "PASS")
        self.assertNotIn("judge", bundle)
        self.assertEqual(calls, [("looppool review round 0 review-a", "review-a")])

    def test_explicit_multi_review_uses_independent_peers_and_strong_judge(self):
        cfg = lp.normalize_config(self.config(
            multi_review=True,
            reviewer_agents=["review-a", "review-b"],
            strong_reviewer_agent="strong",
        ))
        calls = []

        def reviewer(prompt, **kwargs):
            self.assertEqual(prompt_schema(prompt), kwargs["schema"])
            calls.append((kwargs["label"], kwargs["agent"]))
            return Handle(PASS)

        with patch.object(lp, "agent", reviewer, create=True):
            bundle = lp._run_native_review(cfg, "candidate evidence")

        self.assertEqual(bundle["mode"], "multi")
        self.assertEqual(bundle["decision"]["verdict"], "PASS")
        self.assertEqual(bundle["judge"], bundle["decision"])
        self.assertEqual(
            calls,
            [
                ("looppool review round 0 review-a", "review-a"),
                ("looppool review round 0 review-b", "review-b"),
                ("final judge", "strong"),
            ],
        )
        self.assertEqual([row["round"] for row in bundle["history"]], [0])

    def test_single_needs_evidence_expands_to_multi_review(self):
        cfg = lp.normalize_config(self.config(
            reviewer_agents=["review-a", "review-b"],
            strong_reviewer_agent="strong",
        ))
        calls = []
        judge_calls = 0

        def reviewer(prompt, **kwargs):
            nonlocal judge_calls
            label = kwargs["label"]
            calls.append((label, kwargs["agent"]))
            if label == "looppool review round 0 review-a" and not any(
                prior[0] == "looppool review round 0 review-b" for prior in calls
            ):
                return Handle({
                    **copy.deepcopy(PASS),
                    "verdict": "NEEDS_EVIDENCE",
                    "summary": "Need an independent read of the runtime contract",
                })
            if label == "final judge":
                judge_calls += 1
                return Handle(PASS)
            return Handle(PASS)

        with patch.object(lp, "agent", reviewer, create=True):
            bundle = lp._run_native_review(cfg, "candidate evidence")

        self.assertEqual(bundle["mode"], "multi")
        self.assertEqual(bundle["decision"]["verdict"], "PASS")
        self.assertIn(("looppool review round 0 review-b", "review-b"), calls)
        self.assertIn(("final judge", "strong"), calls)
        self.assertGreaterEqual(judge_calls, 1)

    def test_final_judge_uses_the_configured_strong_identity(self):
        cfg = lp.normalize_config(self.config(
            reviewer_agents=["review-a", "review-b"],
            strong_reviewer_agent="strong",
        ))
        calls = []

        def reader(prompt, **kwargs):
            calls.append(kwargs)
            return Handle(PASS)

        with patch.object(lp, "agent", reader, create=True):
            result = lp._fresh_judge(cfg, "candidate material", [], {}, [])

        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(calls[0]["agent"], "strong")
        self.assertEqual(calls[0]["label"], "final judge")
        self.assertEqual(calls[0]["schema"], lp.REVIEW_SCHEMA)

    def test_role_schemas_reject_removed_implementer_status(self):
        properties = lp.IMPLEMENTER_SCHEMA["properties"]
        self.assertIn("test_changes", properties)
        self.assertIn("test_changes", lp.IMPLEMENTER_SCHEMA["required"])
        self.assertEqual(
            properties["status"]["enum"], ["IMPLEMENTED", "BLOCKED"]
        )
        self.assertNotIn("TEST_DISPUTE", properties["status"]["enum"])

    def test_reviewer_and_judge_identities_must_be_distinct(self):
        with self.assertRaisesRegex(lp.ConfigError, "distinct"):
            lp.normalize_config(self.config(
                reviewer_agents=["review-a", "review-a"],
                strong_reviewer_agent="strong",
            ))
        with self.assertRaisesRegex(lp.ConfigError, "distinct"):
            lp.normalize_config(self.config(
                reviewer_agents=["review-a", "review-b"],
                strong_reviewer_agent="review-a",
            ))

    def test_judge_completion_alias_is_not_configurable(self):
        with self.assertRaisesRegex(lp.ConfigError, "Unknown config keys"):
            lp.normalize_config(self.config(judge_model="slow"))

    def test_review_round_resumes_only_quota_limited_invocation(self):
        cfg = lp.normalize_config(self.config(
            reviewer_agents=["review-a", "review-b"],
            quota_usage_db="",
            quota_reset_grace_seconds=0,
        ))
        calls = {"review-a": 0, "review-b": 0}
        clock = [1000.0]
        sleeps = []

        def reviewer(prompt, **kwargs):
            name = kwargs["agent"]
            calls[name] += 1
            if name == "review-a" and calls[name] == 1:
                error = RuntimeError(
                    "Codex error event: usage limit reached (code=usage_limit_reached)"
                )
                error.resets_at = 1002
                raise error
            return Handle(PASS)

        def sleep(seconds):
            sleeps.append(seconds)
            clock[0] += seconds

        with patch.object(lp, "agent", reviewer, create=True), patch.object(
            lp, "_quota_now", lambda: clock[0]
        ), patch.object(lp, "_quota_sleep", sleep):
            result = lp._review_round(
                cfg, "material", ["review-a", "review-b"], 0, [], {}
            )

        self.assertEqual(set(result), {"review-a", "review-b"})
        self.assertEqual(calls, {"review-a": 2, "review-b": 1})
        self.assertEqual(sleeps, [2.0])

    def test_usage_limit_without_reset_retries_on_deterministic_schedule(self):
        cfg = lp.normalize_config(self.config(
            quota_usage_db="", quota_unknown_retry_seconds=60
        ))
        calls = 0
        clock = [1000.25]
        sleeps = []
        notices = []

        def reader(prompt, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError(
                    "Codex error event: The usage limit has been reached "
                    "(code=usage_limit_reached)"
                )
            return Handle(PASS)

        def sleep(seconds):
            sleeps.append(seconds)
            clock[0] += seconds

        with patch.object(lp, "agent", reader, create=True), patch.object(
            lp, "log", notices.append, create=True
        ), patch.object(lp, "_quota_now", lambda: clock[0]), patch.object(
            lp, "_quota_sleep", sleep
        ):
            result = lp._read_agent("Inspect evidence", "review-a", cfg)

        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(calls, 2)
        self.assertEqual(sleeps, [60.0])
        self.assertEqual(cfg["_quota_resume_events"][0]["source"], "scheduled-probe")
        self.assertIn("Next automatic retry", notices[0])

    def test_semantic_error_mentioning_quota_is_not_retried(self):
        cfg = lp.normalize_config(self.config(quota_usage_db=""))
        calls = []
        sleeps = []

        class FailedHandle:
            def wait(self, **kwargs):
                raise ValueError("schema validation failed: usage_limit_reached")

        def reader(prompt, **kwargs):
            calls.append(kwargs["agent"])
            return FailedHandle()

        with patch.object(lp, "agent", reader, create=True), patch.object(
            lp, "_quota_sleep", sleeps.append
        ):
            with self.assertRaisesRegex(ValueError, "schema validation"):
                lp._read_agent("Inspect evidence", "review-a", cfg)

        self.assertEqual(calls, ["review-a"])
        self.assertEqual(sleeps, [])

    def test_invalid_usage_database_reset_is_treated_as_missing(self):
        usage_db = lp.Path(self.tmp.name) / "invalid-usage.db"
        with sqlite3.connect(usage_db) as connection:
            connection.execute(
                "CREATE TABLE usage_history (recorded_at INTEGER, provider TEXT, "
                "account_key TEXT, limit_id TEXT, label TEXT, window_label TEXT, "
                "used_fraction REAL, status TEXT, resets_at INTEGER)"
            )
            connection.execute(
                "INSERT INTO usage_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    999000,
                    "openai-codex",
                    "account",
                    "primary",
                    "5 hours",
                    "5 hours",
                    1.0,
                    "exhausted",
                    "1e300",
                ),
            )
        cfg = lp.normalize_config(self.config(quota_usage_db=str(usage_db)))
        self.assertIsNone(lp._reset_from_usage_db(cfg, "openai-codex", 1000.0))

    def test_foreign_enums_never_enter_the_finding_ledger(self):
        for field, bad_value in (("severity", "BLOCKING"), ("status", "resolved")):
            with self.subTest(field=field):
                review = {
                    **copy.deepcopy(PASS),
                    "verdict": "FAIL",
                    "findings": [copy.deepcopy(FINDING)],
                }
                if field == "severity":
                    review["findings"][0]["severity"] = bad_value
                else:
                    review["dispositions"] = [
                        {"id": "F1", "status": bad_value, "evidence": "claimed resolution"}
                    ]
                original = copy.deepcopy(review)
                ledger = {}

                with self.assertRaises(lp.ProtocolStop) as failure:
                    lp._add_to_ledger(ledger, {"review-a": review})

                self.assertEqual(failure.exception.status, "STOP_INVALID_REVIEW")
                self.assertEqual(failure.exception.evidence["review"], original)
                self.assertEqual(ledger, {})


if __name__ == "__main__":
    unittest.main()
