# cc-praxis — Design Snapshot
**Date:** 2026-04-06
**Topic:** Full collection state — writing infrastructure and garden system
**Supersedes:** *(none — first snapshot)*
**Superseded by:** *(leave blank)*

---

## Where We Are

cc-praxis is a 45-skill Claude Code skills collection spanning Java, TypeScript, Python, and methodology skills. The collection includes a web installer UI, comprehensive validation infrastructure, and a machine-wide knowledge garden. Two significant systems matured this session: the writing infrastructure (mandatory rules, layered style guide, gated enforcement) and the knowledge garden (GE-ID system, three-tier duplicate detection, DEDUPE workflow, integrity validator).

## How We Got Here

Key decisions made to reach this point.

| Decision | Chosen | Why | Alternatives Rejected |
|---|---|---|---|
| Blog writing rules split into layers | mandatory-rules.md + common-voice.md + personal guide | Separation of concerns — non-negotiable craft vs voice defaults vs personal style | Single monolithic style guide (caused enforcement gaps) |
| GE-IDs assigned at submission time | Counter in GARDEN.md, updated at CAPTURE | Submitter can track their entry; enables REVISE by stable ID | ID at merge time (submitter couldn't track, REVISE required fragile path+title) |
| Three-tier duplicate detection | Light (index scan) at CAPTURE, medium (section read) at MERGE, exhaustive DEDUPE periodically | Cost-appropriate — don't pay for deep check on every submission | Full check at every merge (too expensive as garden grows) |
| Sparse pair log (CHECKED.md) | Track only compared pairs, not full matrix | O(N) sweep cost per new batch, not O(N²) | Full matrix (prohibitive at scale) |
| Drift-based DEDUPE trigger | Activity counter vs threshold (default 10) | Scales to actual usage; quiet periods cost nothing | Fixed schedule (ignores activity level) |
| DISCARDED.md for merge rejections | Record discarded GE-ID → canonical GE-ID | Submitter can reconcile; convert to REVISE targeting correct entry | Silent discard (submitter has no way to recover) |
| Dev-only skills pattern | Normal skill in repo, excluded from marketplace.json and README | Marketplace users don't have the scripts; developers get slash commands | Separate skills directory (not auto-discovered) |
| Blog filename convention | YYYY-MM-DD-NN-title.md (always numbered) | Same-day entries sort correctly without renaming | Unnumbered (collision on same-day entries) |
| write-blog defaults/ directory | Bundled mandatory-rules.md and common-voice.md ship with the skill | Any user of write-blog gets baseline craft rules; personal guide is additive | All rules in SKILL.md (too large, can't be overridden per-layer) |
| write-blog four-layer architecture | Mandatory → CLAUDE.md inference → voice (common or personal) → invocation overrides | Clean separation; CLAUDE.md infers audience/topic; personal guide is voice only | Flat single guide (couldn't separate universal from personal) |

## Where We're Going

The garden has 35 submissions (GE-0001–GE-0035) ready to merge — this is the immediate next step. The merge session will assign GE-IDs to all entries, populate CHECKED.md with light duplicate checks, and initialize the garden with real content.

**Next steps:**
- Merge all 35 garden submissions in a dedicated session (full context budget)
- Remove stale `~/.claude/skills/knowledge-garden/` directory (old pre-rename install)
- Consider v1.0.1 tag — significant additions since v1.0.0

**Open questions:**
- Should the image index (`docs/images/IMAGE-INDEX.md`) be global (machine-wide like the garden) or stay project-level? Currently project-level but the rationale may shift once used in practice.
- The `publish-blog` skill (personal, not in cc-praxis) — when blog entries are ready to publish, what's the integration point? Series navigation is deferred to it but the skill isn't built yet.
- The dual-repo model for epic-scoped developer work (logged in idea-log) — worth revisiting before any large upcoming project phase.
- Garden DEDUPE sweep hasn't run yet — CHECKED.md and drift system are untested in practice.

## Linked ADRs

*(No ADRs created yet — decisions captured in blog entries and this snapshot.)*

## Context Links

- Blog entries: `docs/blog/2026-04-06-01-writing-about-itself.md`, `docs/blog/2026-04-06-02-writing-rules-get-teeth.md`
- Garden state: `~/claude/knowledge-garden/GARDEN.md`
- Garden validator: `~/claude/knowledge-garden/scripts/validate_garden.py`
- Test scenarios: `~/claude/knowledge-garden/scripts/TEST-SCENARIOS.md`
