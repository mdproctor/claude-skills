#!/usr/bin/env python3
"""
Tests for scripts/generate_web_app_data.py

This script modifies real files (docs/index.html, tests/test_mockup_chaining.py).
All tests use --dry-run to avoid actual file mutations, except the idempotency
test which runs twice and verifies the output is unchanged.
"""

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_web_app_data.py"
HTML_PATH = REPO_ROOT / "docs" / "index.html"


class TestGenerateWebAppDataDryRun(unittest.TestCase):
    """Tests using --dry-run so no files are modified."""

    def _run(self, *extra_args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--dry-run"] + list(extra_args),
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

    def test_exits_zero_on_real_repo(self):
        result = self._run()
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

    def test_reports_skill_count(self):
        result = self._run()
        self.assertEqual(result.returncode, 0)
        # Should print something like "Processed N skills"
        self.assertIn("Processed", result.stdout)
        self.assertIn("skills", result.stdout)

    def test_skill_count_matches_expected_scale(self):
        """Repo has 40+ skills; a tiny count indicates a parsing failure."""
        result = self._run()
        self.assertEqual(result.returncode, 0)
        # Extract the count from "Processed N skills"
        for line in result.stdout.splitlines():
            if "Processed" in line and "skills" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Processed" and i + 1 < len(parts):
                        try:
                            count = int(parts[i + 1])
                            self.assertGreater(count, 30,
                                msg=f"Expected 30+ skills, got {count}. Parsing may have failed.")
                        except ValueError:
                            pass
                break

    def test_dry_run_does_not_modify_html(self):
        original_html = HTML_PATH.read_text(encoding="utf-8")
        self._run()
        self.assertEqual(HTML_PATH.read_text(encoding="utf-8"), original_html)

    def test_dry_run_complete_message(self):
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run complete", result.stdout)


class TestGenerateWebAppDataChainContent(unittest.TestCase):
    """Verify the CHAIN constant in index.html has the expected structure."""

    def test_chain_js_contains_expected_skills(self):
        """Known skills should appear in the CHAIN const after generation."""
        html = HTML_PATH.read_text(encoding="utf-8")
        # The CHAIN const must exist
        self.assertIn("const CHAIN = {", html)
        # A sample of well-known skills should be present
        for skill in ("git-commit", "adr", "java-dev", "update-claude-md"):
            self.assertIn(f"'{skill}'", html,
                msg=f"Expected skill '{skill}' to appear in CHAIN JS")

    def test_chain_js_has_parents_children_structure(self):
        """Each CHAIN entry should have parents and children keys."""
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn("parents:", html)
        self.assertIn("children:", html)

    def test_chain_js_block_is_closed(self):
        """The CHAIN const block must be properly closed."""
        html = HTML_PATH.read_text(encoding="utf-8")
        # Find the CHAIN block and verify it closes
        start = html.find("const CHAIN = {")
        self.assertGreater(start, -1, "CHAIN const not found")
        # Find the closing }; after the opening
        end = html.find("};", start)
        self.assertGreater(end, start, "CHAIN block not properly closed")


class TestGenerateWebAppDataIdempotency(unittest.TestCase):
    """Verify running the script twice produces identical output."""

    def test_idempotent_dry_run(self):
        """Two dry-run invocations produce identical stdout."""
        def run_dry():
            return subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--dry-run"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )

        r1 = run_dry()
        r2 = run_dry()
        self.assertEqual(r1.returncode, 0)
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(r1.stdout, r2.stdout,
            "Two dry-run invocations produced different output — not idempotent")

    def test_actual_run_exits_zero_twice(self):
        """Running the script twice both exit cleanly — no crash on second run."""
        r1 = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(r1.returncode, 0, msg=f"First run failed: {r1.stderr}")

        r2 = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(r2.returncode, 0, msg=f"Second run failed: {r2.stderr}")

    def test_chain_js_present_after_second_run(self):
        """The CHAIN const block remains valid after a second run."""
        import re

        def has_valid_chain(html: str) -> bool:
            m = re.search(r'const CHAIN = \{[\s\S]*?\};', html)
            if not m:
                return False
            block = m.group(0)
            return "parents:" in block and "children:" in block

        # First run
        subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertTrue(has_valid_chain(HTML_PATH.read_text(encoding="utf-8")),
            "CHAIN block missing or malformed after first run")

        # Second run
        subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertTrue(has_valid_chain(HTML_PATH.read_text(encoding="utf-8")),
            "CHAIN block missing or malformed after second run")


if __name__ == "__main__":
    unittest.main(verbosity=2)
