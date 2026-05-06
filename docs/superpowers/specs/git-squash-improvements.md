# git-squash Skill — Remaining Improvements Spec

**Status:** Pending implementation  
**Derived from:** Engine Claude three-way brief + gap analysis session 2026-05-06  
**Context:** After completing the two-phase filter-repo rework, branch isolation, cross-author guard, and intelligence improvements, four gaps remain before the skill is ready for the casehubio ecosystem compaction and engine reconstruction.

---

## Gap 1 — Plan document format

### Problem

The current plan output has four format deficiencies identified in the engine Claude brief:

1. **Group headings use numbers** ("Group 35:") — the KEEP commit message should be the heading; group number is secondary metadata used only for refusal commands
2. **Already Clean lists every commit** — for large ranges (186 commits in ledger) this drowns the signal; should collapse to count + representative sample
3. **AFTER block has no sample** — shows the arithmetic but not a preview of what git log will actually look like
4. **No offer to write a markdown file** — for significant operations the plan should be persistable; currently exists only in the chat window and is lost to context compaction

### Required changes to SKILL.md Step 4 / 5a

#### Already Clean section

Replace full listing with count + representative sample:

```
## Already Clean — 186 commits (no action needed)
*To see all: `git log --oneline <base>..<HEAD>` excluding the 41 action groups below.*

Representative: feat(supplement), feat(merkle), feat(causality), feat(prov),
feat(reactive), feat(trust), feat(privacy), feat(enricher), feat(art12), feat(#62)...
```

Do not list individual SHAs. The user can always inspect with git log.

#### Action group headings — compaction format

Use the KEEP commit message as the heading. Group number is shown as secondary metadata only, used for refusal commands ("refuse 35", "refuse 12 35"):

```markdown
### refactor: rename to casehub-ledger — groupId io.casehub, package io.casehub.ledger
*Group 35 — absorbs 10 commits*

- 🔽 `2e86342` docs(claude): update CLAUDE.md post-rename *(docs(claude) — follow-on)*
- 🔽 `9613135` refactor: move source directories io/quarkiverse → io/casehub *(rename sweep)*
- 🔽 `5e1d54e` docs: fix stale repo name references post-rename *(stale ref sweep)*
- 🔽 `48dc333` docs: fix stale repo name references post-rename *(stale ref sweep)*
- 🔽 `fdc75c9` ci: fix SNAPSHOT deploy — avoid 422 on redeployment *(CI noise)*
- 🔽 `ea0b385` ci: delete stale SNAPSHOT versions before publish *(CI noise)*
- 🔽 `8788f23` ci: add workflow_dispatch trigger *(CI noise)*
- 🔽 `17b9ca9` fix(ci): remove delete-SNAPSHOT step causing 422 *(CI noise)*
- 🔽 `8129172` docs: add retention classes to structure table *(docs follow-on)*
- 🔽 `1868825` docs: close Quarkiverse submission idea *(docs follow-on)*
```

**Final message line** — only appears for MERGE operations where the curated unified message differs from the KEEP commit's original message. For plain SQUASH groups it is omitted — the KEEP commit message IS the final message:

```markdown
### feat(blackboard): add PlanItem strict lifecycle — markRunning/markCompleted
*Group 7 — MERGE with 1 commit*
**Final message:** `feat(blackboard): PlanItem strict lifecycle with IllegalStateTransition guard — markRunning/markCompleted enforce valid transitions; concurrent CAS prevents races`

- 🔀 `vwx6789` feat(blackboard): PlanItem lifecycle validation — IllegalStateTransition guard *(unified — two halves of one capability)*
```

#### AFTER block with sample

```
## AFTER — what `git log --oneline` will show

  325  commits on main (original)
   -25  pruned by filter-repo (HANDOFF.md + blog/ became empty)
   -72  absorbed by squash
  ─────────────────────────────────────────────────────────
   227  commits — no content lost

Sample (first 10 of 227):
  a1b2c3d  feat(supplement): LedgerSupplement base + three concrete supplements
  e4f5g6h  feat(supplement): LedgerSupplementSerializer — explicit per-type JSON
  ...
  (run `git log --oneline <work-branch>` to see the full list)
```

#### Offer to write markdown file

For any range > 10 commits, after showing the summary (Step 4), offer:

