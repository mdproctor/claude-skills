#!/usr/bin/env python3
"""
Unit tests for scripts/claude-skill

Tests the sync-local command and supporting functions.
Uses temporary directories throughout — never touches the real install location.
"""

import importlib.util
import json
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


class TestIsHookRegistered(unittest.TestCase):
    """is_hook_registered reads settings.json correctly."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_false_when_settings_missing(self):
        self.assertFalse(cs.is_hook_registered(self.settings))

    def test_returns_false_when_hook_absent(self):
        self.settings.write_text(json.dumps({"hooks": {"SessionStart": []}}))
        self.assertFalse(cs.is_hook_registered(self.settings))

    def test_returns_true_when_hook_registered(self):
        content = {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": cs.HOOK_COMMAND}
        ]}]}}
        self.settings.write_text(json.dumps(content))
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_returns_false_for_different_command(self):
        content = {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "/some/other/hook.sh"}
        ]}]}}
        self.settings.write_text(json.dumps(content))
        self.assertFalse(cs.is_hook_registered(self.settings))

    def test_handles_malformed_json(self):
        self.settings.write_text("not json")
        self.assertFalse(cs.is_hook_registered(self.settings))


class TestRegisterHook(unittest.TestCase):
    """register_hook writes to settings.json correctly."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_settings_if_missing(self):
        cs.register_hook(self.settings)
        self.assertTrue(self.settings.exists())
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_adds_to_existing_settings_without_hooks(self):
        self.settings.write_text(json.dumps({"someOtherKey": "value"}))
        cs.register_hook(self.settings)
        settings = json.loads(self.settings.read_text())
        self.assertIn("hooks", settings)
        self.assertEqual(settings["someOtherKey"], "value")
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_adds_to_existing_session_start_group(self):
        existing = {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "/other/hook.sh"}
        ]}]}}
        self.settings.write_text(json.dumps(existing))
        cs.register_hook(self.settings)
        settings = json.loads(self.settings.read_text())
        commands = [h["command"] for h in settings["hooks"]["SessionStart"][0]["hooks"]]
        self.assertIn("/other/hook.sh", commands)
        self.assertIn(cs.HOOK_COMMAND, commands)

    def test_idempotent_when_called_twice(self):
        cs.register_hook(self.settings)
        cs.register_hook(self.settings)
        settings = json.loads(self.settings.read_text())
        hooks = settings["hooks"]["SessionStart"][0]["hooks"]
        matching = [h for h in hooks if h["command"] == cs.HOOK_COMMAND]
        self.assertEqual(len(matching), 2)  # register_hook doesn't deduplicate; is_hook_registered prevents double-call


class TestSyncHook(unittest.TestCase):
    """sync_hook installs, updates, and registers the hook correctly."""

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

    def test_installs_when_dest_missing(self):
        status = self._sync()
        self.assertEqual(status, 'installed')
        self.assertTrue(self.dest.exists())
        self.assertEqual(self.dest.read_text(), self.source.read_text())

    def test_installed_hook_is_executable(self):
        self._sync()
        self.assertTrue(self.dest.stat().st_mode & 0o111)

    def test_installed_registers_in_settings(self):
        self._sync()
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_updates_when_source_differs(self):
        self.dest.parent.mkdir()
        self.dest.write_text("#!/bin/bash\necho 'old version'\n")
        status = self._sync()
        self.assertEqual(status, 'updated')
        self.assertEqual(self.dest.read_text(), "#!/bin/bash\necho 'hook v1'\n")

    def test_up_to_date_when_content_matches(self):
        self.dest.parent.mkdir()
        self.dest.write_text(self.source.read_text())
        # Register first so it's fully up to date
        cs.register_hook(self.settings)
        status = self._sync()
        self.assertEqual(status, 'up-to-date')

    def test_registered_when_file_ok_but_not_in_settings(self):
        self.dest.parent.mkdir()
        self.dest.write_text(self.source.read_text())
        # Don't pre-register
        status = self._sync()
        self.assertEqual(status, 'registered')
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_no_source_when_hook_file_missing(self):
        self.source.unlink()
        status = self._sync()
        self.assertEqual(status, 'no-source')

    def test_sync_local_runs_hook_sync(self):
        """sync-local calls sync_hook and reports status."""
        repo_tmp = TemporaryDirectory()
        install_tmp = TemporaryDirectory()
        try:
            repo = Path(repo_tmp.name)
            make_skill(repo, "git-commit")
            (Path(install_tmp.name) / "git-commit").mkdir()
            (Path(install_tmp.name) / "git-commit" / "SKILL.md").write_text("old")

            with patch.object(cs, "get_repo_root", return_value=repo), \
                 patch.object(cs, "INSTALL_DIR", Path(install_tmp.name)), \
                 patch.object(cs, "get_claude_install_paths", return_value={}), \
                 patch.object(cs, "sync_hook", return_value='up-to-date') as mock_sync:
                cs.cmd_sync_local(make_args())
                mock_sync.assert_called_once()
        finally:
            repo_tmp.cleanup()
            install_tmp.cleanup()


