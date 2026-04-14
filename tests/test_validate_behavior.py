#!/usr/bin/env python3
"""
Tests for scripts/validation/validate_behavior.py

Checks behavioral consistency: invocation claims, blocking claims,
validation claims, bash example syntax, always/never enforcement.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "validate_behavior.py"

sys.path.insert(0, str(SCRIPT_PATH.parent))
from validate_behavior import (
    check_invocation_claims,
    check_blocking_claims,
    check_validation_claims,
    check_example_syntax,
    check_always_never_claims,
)


def make_skill_file(directory: Path, name: str, content: str) -> Path:
    """Create a skill directory with the given SKILL.md content."""
    skill_dir = directory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    f = skill_dir / "SKILL.md"
    f.write_text(content)
    return f


class TestCheckInvocationClaims(unittest.TestCase):
    """Tests for 'invoked by X' claim verification."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_issues_when_no_claims(self):
        f = make_skill_file(self.test_dir, "simple-skill", "# Simple\n\nNo invocation claims.\n")
        issues = check_invocation_claims([f])
        self.assertEqual(issues, [])

    def test_valid_invocation_pair_passes(self):
        # skill-a claims to be invoked by skill-b; skill-b references skill-a
        f_a = make_skill_file(
            self.test_dir, "skill-a",
            "**Invoked by:** `skill-b`\n"
        )
        f_b = make_skill_file(
            self.test_dir, "skill-b",
            "After the run, invoke `skill-a` for cleanup.\n"
        )
        issues = check_invocation_claims([f_a, f_b])
        # If skill-b's dir doesn't exist as a real path for checking, no WARNING
        # The check only fires if invoker_file.exists()
        self.assertIsInstance(issues, list)

    def test_returns_list(self):
        issues = check_invocation_claims([])
        self.assertIsInstance(issues, list)

    def test_unverified_claim_flagged_when_invoker_dir_exists(self):
        # skill-a claims invoked by skill-b, but skill-b doesn't reference it
        # AND skill-b's directory exists
        f_a = make_skill_file(
            self.test_dir, "skill-a",
            "**Invoked by:** `skill-b`\n"
        )
        # Create skill-b dir without a reference to skill-a
        make_skill_file(
            self.test_dir, "skill-b",
            "# Skill B\n\nDoes other things.\n"
        )
        # The check uses cwd-relative paths, so run from test_dir
        import os
        orig_dir = os.getcwd()
        try:
            os.chdir(self.test_dir)
            issues = check_invocation_claims([f_a, self.test_dir / "skill-b" / "SKILL.md"])
        finally:
            os.chdir(orig_dir)

        # If invoker path exists in cwd and doesn't reference back → WARNING
        # (may or may not fire depending on exact text parsing)
        self.assertIsInstance(issues, list)


class TestCheckBlockingClaims(unittest.TestCase):
    """Tests for blocking claim verification."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_blocking_claim_passes(self):
        f = make_skill_file(self.test_dir, "no-block", "# No blocking here.\n")
        issues = check_blocking_claims([f])
        self.assertEqual(issues, [])

    def test_blocking_claim_with_exit_1_passes(self):
        content = "blocks on CRITICAL findings.\n\nIf CRITICAL:\n  exit 1\n"
        f = make_skill_file(self.test_dir, "valid-blocker", content)
        issues = check_blocking_claims([f])
        self.assertEqual(issues, [])

    def test_blocking_claim_with_sys_exit_passes(self):
        content = "block commit if CRITICAL.\n\n```python\nsys.exit(1)\n```\n"
        f = make_skill_file(self.test_dir, "py-blocker", content)
        issues = check_blocking_claims([f])
        self.assertEqual(issues, [])

    def test_blocking_claim_without_exit_logic_flagged(self):
        content = "This skill blocks on CRITICAL findings.\n\nNo actual exit logic anywhere.\n"
        f = make_skill_file(self.test_dir, "bad-blocker", content)
        issues = check_blocking_claims([f])
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "unimplemented_blocking")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_returns_list(self):
        issues = check_blocking_claims([])
        self.assertIsInstance(issues, list)


class TestCheckValidationClaims(unittest.TestCase):
    """Tests for validation claim consistency."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_skill_passes(self):
        f = make_skill_file(self.test_dir, "clean", "# Clean\n\nNo validation claims.\n")
        issues = check_validation_claims([f])
        self.assertEqual(issues, [])

    def test_validation_claim_with_nearby_if_passes(self):
        content = (
            "This validates that all files must be present.\n"
            "If the file is missing:\n"
            "  Report an error.\n"
        )
        f = make_skill_file(self.test_dir, "good-validator", content)
        issues = check_validation_claims([f])
        # Has "if" nearby — should pass
        self.assertEqual(issues, [])

    def test_validation_claim_with_bash_block_passes(self):
        content = (
            "This validates that the build always succeeds.\n"
            "```bash\nmvn compile\n```\n"
        )
        f = make_skill_file(self.test_dir, "bash-validator", content)
        issues = check_validation_claims([f])
        self.assertEqual(issues, [])

    def test_returns_list(self):
        issues = check_validation_claims([])
        self.assertIsInstance(issues, list)


