import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate_repo.py"

VALID_MANIFEST = """schema_version: 1
client_id: "<client-identifier>"
client_name: "<client-display-name>"
approval_gate:
  required_before: production
  approved_by: "<approver>"
  record_location: approvals/approval-record.md
assets:
  context: content-context.md
  demand_map: research/demand-map.csv
  trend_library: research/trend-library.json
  transcript_index: sources/transcript-index.json
  content_history: history/content-history.csv
"""

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
    "schemas/content-candidate.schema.json": "{}\n",
    "templates/client-workspace/content-system.yaml": VALID_MANIFEST,
    "templates/client-workspace/content-context.md": "# Content context\n",
    "templates/client-workspace/research/demand-map.csv": "topic,intent\n",
    "templates/client-workspace/research/trend-library.json": "[]\n",
    "templates/client-workspace/sources/transcript-index.json": "[]\n",
    "templates/client-workspace/history/content-history.csv": "item_id,status\n",
    "templates/client-workspace/approvals/approval-record.md": "# Approval record\n",
    ".github/workflows/validate.yml": "name: Validate\n",
    "scripts/validate_repo.py": "# Fixture validator path\n",
    "scripts/validate_candidate.py": "# Fixture candidate validator path\n",
    "scripts/jsonschema_min.py": "# Fixture schema helper path\n",
    "scripts/new_client.py": "# Fixture workspace scaffold path\n",
    "docs/client-onboarding.md": "# Onboarding\n",
    "docs/skill-evals.md": "# Skill evaluation\n",
    "docs/eval-baselines/social-post-copy-2026-09-18.md": "# Eval baseline\n",
    "tests/test_validate_repo.py": "# Fixture test path\n",
    "tests/test_validate_candidate.py": "# Fixture candidate test path\n",
    "tests/test_new_client.py": "# Fixture workspace test path\n",
    "tests/test_skill_contracts.py": "# Fixture skill contract test path\n",
}

