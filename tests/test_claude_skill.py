#!/usr/bin/env python3
"""
Unit tests for scripts/claude-skill

Tests sync-local, install, uninstall, list, and hook management.
Uses temporary directories — never touches the real ~/.claude/skills/.
"""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_base import DualTempDirTestCase
from importlib.machinery import SourceFileLoader
_script_path = Path(__file__).parent.parent / "scripts" / "claude-skill"
cs = SourceFileLoader("claude_skill", str(_script_path)).load_module()


def make_args(**kwargs) -> SimpleNamespace:
    defaults = {"all": False, "yes": True}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_skill(directory: Path, name: str) -> Path:
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = directory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: >\n  Use when testing.\n---\n# {name}\n"
    )
    return skill_dir


# ---------------------------------------------------------------------------
# sync-local: updates installed skills
# ---------------------------------------------------------------------------

class TestSyncLocalUpdatesInstalled(DualTempDirTestCase):

    def _patch(self):
        return patch.multiple(cs, get_repo_root=lambda: self.repo,
                              SKILLS_DIR=self.skills,
                              sync_hook=lambda: 'up-to-date')

    def test_updated_file_is_synced(self):
        make_skill(self.repo, "git-commit")
        installed = self.skills / "git-commit"
        installed.mkdir()
        (installed / "SKILL.md").write_text("old")

        with self._patch():
            cs.cmd_sync_local(make_args())

        self.assertNotEqual((self.skills / "git-commit" / "SKILL.md").read_text(), "old")

    def test_multiple_skills_all_updated(self):
        for name in ("git-commit", "java-dev", "adr"):
            make_skill(self.repo, name)
            (self.skills / name).mkdir()
            (self.skills / name / "SKILL.md").write_text("old")

        with self._patch():
            cs.cmd_sync_local(make_args())

        for name in ("git-commit", "java-dev", "adr"):
            self.assertNotEqual((self.skills / name / "SKILL.md").read_text(), "old")


# ---------------------------------------------------------------------------
# sync-local: skips uninstalled without --all
# ---------------------------------------------------------------------------

class TestSyncLocalSkipsUninstalled(DualTempDirTestCase):

    def _patch(self):
        return patch.multiple(cs, get_repo_root=lambda: self.repo,
                              SKILLS_DIR=self.skills,
                              sync_hook=lambda: 'up-to-date')

    def test_uninstalled_skill_not_created(self):
        make_skill(self.repo, "java-dev")

        with self._patch():
            cs.cmd_sync_local(make_args())

        self.assertFalse((self.skills / "java-dev").exists())

    def test_installed_updated_uninstalled_skipped(self):
        make_skill(self.repo, "git-commit")
        make_skill(self.repo, "java-dev")
        (self.skills / "git-commit").mkdir()
        (self.skills / "git-commit" / "SKILL.md").write_text("old")

        with self._patch():
            cs.cmd_sync_local(make_args())

        self.assertNotEqual((self.skills / "git-commit" / "SKILL.md").read_text(), "old")
        self.assertFalse((self.skills / "java-dev").exists())


# ---------------------------------------------------------------------------
# sync-local: --all installs new skills
# ---------------------------------------------------------------------------

class TestSyncLocalAllFlag(DualTempDirTestCase):

    def _patch(self):
        return patch.multiple(cs, get_repo_root=lambda: self.repo,
                              SKILLS_DIR=self.skills,
                              sync_hook=lambda: 'up-to-date')

    def test_new_skill_installed_with_all(self):
        make_skill(self.repo, "java-dev")

        with self._patch():
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertTrue((self.skills / "java-dev" / "SKILL.md").exists())

    def test_all_updates_existing_and_installs_new(self):
        make_skill(self.repo, "git-commit")
        make_skill(self.repo, "java-dev")
        (self.skills / "git-commit").mkdir()
        (self.skills / "git-commit" / "SKILL.md").write_text("old")

        with self._patch():
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertNotEqual((self.skills / "git-commit" / "SKILL.md").read_text(), "old")
        self.assertTrue((self.skills / "java-dev" / "SKILL.md").exists())


# ---------------------------------------------------------------------------
# sync-local: edge cases
# ---------------------------------------------------------------------------

class TestSyncLocalEdgeCases(DualTempDirTestCase):

    def _patch(self):
        return patch.multiple(cs, get_repo_root=lambda: self.repo,
                              SKILLS_DIR=self.skills,
                              sync_hook=lambda: 'up-to-date')

    def test_empty_repo_exits_cleanly(self):
        (self.repo / "docs").mkdir()
        with self._patch():
            cs.cmd_sync_local(make_args())

    def test_non_skill_dirs_ignored(self):
        make_skill(self.repo, "git-commit")
        (self.skills / "git-commit").mkdir()
        (self.skills / "git-commit" / "SKILL.md").write_text("old")
        (self.repo / "docs").mkdir()
        (self.repo / "scripts").mkdir()

        with self._patch():
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertFalse((self.skills / "docs").exists())
        self.assertFalse((self.skills / "scripts").exists())

    def test_skills_dir_created_if_missing(self):
        nested = Path(self.skills_tmp.name) / "nested" / "path"
        make_skill(self.repo, "git-commit")

        with patch.multiple(cs, get_repo_root=lambda: self.repo,
                            SKILLS_DIR=nested,
                            sync_hook=lambda: 'up-to-date'):
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertTrue(nested.exists())


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.skills = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lists_installed_skills(self):
        for name in ("adr", "git-commit", "java-dev"):
            d = self.skills / name
            d.mkdir()
            (d / "SKILL.md").write_text("---\nname: x\n---\n")

        buf = io.StringIO()
        with patch.object(cs, "SKILLS_DIR", self.skills), redirect_stdout(buf):
            cs.cmd_list(SimpleNamespace())

        out = buf.getvalue()
        self.assertIn("adr", out)
        self.assertIn("git-commit", out)
        self.assertIn("java-dev", out)

    def test_dirs_without_skill_md_not_listed(self):
        (self.skills / "random-dir").mkdir()

        buf = io.StringIO()
        with patch.object(cs, "SKILLS_DIR", self.skills), redirect_stdout(buf):
            cs.cmd_list(SimpleNamespace())

        self.assertIn("No skills installed", buf.getvalue())

    def test_no_skills_installed(self):
        buf = io.StringIO()
        with patch.object(cs, "SKILLS_DIR", self.skills), redirect_stdout(buf):
            cs.cmd_list(SimpleNamespace())

        self.assertIn("No skills installed", buf.getvalue())


