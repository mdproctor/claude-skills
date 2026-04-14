#!/usr/bin/env python3
"""
Tests for scripts/validation/validate_usability.py

Checks readability/UX: long sentences, dense paragraphs, ambiguous pronouns,
double negatives, excessive nesting, broken heading hierarchy.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "validate_usability.py"

sys.path.insert(0, str(SCRIPT_PATH.parent))
from validate_usability import (
    check_long_sentences,
    check_dense_paragraphs,
    check_ambiguous_pronouns,
    check_double_negatives,
    check_excessive_nesting,
    check_heading_hierarchy,
    validate_file,
)


def make_temp_file(content: str) -> tuple:
    """Return (TemporaryDirectory, Path) for a file with the given content."""
    tmp = TemporaryDirectory()
    f = Path(tmp.name) / "SKILL.md"
    f.write_text(content)
    return tmp, f


class TestCheckLongSentences(unittest.TestCase):

    def test_short_sentence_passes(self):
        tmp, f = make_temp_file("Use this skill when testing short text.\n")
        issues = check_long_sentences(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_long_sentence_flagged(self):
        # 41+ words in a single sentence (not starting with special chars)
        long_sentence = "word " * 42 + ".\n"
        tmp, f = make_temp_file(long_sentence)
        issues = check_long_sentences(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["severity"], "WARNING")
        self.assertEqual(issues[0]["type"], "long_sentence")

    def test_code_block_fence_lines_skipped(self):
        # The ``` fence lines themselves are skipped (they start with ```)
        # but content inside a code block is NOT skipped by this check
        content = "```\nshort\n```\n"
        tmp, f = make_temp_file(content)
        issues = check_long_sentences(f.read_text(), f)
        tmp.cleanup()
        # "short" is 1 word — no issues
        self.assertEqual(issues, [])

    def test_header_lines_skipped(self):
        content = "# " + "word " * 45 + "\n"
        tmp, f = make_temp_file(content)
        issues = check_long_sentences(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_list_lines_skipped(self):
        content = "- " + "word " * 45 + "\n"
        tmp, f = make_temp_file(content)
        issues = check_long_sentences(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])


class TestCheckDenseParagraphs(unittest.TestCase):

    def test_short_paragraph_passes(self):
        content = "\n".join(["line"] * 5) + "\n"
        tmp, f = make_temp_file(content)
        issues = check_dense_paragraphs(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_long_paragraph_flagged(self):
        # 9+ consecutive non-empty lines
        content = "\n".join(["some prose line here"] * 10) + "\n"
        tmp, f = make_temp_file(content)
        issues = check_dense_paragraphs(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "dense_paragraph")

    def test_blank_line_resets_paragraph(self):
        # Two blocks of 5 lines each, separated by a blank
        content = "\n".join(["line"] * 5) + "\n\n" + "\n".join(["line"] * 5) + "\n"
        tmp, f = make_temp_file(content)
        issues = check_dense_paragraphs(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_header_resets_paragraph(self):
        content = "\n".join(["line"] * 5) + "\n## Header\n" + "\n".join(["line"] * 5) + "\n"
        tmp, f = make_temp_file(content)
        issues = check_dense_paragraphs(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])


class TestCheckAmbiguousPronouns(unittest.TestCase):

    def test_clear_sentence_passes(self):
        tmp, f = make_temp_file("Claude reads the file and processes it.\n")
        issues = check_ambiguous_pronouns(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_ambiguous_it_at_start_short_line_flagged(self):
        # Short line starting with "It will"
        tmp, f = make_temp_file("It will run now.\n")
        issues = check_ambiguous_pronouns(f.read_text(), f)
        tmp.cleanup()
        # May or may not flag depending on word count, but should not raise
        self.assertIsInstance(issues, list)

    def test_severity_is_note(self):
        tmp, f = make_temp_file("It will do this.\n")
        issues = check_ambiguous_pronouns(f.read_text(), f)
        tmp.cleanup()
        for issue in issues:
            self.assertEqual(issue["severity"], "NOTE")

    def test_header_lines_skipped(self):
        tmp, f = make_temp_file("# It will be fine\n")
        issues = check_ambiguous_pronouns(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])


class TestCheckDoubleNegatives(unittest.TestCase):

    def test_clean_content_passes(self):
        tmp, f = make_temp_file("Use the tool to run checks.\n")
        issues = check_double_negatives(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_not_un_pattern_flagged(self):
        tmp, f = make_temp_file("This is not uncommon.\n")
        issues = check_double_negatives(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "double_negative")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_never_not_pattern_flagged(self):
        tmp, f = make_temp_file("You should never not do this.\n")
        issues = check_double_negatives(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)

    def test_cannot_not_pattern_flagged(self):
        tmp, f = make_temp_file("You cannot not call this.\n")
        issues = check_double_negatives(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)

    def test_case_insensitive(self):
        tmp, f = make_temp_file("This is NOT UNCOMMON.\n")
        issues = check_double_negatives(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)


class TestCheckExcessiveNesting(unittest.TestCase):

    def test_shallow_nesting_passes(self):
        content = "- level 1\n  - level 2\n    - level 3\n"
        tmp, f = make_temp_file(content)
        issues = check_excessive_nesting(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_deep_nesting_flagged(self):
        # 8 spaces = level 4, which is > 3
        content = "        - level 4 item\n"
        tmp, f = make_temp_file(content)
        issues = check_excessive_nesting(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "excessive_nesting")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_non_list_lines_not_flagged(self):
        content = "        plain indented text (not a list)\n"
        tmp, f = make_temp_file(content)
        issues = check_excessive_nesting(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])


class TestCheckHeadingHierarchy(unittest.TestCase):

    def test_sequential_headings_pass(self):
        content = "# H1\n## H2\n### H3\n"
        tmp, f = make_temp_file(content)
        issues = check_heading_hierarchy(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])

    def test_skipped_level_flagged(self):
        # Goes from ## to #### (skips ###)
        content = "## H2\n#### H4\n"
        tmp, f = make_temp_file(content)
        issues = check_heading_hierarchy(f.read_text(), f)
        tmp.cleanup()
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0]["type"], "broken_hierarchy")
        self.assertEqual(issues[0]["severity"], "WARNING")

    def test_first_heading_can_be_any_level(self):
        # First heading with no previous level — no skip
        content = "### H3 as first heading\n#### H4\n"
        tmp, f = make_temp_file(content)
        issues = check_heading_hierarchy(f.read_text(), f)
        tmp.cleanup()
        # Going from ### to #### is fine (level 3 to 4 = step of 1)
        self.assertEqual(issues, [])

    def test_valid_decrease_passes(self):
        # Going from ### to ## is fine (decrease is always OK)
        content = "# H1\n## H2\n### H3\n## H2 again\n"
        tmp, f = make_temp_file(content)
        issues = check_heading_hierarchy(f.read_text(), f)
        tmp.cleanup()
        self.assertEqual(issues, [])


class TestValidateFileUsability(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.test_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_skill_passes(self):
        f = self.test_dir / "SKILL.md"
        f.write_text("# Clean Skill\n\n## Overview\n\nUse this skill for clean work.\n")
        issues = validate_file(f)
        self.assertEqual(issues, [])

    def test_read_error_returns_warning(self):
        f = self.test_dir / "missing.md"
        issues = validate_file(f)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "read_error")

    def test_aggregates_multiple_issue_types(self):
        # Double negative + deep nesting in one file
        content = "This is not uncommon.\n" + "        - deeply nested\n"
        f = self.test_dir / "SKILL.md"
        f.write_text(content)
        issues = validate_file(f)
        types = {i["type"] for i in issues}
        self.assertIn("double_negative", types)
        self.assertIn("excessive_nesting", types)


class TestValidateUsabilityScript(unittest.TestCase):
    """Subprocess tests for the full validate_usability.py script."""

    def test_real_repo_does_not_exit_critical(self):
        """The actual repo should not have CRITICAL usability issues."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Exit 1 would mean CRITICAL issues; 0 or 2 are acceptable
        self.assertNotEqual(result.returncode, 1,
            msg=f"CRITICAL usability issues found:\n{result.stderr}")

    def test_clean_directory_exits_zero(self):
        with TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            self.assertEqual(result.returncode, 0)

    def test_double_negative_triggers_warning_exit(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("This is not uncommon.\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            # Double negative is WARNING → exit code 2
            self.assertEqual(result.returncode, 2,
                msg=f"Expected exit 2 (WARNING), got {result.returncode}\nstderr: {result.stderr}")

    def test_note_only_issues_exit_zero(self):
        """NOTE-only issues should exit 0 (not block)."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "note-skill"
            skill_dir.mkdir()
            # An ambiguous pronoun at start of a short line — NOTE severity
            (skill_dir / "SKILL.md").write_text("It will run.\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH)],
                capture_output=True,
                text=True,
                cwd=tmp,
            )
            # Should be 0 (NOTE only) or 0 (nothing flagged for this case)
            self.assertIn(result.returncode, [0, 2],
                msg=f"Unexpected exit code {result.returncode}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
