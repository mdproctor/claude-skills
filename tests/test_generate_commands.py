#!/usr/bin/env python3
"""
Tests for scripts/generate_commands.py

Verifies that command files are generated correctly from SKILL.md frontmatter.
Uses temporary directories — never touches the real skills directory.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

# Load generate_commands module directly for unit tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from generate_commands import extract_description, generate_command


REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_commands.py"


def make_skill(directory: Path, name: str, description: str = None, multiline: bool = False) -> Path:
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = directory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    if description is not None:
        if multiline:
            content = (
                f"---\n"
                f"name: {name}\n"
                f"description: >\n"
                f"  {description}\n"
                f"  second line of description.\n"
                f"---\n# {name}\n"
            )
        else:
            content = (
                f"---\n"
                f"name: {name}\n"
                f"description: {description}\n"
                f"---\n# {name}\n"
            )
    else:
        content = f"---\nname: {name}\ndescription: >\n  Use when testing.\n---\n# {name}\n"
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


class TestExtractDescription(unittest.TestCase):
    """Unit tests for the extract_description function."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_extracts_simple_description(self):
        skill_dir = self.test_dir / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription: Use when testing things.\n---\n# body\n"
        )
        desc = extract_description(skill_file)
        self.assertIn("Use when testing things", desc)

    def test_extracts_multiline_description_collapsed(self):
        skill_dir = self.test_dir / "multi-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: multi-skill\ndescription: >\n  Use when first line.\n  Second line here.\n---\n# body\n"
        )
        desc = extract_description(skill_file)
        # Multiline must be collapsed to single line
        self.assertNotIn("\n", desc)
        self.assertIn("Use when first line", desc)
        self.assertIn("Second line here", desc)

    def test_truncates_long_description(self):
        skill_dir = self.test_dir / "long-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        long_desc = "Use when " + "x" * 200
        skill_file.write_text(
            f"---\nname: long-skill\ndescription: >\n  {long_desc}\n---\n# body\n"
        )
        desc = extract_description(skill_file)
        self.assertLessEqual(len(desc), 100)
        self.assertTrue(desc.endswith("..."))

    def test_fallback_when_no_frontmatter(self):
        skill_dir = self.test_dir / "bare-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# No frontmatter at all\n\nJust content.\n")
        desc = extract_description(skill_file)
        self.assertIn("bare-skill", desc)

    def test_fallback_when_no_description_field(self):
        skill_dir = self.test_dir / "nodesc-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: nodesc-skill\n---\n# body\n")
        desc = extract_description(skill_file)
        self.assertIn("nodesc-skill", desc)


class TestGenerateCommand(unittest.TestCase):
    """Unit tests for the generate_command function."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make_skill_file(self, name: str, description: str = "Use when testing.") -> Path:
        skill_dir = self.test_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {name}\ndescription: >\n  {description}\n---\n# {name}\n"
        )
        return skill_file

    def test_creates_commands_dir_and_file(self):
        skill_file = self._make_skill_file("test-skill")
        status = generate_command(skill_file)
        self.assertEqual(status, "created")
        cmd_file = self.test_dir / "test-skill" / "commands" / "test-skill.md"
        self.assertTrue(cmd_file.exists())

    def test_generated_file_has_correct_format(self):
        skill_file = self._make_skill_file("fmt-skill", "Use when formatting.")
        generate_command(skill_file)
        cmd_file = self.test_dir / "fmt-skill" / "commands" / "fmt-skill.md"
        content = cmd_file.read_text()
        # Must have YAML frontmatter with description
        self.assertTrue(content.startswith("---\n"))
        self.assertIn('description: "', content)
        self.assertIn("---\n", content)
        # Must have invoke body
        self.assertIn("`fmt-skill`", content)
        self.assertIn("Invoke", content)

    def test_description_from_frontmatter_in_command_file(self):
        skill_file = self._make_skill_file("desc-skill", "Use when describing things.")
        generate_command(skill_file)
        cmd_file = self.test_dir / "desc-skill" / "commands" / "desc-skill.md"
        content = cmd_file.read_text()
        self.assertIn("Use when describing things", content)

    def test_skips_if_command_file_exists_without_overwrite(self):
        skill_file = self._make_skill_file("skip-skill")
        cmd_dir = self.test_dir / "skip-skill" / "commands"
        cmd_dir.mkdir()
        cmd_file = cmd_dir / "skip-skill.md"
        cmd_file.write_text("original content")
        status = generate_command(skill_file, overwrite=False)
        self.assertEqual(status, "skipped")
        self.assertEqual(cmd_file.read_text(), "original content")

    def test_overwrites_if_all_flag(self):
        skill_file = self._make_skill_file("overwrite-skill")
        cmd_dir = self.test_dir / "overwrite-skill" / "commands"
        cmd_dir.mkdir()
        cmd_file = cmd_dir / "overwrite-skill.md"
        cmd_file.write_text("original content")
        status = generate_command(skill_file, overwrite=True)
        self.assertEqual(status, "updated")
        self.assertNotEqual(cmd_file.read_text(), "original content")

    def test_returns_created_for_new_file(self):
        skill_file = self._make_skill_file("new-skill")
        status = generate_command(skill_file)
        self.assertEqual(status, "created")

    def test_returns_updated_for_existing_file_with_overwrite(self):
        skill_file = self._make_skill_file("update-skill")
        # Generate once first
        generate_command(skill_file)
        # Generate again with overwrite
        status = generate_command(skill_file, overwrite=True)
        self.assertEqual(status, "updated")


class TestGenerateCommandsScript(unittest.TestCase):
    """Subprocess tests for the full generate_commands.py script."""

    def test_exit_code_zero_on_real_repo(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--all"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

    def test_output_shows_already_present(self):
        # Running without --all on a repo where commands exist should report skipped
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("already present", result.stdout)

    def test_skill_dir_without_skill_md_is_skipped(self):
        """A directory without SKILL.md should not produce a command file."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Create a non-skill directory
            (tmp_path / "not-a-skill").mkdir()
            # Create a real skill
            skill_dir = tmp_path / "real-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: real-skill\ndescription: Use when real.\n---\n# real\n"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--all"],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(result.returncode, 0)
            # not-a-skill should have no commands dir
            self.assertFalse((tmp_path / "not-a-skill" / "commands").exists())
            # real-skill should have its command file
            self.assertTrue((skill_dir / "commands" / "real-skill.md").exists())

    def test_idempotent_with_all_flag(self):
        """Running --all twice produces the same output."""
        result1 = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--all"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        result2 = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--all"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result1.returncode, 0)
        self.assertEqual(result2.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
