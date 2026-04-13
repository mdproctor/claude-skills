# cc-praxis — Design

Architectural decisions for the cc-praxis skill collection. Conventions and workflow rules live in `CLAUDE.md`; skill documentation lives in `README.md`. This file captures the *why* behind structural choices.

---

## Workspace Model

Skills write methodology artifacts to a companion workspace directory (`~/claude/private/<project>/` or `public/`), not the project repo. `workspace-init` sets up the workspace on first use.

**Key decisions:**

| Decision | Chosen | Why | Alternatives Rejected |
|---|---|---|---|
| Workspace as CWD | Claude opens in workspace, project added via `add-dir` | All skills (including third-party superpowers) write to CWD universally | Project as CWD (third-party skills would write artifacts into project repo) |
| CLAUDE.md symlink | Symlink from project `CLAUDE.md` → workspace `CLAUDE.md` via `.git/info/exclude` | Works for any repo regardless of ownership; never touches tracked files | Tracked `.gitignore` entry (modifies upstream repo) |
| Single authoritative design doc | One `design/DESIGN.md` in workspace, no snapshot chain | Snapshots at different time periods create stale-content risk when merging; git is the archive | Snapshot-per-session accumulation (maintenance burden grows linearly) |

**Resolved:**
- Claude Code follows a CLAUDE.md symlink for session initialisation — confirmed via smoke test on cccli (2026-04-13).
- cc-praxis does not use the workspace model — its CLAUDE.md is a public artifact committed to the repo, not personal workflow config. Opening Claude in the project directory is the correct workflow.

---

## write-blog Architecture

The blog skill uses a four-layer architecture to separate universal craft rules from voice:

| Layer | File | Override? |
|---|---|---|
| 1. Universal craft rules | `write-blog/defaults/mandatory-rules.md` | No — binding for all authors |
| 2. CLAUDE.md audience inference | Project CLAUDE.md | Invocation-time only |
| 3. Voice | `write-blog/defaults/common-voice.md` or personal guide | Personal guide replaces common |
| 4. Invocation overrides | `/write-blog <args>` | This entry only |

**Key decisions:**

| Decision | Chosen | Why | Alternatives Rejected |
|---|---|---|---|
| Blog rules split into layers | mandatory-rules.md + common-voice.md + personal guide | Separation of concerns — non-negotiable craft vs voice defaults vs personal style | Single monolithic guide (caused enforcement gaps) |
| write-blog defaults/ directory | Bundled mandatory-rules.md and common-voice.md ship with skill | Any user gets baseline craft rules; personal guide is additive | All rules in SKILL.md (too large, not layered) |
| Blog filename convention | `YYYY-MM-DD-<initials>NN-title.md` (always initials + numbered) | Same-day same-author entries sort correctly; initials prevent cross-author collisions | Unnumbered (collision on same-day entries) |
| Blog directory | Configurable via `Blog directory:` in CLAUDE.md | Projects use different layouts (Jekyll `_posts/`, `docs/blog/`, etc.) | Hardcoded path |

**Mandatory rules (current):**
- I/we/Claude register system — deliberate, not default "we" for everything
- Factual accuracy — no inflated timeframes, counts, or difficulty
- No theatrical dramatisation — no heightened stakes, "the moment everything changed"
- No preamble; no trailing summary; no `**Next:**` template footer

---

## Issue Tracking Infrastructure

Work Tracking is enabled in cc-praxis CLAUDE.md and wired into all four commit skills.

**Key decisions:**

| Decision | Chosen | Why | Alternatives Rejected |
|---|---|---|---|
| Step 0b in all commit skills | Duplicate across java/blog/custom/skills/generic/git-commit | Each skill is independent; no inheritance mechanism | Single place in git-commit only (java repos never saw the prompt) |
| Release notes | `gh release create --generate-notes` | Auto-generates from closed issues; zero maintenance | Manual CHANGELOG.md |
| retro-issues.md retention | Permanent audit trail, never delete | Records the grouping rationale; GitHub issues record only outcomes | Delete after issue creation |

---

## Knowledge Garden

The `garden` skill was removed from cc-praxis and the entire knowledge garden system was migrated to the hortora project. The garden now lives at `~/.hortora/garden/` (via `HORTORA_GARDEN` env var; legacy symlink `~/claude/knowledge-garden/` preserved). The replacement skills — `forage` (session-time capture) and `harvest` (deduplication) — ship from hortora/soredium and are installed into `~/.claude/skills/` alongside cc-praxis skills.

Use `forage` for session-time capture and `harvest` for deduplication. The `garden` skill is gone.

---

## Design Backlog

No open design decisions at this time.