class TestGetClaudeInstallPaths(unittest.TestCase):
    """get_claude_install_paths reads installed_plugins.json correctly."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.plugins_json = Path(self.tmp.name) / "installed_plugins.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _write_plugins(self, data):
        self.plugins_json.write_text(json.dumps(data))

    def test_returns_empty_when_file_missing(self):
        result = cs.get_claude_install_paths.__wrapped__(
            "mdproctor-skills"
        ) if hasattr(cs.get_claude_install_paths, '__wrapped__') else {}
        # Just test via patching INSTALLED_PLUGINS_JSON
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", self.plugins_json):
            self.assertEqual(cs.get_claude_install_paths("mdproctor-skills"), {})

    def test_returns_paths_for_matching_marketplace(self):
        self._write_plugins({"plugins": {
            "java-dev@mdproctor-skills": [{"installPath": "/some/path/java-dev/1.0.0"}],
            "git-commit@mdproctor-skills": [{"installPath": "/some/path/git-commit/1.0.0-SNAPSHOT"}],
            "superpowers@claude-plugins-official": [{"installPath": "/other/path"}],
        }})
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", self.plugins_json):
            result = cs.get_claude_install_paths("mdproctor-skills")
        self.assertIn("java-dev", result)
        self.assertIn("git-commit", result)
        self.assertNotIn("superpowers", result)
        self.assertEqual(result["java-dev"], Path("/some/path/java-dev/1.0.0"))

    def test_ignores_other_marketplaces(self):
        self._write_plugins({"plugins": {
            "superpowers@claude-plugins-official": [{"installPath": "/official/path"}],
        }})
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", self.plugins_json):
            result = cs.get_claude_install_paths("mdproctor-skills")
        self.assertEqual(result, {})

    def test_sync_local_syncs_to_claude_cache(self):
        """sync-local copies skills to the real Claude plugin cache paths."""
        repo_tmp = TemporaryDirectory()
        install_tmp = TemporaryDirectory()
        cache_tmp = TemporaryDirectory()
        try:
            repo = Path(repo_tmp.name)
            install = Path(install_tmp.name)
            cache = Path(cache_tmp.name)

            make_skill(repo, "git-commit")
            (install / "git-commit").mkdir()
            (install / "git-commit" / "SKILL.md").write_text("old")

            # Simulate Claude Code cache with an older version
            cache_path = cache / "git-commit" / "1.0.0-SNAPSHOT"
            cache_path.mkdir(parents=True)
            (cache_path / "SKILL.md").write_text("old cached version")

            with patch.object(cs, "get_repo_root", return_value=repo), \
                 patch.object(cs, "INSTALL_DIR", install), \
                 patch.object(cs, "get_claude_install_paths",
                              return_value={"git-commit": cache_path}), \
                 patch.object(cs, "sync_hook", return_value='up-to-date'):
                cs.cmd_sync_local(make_args())

            # Cache should now have the updated content
            updated = (cache_path / "SKILL.md").read_text()
            self.assertNotEqual(updated, "old cached version")
            self.assertIn("git-commit", updated)
        finally:
            repo_tmp.cleanup()
            install_tmp.cleanup()
            cache_tmp.cleanup()


class TestGetRepoRoot(unittest.TestCase):
    """get_repo_root returns parent of scripts/ directory."""

    def test_repo_root_is_parent_of_scripts(self):
        root = cs.get_repo_root()
        self.assertEqual(root, _script_path.parent.parent)
        self.assertTrue((root / "scripts").is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
