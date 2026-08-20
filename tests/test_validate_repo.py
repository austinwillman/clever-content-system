import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate_repo.py"

REQUIRED_REPOSITORY_FILES = {
    ".gitignore": "clients/\nprivate/\nsecrets/\n.env\n.env.*\n!.env.example\n",
    "LICENSE": (
        "MIT License\n\nCopyright (c) 2026 "
        + "Aust"
        + "in "
        + "Will"
        + "man\n"
    ),
    "README.md": "# Fixture repository\n",
    "SECURITY.md": "# Security\n",
    "docs/architecture.md": "# Architecture\n",
    "schemas/content-system.schema.json": "{}\n",
    "templates/client-workspace/content-system.yaml": "schema_version: 1\n",
    "templates/client-workspace/content-context.md": "# Content context\n",
    "templates/client-workspace/research/demand-map.csv": "topic,intent\n",
    "templates/client-workspace/research/trend-library.json": "[]\n",
    "templates/client-workspace/sources/transcript-index.json": "[]\n",
    "templates/client-workspace/history/content-history.csv": "item_id,status\n",
    "templates/client-workspace/approvals/approval-record.md": "# Approval record\n",
    ".github/workflows/validate.yml": "name: Validate\n",
    "scripts/validate_repo.py": "# Fixture validator path\n",
    "tests/test_validate_repo.py": "# Fixture test path\n",
}

REQUIRED_SKILL_FILES = {
    "skills/brand-thumbnail/SKILL.md": (
        "---\n"
        "name: fixture-thumbnail\n"
        "description: Create a generic thumbnail fixture.\n"
        "---\n\n"
        "# Fixture skill\n"
    ),
    "skills/brand-thumbnail/agents/openai.yaml": "interface:\n  display_name: Fixture\n",
    "skills/brand-thumbnail/references/brand-profile-template.md": "# Brand profile\n",
    "skills/brand-thumbnail/references/layouts.md": "# Layouts\n",
    "skills/brand-thumbnail/references/output-contract.md": "# Output contract\n",
    "skills/brand-thumbnail/scripts/analyze-video.sh": "#!/bin/sh\nexit 0\n",
    "skills/brand-thumbnail/scripts/verify-image.sh": "#!/bin/sh\nexit 0\n",
}


class RepositoryFixture:
    def __init__(self, root: Path) -> None:
        self.root = root

    def create(self) -> None:
        for relative_path, content in {
            **REQUIRED_REPOSITORY_FILES,
            **REQUIRED_SKILL_FILES,
        }.items():
            self.write(relative_path, content)

        for relative_path in REQUIRED_SKILL_FILES:
            if relative_path.endswith(".sh"):
                (self.root / relative_path).chmod(0o755)

        subprocess.run(
            ["git", "init", "-q", str(self.root)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.track_all()

    def write(self, relative_path: str, content: str) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_bytes(self, relative_path: str, content: bytes) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def track_all(self) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "add", "-A"],
            check=True,
            capture_output=True,
            text=True,
        )


class ValidateRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.fixture = RepositoryFixture(self.root)
        self.fixture.create()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_valid(self) -> None:
        result = self.run_validator()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Repository validation passed", result.stdout)

    def assert_invalid(self, expected_message: str) -> None:
        result = self.run_validator()
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(expected_message, result.stdout + result.stderr)

    def test_valid_repository_passes(self) -> None:
        self.assert_valid()

    def test_missing_required_repository_file_fails(self) -> None:
        self.assert_valid()
        (self.root / "README.md").unlink()
        self.fixture.track_all()

        self.assert_invalid("missing required repository file: README.md")

    def test_missing_required_skill_file_fails(self) -> None:
        self.assert_valid()
        (self.root / "skills/brand-thumbnail/references/layouts.md").unlink()
        self.fixture.track_all()

        self.assert_invalid(
            "missing required skill file: skills/brand-thumbnail/references/layouts.md"
        )

    def test_tracked_private_path_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "notes.md", "Asset: /" + "Users/example/private-client/logo.png\n"
        )
        self.fixture.track_all()

        self.assert_invalid("blocked private path")

    def test_tracked_willman_specific_token_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "notes.md", "Use the " + "Willman" + " Ventures brand treatment.\n"
        )
        self.fixture.track_all()

        self.assert_invalid("blocked Willman-specific token")

    def test_staged_private_content_hidden_by_safe_worktree_copy_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "notes.md", "Asset: /" + "Users/example/private-client/logo.png\n"
        )
        self.fixture.track_all()
        self.fixture.write("notes.md", "No private content here.\n")

        self.assert_invalid("blocked private path")

    def test_tracked_symlink_target_blob_is_scanned(self) -> None:
        self.assert_valid()
        link = self.root / "asset-link"
        link.symlink_to("/" + "Vol" + "umes/private-client/logo.png")
        self.fixture.track_all()

        self.assert_invalid("blocked private path")

    def test_nul_containing_tracked_blob_fails(self) -> None:
        self.assert_valid()
        self.fixture.write_bytes("notes.md", b"public text\x00hidden content\n")
        self.fixture.track_all()

        self.assert_invalid("NUL byte in tracked public file")

    def test_separated_identity_fields_fail(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "profile.yaml",
            "first_name: "
            + "Aust"
            + "in\nlast_name: "
            + "Will"
            + "man\n",
        )
        self.fixture.track_all()

        self.assert_invalid("blocked Willman-specific identity")

    def test_generic_home_services_market_content_outside_skill_passes(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "market.md",
            "A generic "
            + "home"
            + " services and "
            + "home"
            + "-services market overview.\n",
        )
        self.fixture.track_all()

        self.assert_valid()

    def test_hyphenated_home_services_assumption_inside_skill_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "skills/brand-thumbnail/notes.md",
            "Use the " + "home" + "-services operating defaults.\n",
        )
        self.fixture.track_all()

        self.assert_invalid("blocked public-skill assumption")

    def test_untracked_content_is_not_scanned(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "local-notes.md", "Asset: /" + "Users/example/private-client/logo.png\n"
        )

        self.assert_valid()

    def test_invalid_json_fails(self) -> None:
        self.assert_valid()
        self.fixture.write("templates/client-workspace/research/trend-library.json", "{\n")
        self.fixture.track_all()

        self.assert_invalid("invalid JSON")

    def test_csv_template_without_headers_fails(self) -> None:
        self.assert_valid()
        self.fixture.write("templates/client-workspace/research/demand-map.csv", "")
        self.fixture.track_all()

        self.assert_invalid("CSV template has no header")

    def test_staged_non_executable_mode_hidden_by_worktree_mode_fails(self) -> None:
        self.assert_valid()
        script = self.root / "skills/brand-thumbnail/scripts/analyze-video.sh"
        script.chmod(0o644)
        self.fixture.track_all()
        script.chmod(0o755)

        self.assert_invalid("shell script is not executable")

    def test_skill_frontmatter_without_name_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "skills/brand-thumbnail/SKILL.md",
            "---\ndescription: Generic fixture.\n---\n\n# Fixture skill\n",
        )
        self.fixture.track_all()

        self.assert_invalid("SKILL.md frontmatter is missing name")

    def test_skill_frontmatter_without_description_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "skills/brand-thumbnail/SKILL.md",
            "---\nname: fixture-thumbnail\n---\n\n# Fixture skill\n",
        )
        self.fixture.track_all()

        self.assert_invalid("SKILL.md frontmatter is missing description")

    def test_semantically_empty_skill_frontmatter_values_fail(self) -> None:
        empty_values = ("# comment only", "null", "~", '""', "''")
        for value in empty_values:
            with self.subTest(value=value):
                self.fixture.write(
                    "skills/brand-thumbnail/SKILL.md",
                    "---\n"
                    "name: fixture-thumbnail\n"
                    f"description: {value}\n"
                    "---\n\n"
                    "# Fixture skill\n",
                )
                self.fixture.track_all()

                self.assert_invalid("SKILL.md frontmatter is missing description")

    def test_comment_only_skill_name_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "skills/brand-thumbnail/SKILL.md",
            "---\n"
            "name: # comment only\n"
            "description: Generic fixture.\n"
            "---\n\n"
            "# Fixture skill\n",
        )
        self.fixture.track_all()

        self.assert_invalid("SKILL.md frontmatter is missing name")

    def test_required_identity_exceptions_are_narrowly_allowed(self) -> None:
        self.fixture.write(
            "SECURITY.md",
            "Report privately: "
            "https://github.com/"
            + "aust"
            + "in"
            + "will"
            + "man/client-content-system/security/advisories/new\n",
        )
        self.fixture.track_all()

        self.assert_valid()


if __name__ == "__main__":
    unittest.main()
