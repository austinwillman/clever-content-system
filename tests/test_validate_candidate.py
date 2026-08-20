import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate_candidate.py"

sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import validate_candidate  # noqa: E402


VALID_CANDIDATE = {
    "schema_version": "1.0",
    "candidate_id": "candidate-test-0001",
    "created_date": "2000-01-01",
    "status": "proposed",
    "pillar_id": "pillar-1",
    "topic": "example-topic",
    "audience_problem": "Example audience problem.",
    "source": {
        "type": "transcript",
        "references": [
            {
                "reference_id": "reference-one",
                "locator": "sources/example-transcript.md",
                "locator_detail": "00:00:00-00:00:30",
                "retrieved_date": "2000-01-01",
            }
        ],
    },
    "proposal": {
        "hook": "Example hook.",
        "core_claim": {
            "statement": "Example claim.",
            "reference_ids": ["reference-one"],
        },
        "supporting_evidence": [
            {
                "statement": "Example evidence.",
                "reference_ids": ["reference-one"],
                "strength": "paraphrase",
            }
        ],
        "format": {"type": "short_video", "required_assets": ["thumbnail"]},
    },
    "cta_stage": "awareness",
    "assessment": {
        "confidence": "low",
        "confidence_rationale": "Example rationale.",
        "uncertainties": ["Example uncertainty."],
    },
    "approval": {"state": "not_requested"},
}


def candidate(**overrides):
    document = copy.deepcopy(VALID_CANDIDATE)
    document.update(copy.deepcopy(overrides))
    return document


def approved_candidate():
    document = candidate(status="approved")
    document["approval"] = {
        "state": "approved",
        "record_reference": {
            "locator": "approvals/approval-record.md",
            "entry_id": "entry-1",
        },
        "decided_by": "workspace approval owner",
        "decision_date": "2000-01-02",
        "approved_content_digest": validate_candidate.content_digest(document),
    }
    return document


