# Commit Squash Policy

**Principle:** Good commit messages are information. The noise patterns below
are mechanical artifacts of the development process, not meaningful history.
Keep the signal, remove the noise.

**Tie-breaking rule:** When a commit matches multiple rows, the first matching
row wins. Squash targets are always the preceding KEEP commit; if none exists
in the range, squash *forward* into the next KEEP commit instead. If no KEEP
commits exist at all, treat the most substantive commit as KEEP and squash
the rest into it.

---

## Always DROP — workspace operational artifacts

These commits record methodology and process, not code history. They belong in
the workspace, not in the project's `git log`. Always drop regardless of size
or content.

| Pattern | Reason |
|---------|--------|
| `docs: session handover ...` / `docs: session wrap ...` | Operational handoff — pure process noise |
| `docs: add blog entry ...` / `docs: add project blog entry ...` | Workspace diary — not code history |
| `docs(claude): ...` / `docs: ... in CLAUDE.md` / `chore: ... in CLAUDE.md` | Workspace methodology updates |
| `chore: retroactive issue linkage ...` | Commit metadata update — no code change |
| `ci: retrigger` / `ci: trigger CI for PR` | Mechanical CI artifact — zero information |

---

## Keep as standalone commits

| Pattern | Reason to keep |
|---------|---------------|
| `feat(scope): ...` | Introduces a new capability — the what and why matter |
| `fix(scope): ...` with ≥ 10 lines changed | Real bug fix with context |
| `fix(scope): ...` correcting user-visible output | Error messages, labels, UI strings — standalone regardless of size |
| `test(scope): <scenario name> ...` describing a specific scenario | Documents intended behaviour |
| `refactor(scope): ...` with ≥ 20 lines changed | Structural change worth understanding |
| `perf(scope): ...` with ≥ 10 lines changed | Performance change — the tradeoff matters |
| `adr: ...` | Architecture decision record — always standalone |
| `docs: <filename>.md` introducing a new document | New reference material — standalone if substantive |
| Any commit with code changes referencing an issue number (`Closes #N`, `Refs #N`) | Traceability — standalone regardless of size |

---

## Squash into the preceding meaningful commit

Process rows in order — first match wins.

| Priority | Pattern | Action |
|----------|---------|--------|
| 1 | `wip:` / `WIP` / `checkpoint:` / `savepoint:` / `temp:` | Always squash — save-state artifacts |
| 2 | `Merge branch '...'` / `Merge pull request #...` | Always squash — workflow noise |
| 3 | `Revert "..."` followed within 3 commits by a replacement | Squash all three into the final working commit |
| 4 | `build: wire ...` with a `Revert "build: wire ..."` following it | Both noise — squash into the eventual working state |
| 5 | `style: ...` / `chore: apply spotless` / `chore: fix formatting` | Always squash — cosmetic only |
| 6 | `chore: pin <tool> <version> in root pluginManagement` / `chore: add <tool> for CDI bean discovery` | Squash into the commit that triggered the need, or next infra commit |
| 7 | `chore: remove dead ...` / `chore: update .gitignore` / `chore: bump version` | Squash into preceding commit |
| 8 | `docs(scope): align Javadoc ...` / `docs(scope): fix wording` / `docs(scope): add missing ...` | Squash into the feature commit it follows |
| 9 | `docs: fix stale ... references post-rename` / `docs: fix stale ... references` (multiple trailing fixups after a rename commit) | MERGE all into the rename commit — they are part of the same sweep |
| 10 | `docs: ...` with issue reference immediately following `feat: ...` with the same issue reference | MERGE into the feat — same issue, same sitting |
| 11 | `fix(test): ...` where the same test class was fixed in the previous commit | Squash — same test being hardened |
| 12 | `fix(test): ...` adjusting timing, bounds, or parameters with no scenario change | Squash — test mechanical adjustment, not new scenario |
| 13 | `ci: use GH_PAT for ...` / `ci: standardise publish workflow` / `ci: add workflow_dispatch` / `ci: fix ...` | Squash into preceding commit, or DROP if no meaningful target |
| 14 | `fix(ci): ...` / `build: bump` when a feature commit follows | Squash into the feature it unblocked |
| 15 | `fix(ci): ...` / `ci: retrigger` / `build: bump` when no feature follows | ❌ DROP — see Always DROP table |
| 16 | Any commit with `< 5 lines changed` (excluding blank lines and imports) and no issue reference | Squash into preceding commit |
| 17 | Multiple commits with near-identical messages on the same class/file | Identify the most complete, integrate unique content, squash the rest |

---

## Merge similar commits into a unified message

When two or more commits address the same concern, merge into one if a single
message tells the story more cleanly.

**Signals that two commits should merge:**
- Same scope and file set (both touching the same class/module)
- Sequential commits forming one logical change ("add field" + "wire field into handler")
- Two `test:` commits for the same scenario (setup + assertion split across commits)
- Two `feat:` commits that are clearly part one and part two of the same capability
- A rename commit followed immediately by import/reference fixup commits

