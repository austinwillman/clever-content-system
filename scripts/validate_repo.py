#!/usr/bin/env python3
"""Validate the tracked public repository without third-party dependencies."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


REQUIRED_REPOSITORY_FILES = (
    ".gitignore",
    ".github/workflows/validate.yml",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "docs/architecture.md",
    "schemas/content-system.schema.json",
    "schemas/content-candidate.schema.json",
    "scripts/validate_repo.py",
    "scripts/validate_candidate.py",
    "scripts/jsonschema_min.py",
    "scripts/new_client.py",
    "docs/client-onboarding.md",
    "tests/test_validate_repo.py",
    "tests/test_validate_candidate.py",
    "tests/test_new_client.py",
    "tests/test_skill_contracts.py",
    "templates/client-workspace/content-system.yaml",
    "templates/client-workspace/content-context.md",
    "templates/client-workspace/research/demand-map.csv",
    "templates/client-workspace/research/trend-library.json",
    "templates/client-workspace/sources/transcript-index.json",
    "templates/client-workspace/history/content-history.csv",
    "templates/client-workspace/approvals/approval-record.md",
)

REQUIRED_SKILL_FILES = (
    "skills/brand-thumbnail/SKILL.md",
    "skills/brand-thumbnail/agents/openai.yaml",
    "skills/brand-thumbnail/references/brand-profile-template.md",
    "skills/brand-thumbnail/references/layouts.md",
    "skills/brand-thumbnail/references/output-contract.md",
    "skills/brand-thumbnail/scripts/analyze-video.sh",
    "skills/brand-thumbnail/scripts/verify-image.sh",
    "skills/transcript-to-content/SKILL.md",
    "skills/transcript-to-content/references/client-foundation-and-research.md",
    "skills/transcript-to-content/references/live-hooks-and-production.md",
    "skills/transcript-to-content/references/output-contract.md",
    "skills/transcript-to-content/references/owner-recognition-filter.md",
    "skills/transcript-to-content/references/scoring-and-routing.md",
    "skills/trend-to-fit/SKILL.md",
    "skills/trend-to-fit/references/trend-score.md",
)

BLOCKED_TOP_LEVEL_PATHS = frozenset(("clients", "private", "secrets"))

PRIVATE_PATH_PATTERNS = (
    re.compile(r"/" + r"Users/[A-Za-z0-9._-]+(?:/|$)"),
    re.compile(r"/" + r"home/[A-Za-z0-9._-]+(?:/|$)"),
    re.compile(r"/" + r"Volumes/[A-Za-z0-9._ -]+(?:/|$)"),
    re.compile(r"/" + r"private/var/folders(?:/|$)"),
    re.compile(r"(?:[A-Za-z]:)?\\Users\\[A-Za-z0-9._-]+(?:\\|$)", re.IGNORECASE),
)

PERSON_GIVEN_NAME = "aust" + "in"
PERSON_FAMILY_NAME = "will" + "man"

WILLMAN_SPECIFIC_TOKENS = (
    " ".join((PERSON_GIVEN_NAME, PERSON_FAMILY_NAME)),
    "".join((PERSON_GIVEN_NAME, PERSON_FAMILY_NAME)),
    " ".join((PERSON_FAMILY_NAME, "ventures")),
    "".join((PERSON_FAMILY_NAME, "ic")),
    "-".join((PERSON_FAMILY_NAME, "thumbnail")),
    " ".join(("human", "leverage")),
    "#" + "96ff2b",
)

SKILL_SPECIFIC_BLOCKED_TOKENS = (
    " ".join(("home", "services")),
    "-".join(("home", "services")),
)

SKILL_PRIVATE_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9._-])(?:clients|private|secrets)/[^\s)\]}>,'\"]+",
    re.IGNORECASE,
)

EMPTY_JSON_TEMPLATES = frozenset(
    (
        "templates/client-workspace/research/trend-library.json",
        "templates/client-workspace/sources/transcript-index.json",
    )
)

MANIFEST_PATH = "templates/client-workspace/content-system.yaml"
WORKSPACE_TEMPLATE_PREFIX = "templates/client-workspace/"
MANIFEST_TOP_LEVEL_SECTIONS = (
    "schema_version",
    "client",
    "active_90_day_objective",
    "content_pillars",
    "cadence",
    "cta_ladder",
    "locations",
    "approval_gate",
    "fatigue_rules",
    "last_refresh_dates",
)
MANIFEST_LOCATION_KEYS = (
    "content_context",
    "demand_map",
    "trend_library",
    "transcript_index",
    "content_history",
)

ALLOWED_IDENTITY_TEXT = {
    "LICENSE": (" ".join((PERSON_GIVEN_NAME.title(), PERSON_FAMILY_NAME.title())),),
    "SECURITY.md": (
        "https://github.com/"
        + "".join((PERSON_GIVEN_NAME, PERSON_FAMILY_NAME))
        + "/clever-content-system/security/advisories/new",
    ),
}


class IndexEntry(NamedTuple):
    mode: str
    object_id: str
    path: str
    data: bytes


class ManifestSection(NamedTuple):
    value: str
    body: list[str]


def indexed_files(root: Path) -> tuple[dict[str, IndexEntry], list[str]]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--stage", "-z"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        return {}, [f"could not read Git index: {detail}"]

    entries: dict[str, IndexEntry] = {}
    errors: list[str] = []
    blob_cache: dict[str, bytes] = {}
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        try:
            metadata, path_bytes = record.split(b"\t", 1)
            mode_bytes, object_id_bytes, stage_bytes = metadata.split(b" ", 2)
        except ValueError:
            errors.append("could not parse a Git index entry")
            continue
        path = path_bytes.decode("utf-8", errors="surrogateescape")
        stage = stage_bytes.decode("ascii", errors="replace")
        if stage != "0":
            errors.append(f"unmerged Git index entry: {path}")
            continue
        mode = mode_bytes.decode("ascii", errors="replace")
        object_id = object_id_bytes.decode("ascii", errors="replace")
        if object_id not in blob_cache:
            blob_result = subprocess.run(
                ["git", "-C", str(root), "cat-file", "blob", object_id],
                capture_output=True,
                check=False,
            )
            if blob_result.returncode != 0:
                detail = blob_result.stderr.decode("utf-8", errors="replace").strip()
                errors.append(f"could not read indexed blob for {path}: {detail}")
                continue
            blob_cache[object_id] = blob_result.stdout
        entries[path] = IndexEntry(mode, object_id, path, blob_cache[object_id])
    return entries, errors


def check_required_files(index: dict[str, IndexEntry]) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_REPOSITORY_FILES:
        if relative_path not in index:
            errors.append(f"missing required repository file: {relative_path}")
    for relative_path in REQUIRED_SKILL_FILES:
        if relative_path not in index:
            errors.append(f"missing required skill file: {relative_path}")
    return errors


def check_index_paths(index: dict[str, IndexEntry]) -> list[str]:
    errors: list[str] = []
    for relative_path in index:
        top_level = relative_path.split("/", 1)[0]
        if top_level in BLOCKED_TOP_LEVEL_PATHS:
            errors.append(f"blocked tracked path: {relative_path}")
    return errors


def decode_public_text(
    index: dict[str, IndexEntry],
) -> tuple[dict[str, str], list[str]]:
    texts: dict[str, str] = {}
    errors: list[str] = []
    for relative_path, entry in index.items():
        if b"\0" in entry.data:
            errors.append(f"NUL byte in tracked public file: {relative_path}")
            continue
        try:
            texts[relative_path] = entry.data.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"tracked public file is not UTF-8: {relative_path}: {exc}")
    return texts, errors


def check_blocked_content(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for relative_path, original_text in texts.items():
        text = original_text
        for allowed_text in ALLOWED_IDENTITY_TEXT.get(relative_path, ()):
            text = text.replace(allowed_text, "")
        lowered = text.casefold()
        for pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(text):
                errors.append(f"blocked private path in tracked file: {relative_path}")
                break
        for token in WILLMAN_SPECIFIC_TOKENS:
            if token in lowered:
                errors.append(
                    f"blocked Willman-specific token in tracked file: {relative_path}"
                )
                break
        has_given_name = re.search(
            rf"(?<![A-Za-z0-9]){re.escape(PERSON_GIVEN_NAME)}(?![A-Za-z0-9])",
            lowered,
        )
        has_family_name = re.search(
            rf"(?<![A-Za-z0-9]){re.escape(PERSON_FAMILY_NAME)}(?![A-Za-z0-9])",
            lowered,
        )
        if has_given_name and has_family_name:
            errors.append(
                f"blocked Willman-specific identity in tracked file: {relative_path}"
            )
        if relative_path.startswith("skills/brand-thumbnail/"):
            for token in SKILL_SPECIFIC_BLOCKED_TOKENS:
                if token in lowered:
                    errors.append(
                        f"blocked public-skill assumption in tracked file: {relative_path}"
                    )
                    break
            if SKILL_PRIVATE_REFERENCE.search(text):
                errors.append(
                    "blocked private asset reference in public skill: "
                    f"{relative_path}"
                )
            family_name = re.search(
                rf"(?<![A-Za-z0-9]){re.escape(PERSON_FAMILY_NAME)}"
                r"(?![A-Za-z0-9])",
                lowered,
            )
            if family_name:
                errors.append(
                    f"blocked family-brand token in public skill: {relative_path}"
                )
    return errors


def check_json_files(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for relative_path, text in texts.items():
        if not relative_path.endswith(".json"):
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {relative_path}: {exc}")
            continue
        if relative_path in EMPTY_JSON_TEMPLATES and value != []:
            errors.append(f"JSON template must be an empty array: {relative_path}")
    return errors


def check_csv_templates(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for relative_path, text in texts.items():
        if not (
            relative_path.startswith("templates/") and relative_path.endswith(".csv")
        ):
            continue
        try:
            rows = list(csv.reader(io.StringIO(text, newline="")))
        except csv.Error as exc:
            errors.append(f"could not read CSV template {relative_path}: {exc}")
            continue
        header = rows[0] if rows else None
        if header is None or not header or any(not cell.strip() for cell in header):
            errors.append(f"CSV template has no header: {relative_path}")
            continue
        if any(any(cell.strip() for cell in row) for row in rows[1:]):
            errors.append(f"CSV template contains a data row: {relative_path}")
    return errors


def check_shell_scripts(index: dict[str, IndexEntry]) -> list[str]:
    errors: list[str] = []
    for relative_path, entry in index.items():
        if not relative_path.endswith(".sh"):
            continue
        if entry.mode != "100755":
            errors.append(f"shell script is not executable: {relative_path}")
    return errors


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        return None
    values: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def strip_yaml_comment(value: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if quote == '"' and character == "\\":
            escaped = True
            continue
        if quote:
            if character == quote:
                quote = None
            continue
        if character in ("'", '"'):
            quote = character
            continue
        if character == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.strip()


def frontmatter_value_present(value: str | None) -> bool:
    if value is None:
        return False
    scalar = strip_yaml_comment(value).strip()
    if not scalar or scalar.casefold() in {"null", "~"}:
        return False
    if scalar[0] in ("'", '"'):
        if len(scalar) < 2 or scalar[-1] != scalar[0]:
            return False
        return bool(scalar[1:-1].strip())
    if scalar[0] in "[{|>!&*":
        return False
    return True


def check_skill_frontmatter(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for relative_path, text in texts.items():
        if Path(relative_path).name != "SKILL.md":
            continue
        frontmatter = parse_frontmatter(text)
        if frontmatter is None or not frontmatter_value_present(
            frontmatter.get("name")
        ):
            errors.append(f"SKILL.md frontmatter is missing name: {relative_path}")
        if frontmatter is None or not frontmatter_value_present(
            frontmatter.get("description")
        ):
            errors.append(f"SKILL.md frontmatter is missing description: {relative_path}")
    return errors


def narrow_scalar_text(value: str | None) -> str | None:
    if not frontmatter_value_present(value):
        return None
    assert value is not None
    scalar = strip_yaml_comment(value).strip()
    if scalar[0] in ("'", '"'):
        return scalar[1:-1].strip()
    return scalar


def parse_manifest_sections(
    text: str,
) -> tuple[dict[str, ManifestSection], list[str]]:
    sections: dict[str, ManifestSection] = {}
    errors: list[str] = []
    current_name: str | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace():
            if current_name is None:
                errors.append(
                    f"manifest has indented content before a section on line {line_number}"
                )
            else:
                sections[current_name].body.append(line)
            continue
        match = re.fullmatch(r"([a-z][a-z0-9_]*):[ \t]*(.*)", line)
        if match is None:
            errors.append(f"manifest has unsupported syntax on line {line_number}")
            current_name = None
            continue
        name, value = match.groups()
        if name in sections:
            errors.append(f"manifest has duplicate top-level section: {name}")
        sections[name] = ManifestSection(value, [])
        current_name = name
    return sections, errors


def manifest_direct_mapping(section: ManifestSection) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in section.body:
        match = re.fullmatch(r"  ([a-z][a-z0-9_]*):[ \t]*(.*)", line)
        if match is not None:
            key, value = match.groups()
            values[key] = value
    return values


def manifest_reference_error(
    label: str,
    raw_value: str,
    index: dict[str, IndexEntry],
) -> str | None:
    value = narrow_scalar_text(raw_value)
    if value is None:
        return f"manifest path is not workspace-relative: {label}"
    components = value.split("/")
    has_windows_drive = re.match(r"^[A-Za-z]:", value) is not None
    if (
        value.startswith("/")
        or value.startswith("\\")
        or "\\" in value
        or has_windows_drive
        or any(component in ("", ".", "..") for component in components)
    ):
        return f"manifest path is not workspace-relative: {label}"
    indexed_path = WORKSPACE_TEMPLATE_PREFIX + value
    if indexed_path not in index:
        return f"manifest referenced file is missing: {label} -> {indexed_path}"
    return None


def check_manifest_template(
    index: dict[str, IndexEntry], texts: dict[str, str]
) -> list[str]:
    """Check the fixed repository template shape without parsing general YAML."""
    text = texts.get(MANIFEST_PATH)
    if text is None:
        return []
    sections, errors = parse_manifest_sections(text)
    for section_name in MANIFEST_TOP_LEVEL_SECTIONS:
        if section_name not in sections:
            errors.append(f"manifest is missing top-level section: {section_name}")

    schema_section = sections.get("schema_version")
    if schema_section is not None:
        schema_version = narrow_scalar_text(schema_section.value)
        if schema_version != "1.0":
            errors.append("manifest schema_version must be 1.0")

    pillars_section = sections.get("content_pillars")
    if pillars_section is not None:
        pillar_count = sum(line.startswith("  - ") for line in pillars_section.body)
        if pillar_count != 4:
            errors.append("manifest must define exactly four content pillars")

    cadence_section = sections.get("cadence")
    if cadence_section is not None:
        cadence_values = manifest_direct_mapping(cadence_section)
        if narrow_scalar_text(cadence_values.get("cycle_days")) != "6":
            errors.append("manifest cadence cycle_days must be 6")
        cadence_days: list[int] = []
        for line in cadence_section.body:
            match = re.fullmatch(r"    - day:[ \t]*([0-9]+)", line)
            if match is not None:
                cadence_days.append(int(match.group(1)))
        if cadence_days != [1, 2, 3, 4, 5, 6]:
            errors.append("manifest cadence days must be exactly 1 through 6")

    references: list[tuple[str, str]] = []
    locations_section = sections.get("locations")
    if locations_section is not None:
        location_values = manifest_direct_mapping(locations_section)
        for key in MANIFEST_LOCATION_KEYS:
            if key not in location_values:
                errors.append(f"manifest locations is missing {key}")
            else:
                references.append((f"locations.{key}", location_values[key]))

    approval_section = sections.get("approval_gate")
    if approval_section is not None:
        approval_values = manifest_direct_mapping(approval_section)
        for key in ("required_before", "approved_by", "record_location"):
            if key not in approval_values:
                errors.append(f"manifest approval_gate is missing {key}")
        required_before = narrow_scalar_text(approval_values.get("required_before"))
        if "required_before" in approval_values and required_before not in {
            "planning",
            "production",
            "distribution",
        }:
            errors.append("manifest approval_gate required_before is invalid")
        if "approved_by" in approval_values and narrow_scalar_text(
            approval_values["approved_by"]
        ) is None:
            errors.append("manifest approval_gate approved_by must be non-empty")
        if "record_location" in approval_values:
            references.append(
                ("approval_gate.record_location", approval_values["record_location"])
            )

    for label, raw_value in references:
        error = manifest_reference_error(label, raw_value, index)
        if error is not None:
            errors.append(error)
    return errors


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    index, errors = indexed_files(root)
    errors.extend(check_required_files(index))
    errors.extend(check_index_paths(index))
    texts, text_errors = decode_public_text(index)
    errors.extend(text_errors)
    errors.extend(check_blocked_content(texts))
    errors.extend(check_json_files(texts))
    errors.extend(check_csv_templates(texts))
    errors.extend(check_shell_scripts(index))
    errors.extend(check_skill_frontmatter(texts))
    errors.extend(check_manifest_template(index, texts))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root to validate",
    )
    args = parser.parse_args(argv)
    errors = validate_repository(args.root)
    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
