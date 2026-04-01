#!/usr/bin/env python3
"""
Unit tests for scripts/claude-skill

Tests sync-local, install registry management, hook management,
and list/uninstall commands.
Uses temporary directories throughout — never touches the real Claude installation.
"""

import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from importlib.machinery import SourceFileLoader
_script_path = Path(__file__).parent.parent / "scripts" / "claude-skill"
cs = SourceFileLoader("claude_skill", str(_script_path)).load_module()


def make_args(**kwargs) -> SimpleNamespace:
    """Build a minimal args namespace with safe defaults."""
    defaults = {"all": False, "yes": True}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_skill(directory: Path, name: str) -> Path:
    """Create a minimal skill directory with SKILL.md and plugin.json."""
    skill_dir = directory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: >\n  Use when testing.\n---\n# {name}\n"
    )
    plugin_dir = skill_dir / ".claude-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(
        json.dumps({"name": name, "version": "1.0.0-SNAPSHOT"})
    )
    return skill_dir


def make_plugins_json(tmp: Path, skills: dict) -> Path:
    """
    Write a minimal installed_plugins.json.
    skills: {skill_name: install_path_str}
    """
    plugins_json = tmp / "installed_plugins.json"
    plugins = {
        f"{name}@mdproctor-skills": [{"installPath": path, "version": "1.0.0-SNAPSHOT",
                                       "installedAt": "2026-01-01T00:00:00+00:00",
                                       "lastUpdated": "2026-01-01T00:00:00+00:00",
                                       "scope": "user"}]
        for name, path in skills.items()
    }
    plugins_json.write_text(json.dumps({"version": 2, "plugins": plugins}))
    return plugins_json


# ---------------------------------------------------------------------------
# sync-local: updates installed skills
# ---------------------------------------------------------------------------

class TestSyncLocalUpdatesInstalledSkills(unittest.TestCase):
    """sync-local copies updated local skills into the Claude plugin cache."""

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.cache_tmp = TemporaryDirectory()
        self.plugins_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)
        self.cache = Path(self.cache_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.cache_tmp.cleanup()
        self.plugins_tmp.cleanup()

    def _cache_path(self, name):
        return self.cache / name / "1.0.0-SNAPSHOT"

    def _make_installed(self, name, content="old content"):
        path = self._cache_path(name)
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(content)
        return path

    def test_updated_file_is_synced(self):
        make_skill(self.repo, "git-commit")
        cache_path = self._make_installed("git-commit")
        plugins_json = make_plugins_json(
            Path(self.plugins_tmp.name), {"git-commit": str(cache_path)}
        )

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args())

        content = (cache_path / "SKILL.md").read_text()
        self.assertIn("git-commit", content)
        self.assertNotEqual(content, "old content")

    def test_multiple_installed_skills_all_updated(self):
        for name in ("git-commit", "java-dev", "adr"):
            make_skill(self.repo, name)
            self._make_installed(name)

        cache_paths = {n: str(self._cache_path(n)) for n in ("git-commit", "java-dev", "adr")}
        plugins_json = make_plugins_json(Path(self.plugins_tmp.name), cache_paths)

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args())

        for name in ("git-commit", "java-dev", "adr"):
            content = (self._cache_path(name) / "SKILL.md").read_text()
            self.assertNotEqual(content, "old content")


# ---------------------------------------------------------------------------
# sync-local: skips uninstalled skills without --all
# ---------------------------------------------------------------------------

class TestSyncLocalSkipsUninstalled(unittest.TestCase):

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.plugins_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.plugins_tmp.cleanup()

    def test_uninstalled_skill_not_created(self):
        make_skill(self.repo, "java-dev")
        plugins_json = make_plugins_json(Path(self.plugins_tmp.name), {})

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args())

        data = json.loads(plugins_json.read_text())
        self.assertNotIn("java-dev@mdproctor-skills", data["plugins"])

    def test_installed_skill_updated_uninstalled_skipped(self):
        make_skill(self.repo, "git-commit")
        make_skill(self.repo, "java-dev")

        cache_dir = Path(self.plugins_tmp.name) / "cache" / "git-commit" / "1.0.0-SNAPSHOT"
        cache_dir.mkdir(parents=True)
        (cache_dir / "SKILL.md").write_text("old")

        plugins_json = make_plugins_json(
            Path(self.plugins_tmp.name), {"git-commit": str(cache_dir)}
        )

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args())

        self.assertNotEqual((cache_dir / "SKILL.md").read_text(), "old")
        data = json.loads(plugins_json.read_text())
        self.assertNotIn("java-dev@mdproctor-skills", data["plugins"])


