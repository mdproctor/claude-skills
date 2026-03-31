#!/usr/bin/env python3
"""
Unit tests for scripts/claude-skill

Tests the sync-local command and supporting functions.
Uses temporary directories throughout — never touches the real install location.
"""

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

# Load claude-skill (no .py extension) as a module
from importlib.machinery import SourceFileLoader
_script_path = Path(__file__).parent.parent / "scripts" / "claude-skill"
cs = SourceFileLoader("claude_skill", str(_script_path)).load_module()


def make_args(**kwargs) -> SimpleNamespace:
    """Build a minimal args namespace with safe defaults."""
    defaults = {"all": False, "link": False, "yes": True}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_skill(directory: Path, name: str) -> Path:
    """Create a minimal skill directory with a SKILL.md file."""
    skill_dir = directory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: >\n  Use when testing.\n---\n# {name}\n"
    )
    return skill_dir


class TestSyncLocalUpdatesInstalledSkills(unittest.TestCase):
    """sync-local copies updated local skills over existing installed copies."""

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.install_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.install_tmp.cleanup()

    def test_updated_file_is_synced(self):
        make_skill(self.repo, "git-commit")
        # Pre-install an outdated version
        installed = self.install / "git-commit"
        installed.mkdir()
        (installed / "SKILL.md").write_text("old content")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args())

        content = (self.install / "git-commit" / "SKILL.md").read_text()
        self.assertIn("git-commit", content)
        self.assertNotEqual(content, "old content")

    def test_multiple_installed_skills_all_updated(self):
        for name in ("git-commit", "java-dev", "adr"):
            make_skill(self.repo, name)
            installed = self.install / name
            installed.mkdir()
            (installed / "SKILL.md").write_text("old")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args())

        for name in ("git-commit", "java-dev", "adr"):
            content = (self.install / name / "SKILL.md").read_text()
            self.assertNotEqual(content, "old")


class TestSyncLocalSkipsUninstalled(unittest.TestCase):
    """Without --all, skills not in the install dir are left alone."""

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.install_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.install_tmp.cleanup()

    def test_uninstalled_skill_not_created(self):
        make_skill(self.repo, "java-dev")  # exists locally but not installed

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args())

        self.assertFalse((self.install / "java-dev").exists())

    def test_installed_skill_updated_uninstalled_skipped(self):
        make_skill(self.repo, "git-commit")
        make_skill(self.repo, "java-dev")
        installed = self.install / "git-commit"
        installed.mkdir()
        (installed / "SKILL.md").write_text("old")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args())

        # git-commit updated
        self.assertNotEqual((self.install / "git-commit" / "SKILL.md").read_text(), "old")
        # java-dev not installed
        self.assertFalse((self.install / "java-dev").exists())


class TestSyncLocalAllFlag(unittest.TestCase):
    """--all installs skills that are not yet in the install dir."""

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.install_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.install_tmp.cleanup()

    def test_uninstalled_skill_created_with_all_flag(self):
        make_skill(self.repo, "java-dev")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertTrue((self.install / "java-dev" / "SKILL.md").exists())

    def test_all_flag_installs_both_new_and_existing(self):
        make_skill(self.repo, "git-commit")
        make_skill(self.repo, "java-dev")
        # git-commit already installed
        (self.install / "git-commit").mkdir()
        (self.install / "git-commit" / "SKILL.md").write_text("old")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertNotEqual((self.install / "git-commit" / "SKILL.md").read_text(), "old")
        self.assertTrue((self.install / "java-dev" / "SKILL.md").exists())


class TestSyncLocalLinkFlag(unittest.TestCase):
    """--link creates symlinks instead of copies."""

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.install_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.install_tmp.cleanup()

    def test_link_creates_symlink_not_copy(self):
        make_skill(self.repo, "git-commit")
        (self.install / "git-commit").mkdir()
        (self.install / "git-commit" / "SKILL.md").write_text("old")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(link=True))

        self.assertTrue((self.install / "git-commit").is_symlink())

    def test_link_symlink_points_to_local_source(self):
        skill_dir = make_skill(self.repo, "git-commit")
        (self.install / "git-commit").mkdir()
        (self.install / "git-commit" / "SKILL.md").write_text("old")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(link=True))

        self.assertEqual(
            (self.install / "git-commit").resolve(),
            skill_dir.resolve()
        )

    def test_link_replaces_existing_copy_with_symlink(self):
        """Physical copy is replaced with symlink when --link used."""
        skill_dir = make_skill(self.repo, "git-commit")
        # Start with a physical copy
        copied = self.install / "git-commit"
        copied.mkdir()
        (copied / "SKILL.md").write_text("physical copy")
        self.assertFalse(copied.is_symlink())

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(link=True))

        self.assertTrue((self.install / "git-commit").is_symlink())

    def test_link_replaces_existing_symlink_with_new_symlink(self):
        """Existing symlink is replaced cleanly."""
        skill_dir = make_skill(self.repo, "git-commit")
        old_target = Path(self.install_tmp.name + "_old")
        old_target.mkdir()
        link = self.install / "git-commit"
        link.symlink_to(old_target)

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(link=True))

        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), skill_dir.resolve())
        old_target.rmdir()

    def test_link_edit_in_source_immediately_visible_in_install(self):
        """With symlinks, editing the source is reflected in the install instantly."""
        skill_dir = make_skill(self.repo, "git-commit")
        (self.install / "git-commit").mkdir()
        (self.install / "git-commit" / "SKILL.md").write_text("old")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(link=True))

        # Edit the source after linking
        (skill_dir / "SKILL.md").write_text("updated content")

        # Install location sees the change immediately (no re-sync needed)
        self.assertEqual(
            (self.install / "git-commit" / "SKILL.md").read_text(),
            "updated content"
        )


