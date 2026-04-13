# Handover — 2026-04-13

**Branch:** main
**Head:** 97bfd39

---

## What Changed This Session

**workspace-init hardened** — CLAUDE.md detection and migration (copy-delete-symlink),
expanded Step 9 artifact detection (HANDOFF.md, .superpowers/, docs/_posts/),
automated git rm + commit, Step 9b session history migration (`mv ~/.claude/projects/`),
Step 5 prompt-confirm before writing CLAUDE.md, Step 5b optional additions
(proactive handover on context pressure).

**cccli workspace created** — `~/claude/public/cccli/`, CLAUDE.md migrated,
artifacts migrated, session history moved. Smoke tested: `add-dir` fires
automatically — confirmed.

**Epic lifecycle model** — workspaces are ephemeral per epic branch, not
long-lived archives. Specs/plans posted to GitHub issue at epic close
(visible summary + `<details>`), ADRs/blog promoted to project repo.
`epic-start` + `epic-close` skills filed as mdproctor/cc-praxis#49.

**DESIGN.md** — open questions resolved, "Next Steps" → "Design Backlog:
No open design decisions."

---

## Immediate Next Step

**Design DESIGN.md interaction between project and workspace versions** —
the user wants to nail how project `DESIGN.md` and `workspace/design/DESIGN.md`
relate: when they diverge, how merging works at epic close, what "working copy"
means in practice. Start there next session.

---

## References

| Context | Where |
|---------|-------|
| workspace-init skill | `workspace-init/SKILL.md` |
| Workspace model spec (updated) | `docs/superpowers/specs/2026-04-09-workspace-model-design.md` |
| Workspace model plan (updated) | `docs/superpowers/plans/2026-04-09-workspace-model.md` |
| epic-lifecycle issue | mdproctor/cc-praxis#49 |
| cccli workspace | `~/claude/public/cccli/` |
| Previous handover | `git show HEAD~1:HANDOFF.md` |
