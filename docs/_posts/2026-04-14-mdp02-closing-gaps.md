---
layout: post
title: "cc-praxis — Closing the Gaps"
date: 2026-04-14
type: phase-update
entry_type: note
subtype: diary
projects: [cc-praxis]
---
# cc-praxis — Closing the Gaps

**Date:** 2026-04-14
**Type:** phase-update

---

The session started with a parked idea. Blog entries had needed a type taxonomy since April 13 — articles vs. diary notes — sitting in IDEAS.md. I brought Claude in and we designed it in under an hour, brainstormed the spec, then shipped via TDD subagents. Fourteen existing blog entries got backfilled with `entry_type: note`, `subtype: diary`, `projects: [cc-praxis]`. While we were in there, `yaml_utils.py` got replaced — the homemade YAML parser couldn't handle list fields, so it was swapped out for PyYAML. Validator count went from 17 to 18.

Mid-session I noticed a gap in the workspace model. Artifact routing had essentially one destination with different syntax: the project repo. If a project wants zero methodology artifacts in its own repo, there's nowhere for ADRs and DESIGN.md to accumulate between epics. The workspace is already a git repo with `main` — it just wasn't wired as a routing target.

I spent time with Claude designing the fix: three routing layers (built-in default → `~/.claude/CLAUDE.md` → workspace CLAUDE.md), three targets (`project`, `workspace`, `alternative <path>`). We specced it, implemented it in `epic-close` and `workspace-init`, then ran a systematic consistency review. Six issues found — including a SHA baseline ratchet bug where routing `design → workspace` would silently corrupt the next epic's three-way merge if the baseline wasn't updated.

The health sweeps ran twice. First pass: the `garden` skill documented in five README sections but not existing — we replaced it with `forage` months ago, never cleaned up the docs. Web app stats bar showed 44/17/295 instead of 48/19/446. The blog INDEX.md listed 1 of 14 posts. Second pass: CLAUDE.md's quick reference had `flowcharts` in the commit tier when it runs in push. We fixed all of it, plus count drift across README, QUALITY.md, CLAUDE.md, and SKILL-MANAGER.md.

Test coverage was the day's largest chunk. Before today: 446 tests, 3 of 22 validators covered. I brought Claude in to dispatch TDD subagent batches with one instruction: "read the source first, then write tests." That instruction turned out to matter considerably.

Claude's agents came back with findings from reading the source. `validate_links.py` uses `requests.get`, not `requests.head` — most link validators use HEAD to avoid downloading content, so the mock target assumption was wrong. Any test patching `requests.head` would pass silently while testing nothing. `validate_cross_document.py` writes to stderr, not stdout. `validate_examples.py` silently skips any JSON block matching `{[^}]*}` as a template marker — you need array-format JSON to reach the WARNING path. Three forage entries written on the spot.

One debugging session took longer than it should. We ran `generate_web_app_data.py` from a git worktree and it reported "CHAINING_TRUTH: updated (48 skills)". The test still failed with empty `builds_on` lists. The script was finding the file, writing to it, reporting success — but every list was `[]`. The problem: the session's CWD was the worktree directory. `Path.cwd()` returned the worktree root. The worktree inherits `CLAUDE.md` from the main repo, so `find_skills_root()` stopped walking upward there, `glob('*/SKILL.md')` found nothing, and the script wrote empty data and logged a success. Nothing in the output signalled any of this.

Final: 1016 tests, 19 of 19 registered validators covered. Six forage entries submitted — three gotchas, one technique, two undocumented.
