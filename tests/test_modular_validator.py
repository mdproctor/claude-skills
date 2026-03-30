#!/usr/bin/env python3
"""
Unit tests for modular_validator.py

Tests cross-module validation including link integrity,
completeness, duplication detection, and overall validation orchestration.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.document_discovery import DocumentGroup, ModuleFile
from scripts.modular_validator import (
    ValidationResult,
    validate_document_group,
    validate_link_integrity,
    check_completeness,
    find_duplication,
    check_anchor_exists,
    get_referenced_files,
)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class"""

    def test_validation_result_creation(self):
        """ValidationResult can be created and populated"""
        result = ValidationResult("Test Check")

        self.assertEqual(result.check_name, "Test Check")
        self.assertEqual(len(result.critical), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(len(result.notes), 0)

    def test_add_findings(self):
        """Can add findings of different severities"""
        result = ValidationResult("Test")

        result.add_critical("Critical issue")
        result.add_warning("Warning issue")
        result.add_note("Note issue")

        self.assertEqual(len(result.critical), 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(len(result.notes), 1)

    def test_has_issues(self):
        """has_issues() returns True if critical or warnings"""
        result = ValidationResult("Test")

        self.assertFalse(result.has_issues())

        result.add_note("Just a note")
        self.assertFalse(result.has_issues())

        result.add_warning("Warning")
        self.assertTrue(result.has_issues())


class TestLinkIntegrity(unittest.TestCase):
    """Test link integrity validation"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_link_integrity_all_valid(self):
        """All links exist → pass"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("# Design\n\n[Link](architecture.md)")
        module.write_text("# Architecture")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = validate_link_integrity(group)

        self.assertFalse(result.has_critical())
        self.assertFalse(result.has_warnings())

    def test_validate_link_integrity_broken_link(self):
        """Link to missing file → CRITICAL"""
        primary = self.test_dir / "DESIGN.md"

        primary.write_text("# Design\n\n[Missing](missing.md)")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        result = validate_link_integrity(group)

        self.assertTrue(result.has_critical())
        self.assertIn("missing.md", result.critical[0].lower())

    def test_validate_link_integrity_broken_anchor(self):
        """Link to valid file but invalid anchor → WARNING"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("# Design\n\n[Link](architecture.md#nonexistent)")
        module.write_text("# Architecture\n\n## Existing Section")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = validate_link_integrity(group)

        self.assertFalse(result.has_critical())
        self.assertTrue(result.has_warnings())
        self.assertIn("nonexistent", result.warnings[0].lower())

    def test_validate_link_integrity_internal_anchor(self):
        """Internal anchor (#section) should be validated"""
        primary = self.test_dir / "DESIGN.md"

        primary.write_text("# Design\n\n[Link](#overview)\n\n## Overview")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        result = validate_link_integrity(group)

        # Internal anchor exists, should pass
        self.assertFalse(result.has_warnings())

    def test_validate_link_integrity_missing_internal_anchor(self):
        """Internal anchor that doesn't exist → WARNING"""
        primary = self.test_dir / "DESIGN.md"

        primary.write_text("# Design\n\n[Link](#missing)")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        result = validate_link_integrity(group)

        self.assertTrue(result.has_warnings())
        self.assertIn("missing", result.warnings[0].lower())

    def test_check_anchor_exists(self):
        """check_anchor_exists() finds headers correctly"""
        file_path = self.test_dir / "test.md"

        file_path.write_text("""
# Main Title

## Architecture Overview

### Subsection
        """)

        # GitHub-style anchors
        self.assertTrue(check_anchor_exists(file_path, "architecture-overview"))
        self.assertTrue(check_anchor_exists(file_path, "subsection"))
        self.assertFalse(check_anchor_exists(file_path, "nonexistent"))

    def test_check_anchor_exists_special_chars(self):
        """Anchor generation strips special characters"""
        file_path = self.test_dir / "test.md"

        file_path.write_text("## API (v2.0)")

        # Special chars removed: "API (v2.0)" → "api-v20"
        self.assertTrue(check_anchor_exists(file_path, "api-v20"))

    def test_validate_link_integrity_external_urls_skipped(self):
        """External URLs are not validated"""
        primary = self.test_dir / "DESIGN.md"

        primary.write_text("[External](https://example.com)")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        result = validate_link_integrity(group)

        # Should not report issues for external links
        self.assertFalse(result.has_issues())


class TestCompleteness(unittest.TestCase):
    """Test completeness validation"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_check_completeness_single_file(self):
        """Single-file group has no completeness checks"""
        primary = self.test_dir / "DESIGN.md"
        primary.write_text("# Design")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        result = check_completeness(group)

        # No issues for single-file group
        self.assertFalse(result.has_issues())

    def test_check_completeness_orphaned_module(self):
        """Module not referenced from primary → WARNING"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "orphan.md"

        primary.write_text("# Design\n\nNo links")
        module.write_text("# Orphan")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = check_completeness(group)

        self.assertTrue(result.has_warnings())
        self.assertIn("orphan", result.warnings[0].lower())

    def test_check_completeness_directory_pattern_skipped(self):
        """Directory pattern modules don't need explicit reference"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "docs" / "design" / "architecture.md"
        module.parent.mkdir(parents=True)

        primary.write_text("# Design")
        module.write_text("# Architecture")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="directory-pattern")],
            discovered_via="auto",
            cache_key="",
        )

        result = check_completeness(group)

        # Directory pattern doesn't require explicit reference
        self.assertFalse(result.has_warnings())

    def test_check_completeness_bidirectional(self):
        """Module doesn't reference back → NOTE"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("[Link](architecture.md)")
        module.write_text("# Architecture\n\nNo back-reference")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = check_completeness(group)

        # Module should ideally reference primary or other modules
        self.assertEqual(len(result.notes), 1)
        self.assertIn("doesn't reference", result.notes[0].lower())

    def test_get_referenced_files(self):
        """get_referenced_files() extracts file links"""
        file_path = self.test_dir / "test.md"
        ref1 = self.test_dir / "ref1.md"
        ref2 = self.test_dir / "ref2.md"

        file_path.write_text("[Link1](ref1.md)\n[Link2](ref2.md)")
        ref1.write_text("# Ref1")
        ref2.write_text("# Ref2")

        referenced = get_referenced_files(file_path)

        self.assertEqual(len(referenced), 2)
        self.assertIn(ref1.resolve(), referenced)
        self.assertIn(ref2.resolve(), referenced)


class TestDuplication(unittest.TestCase):
    """Test duplication detection"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_duplication_single_file(self):
        """Single-file group has no duplication checks"""
        primary = self.test_dir / "DESIGN.md"
        primary.write_text("# Design")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        result = find_duplication(group)

        self.assertFalse(result.has_issues())

    def test_find_duplication_no_duplicates(self):
        """Unique content across modules → no issues"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("# Design\n\nUnique content in primary file")
        module.write_text("# Architecture\n\nCompletely different content in module")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = find_duplication(group)

        self.assertEqual(len(result.notes), 0)

    def test_find_duplication_duplicate_paragraphs(self):
        """Same paragraph in multiple modules → NOTE"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        # Substantial paragraph (>100 chars)
        duplicate_content = "This is a substantial paragraph that appears in both files. It has enough content to be detected as duplication by the validator. Lorem ipsum dolor sit amet."

        primary.write_text(f"# Design\n\n{duplicate_content}")
        module.write_text(f"# Architecture\n\n{duplicate_content}")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = find_duplication(group)

        self.assertEqual(len(result.notes), 1)
        self.assertIn("duplicate", result.notes[0].lower())

    def test_find_duplication_short_content_ignored(self):
        """Short paragraphs (<100 chars) are ignored"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        # Short content (< 100 chars)
        short_content = "Short paragraph."

        primary.write_text(f"# Design\n\n{short_content}")
        module.write_text(f"# Architecture\n\n{short_content}")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        result = find_duplication(group)

        # Short content should not trigger duplication detection
        self.assertEqual(len(result.notes), 0)


class TestDocumentGroupValidation(unittest.TestCase):
    """Test overall validate_document_group() orchestration"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_document_group_clean(self):
        """Clean group with valid links and content → no critical issues"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        # Create substantial content with bidirectional links
        primary.write_text("# Design\n\n[Architecture](architecture.md)\n\nDesign content here.")
        module.write_text("# Architecture\n\n## Overview\n\nContent here.\n\n[Back to design](DESIGN.md)")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        results = validate_document_group(group)

        # Main test: no CRITICAL issues (warnings and notes are acceptable)
        critical_results = [r for r in results if r.has_critical()]

        self.assertEqual(len(critical_results), 0)

    def test_validate_document_group_multiple_issues(self):
        """Group with multiple issues reported correctly"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        # Broken link + duplication
        duplicate = "This is substantial duplicate content that appears in both files and should be detected by the duplication checker algorithm."

        primary.write_text(f"# Design\n\n[Missing](missing.md)\n\n{duplicate}")
        module.write_text(f"# Architecture\n\n{duplicate}")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="",
        )

        results = validate_document_group(group)

        # Should have link integrity CRITICAL and duplication NOTE
        critical_results = [r for r in results if r.has_critical()]
        note_results = [r for r in results if len(r.notes) > 0]

        self.assertGreater(len(critical_results), 0)
        self.assertGreater(len(note_results), 0)

    def test_validate_document_group_filters_clean_results(self):
        """Results with no issues are filtered out"""
        primary = self.test_dir / "DESIGN.md"

        primary.write_text("# Design\n\nClean content")

        group = DocumentGroup(
            primary_file=primary,
            modules=[],
            discovered_via="auto",
            cache_key="",
        )

        results = validate_document_group(group)

        # All checks should run but return no issues
        # Results with no issues should be filtered
        for result in results:
            # At least one of these should be true
            has_something = (
                result.has_critical() or
                result.has_warnings() or
                len(result.notes) > 0
            )
            self.assertTrue(has_something)


if __name__ == "__main__":
    unittest.main()
