# Blog Entry Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `entry_type`, `subtype`, `projects`, and `tags` frontmatter fields to blog entries, update write-blog/SKILL.md to prompt for them, and add a blog entry frontmatter validator.

**Architecture:** Purely additive — new frontmatter fields on all blog entries, a new validator that checks them, and a one-step addition to the write-blog workflow. No routing implementation (publish-blog is out of scope). Routing config format is documented in the design spec.

**Tech Stack:** Python 3 (validator), Markdown/YAML (frontmatter), pytest

**Spec:** `docs/superpowers/specs/2026-04-14-blog-entry-types-design.md`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `scripts/validation/validate_blog_frontmatter.py` | Create | Validates blog entry frontmatter fields |
| `tests/test_blog_frontmatter.py` | Create | Tests for the new validator |
| `scripts/validate_all.py` | Modify | Register validator in commit tier |
| `write-blog/SKILL.md` | Modify | Add Step 1 article/note prompt + update Success Criteria |
| `docs/_posts/*.md` (14 files) | Modify | Backfill new frontmatter fields |
| `QUALITY.md` | Modify | Update validator count and Implementation Status |
| `README.md` | Modify | Update validator count in Skill Quality & Validation |

---

### Task 1: Write failing tests for blog entry frontmatter validator

**Files:**
- Create: `tests/test_blog_frontmatter.py`

- [ ] **Step 1: Write the test file**

```python
# tests/test_blog_frontmatter.py
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.validation.validate_blog_frontmatter import validate_blog_entry_frontmatter


def test_valid_diary_entry():
    frontmatter = {
        'layout': 'post',
        'title': 'Test Entry',
        'date': '2026-04-14',
        'type': 'phase-update',
        'entry_type': 'note',
        'subtype': 'diary',
        'projects': ['cc-praxis'],
    }
    assert validate_blog_entry_frontmatter(frontmatter) == []


def test_valid_article():
    frontmatter = {
        'layout': 'post',
        'title': 'Test Article',
        'date': '2026-04-14',
        'entry_type': 'article',
        'projects': ['cc-praxis'],
        'tags': ['quarkus'],
    }
    assert validate_blog_entry_frontmatter(frontmatter) == []


def test_article_with_multiple_projects():
    frontmatter = {
        'layout': 'post',
        'title': 'Test Article',
        'date': '2026-04-14',
        'entry_type': 'article',
        'projects': ['cc-praxis', 'quarkus-flow'],
        'tags': ['quarkus', 'skills'],
    }
    assert validate_blog_entry_frontmatter(frontmatter) == []


def test_tags_optional():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'article',
        'projects': ['cc-praxis'],
        # no tags field
    }
    assert validate_blog_entry_frontmatter(frontmatter) == []


def test_missing_entry_type():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'type': 'phase-update',
        'projects': ['cc-praxis'],
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('entry_type' in e for e in errors)


def test_invalid_entry_type():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'diary',  # wrong — diary is a subtype, not an entry_type
        'projects': ['cc-praxis'],
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('entry_type' in e for e in errors)


def test_missing_projects():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'note',
        'subtype': 'diary',
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('projects' in e for e in errors)


def test_empty_projects():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'note',
        'subtype': 'diary',
        'projects': [],
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('projects' in e for e in errors)


def test_projects_not_a_list():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'note',
        'subtype': 'diary',
        'projects': 'cc-praxis',  # should be a list
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('projects' in e for e in errors)


def test_note_missing_subtype():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'note',
        'projects': ['cc-praxis'],
        # no subtype
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('subtype' in e for e in errors)


def test_article_no_subtype_required():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'article',
        'projects': ['cc-praxis'],
        # no subtype — correct for articles
    }
    assert validate_blog_entry_frontmatter(frontmatter) == []


def test_tags_must_be_list():
    frontmatter = {
        'layout': 'post',
        'title': 'Test',
        'date': '2026-04-14',
        'entry_type': 'article',
        'projects': ['cc-praxis'],
        'tags': 'quarkus',  # should be a list
    }
    errors = validate_blog_entry_frontmatter(frontmatter)
    assert any('tags' in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail (import error expected)**

```bash
python3 -m pytest tests/test_blog_frontmatter.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `validate_blog_frontmatter` doesn't exist yet.

