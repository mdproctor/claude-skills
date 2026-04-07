# Handover — 2026-04-07

**Head commit:** `8840bf9` — feat(blog): author initials prefix in blog post filenames
**Previous handover:** `git show HEAD~1:HANDOVER.md` | diff: `git diff HEAD~1 HEAD -- HANDOVER.md`

## What Changed This Session

- **Work Tracking enabled by default** — `git-commit` Step 0b prompts whenever absent (not just new projects); `update-claude-md` Step 4b checks and offers; starter templates include section; cc-praxis/permuplate/sparge CLAUDE.md updated
- **Mandatory bug fix workflow** — `⛔` rule added to java-dev, python-dev, ts-dev, and code-review-principles (CRITICAL check): write failing test before fix, verify before reporting back
- **Blog filename initials** — `write-blog` now uses `YYYY-MM-DD-<initials>NN-slug.md`; initials from `~/.claude/settings.json` § `initials` (set to `mdp`); prompts once if absent
- **42 blog renames** across permuplate (12), remotecc (10), skills (9), sparge (5), starcraft (6) — all committed; permuplate + sparge pushed to GitHub
- **All pushed and synced** — cc-praxis, permuplate, sparge on GitHub; 46/46 skills synced

## State Right Now

- `main` clean, everything committed and pushed
- Garden: GE-0054, GE-0055 + prior GE-0048–GE-0050 pending merge

## Immediate Next Step

Everything is clean and pushed. Test the Work Tracking prompt in a real commit session on permuplate or sparge to verify the Step 0b flow works end-to-end.

## Open Questions / Blockers

*Unchanged — `git show HEAD~1:HANDOVER.md`* (retro-issues epic path, image index, publish-blog, v1.0.1 tag, ADR Date auto-populate, docs/retro-issues.md retention)

## References

| Context | Where | Retrieve with |
|---------|-------|---------------|
| Blog rename commits | each repo git log | `git log --oneline -- docs/blog/` |
| Work Tracking template | `update-claude-md/starter-templates.md` | `cat` |
| Bug fix workflow rule | `code-review-principles/SKILL.md` | `grep -A 10 "Bug Fix"` |
| Previous handover | git history | `git show HEAD~1:HANDOVER.md` |
