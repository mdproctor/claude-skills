# Commit Squash Policy

**Principle:** Good commit messages are information. The noise patterns below
are mechanical artifacts of the development process, not meaningful history.
Keep the signal, remove the noise.

**Tie-breaking rule:** When a commit matches multiple SQUASH rows, the first
matching row wins. Squash targets are always the preceding KEEP commit; if
none exists in the range, squash *forward* into the next KEEP commit instead.
If no KEEP commits exist at all, treat the most substantive commit as KEEP
and squash the rest into it.

---

## Keep as standalone commits

| Pattern | Reason to keep |
|---------|---------------|
| `feat(scope): ...` | Introduces a new capability — the what and why matter |
| `fix(scope): ...` with ≥ 10 lines changed | Real bug fix with context |
| `fix(scope): ...` correcting user-visible output | Error messages, labels, UI strings — always standalone regardless of size |
| `test(scope): <scenario name> ...` | Describes a specific test scenario — documents intended behaviour |
| `refactor(scope): ...` with ≥ 20 lines changed | Structural change worth understanding |
| `perf(scope): ...` with ≥ 10 lines changed | Performance change — the tradeoff matters |
| `adr: ...` | Architecture decision record — always standalone |
| `docs: DESIGN.md ...` with substantive content | Design decisions, not fixups |
| Any commit referencing an issue number (`Closes #N`, `Refs #N`) | Traceability — always standalone regardless of size |

---

## Squash into the preceding meaningful commit

Process rows in order — first match wins.

| Priority | Pattern | Action |
|----------|---------|--------|
| 1 | `wip:` / `WIP` / `checkpoint:` / `savepoint:` / `temp:` | Always squash — save-state artifacts |
| 2 | `Merge branch '...'` / `Merge pull request #...` | Always squash — workflow noise |
| 3 | `Revert "..."` followed within 3 commits by a replacement | Squash all three (revert + retry + fix) into the final working commit |
| 4 | `build: wire ...` with a `Revert "build: wire ..."` following it | Both noise — squash into the eventual working state |
| 5 | `style: ...` / `chore: apply spotless` / `chore: fix formatting` | Always squash — cosmetic only |
| 6 | `chore: remove dead ...` / `chore: update .gitignore` / `chore: bump version` | Squash into preceding commit |
| 7 | `docs(scope): align Javadoc ...` / `docs(scope): fix wording` / `docs(scope): add missing ...` | Squash into the feature commit it follows |
| 8 | `fix(test): ...` where the same test class was fixed in the previous commit | Squash — same test being hardened |
| 9 | `ci: retrigger` / `build: bump` when standalone with no following commit to absorb into | ❌ DROP — zero information value, discard entirely |
| 9b | `ci: retrigger` / `fix(ci): ...` / `build: bump` when a feature commit follows | Squash into the feature it unblocked |
| 10 | Any commit with `< 5 lines changed` (excluding blank lines and imports) and no issue reference | Squash into preceding commit |
| 11 | Multiple commits with near-identical messages on the same class/file | Identify the most complete, integrate unique content, squash the rest |

---

## Merge similar commits into a unified message

When two or more commits address the same concern, merge into one if a single
message tells the story more cleanly.

**Signals that two commits should merge:**
- Same scope and file set (both touching the same class/module)
- Sequential commits forming one logical change ("add field" + "wire field into handler")
- Two `test:` commits for the same scenario (setup + assertion split across commits)
- Two `feat:` commits that are clearly part one and part two of the same capability

**How to write the unified message:**
- Use the broader of the two scopes
- Combine the key points — richer than either alone, but no longer than necessary
- Keep all issue references from both commits

**Do not merge** commits from different features or scopes just because they
are small. Merge only when the result tells a cleaner, more complete story.

**Good — same concern, single story:**
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

**Revert chains:** `Revert X` + `X (attempt 2)` + eventual fix → collapse to one
commit with the final message, noting the approach that worked. Never preserve
failed attempts.

**Test hardening runs:** When 3+ commits repeatedly touch the same test class,
identify the one with the most complete message, integrate unique context from
the others, squash the rest.

**Long squash chains:** When squashing 4+ commits into one, the resulting message
must remain readable. Summarise rather than concatenate — one tight message beats
four messages stapled together.

**CI/build fixups:** `ci: retrigger`, `build: bump`, `fix(ci): correct URL` —
squash into the feature they were unblocking, or discard if purely mechanical.

---

## Examples

### Keep all — each commit tells a distinct story
```
feat(engine): wire WorkerStatusListener and CaseChannelProvider — Closes #152
test(blackboard): R1 — two sequential stages activate in order
test(blackboard): R3 — exit condition satisfied by worker output end-to-end
fix(blackboard): nested stage activation gated on parent ACTIVE state
feat(blackboard): CaseEvictionHandler — evict plan models on terminal case state
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

### Squash — cleanup after feature
```
KEEP   → feat(engine): wire WorkerStatusListener, WorkerContextProvider, CaseChannelProvider
SQUASH ← chore: remove dead workerContextProvider.buildContext() call
SQUASH ← style: apply spotless formatting
```

### Drop — purely mechanical, zero information value
```
❌ DROP  ci: trigger CI for PR #199
❌ DROP  ci: retrigger (network timeout)
```

### Merge — two halves of one capability
```
MERGE ← feat(api): add UserRepository SPI interface
MERGE ← feat(api): wire UserRepository into ServiceLocator
INTO  → feat(api): add UserRepository SPI and wire into ServiceLocator
```
