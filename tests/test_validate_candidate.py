"""Contract tests for the content candidate validator."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from jsonschema_min import UnsupportedSchema, validate  # noqa: E402
from validate_candidate import (  # noqa: E402
    load_schema,
    main,
    validate_batch,
    validate_candidate,
)


def fictional_candidate() -> dict:
    """An obviously fictional, structurally complete candidate."""

    return {
        "schema_version": "1.0",
        "candidate_id": "example-candidate-01",
        "client_id": "example-client",
        "batch_id": "example-batch",
        "status": "proposed",
        "source": {
            "source_type": "transcript",
            "references": [
                {
                    "recording_id": "fixture-recording",
                    "timestamp_ms": 1000,
                    "speaker": "Example Speaker",
                    "excerpt": "A sentence taken from the fixture transcript.",
                    "ownership_confidence": "high",
                }
            ],
        },
        "audience_problem": "The example audience cannot tell two options apart.",
        "content_pillar": "example-pillar",
        "proposed_hook_material": ["A raw phrase from the fixture."],
        "core_claim": "The example claim under evaluation.",
        "supporting_evidence": [
            {
                "evidence_id": "evidence-001",
                "evidence_type": "demand",
                "validation_status": "provisional",
            }
        ],
        "format": "video",
        "cta_stage": "awareness",
        "confidence": {
            "level": "medium",
            "ownership_confidence": "high",
            "uncertainty": ["No query volume evidence was available."],
            "review_notes": "",
        },
        "approval": {"state": "unapproved"},
    }


def approved_candidate() -> dict:
    candidate = fictional_candidate()
    candidate["status"] = "approved_for_recording"
    candidate["approval"] = {
        "state": "approved",
        "approved_by": "example-approver",
        "approved_at": "2026-01-01",
        "record_reference": "approvals/approval-record.md",
    }
    return candidate


class CandidateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = load_schema()

    def test_fictional_candidate_passes(self) -> None:
        self.assertEqual(validate_candidate(fictional_candidate()), [])

    def test_approved_candidate_passes(self) -> None:
        self.assertEqual(validate_candidate(approved_candidate()), [])

    def test_missing_source_references_fail(self) -> None:
        candidate = fictional_candidate()
        candidate["source"]["references"] = []
        errors = validate_candidate(candidate)
        self.assertTrue(any("fewer than 1 items" in error for error in errors), errors)

    def test_missing_supporting_evidence_fails(self) -> None:
        candidate = fictional_candidate()
        candidate["supporting_evidence"] = []
        errors = validate_candidate(candidate)
        self.assertTrue(any("supporting_evidence" in error for error in errors), errors)

    def test_source_reference_without_excerpt_fails(self) -> None:
        candidate = fictional_candidate()
        del candidate["source"]["references"][0]["excerpt"]
        errors = validate_candidate(candidate)
        self.assertTrue(any("excerpt" in error for error in errors), errors)

    def test_invented_approval_state_fails(self) -> None:
        candidate = fictional_candidate()
        candidate["approval"] = {"state": "auto_approved"}
        errors = validate_candidate(candidate)
        self.assertTrue(any("must be one of" in error for error in errors), errors)

    def test_approval_without_record_reference_fails(self) -> None:
        candidate = approved_candidate()
        del candidate["approval"]["record_reference"]
        errors = validate_candidate(candidate)
        self.assertIn(
            "approval.record_reference is required when state is 'approved'", errors
        )

    def test_approval_without_approver_fails(self) -> None:
        candidate = approved_candidate()
        candidate["approval"]["approved_by"] = "   "
        errors = validate_candidate(candidate)
        self.assertIn("approval.approved_by is required when state is 'approved'", errors)

    def test_production_status_without_approval_fails(self) -> None:
        candidate = fictional_candidate()
        candidate["status"] = "approved_for_recording"
        errors = validate_candidate(candidate)
        self.assertIn(
            "status 'approved_for_recording' requires approval.state 'approved'", errors
        )

    def test_proposed_status_cannot_claim_approval(self) -> None:
        candidate = fictional_candidate()
        candidate["approval"] = {
            "state": "approved",
            "approved_by": "example-approver",
            "approved_at": "2026-01-01",
            "record_reference": "approvals/approval-record.md",
        }
        errors = validate_candidate(candidate)
        self.assertIn(
            "approval.state 'approved' requires status 'approved_for_recording'", errors
        )

    def test_approval_on_unavailable_evidence_only_fails(self) -> None:
        candidate = approved_candidate()
        candidate["supporting_evidence"] = [
            {
                "evidence_id": "evidence-002",
                "evidence_type": "research",
                "validation_status": "unavailable",
            }
        ]
        errors = validate_candidate(candidate)
        self.assertTrue(
            any("validation_status is not 'unavailable'" in error for error in errors),
            errors,
        )

    def test_escaping_record_reference_fails(self) -> None:
        candidate = approved_candidate()
        candidate["approval"]["record_reference"] = "../other-client/approval-record.md"
        errors = validate_candidate(candidate)
        self.assertIn("approval.record_reference must not escape the workspace", errors)

    def test_absolute_record_reference_fails(self) -> None:
        candidate = approved_candidate()
        candidate["approval"]["record_reference"] = "/tmp/approval-record.md"
        errors = validate_candidate(candidate)
        self.assertIn("approval.record_reference must be workspace-relative", errors)

    def test_unexpected_property_fails(self) -> None:
        candidate = fictional_candidate()
        candidate["published_url"] = "https://example.invalid/post"
        errors = validate_candidate(candidate)
        self.assertTrue(any("unexpected property" in error for error in errors), errors)

    def test_client_id_mismatch_fails(self) -> None:
        errors = validate_candidate(fictional_candidate(), client_id="other-client")
        self.assertTrue(any("does not match the active workspace" in e for e in errors), errors)

    def test_client_id_match_passes(self) -> None:
        self.assertEqual(
            validate_candidate(fictional_candidate(), client_id="example-client"), []
        )

    def test_uppercase_identifier_fails(self) -> None:
        candidate = fictional_candidate()
        candidate["client_id"] = "Example-Client"
        errors = validate_candidate(candidate)
        self.assertTrue(any("does not match" in error for error in errors), errors)


class BatchContractTests(unittest.TestCase):
    def test_valid_batch_passes(self) -> None:
        first = fictional_candidate()
        second = fictional_candidate()
        second["candidate_id"] = "example-candidate-02"
        self.assertEqual(validate_batch([first, second], "example-client"), [])

    def test_batch_mixing_clients_fails(self) -> None:
        first = fictional_candidate()
        second = fictional_candidate()
        second["candidate_id"] = "example-candidate-02"
        second["client_id"] = "other-client"
        errors = validate_batch([first, second])
        self.assertTrue(any("mixes multiple clients" in error for error in errors), errors)

    def test_duplicate_candidate_ids_fail(self) -> None:
        first = fictional_candidate()
        second = fictional_candidate()
        errors = validate_batch([first, second])
        self.assertTrue(any("duplicate candidate_id" in error for error in errors), errors)

    def test_non_object_candidate_fails(self) -> None:
        errors = validate_batch(["not-a-candidate"])
        self.assertTrue(any("must be an object" in error for error in errors), errors)


class CommandLineTests(unittest.TestCase):
    def test_cli_reports_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / "good.json"
            good.write_text(json.dumps(fictional_candidate()), encoding="utf-8")
            self.assertEqual(main([str(good), "--client-id", "example-client"]), 0)

            bad = Path(directory) / "bad.json"
            broken = fictional_candidate()
            broken["supporting_evidence"] = []
            bad.write_text(json.dumps(broken), encoding="utf-8")
            self.assertEqual(main([str(bad)]), 1)


class MinimalValidatorTests(unittest.TestCase):
    def test_unsupported_keyword_raises(self) -> None:
        with self.assertRaises(UnsupportedSchema):
            validate({}, {"oneOf": []})

    def test_boolean_is_not_an_integer(self) -> None:
        errors = validate(True, {"type": "integer"})
        self.assertEqual(len(errors), 1)

    def test_schema_document_is_within_the_supported_subset(self) -> None:
        schema = load_schema()
        self.assertEqual(validate(_deep_placeholder(schema), schema), [])


def _deep_placeholder(schema: dict) -> dict:
    """Building a valid instance proves the schema stays inside the subset."""

    return copy.deepcopy(fictional_candidate())


if __name__ == "__main__":
    unittest.main()
