#!/usr/bin/env python3
"""Create a private client workspace from the public template.

The public engine must never contain a client workspace. This script refuses to
write inside the repository checkout, refuses to overwrite an existing
workspace, and stamps the client identity into the copied manifest so the
workspace is immediately addressable by client identifier.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates" / "client-workspace"
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

IDENTIFIER_PLACEHOLDER = "<client-identifier>"
DISPLAY_NAME_PLACEHOLDER = "<client-display-name>"


class WorkspaceError(Exception):
    """Raised when a workspace cannot be created safely."""


def _is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def create_workspace(
    client_id: str,
    display_name: str,
    destination: Path,
    template_dir: Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Copy the template into destination/<client_id> and stamp the identity."""

    template_dir = template_dir or TEMPLATE_DIR
    repo_root = repo_root or REPO_ROOT

    if not IDENTIFIER_PATTERN.match(client_id):
        raise WorkspaceError(
            f"client id '{client_id}' must be lowercase letters, digits, and hyphens"
        )
    if not display_name.strip():
        raise WorkspaceError("display name must not be empty")
    if not template_dir.is_dir():
        raise WorkspaceError(f"template directory not found: {template_dir}")

    workspace = destination / client_id
    if _is_inside(workspace, repo_root):
        raise WorkspaceError(
            "refusing to create a client workspace inside the public engine repository"
        )
    if workspace.exists():
        raise WorkspaceError(f"workspace already exists: {workspace}")

    shutil.copytree(template_dir, workspace)

    manifest = workspace / "content-system.yaml"
    text = manifest.read_text(encoding="utf-8")
    if IDENTIFIER_PLACEHOLDER not in text or DISPLAY_NAME_PLACEHOLDER not in text:
        shutil.rmtree(workspace)
        raise WorkspaceError("template manifest is missing its identity placeholders")
    text = text.replace(IDENTIFIER_PLACEHOLDER, client_id, 1)
    text = text.replace(DISPLAY_NAME_PLACEHOLDER, display_name, 1)
    manifest.write_text(text, encoding="utf-8")

    return workspace


def git_init(workspace: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=workspace, check=True)
    gitignore = workspace / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".DS_Store\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id", required=True, help="lowercase workspace identifier")
    parser.add_argument("--display-name", required=True, help="client display name")
    parser.add_argument(
        "--destination",
        required=True,
        type=Path,
        help="private directory that will contain the new workspace",
    )
    parser.add_argument(
        "--git-init", action="store_true", help="initialize a git repository in the workspace"
    )
    args = parser.parse_args(argv)

    try:
        workspace = create_workspace(
            args.client_id, args.display_name, args.destination.expanduser()
        )
        if args.git_init:
            git_init(workspace)
    except WorkspaceError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Created client workspace: {workspace}")
    print("Next: complete the manifest, then run the foundation intake before the first batch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
