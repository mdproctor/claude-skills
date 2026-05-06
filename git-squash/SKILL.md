---
name: git-squash
description: >
  Use when the commit history contains noise — fixup commits, revert
  chains, docs wording chores, tiny cleanups — that obscures meaningful
  history. Also triggered when the pre-push hook flags squash candidates,
  or invoked on demand via /git-squash on any commit range.
---

# Git Squash

Applies the commit squash policy to a range of commits. Eliminates noise
(tiny fixups, revert chains, formatting commits) while preserving meaningful
history. Author approves every change — nothing is applied automatically.

The full policy is in `squash-policy.md` alongside this skill.

**Two modes:**
- **On-demand** (`/git-squash`): full workflow with branch isolation, filter-repo,
  intelligent classification, review gate, and branch swap. Can handle pushed commits safely.
- **Pre-push hook**: in-place squash on unpushed commits only. Fast, no branch
  creation, no force-push. Never runs filter-repo.

---

## When to Use

- **Before pushing:** run on unpushed commits to clean history before it's shared.
  The pre-push hook operates on unpushed commits only — in-place, no force-push needed.
- **On demand:** clean up any commit range at any point (`/git-squash`).
  All work happens on an isolated working branch — pushed commits can be included safely.
- **After the hook fires:** the pre-push hook detected squash candidates; run this to resolve them.
- **Pre-PR review:** branch is pushed but no PR exists yet. On-demand mode handles
  this with branch isolation and a review gate before the swap.

---

## On-Demand Workflow

### Step 0 — Create working branch

Before any destructive operation, create an isolated working branch:

```bash
ORIG_BRANCH=$(git branch --show-current)
WORK_BRANCH="squash/wip-${ORIG_BRANCH}-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$WORK_BRANCH"
```

Record both names — needed for the swap in Step 8. All filter-repo and rebase
operations run on `$WORK_BRANCH`. The original branch is untouched until the
author explicitly approves the swap.

---

### Step 1 — Filter-repo Q&A (on-demand only)

**Never run filter-repo from the pre-push hook or any automatic trigger.**
**Always runs on the working branch, never on the original.**

#### 1a — Resolve project artifacts

Check CLAUDE.md for a `## Project Artifacts` section:
```bash
grep -A 50 "^## Project Artifacts" CLAUDE.md 2>/dev/null
```

**If `## Project Artifacts` exists:** paths listed there are project content — never
filter them by default.

**If `## Project Artifacts` is absent:** ask the user about common workspace artifact
paths found in the commit range, then offer to write the section:

```
CLAUDE.md has no ## Project Artifacts section.

Which of these paths in the commit range are project content (not workspace noise)?

  [x] docs/adr/       — architecture decision records
  [x] CLAUDE.md       — project conventions (build, test, naming)
  [ ] HANDOFF.md      — session handovers (workspace noise by default)
  [ ] docs/_posts/    — blog entries (workspace noise unless type: blog)

Type numbers to toggle, "go" to proceed:
```

After the user responds, offer:
```
Add a ## Project Artifacts section to CLAUDE.md with these selections? (YES / n)
```

If YES, write the section to the original branch's CLAUDE.md (not the working branch).

#### 1b — Scan and filter

Scan the commit range for files that could be filtered:
```bash
git log --name-only --format="" <range> | sort -u
```

**Important limitation:** `git filter-repo` operates on whole file paths only — it
cannot strip sections within a file. Only offer filtering for whole files. For
CLAUDE.md commits, the squash pass (Step 3) handles them as SQUASH candidates instead.

Filter only paths that are NOT in Project Artifacts and match known whole-file
workspace patterns (HANDOFF.md, docs/_posts/ entries in non-blog repos, etc.).

If filterable paths are found, present a checkbox Q&A:

