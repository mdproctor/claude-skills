# project-refine — Design Document

**Status:** Design phase — not yet implemented as a skill
**Skill name (planned):** `project-refine`
**Slash command (planned):** `/project-refine`
**Companion skill:** [`project-health`](project-health.md) — correctness and compliance checks

This document tracks the design and scope of the `project-refine` skill. It is a working document — update it as the skill evolves.

---

## Purpose

Answers the question: **could the project be smaller, clearer, or better structured?**

A dedicated improvement session across documentation, code, and tests. It looks at things that already work and asks whether they could be better — restructured, deduplicated, consolidated, simplified. It never blocks work; findings are always opportunities, never failures.

It replaces:
- "look for ways to improve our docs structure"
- "find duplicated code we could abstract"
- "check if we can modularise or consolidate things"
- "do a bloat check on our codebase"
- periodic "tidying up" sessions

---

## Relationship with project-health

`project-refine` and [`project-health`](project-health.md) are companion skills designed to work together:

| | `project-health` | `project-refine` |
|--|-----------------|-----------------|
| **Question** | Is it correct? | Could it be better? |
| **Output** | CRITICAL / HIGH / MEDIUM / LOW findings | 🔴🟡🟢 bloat score opportunities |
| **Mindset** | Pass / fail | Improvement suggestions |
| **Runs at** | Every commit (subset), pre-release, on demand | Periodic sessions, on demand |
| **Blocks work?** | CRITICAL findings should block release | Never blocks — always advisory |

**The distinction between refinement notes in project-health and project-refine:**

Each category in `project-health` includes refinement questions specific to that category — "could `docs-sync` correctness be expressed more concisely?", "could `logic` workflows be simplified?". These belong in `project-health` because they are refinement considerations *about a specific correctness domain*.

`project-refine` covers improvement work that **cuts across domains** — docs structure is not a correctness concern, code deduplication is not a logic concern, test grouping is not a coverage concern. These need their own session with a different mindset.

**Using them together:**

```bash
# 1. Verify correctness first — fix anything CRITICAL or HIGH
/project-health --prerelease

# 2. Once health is green, look for improvement opportunities
/project-refine

# Or run both for a full pre-release review
/project-health --all
/project-refine
```