# ---------------------------------------------------------------------------
# cmd_uninstall
# ---------------------------------------------------------------------------

class TestCmdUninstall(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.skills = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_removes_skill_directory(self):
        skill = self.skills / "git-commit"
        skill.mkdir()
        (skill / "SKILL.md").write_text("content")

        with patch.object(cs, "SKILLS_DIR", self.skills):
            cs.cmd_uninstall(SimpleNamespace(skill="git-commit"))

        self.assertFalse(skill.exists())

    def test_nonexistent_skill_exits(self):
        with patch.object(cs, "SKILLS_DIR", self.skills):
            with self.assertRaises(SystemExit) as ctx:
                cs.cmd_uninstall(SimpleNamespace(skill="nonexistent"))
        self.assertNotEqual(ctx.exception.code, 0)

    def test_removes_symlinked_skill(self):
        target = Path(self.tmp.name + "_target")
        target.mkdir()
        link = self.skills / "git-commit"
        link.symlink_to(target)

        with patch.object(cs, "SKILLS_DIR", self.skills):
            cs.cmd_uninstall(SimpleNamespace(skill="git-commit"))

        self.assertFalse(link.exists())
        target.rmdir()


# ---------------------------------------------------------------------------
# Hook management
# ---------------------------------------------------------------------------

class TestIsHookRegistered(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_false_when_missing(self):
        self.assertFalse(cs.is_hook_registered(self.settings))

    def test_false_when_absent(self):
        self.settings.write_text(json.dumps({"hooks": {"SessionStart": []}}))
        self.assertFalse(cs.is_hook_registered(self.settings))

    def test_true_when_registered(self):
        self.settings.write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": cs.HOOK_COMMAND}
        ]}]}}))
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_false_for_different_command(self):
        self.settings.write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "/other/hook.sh"}
        ]}]}}))
        self.assertFalse(cs.is_hook_registered(self.settings))

    def test_handles_malformed_json(self):
        self.settings.write_text("not json")
        self.assertFalse(cs.is_hook_registered(self.settings))


class TestRegisterHook(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_and_registers(self):
        cs.register_hook(self.settings)
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_preserves_existing_settings(self):
        self.settings.write_text(json.dumps({"model": "claude-opus"}))
        cs.register_hook(self.settings)
        settings = json.loads(self.settings.read_text())
        self.assertEqual(settings["model"], "claude-opus")
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_adds_alongside_existing_hook(self):
        existing = {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "/other/hook.sh"}
        ]}]}}
        self.settings.write_text(json.dumps(existing))
        cs.register_hook(self.settings)
        commands = [h["command"] for h in
                    json.loads(self.settings.read_text())["hooks"]["SessionStart"][0]["hooks"]]
        self.assertIn("/other/hook.sh", commands)
        self.assertIn(cs.HOOK_COMMAND, commands)


class TestSyncHook(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source = root / "hooks" / "check_project_setup.sh"
        self.dest = root / "dest" / "check_project_setup.sh"
        self.settings = root / "settings.json"
        self.source.parent.mkdir()
        self.source.write_text("#!/bin/bash\necho 'hook v1'\n")

    def tearDown(self):
        self.tmp.cleanup()

    def _sync(self):
        return cs.sync_hook(self.source, self.dest, self.settings)

    def test_installs_when_missing(self):
        self.assertEqual(self._sync(), 'installed')
        self.assertEqual(self.dest.read_text(), self.source.read_text())

    def test_installed_hook_is_executable(self):
        self._sync()
        self.assertTrue(self.dest.stat().st_mode & 0o111)

    def test_installs_and_registers(self):
        self._sync()
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_updates_when_content_differs(self):
        self.dest.parent.mkdir()
        self.dest.write_text("old version")
        self.assertEqual(self._sync(), 'updated')

    def test_up_to_date_when_unchanged(self):
        self.dest.parent.mkdir()
        self.dest.write_text(self.source.read_text())
        cs.register_hook(self.settings)
        self.assertEqual(self._sync(), 'up-to-date')

    def test_registered_when_file_ok_but_not_in_settings(self):
        self.dest.parent.mkdir()
        self.dest.write_text(self.source.read_text())
        self.assertEqual(self._sync(), 'registered')

    def test_no_source_when_file_missing(self):
        self.source.unlink()
        self.assertEqual(self._sync(), 'no-source')


# ---------------------------------------------------------------------------
# get_repo_root
# ---------------------------------------------------------------------------

class TestGetRepoRoot(unittest.TestCase):

    def test_is_parent_of_scripts(self):
        root = cs.get_repo_root()
        self.assertEqual(root, _script_path.parent.parent)
        self.assertTrue((root / "scripts").is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
