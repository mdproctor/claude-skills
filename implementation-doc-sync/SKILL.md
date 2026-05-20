---
name: implementation-doc-sync
description: >
  Use when documentation needs syncing — user says "sync docs", "update docs",
  "doc sweep", or invoked from a prompt snippet at session end. Scoped to what
  changed this session only, not a full project sweep. NOT a design journal
  update (java-git-commit handles that).
---

# Implementation Doc Sync

Answer the question: **given what changed this session, which docs need to catch up?**

Scope is intentionally narrow — only docs that cover the components, capabilities,
or conventions that were modified. Sweeping unrelated docs wastes time and creates
noise.

---

## Step 1 — Establish Session Scope

Identify what changed. Use git and conversation context — do not guess.

```bash
# What repos have uncommitted or recently committed changes?
git log --oneline --since="8 hours ago"
git diff --name-only HEAD~5..HEAD 2>/dev/null | head -30
```

From this, extract:
- **Which repos** were touched (ledger, work, engine, etc.)
- **Which components** changed (specific modules, SPIs, APIs, protocols)
- **What kind of change** — new capability, rename, SPI change, protocol addition,
  dependency change, architecture decision

Store this as the **session scope**. Everything below is filtered through it.

---

## Step 2 — Map Changes to Docs

Use this mapping to identify which docs are in scope. Only include docs that
directly cover something in the session scope.

| Change type | Docs to check |
|-------------|--------------|
| New capability or feature | `docs/PLATFORM.md` → Capability Ownership table |
| New or changed cross-repo dependency | `docs/PLATFORM.md` → Cross-Repo Dependency Map |
| Repo renamed / restructured | `docs/PLATFORM.md` → Repository Map |
| Per-repo deep dive affected | `docs/repos/casehub-{repo}.md` |
| Application tier change | `docs/APPLICATIONS.md` |
| New platform protocol | `docs/protocols/INDEX.md` + the protocol file itself |
| Existing protocol updated | The protocol file + any files that reference it |
| Convention or workflow change | `CLAUDE.md` (invoke `update-claude-md`) |
| Architecture decision | `adr/` (invoke `adr` if not yet recorded) |
| Design journal (epic branch) | `design/JOURNAL.md` (invoke `java-update-design`) |
| Maven coordinate change | `docs/protocols/maven-coordinate-standard.md` if convention changed |
| Cross-repo artifact rename | `docs/PLATFORM.md` → Cross-Repo Dependency Map |

If a doc type is not in this table and not obviously related to the session
scope, skip it.

---

## Step 3 — Check Each In-Scope Doc

For each doc identified in Step 2, run this checklist:

### Drift
- Does the doc still accurately describe the current code/structure?
- Are any statements now false because of this session's changes?
- Are examples or code snippets still valid?

### Cross-references
- Do all links to other docs, files, or sections resolve?
- Do referenced file paths still exist (e.g. after folder renames)?
- Do referenced artifactIds match the current coordinates?

### Staleness
- Is there content that was accurate before this session but no longer is?
- Are version numbers, module names, or artifact names outdated?

### Gaps
- Is there something that changed this session that the doc should cover but doesn't?
- Was a new capability added that belongs in the Capability Ownership table?
- Was a new protocol created that isn't in INDEX.md?
- Was a new cross-repo dependency introduced that isn't in the Dependency Map?

---

## Step 4 — Fix and Report

For each issue found:

1. Fix it directly — do not just flag it
2. Use IntelliJ `replace_text_in_file` for targeted edits; Edit tool for structured
   doc sections
3. After all fixes, report a brief summary:

```
Doc sync complete — {n} docs checked, {n} updated:
- docs/PLATFORM.md: updated Dependency Map (casehub-connectors → casehub-connectors-core)
- docs/protocols/INDEX.md: added artifact-rename-propagation.md entry
- docs/repos/casehub-work.md: updated notifications module description
- (no changes needed): docs/APPLICATIONS.md, CLAUDE.md
```

If a gap requires more than a doc update (e.g. a missing ADR for a significant
decision), flag it: *"ADR not yet recorded for X — invoke `adr` to capture it."*
Do not silently skip it.

---

## Step 5 — Commit Doc Changes

If any docs were updated, commit them separately from code changes:

```bash
git add docs/
git commit -m "docs: sync documentation to session changes

[brief description of what was updated and why]

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>"
```

Docs and code in separate commits keeps the history readable.

---

## What This Skill Does NOT Do

- **Does not** check docs unrelated to the session scope — that is `project-health`
- **Does not** update the design journal — that is `java-update-design` (via `java-git-commit`)
- **Does not** update CLAUDE.md for convention changes — that is `update-claude-md`
  (but it will invoke those skills if the session scope triggers them)
- **Does not** write ADRs — it will flag the gap and suggest invoking `adr`
- **Does not** run tests or check code correctness — that is `superpowers:requesting-code-review`

---

## Skill Chaining

**Invoked by:** prompt snippet at end of implementation session; user says
"sync docs", "update docs", "doc sweep"

**Invokes when triggered by session scope:**
- `update-claude-md` — if conventions or workflows changed
- `java-update-design` — if on an epic branch and design decisions were made
- suggests `adr` — if a significant architectural decision lacks a record

**Complements:**
- `project-health` — full project correctness check (not session-scoped)
- `java-git-commit` — chains to `java-update-design` for design journal
- `handover` — runs after this skill; the handover references updated docs
