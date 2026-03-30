#!/usr/bin/env python3
"""
Unit tests for document_group_cache.py

Tests caching layer including cache hits, invalidation,
corruption recovery, and staleness detection.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import time
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.document_discovery import DocumentGroup, ModuleFile
from scripts.document_group_cache import (
    CACHE_FILE,
    CACHE_MAX_AGE_HOURS,
    get_cached_group,
    cache_group,
    invalidate_cache,
    compute_cache_key,
    is_cache_stale_entry,
)


class TestDocumentCache(unittest.TestCase):
    """Test document group caching"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

        # Change to test directory so cache file is created there
        import os
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory and restore working directory"""
        import os
        os.chdir(self.original_dir)
        self.temp_dir.cleanup()

    def test_cache_hit(self):
        """Cached group returned when cache key matches"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("[Link](architecture.md)")
        module.write_text("# Architecture")

        # Create group and cache it
        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key=compute_cache_key(primary),
        )

        cache_group(group)

        # Retrieve from cache
        cached = get_cached_group(primary)

        self.assertIsNotNone(cached)
        self.assertEqual(cached.primary_file, primary)
        self.assertEqual(len(cached.modules), 1)
        self.assertEqual(cached.modules[0].path, module)
        self.assertEqual(cached.discovered_via, "auto")

    def test_cache_miss_no_entry(self):
        """Returns None if no cache entry exists"""
        primary = self.test_dir / "DESIGN.md"
        primary.write_text("# Design")

        cached = get_cached_group(primary)

        self.assertIsNone(cached)

    def test_cache_miss_no_file(self):
        """Returns None if cache file doesn't exist"""
        primary = self.test_dir / "DESIGN.md"
        primary.write_text("# Design")

        # Don't create cache file
        cached = get_cached_group(primary)

        self.assertIsNone(cached)

    def test_cache_invalidation_on_structure_change(self):
        """Cache invalidated when structure changes (cache_key mismatch)"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("[Link](architecture.md)")
        module.write_text("# Architecture")

        # Cache with current structure
        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key=compute_cache_key(primary),
        )
        cache_group(group)

        # Change structure (add new link)
        primary.write_text("[Link](architecture.md)\n[New](components.md)")

        # Cache key should mismatch, return None
        cached = get_cached_group(primary)

        self.assertIsNone(cached)

    def test_cache_valid_after_content_change(self):
        """Cache still valid when only content changes (not structure)"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("# Design\n\n[Link](architecture.md)\n\nSome content")
        module.write_text("# Architecture")

        # Cache
        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key=compute_cache_key(primary),
        )
        cache_group(group)

        # Change content only (not structure)
        primary.write_text("# Design\n\n[Link](architecture.md)\n\nDifferent content")

        # Cache should still be valid (structure unchanged)
        cached = get_cached_group(primary)

        self.assertIsNotNone(cached)

    def test_cache_corruption_recovery(self):
        """Invalid JSON triggers cache deletion"""
        primary = self.test_dir / "DESIGN.md"
        primary.write_text("# Design")

        # Write corrupted cache file
        cache_path = self.test_dir / ".doc-cache.json"
        cache_path.write_text("{ invalid json")

        # Should delete cache and return None
        cached = get_cached_group(primary)

        self.assertIsNone(cached)
        self.assertFalse(cache_path.exists())

    def test_invalidate_cache_removes_entry(self):
        """invalidate_cache() removes specific entry"""
        primary1 = self.test_dir / "DESIGN.md"
        primary2 = self.test_dir / "README.md"

        primary1.write_text("# Design")
        primary2.write_text("# README")

        # Cache both
        group1 = DocumentGroup(
            primary_file=primary1,
            modules=[],
            discovered_via="auto",
            cache_key=compute_cache_key(primary1),
        )
        group2 = DocumentGroup(
            primary_file=primary2,
            modules=[],
            discovered_via="auto",
            cache_key=compute_cache_key(primary2),
        )

        cache_group(group1)
        cache_group(group2)

        # Invalidate only primary1
        invalidate_cache(primary1)

        # primary1 should be gone, primary2 should remain
        self.assertIsNone(get_cached_group(primary1))
        self.assertIsNotNone(get_cached_group(primary2))

    def test_cache_multiple_entries(self):
        """Cache can store multiple document groups"""
        primary1 = self.test_dir / "DESIGN.md"
        primary2 = self.test_dir / "README.md"
        module1 = self.test_dir / "architecture.md"
        module2 = self.test_dir / "usage.md"

        primary1.write_text("[Link](architecture.md)")
        primary2.write_text("[Link](usage.md)")
        module1.write_text("# Architecture")
        module2.write_text("# Usage")

        # Cache both groups
        group1 = DocumentGroup(
            primary_file=primary1,
            modules=[ModuleFile(path=module1, relationship="linked")],
            discovered_via="auto",
            cache_key=compute_cache_key(primary1),
        )
        group2 = DocumentGroup(
            primary_file=primary2,
            modules=[ModuleFile(path=module2, relationship="linked")],
            discovered_via="auto",
            cache_key=compute_cache_key(primary2),
        )

        cache_group(group1)
        cache_group(group2)

        # Both should be retrievable
        cached1 = get_cached_group(primary1)
        cached2 = get_cached_group(primary2)

        self.assertIsNotNone(cached1)
        self.assertIsNotNone(cached2)
        self.assertEqual(len(cached1.modules), 1)
        self.assertEqual(len(cached2.modules), 1)

    def test_cache_entry_staleness(self):
        """is_cache_stale_entry() detects old entries"""
        # Fresh entry
        fresh_entry = {
            "timestamp": datetime.now().isoformat()
        }
        self.assertFalse(is_cache_stale_entry(fresh_entry))

        # Old entry (> CACHE_MAX_AGE_HOURS)
        old_timestamp = datetime.now() - timedelta(hours=CACHE_MAX_AGE_HOURS + 1)
        stale_entry = {
            "timestamp": old_timestamp.isoformat()
        }
        self.assertTrue(is_cache_stale_entry(stale_entry))

    def test_cache_entry_missing_timestamp(self):
        """Entry without timestamp is considered stale"""
        entry = {}
        self.assertTrue(is_cache_stale_entry(entry))

    def test_cache_entry_malformed_timestamp(self):
        """Entry with invalid timestamp is considered stale"""
        entry = {"timestamp": "not-a-timestamp"}
        self.assertTrue(is_cache_stale_entry(entry))

    def test_cache_file_structure(self):
        """Cache file has correct JSON structure"""
        primary = self.test_dir / "DESIGN.md"
        module = self.test_dir / "architecture.md"

        primary.write_text("[Link](architecture.md)")
        module.write_text("# Architecture")

        group = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module, relationship="linked")],
            discovered_via="auto",
            cache_key="test-key-123",
        )

        cache_group(group)

        # Read cache file directly
        cache_path = self.test_dir / ".doc-cache.json"
        with open(cache_path) as f:
            cache_data = json.load(f)

        primary_str = str(primary.resolve())
        self.assertIn(primary_str, cache_data)

        entry = cache_data[primary_str]
        self.assertEqual(entry["primary"], str(primary))
        self.assertEqual(len(entry["modules"]), 1)
        self.assertEqual(entry["modules"][0]["path"], str(module))
        self.assertEqual(entry["modules"][0]["relationship"], "linked")
        self.assertEqual(entry["discovered_via"], "auto")
        self.assertEqual(entry["cache_key"], "test-key-123")
        self.assertIn("timestamp", entry)

    def test_cache_update_overwrites_entry(self):
        """Caching same primary file with same cache_key updates existing entry"""
        primary = self.test_dir / "DESIGN.md"
        module1 = self.test_dir / "architecture.md"
        module2 = self.test_dir / "components.md"

        primary.write_text("[Link](architecture.md)")
        module1.write_text("# Architecture")
        module2.write_text("# Components")

        # Compute actual cache key from file content
        actual_key = compute_cache_key(primary)

        # Cache with module1
        group1 = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module1, relationship="linked")],
            discovered_via="auto",
            cache_key=actual_key,
        )
        cache_group(group1)

        # Update cache with module2 (same cache_key - structure didn't change)
        group2 = DocumentGroup(
            primary_file=primary,
            modules=[ModuleFile(path=module2, relationship="linked")],
            discovered_via="auto",
            cache_key=actual_key,
        )
        cache_group(group2)

        # Should retrieve latest (module2) because cache_key matches
        cached = get_cached_group(primary)

        self.assertIsNotNone(cached)
        self.assertEqual(len(cached.modules), 1)
        self.assertEqual(cached.modules[0].path, module2)
        self.assertEqual(cached.cache_key, actual_key)


if __name__ == "__main__":
    unittest.main()