```
Write this plan to a file for review and sign-off? (YES / n)
  Default path: docs/superpowers/specs/squash-plan-YYYY-MM-DD.md
  (Can be reviewed by others before the swap is approved)
```

If YES, write the full plan document in the format above to that path on the **working branch** (not main). The file travels with the working branch, can be pushed for review, and is discarded when the working branch is deleted after the swap.

The markdown file format is the same as the screen format — the same headings, same group structure, same AFTER block — so it renders cleanly as a GitHub document.

---

## Gap 2 — PR/branch pre-pass for semantic grouping

### Problem

Classification currently works bottom-up from individual commit messages. For flat-history repos (ledger, work, qhorus, claudony), PR and branch metadata provides a higher-level semantic grouping — "these 12 commits all belong to feat/causality" — which makes reports more readable and groups more meaningful. For squash-merged repos (engine reconstruction), it is essential: without it, you cannot tell which original commits belonged to which PR.

### Two use cases

**Compaction (ledger/work/qhorus/claudony):** All original commits are present. PR/branch metadata provides grouping information. The output is still compaction-format (single KEEP per group), but group headings come from PR titles or branch names rather than the KEEP commit message.

**Reconstruction (engine):** Source branches were squash-merged — each PR became one commit on main. The pre-pass recovers the original branch commits and groups them under their PR heading. Output uses reconstruction-format (three-column table per PR).

### Pre-pass implementation (Step 0b in SKILL.md)

Run before classification, after creating the working branch:

```bash
# 1. Check for merged PRs whose merge commit SHA appears in the range
gh pr list --state merged --json number,title,mergeCommit,headRefName,author,mergedAt \
  --limit 500 2>/dev/null

# 2. Check for surviving remote branch tips that match commits in the range
git branch -r | grep -E "origin/(feat|fix|refactor|docs|chore)/" 2>/dev/null

# 3. Get commit SHAs in range for matching
git log --format="%H" <range>
```

Hard timeout: 10 seconds total. If gh is unavailable or times out, skip the pre-pass silently and proceed with compaction format. Never surface the failure to the user.

### Matching strategies (in priority order)

**Strategy A — Direct SHA match (squash-merge)**  
`gh pr list` returns `mergeCommit.oid`. If that SHA appears in the range, all commits on `headRefName` that were squashed into it are members of that PR group.

**Strategy B — Merge commit in range (merge-commit PR)**  
A `Merge pull request #N` commit in the range is matched to its PR by number. All commits between it and the previous merge commit belong to that PR group.

**Strategy C — Remote branch tip match**  
`git branch -r | grep origin/feat/...` — if the tip SHA of a remote branch appears in the range, all commits on that branch (back to where it diverged from main) belong to that group.

**Strategy D — Conventional commit scope clustering**  
When A/B/C all fail, group contiguous commits sharing the same scope tag (`feat(causality)`, `feat(merkle)`) into a named capability group. Do NOT group non-contiguous same-scope commits — separate instances of the same scope are separate capabilities.

**Strategy E — Flat compaction (no context)**  
No grouping information available. Use KEEP commit message as heading (existing behaviour).

### False grouping guard

Only group commits if they are **contiguous** in the range (no intervening commits from a different scope or branch breaking the cluster). Non-contiguous commits with the same scope stay as separate groups even if they conceptually belong to the same feature — the history tells a different story.

### Output formats

**Compaction format** (all commits present, PR/branch context provides grouping):

```markdown
### PR #47 — feat(causality): findCausedBy — causal chain traversal (2026-04-18) [MDPROCTOR]

- ✅ `3717757` feat(causality): findCausedBy — SPI + JPA + 6 @QuarkusTest IT tests
- 🔽 `26fe313` docs: design spec — causality query API *(methodology — pre-implementation)*
- ✅ `4bc27ae` docs: update causality spec — correlationId + causedByEntryId to core
- 🔽 `a9a5754` docs: revise causality plan — no migration ceremony, 3 tasks *(methodology)*

> Result: 2 commits (2 absorbed)
```

**Reconstruction format** (squash-merged, recovering original branch commits):

