"""
Shared base classes for tests requiring temporary directories.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class TempDirTestCase(unittest.TestCase):
    """Base class for tests that need a temporary working directory.

    Provides self.test_dir (Path) pointing to a fresh temp directory.
    Automatically cleaned up after each test.
    """

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()
