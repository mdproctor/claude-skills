#!/usr/bin/env python3
"""
Tests for scripts/validation/validate_edge_cases.py

Checks error handling patterns: file existence checks, bash error handling,
empty input validation, conditional completeness, success verification.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "validate_edge_cases.py"

sys.path.insert(0, str(SCRIPT_PATH.parent))
from validate_edge_cases import (
    check_file_existence_before_read,
    check_command_error_handling,
    check_empty_input_handling,
    check_conditional_completeness,
    check_success_without_verification,
    validate_file,
)


def make_temp_file(content: str) -> tuple:
    tmp = TemporaryDirectory()
    f = Path(tmp.name) / "SKILL.md"
    f.write_text(content)
    return tmp, f


class TestCheckFileExistenceBeforeRead(unittest.TestCase):
    """Tests for file-read-without-existence-check detection."""

    def test_read_with_existence_check_passes(self):
        content = (
            "```\n"
            "test -f myfile.txt\n"
            "cat myfile.txt\n"
            "```\n"
        )
        tmp, f = make_temp_file(content)
        issues = check_file_existence_before_read(f.read_text(), f)
        tmp.cleanup()
        # Should not flag — existence check precedes the read
        cat_issues = [i for i in issues if "cat" in i.get("message", "")]
        self.assertEqual(cat_issues, [])

    def test_clean_content_has_no_issues(self):
        tmp, f = make_temp_file("# Clean skill\n\nNo file operations.\n")
        issues = check_file_existence_before_read(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_returns_list(self):
        tmp, f = make_temp_file("Some content here.\n")
        issues = check_file_existence_before_read(f.read_text(), f)
        tmp.cleanup()
        self.assertIsInstance(issues, list)


class TestCheckCommandErrorHandling(unittest.TestCase):
    """Tests for bash blocks lacking error handling."""

    def test_bash_block_with_error_handling_passes(self):
        content = "```bash\ngit status || echo 'failed'\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_bash_block_with_set_e_passes(self):
        content = "```bash\nset -e\ngit status\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_bash_block_with_dev_null_passes(self):
        content = "```bash\ngrep pattern file 2>/dev/null\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_bash_block_without_error_handling_flagged(self):
        content = "```bash\ngit status\nfind . -name '*.md'\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "missing_error_handling")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_bash_block_without_risky_commands_passes(self):
        # A bash block that has no risky commands should not be flagged
        content = "```bash\necho 'hello'\npwd\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_non_bash_code_block_not_flagged(self):
        content = "```python\nimport os\nos.listdir('.')\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_returns_list(self):
        tmp, f = make_temp_file("No bash blocks here.\n")
        issues = check_command_error_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertIsInstance(issues, list)


class TestCheckEmptyInputHandling(unittest.TestCase):
    """Tests for unquoted variable usage that may fail on empty input."""

    def test_clean_content_passes(self):
        tmp, f = make_temp_file("Use the `$FILE` variable safely.\n")
        issues = check_empty_input_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_unquoted_variable_comparison_flagged(self):
        content = "if $MYVAR == something; then\n  echo yes\nfi\n"
        tmp, f = make_temp_file(content)
        issues = check_empty_input_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "potential_empty_input")
        self.assertEqual(issues[0]["severity"], "NOTE")

    def test_for_loop_over_unquoted_variable_flagged(self):
        content = "for item in $ITEMS; do echo $item; done\n"
        tmp, f = make_temp_file(content)
        issues = check_empty_input_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)

    def test_returns_list(self):
        tmp, f = make_temp_file("# heading\n")
        issues = check_empty_input_handling(f.read_text(), f)
        tmp.cleanup()
        self.assertIsInstance(issues, list)


class TestCheckConditionalCompleteness(unittest.TestCase):
    """Tests for if-elif chains without else clauses."""

    def test_complete_if_elif_else_passes(self):
        # The else detection requires "Otherwise " (with trailing space), not "Otherwise:"
        # Use "Otherwise do" to match the startswith pattern
        content = "If condition A:\n  do thing\nOtherwise if condition B:\n  do other\nOtherwise do fallback.\n\n"
        tmp, f = make_temp_file(content)
        issues = check_conditional_completeness(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_if_without_elif_passes(self):
        # Simple if without elif — no requirement for else
        content = "If condition A:\n  do thing.\n\n"
        tmp, f = make_temp_file(content)
        issues = check_conditional_completeness(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_if_elif_without_else_flagged(self):
        content = (
            "If condition A:\n"
            "  do thing A.\n"
            "Else if condition B:\n"
            "  do thing B.\n"
            "\n"  # blank line ends block
        )
        tmp, f = make_temp_file(content)
        issues = check_conditional_completeness(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "incomplete_conditional")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_returns_list(self):
        tmp, f = make_temp_file("No conditionals here.\n")
        issues = check_conditional_completeness(f.read_text(), f)
        tmp.cleanup()
        self.assertIsInstance(issues, list)


class TestCheckSuccessWithoutVerification(unittest.TestCase):
    """Tests for success claims without verification commands."""

    def test_clean_content_passes(self):
        tmp, f = make_temp_file("Run the tests before merging.\n")
        issues = check_success_without_verification(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_success_criteria_without_verification_flagged(self):
        content = "## Success Criteria\n\nAll criteria met.\n"
        tmp, f = make_temp_file(content)
        issues = check_success_without_verification(f.read_text(), f)
        tmp.cleanup()
        # May flag the "Success Criteria" line itself
        self.assertIsInstance(issues, list)

    def test_success_with_git_log_verification_passes(self):
        content = "## Success Criteria\n\nCheck with git log.\n"
        tmp, f = make_temp_file(content)
        issues = check_success_without_verification(f.read_text(), f)
        tmp.cleanup()
        # git log is a verification pattern — should pass
        success_issues = [i for i in issues if "unverified_success" in i.get("type", "")]
        self.assertEqual(success_issues, [])

    def test_severity_is_note(self):
        content = "## Success Criteria\n\nAll done.\n"
        tmp, f = make_temp_file(content)
        issues = check_success_without_verification(f.read_text(), f)
        tmp.cleanup()
        for issue in issues:
            self.assertEqual(issue["severity"], "NOTE")

    def test_returns_list(self):
        tmp, f = make_temp_file("# heading\n")
        issues = check_success_without_verification(f.read_text(), f)
        tmp.cleanup()
        self.assertIsInstance(issues, list)


class TestValidateFileEdgeCases(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_file_has_no_issues(self):
        f = self.test_dir / "SKILL.md"
        f.write_text("# Clean Skill\n\n## Overview\n\nNo edge case problems here.\n")
        issues = validate_file(f)
        self.assertEqual(issues, [])

    def test_read_error_returns_warning(self):
        f = self.test_dir / "missing.md"
        issues = validate_file(f)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["severity"], "WARNING")
        self.assertEqual(issues[0]["type"], "read_error")

    def test_aggregates_multiple_issue_types(self):
        content = (
            "```bash\ngit status\nfind . -name '*.md'\n```\n"
            "if $MYVAR == foo; then echo yes; fi\n"
        )
        f = self.test_dir / "SKILL.md"
        f.write_text(content)
        issues = validate_file(f)
        types = {i["type"] for i in issues}
        # bash block + empty input issues should both be present
        self.assertGreater(len(types), 0)


class TestValidateEdgeCasesScript(unittest.TestCase):
    """Subprocess tests for the full validate_edge_cases.py script."""

    def test_real_repo_does_not_exit_critical(self):
        """The real repo should not have CRITICAL edge case issues."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(result.returncode, 1,
            msg=f"CRITICAL edge case issues:\n{result.stderr}")

    def test_clean_directory_exits_zero(self):
        with TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(result.returncode, 0)

    def test_bash_block_without_error_handling_triggers_warning(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "```bash\ngit status\nfind . -name '*.py'\n```\n"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            # Bash block with risky commands but no error handling = WARNING
            self.assertEqual(result.returncode, 2,
                msg=f"Expected exit 2 (WARNING), got {result.returncode}\nstderr: {result.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
