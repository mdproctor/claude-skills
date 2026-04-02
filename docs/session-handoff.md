# Session Handoff — cc-praxis Health & Refine Skills

**Date:** 2026-04-02
**Repository:** github.com/mdproctor/cc-praxis
**Working directory:** /Users/mdproctor/claude/skills

---

## What We Just Finished

Designed and documented a complete health and refinement skill system. Six design documents are in `docs/`:

| Document | Status | Purpose |
|----------|--------|---------|
| `project-health.md` | ✅ Design complete | Universal health checks, routes to type-specific |
| `project-refine.md` | ✅ Design complete | Improvement opportunities across docs and code |
| `java-project-health.md` | ✅ Design complete | Java/Quarkus-specific health checks |
| `blog-project-health.md` | ✅ Design complete | Jekyll/GitHub Pages-specific health checks |
| `custom-project-health.md` | ✅ Design complete | Custom project health checks |
| `skills-project-health.md` | ✅ Design complete | Skills repository health checks |

**These are design documents only — the skills have NOT been implemented yet.**

---

## Key Design Decisions Made

**Architecture: Bidirectional chain**
- `/project-health` detects project type, runs universal checks, auto-chains to the type-specific skill in the same session
- `/java-project-health` runs universal checks first as prerequisite, then its own — identical output to `/project-health` on a java project
- Either entry point produces the same result

**Tier system (both skills)**
- `--tier 1` / `--commit` — validators only (~30s)
- `--tier 2` / `--standard` — universal quality checks, no type-specific (~5 min)
- `--tier 3` / `--prerelease` — full universal + type-specific (~15 min)
- `--tier 4` / `--deep` — everything + refinement questions (~30 min)
- If `--tier` is omitted, user is prompted to choose 1-4

**project-refine tiers**
- Tier 1: structural checks, no file reading (~2 min)
- Tier 2: read top candidates by churn+size, search-based duplication (~10 min)
- Tier 3: deeper scan, IntelliJ MCP if available (~20 min)
- Tier 4: full scope, focus prompt for user-specified directory (~30-45 min)

**Implementation approach**
- Run `validate_all.py --tier commit` first (mechanical checks), then Claude handles judgment checks
- Auto-fix mechanical issues with confirmation (propose → YES → apply)
- `--save` writes `YYYY-MM-DD-health-report.md` (gitignored, date-prefixed)
- Deferred findings: always show all — can add defer mechanism later if needed

**project-refine code scanning**
- Tier 1: user-specified scope if given, otherwise skip to tiers 2+3
- Tiers 2+3: combine git churn + file size to identify top ~15 candidates to read
- Tier 4: adds focus prompt "which directory/package should I look at?"
- Search-based tools (grep, `ide_search_text`) always run for duplication detection regardless of tier

---

## What To Do Next

The immediate task is to **trial the designs on this repository** using the design documents as the skill specification:

```bash
# Try project-health on this skills repo
/project-health --tier 3

# Try project-refine
/project-refine --tier 2

# Or use the type-specific entry point directly
/skills-project-health --tier 3
```

Since the skills aren't built yet, to trial them read the design docs and manually follow the check lists in each relevant category.

After trialling, the next task is to **implement the six skills** as proper SKILL.md files following the cc-praxis conventions (CSO description, Use when..., commands/ directory for slash commands, etc.).

---

## Repository State

- **Branch:** main, up to date with origin
- **22 skills installed** in `~/.claude/skills/` (synced)
- **All tests passing:** `python3 -m pytest tests/ -q`
- **Validators passing:** `python3 scripts/validate_all.py`
- **Approaching v1.0** — health/refine implementation is the main remaining work

---

## Files to Read First in a New Session

1. `CLAUDE.md` — project conventions, skill architecture, no-AI-attribution rule
2. `docs/project-health.md` — the main design document
3. `docs/project-refine.md` — the companion skill design
4. Pick one type-specific doc depending on which project you're checking