# ---------------------------------------------------------------------------
# sync-local: --all installs new skills
# ---------------------------------------------------------------------------

class TestSyncLocalAllFlag(unittest.TestCase):

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.plugins_tmp = TemporaryDirectory()
        self.cache_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.plugins_tmp.cleanup()
        self.cache_tmp.cleanup()

    def test_uninstalled_skill_installed_with_all_flag(self):
        make_skill(self.repo, "java-dev")
        plugins_json = make_plugins_json(Path(self.plugins_tmp.name), {})

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "PLUGIN_CACHE", Path(self.cache_tmp.name)), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args(**{"all": True}))

        data = json.loads(plugins_json.read_text())
        self.assertIn("java-dev@mdproctor-skills", data["plugins"])

    def test_all_flag_updates_existing_and_installs_new(self):
        make_skill(self.repo, "git-commit")
        make_skill(self.repo, "java-dev")

        cache_dir = Path(self.cache_tmp.name) / "git-commit" / "1.0.0-SNAPSHOT"
        cache_dir.mkdir(parents=True)
        (cache_dir / "SKILL.md").write_text("old")

        plugins_json = make_plugins_json(
            Path(self.plugins_tmp.name), {"git-commit": str(cache_dir)}
        )

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "PLUGIN_CACHE", Path(self.cache_tmp.name)), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args(**{"all": True}))

        self.assertNotEqual((cache_dir / "SKILL.md").read_text(), "old")
        data = json.loads(plugins_json.read_text())
        self.assertIn("java-dev@mdproctor-skills", data["plugins"])


# ---------------------------------------------------------------------------
# sync-local: always copies, never symlinks to cache
# ---------------------------------------------------------------------------

class TestSyncLocalAlwaysCopies(unittest.TestCase):

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.plugins_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.plugins_tmp.cleanup()

    def test_cache_is_real_directory_not_symlink(self):
        make_skill(self.repo, "git-commit")
        cache_dir = Path(self.plugins_tmp.name) / "cache" / "git-commit" / "1.0.0-SNAPSHOT"
        cache_dir.mkdir(parents=True)
        (cache_dir / "SKILL.md").write_text("old")

        plugins_json = make_plugins_json(
            Path(self.plugins_tmp.name), {"git-commit": str(cache_dir)}
        )

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args())

        self.assertFalse(cache_dir.is_symlink())
        self.assertTrue(cache_dir.is_dir())


# ---------------------------------------------------------------------------
# sync-local: edge cases
# ---------------------------------------------------------------------------

