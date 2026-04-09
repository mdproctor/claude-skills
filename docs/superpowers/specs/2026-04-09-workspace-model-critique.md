# Workspace Model — Critical Analysis

**Date:** 2026-04-09
**Related spec:** `2026-04-09-workspace-model-design.md`
**Status:** Pre-implementation review — unresolved concerns, do not implement until addressed

---

## Summary

The design solves "methodology artifacts pollute the project repo" by making the
workspace the primary Claude working directory. This fights against Claude Code's
fundamental assumption that CWD is the project. The result is friction at every
layer: git, CLAUDE.md loading, skills, and session startup.

---

## Problem 1: The "Always Open In Workspace" Invariant Is Unenforceable

The entire model collapses the moment anyone opens Claude in the project directory
instead of the workspace. That will happen constantly:

- **IDE integration fights you**: VS Code and JetBrains Claude extensions launch
  in the project directory. You'd have to consciously override this every session.
- **Muscle memory fights you**: Developers `cd project && claude`. That's years
  of habit the model requires you to break permanently.
- **No enforcement**: Nothing stops you. No hook, no warning, no guard. Open in
  the wrong place once, write a handover, and artifacts are now in two locations.

One person on a team does this wrong once — everything is inconsistent.

---

## Problem 2: The Project's CLAUDE.md Is No Longer Auto-Loaded

**This is the biggest issue and the design doesn't address it.**

Claude Code auto-loads CLAUDE.md from the working directory. If Claude opens in
the workspace, it loads the **workspace** CLAUDE.md — not the project's. The
project CLAUDE.md contains:

- Project type (`type: java`, `type: skills`) — skills route on this
- Build commands (`mvn compile`, `python3 -m pytest`)
- Commit conventions, work tracking configuration
- All project-specific behavioural rules

All of it invisible to Claude unless explicitly loaded. Every skill that reads
project type breaks silently.

**Options, all bad:**
- Duplicate project type info in workspace CLAUDE.md — two copies that drift
- Reference the project CLAUDE.md from the workspace one — no `@import`
  mechanism exists; Claude would have to explicitly read it every session
- Load both manually — more per-session overhead

---

## Problem 3: `add-dir` Is Manual, Every Session

`add-dir` does not persist across sessions. Every single session:

1. Open Claude in workspace
2. Manually type `add-dir /path/to/project`
3. Then start working

CLAUDE.md provides context, it cannot issue commands. A session-start hook could
theoretically automate this, but that's complex additional infrastructure to set
up and maintain per project. This is recurring friction on every session for the
lifetime of the project.

---

## Problem 4: Every Git Command In Every Skill Breaks

Skills currently do `git log`, `git status`, `git add`, `git commit` — all
CWD-relative. If CWD is the workspace, those operate on the workspace git repo,
not the project.

To commit code to the project, every skill now needs something like:

```bash
PROJECT=$(grep "Project repo:" CLAUDE.md | cut -d' ' -f3)
git -C "$PROJECT" add src/Foo.java
git -C "$PROJECT" commit -m "feat: ..."
```

Instead of `git add && git commit`. Every skill, every git operation, permanently
more complex. Every skill also needs to know whether it's operating on the
workspace repo or the project repo — a distinction that currently does not exist
and would need to be threaded through all of them.

---

## Problem 5: Two Git Repos, Constant Cognitive Split

Currently: one repo, one `git log`, one history, one branch.

After: two repos. Every time something is unclear:
- Is the uncommitted change in the workspace or the project?
- Which `git log` do I look at for context?
- Which branch am I actually on in each repo?

The branch-mirror convention ("workspace branch mirrors project branch") is
purely a manual convention. Forget to switch the workspace branch once and
handovers and snapshots are on the wrong branch — silently, with no warning.

---

## Problem 6: The Design Conflates Two Separate Concerns

"Claude opens in the workspace" bundles together:

1. **Where methodology artifacts are stored** — the problem being solved
2. **Where Claude does its primary work** — not a problem that needed changing

These don't have to be the same thing. The original symlink approach kept them
separate: project is CWD, workspace accessible via `workspace/` symlink.

The discomfort with the symlink was: "what if someone opens Claude in the project
without the workspace context?" But that's the same discipline problem as "what
if someone opens Claude in the project instead of the workspace?" The invariant
you need to enforce is **identical in both models** — but the symlink model
doesn't break git, doesn't break CLAUDE.md auto-loading, and doesn't require
`add-dir` every session.

---

## Problem 7: Git Worktrees Are Not Addressed

Claude Code supports git worktrees for parallel development. If you create a
worktree on the project (`git worktree add ../project-feat ../feat`), do you
also create a matching worktree on the workspace? If not, the workspace is on
the wrong branch for that work. If yes, that's another manual step every time
you create a worktree — a convention with no enforcement and easy to forget.

---

## Problem 8: The Parent `~/claude/` Repo Cannot See Child History

Child project workspaces are their own git repos inside `~/claude/private/` and
`~/claude/public/`. A parent git repo at `~/claude/` would see those as untracked
nested repos. Git does not handle nested repos without submodules (explicitly
rejected). The parent repo would need to `.gitignore` all child workspace
directories.

Result: the parent's git history contains only cross-workspace artifacts. "Seeing
all projects" means filesystem access only — not git access. Weaker than it sounds.

---

## Problem 9: Quick Tasks Become Expensive

Currently: `cd project && claude "quick question"` — done in one step.

After: navigate to workspace → open Claude → `add-dir project` → ask question.
Three steps of overhead for the most common lightweight use case. The model is
designed for long epic-scoped sessions and penalises every quick interaction.

---

## The Underlying Flaw

The design solves "artifacts in the wrong place" by changing **where Claude
opens**. But Claude Code is built assuming the project is the working directory.
Everything — CLAUDE.md loading, git operations, skill path logic — assumes CWD
is the project. Fighting that assumption creates friction at every layer rather
than solving one problem cleanly.

---

## Alternative Worth Considering

Keep CWD as the project. Solve the artifact location problem at the **path
level**, not the working directory level:

- Project `CLAUDE.md` declares `workspace: ~/claude/private/cc-praxis/`
- Skills that write methodology artifacts check for this config and write there
  instead of `docs/`
- If no workspace configured, fall back to current `docs/` behaviour (backwards
  compatible)
- Claude reads project CLAUDE.md automatically — no broken assumptions
- Git operations stay simple — one repo is CWD
- `add-dir ~/claude/private/cc-praxis/` gives workspace read/write access when
  needed, or skills write directly to the absolute path
- The "always open in workspace" discipline disappears entirely — you just open
  in the project as normal

This solves the original problem (artifacts out of project repo) without
inverting the fundamental CWD assumption that everything else is built on.

**Trade-off:** Skills become path-aware (they check CLAUDE.md for workspace
config). But this is less complexity than making all git operations project-aware,
which the current design requires.

---

## Open Questions Before Proceeding

1. Does `add-dir` cause Claude to auto-load CLAUDE.md from the added directory?
   If yes, Problem 2 is partially mitigated.
2. Is there a session-start hook mechanism that could auto-run `add-dir`? If yes,
   Problem 3 is mitigated.
3. Can the "always open in workspace" discipline be enforced via a hook that
   detects when Claude opens in a project dir that has a known workspace and
   warns the user?
4. Is the alternative (workspace path in project CLAUDE.md, skills write there)
   sufficient to solve the original problem without the CWD inversion?
