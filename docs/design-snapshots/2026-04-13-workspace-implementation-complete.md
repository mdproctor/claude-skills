# cc-praxis — Design Snapshot
**Date:** 2026-04-13
**Topic:** Workspace model implemented + design doc consolidation
**Supersedes:** [2026-04-09-workspace-model](2026-04-09-workspace-model.md)
**Superseded by:** *(leave blank — filled in if this snapshot is later superseded)*

---

## Where We Are

The workspace model is fully implemented and shipped. All 47 skills are synced. Skills now write methodology artifacts to `~/claude/private/<project>/` (workspace) rather than the project repo, with `workspace-init` handling per-project setup. Design snapshots for CaseHub, QuarkMind, cccli, remotecc, and hortora were consolidated into their primary design documents and deleted — completing the shift away from snapshot-per-session accumulation toward a single authoritative design file. The write-blog voice defaults were tightened to reduce theatrical tone. 433 tests pass.

## How We Got Here

| Decision | Chosen | Why | Alternatives Rejected |
|---|---|---|---|
| Workspace path | `~/claude/private/<project>/` or `public/` | Hidden, namespaced, tool-agnostic | `~/claude/<project>/` (confusing with project repos in same dir) |
| CLAUDE.md symlink | `.git/info/exclude` (never `.gitignore`) | Works for any repo regardless of ownership | Tracked `.gitignore` (modifies the upstream repo) |
| Snapshot accumulation | Drop entirely — single authoritative design file | Snapshots at different time periods create stale-content risk when merging | Keep snapshot chain (maintenance burden grows linearly) |
| Design doc consolidation | 8-point review checklist mandatory | Ad-hoc merges reliably leave gaps, conflicts, redundancy | Single readthrough (misses 6 of 8 defect classes) |
| write-blog drama | Explicit "theatrical dramatisation" ban in mandatory-rules | Common-voice guide alone didn't prevent heightened stakes language | Style guide only (advisory, easy to rationalize past) |

## Where We're Going

**Next steps:**
- Smoke test `workspace-init` in a live session — verify CLAUDE.md symlink auto-loads in Claude Code (still empirically unverified)
- Run `/harvest` on merged garden PRs (GE-0004 through GE-0009 now merged)
- Consolidate cc-praxis's own `docs/design-snapshots/` — 4 older snapshots exist, same process as the other projects

**Open questions:**
- Does Claude Code follow a CLAUDE.md symlink for session initialisation? Assumed yes but untested.
- Should cc-praxis set up its own workspace (`/workspace-init`)? Currently the project runs as its own CWD.

## Linked ADRs

*(No ADRs for cc-praxis yet)*

## Context Links

- Implementation plan (completed): `docs/superpowers/plans/2026-04-09-workspace-model.md`
- Design spec: `docs/superpowers/specs/2026-04-09-workspace-model-design.md`
- Issue #48 (closed): mdproctor/cc-praxis#48