class TestSyncLocalEdgeCases(unittest.TestCase):

    def setUp(self):
        self.repo_tmp = TemporaryDirectory()
        self.plugins_tmp = TemporaryDirectory()
        self.repo = Path(self.repo_tmp.name)

    def tearDown(self):
        self.repo_tmp.cleanup()
        self.plugins_tmp.cleanup()

    def test_empty_repo_exits_cleanly(self):
        (self.repo / "docs").mkdir()
        plugins_json = make_plugins_json(Path(self.plugins_tmp.name), {})

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args())

    def test_dirs_without_skill_md_ignored(self):
        make_skill(self.repo, "git-commit")
        (self.repo / "docs").mkdir()
        (self.repo / "scripts").mkdir()

        cache_dir = Path(self.plugins_tmp.name) / "git-commit" / "1.0.0-SNAPSHOT"
        cache_dir.mkdir(parents=True)
        (cache_dir / "SKILL.md").write_text("old")
        plugins_json = make_plugins_json(
            Path(self.plugins_tmp.name), {"git-commit": str(cache_dir)}
        )

        with patch.object(cs, "get_repo_root", return_value=self.repo), \
             patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", Path(self.plugins_tmp.name) / "settings.json"), \
             patch.object(cs, "sync_hook", return_value="up-to-date"):
            cs.cmd_sync_local(make_args(**{"all": True}))

        data = json.loads(plugins_json.read_text())
        self.assertNotIn("docs@mdproctor-skills", data["plugins"])
        self.assertNotIn("scripts@mdproctor-skills", data["plugins"])


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_shows_installed_skills(self):
        plugins_json = make_plugins_json(
            Path(self.tmp.name),
            {"adr": "/p/adr", "git-commit": "/p/git-commit", "java-dev": "/p/java-dev"}
        )
        buf = io.StringIO()
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), redirect_stdout(buf):
            cs.cmd_list(SimpleNamespace())

        out = buf.getvalue()
        self.assertIn("adr", out)
        self.assertIn("git-commit", out)
        self.assertIn("java-dev", out)

    def test_no_skills_installed(self):
        plugins_json = make_plugins_json(Path(self.tmp.name), {})
        buf = io.StringIO()
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), redirect_stdout(buf):
            cs.cmd_list(SimpleNamespace())

        self.assertIn("No skills installed", buf.getvalue())

    def test_missing_plugins_json(self):
        plugins_json = Path(self.tmp.name) / "missing.json"
        buf = io.StringIO()
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), redirect_stdout(buf):
            cs.cmd_list(SimpleNamespace())

        self.assertIn("No skills installed", buf.getvalue())


# ---------------------------------------------------------------------------
# cmd_uninstall
# ---------------------------------------------------------------------------

class TestCmdUninstall(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.cache_tmp = TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()
        self.cache_tmp.cleanup()

    def test_uninstall_removes_cache_directory(self):
        cache_path = Path(self.cache_tmp.name) / "git-commit" / "1.0.0-SNAPSHOT"
        cache_path.mkdir(parents=True)
        (cache_path / "SKILL.md").write_text("content")

        plugins_json = make_plugins_json(Path(self.tmp.name), {"git-commit": str(cache_path)})
        settings_path = Path(self.tmp.name) / "settings.json"

        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", settings_path):
            cs.cmd_uninstall(SimpleNamespace(skill="git-commit"))

        self.assertFalse(cache_path.exists())
        data = json.loads(plugins_json.read_text())
        self.assertNotIn("git-commit@mdproctor-skills", data["plugins"])

    def test_uninstall_nonexistent_skill_exits(self):
        plugins_json = make_plugins_json(Path(self.tmp.name), {})
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json):
            with self.assertRaises(SystemExit) as ctx:
                cs.cmd_uninstall(SimpleNamespace(skill="nonexistent"))
        self.assertNotEqual(ctx.exception.code, 0)

    def test_uninstall_removes_from_settings(self):
        cache_path = Path(self.cache_tmp.name) / "git-commit" / "1.0.0-SNAPSHOT"
        cache_path.mkdir(parents=True)

        plugins_json = make_plugins_json(Path(self.tmp.name), {"git-commit": str(cache_path)})
        settings_path = Path(self.tmp.name) / "settings.json"
        settings_path.write_text(json.dumps({
            "enabledPlugins": {"git-commit@mdproctor-skills": True}
        }))

        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json), \
             patch.object(cs, "SETTINGS_PATH", settings_path):
            cs.cmd_uninstall(SimpleNamespace(skill="git-commit"))

        settings = json.loads(settings_path.read_text())
        self.assertNotIn("git-commit@mdproctor-skills", settings.get("enabledPlugins", {}))


# ---------------------------------------------------------------------------
# Plugin registry helpers
# ---------------------------------------------------------------------------

class TestGetInstalledPlugins(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_empty_when_missing(self):
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", Path(self.tmp.name) / "missing.json"):
            data = cs.get_installed_plugins()
        self.assertEqual(data["plugins"], {})

    def test_reads_existing_file(self):
        plugins_json = make_plugins_json(Path(self.tmp.name), {"git-commit": "/some/path"})
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json):
            data = cs.get_installed_plugins()
        self.assertIn("git-commit@mdproctor-skills", data["plugins"])