**How to write the unified message:**
- Use the broader of the two scopes
- Combine key points from both messages into one description — richer than either alone, no longer than necessary
- Keep all issue references from both commits

**Do not merge** commits from different features or scopes just because they are small.
Merge only when the result tells a cleaner, more complete story.

**Good — rename sweep merged into one:**
```
MERGE ← refactor: rename to casehub-work — groupId io.casehub, package io.casehub.work
MERGE ← docs: fix stale repo name references post-rename
MERGE ← docs: fix stale repo name references post-rename
MERGE ← fix: update imports in quarkus-work-notifications to io.casehub.connectors
INTO  → refactor: rename to casehub-work — groupId, package, import references updated
```

**Good — two halves of one capability:**
```
MERGE ← feat(blackboard): add PlanItem strict lifecycle — markRunning/markCompleted
MERGE ← feat(blackboard): PlanItem lifecycle validation — IllegalStateTransition guard
INTO  → feat(blackboard): PlanItem strict lifecycle with IllegalStateTransition guard —
        markRunning/markCompleted enforce valid transitions; concurrent CAS prevents races
```

**Bad — different modules, don't merge:**
```
DO NOT MERGE:
  feat(api): add UserRepository SPI
  feat(engine): wire WorkerStatusListener
These address different concerns in different modules.
```

---

## Special cases

**Revert chains:** `Revert X` + `X (attempt 2)` + eventual fix → collapse to one commit
with the final message. Never preserve failed attempts.

**Test hardening runs:** When 3+ commits repeatedly touch the same test class,
identify the one with the most complete message, integrate unique context, squash the rest.

**Long squash chains:** When squashing 4+ commits into one, summarise rather than
concatenate — one tight message beats four messages stapled together.

**Rename sweeps:** A major rename (groupId, package, artifact names) is always followed
by trailing fixup commits. MERGE all trailing fixups into the rename commit — they are
inseparable parts of the same change.

**No preceding KEEP target:** Squash forward into the next KEEP commit instead.

---

## Examples

### Drop — workspace operational artifacts
```
❌ DROP  docs: session handover 2026-05-02 — CI fixes and normative layer doc
❌ DROP  docs: add blog entry 2026-05-01 — three intermittent test failures
❌ DROP  docs(claude): update CLAUDE.md — fix stale paths post-ecosystem rename
❌ DROP  chore: retroactive issue linkage for naming consistency sweep
❌ DROP  ci: retrigger after quarkus-ledger findScore() publish
```

### Keep all — each commit tells a distinct story
```
feat(engine): wire WorkerStatusListener and CaseChannelProvider — Closes #152
test(blackboard): R1 — two sequential stages activate in order
fix(blackboard): nested stage activation gated on parent ACTIVE state
feat(blackboard): CaseEvictionHandler — evict plan models on terminal case state
```

### Merge — rename sweep (trailing fixups absorbed into rename)
```
MERGE ← refactor: rename to casehub-work — groupId io.casehub, package io.casehub.work
MERGE ← docs: fix stale repo name references post-rename
MERGE ← docs: fix stale repo name references post-rename
MERGE ← fix: update imports in quarkus-work-notifications to io.casehub.connectors
INTO  → refactor: rename to casehub-work — groupId, package, import references updated
```

### Squash — WIP and checkpoint artifacts
```
SQUASH ← wip: halfway through blackboard refactor
SQUASH ← checkpoint: tests passing locally
KEEP   → refactor(blackboard): extract PlanItemFactory — simplifies activation flow
```

### Squash — revert chain collapses to one
```
SQUASH ← build: wire casehub-parent BOM for quarkus-ledger
SQUASH ← Revert "build: wire casehub-parent BOM for quarkus-ledger"
KEEP   → build: remove embedded builds; use GitHub Packages; add distributionManagement
```

### Squash — small docs follow-on
```
KEEP   → feat(engine): add CaseMetaModelRepository and EventLogRepository SPI interfaces
SQUASH ← docs(engine): align findByKey Javadoc null-return wording
```

### Squash — cross-repo infrastructure chore
```
KEEP   → feat: add PostgreSQL LISTEN/NOTIFY broadcaster for distributed SSE (#93)
SQUASH ← chore: pin jandex-maven-plugin 3.1.2 in root pluginManagement
SQUASH ← chore: add jandex-maven-plugin for CDI bean discovery
```

### Merge — feat and its docs commit share same issue
```
MERGE ← feat: add PostgreSQL LISTEN/NOTIFY broadcaster for distributed SSE (#93)
MERGE ← docs: systematic documentation update for PostgreSQL broadcaster (#93)
INTO  → feat: add PostgreSQL LISTEN/NOTIFY broadcaster for distributed SSE —
        with documented configuration and usage (#93)
```

### Drop — purely mechanical CI
```
❌ DROP  ci: use GH_PAT for cross-repo repository_dispatch
❌ DROP  ci: add workflow_dispatch trigger to publish workflow
❌ DROP  ci: standardise publish workflow — consistent build/test/publish/dispatch chain
```