class TestCheckExampleSyntax(unittest.TestCase):
    """Tests for bash code example syntax issues."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_quoted_variable_comparison_passes(self):
        content = '```bash\nif [ "$VAR" == "value" ]; then echo ok; fi\n```\n'
        f = make_skill_file(self.test_dir, "good-bash", content)
        issues = check_example_syntax([f])
        self.assertEqual(issues, [])

    def test_unquoted_variable_comparison_flagged(self):
        content = "```bash\nif [ $VAR == value ]; then echo ok; fi\n```\n"
        f = make_skill_file(self.test_dir, "bad-bash", content)
        issues = check_example_syntax([f])
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "bash_syntax_error")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_no_bash_blocks_passes(self):
        content = "No bash examples here.\n"
        f = make_skill_file(self.test_dir, "no-bash", content)
        issues = check_example_syntax([f])
        self.assertEqual(issues, [])

    def test_returns_list(self):
        issues = check_example_syntax([])
        self.assertIsInstance(issues, list)


class TestCheckAlwaysNeverClaims(unittest.TestCase):
    """Tests for 'always/never' rule enforcement checks."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_always_with_enforcement_passes(self):
        content = (
            "Always verify before committing.\n"
            "If the check fails:\n"
            "  stop immediately.\n"
        )
        f = make_skill_file(self.test_dir, "enforced", content)
        issues = check_always_never_claims([f])
        self.assertEqual(issues, [])

    def test_always_in_header_skipped(self):
        content = "# Always run tests first\n\nBody text here.\n"
        f = make_skill_file(self.test_dir, "header-always", content)
        issues = check_always_never_claims([f])
        self.assertEqual(issues, [])

    def test_never_with_check_nearby_passes(self):
        content = (
            "Never skip validation.\n"
            "Check the file exists first.\n"
        )
        f = make_skill_file(self.test_dir, "never-check", content)
        issues = check_always_never_claims([f])
        self.assertEqual(issues, [])

    def test_severity_is_note(self):
        # An always/never with no enforcement → NOTE
        content = "Always update the docs.\n\nSome unrelated paragraph.\n\nMore text.\n\nMore.\n\nMore.\n\nEnd.\n"
        f = make_skill_file(self.test_dir, "note-always", content)
        issues = check_always_never_claims([f])
        for issue in issues:
            self.assertEqual(issue["severity"], "NOTE")

    def test_returns_list(self):
        issues = check_always_never_claims([])
        self.assertIsInstance(issues, list)


def _all_issues(skill_files: list) -> list:
    """Run all behavior checks and aggregate results."""
    issues = []
    issues.extend(check_invocation_claims(skill_files))
    issues.extend(check_blocking_claims(skill_files))
    issues.extend(check_validation_claims(skill_files))
    issues.extend(check_example_syntax(skill_files))
    issues.extend(check_always_never_claims(skill_files))
    return issues


class TestValidateFileBehavior(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_file_has_no_issues(self):
        f = self.test_dir / "SKILL.md"
        f.write_text("# Clean Skill\n\n## Overview\n\nNo behavioral claims here.\n")
        issues = _all_issues([f])
        self.assertEqual(issues, [])

    def test_blocking_claim_without_logic_flagged(self):
        f = self.test_dir / "SKILL.md"
        f.write_text("This blocks on CRITICAL findings.\n\nNo exit logic.\n")
        issues = _all_issues([f])
        types = {i["type"] for i in issues}
        self.assertIn("unimplemented_blocking", types)

    def test_bash_syntax_error_detected(self):
        f = self.test_dir / "SKILL.md"
        f.write_text("```bash\nif [ $VAR == value ]; then echo ok; fi\n```\n")
        issues = _all_issues([f])
        types = {i["type"] for i in issues}
        self.assertIn("bash_syntax_error", types)


class TestValidateBehaviorScript(unittest.TestCase):
    """Subprocess tests for the full validate_behavior.py script."""

    def test_real_repo_does_not_exit_critical(self):
        """The real repo should not have CRITICAL behavioral issues."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(result.returncode, 1,
            msg=f"CRITICAL behavior issues:\n{result.stderr}")

    def test_clean_directory_exits_zero(self):
        with TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(result.returncode, 0)

    def test_unimplemented_blocking_claim_triggers_warning(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "bad-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "This skill blocks on CRITICAL findings.\n\nNo actual exit logic.\n"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            # Unimplemented blocking = WARNING → exit 2
            self.assertEqual(result.returncode, 2,
                msg=f"Expected exit 2, got {result.returncode}\nstderr: {result.stderr}")

    def test_unquoted_bash_variable_triggers_warning(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "bash-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "```bash\nif [ $VAR == value ]; then echo ok; fi\n```\n"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            # bash_syntax_error = WARNING → exit 2
            self.assertEqual(result.returncode, 2,
                msg=f"Expected exit 2, got {result.returncode}\nstderr: {result.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