class TestGetClaudeInstallPaths(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_empty_when_file_missing(self):
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", Path(self.tmp.name) / "missing.json"):
            self.assertEqual(cs.get_claude_install_paths(), {})

    def test_returns_paths_for_matching_marketplace(self):
        plugins_json = make_plugins_json(
            Path(self.tmp.name),
            {"java-dev": "/some/path/java-dev/1.0.0",
             "git-commit": "/some/path/git-commit/1.0.0-SNAPSHOT"}
        )
        # Add an unrelated plugin
        data = json.loads(plugins_json.read_text())
        data["plugins"]["superpowers@claude-plugins-official"] = [{"installPath": "/other"}]
        plugins_json.write_text(json.dumps(data))

        with patch.object(cs, "INSTALLED_PLUGINS_JSON", plugins_json):
            result = cs.get_claude_install_paths()

        self.assertIn("java-dev", result)
        self.assertIn("git-commit", result)
        self.assertNotIn("superpowers", result)

    def test_ignores_other_marketplaces(self):
        pj = Path(self.tmp.name) / "installed_plugins.json"
        pj.write_text(json.dumps({"version": 2, "plugins": {
            "superpowers@claude-plugins-official": [{"installPath": "/official/path"}]
        }}))
        with patch.object(cs, "INSTALLED_PLUGINS_JSON", pj):
            self.assertEqual(cs.get_claude_install_paths(), {})


class TestRegisterPluginInSettings(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_adds_to_enabled_plugins(self):
        with patch.object(cs, "SETTINGS_PATH", self.settings):
            cs.register_plugin_in_settings("java-dev")
        settings = json.loads(self.settings.read_text())
        self.assertTrue(settings["enabledPlugins"]["java-dev@mdproctor-skills"])

    def test_preserves_existing_settings(self):
        self.settings.write_text(json.dumps({"model": "claude-opus"}))
        with patch.object(cs, "SETTINGS_PATH", self.settings):
            cs.register_plugin_in_settings("java-dev")
        settings = json.loads(self.settings.read_text())
        self.assertEqual(settings["model"], "claude-opus")
        self.assertIn("java-dev@mdproctor-skills", settings["enabledPlugins"])


class TestDeregisterPluginInSettings(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_removes_from_enabled_plugins(self):
        self.settings.write_text(json.dumps({
            "enabledPlugins": {"java-dev@mdproctor-skills": True, "adr@mdproctor-skills": True}
        }))
        with patch.object(cs, "SETTINGS_PATH", self.settings):
            cs.deregister_plugin_in_settings("java-dev")
        settings = json.loads(self.settings.read_text())
        self.assertNotIn("java-dev@mdproctor-skills", settings["enabledPlugins"])
        self.assertIn("adr@mdproctor-skills", settings["enabledPlugins"])

    def test_no_error_when_missing(self):
        with patch.object(cs, "SETTINGS_PATH", Path(self.tmp.name) / "missing.json"):
            cs.deregister_plugin_in_settings("java-dev")  # should not raise


# ---------------------------------------------------------------------------
# Hook management (unchanged behaviour)
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

    def test_creates_settings_if_missing(self):
        cs.register_hook(self.settings)
        self.assertTrue(cs.is_hook_registered(self.settings))

    def test_preserves_existing_settings(self):
        self.settings.write_text(json.dumps({"someOtherKey": "value"}))
        cs.register_hook(self.settings)
        settings = json.loads(self.settings.read_text())
        self.assertEqual(settings["someOtherKey"], "value")
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
        self.assertEqual(self.dest.read_text(), self.source.read_text())

    def test_up_to_date_when_unchanged(self):
        self.dest.parent.mkdir()
        self.dest.write_text(self.source.read_text())
        cs.register_hook(self.settings)
        self.assertEqual(self._sync(), 'up-to-date')

    def test_registered_when_file_ok_but_not_in_settings(self):
        self.dest.parent.mkdir()
        self.dest.write_text(self.source.read_text())
        self.assertEqual(self._sync(), 'registered')
        self.assertTrue(cs.is_hook_registered(self.settings))

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
