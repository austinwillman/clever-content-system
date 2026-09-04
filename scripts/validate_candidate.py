#!/usr/bin/env python3
"""Validate content candidates against the public candidate contract.

Structural conformance comes from schemas/content-candidate.schema.json.
This module adds the cross-field rules that the schema cannot express:
approval cannot be asserted without an approval record, a candidate cannot be
routed to production without approval, evidence cannot be entirely unavailable
at approval, and a candidate cannot cross client boundaries.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsonschema_min import validate  # noqa: E402

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "content-candidate.schema.json"

UNAPPROVED_STATUSES = frozenset(("proposed", "refined", "held"))
APPROVAL_EVIDENCE_EXCLUDED = "unavailable"


def load_schema(path: Path | None = None) -> dict:
    return json.loads((path or SCHEMA_PATH).read_text(encoding="utf-8"))


def _check_approval_rules(candidate: dict) -> list[str]:
    errors: list[str] = []
    approval = candidate.get("approval")
    if not isinstance(approval, dict):
        return errors
    state = approval.get("state")
    status = candidate.get("status")

    if state == "approved":
        for field in ("approved_by", "approved_at", "record_reference"):
            value = approval.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"approval.{field} is required when state is 'approved'")
        if status != "approved_for_recording":
            errors.append(
                "approval.state 'approved' requires status 'approved_for_recording'"
            )
        evidence = candidate.get("supporting_evidence") or []
        usable = [
            item
            for item in evidence
            if isinstance(item, dict)
            and item.get("validation_status") != APPROVAL_EVIDENCE_EXCLUDED
        ]
        if not usable:
            errors.append(
                "approval requires at least one supporting_evidence entry whose "
                "validation_status is not 'unavailable'"
            )

    if status == "approved_for_recording" and state != "approved":
        errors.append("status 'approved_for_recording' requires approval.state 'approved'")

    if status in UNAPPROVED_STATUSES and state != "unapproved":
        errors.append(f"status '{status}' requires approval.state 'unapproved'")

    if status == "rejected" and state == "approved":
        errors.append("a rejected candidate cannot carry an approved approval state")

    reference = approval.get("record_reference")
    if isinstance(reference, str) and reference:
        if reference.startswith("/") or reference.startswith("~"):
            errors.append("approval.record_reference must be workspace-relative")
        if ".." in Path(reference).parts:
            errors.append("approval.record_reference must not escape the workspace")

    return errors


def validate_candidate(candidate: dict, client_id: str | None = None,
                       schema: dict | None = None) -> list[str]:
    """Return validation errors for one candidate. Empty means valid."""

    schema = schema or load_schema()
    errors = list(validate(candidate, schema))
    errors.extend(_check_approval_rules(candidate))

    if client_id is not None:
        actual = candidate.get("client_id")
        if actual != client_id:
            errors.append(
                f"client_id '{actual}' does not match the active workspace '{client_id}'"
            )
    return errors


def validate_batch(candidates: list, client_id: str | None = None,
                   schema: dict | None = None) -> list[str]:
    """Validate a batch and enforce batch-level uniqueness and client isolation."""

    schema = schema or load_schema()
    errors: list[str] = []
    if not isinstance(candidates, list):
        return ["batch must be a list of candidates"]

    seen: set[str] = set()
    for position, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            errors.append(f"batch[{position}]: candidate must be an object")
            continue
        for error in validate_candidate(candidate, client_id, schema):
            errors.append(f"batch[{position}]: {error}")
        candidate_id = candidate.get("candidate_id")
        if isinstance(candidate_id, str):
            if candidate_id in seen:
                errors.append(f"batch[{position}]: duplicate candidate_id '{candidate_id}'")
            seen.add(candidate_id)

    client_ids = {
        candidate.get("client_id")
        for candidate in candidates
        if isinstance(candidate, dict)
    }
    if len(client_ids) > 1:
        errors.append(f"batch mixes multiple clients: {sorted(map(str, client_ids))}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="JSON file holding one candidate or a list")
    parser.add_argument("--client-id", default=None, help="expected workspace client identifier")
    args = parser.parse_args(argv)

    payload = json.loads(args.path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        errors = validate_batch(payload, args.client_id)
    else:
        errors = validate_candidate(payload, args.client_id)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Candidate validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
