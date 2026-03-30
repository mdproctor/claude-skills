#!/usr/bin/env python3
"""
Unit tests for generate_skill_metadata.py - Skill Scanner

Tests skill directory scanning (Task 1 of marketplace implementation).
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSkillScanner(unittest.TestCase):
    """Test skill directory scanning"""

    def test_scan_finds_skill_directories(self):
        """Scanner should find directories containing SKILL.md files"""
        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test skill directories
            (tmpdir / "java-dev").mkdir()
            (tmpdir / "java-dev" / "SKILL.md").write_text("---\nname: java-dev\n---\n")

            (tmpdir / "quarkus-flow-dev").mkdir()
            (tmpdir / "quarkus-flow-dev" / "SKILL.md").write_text("---\nname: quarkus-flow-dev\n---\n")

            # Create non-skill directory (should be excluded)
            (tmpdir / "scripts").mkdir()
            (tmpdir / "scripts" / "test.py").write_text("# not a skill")

            from scripts.generate_skill_metadata import scan_for_skills

            skills = scan_for_skills(tmpdir)

            self.assertEqual(len(skills), 2)
            self.assertIn(tmpdir / "java-dev", skills)
            self.assertIn(tmpdir / "quarkus-flow-dev", skills)
            self.assertNotIn(tmpdir / "scripts", skills)


class TestFrontmatterParser(unittest.TestCase):
    """Test SKILL.md frontmatter parsing"""

    def test_parse_frontmatter_extracts_name(self):
        """Parser should extract name from SKILL.md frontmatter"""
        skill_md = """---
name: java-dev
description: >
  Use when writing Java code
---

# Java Development

Content here...
"""
        from scripts.generate_skill_metadata import parse_frontmatter

        name = parse_frontmatter(skill_md)

        self.assertEqual(name, "java-dev")

    def test_parse_frontmatter_raises_on_missing_name(self):
        """Parser should raise error if name field missing"""
        skill_md = """---
description: No name field
---
"""
        from scripts.generate_skill_metadata import parse_frontmatter

        with self.assertRaisesRegex(ValueError, "Missing 'name' field"):
            parse_frontmatter(skill_md)


class TestDependencyParser(unittest.TestCase):
    """Test SKILL.md dependency parsing"""

    def test_parse_dependencies_finds_single_dependency(self):
        """Parser should extract dependencies from Prerequisites section"""
        skill_md = """---
name: quarkus-flow-dev
---

## Prerequisites

**This skill builds on [`java-dev`]**.

Apply all rules from java-dev.
"""
        from scripts.generate_skill_metadata import parse_dependencies

        deps = parse_dependencies(skill_md)

        self.assertEqual(deps, ["java-dev"])

    def test_parse_dependencies_finds_multiple_dependencies(self):
        """Parser should extract multiple dependencies"""
        skill_md = """---
name: quarkus-flow-testing
---

## Prerequisites

**This skill builds on [`java-dev`] and [`quarkus-flow-dev`]**.
"""
        from scripts.generate_skill_metadata import parse_dependencies

        deps = parse_dependencies(skill_md)

        self.assertEqual(set(deps), {"java-dev", "quarkus-flow-dev"})

    def test_parse_dependencies_returns_empty_for_no_prereqs(self):
        """Parser should return empty list if no Prerequisites section"""
        skill_md = """---
name: java-dev
---

# Java Development

No prerequisites.
"""
        from scripts.generate_skill_metadata import parse_dependencies

        deps = parse_dependencies(skill_md)

        self.assertEqual(deps, [])


if __name__ == '__main__':
    unittest.main()
