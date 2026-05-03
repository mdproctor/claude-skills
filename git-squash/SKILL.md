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

---

## When to Use

- **Before pushing:** run on unpushed commits to clean history before it's shared
- **On demand:** clean up a branch at any point (`/git-squash`)
- **After the hook fires:** the pre-push hook detected squash candidates; run this to resolve them
- **Pre-PR review:** branch is pushed but no PR exists yet — final review before opening the PR;
  squashing requires `git push --force-with-lease` but is safe on a personal fork branch
- **On pushed commits:** specify a range explicitly for any other pushed-branch cleanup

---

## Step 1 — Determine the commit range

**Default (no argument):** unpushed commits on the current branch:
```bash
git log --oneline @{u}..HEAD 2>/dev/null || git log --oneline origin/HEAD..HEAD 2>/dev/null
```

If invoked with a range argument (e.g. `/git-squash HEAD~10..HEAD` or
`/git-squash abc123..def456`), use that range instead.

If no upstream is configured and no range given, ask:
> "No upstream found. Squash commits since which point?
> (e.g. `main`, `origin/main`, a SHA, or `HEAD~N`)"

Record the resolved range for all subsequent steps.

**Check for pushed commits in range:**
```bash
git log --oneline <range> | while read sha rest; do
  git branch -r --contains "$sha" 2>/dev/null | grep -v HEAD | head -1
done
```

If any commits in the range are already pushed, warn before proceeding:
> ⚠️ Some commits in this range are already on the remote. Squashing them
> requires a force-push. Continue? (YES / n)

---

## Step 2 — Classify commits per policy

Read `squash-policy.md` (in this skill directory at
`~/.claude/skills/git-squash/squash-policy.md`).

For each commit in the range, classify as:
- **KEEP** — carries standalone information; leave as-is
- **SQUASH** — artifact/noise; squash into preceding KEEP commit
- **MERGE** — two commits tell the same story more cleanly as one

For SQUASH and MERGE, identify:
- Which commit to squash into (the target)
- A proposed combined message (for MERGE only)

Apply the special-case rules: revert chains, test hardening runs, CI fixups.

---

## Step 3 — Show summary

Present a concise summary before showing any table:

```
Commit squash analysis — <N> commits in range

  SQUASH candidates (<count>):
    Docs follow-on (Javadoc/wording):  <n>
    Formatting/cleanup (chore):        <n>
    Revert chains:                     <n>
    Small fixups (< 5 lines):          <n>
    Test hardening:                    <n>

  MERGE candidates (<count>):
    Same scope/feature pairs:          <n>

  KEEP: <n> commits unchanged

View full comparison table? (YES / n)
```

---

## Step 4a — Full table (if user says YES)

Show the squash plan as a grouped diff table. Use emoji icons for immediate
scannability, inline `*(reason)*` annotations explaining WHY, a result column
showing the final message for each KEEP/MERGE commit, and dashed separators
between squash groups.

```
SQUASH PLAN — <N> commits → <M> commits

| SHA     | Message                                          | Action       | Result / Reason                                                        |
|---------|--------------------------------------------------|--------------|------------------------------------------------------------------------|
| abc1234 | feat(api): add UserRepository SPI                | ✅ KEEP      | `feat(api): add UserRepository SPI and wire into locator` (+ def5678) |
| def5678 | feat(api): wire UserRepository into ServiceLocator | 🔀 MERGE ↑  | *(unified — two halves of same capability)*                            |
| ghi9012 | docs(api): align findByKey Javadoc wording       | 🔽 SQUASH ↑  | *(absorbed — docs follow feature)*                                     |
|─────────|──────────────────────────────────────────────────|──────────────|───────────────────────────────────────────────────────────────────────|
| jkl0123 | feat(engine): add CaseRepository                 | ✅ KEEP      | `feat(engine): add CaseRepository` (unchanged)                         |
| mno4567 | chore: remove dead buildContext() call            | 🔽 SQUASH ↑  | *(absorbed — cleanup after feature)*                                   |
| pqr8901 | fix(test): correct assertion in same test        | 🔽 SQUASH ↑  | *(absorbed — same test being hardened)*                                |
|─────────|──────────────────────────────────────────────────|──────────────|───────────────────────────────────────────────────────────────────────|
| stu2345 | wip: halfway through blackboard refactor          | 🔽 SQUASH ↓  | *(absorbed — WIP save-state artifact)*                                 |
| vwx6789 | refactor(blackboard): extract PlanItemFactory    | ✅ KEEP      | `refactor(blackboard): extract PlanItemFactory` (unchanged)            |
|─────────|──────────────────────────────────────────────────|──────────────|───────────────────────────────────────────────────────────────────────|
| ci12345 | ci: trigger CI for PR                            | ❌ DROP      | *(dropped — mechanical CI artifact, no information value)*             |

> **Result:** <M> commits. <one-line narrative of what remains>.

AFTER
────────────────────────────────────────────────────────────────────────────
abc1234  feat(api): add UserRepository SPI and wire into ServiceLocator
jkl0123  feat(engine): add CaseRepository
vwx6789  refactor(blackboard): extract PlanItemFactory
```