```
Filter workspace artifact files from history before compacting?

Detected in commit range:
[x] HANDOFF.md (session handovers — 3 commits)
[ ] docs/_posts/*.md — deselected: declared as Project Artifact in CLAUDE.md

Type numbers to toggle, "go" to proceed, or "skip" to skip filtering:
```

On **"go":** run filter-repo on the working branch only:
```bash
git filter-repo --path <path> --invert-paths --prune-empty always \
  --refs "refs/heads/$WORK_BRANCH"
```

Show the Phase 0 report:
```
Phase 0 — filter-repo
  Stripped paths: HANDOFF.md (3 commits)
  Commits pruned after strip (became empty): 3
  Commits remaining for compaction: 11
```

On **"skip":** proceed directly to Step 2.

---

### Step 2 — Resolve commit range

**Resolve AFTER filter-repo completes** — filter-repo rewrites all SHAs.

```bash
git log --oneline @{u}..HEAD 2>/dev/null || git log --oneline origin/HEAD..HEAD 2>/dev/null
```

If no upstream is configured, ask for the base point. Record the resolved range.

**Check for pushed commits in range:**
```bash
git log --oneline <range> | while read sha rest; do
  git branch -r --contains "$sha" 2>/dev/null | grep -v HEAD | head -1
done
```

If pushed commits are in range, warn and require YES before continuing.

---

### Step 3 — Classify commits

Read `squash-policy.md`. Run all analysis passes in order, then synthesise into a
final classification for each commit.

#### 3a — Gather raw data

For every commit in the range, collect:
```bash
# Message, author, timestamp, file set
git log --format="%H %ae %ai %s" <range>
git show --name-only --format="" <sha>   # per commit
git show --stat <sha>                    # line counts for small-commit detection
```

#### 3b — Detect conventional commits

Scan recent history (last 20 commits outside the range) to determine if the repo
uses conventional commits:
```bash
git log --oneline -20 @{u} | grep -cE "^[a-f0-9]+ (feat|fix|chore|docs|test|refactor|perf|style)[:(]"
```
If ≥ 80% match, record `CONVENTIONAL=true` — used in Step 6 to enforce format
on MERGE messages.

#### 3c — PR/issue body integration

If `gh` is available, fetch the PR for the current branch:
```bash
gh pr view --json body,title,number,baseRefName 2>/dev/null
```

If a PR exists:
- **Protected-branch merge target** (`main`, `master`, `release/*`): note this for
  merge commit classification (Step 3d)
- **Commits mentioned by SHA** in the PR description → KEEP regardless of size
- **PR task list** where each task maps 1:1 to a commit → treat all as KEEP
  (they document the work breakdown; squashing loses the traceability)
- **PR description says "fix typo in X"** → corresponding commit is SQUASH regardless
  of message pattern

#### 3d — Pattern classification

For each commit, apply the KEEP / SQUASH / MERGE / DROP rules from `squash-policy.md`
in priority order. Pay particular attention to the refined merge commit rules (rows
2a–2e): inspect branch names in the merge message before classifying.

Only classify a commit as DROP if `git show --stat` confirms **zero files changed**.

#### 3e — Temporal scrutiny

Extract timestamps and identify commits from the same author within 30-minute windows:
```bash
git log --format="%H %ae %ai" <range>
```

Temporal proximity is not a merge signal — two commits 10 minutes apart may address
completely different concerns. It is a scrutiny signal: surface them together in the
plan and ask the author to confirm they are genuinely distinct before leaving them as
separate KEEP commits.

Do not reclassify or merge automatically. Show the cluster as a question:
```
⏱ Close together — 3 commits from alice@example.com within 18 minutes:
   abc1234  feat(api): add UserRepository SPI
   def5678  docs: update CLAUDE.md for new conventions
   ghi9012  fix(test): correct assertion timing
   Are these genuinely distinct? (YES to keep separate / n to review for merge)
```

#### 3f — File-overlap MERGE detection

For each pair of KEEP commits in the range, compute Jaccard similarity of their
file sets:
```
similarity = |files(A) ∩ files(B)| / |files(A) ∪ files(B)|
```