class CandidateContractTests(unittest.TestCase):
    def assert_valid(self, document) -> None:
        self.assertEqual([], validate_candidate.validate_document(document))

    def assert_error(self, document, expected: str) -> None:
        errors = validate_candidate.validate_document(document)
        self.assertTrue(errors, "expected the candidate to fail validation")
        self.assertTrue(
            any(expected in error for error in errors),
            f"expected {expected!r} in {errors!r}",
        )

    def test_valid_proposed_candidate_passes(self) -> None:
        self.assert_valid(candidate())

    def test_empty_candidate_collection_passes(self) -> None:
        self.assert_valid([])

    def test_candidate_collection_passes(self) -> None:
        second = candidate(candidate_id="candidate-test-0002")
        self.assert_valid([candidate(), second])

    def test_duplicate_candidate_identifiers_fail(self) -> None:
        self.assert_error(
            [candidate(), candidate()], "duplicate candidate identifier"
        )

    def test_non_object_candidate_fails(self) -> None:
        self.assert_error("candidate", "must be an object")

    def test_missing_required_field_fails(self) -> None:
        document = candidate()
        del document["audience_problem"]
        self.assert_error(document, "missing required field 'audience_problem'")

    def test_unsupported_field_fails(self) -> None:
        self.assert_error(
            candidate(published=True), "unsupported field 'published'"
        )

    def test_wrong_schema_version_fails(self) -> None:
        self.assert_error(candidate(schema_version="2.0"), "schema_version")

    def test_invalid_candidate_identifier_fails(self) -> None:
        self.assert_error(candidate(candidate_id="Candidate 1"), "candidate_id")

    def test_invalid_created_date_fails(self) -> None:
        self.assert_error(candidate(created_date="2000-13-01"), "created_date")

    def test_overlong_topic_fails(self) -> None:
        self.assert_error(candidate(topic="t" * 121), "topic")

    def test_empty_pillar_fails(self) -> None:
        self.assert_error(candidate(pillar_id="  "), "pillar_id")

    def test_empty_cta_stage_fails(self) -> None:
        self.assert_error(candidate(cta_stage=""), "cta_stage")

    def test_missing_source_references_fail(self) -> None:
        document = candidate()
        document["source"]["references"] = []
        self.assert_error(document, "at least one source reference is required")

    def test_source_reference_without_span_fails(self) -> None:
        document = candidate()
        document["source"]["references"][0]["locator_detail"] = ""
        self.assert_error(document, "locator_detail")

    def test_absolute_source_locator_fails(self) -> None:
        document = candidate()
        document["source"]["references"][0]["locator"] = "/absolute/transcript.md"
        self.assert_error(document, "must be a workspace-relative path")

    def test_escaping_source_locator_fails(self) -> None:
        document = candidate()
        document["source"]["references"][0]["locator"] = "../outside/transcript.md"
        self.assert_error(document, "must be a workspace-relative path")

    def test_duplicate_source_reference_identifiers_fail(self) -> None:
        document = candidate()
        document["source"]["references"].append(
            copy.deepcopy(document["source"]["references"][0])
        )
        self.assert_error(document, "duplicate reference identifier")

    def test_invalid_source_type_fails(self) -> None:
        document = candidate()
        document["source"]["type"] = "rumor"
        self.assert_error(document, "source.type")

    def test_claim_without_source_fails(self) -> None:
        document = candidate()
        document["proposal"]["core_claim"]["reference_ids"] = []
        self.assert_error(
            document, "every claim must cite at least one source reference"
        )

    def test_claim_citing_undeclared_source_fails(self) -> None:
        document = candidate()
        document["proposal"]["core_claim"]["reference_ids"] = ["reference-two"]
        self.assert_error(document, "is not a declared source reference")

    def test_evidence_citing_undeclared_source_fails(self) -> None:
        document = candidate()
        document["proposal"]["supporting_evidence"][0]["reference_ids"] = [
            "reference-two"
        ]
        self.assert_error(document, "is not a declared source reference")

    def test_missing_supporting_evidence_fails(self) -> None:
        document = candidate()
        document["proposal"]["supporting_evidence"] = []
        self.assert_error(document, "at least one supporting item is required")

    def test_invalid_evidence_strength_fails(self) -> None:
        document = candidate()
        document["proposal"]["supporting_evidence"][0]["strength"] = "obvious"
        self.assert_error(document, "strength")

    def test_overlong_hook_fails(self) -> None:
        document = candidate()
        document["proposal"]["hook"] = "h" * 301
        self.assert_error(document, "proposal.hook")

    def test_invalid_format_type_fails(self) -> None:
        document = candidate()
        document["proposal"]["format"]["type"] = "interpretive-dance"
        self.assert_error(document, "proposal.format.type")

    def test_invalid_required_asset_fails(self) -> None:
        document = candidate()
        document["proposal"]["format"]["required_assets"] = ["billboard"]
        self.assert_error(document, "required_assets")

    def test_low_confidence_without_uncertainty_fails(self) -> None:
        document = candidate()
        document["assessment"]["uncertainties"] = []
        self.assert_error(document, "must record at least one uncertainty")

    def test_high_confidence_without_uncertainty_passes(self) -> None:
        document = candidate()
        document["assessment"]["confidence"] = "high"
        document["assessment"]["uncertainties"] = []
        self.assert_valid(document)

    def test_missing_confidence_rationale_fails(self) -> None:
        document = candidate()
        document["assessment"]["confidence_rationale"] = ""
        self.assert_error(document, "confidence_rationale")

    def test_invented_approval_state_fails(self) -> None:
        document = candidate()
        document["approval"]["state"] = "published"
        self.assert_error(document, "approval.state")

    def test_invented_status_fails(self) -> None:
        self.assert_error(candidate(status="published"), "status: must be one of")

    def test_proposed_candidate_carrying_decision_fails(self) -> None:
        document = candidate()
        document["approval"]["decided_by"] = "someone"
        self.assert_error(document, "must not carry an approval decision")

    def test_pending_candidate_carrying_digest_fails(self) -> None:
        document = candidate()
        document["approval"] = {
            "state": "pending",
            "approved_content_digest": validate_candidate.content_digest(document),
        }
        self.assert_error(document, "must not carry an approval decision")

    def test_approved_status_without_approved_state_fails(self) -> None:
        document = candidate(status="approved")
        self.assert_error(
            document, "an approved candidate requires approval.state 'approved'"
        )

    def test_approved_state_without_record_fails(self) -> None:
        document = approved_candidate()
        del document["approval"]["record_reference"]
        self.assert_error(
            document, "an approved candidate requires 'record_reference'"
        )

    def test_approved_state_without_digest_fails(self) -> None:
        document = approved_candidate()
        del document["approval"]["approved_content_digest"]
        self.assert_error(
            document, "an approved candidate requires 'approved_content_digest'"
        )

    def test_approved_candidate_passes(self) -> None:
        self.assert_valid(approved_candidate())

    def test_changed_approved_candidate_fails(self) -> None:
        document = approved_candidate()
        document["proposal"]["hook"] = "A different hook."
        self.assert_error(document, "the approval no longer applies")

    def test_approval_bookkeeping_does_not_change_the_digest(self) -> None:
        document = approved_candidate()
        before = validate_candidate.content_digest(document)
        document["assessment"]["review_notes"] = ["Reviewed."]
        document["status"] = "approved"
        self.assertEqual(before, validate_candidate.content_digest(document))
        self.assert_valid(document)

    def test_approved_record_outside_workspace_fails(self) -> None:
        document = approved_candidate()
        document["approval"]["record_reference"]["locator"] = "/approvals/record.md"
        self.assert_error(document, "must be a workspace-relative path")

    def test_rejected_candidate_requires_a_record(self) -> None:
        document = candidate(status="rejected")
        document["approval"] = {"state": "rejected"}
        self.assert_error(document, "a 'rejected' decision requires 'record_reference'")

    def test_rejected_candidate_with_record_passes(self) -> None:
        document = candidate(status="rejected")
        document["approval"] = {
            "state": "rejected",
            "record_reference": {
                "locator": "approvals/approval-record.md",
                "entry_id": "entry-2",
            },
            "decided_by": "workspace approval owner",
            "decision_date": "2000-01-02",
        }
        self.assert_valid(document)

    def test_rejected_candidate_carrying_digest_fails(self) -> None:
        document = candidate(status="rejected")
        document["approval"] = {
            "state": "rejected",
            "record_reference": {
                "locator": "approvals/approval-record.md",
                "entry_id": "entry-2",
            },
            "decided_by": "workspace approval owner",
            "decision_date": "2000-01-02",
            "approved_content_digest": "a" * 64,
        }
        self.assert_error(
            document, "only an approved candidate may carry an approved content digest"
        )

    def test_status_and_approval_state_cannot_disagree(self) -> None:
        document = approved_candidate()
        document["status"] = "in_review"
        self.assert_error(document, "must not carry a decided approval state")

    def test_expired_approval_cannot_claim_approved_status(self) -> None:
        document = candidate(status="approved")
        document["approval"] = {
            "state": "expired",
            "record_reference": {
                "locator": "approvals/approval-record.md",
                "entry_id": "entry-3",
            },
            "decided_by": "workspace approval owner",
            "decision_date": "2000-01-02",
        }
        self.assert_error(
            document, "an approved candidate requires approval.state 'approved'"
        )

    def test_extensions_pass(self) -> None:
        document = candidate()
        document["extensions"] = {"trend_fit": {"signal_age_days": 3}}
        self.assert_valid(document)

    def test_extension_shadowing_a_contract_field_fails(self) -> None:
        document = candidate()
        document["extensions"] = {"approval": {"state": "approved"}}
        self.assert_error(document, "must not shadow a contract field")

    def test_non_object_extension_fails(self) -> None:
        document = candidate()
        document["extensions"] = {"trend_fit": "approved"}
        self.assert_error(document, "extensions.trend_fit: must be an object")

    def test_example_fixture_is_valid_and_unapproved(self) -> None:
        example_path = (
            REPOSITORY_ROOT / "schemas" / "examples" / "content-candidate.example.json"
        )
        example = json.loads(example_path.read_text(encoding="utf-8"))
        self.assert_valid(example)
        self.assertIn(example["status"], validate_candidate.UNAPPROVED_STATUSES)
        self.assertIn(
            example["approval"]["state"], validate_candidate.UNDECIDED_APPROVAL_STATES
        )


class CandidateValidatorCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *(str(path) for path in paths)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_file_passes(self) -> None:
        path = self.write("candidate.json", json.dumps(candidate()))
        result = self.run_validator(path)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Candidate validation passed", result.stdout)

    def test_invalid_file_fails(self) -> None:
        document = candidate()
        document["source"]["references"] = []
        path = self.write("candidate.json", json.dumps(document))
        result = self.run_validator(path)
        self.assertEqual(1, result.returncode)
        self.assertIn("at least one source reference is required", result.stdout)

    def test_malformed_json_fails(self) -> None:
        path = self.write("candidate.json", "{")
        result = self.run_validator(path)
        self.assertEqual(1, result.returncode)
        self.assertIn("invalid JSON", result.stdout)

    def test_missing_file_fails(self) -> None:
        result = self.run_validator(self.root / "absent.json")
        self.assertEqual(1, result.returncode)
        self.assertIn("could not read candidate file", result.stdout)


if __name__ == "__main__":
    unittest.main()