**Icon guide:**
- ✅ `KEEP` — standalone commit, stays as-is (or reworded if MERGE target)
- 🔽 `SQUASH ↑` — absorbed into the preceding KEEP commit
- 🔽 `SQUASH ↓` — absorbed into the following KEEP commit (when WIP precedes its target)
- 🔀 `MERGE ↑` — merged into the preceding KEEP; unified message written
- ❌ `DROP` — discarded entirely; purely mechanical, zero information value

**Table rules:**
- Dashed separators between squash groups — one group per KEEP target
- Reason annotation on every non-KEEP row — always say WHY
- Result column on KEEP/MERGE rows shows the final committed message
- Result summary line gives a one-line narrative of what survives
- AFTER block shows the clean final list for easy review

Then ask:
```
Refuse any changes? Type SHAs or row numbers (e.g. "def5678 pqr8901"),
"all" to accept all, or "none" to refuse all:
```

Wait for response. Parse as refusals; everything else remains accepted.

Show confirmation:
```
  Accepted: <n> changes  (abc1234←def5678 merged, abc1234←ghi9012 squashed ...)
  Refused:  <n> kept standalone  (pqr8901)

Apply <n> changes? (YES / n)
```

---

## Step 4b — Skip table (if user says n)

```
Apply all <N> squash/merge candidates? (YES / n / custom)
  YES    — apply all candidates shown in the summary
  n      — abort, make no changes
  custom — show the full table to pick individually
```

---

## Step 5 — Execute

**If nothing to do (all refused or N=0):** confirm and exit.

**If applying squashes:**

Build the rebase instruction list. For each squash group:
```bash
# Example: squash commits 2 and 3 into commit 1
git rebase -i <base-sha>
# In the todo list:
#   pick  abc1234  feat(api): add UserRepository SPI
#   squash def5678  docs(api): align findByKey Javadoc wording
#   squash ghi9012  feat(api): wire UserRepository into locator
```

For **MERGE** operations, use `reword` on the target and `squash` the others,
then set the proposed combined message.

Execute the rebase non-interactively by writing the instruction file directly:
```bash
git rebase -i --autosquash <base-sha>
```

Or construct the todo file explicitly if autosquash doesn't cover the plan.

After rebase completes:
```bash
git log --oneline <original-range-equivalent>
```

Show the same table format used in the plan, now as a completed record:

```
SQUASH RESULT — <N> → <M> commits

| SHA     | Message                                          | Action      | Result / Reason                                                        |
|---------|--------------------------------------------------|-------------|------------------------------------------------------------------------|
| abc1234 | feat(api): add UserRepository SPI                | ✅ KEEP     | `feat(api): add UserRepository SPI and wire into locator` (+ def5678) |
| def5678 | feat(api): wire UserRepository into ServiceLocator | 🔀 MERGE ↑ | *(unified — two halves of same capability)*                            |
| ghi9012 | docs(api): align findByKey Javadoc wording       | 🔽 SQUASH ↑ | *(absorbed — docs follow feature)*                                     |
...

> **Result:** <M> commits. <one-line narrative>.

✅ <N> → <M> commits  (<squashed> squashed, <merged> merged, <dropped> dropped, <kept> unchanged)
```

---

## Step 6 — Push advice

If commits were originally pushed:
> "Force-push required. Run: `git push --force-with-lease`
> (--force-with-lease is safer than --force — it aborts if someone else pushed)"

If commits were unpushed:
> "Ready to push: `git push`"

---

## Installing the pre-push hook

The pre-push hook blocks obvious squash candidates before they reach the remote.
It performs a mechanical pattern check — not the full AI analysis — and exits 1
if patterns are found, prompting the user to run `/git-squash` first.

**Install:**
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

Run this once per repository. The hook stays in `.git/hooks/` (not committed).
Bypass with `git push --no-verify` after manually confirming the history is clean.

---

## Common Pitfalls

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Squashing pushed commits without warning | Rewrites shared history | Always warn and require explicit confirmation |
| Auto-applying without showing summary | Author loses visibility | Always show summary first |
| Using `--force` instead of `--force-with-lease` | Overwrites concurrent pushes | Always recommend `--force-with-lease` |
| Squashing commits with issue references | Loses traceability | Issue references are always KEEP — see policy |

---

## Skill Chaining

**Invoked by:** User directly via `/git-squash`; pre-push hook when squash
candidates detected

**Reads:** `~/.claude/skills/git-squash/squash-policy.md` — the classification rules

**Does not invoke anything** — standalone analysis and rebase skill