If similarity ≥ 0.7, flag as a MERGE candidate — both commits are likely addressing
the same capability regardless of message wording. Surface as:
```
📁 File-overlap MERGE candidate — these commits share 4/5 files:
   abc1234  feat(api): add UserRepository SPI
   def5678  feat(api): wire UserRepository into ServiceLocator
   Overlap: UserRepository.java, UserRepositoryImpl.java, UserRepositoryTest.java, ...
```

Do not merge commits from different features/scopes just because files overlap.
Confirm that the overlap makes semantic sense (same module, same capability).

#### 3g — Cross-author check

For any KEEP or MERGE candidate that would be absorbed into a commit from a different
author — reclassify as KEEP and flag it. Cross-author squash is only permitted when
the absorbed commit is already classified SQUASH (formatting, CI, spelling).

#### 3h — Cherry-pick detection

For commits classified SQUASH or MERGE, check if any appear on other branches:
```bash
# Get patch-id for the commit
git show <sha> | git patch-id --stable

# Compare against all other branches
git log --all --format="%H" -- | \
  grep -v $(git rev-list <range>) | \
  xargs -I{} sh -c 'git show {} | git patch-id --stable' 2>/dev/null
```

If a commit being squashed has a matching patch-id on another branch, warn:
```
⚠️  Cherry-pick detected: abc1234 appears on branch release/2.1
    Squashing this commit rewrites its identity — the cherry-pick will conflict on
    future merges. Confirm? (YES to proceed, n to keep standalone)
```

---

### Step 4 — Show summary

```
Commit squash analysis — <N> commits in range

  Already clean (KEEP, no action): <n>
  SQUASH candidates: <n>
    Docs follow-on (Javadoc/wording):  <n>
    Formatting/cleanup (chore):        <n>
    Revert chains:                     <n>
    Small fixups (< 5 lines):          <n>
    Test hardening:                    <n>
  MERGE candidates: <n>
    Same scope/feature pairs:          <n>
    File-overlap detected:             <n>
    Temporal clusters:                 <n>
  DROP (truly empty, zero files): <n>

  Result: <N> commits → <M> commits — <absorbed> absorbed (no content lost), <dropped> dropped
```

**Large-range handling (> 50 commits):** skip straight to a group view:

```
<N> commits is a large range. How would you like to review?

  group   — show one capability group at a time (recommended)
  bulk    — show summary only; accept/refuse by pattern category
  full    — show the complete plan (may be very long)
```

For **"group"**: present one squash group at a time, get YES/n per group, then move
to the next. Show progress: "Group 3 of 12."

For **"bulk"**: list pattern categories with counts and let the user accept/refuse
each category en masse before reviewing individual exceptions.

For **"full"** or for ranges ≤ 50 commits, continue to Step 5a.

---

### Step 5a — Full plan (if user says YES or range ≤ 50)

#### Already-clean callout

```
Already clean — no action needed (<n> commits):
  <sha>  <message>
  ...
```

#### Action groups

One group per KEEP target. Indented layout shows what folds into what.

**KEEP with absorbed commits:**
```
✅ <sha> <message>   →  [absorbs: <what was squashed in>]
   🔽 <sha> <absorbed message>  → absorbed *(reason)*
```

**MERGE:**
```
🔀 MERGE — <reason>:
   ← <sha> <original message 1>
   ← <sha> <original message 2>
   → <proposed unified message>
   Richer than either alone? <YES — what combining adds>
```

**File-overlap MERGE hint (when not yet classified as MERGE):**
```
📁 <sha> <message>   [shares files with abc1234 — possible MERGE?]
```

**Temporal scrutiny annotation:**
```
⏱ <sha> <message>   [12 min after abc1234 — confirm this is genuinely distinct]
```

**DROP:**
```
❌ <sha> <message>  → dropped (zero file changes confirmed)
```