class TestSyncLocalEdgeCases(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.install_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.install_tmp.cleanup()

    def test_empty_repo_prints_message_and_returns(self):
        """Repo with no skill dirs (no SKILL.md) exits cleanly."""
        (self.repo / "docs").mkdir()  # non-skill dir
        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            # Should not raise
            cs.cmd_sync_local(make_args())

        # Nothing installed
        self.assertEqual(list(self.install.iterdir()), [])

    def test_no_installed_skills_without_all_flag(self):
        """Skills in repo but none installed and no --all: nothing happens."""
        make_skill(self.repo, "git-commit")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args())

        self.assertFalse((self.install / "git-commit").exists())

    def test_dirs_without_skill_md_are_ignored(self):
        """Non-skill dirs (docs, scripts, etc.) in repo root are not synced."""
        make_skill(self.repo, "git-commit")
        (self.install / "git-commit").mkdir()
        (self.install / "git-commit" / "SKILL.md").write_text("old")
        # Non-skill dirs
        (self.repo / "docs").mkdir()
        (self.repo / "scripts").mkdir()

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_sync_local(make_args(**{"all": True}))

        # docs and scripts not installed
        self.assertFalse((self.install / "docs").exists())
        self.assertFalse((self.install / "scripts").exists())

    def test_install_dir_created_if_missing(self):
        """INSTALL_DIR is created if it doesn't exist."""
        install = Path(self.install_tmp.name) / "nested" / "path"
        make_skill(self.repo, "git-commit")

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALL_DIR", install):
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertTrue(install.exists())


class TestCmdList(unittest.TestCase):
    """cmd_list shows installed skills correctly."""

    def setUp(self):
        self.install_tmp = TemporaryDirectory()
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.install_tmp.cleanup()

    def test_list_shows_installed_skills(self):
        for name in ("adr", "git-commit", "java-dev"):
            (self.install / name).mkdir()

        with patch.object(cs, "INSTALL_DIR", self.install):
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                cs.cmd_list(SimpleNamespace())
            output = buf.getvalue()

        self.assertIn("adr", output)
        self.assertIn("git-commit", output)
        self.assertIn("java-dev", output)

    def test_list_empty_install_dir(self):
        with patch.object(cs, "INSTALL_DIR", self.install):
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                cs.cmd_list(SimpleNamespace())
            output = buf.getvalue()

        self.assertIn("No skills installed", output)


class TestCmdUninstall(unittest.TestCase):
    """cmd_uninstall removes skills correctly."""

    def setUp(self):
        self.install_tmp = TemporaryDirectory()
        self.install = Path(self.install_tmp.name)

    def tearDown(self):
        self.install_tmp.cleanup()

    def test_uninstall_removes_skill_directory(self):
        skill = self.install / "git-commit"
        skill.mkdir()
        (skill / "SKILL.md").write_text("content")

        with patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_uninstall(SimpleNamespace(skill="git-commit"))

        self.assertFalse(skill.exists())

    def test_uninstall_nonexistent_skill_exits(self):
        with patch.object(cs, "INSTALL_DIR", self.install):
            with self.assertRaises(SystemExit) as ctx:
                cs.cmd_uninstall(SimpleNamespace(skill="nonexistent"))
        self.assertNotEqual(ctx.exception.code, 0)

    def test_uninstall_symlinked_skill(self):
        """Uninstalling a symlinked skill removes the symlink."""
        target = Path(self.install_tmp.name + "_target")
        target.mkdir()
        link = self.install / "git-commit"
        link.symlink_to(target)

        with patch.object(cs, "INSTALL_DIR", self.install):
            cs.cmd_uninstall(SimpleNamespace(skill="git-commit"))

        self.assertFalse(link.exists())
        target.rmdir()


class TestGetRepoRoot(unittest.TestCase):
    """get_repo_root returns parent of scripts/ directory."""

    def test_repo_root_is_parent_of_scripts(self):
        root = cs.get_repo_root()
        self.assertEqual(root, _script_path.parent.parent)
        self.assertTrue((root / "scripts").is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
