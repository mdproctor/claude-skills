#!/usr/bin/env python3
"""
Tests for scripts/validation/validate_blog_commit.py

Verifies each content type gets the correct conventions enforced.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "validation"))
from validate_blog_commit import validate_blog_commit, VALID_TYPES, MAX_SUBJECT_LENGTH


class TestValidTypes(unittest.TestCase):
    """Each valid type is accepted; all other types are rejected."""

    def test_post_type_accepted(self):
        self.assertEqual(validate_blog_commit("post: add guide to refactoring with Claude"), [])

    def test_edit_type_accepted(self):
        self.assertEqual(validate_blog_commit("edit: fix typos in MCP server post"), [])

    def test_draft_type_accepted(self):
        self.assertEqual(validate_blog_commit("draft: WIP post on Quarkus observability"), [])

    def test_asset_type_accepted(self):
        self.assertEqual(validate_blog_commit("asset: add refactoring diagram for MCP post"), [])

    def test_config_type_accepted(self):
        self.assertEqual(validate_blog_commit("config: update site theme colours"), [])

    def test_code_commit_types_rejected(self):
        for bad_type in ("feat", "fix", "refactor", "chore", "docs", "build", "test"):
            with self.subTest(type=bad_type):
                errors = validate_blog_commit(f"{bad_type}: some description")
                self.assertTrue(any("type" in e.lower() for e in errors),
                                f"Expected type error for '{bad_type}', got: {errors}")

    def test_unknown_type_rejected(self):
        errors = validate_blog_commit("article: some description")
        self.assertTrue(any("type" in e.lower() for e in errors))


class TestScopes(unittest.TestCase):
    """Scopes are optional but must be non-empty if present."""

    def test_scope_optional(self):
        self.assertEqual(validate_blog_commit("post: add guide to Claude Code"), [])

    def test_valid_scope_accepted(self):
        self.assertEqual(validate_blog_commit("post(java): add IntelliJ MCP Server guide"), [])

    def test_scope_with_hyphen_accepted(self):
        self.assertEqual(validate_blog_commit("post(claude-code): intro to skills"), [])

    def test_edit_with_scope(self):
        self.assertEqual(validate_blog_commit("edit(quarkus): update observability examples"), [])

    def test_asset_with_scope(self):
        self.assertEqual(validate_blog_commit("asset(mcp): add server comparison diagram"), [])

    def test_empty_scope_rejected(self):
        errors = validate_blog_commit("post(): add guide")
        self.assertTrue(any("scope" in e.lower() for e in errors))


class TestSubjectLength(unittest.TestCase):
    """Subject line must not exceed MAX_SUBJECT_LENGTH (72 chars for blog)."""

    def test_exactly_at_limit_accepted(self):
        # post: + space + 66 chars of description = 72 total
        desc = "a" * 66
        msg = f"post: {desc}"
        self.assertEqual(len(msg), 72)
        self.assertEqual(validate_blog_commit(msg), [])

    def test_one_over_limit_rejected(self):
        desc = "a" * 67
        msg = f"post: {desc}"
        self.assertEqual(len(msg), 73)
        errors = validate_blog_commit(msg)
        self.assertTrue(any("long" in e.lower() or str(MAX_SUBJECT_LENGTH) in e for e in errors))

    def test_short_subject_accepted(self):
        self.assertEqual(validate_blog_commit("post(java): add MCP guide"), [])

    def test_72_char_limit_not_50(self):
        """Blog posts use 72 char limit, not the 50-char code commit limit."""
        # 51-char description — valid for blog, would fail code commits
        desc = "a" * 51
        msg = f"post: {desc}"
        self.assertGreater(len(msg), 50)
        self.assertLessEqual(len(msg), 72)
        self.assertEqual(validate_blog_commit(msg), [])


class TestDescription(unittest.TestCase):
    """Description must be present and not end with a period."""

    def test_empty_description_rejected(self):
        errors = validate_blog_commit("post: ")
        self.assertTrue(any("description" in e.lower() or "empty" in e.lower() for e in errors))

    def test_trailing_period_rejected(self):
        errors = validate_blog_commit("post: add guide to refactoring.")
        self.assertTrue(any("period" in e.lower() for e in errors))

    def test_trailing_period_with_scope_rejected(self):
        errors = validate_blog_commit("edit(java): fix code examples.")
        self.assertTrue(any("period" in e.lower() for e in errors))

    def test_description_without_period_accepted(self):
        self.assertEqual(validate_blog_commit("post: add guide to refactoring"), [])

    def test_question_mark_accepted(self):
        """Titles ending in ? are fine for blog posts."""
        self.assertEqual(validate_blog_commit("post: is IntelliJ's MCP server enough?"), [])


class TestBodyFormat(unittest.TestCase):
    """Body must be separated from subject by a blank line."""

    def test_body_with_blank_line_accepted(self):
        msg = "post(java): add IntelliJ MCP guide\n\nCovers the IDE Index MCP plugin and three-tier strategy."
        self.assertEqual(validate_blog_commit(msg), [])

    def test_body_without_blank_line_rejected(self):
        msg = "post(java): add IntelliJ MCP guide\nCovers the IDE Index MCP plugin."
        errors = validate_blog_commit(msg)
        self.assertTrue(any("blank" in e.lower() or "second line" in e.lower() for e in errors))

    def test_no_body_accepted(self):
        self.assertEqual(validate_blog_commit("edit: fix typos in observability post"), [])

    def test_multiline_body_accepted(self):
        msg = "post(mcp): add IDE Index MCP Server guide\n\nCovers setup, configuration, and the three-tier\nrefactoring strategy for Java projects."
        self.assertEqual(validate_blog_commit(msg), [])


class TestPostTypeConventions(unittest.TestCase):
    """post type — new blog post added."""

    def test_new_post_valid(self):
        self.assertEqual(
            validate_blog_commit("post(java): give Claude Code IntelliJ's brain"),
            []
        )

    def test_new_post_with_body(self):
        msg = "post(cc-praxis): introducing the cc-praxis skills collection\n\nOverview of the Java/Quarkus skills and universal principles."
        self.assertEqual(validate_blog_commit(msg), [])

    def test_new_post_no_scope_valid(self):
        self.assertEqual(validate_blog_commit("post: my first Claude Code blog post"), [])


class TestEditTypeConventions(unittest.TestCase):
    """edit type — updating an existing published post."""

    def test_edit_typos_valid(self):
        self.assertEqual(validate_blog_commit("edit: fix typos across MCP server post"), [])

    def test_edit_with_topic_scope(self):
        self.assertEqual(
            validate_blog_commit("edit(quarkus): add missing @Blocking annotation example"),
            []
        )

    def test_edit_code_examples(self):
        self.assertEqual(
            validate_blog_commit("edit(java): update code examples for Java 21"),
            []
        )


class TestDraftTypeConventions(unittest.TestCase):
    """draft type — work-in-progress, not yet published."""

    def test_draft_wip_valid(self):
        self.assertEqual(validate_blog_commit("draft: WIP post on Quarkus observability"), [])

    def test_draft_with_scope(self):
        self.assertEqual(validate_blog_commit("draft(java): outline for virtual threads post"), [])

    def test_draft_no_wip_label_also_valid(self):
        """WIP label is conventional but not enforced."""
        self.assertEqual(validate_blog_commit("draft: thoughts on AI-assisted refactoring"), [])


class TestAssetTypeConventions(unittest.TestCase):
    """asset type — images, CSS, JS, or other non-post files."""

    def test_add_image_valid(self):
        self.assertEqual(validate_blog_commit("asset: add MCP server architecture diagram"), [])

    def test_add_css_valid(self):
        self.assertEqual(validate_blog_commit("asset: update syntax highlighting theme"), [])

    def test_asset_with_scope(self):
        self.assertEqual(validate_blog_commit("asset(mcp): add port configuration table image"), [])


class TestConfigTypeConventions(unittest.TestCase):
    """config type — _config.yml, layouts, includes, Gemfile."""

    def test_config_yml_change_valid(self):
        self.assertEqual(validate_blog_commit("config: enable pagination plugin"), [])

    def test_layout_change_valid(self):
        self.assertEqual(validate_blog_commit("config: add post layout with reading time"), [])

    def test_gemfile_update_valid(self):
        self.assertEqual(validate_blog_commit("config: bump jekyll-feed to 0.17"), [])


class TestEdgeCases(unittest.TestCase):

    def test_empty_message_rejected(self):
        errors = validate_blog_commit("")
        self.assertTrue(len(errors) > 0)

    def test_whitespace_only_rejected(self):
        errors = validate_blog_commit("   ")
        self.assertTrue(len(errors) > 0)

    def test_no_colon_separator_rejected(self):
        errors = validate_blog_commit("post add a guide")
        self.assertTrue(len(errors) > 0)

    def test_multiple_errors_reported(self):
        """Wrong type AND trailing period should both be reported."""
        errors = validate_blog_commit("feat: add a post.")
        self.assertGreaterEqual(len(errors), 2)

    def test_valid_types_constant_has_five_entries(self):
        self.assertEqual(len(VALID_TYPES), 5)
        self.assertEqual(VALID_TYPES, {'post', 'edit', 'draft', 'asset', 'config'})


if __name__ == "__main__":
    unittest.main(verbosity=2)