**Cross-author retention:**
```
✅ <sha> <message>  → kept standalone
   ⚠️  cross-author: committed by <other-author> — not squashed (contains design content)
```

**AFTER block:**
```
AFTER — what git log will show:
────────────────────────────────────────────────────────────────
<sha>  <message>
<sha>  <message>
```

**Impact line:**
```
Result: <N> commits → <M> commits — <absorbed> absorbed (no content lost), <dropped> dropped
```

Then ask:
```
Refuse any group? Enter group numbers or commit SHAs,
"all" to accept all, or "none" to refuse all:
```

Show confirmation and wait for final YES.

---

### Step 5b — Skip plan (if user says n)

```
Apply all <N> squash/merge candidates? (YES / n / custom)
```

---

### Step 6 — Execute

**If nothing to do:** confirm and exit. Offer to delete the working branch.

**Single-commit squash** (fast path — only when squashing HEAD~1 into HEAD):
```bash
git reset --soft HEAD~1 && git commit --amend --no-edit
```

**Multi-commit squashes:** write the todo and execute non-interactively:
```bash
PLAN=$(mktemp)
cat > "$PLAN" <<'PLAN_EOF'
pick abc1234 feat(api): add UserRepository SPI
squash ghi9012 docs(api): align findByKey Javadoc wording
pick jkl0123 feat(engine): add CaseRepository
PLAN_EOF

GIT_SEQUENCE_EDITOR="cp $PLAN" git rebase -i <base-sha>
rm -f "$PLAN"
```

**MERGE messages — conventional commit enforcement:**

For each MERGE operation, before finalising the unified message:

1. **Format check** (if `CONVENTIONAL=true`): the proposed message must follow
   `type(scope): description`. If it doesn't, suggest a corrected form before
   showing it to the user.

2. **Scope drift check**: if the two commits being merged have different scopes
   (`feat(auth)` and `feat(payment)`), flag it:
   ```
   ⚠️  Scope drift: merging (auth) and (payment) — different concerns.
       Merging may violate single-responsibility.
       Recommend KEEP instead? (YES / n to merge anyway)
   ```

3. Apply the message via:
   ```bash
   git commit --amend -m "<unified message>"
   ```

Show the result in group format with real post-rebase SHAs.

---

### Step 7 — Review gate

```
Working branch: squash/wip-<branch>-<timestamp>

Compare against original:
  git diff <orig-branch>...squash/wip-<branch>-<timestamp>
  git log --oneline <orig-branch>..squash/wip-<branch>-<timestamp>

Push working branch for review by others? (YES / n)
  YES — git push -u origin squash/wip-<branch>-<timestamp>

Ready to swap? (YES / n / push-first)
```

Wait for explicit YES before proceeding to Step 8.

---

### Step 8 — Swap branches

```bash
BACKUP="backup/pre-squash-${ORIG_BRANCH}-$(date +%Y%m%d)"
git branch -m "$ORIG_BRANCH" "$BACKUP"
git branch -m "$WORK_BRANCH" "$ORIG_BRANCH"
git branch --set-upstream-to="origin/$ORIG_BRANCH" "$ORIG_BRANCH" 2>/dev/null || true
git push --force-with-lease origin "$ORIG_BRANCH"
```

Confirm:
```
✅ Swap complete.
  Active branch:  <orig-branch> (squashed history)
  Backup branch:  backup/pre-squash-<orig-branch>-<YYYYMMDD> (original history)

To push backup for off-machine safety:
  git push origin backup/pre-squash-<orig-branch>-<YYYYMMDD>

To undo entirely:
  git checkout backup/pre-squash-<orig-branch>-<YYYYMMDD>
  git branch -m <orig-branch> squash/wip-<orig-branch>-<timestamp>
  git branch -m backup/pre-squash-<orig-branch>-<YYYYMMDD> <orig-branch>
  git push --force-with-lease origin <orig-branch>
```

---

### Step 9 — Backup cleanup (offered on future runs)

