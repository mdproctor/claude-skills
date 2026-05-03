# Commit Squash Policy

**Purpose:** Applied on demand and enforced pre-push by the `git-squash` skill.
Retains the granular, well-written commit messages that carry genuine information
while eliminating noise that obscures the history.

**Principle:** Good commit messages are information. The noise patterns below are
mechanical artifacts of the development process, not meaningful history. This
policy keeps the signal and removes the noise.

---

## Keep as standalone commits

These commit types carry information a future developer needs when reading `git log`:

| Pattern | Reason to keep |
|---------|---------------|
| `feat(scope): ...` | Introduces a new capability — the what and why matter |
| `fix(scope): ...` with ≥ 10 lines changed | Real bug fix with context |
| `test(scope): <scenario name> ...` | Describes specific test scenario — documents intended behaviour |
| `refactor(scope): ...` with ≥ 20 lines changed | Structural change worth understanding |
| `adr: ...` | Architecture decision record — always standalone |
| `docs: DESIGN.md ...` with substantive content | Design decisions, not fixups |
| Any commit referencing an issue number (`Closes #N`, `Refs #N`) | Traceability |

---

## Squash into the preceding meaningful commit

These are artifacts of the development process, not history:

| Pattern | Action |
|---------|--------|
| `Revert "..."` followed within 3 commits by a replacement | Squash all three (revert + retry + fix) into the final working commit |
| `chore: remove dead ...` / `chore: apply spotless` / `chore: fix formatting` | Squash into preceding commit |
| `docs(scope): align Javadoc ...` / `docs(scope): fix wording` / `docs(scope): add missing ...` | Squash into the feature commit it follows |
| `fix(test): ...` where the same test class was fixed in the previous commit | Squash — it's the same test being hardened |
| `build: wire ...` with a `Revert "build: wire ..."` following it | Both are noise — squash into the eventual working state |
| Any commit with `< 5 lines changed` and no issue reference | Squash into preceding commit |
| Multiple commits with near-identical messages on the same class/file | Identify the most complete commit, integrate any unique information from the others into its message, then squash the rest |

---

## Merge similar commits into a unified message

When two or more commits address the same concern — even if both have detailed,
well-written messages — they can be merged into one if a single message can
capture the full story more cleanly than two separate ones.

**Signals that two commits should merge:**
- Same scope and file set (`fix(blackboard): X` + `fix(blackboard): Y` both touching the same file)
- Sequential commits that together form one logical change ("add field" + "wire field into handler")
- Two `test:` commits for the same feature scenario (setup + assertion split across commits)
- Two `feat:` commits that are clearly part one and part two of the same capability

**How to write the unified message:**
- Use the broader of the two scopes
- Combine the key points from both messages into one description
- If both had issue references, keep all of them
- The unified message should be richer than either individual message alone

**Example:**
```
MERGE ← feat(blackboard): add PlanItem strict lifecycle — markRunning/markCompleted
MERGE ← feat(blackboard): PlanItem lifecycle validation — IllegalStateTransition guard
INTO → feat(blackboard): PlanItem strict lifecycle with IllegalStateTransition guard —
       markRunning/markCompleted enforce valid transitions; concurrent CAS prevents races
```

Do not merge commits from different features or scopes just because they are small.
Merge only when the result tells a cleaner, more complete story than either commit alone.

---

## Special cases

**Revert chains:** `Revert X` + `X (attempt 2)` + `fix` → collapse to one commit with the
final message, noting the approach that worked. Do not preserve the failed attempts.

**Test hardening runs:** When 3+ commits touch the same test class (`fix(test): ...`
repeatedly), identify the one with the most complete message, integrate any unique
context from the others, and squash the rest into it.

**CI/build fixups:** `ci: retrigger`, `build: bump`, `fix(ci): correct URL` — squash into
the feature or fix they were unblocking, or discard if purely mechanical.

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

### Squash — revert chain collapses to one
```
SQUASH ← build: wire casehub-parent BOM and GitHub Packages for quarkus-ledger
SQUASH ← Revert "build: wire casehub-parent BOM and GitHub Packages for quarkus-ledger"
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
SQUASH ← chore: remove unused wiring tests
```

### Merge — two halves of one capability
```
MERGE ← feat(api): add UserRepository SPI interface
MERGE ← feat(api): wire UserRepository into ServiceLocator
INTO  → feat(api): add UserRepository SPI and wire into ServiceLocator
```
