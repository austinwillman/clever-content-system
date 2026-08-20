#!/usr/bin/env python3
"""Validate the tracked public repository without third-party dependencies."""

from __future__ import annotations

import argparse
import csv
import json
import re
import stat
import subprocess
import sys
from pathlib import Path


REQUIRED_REPOSITORY_FILES = (
    ".gitignore",
    ".github/workflows/validate.yml",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "docs/architecture.md",
    "schemas/content-system.schema.json",
    "scripts/validate_repo.py",
    "tests/test_validate_repo.py",
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
)

PRIVATE_PATH_PATTERNS = (
    re.compile(r"/" + r"Users/[A-Za-z0-9._-]+(?:/|$)"),
    re.compile(r"/" + r"home/[A-Za-z0-9._-]+(?:/|$)"),
    re.compile(r"(?:[A-Za-z]:)?\\Users\\[A-Za-z0-9._-]+(?:\\|$)", re.IGNORECASE),
)

WILLMAN_SPECIFIC_TOKENS = (
    " ".join(("austin", "willman")),
    "".join(("austin", "willman")),
    " ".join(("willman", "ventures")),
    "".join(("willman", "ic")),
    "-".join(("willman", "thumbnail")),
    " ".join(("human", "leverage")),
    "-".join(("home", "services")),
    " ".join(("home", "services")),
    "#" + "96ff2b",
)

ALLOWED_IDENTITY_TEXT = {
    "LICENSE": (" ".join(("Austin", "Willman")),),
    "SECURITY.md": (
        "https://github.com/"
        + "".join(("austin", "willman"))
        + "/client-content-system/security/advisories/new",
    ),
}


def tracked_files(root: Path) -> tuple[list[str], list[str]]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        return [], [f"could not list tracked files: {detail}"]
    paths = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return [path for path in paths if path], []


def check_required_files(root: Path, tracked: set[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_REPOSITORY_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing required repository file: {relative_path}")
        elif relative_path not in tracked:
            errors.append(f"required repository file is not tracked: {relative_path}")
    for relative_path in REQUIRED_SKILL_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing required skill file: {relative_path}")
        elif relative_path not in tracked:
            errors.append(f"required skill file is not tracked: {relative_path}")
    return errors


def read_public_text(path: Path) -> str:
    data = path.read_bytes()
    if b"\0" in data:
        return ""
    return data.decode("utf-8", errors="replace")


def check_blocked_content(root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in tracked:
        path = root / relative_path
        if not path.is_file():
            continue
        text = read_public_text(path)
        if not text:
            continue
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
    return errors


def check_json_files(root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in tracked:
        if not relative_path.endswith(".json"):
            continue
        path = root / relative_path
        if not path.is_file():
            continue
        try:
            with path.open(encoding="utf-8") as handle:
                json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON in {relative_path}: {exc}")
    return errors


def check_csv_templates(root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in tracked:
        if not (
            relative_path.startswith("templates/") and relative_path.endswith(".csv")
        ):
            continue
        path = root / relative_path
        if not path.is_file():
            continue
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                header = next(csv.reader(handle), None)
        except (OSError, UnicodeError, csv.Error) as exc:
            errors.append(f"could not read CSV template {relative_path}: {exc}")
            continue
        if header is None or not header or any(not cell.strip() for cell in header):
            errors.append(f"CSV template has no header: {relative_path}")
    return errors


def check_shell_scripts(root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in tracked:
        if not relative_path.endswith(".sh"):
            continue
        path = root / relative_path
        if not path.is_file():
            continue
        executable_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if path.stat().st_mode & executable_bits == 0:
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
        values[key.strip()] = value.strip().strip("'\"")
    return values


def check_skill_frontmatter(root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in tracked:
        if Path(relative_path).name != "SKILL.md":
            continue
        path = root / relative_path
        if not path.is_file():
            continue
        frontmatter = parse_frontmatter(read_public_text(path))
        if frontmatter is None or not frontmatter.get("name"):
            errors.append(f"SKILL.md frontmatter is missing name: {relative_path}")
        if frontmatter is None or not frontmatter.get("description"):
            errors.append(f"SKILL.md frontmatter is missing description: {relative_path}")
    return errors


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    tracked, errors = tracked_files(root)
    tracked_set = set(tracked)
    errors.extend(check_required_files(root, tracked_set))
    errors.extend(check_blocked_content(root, tracked))
    errors.extend(check_json_files(root, tracked))
    errors.extend(check_csv_templates(root, tracked))
    errors.extend(check_shell_scripts(root, tracked))
    errors.extend(check_skill_frontmatter(root, tracked))
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