On any subsequent `/git-squash` invocation, check for old backup branches:
```bash
git branch | grep "backup/pre-squash-"
```

If any exist, surface them before starting new work:
```
Old squash backups found:
  backup/pre-squash-main-20260415    (21 days ago)
  backup/pre-squash-feat-auth-20260502    (4 days ago)

Delete any? Enter branch names, "all", or "none" to skip:
```

Only delete on explicit user confirmation.

---

## Pre-Push Workflow (fast — unpushed commits only)

When invoked in response to the pre-push hook, skip Steps 0, 1, 7, 8, and 9.
In-place squash is safe — history hasn't been shared yet.

1. **Step 2:** Resolve unpushed range (`@{u}..HEAD`)
2. **Step 3:** Classify per policy (run all analysis passes, including temporal
   grouping, file-overlap, and conventional commit detection — skip cherry-pick
   detection and PR integration as they add friction to the fast path)
3. **Step 4:** Show summary
4. **Step 5:** Show plan and get approval
5. **Step 6:** Execute in-place
6. **Push:** `git push` (no force needed)

---

## Installing the pre-push hook

The pre-push hook checks unpushed commits for obvious squash candidates and exits 1
if found, prompting the user to run `/git-squash` first. It never runs filter-repo.

```bash
HOOK_SRC="$HOME/.claude/skills/git-squash/hooks/pre-push"
HOOK_DEST="$(git rev-parse --git-dir)/hooks/pre-push"

if [ -f "$HOOK_DEST" ]; then
  echo "⚠️  pre-push hook already exists at $HOOK_DEST — skipping."
else
  cp "$HOOK_SRC" "$HOOK_DEST"
  chmod +x "$HOOK_DEST"
  echo "✅ pre-push hook installed."
fi
```

Bypass with `git push --no-verify` after manually confirming history is clean.

---

## Common Pitfalls

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Resolving commit range before filter-repo | filter-repo rewrites all SHAs; range is stale | Always resolve range after Phase 0 completes |
| Running filter-repo without `--refs` | Rewrites entire repo history, not just working branch | Always pass `--refs refs/heads/$WORK_BRANCH` |
| Claiming to filter CLAUDE.md sections | filter-repo operates on whole file paths only | Offer whole-file filtering only; handle CLAUDE.md commits via squash pass |
| Swapping branches without review gate | No chance for second opinion on pushed history | Always show review gate before swap |
| Dropping commits with file changes | Silent data loss | Use Phase 1 filter-repo to strip files first; only drop truly empty commits |
| Squashing a KEEP/MERGE commit from a different author | Rewrites attribution | Cross-author squash only for SQUASH-classified noise |
| Using fast-path reset for non-HEAD squash pairs | Amends the wrong commit | Fast path only when squash pair is HEAD←HEAD~1 |
| Running filter-repo from pre-push hook | Destructive rewrite must be deliberate | filter-repo on-demand only, never automatic |
| Skipping Project Artifacts check | May filter project history | Always resolve Project Artifacts before scanning |
| Using `git rebase -i` without GIT_SEQUENCE_EDITOR | Opens interactive editor; blocks | Always use `GIT_SEQUENCE_EDITOR="cp $PLAN"` |
| Merging commits with different scopes without warning | Violates single-responsibility | Scope drift check on all MERGE operations |
| Squashing commits cherry-picked to other branches | Future merges will conflict | Cherry-pick detection before squashing |
| Using `--force` instead of `--force-with-lease` | Overwrites concurrent pushes | Always use `--force-with-lease` |
| Squashing commits with issue references | Loses traceability | Issue references are always KEEP — see policy |

---

## Skill Chaining

**Invoked by:** User directly via `/git-squash`; pre-push hook when squash
candidates detected

**Reads:** `~/.claude/skills/git-squash/squash-policy.md` — the classification rules

**Does not invoke anything** — standalone analysis and rebase skill
