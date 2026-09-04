"""Contract tests for the installable pipeline skills.

The rule these tests protect: a skill must never resolve a client workspace on
its own. At one client a default is a convenience. At five clients it silently
produces one client's strategy inside another client's batch.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

PIPELINE_SKILLS = ("transcript-to-content", "trend-to-fit")

DEFAULT_WORKSPACE_PATTERNS = (
    re.compile(r"the\s+default\s+is\s+`[^`]*content-system\.yaml`", re.IGNORECASE),
    re.compile(r"default\s+(?:client\s+)?(?:workspace|manifest)\s+is\b", re.IGNORECASE),
    re.compile(r"clients/[a-z0-9-]+/content-system\.yaml", re.IGNORECASE),
)

EXPLICIT_REQUIREMENT_PATTERNS = (
    re.compile(r"no default workspace", re.IGNORECASE),
    re.compile(r"require an explicit", re.IGNORECASE),
)


def skill_documents(skill: str) -> list[Path]:
    root = SKILLS_DIR / skill
    return sorted(root.rglob("*.md"))


class SkillFrontmatterTests(unittest.TestCase):
    def test_every_skill_declares_name_and_description(self) -> None:
        for skill in PIPELINE_SKILLS:
            with self.subTest(skill=skill):
                text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), "missing frontmatter")
                frontmatter = text.split("---\n", 2)[1]
                self.assertRegex(frontmatter, r"(?m)^name:\s*\S+")
                self.assertRegex(frontmatter, r"(?m)^description:\s*\S+")

    def test_skill_name_matches_directory(self) -> None:
        for skill in PIPELINE_SKILLS:
            with self.subTest(skill=skill):
                text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
                match = re.search(r"(?m)^name:\s*(\S+)", text)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1).strip("\"'"), skill)


class NoDefaultClientTests(unittest.TestCase):
    def test_no_skill_document_declares_a_default_workspace(self) -> None:
        for skill in PIPELINE_SKILLS:
            for document in skill_documents(skill):
                text = document.read_text(encoding="utf-8")
                for pattern in DEFAULT_WORKSPACE_PATTERNS:
                    with self.subTest(document=str(document), pattern=pattern.pattern):
                        self.assertIsNone(
                            pattern.search(text),
                            f"{document} declares a default client workspace",
                        )

    def test_each_pipeline_skill_requires_an_explicit_workspace(self) -> None:
        for skill in PIPELINE_SKILLS:
            with self.subTest(skill=skill):
                text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertTrue(
                    any(pattern.search(text) for pattern in EXPLICIT_REQUIREMENT_PATTERNS),
                    f"{skill} does not state that the client workspace must be explicit",
                )


class SkillPortabilityTests(unittest.TestCase):
    def test_skills_carry_no_absolute_local_paths(self) -> None:
        pattern = re.compile(r"/Users/|/home/[a-z]|C:\\\\Users", re.IGNORECASE)
        for skill in PIPELINE_SKILLS:
            for document in skill_documents(skill):
                with self.subTest(document=str(document)):
                    self.assertIsNone(
                        pattern.search(document.read_text(encoding="utf-8")),
                        f"{document} contains an absolute local path",
                    )

    def test_referenced_reference_files_exist(self) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\((references/[^)]+)\)")
        for skill in PIPELINE_SKILLS:
            root = SKILLS_DIR / skill
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            for relative in link_pattern.findall(text):
                with self.subTest(skill=skill, reference=relative):
                    self.assertTrue((root / relative).exists(), f"missing {relative}")


if __name__ == "__main__":
    unittest.main()
