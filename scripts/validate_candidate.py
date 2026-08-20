#!/usr/bin/env python3
"""Validate content candidate documents against the public candidate contract.

This module is the executable form of ``schemas/content-candidate.schema.json``.
It uses only the Python standard library so that skills, tests, and CI can share
one contract implementation.

A candidate is a proposal. Approval, production, and distribution are separate
states that must be recorded explicitly and must never be inferred here.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"

REQUIRED_FIELDS = (
    "schema_version",
    "candidate_id",
    "created_date",
    "status",
    "pillar_id",
    "topic",
    "audience_problem",
    "source",
    "proposal",
    "cta_stage",
    "assessment",
    "approval",
)

OPTIONAL_FIELDS = ("extensions",)

CANDIDATE_STATUSES = ("proposed", "in_review", "needs_revision", "rejected", "approved")
UNAPPROVED_STATUSES = ("proposed", "in_review", "needs_revision")
SOURCE_TYPES = ("transcript", "trend_signal", "demand_signal", "brief")
FORMAT_TYPES = (
    "short_video",
    "long_video",
    "image_post",
    "carousel",
    "text_post",
    "newsletter",
    "audio",
)
REQUIRED_ASSETS = ("thumbnail", "cover_image", "captions", "graphic")
EVIDENCE_STRENGTHS = ("direct_quote", "paraphrase", "observed_metric", "inference")
CONFIDENCE_LEVELS = ("low", "medium", "high")
APPROVAL_STATES = ("not_requested", "pending", "approved", "rejected", "expired")
DECIDED_APPROVAL_STATES = ("approved", "rejected", "expired")
UNDECIDED_APPROVAL_STATES = ("not_requested", "pending")

DECISION_FIELDS = (
    "record_reference",
    "decided_by",
    "decision_date",
    "approved_content_digest",
)

RESERVED_EXTENSION_NAMES = frozenset(REQUIRED_FIELDS)

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
EXTENSION_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
DIGEST_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:")

MAX_TOPIC_LENGTH = 120
MAX_HOOK_LENGTH = 300

# The approved content digest covers the fields a human actually approves.
# Lifecycle and approval bookkeeping are deliberately excluded so that recording
# a decision does not invalidate the decision it records.
DIGEST_FIELDS = (
    "pillar_id",
    "topic",
    "audience_problem",
    "source",
    "proposal",
    "cta_stage",
)


def content_digest(document: dict[str, Any]) -> str:
    """Return the digest of the approvable content of a candidate."""
    payload = {field: document.get(field) for field in DIGEST_FIELDS}
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_object(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label}: must be an object")
        return False
    return True


def _check_keys(
    value: dict[str, Any],
    label: str,
    required: tuple[str, ...],
    optional: tuple[str, ...],
    errors: list[str],
) -> None:
    for key in required:
        if key not in value:
            errors.append(f"{label}: missing required field '{key}'")
    allowed = set(required) | set(optional)
    for key in sorted(value):
        if key not in allowed:
            errors.append(f"{label}: unsupported field '{key}'")


def _check_enum(
    value: Any, label: str, allowed: tuple[str, ...], errors: list[str]
) -> None:
    if value not in allowed:
        errors.append(f"{label}: must be one of {', '.join(allowed)}")


def _check_date(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        errors.append(f"{label}: must be a YYYY-MM-DD date")
        return
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: must be a real calendar date")


def _check_identifier(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not IDENTIFIER_PATTERN.fullmatch(value):
        errors.append(
            f"{label}: must be a lowercase identifier of 3 to 64 characters"
        )


def _check_workspace_relative_path(value: Any, label: str, errors: list[str]) -> None:
    if not _is_nonempty_string(value):
        errors.append(f"{label}: must be a workspace-relative path")
        return
    if (
        value.startswith("/")
        or value.startswith("\\")
        or "\\" in value
        or WINDOWS_DRIVE_PATTERN.match(value) is not None
        or any(component in ("", ".", "..") for component in value.split("/"))
    ):
        errors.append(f"{label}: must be a workspace-relative path")


def _check_note_list(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{label}: must be an array of notes")
        return
    for index, note in enumerate(value):
        if not _is_nonempty_string(note):
            errors.append(f"{label}[{index}]: must be a non-empty string")


def _check_source(value: Any, errors: list[str]) -> set[str]:
    reference_ids: set[str] = set()
    if not _check_object(value, "source", errors):
        return reference_ids
    _check_keys(value, "source", ("type", "references"), (), errors)
    if "type" in value:
        _check_enum(value["type"], "source.type", SOURCE_TYPES, errors)

    references = value.get("references")
    if not isinstance(references, list):
        if "references" in value:
            errors.append("source.references: must be an array")
        return reference_ids
    if not references:
        errors.append("source.references: at least one source reference is required")

    seen: set[str] = set()
    for index, reference in enumerate(references):
        label = f"source.references[{index}]"
        if not _check_object(reference, label, errors):
            continue
        _check_keys(
            reference,
            label,
            ("reference_id", "locator", "locator_detail", "retrieved_date"),
            (),
            errors,
        )
        reference_id = reference.get("reference_id")
        _check_identifier(reference_id, f"{label}.reference_id", errors)
        if isinstance(reference_id, str):
            if reference_id in seen:
                errors.append(f"{label}.reference_id: duplicate reference identifier")
            seen.add(reference_id)
            reference_ids.add(reference_id)
        _check_workspace_relative_path(
            reference.get("locator"), f"{label}.locator", errors
        )
        if not _is_nonempty_string(reference.get("locator_detail")):
            errors.append(
                f"{label}.locator_detail: must identify the span inside the source"
            )
        _check_date(reference.get("retrieved_date"), f"{label}.retrieved_date", errors)
    return reference_ids


def _check_reference_ids(
    value: Any, label: str, declared: set[str], errors: list[str]
) -> None:
    if not isinstance(value, list):
        errors.append(f"{label}: must be an array of source reference identifiers")
        return
    if not value:
        errors.append(f"{label}: every claim must cite at least one source reference")
        return
    seen: set[str] = set()
    for index, reference_id in enumerate(value):
        item_label = f"{label}[{index}]"
        _check_identifier(reference_id, item_label, errors)
        if not isinstance(reference_id, str):
            continue
        if reference_id in seen:
            errors.append(f"{item_label}: duplicate source reference")
        seen.add(reference_id)
        if declared and reference_id not in declared:
            errors.append(
                f"{item_label}: '{reference_id}' is not a declared source reference"
            )


def _check_grounded_statement(
    value: Any, label: str, declared: set[str], errors: list[str]
) -> None:
    if not _check_object(value, label, errors):
        return
    _check_keys(value, label, ("statement", "reference_ids"), (), errors)
    if not _is_nonempty_string(value.get("statement")):
        errors.append(f"{label}.statement: must be a non-empty string")
    _check_reference_ids(
        value.get("reference_ids"), f"{label}.reference_ids", declared, errors
    )


def _check_proposal(value: Any, declared: set[str], errors: list[str]) -> None:
    if not _check_object(value, "proposal", errors):
        return
    _check_keys(
        value,
        "proposal",
        ("hook", "core_claim", "supporting_evidence", "format"),
        (),
        errors,
    )

    hook = value.get("hook")
    if not _is_nonempty_string(hook):
        errors.append("proposal.hook: must be a non-empty string")
    elif len(hook) > MAX_HOOK_LENGTH:
        errors.append(
            f"proposal.hook: must be {MAX_HOOK_LENGTH} characters or fewer"
        )

    _check_grounded_statement(
        value.get("core_claim"), "proposal.core_claim", declared, errors
    )

    evidence = value.get("supporting_evidence")
    if not isinstance(evidence, list):
        if "supporting_evidence" in value:
            errors.append("proposal.supporting_evidence: must be an array")
    elif not evidence:
        errors.append(
            "proposal.supporting_evidence: at least one supporting item is required"
        )
    else:
        for index, item in enumerate(evidence):
            label = f"proposal.supporting_evidence[{index}]"
            if not _check_object(item, label, errors):
                continue
            _check_keys(
                item, label, ("statement", "reference_ids", "strength"), (), errors
            )
            if not _is_nonempty_string(item.get("statement")):
                errors.append(f"{label}.statement: must be a non-empty string")
            _check_reference_ids(
                item.get("reference_ids"), f"{label}.reference_ids", declared, errors
            )
            if "strength" in item:
                _check_enum(
                    item["strength"], f"{label}.strength", EVIDENCE_STRENGTHS, errors
                )

    _check_format(value.get("format"), errors)


def _check_format(value: Any, errors: list[str]) -> None:
    if not _check_object(value, "proposal.format", errors):
        return
    _check_keys(
        value, "proposal.format", ("type", "required_assets"), ("notes",), errors
    )
    if "type" in value:
        _check_enum(value["type"], "proposal.format.type", FORMAT_TYPES, errors)
    assets = value.get("required_assets")
    if not isinstance(assets, list):
        if "required_assets" in value:
            errors.append("proposal.format.required_assets: must be an array")
    else:
        seen: set[str] = set()
        for index, asset in enumerate(assets):
            label = f"proposal.format.required_assets[{index}]"
            _check_enum(asset, label, REQUIRED_ASSETS, errors)
            if isinstance(asset, str):
                if asset in seen:
                    errors.append(f"{label}: duplicate required asset")
                seen.add(asset)
    if "notes" in value and not _is_nonempty_string(value["notes"]):
        errors.append("proposal.format.notes: must be a non-empty string when present")


def _check_assessment(value: Any, errors: list[str]) -> None:
    if not _check_object(value, "assessment", errors):
        return
    _check_keys(
        value,
        "assessment",
        ("confidence", "confidence_rationale", "uncertainties"),
        ("risk_notes", "review_notes"),
        errors,
    )
    confidence = value.get("confidence")
    if "confidence" in value:
        _check_enum(confidence, "assessment.confidence", CONFIDENCE_LEVELS, errors)
    if not _is_nonempty_string(value.get("confidence_rationale")):
        errors.append("assessment.confidence_rationale: must be a non-empty string")
    _check_note_list(value.get("uncertainties"), "assessment.uncertainties", errors)
    for optional_key in ("risk_notes", "review_notes"):
        if optional_key in value:
            _check_note_list(
                value[optional_key], f"assessment.{optional_key}", errors
            )
    uncertainties = value.get("uncertainties")
    if (
        confidence in ("low", "medium")
        and isinstance(uncertainties, list)
        and not uncertainties
    ):
        errors.append(
            "assessment.uncertainties: confidence below high must record at least "
            "one uncertainty"
        )


def _check_approval(value: Any, document: dict[str, Any], errors: list[str]) -> None:
    if not _check_object(value, "approval", errors):
        return
    _check_keys(value, "approval", ("state",), DECISION_FIELDS, errors)
    state = value.get("state")
    if "state" in value:
        _check_enum(state, "approval.state", APPROVAL_STATES, errors)

    if "record_reference" in value:
        reference = value["record_reference"]
        if _check_object(reference, "approval.record_reference", errors):
            _check_keys(
                reference,
                "approval.record_reference",
                ("locator", "entry_id"),
                (),
                errors,
            )
            _check_workspace_relative_path(
                reference.get("locator"), "approval.record_reference.locator", errors
            )
            if not _is_nonempty_string(reference.get("entry_id")):
                errors.append(
                    "approval.record_reference.entry_id: must be a non-empty string"
                )
    if "decided_by" in value and not _is_nonempty_string(value["decided_by"]):
        errors.append("approval.decided_by: must be a non-empty string")
    if "decision_date" in value:
        _check_date(value["decision_date"], "approval.decision_date", errors)
    if "approved_content_digest" in value:
        digest = value["approved_content_digest"]
        if not isinstance(digest, str) or not DIGEST_PATTERN.fullmatch(digest):
            errors.append(
                "approval.approved_content_digest: must be a 64 character sha256 digest"
            )
        elif digest != content_digest(document):
            errors.append(
                "approval.approved_content_digest: does not match the candidate "
                "content, so the approval no longer applies"
            )

    if state == "approved":
        for field in DECISION_FIELDS:
            if field not in value:
                errors.append(f"approval: an approved candidate requires '{field}'")
    elif state in ("rejected", "expired"):
        for field in ("record_reference", "decided_by", "decision_date"):
            if field not in value:
                errors.append(f"approval: a '{state}' decision requires '{field}'")
        if "approved_content_digest" in value:
            errors.append(
                "approval.approved_content_digest: only an approved candidate may "
                "carry an approved content digest"
            )
    elif state in UNDECIDED_APPROVAL_STATES:
        for field in DECISION_FIELDS:
            if field in value:
                errors.append(
                    f"approval.{field}: a '{state}' candidate must not carry an "
                    "approval decision"
                )


def _check_status_coupling(document: dict[str, Any], errors: list[str]) -> None:
    status = document.get("status")
    approval = document.get("approval")
    if not isinstance(approval, dict):
        return
    state = approval.get("state")
    if status == "approved" and state != "approved":
        errors.append(
            "status: an approved candidate requires approval.state 'approved'"
        )
    if status == "rejected" and state != "rejected":
        errors.append(
            "status: a rejected candidate requires approval.state 'rejected'"
        )
    if status in UNAPPROVED_STATUSES and state in ("approved", "rejected"):
        errors.append(
            f"status: a '{status}' candidate must not carry a decided approval state"
        )


def _check_extensions(value: Any, errors: list[str]) -> None:
    if not _check_object(value, "extensions", errors):
        return
    for name in sorted(value):
        if not EXTENSION_NAME_PATTERN.fullmatch(name):
            errors.append(f"extensions.{name}: name must be lower snake case")
        if name in RESERVED_EXTENSION_NAMES:
            errors.append(
                f"extensions.{name}: must not shadow a contract field"
            )
        if not isinstance(value[name], dict):
            errors.append(f"extensions.{name}: must be an object")


def validate_candidate(document: Any) -> list[str]:
    """Return contract errors for one candidate document."""
    errors: list[str] = []
    if not _check_object(document, "candidate", errors):
        return errors

    _check_keys(document, "candidate", REQUIRED_FIELDS, OPTIONAL_FIELDS, errors)

    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: must be '{SCHEMA_VERSION}'")
    _check_identifier(document.get("candidate_id"), "candidate_id", errors)
    _check_date(document.get("created_date"), "created_date", errors)
    if "status" in document:
        _check_enum(document["status"], "status", CANDIDATE_STATUSES, errors)
    if not _is_nonempty_string(document.get("pillar_id")):
        errors.append("pillar_id: must reference a configured workspace pillar")
    topic = document.get("topic")
    if not _is_nonempty_string(topic):
        errors.append("topic: must be a non-empty string")
    elif len(topic) > MAX_TOPIC_LENGTH:
        errors.append(f"topic: must be {MAX_TOPIC_LENGTH} characters or fewer")
    if not _is_nonempty_string(document.get("audience_problem")):
        errors.append("audience_problem: must be a non-empty string")
    if not _is_nonempty_string(document.get("cta_stage")):
        errors.append("cta_stage: must name a stage from the workspace CTA ladder")

    declared = _check_source(document.get("source"), errors)
    _check_proposal(document.get("proposal"), declared, errors)
    _check_assessment(document.get("assessment"), errors)
    _check_approval(document.get("approval"), document, errors)
    _check_status_coupling(document, errors)
    if "extensions" in document:
        _check_extensions(document["extensions"], errors)
    return errors


def validate_document(document: Any) -> list[str]:
    """Validate a single candidate or an array of candidates."""
    if isinstance(document, list):
        errors: list[str] = []
        seen: set[str] = set()
        for index, candidate in enumerate(document):
            for error in validate_candidate(candidate):
                errors.append(f"[{index}] {error}")
            if isinstance(candidate, dict):
                candidate_id = candidate.get("candidate_id")
                if isinstance(candidate_id, str):
                    if candidate_id in seen:
                        errors.append(
                            f"[{index}] candidate_id: duplicate candidate identifier"
                        )
                    seen.add(candidate_id)
        return errors
    return validate_candidate(document)


def validate_candidate_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"could not read candidate file: {exc}"]
    except UnicodeDecodeError as exc:
        return [f"candidate file is not UTF-8: {exc}"]
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]
    return validate_document(document)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="candidate JSON files, each holding one candidate or an array",
    )
    args = parser.parse_args(argv)
    failed = False
    for path in args.paths:
        errors = validate_candidate_file(path)
        if errors:
            failed = True
            print(f"Candidate validation failed: {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"Candidate validation passed: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