```markdown
### PR #38 — refactor(api): rename DispatchRule → Binding (2026-04-14) [MDPROCTOR]

**Branch:** `feat/rename-binding-casedefinition`

| Original commit | Action | Curated result |
|----------------|--------|----------------|
| `2ca7bfb` refactor(api): rename DispatchRule → Binding | ✅ KEEP | `refactor(api): rename DispatchRule → Binding — unified with schema rename` |
| `5ac72ea` refactor(schema): rename CaseHubDefinition.yaml | 🔀 MERGE ↑ | *(unified — same rename scope)* |
| `441213d` chore: remove .claude/ from tracking | 🔽 SQUASH ↑ | *(absorbed — < 5 lines, no issue ref)* |

> **Result:** 1 commit.
```

**Curated result message seeding**  
For reconstruction format, seed the curated message from the PR title (subject to conventional commit enforcement and scope drift check). The user confirms or edits before it is applied.

### Graceful degradation chain

```
Strategy A (SHA match) 
  → Strategy B (merge commit)
    → Strategy C (branch tip)
      → Strategy D (scope clustering)
        → Strategy E (flat — KEEP message as heading)
```

Each level falls through automatically if no match is found. The user sees the best available output; the degradation is invisible.

---

## Gap 3 — Branch-scoped operation as first-class use case

### Problem

The "When to Use" section mentions explicit ranges but does not call out branch-scoped operation as the primary reconstruction workflow. For the engine reconstruction — the most complex planned use — this is the critical path.

### Required changes to SKILL.md "When to Use"

Add an explicit entry:

```
- **Full branch compaction / reconstruction:** compact an entire feature branch before
  merging, or reconstruct a squash-merged branch for review.
  Range syntax: `upstream/main..feat/some-feature` or `origin/main..HEAD`.
  This is the primary use case for reconstruction work — /git-squash handles the
  full range; do not use ad-hoc git commands outside the skill.
```

Also add a note at the end of the section:

```
**git-squash is the single entrypoint for all compaction.** Do not reach for
`git reset --soft HEAD~1 && git commit --amend` or `git rebase -i` directly —
these are internal implementation details. All compaction, from a single-commit
cleanup to a full reconstruction, goes through /git-squash.
```

---

## Gap 4 — workspace-init and init skills do not write Project Artifacts

### Problem

The `## Project Artifacts` section was added to `update-claude-md/starter-templates.md` (done), but `workspace-init` and `init` skills still do not populate it when creating CLAUDE.md. Skills like git-squash read this section at runtime — if it's absent, the git-squash Q&A has to ask the user instead, adding friction on every first run.

### Required changes

**`workspace-init/SKILL.md`**  
During CLAUDE.md generation (the step that writes the project CLAUDE.md), add a question to the Q&A that asks which paths are project artifacts. Use the routing table the skill already builds (what stays in the project repo vs what goes to the workspace) as the source of truth for the answer.

The workspace routing table already knows:
- Blog entries → workspace (or external via blog-routing.yaml)  
- HANDOFF.md → workspace  
- ADRs → workspace or project (user-configured)  
- DESIGN.md / docs/ → project  
- CLAUDE.md → project  

Write the inverse of "goes to workspace" into `## Project Artifacts` in the project CLAUDE.md.

**`init/SKILL.md`** (if it exists and generates CLAUDE.md)  
Same: during CLAUDE.md generation, populate `## Project Artifacts` with sensible defaults (`docs/adr/`, `CLAUDE.md`, any declared design docs). Ask if unsure.

### Priority

Lower than Gaps 1–3. The git-squash Q&A fallback covers the missing-section case adequately for now. Implement after the compaction workflow is proven on the casehubio repos.

---

## Implementation order

1. **Gap 1** (plan format) — implement now; needed for improved ledger report
2. **Gap 3** (When to Use, single entrypoint note) — small; do alongside Gap 1
3. **Gap 2** (PR/branch pre-pass) — implement before engine reconstruction; requires testing against ledger and work first
4. **Gap 4** (workspace-init/init) — separate session; lower urgency

---

## Open questions

- **Gap 2, reconstruction format:** Should the three-column table include line counts per commit? The brief doesn't mention it but it was useful context in classification. Decision: omit from reconstruction table (too wide); available on request.
- **Gap 1, markdown file path:** `docs/superpowers/specs/` is the default but some repos (engine) may route specs to the workspace. Should the skill check `## Artifact Locations` in CLAUDE.md for the specs path? Likely yes — add this to the Gap 1 implementation.
- **Gap 2, scope clustering threshold:** How many commits in a contiguous same-scope cluster before it becomes a named group? Suggested: 2+ commits. A single isolated `feat(causality)` commit doesn't need a group heading.