---

### Task 2: Implement the blog entry frontmatter validator

**Files:**
- Create: `scripts/validation/validate_blog_frontmatter.py`

- [ ] **Step 1: Write the validator**

```python
#!/usr/bin/env python3
"""
Validate frontmatter in blog entry files (docs/_posts/).

Checks:
- entry_type present and valid (article | note)
- subtype present for notes (e.g. diary)
- projects present and non-empty list
- tags, if present, is a list
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import (
    ValidationIssue, ValidationResult, Severity, print_summary
)
from utils.yaml_utils import extract_frontmatter

VALID_ENTRY_TYPES = {'article', 'note'}
BLOG_DIR = Path('docs/_posts')


def validate_blog_entry_frontmatter(frontmatter: dict) -> list[str]:
    """
    Validate blog entry frontmatter fields.
    Returns list of error message strings — empty list means valid.
    """
    errors = []

    # entry_type required and valid
    entry_type = frontmatter.get('entry_type')
    if not entry_type:
        errors.append("Missing required field: entry_type (article | note)")
    elif entry_type not in VALID_ENTRY_TYPES:
        errors.append(
            f"Invalid entry_type '{entry_type}': must be one of "
            f"{sorted(VALID_ENTRY_TYPES)}"
        )

    # projects required and non-empty list
    projects = frontmatter.get('projects')
    if projects is None:
        errors.append("Missing required field: projects (non-empty list of project identifiers)")
    elif not isinstance(projects, list):
        errors.append(f"projects must be a list, got {type(projects).__name__}")
    elif len(projects) == 0:
        errors.append("projects must be non-empty")

    # subtype required for notes
    if entry_type == 'note':
        subtype = frontmatter.get('subtype')
        if not subtype:
            errors.append(
                "Missing required field: subtype for entry_type 'note' "
                "(e.g. 'diary')"
            )

    # tags must be a list if present
    tags = frontmatter.get('tags')
    if tags is not None and not isinstance(tags, list):
        errors.append(f"tags must be a list, got {type(tags).__name__}")

    return errors


def validate_blog_file(path: Path) -> list[ValidationIssue]:
    """Validate a single blog entry file."""
    issues = []

    frontmatter, error, _ = extract_frontmatter(path)

    if error:
        issues.append(ValidationIssue(
            severity=Severity.CRITICAL,
            file_path=str(path),
            line_number=1,
            message=error,
            fix_suggestion="Add valid YAML frontmatter"
        ))
        return issues

    for msg in validate_blog_entry_frontmatter(frontmatter):
        issues.append(ValidationIssue(
            severity=Severity.CRITICAL,
            file_path=str(path),
            line_number=1,
            message=msg,
            fix_suggestion="Add or correct the field in frontmatter"
        ))

    return issues


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate blog entry frontmatter')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('files', nargs='*', help='Specific files to check')
    args = parser.parse_args()

    if args.files:
        blog_files = [Path(f) for f in args.files]
    else:
        blog_files = sorted(BLOG_DIR.glob('*.md')) if BLOG_DIR.exists() else []
        # Exclude INDEX.md
        blog_files = [f for f in blog_files if f.name != 'INDEX.md']

    all_issues = []
    for path in blog_files:
        all_issues.extend(validate_blog_file(path))

    result = ValidationResult(
        validator_name='Blog Entry Frontmatter',
        issues=all_issues,
        files_checked=len(blog_files)
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_summary(result, verbose=args.verbose)

    sys.exit(result.exit_code)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run tests — expect passing**

```bash
python3 -m pytest tests/test_blog_frontmatter.py -v
```

Expected: all 13 tests PASS.

- [ ] **Step 3: Run validator against existing blog entries (expect failures)**

```bash
python3 scripts/validation/validate_blog_frontmatter.py --verbose
```

Expected: CRITICAL errors on all 14 entries — `entry_type`, `projects` missing. This confirms the validator works and shows what the backfill task must fix.

---

### Task 3: Register validator in commit tier

**Files:**
- Modify: `scripts/validate_all.py`

- [ ] **Step 1: Add validator to the commit tier list**

In `scripts/validate_all.py`, find the `'commit'` list and add after `validate_project_types.py`:

```python
# Before:
{'script': 'validate_project_types.py', 'name': 'Project Type Lists', 'target': None},
```

```python
# After:
{'script': 'validate_project_types.py', 'name': 'Project Type Lists', 'target': None},
{'script': 'validate_blog_frontmatter.py', 'name': 'Blog Entry Frontmatter', 'target': None},
```

- [ ] **Step 2: Run full commit-tier validation to confirm registration**

```bash
python3 scripts/validate_all.py --tier commit --verbose
```

Expected: `Blog Entry Frontmatter` appears in results. It will report CRITICAL failures (14 blog entries not yet backfilled) — that's expected at this stage.

- [ ] **Step 3: Commit**

```bash
git add scripts/validation/validate_blog_frontmatter.py tests/test_blog_frontmatter.py scripts/validate_all.py
git commit -m "feat(validation): add blog entry frontmatter validator"
```

---

### Task 4: Backfill existing blog entries

**Files:**
- Modify: all 14 files in `docs/_posts/`

Add three fields after the existing `type:` line in each file. All existing entries are diary notes for cc-praxis.

Fields to add:
```yaml
entry_type: note
subtype: diary
projects: [cc-praxis]
```

- [ ] **Step 1: Backfill all 14 entries**

For each file in `docs/_posts/` (except `INDEX.md`), insert after the `type:` line:

```
2026-03-29-mdp01-day-zero.md              type: day-zero
2026-03-31-mdp01-building-the-infrastructure.md  type: phase-update
2026-04-02-mdp01-health-typescript-python.md     type: phase-update
2026-04-03-mdp01-the-web-installer.md            type: phase-update
2026-04-04-mdp01-the-methodology-family.md       type: phase-update
2026-04-06-mdp01-writing-about-itself.md         type: phase-update
2026-04-06-mdp02-writing-rules-get-teeth.md      type: phase-update
2026-04-06-mdp03-garden-remembers-itself.md      type: phase-update
2026-04-07-mdp01-retrospective-runs-on-itself.md type: phase-update
2026-04-07-mdp02-issue-tracking-live.md          type: phase-update
2026-04-08-mdp01-words-matter-then-gardens-grow.md type: phase-update
2026-04-09-mdp01-where-claude-lives-now.md       type: phase-update
2026-04-13-mdp01-workspace-init-ships.md         type: phase-update
2026-04-14-mdp01-the-model-comes-together.md     type: phase-update
```

After each `type: <value>` line, insert:
```yaml
entry_type: note
subtype: diary
projects: [cc-praxis]
```

- [ ] **Step 2: Run the validator to confirm all entries pass**

```bash
python3 scripts/validation/validate_blog_frontmatter.py --verbose
```

Expected: `Blog Entry Frontmatter: 14 files checked, 0 issues`

- [ ] **Step 3: Run full commit-tier validation — must be clean**

```bash
python3 scripts/validate_all.py --tier commit
```

Expected: all validators pass.

- [ ] **Step 4: Commit**

```bash
git add docs/_posts/
git commit -m "feat(blog): backfill entry_type, subtype, projects frontmatter"
```

---

### Task 5: Update write-blog/SKILL.md

**Files:**
- Modify: `write-blog/SKILL.md`

Three changes: Step 1 (add article/note prompt), Step 6 (frontmatter block), Success Criteria.

- [ ] **Step 1: Update Step 1 — add article/note classification**

Replace the current `### Step 1 — Confirm entry type and voice` section (lines 237–249) with:

```markdown
### Step 1 — Confirm entry type and voice

**Part A — Article or note?**

Ask (or infer from context if obvious):

```
Article or note?

  [A] Article — topic-driven, standalone
  [N] Note / diary — session narrative  (default: N)

Projects: [<project-name from CLAUDE.md>]   ← confirm or extend
Tags (optional):
```

Set frontmatter from the response:
- `entry_type: article` or `entry_type: note`
- `subtype: diary` (if note — the only subtype currently; omit for articles)
- `projects: [...]` — pre-populate from the project's CLAUDE.md `Name:` field; user may extend
- `tags: [...]` — if provided; omit field entirely if no tags given

**Part B — Narrative type (notes only; skip for articles)**

If invoked via `/write-blog <context>`, the type was already proposed in Step 0b — confirm or adjust here, don't ask again from scratch.

If type is still undetermined, infer from context:
- First entry ever? → **Day Zero**
- Phase milestone or significant work? → **Phase Update**
- Direction changing? → **Pivot**
- Earlier entry proved wrong? → **Correction**

**Part C — Voice**

Also determine: is this primarily solo exploration (use "I") or collaborative
work (use "we")? Both can appear in the same entry — use whichever fits each
sentence.
```

- [ ] **Step 2: Update Step 6 — add new fields to frontmatter block**