**Shared infrastructure:** both skills use the same document scanning scope (see [`project-health` § Document Scanning Scope](project-health.md#document-scanning-scope)) and the same CLAUDE.md configuration section. Running one does not duplicate work done by the other.

---

## Invocation

```bash
# Run all refinement domains
/project-refine

# Run specific domains
/project-refine docs code

# Run configured defaults
/project-refine --defaults
```

---

## CLAUDE.md Configuration

Shares the same `## Health Check Configuration` section as `project-health`:

```markdown
## Health Check Configuration

**Default refine domains:** docs, code, tests, universal
**Refine skip:** (none)
**Performance budget:** 400 lines max per SKILL.md
**Additional doc paths:** wiki/, design/
```

---

## Bloat Score

Every finding is rated on two axes:

**Size reduction potential:**
- 🔴 **HIGH** — >30% reduction possible in that file or area
- 🟡 **MEDIUM** — 10–30% reduction possible
- 🟢 **LOW** — <10%, still worth noting

**Impact of fixing:**
- **A** — significantly improves navigation, readability, or maintenance
- **B** — noticeable improvement
- **C** — cosmetic or marginal

Combined: `🔴A` = large reduction with high impact, `🟢C` = tiny cosmetic change.

Findings are always presented as **opportunities**, never as failures. There is no CRITICAL — a bloated file is not broken.

---

## Refinement Domains

### `docs` — Documentation Structure & Readability

> Could documentation be better structured, smaller, or easier to read?

**Structure & organisation**
- [ ] Would a different grouping or ordering of sections improve navigation?
- [ ] Are there docs over ~400 lines with multiple distinct topics that would be clearer as separate linked files?
- [ ] Are there multiple small files covering closely related topics that would read better merged?
- [ ] Are related topics scattered across documents that should be consolidated?

**Readability**
- [ ] Are there readability issues — passive voice, unexplained jargon, walls of text, sentences over 25 words?
- [ ] Could any prose be replaced with a table or example that's easier to scan?
- [ ] Is the detail level appropriate for the intended audience?

**Dead weight**
- [ ] Are there sections that restate what was just said, or introductory paragraphs that add no information?
- [ ] Are there sections describing plans, history, or context that are no longer relevant?
- [ ] Are there documents or sections that are never read because they're hard to find or navigate to?

---

### `code` — Deduplication & Abstraction

> Could code be deduplicated, abstracted, or simplified?

**Duplication**
- [ ] Are there the same blocks of logic appearing 3+ times? (high risk: fix one, miss others)
- [ ] Are there similar but not identical blocks that should be parameterised and shared?
- [ ] Are there literal values (strings, numbers, paths) repeated in multiple places? (should be named constants)

**Abstraction opportunities**
- [ ] Are there repeated sequences of calls that always appear together and belong in a helper?
- [ ] Are there functions over ~30 lines combining multiple distinct concerns that would be clearer split?
- [ ] Are there missing abstractions that would make the code more expressive?

**Dead code**
- [ ] Is there commented-out code? (remove it — git history preserves it)
- [ ] Are there functions, classes, or modules that are never called?
- [ ] Are there feature flags or compatibility shims for things that no longer exist?

---

### `tests` — Grouping & Modularisation

> Could tests be better grouped, modularised, or deduplicated?

**Organisation**
- [ ] Are there tests for one feature spread across multiple files without clear ownership?
- [ ] Would any tests benefit from being grouped into classes or modules to reflect what they're testing?
- [ ] Do test names follow a consistent pattern, making it easy to see what's covered?

**Duplication**
- [ ] Is the same fixture or arrangement code copy-pasted across multiple test methods?
- [ ] Are there test patterns repeated enough to extract into shared helpers or base classes?

**Size & scope**
- [ ] Are there test files over ~300 lines testing multiple unrelated concerns?
- [ ] Are there tests so tightly coupled to implementation they'd break on any refactor?

---

### `universal` — Bloat Across All Areas

> What is oversized, over-engineered, or unnecessarily complex anywhere in the project?

- [ ] Are there files >50% larger than the guideline for their type? (SKILL.md: ~400 lines, test files: ~300 lines)
- [ ] Are there logic or document sections nested >3 levels deep that could be flattened?
- [ ] Are there functions with >4 parameters that could be grouped into a config object or simplified?
- [ ] Are there complex solutions for problems that have a simpler answer?
- [ ] Are there more comment lines than code lines explaining obvious things?
- [ ] Are there dependencies that are larger than the value they provide?

---

## Output Format

Findings presented as opportunities, rated by bloat score:

```
## project-refine — Opportunities Found

### 🔴A — High impact, significant size reduction
- scripts/validate_all.py (lines 45–89): run_validator() logic repeated
  for each tier; extract to a shared helper. Est. -40 lines. [code]

### 🟡B — Medium impact
- update-primary-doc/SKILL.md (312 lines): Steps 4–7 cover two unrelated
  concerns; splitting would improve navigation. Est. -20 lines. [docs]

### 🟢C — Low impact, cosmetic
- java-dev/SKILL.md: "Code duplication" and "Code clarity" are adjacent
  and both cover style; could merge. Est. -5 lines. [docs]

### Nothing found
✅ tests, universal
```

---

## Open Questions

- [ ] Should `project-refine` offer to apply changes automatically for mechanical improvements (extract constant, rename file)?
- [ ] Should it track which opportunities were accepted vs deferred, to avoid re-surfacing them?
- [ ] Should there be a threshold below which findings aren't reported (e.g. ignore `🟢C` by default)?
- [ ] Should the bloat score be shown as a summary metric per domain (e.g. "docs: 🟡 moderate bloat")?