REQUIRED_SKILL_FILES = {
    "skills/intent-drift-audit/SKILL.md": (
        "---\n"
        "name: intent-drift-audit\n"
        "description: Audit completed work against the latest stated intent.\n"
        "---\n\n"
        "# Fixture skill\n"
    ),
    "skills/intent-drift-audit/agents/openai.yaml": "interface:\n  display_name: Fixture\n",
    "skills/social-post-copy/SKILL.md": "---\nname: social-post-copy\ndescription: Write source-grounded social posts.\n---\n# Fixture skill\n",
    "skills/social-post-copy/references/editorial-review.md": "# Editorial review\n",
    "skills/social-post-copy/agents/openai.yaml": "interface:\n  display_name: Fixture\n",
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
    "skills/kallaway-hooks/SKILL.md": (
        "---\n"
        "name: kallaway-hooks\n"
        "description: Write or critique founder-led social video hooks.\n"
        "---\n\n"
        "# Fixture skill\n"
    ),
    "skills/kallaway-hooks/references/kallaway-frameworks.md": "# Frameworks\n",
    "skills/kallaway-hooks/references/provenance.md": "# Provenance\n",
    "skills/transcript-to-content/SKILL.md": (
        "---\n"
        "name: transcript-to-content\n"
        "description: Turn supplied source material into content candidates.\n"
        "---\n\n"
        "# Fixture skill\n"
    ),
    "skills/transcript-to-content/references/client-foundation-and-research.md": "# Foundation\n",
    "skills/transcript-to-content/references/live-hooks-and-production.md": "# Live hooks\n",
    "skills/transcript-to-content/references/output-contract.md": "# Output contract\n",
    "skills/transcript-to-content/references/owner-recognition-filter.md": "# Recognition\n",
    "skills/transcript-to-content/references/scoring-and-routing.md": "# Scoring\n",
    "skills/trend-to-fit/SKILL.md": (
        "---\n"
        "name: trend-to-fit\n"
        "description: Evaluate whether a supplied trend signal fits the client.\n"
        "---\n\n"
        "# Fixture skill\n"
    ),
    "skills/trend-to-fit/references/trend-score.md": "# Trend score\n",
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

    def force_track(self, relative_path: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "add", "-f", "--", relative_path],
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

    def test_manifest_template_absolute_asset_path_fails(self) -> None:
        self.fixture.write(
            "templates/client-workspace/content-system.yaml",
            VALID_MANIFEST.replace(
                "  context: content-context.md",
                "  context: /etc/content-context.md",
            ),
        )
        self.fixture.track_all()
        self.assert_invalid("manifest template path context must be workspace-relative")

    def test_manifest_template_escaping_asset_path_fails(self) -> None:
        self.fixture.write(
            "templates/client-workspace/content-system.yaml",
            VALID_MANIFEST.replace(
                "  context: content-context.md",
                "  context: ../other-client/content-context.md",
            ),
        )
        self.fixture.track_all()
        self.assert_invalid("manifest template path context must not escape the workspace")

    def test_manifest_template_missing_asset_file_fails(self) -> None:
        self.fixture.write(
            "templates/client-workspace/content-system.yaml",
            VALID_MANIFEST.replace(
                "  context: content-context.md",
                "  context: research/not-created.md",
            ),
        )
        self.fixture.track_all()
        self.assert_invalid("manifest template path context does not exist in the template")

    def test_valid_manifest_template_paths_pass(self) -> None:
        self.assert_valid()

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

    def test_missing_kallaway_hook_skill_fails(self) -> None:
        self.assert_valid()
        (self.root / "skills/kallaway-hooks/SKILL.md").unlink()
        self.fixture.track_all()

        self.assert_invalid(
            "missing required skill file: skills/kallaway-hooks/SKILL.md"
        )

    def test_missing_intent_drift_audit_skill_fails(self) -> None:
        self.assert_valid()
        (self.root / "skills/intent-drift-audit/SKILL.md").unlink()
        self.fixture.track_all()

        self.assert_invalid(
            "missing required skill file: skills/intent-drift-audit/SKILL.md"
        )

    def test_force_added_clients_path_fails(self) -> None:
        self.assert_valid()
        self.fixture.write("clients/example/record.md", "Private record.\n")
        self.fixture.force_track("clients/example/record.md")

        self.assert_invalid("blocked tracked path: clients/example/record.md")

    def test_force_added_private_path_fails(self) -> None:
        self.assert_valid()
        self.fixture.write("private/example/record.md", "Private record.\n")
        self.fixture.force_track("private/example/record.md")

        self.assert_invalid("blocked tracked path: private/example/record.md")

    def test_force_added_secrets_path_fails(self) -> None:
        self.assert_valid()
        self.fixture.write("secrets/example/record.md", "Private record.\n")
        self.fixture.force_track("secrets/example/record.md")

        self.assert_invalid("blocked tracked path: secrets/example/record.md")

    def test_tracked_private_path_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "notes.md", "Asset: /" + "Users/example/private-client/logo.png\n"
        )
        self.fixture.track_all()

        self.assert_invalid("blocked private path")

    def test_private_var_folders_path_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "notes.md", "Cache: /" + "private/var/folders/example/output.png\n"
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

    def test_underscore_separated_identity_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "profile.yaml",
            "profile_name: "
            + "Aust"
            + "in_"
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

    def test_home_services_assumptions_inside_skill_fail(self) -> None:
        self.assert_valid()
        for separator in (" ", "-"):
            with self.subTest(separator=separator):
                self.fixture.write(
                    "skills/brand-thumbnail/notes.md",
                    "Use the "
                    + "home"
                    + separator
                    + "services operating defaults.\n",
                )
                self.fixture.track_all()

                self.assert_invalid("blocked public-skill assumption")

    def test_relative_private_asset_reference_inside_skill_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "skills/brand-thumbnail/notes.md",
            "Load " + "private/acme/logo.png before rendering.\n",
        )
        self.fixture.track_all()

        self.assert_invalid("blocked private asset reference in public skill")

    def test_standalone_family_brand_token_inside_skill_fails(self) -> None:
        self.assert_valid()
        self.fixture.write(
            "skills/brand-thumbnail/notes.md",
            "Apply the " + "Will" + "man visual treatment.\n",
        )
        self.fixture.track_all()

        self.assert_invalid("blocked family-brand token in public skill")

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

    def test_populated_json_templates_fail(self) -> None:
        self.assert_valid()
        for relative_path in (
            "templates/client-workspace/research/trend-library.json",
            "templates/client-workspace/sources/transcript-index.json",
        ):
            with self.subTest(relative_path=relative_path):
                self.fixture.write(relative_path, '[{"placeholder": true}]\n')
                self.fixture.track_all()

                self.assert_invalid("JSON template must be an empty array or object")

                self.fixture.write(relative_path, "[]\n")
                self.fixture.track_all()

    def test_csv_template_without_headers_fails(self) -> None:
        self.assert_valid()
        self.fixture.write("templates/client-workspace/research/demand-map.csv", "")
        self.fixture.track_all()

        self.assert_invalid("CSV template has no header")

    def test_populated_csv_templates_fail(self) -> None:
        self.assert_valid()
        cases = {
            "templates/client-workspace/research/demand-map.csv": (
                "topic,intent\nexample,learn\n"
            ),
            "templates/client-workspace/history/content-history.csv": (
                "item_id,status\nexample,draft\n"
            ),
        }
        for relative_path, content in cases.items():
            with self.subTest(relative_path=relative_path):
                self.fixture.write(relative_path, content)
                self.fixture.track_all()

                self.assert_invalid("CSV template contains a data row")

                self.fixture.write(relative_path, REQUIRED_REPOSITORY_FILES[relative_path])
                self.fixture.track_all()

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
        empty_values = (
            "# comment only",
            "null",
            "~",
            '""',
            "''",
            "[]",
            "{}",
            "|",
            ">",
            "!!null",
            "&empty",
        )
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

    def test_plain_and_quoted_frontmatter_values_pass(self) -> None:
        valid_values = (
            ("fixture-thumbnail", "Create a generic thumbnail fixture."),
            ('"fixture-thumbnail"', "'Create a generic thumbnail fixture.'"),
        )
        for name, description in valid_values:
            with self.subTest(name=name):
                self.fixture.write(
                    "skills/brand-thumbnail/SKILL.md",
                    "---\n"
                    f"name: {name}\n"
                    f"description: {description}\n"
                    "---\n\n"
                    "# Fixture skill\n",
                )
                self.fixture.track_all()

                self.assert_valid()

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
            + "man/clever-content-system/security/advisories/new\n",
        )
        self.fixture.track_all()

        self.assert_valid()


if __name__ == "__main__":
    unittest.main()
