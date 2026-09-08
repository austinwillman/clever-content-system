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
from pathlib import Path, PurePosixPath
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
    "skills/social-post-copy/SKILL.md",
    "skills/social-post-copy/references/editorial-review.md",
    "skills/social-post-copy/agents/openai.yaml",
    "skills/brand-thumbnail/SKILL.md",
    "skills/brand-thumbnail/agents/openai.yaml",
    "skills/brand-thumbnail/references/brand-profile-template.md",
    "skills/brand-thumbnail/references/layouts.md",
    "skills/brand-thumbnail/references/output-contract.md",
    "skills/brand-thumbnail/scripts/analyze-video.sh",
    "skills/brand-thumbnail/scripts/verify-image.sh",
    "skills/kallaway-hooks/SKILL.md",
    "skills/kallaway-hooks/references/kallaway-frameworks.md",
    "skills/kallaway-hooks/references/provenance.md",
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
        "templates/client-workspace/research/hook-library.json",
        "templates/client-workspace/research/research-log.json",
        "templates/client-workspace/strategy/client-foundation.json",
        "templates/client-workspace/strategy/topic-bank.json",
    )
)

MANIFEST_PATH = "templates/client-workspace/content-system.yaml"
WORKSPACE_TEMPLATE_PREFIX = "templates/client-workspace/"
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
        if relative_path in EMPTY_JSON_TEMPLATES and value not in ([], {}):
            errors.append(
                f"JSON template must be an empty array or object: {relative_path}"
            )
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


def check_workspace_template_paths(texts: dict[str, str]) -> list[str]:
    """Workspace template asset paths must stay inside the workspace.

    Manifest semantics belong to the engine validator (`scripts/validate-client.mjs`).
    This repository validator keeps only the privacy-relevant question: can a
    template path reach outside the client workspace it describes.
    """

    errors: list[str] = []
    manifest_text = texts.get(MANIFEST_PATH)
    if manifest_text is None:
        return errors

    for match in re.finditer(r"(?m)^\s{2,}([a-z_]+):\s*([^\s#\[{][^\n#]*)$", manifest_text):
        key, raw_value = match.group(1), match.group(2).strip().strip('"\'')
        if "/" not in raw_value and not raw_value.endswith((".md", ".csv", ".json")):
            continue
        if raw_value.startswith(("/", "~")) or raw_value.startswith("\\"):
            errors.append(f"manifest template path {key} must be workspace-relative")
        elif ".." in PurePosixPath(raw_value).parts:
            errors.append(f"manifest template path {key} must not escape the workspace")
        elif f"{WORKSPACE_TEMPLATE_PREFIX}{raw_value}" not in texts:
            errors.append(f"manifest template path {key} does not exist in the template")
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
    errors.extend(check_workspace_template_paths(texts))
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
