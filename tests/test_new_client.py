"""Tests for private client workspace creation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from new_client import WorkspaceError, create_workspace, main  # noqa: E402


class CreateWorkspaceTests(unittest.TestCase):
    def test_creates_workspace_and_stamps_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = create_workspace(
                "example-client", "Example Client", Path(directory)
            )
            manifest = (workspace / "content-system.yaml").read_text(encoding="utf-8")
            self.assertIn('identifier: "example-client"', manifest)
            self.assertIn('display_name: "Example Client"', manifest)
            self.assertNotIn("<client-identifier>", manifest)
            for relative in (
                "content-context.md",
                "research/demand-map.csv",
                "research/trend-library.json",
                "sources/transcript-index.json",
                "history/content-history.csv",
                "approvals/approval-record.md",
            ):
                self.assertTrue((workspace / relative).exists(), relative)

    def test_refuses_to_write_inside_the_engine_repository(self) -> None:
        with self.assertRaises(WorkspaceError) as caught:
            create_workspace("example-client", "Example Client", REPO_ROOT / "templates")
        self.assertIn("inside the public engine", str(caught.exception))

    def test_refuses_to_overwrite_existing_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            create_workspace("example-client", "Example Client", Path(directory))
            with self.assertRaises(WorkspaceError) as caught:
                create_workspace("example-client", "Example Client", Path(directory))
            self.assertIn("already exists", str(caught.exception))

    def test_rejects_invalid_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for invalid in ("Example Client", "example_client", "-example", ""):
                with self.assertRaises(WorkspaceError):
                    create_workspace(invalid, "Example Client", Path(directory))

    def test_rejects_empty_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(WorkspaceError):
                create_workspace("example-client", "   ", Path(directory))

    def test_two_clients_stay_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = create_workspace("client-one", "Client One", Path(directory))
            second = create_workspace("client-two", "Client Two", Path(directory))
            self.assertNotEqual(first, second)
            self.assertIn(
                'identifier: "client-one"',
                (first / "content-system.yaml").read_text(encoding="utf-8"),
            )
            self.assertIn(
                'identifier: "client-two"',
                (second / "content-system.yaml").read_text(encoding="utf-8"),
            )

    def test_cli_returns_error_code_on_invalid_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code = main(
                [
                    "--client-id",
                    "Bad Id",
                    "--display-name",
                    "Example Client",
                    "--destination",
                    directory,
                ]
            )
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
