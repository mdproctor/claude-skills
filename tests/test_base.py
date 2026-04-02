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


class DualTempDirTestCase(unittest.TestCase):
    """Base class for tests that need two temporary directories.

    Provides self.repo and self.skills (Path) pointing to fresh temp
    directories. Automatically cleaned up after each test. Used for tests
    that simulate a repo + installed skills directory pair.
    """

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.skills_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.skills = Path(self.skills_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.skills_tmp.cleanup()
