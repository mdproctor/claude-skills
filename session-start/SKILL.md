---
name: session-start
description: >
  Use at the start of any development session — user says "session start",
  "start session", "begin session", or invokes /session-start. Reads the
  project's platform doc, runs the coherence protocol, confirms an issue
  exists, verifies IntelliJ MCPs, and establishes the full skill chain for
  the session. Works for any cc-praxis project; currently resolves the
  platform doc for casehubio automatically. NOT a health check (use
  project-health for that). NOT a handover (use handover for session end).
---

# Session Start

Bootstraps a development session with the right context, tools, and workflow
disciplines active from the first message.

---

## Step 1 — Locate the Platform Doc

The platform doc is the primary architectural reference for this project.
Resolve it in this order — use the first one found:

### 1a — Check CLAUDE.md for a declared path

```bash
grep -i "platform.doc\|primary.doc\|architecture.doc" CLAUDE.md 2>/dev/null | head -3
```

If CLAUDE.md declares a path (e.g. `platform-doc: docs/PLATFORM.md`), use it.

### 1b — Check conventional local paths

```bash
# Project-local
ls docs/PLATFORM.md 2>/dev/null
# Known platform locations (add new projects here)
ls ~/claude/casehub/parent/docs/PLATFORM.md 2>/dev/null   # casehubio
```

> **Extensibility note:** This hard-coded path list is the current limitation.
> Future improvement: projects declare their platform doc in CLAUDE.md under
> a `platform-doc:` key, removing the need for hard-coded paths entirely.
> When adding a new project, add its platform doc path to 1b above AND add
> a `platform-doc:` entry to that project's CLAUDE.md.

### 1c — No platform doc found

If neither 1a nor 1b resolves, continue without it — note it in the session
report but do not block. Not every project has a platform doc.

---

## Step 2 — Read the Platform Doc and Run the Coherence Protocol

If a platform doc was found, read it and run its embedded coherence protocol
(usually the first major section — "Platform Coherence Protocol" or similar).

The protocol typically asks:
- Does this already exist somewhere in the platform?
- Is this the right repo for the work?
- Does it create a consolidation opportunity?
- Is it consistent with platform patterns?
- Does it need a platform-level doc update?

Run through it now, against the work the user has described. If the user
hasn't described what they're working on yet, defer this step until they do
and surface it at that point.

---

## Step 3 — Confirm an Issue Exists

Every piece of work should be tracked against a GitHub issue.

```bash
gh issue list --state open --limit 10
```

If the user has described the work:
- Check if an open issue covers it
- If not: create one before proceeding (`gh issue create`)

If the user hasn't described the work yet, remind them at the point they do:
*"Before we start — confirm an open issue exists for this, or I'll create one."*

---

## Step 4 — Verify IntelliJ MCPs

Both IntelliJ MCP servers must be available for semantic operations.

Check by calling:
- `ide_index_status` (intellij-index) — confirms semantic index is ready
- `get_project_modules` (intellij) — confirms project structure is visible

If either is missing:
- **Report it explicitly:** "⚠️ IntelliJ MCP [name] is not available."
- **Do not proceed with semantic operations** (rename, move, find-references,
  diagnostics) that require the missing server
- Prompt the user: "Run `/mcp` to reconnect, then continue"

If both are available: report "✅ Both IntelliJ MCPs connected."

---

## Step 5 — Establish Tool Preferences

These apply for the entire session. State them once now so they're active:

| Operation | Use | Never use |
|-----------|-----|-----------|
| Rename symbol, file, package | `ide_refactor_rename` | sed, Edit, Find+Replace |
| Move file or source tree | `ide_move_file` | bash mv, git mv for Java files |
| Find all usages | `ide_find_references` | grep, search_text |
| Navigate to definition | `ide_find_definition` | grep, manual search |
| Build verification | `build_project` | mvn install (except for full-stack) |

---

## Step 6 — Establish the Session Skill Chain

State the active skill chain for this session. These apply from now until
the session ends:

**Before designing anything:**
→ invoke `superpowers:brainstorming` to explore the problem space first

**Before implementing:**
→ invoke `superpowers:test-driven-development` — red/green/refactor discipline

**For all Java work:**
→ invoke `java-dev` — loads `testing-principles` (unit/integration/E2E,
  happy path, correctness, robustness) and `ide-tooling`. Do not skip for
  small changes.

**Before committing:**
→ invoke `superpowers:requesting-code-review`

**After implementation, before ending the session:**
→ invoke `implementation-doc-sync` — scoped doc sweep for what changed

---

## Step 7 — Session Start Report

Output a brief confirmation:

```
Session start complete.

Platform doc: [path read, or "not found"]
Coherence protocol: [run / deferred until work is described / skipped]
Issue: [#N — title, or "none yet — will confirm when work is described"]
IntelliJ MCPs: [✅ both connected / ⚠️ missing: name]

Active skill chain:
  brainstorming → TDD → java-dev (+ testing-principles) → code-review → doc-sync

Ready.
```

---

## What This Skill Does NOT Do

- Does not run project health checks — use `project-health`
- Does not write a handover — use `handover` at session end
- Does not start an epic — use `epic`
- Does not replace `superpowers:using-superpowers` — that governs the
  meta-rule for skill invocation; this governs project-specific startup

---

## Skill Chaining

**Invoked by:** user at start of session ("session start", "begin session",
  or the prompt snippet trigger phrase)

**Establishes for the session:**
- `superpowers:brainstorming` — before design
- `superpowers:test-driven-development` — before implementation
- `java-dev` → `testing-principles` + `ide-tooling` — for Java work
- `superpowers:requesting-code-review` — before commit
- `implementation-doc-sync` — after implementation

**Complements:**
- `handover` — session end counterpart
- `project-health` — full correctness check (not session-scoped)
- `epic` — epic branch lifecycle