In Step 6 (Write to disk), update the frontmatter example. Find the file-writing section and ensure the frontmatter written includes the new fields:

```yaml
---
layout: post
title: "<title>"
date: YYYY-MM-DD
type: <day-zero|phase-update|pivot|correction>   # omit for articles
entry_type: <article|note>
subtype: diary                                    # omit for articles
projects: [<project>, ...]
tags: [<tag>, ...]                               # omit if empty
---
```

- [ ] **Step 3: Update Success Criteria — add new field checks**

In `## Success Criteria`, after the file existence check, add:

```markdown
- ✅ `entry_type` present in frontmatter (`article` or `note`)
- ✅ `projects` non-empty list in frontmatter
- ✅ `subtype: diary` present for note entries; omitted for articles
```

- [ ] **Step 4: Run commit-tier validation**

```bash
python3 scripts/validate_all.py --tier commit --verbose
```

Expected: all validators pass.

- [ ] **Step 5: Sync the updated skill**

```bash
python3 scripts/claude-skill sync-local --all -y
```

Expected: `write-blog` synced to `~/.claude/skills/write-blog/`.

- [ ] **Step 6: Commit**

```bash
git add write-blog/SKILL.md
git commit -m "feat(write-blog): add article/note classification prompt at Step 1"
```

---

### Task 6: Update QUALITY.md and README.md

**Files:**
- Modify: `QUALITY.md` (validator count, Implementation Status)
- Modify: `README.md` (validator count in Skill Quality & Validation)

- [ ] **Step 1: Update validator count in QUALITY.md**

Find the validator count in `QUALITY.md § Implementation Status` and increment from 17 to 18. Update the COMMIT tier list to include `validate_blog_frontmatter.py`.

- [ ] **Step 2: Update validator count in README.md**

Find the validator count reference in `README.md § Skill Quality & Validation` and update from 17 to 18 validators. Add `validate_blog_frontmatter.py` to the COMMIT tier description.

- [ ] **Step 3: Update CLAUDE.md validator count**

Find in `CLAUDE.md`:
```
**18 validators across 3 tiers (COMMIT/PUSH/CI):**
```
Update to:
```
**18 validators across 3 tiers (COMMIT/PUSH/CI):**
```

And in the `**COMMIT tier (<2s)**` line, add `blog-frontmatter` to the list.

- [ ] **Step 4: Run commit-tier validation — final check**

```bash
python3 scripts/validate_all.py --tier commit
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all validators pass, all tests pass.

- [ ] **Step 5: Commit**

```bash
git add QUALITY.md README.md CLAUDE.md
git commit -m "docs: update validator count to 18, document blog frontmatter validator"
```
