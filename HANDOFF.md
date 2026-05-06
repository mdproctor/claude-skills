# Handover — 2026-05-06

**Branch:** main  
**Head:** 81a8e25

*Previous handover (2026-04-14): `git show 5c3c516:HANDOFF.md`*

---

## What Changed Since Last Handover

### New skills

**`git-squash`** — commit squash skill with pre-push hook. Policy trained on casehub work/ledger/qhorus/claudony patterns. Rich diff table UX showing what gets squashed before committing. Pre-PR run is a safety net, not the primary step.

### Major skill work

**`workspace-init`** — extensive rework across ~20 commits:
- Family detection: detects multi-repo parent/child structures, offers nested workspace paths, batch creates workspaces for all family members, root `.gitignore` excludes child workspace repos
- Wizard UI: all questions batched into single `AskUserQuestion` calls (restores step-wizard header UI)
- Naming: `wsp-` tag with prefix/postfix choice; postfix always at the end (`casehub-work-wsp` not `casehub-wsp-work`)
- CLAUDE.md handling: explicit A/B choice (migrate vs keep in project); decision shown in plan and gated before execution; three explicit cases, none skippable
- Check B: always diffs local vs GitHub — clones missing peers
- Privacy: respects user's privacy choice — no longer hardcodes `--private`
- Specs routing: stays in project under `docs/specs/` — not migrated to workspace
- Superpowers install offered at Step 10c
- Dry-run plan shown before execution (Step 1.5)
- `**Name:**` field enforced — if absent, skill stops and directs user to fix

**`update-claude-md` + `write-blog`** — `**Name:**` field detection and enforcement added. Both skills stop if `Name:` absent from workspace CLAUDE.md.

**`handover` + `install-skills`** — content boundary protection extended beyond `write-blog`. Explicit author override allowed (default is not absolute).

**`issue-workflow`** — commit-msg hook added to hard-block unlinked commits.

**UX sweep** — replaced all "press Enter to proceed" with explicit typed responses (`go`, `YES`, `auto`) throughout all skills. Enter is unusable in chat UI.

**`write-blog`** — mandatory third-party reference review before any entry is saved.

**`adr`** — default location changed to `docs/adr/` (MADR/e-adr community standard).

### Open issues (from previous handover — verify still open)

- `#50` blog pipeline, `#52` publish-blog, `#53` Jekyll pages, `#54` workspace routing epic, `#56` epic-start SHA baseline

---

## State

Working tree clean. All commits on `main`, pushed.

## Immediate Next Step

Verify open issues are still current:
```bash
gh issue list --repo mdproctor/cc-praxis --state open
```

Then check if workspace-init smoke tests are still queued (they were deferred earlier this session pending manual testing).
