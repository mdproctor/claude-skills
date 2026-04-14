#!/usr/bin/env python3
"""
Tests for scripts/validation/validate_temporal.py

Checks stale references: deprecated tools, moved files, renamed skills.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "validate_temporal.py"

sys.path.insert(0, str(SCRIPT_PATH.parent))
from validate_temporal import (
    find_deprecated_tool_usage,
    find_moved_file_references,
    find_renamed_skill_references,
    validate_file,
    DEPRECATED_TOOLS,
    MOVED_FILES,
)


class TestFindDeprecatedToolUsage(unittest.TestCase):
    """Unit tests for deprecated tool detection."""

    def _tmp_file(self, content: str) -> Path:
        self.tmp = TemporaryDirectory()
        f = Path(self.tmp.name) / "SKILL.md"
        f.write_text(content)
        return f

    def tearDown(self):
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def test_detects_TodoWrite_usage(self):
        f = self._tmp_file("Use `TodoWrite` to track tasks.\n")
        issues = find_deprecated_tool_usage(f.read_text(), f)
        self.assertTrue(any(i["tool"] == "TodoWrite" for i in issues))

    def test_detects_TodoRead_usage(self):
        f = self._tmp_file("Call `TodoRead` to get todos.\n")
        issues = find_deprecated_tool_usage(f.read_text(), f)
        self.assertTrue(any(i["tool"] == "TodoRead" for i in issues))

    def test_no_issue_when_no_deprecated_tool(self):
        f = self._tmp_file("Use the Edit tool to modify files.\n")
        issues = find_deprecated_tool_usage(f.read_text(), f)
        self.assertEqual(issues, [])

    def test_deprecated_issue_is_warning_severity(self):
        f = self._tmp_file("TodoWrite is called here.\n")
        issues = find_deprecated_tool_usage(f.read_text(), f)
        for issue in issues:
            if issue["tool"] == "TodoWrite":
                self.assertEqual(issue["severity"], "WARNING")

    def test_reports_correct_line_number(self):
        content = "line one\nline two\nTodoWrite on line three\n"
        f = self._tmp_file(content)
        issues = find_deprecated_tool_usage(f.read_text(), f)
        self.assertTrue(any(i["line"] == 3 for i in issues))

    def test_replacement_info_included(self):
        f = self._tmp_file("Use TodoWrite here.\n")
        issues = find_deprecated_tool_usage(f.read_text(), f)
        self.assertTrue(any("replacement" in i for i in issues))

    def test_all_deprecated_tools_detected(self):
        """Each entry in DEPRECATED_TOOLS should be detected."""
        for tool in DEPRECATED_TOOLS:
            content = f"This file references {tool} in some way.\n"
            f = self._tmp_file(content)
            issues = find_deprecated_tool_usage(f.read_text(), f)
            self.assertTrue(
                any(i["tool"] == tool for i in issues),
                msg=f"Expected {tool} to be flagged as deprecated"
            )


class TestFindMovedFileReferences(unittest.TestCase):
    """Unit tests for moved file detection."""

    def _tmp_file(self, content: str) -> Path:
        self.tmp = TemporaryDirectory()
        f = Path(self.tmp.name) / "SKILL.md"
        f.write_text(content)
        return f

    def tearDown(self):
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def test_detects_old_architecture_path(self):
        f = self._tmp_file("See docs/ARCHITECTURE.md for details.\n")
        issues = find_moved_file_references(f.read_text(), f)
        self.assertTrue(len(issues) > 0)

    def test_includes_new_path_in_message(self):
        f = self._tmp_file("See ARCHITECTURE.md for details.\n")
        issues = find_moved_file_references(f.read_text(), f)
        if issues:
            self.assertTrue(any("DESIGN.md" in i["message"] for i in issues))

    def test_no_issue_for_current_paths(self):
        f = self._tmp_file("See docs/DESIGN.md for current architecture.\n")
        issues = find_moved_file_references(f.read_text(), f)
        self.assertEqual(issues, [])

    def test_moved_file_issue_is_warning(self):
        f = self._tmp_file("Reference: ARCHITECTURE.md\n")
        issues = find_moved_file_references(f.read_text(), f)
        for issue in issues:
            self.assertEqual(issue["severity"], "WARNING")

    def test_all_moved_files_detected(self):
        for old_path in MOVED_FILES:
            f = self._tmp_file(f"See {old_path} for info.\n")
            issues = find_moved_file_references(f.read_text(), f)
            self.assertTrue(
                len(issues) > 0,
                msg=f"Expected '{old_path}' to be flagged as moved"
            )


class TestFindRenamedSkillReferences(unittest.TestCase):
    """Unit tests for renamed skill detection."""

    def _tmp_file(self, content: str) -> Path:
        self.tmp = TemporaryDirectory()
        f = Path(self.tmp.name) / "SKILL.md"
        f.write_text(content)
        return f

    def tearDown(self):
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def test_no_issues_when_renamed_skills_empty(self):
        """Current RENAMED_SKILLS is empty — no spurious issues."""
        f = self._tmp_file("Use `git-commit` for commits.\n")
        issues = find_renamed_skill_references(f.read_text(), f)
        self.assertEqual(issues, [])

    def test_detects_renamed_skill_in_backticks(self):
        """If a renamed skill is added, backtick references are flagged as CRITICAL."""
        from unittest.mock import patch
        import validate_temporal as vt
        with patch.dict(vt.RENAMED_SKILLS, {"old-skill": "new-skill"}):
            f = self._tmp_file("Invoke `old-skill` for this task.\n")
            issues = vt.find_renamed_skill_references(f.read_text(), f)
            self.assertTrue(len(issues) > 0)
            self.assertEqual(issues[0]["severity"], "CRITICAL")
            self.assertEqual(issues[0]["old_name"], "old-skill")
            self.assertEqual(issues[0]["new_name"], "new-skill")

    def test_renamed_skill_not_flagged_without_backticks(self):
        """Plain-text references (not in backticks) are not flagged."""
        from unittest.mock import patch
        import validate_temporal as vt
        with patch.dict(vt.RENAMED_SKILLS, {"old-skill": "new-skill"}):
            f = self._tmp_file("old-skill was the old name.\n")
            issues = vt.find_renamed_skill_references(f.read_text(), f)
            self.assertEqual(issues, [])


class TestValidateFile(unittest.TestCase):
    """Integration tests for validate_file."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_file_has_no_issues(self):
        f = self.test_dir / "clean.md"
        f.write_text("# Clean Skill\n\nNo deprecated tools here.\n")
        issues = validate_file(f)
        self.assertEqual(issues, [])

    def test_returns_warning_on_read_error(self):
        f = self.test_dir / "nonexistent.md"
        issues = validate_file(f)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["severity"], "WARNING")
        self.assertEqual(issues[0]["type"], "read_error")

    def test_detects_multiple_issues_in_one_file(self):
        f = self.test_dir / "multi.md"
        f.write_text("Use TodoWrite and see ARCHITECTURE.md.\n")
        issues = validate_file(f)
        types = {i["type"] for i in issues}
        self.assertIn("deprecated_tool", types)
        self.assertIn("moved_file", types)


class TestValidateTemporalScript(unittest.TestCase):
    """Subprocess tests for the full validate_temporal.py script."""

    def test_real_repo_exits_cleanly(self):
        """The actual repo should pass temporal validation (exit 0 or 2, not 1)."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Exit 0 = clean, exit 2 = warnings only. Exit 1 = CRITICAL (fail)
        self.assertNotEqual(result.returncode, 1,
            msg=f"CRITICAL temporal issues found:\n{result.stderr}")

    def test_deprecated_tool_causes_warning(self):
        """A file with a deprecated tool reference triggers exit 2."""
        with TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Use TodoWrite to track.\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            # Should exit 2 (warnings) since deprecated tool = WARNING
            self.assertEqual(result.returncode, 2,
                msg=f"Expected exit 2 (WARNING), got {result.returncode}\nstderr: {result.stderr}")

    def test_clean_directory_exits_zero(self):
        """A directory with no issues exits 0."""
        with TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
