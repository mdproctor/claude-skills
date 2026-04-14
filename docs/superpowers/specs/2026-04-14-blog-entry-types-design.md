# Blog Entry Types Design

**Date:** 2026-04-14
**Status:** Approved
**Promoted from:** IDEAS.md — 2026-04-13 entry

---

## Problem

All blog entries produced by `write-blog` are diary-style session narratives. There
is no way to distinguish a topic-driven standalone article from a session diary entry,
no way to tag entries with projects or topics for filtering, and no routing metadata
to drive publishing to multiple destinations.

---

## Type Taxonomy

Entries are classified at two levels:

```
entry
├── article        topic-driven, standalone, ad-hoc
└── note           work narrative
    ├── diary      session/phase summaries (current write-blog output)
    └── ...        other note subtypes (TBD, extensible)
```

Classification is **purely metadata** — it never changes the writing workflow, voice,
or content. The same diary process applies to all note/diary entries. Articles use
the same write-blog workflow with no structural difference.

---

## Entry Frontmatter Schema

Three new fields added to entry frontmatter:

```yaml
entry_type: article | note     # top-level classification; routing-relevant
subtype: diary | ...           # note subtype; omitted for articles; extensible
projects: [cc-praxis]          # 1..n project identifiers; drives personal blog filtering
tags: [quarkus, java]          # topic tags; drives routing rules and discovery
```

The existing `type` field (`day-zero | phase-update | pivot | correction`) is kept
unchanged. It describes the narrative structure of a diary entry and is only
meaningful when `entry_type: note, subtype: diary`.

### Example: diary note

```yaml
---
layout: post
title: "cc-praxis — The Model Comes Together"
date: 2026-04-14
type: phase-update
entry_type: note
subtype: diary
projects: [cc-praxis]
tags: []
---
```

### Example: article spanning two projects

```yaml
---
layout: post
title: "Designing JOURNAL.md: Three-Way Merge for AI Workflows"
date: 2026-04-14
entry_type: article
projects: [cc-praxis, quarkus-flow]
tags: [quarkus, skills, workflow]
---
```

---

## Routing Config Format

Routing is resolved at publish time — entries carry type/tags/projects only.
The routing config computes destinations when `publish-blog` or `epic-close` runs.

### Two-layer config (same strategy as CLAUDE.md `@include`)

**Global** (`~/.claude/blog-routing.yaml`):

```yaml
version: 1

destinations:
  personal-blog:
    type: git
    path: ~/blog/
    subdir: _posts/
  quarkus-blog:
    type: git
    path: ~/quarkus-community-blog/
    subdir: _posts/

defaults:
  destinations: [personal-blog]

rules:
  - match:
      tags: [quarkus]
    destinations: [quarkus-blog, personal-blog]
```

**Project override** (`<workspace>/blog-routing.yaml`):

```yaml
extends: ~/.claude/blog-routing.yaml

rules:
  - match:
      entry_type: article
      projects: [cc-praxis]
    destinations: [personal-blog, project-blog]
```

### Rule semantics

- **Match fields:** AND logic — all listed fields must match the entry
- **Multiple matching rules:** destinations are unioned (not first-match-wins)
- **Project rules extend global** — they do not replace global rules
- **No matching rule:** entry goes to `defaults.destinations`
- **`extends:`** resolves the global config and merges project rules on top

---

## write-blog Workflow Change

One new prompt inserted at **Step 1**, after narrative type is determined:

```
Article or note?

  [A] Article — topic-driven, standalone
  [N] Note / diary — session narrative  (default)

Projects: [cc-praxis]   ← inferred from CLAUDE.md; confirm or extend
Tags (optional):
```

- `projects` is pre-populated from the project name in CLAUDE.md — user confirms or adds more
- `tags` is optional and freeform
- Selecting `[N]` sets `subtype: diary` automatically
- Selecting `[A]` omits `type` and `subtype` from frontmatter
- No other workflow changes — voice, drafting, confirmation, file naming unchanged

---

## Blog Page Separation

Articles and diary entries appear on separate pages driven by `entry_type` in
frontmatter. This is a Jekyll template concern — the skill's job ends at writing
correct frontmatter. Implementation of filtered Jekyll pages is a separate task.

---

## Out of Scope

| Item | Where it belongs |
|------|-----------------|
| Jekyll template changes for filtered pages | Separate task (project website) |
| `publish-blog` implementation | Separate skill (routes entries to destinations) |
| `epic-close` blog routing integration | Separate design (depends on stable frontmatter schema) |
| Other note subtypes beyond `diary` | Future extension — `subtype` field is the hook |

---

## Dependencies

- `write-blog/SKILL.md` — add Step 1 prompt for entry_type, projects, tags
- `~/.claude/blog-routing.yaml` — new global config file (created by `workspace-init` or manually)
- `publish-blog` (personal skill, not in cc-praxis) — reads routing config at publish time
