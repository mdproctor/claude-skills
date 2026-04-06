# Handover — 2026-04-06

**Head commit:** `0a512d9` — fix(retro-issues): fix classifier bugs and add scope-based clustering
**Previous handover:** `git show HEAD~1:HANDOVER.md` | diff: `git diff HEAD~1 HEAD -- HANDOVER.md`

## What Changed This Session

- **issue-workflow** completely rewritten — merged the draft epic-workflow concept in. Now 4 phases: Phase 0 Setup, Phase 1 Pre-Implementation (epic + child issues with active epic/issue state), Phase 2 Task Intake (proactive issue creation before coding + ad-hoc placement flowchart + planned-vs-adhoc distinction), Phase 3 Pre-Commit safety net. Explicit user override required to skip issue refs.
- **retro-issues** new standalone skill — `/retro-issues` command for mapping git history to GitHub epics/issues. Three-stage: gather inputs → write `docs/retro-issues.md` for review → create on YES. Bundled scripts (`retro-parse-mapping.py`, `retro-amend-commits.py`). Optional commit amendment uses branch-swap safety pattern.
- **Tests** — 90 passing: 7 parser unit tests, 11-repo fixture integration tests, synthetic edge-case tests. Fixtures extracted from all ~/claude repos and committed (self-contained — no runtime dependency on ~/claude).
- **Two classifier bugs fixed** — `format(?:s)?` matched "formats" (noun); `update .+ to` matched "update description to". Scope-based clustering added as primary signal over file paths.
- **Garden** — 3 submissions: GE-0042 (regex plural false positive), GE-0043 (commit scope clustering), GE-0044 (MADR Date: field never auto-populated).

## State Right Now

- `main` clean, pushed to GitHub, 46/46 skills synced
- `retro-issues` live and validated (pre-GitHub-creation analysis run on this repo)
- Garden: 38 submissions pending merge (GE-0001–GE-0044, some already merged)

## Immediate Next Step

Open a **new session** in this repo and run `/retro-issues`. Review the generated `docs/retro-issues.md` — stop before Step 8 (no GitHub issues until YES). Key things to validate:
- Scope clustering produces sensible groupings (marketplace/garden/write-blog etc.)
- Trivials correctly excluded (only 2 expected)
- Only 1 phase boundary found (v1.0.0 tag) — no epics expected, just issues

## Open Questions / Blockers

*Unchanged — `git show HEAD~1:HANDOVER.md`* (image index, publish-blog, v1.0.1 tag)

- ADR Date: fields are empty across all 10 ADRs — if boundary detection from ADRs matters, the `adr` skill should auto-populate Date: on creation. Git log proxy: `git log --follow --diff-filter=A --format="%ad" --date=short -- docs/adr/FILE.md`

## References

| Context | Where | Retrieve with |
|---------|-------|---------------|
| retro-issues skill | `retro-issues/SKILL.md` | `cat` |
| retro-issues plan | `docs/superpowers/plans/2026-04-06-retrospective-issue-mapping.md` | `cat` |
| issue-workflow skill | `issue-workflow/SKILL.md` | `cat` |
| Latest design snapshot | `docs/design-snapshots/2026-04-06-writing-infrastructure-and-garden.md` | `cat` |
| Garden submissions | `~/claude/knowledge-garden/submissions/` | `ls` then `cat` |
| Previous handover | git history | `git show HEAD~1:HANDOVER.md` |
