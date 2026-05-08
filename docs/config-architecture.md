# Claude Configuration Architecture

> **Source:** https://raw.githubusercontent.com/mdproctor/cc-praxis/main/docs/config-architecture.md  
> **Installed to:** `~/.claude/config-architecture.md` — refreshed daily by `update-claude-md`  
> **Tracks:** casehubio/parent#13

This document is the canonical map of the Claude configuration system. Before adding new guidance anywhere, consult this map to find the authoritative location and avoid duplication.

---

## Layer Architecture

Each layer has a defined purpose and hard boundaries.

| Layer | Files | Purpose | Must NOT contain |
|-------|-------|---------|-----------------|
| **Global norms** | `~/.claude/engagement.md`, `working-style.md`, `document-boundaries.md`, `design-implementation.md` | Behavioral norms — how Claude engages, universal workflow principles | Project-specific facts, workflow procedures, tool catalogues |
| **Skills** | `~/.claude/skills/*/SKILL.md` | Comprehensive guidance for a specific task type | Repetition of other skills' content — use Prerequisites instead |
| **Project CLAUDE.md** | `<repo>/CLAUDE.md` | Project-specific facts + invocation hooks | Generic norms already in global config |
| **Platform doc** | `PLATFORM.md` (casehubio) | Platform architecture + coherence protocol | Workflow procedures, skill invocations, tool catalogues |
| **Prompt snippet** | `~/claude/casehub/parent/docs/prompt-snippets.md` | Session-critical non-negotiables that must not fade | Everything that can live elsewhere |
| **This map** | `~/.claude/config-architecture.md` | Topic ownership — where each concern lives | (meta — do not add guidance here) |

---

## Topic Ownership Map

For each topic: the **authoritative** location, plus acceptable secondary appearances (pointers, not duplicates).

### IntelliJ / IDE tool guide

| Location | Role |
|----------|------|
| `ide-tooling` skill ← **authoritative** | Full mcp__intellij-index and mcp__intellij catalogue, operation→tool table, decision rule |
| `design-implementation.md` | One-line pointer to ide-tooling |
| `java-dev`, `python-dev`, `ts-dev` skills | One-line prerequisite reference |

### Bug-fix workflow (write failing test first)

| Location | Role |
|----------|------|
| `testing-principles` skill §5 ← **authoritative** | Full 5-step workflow + rationale |
| `java-dev`, `python-dev`, `ts-dev` skills | One-line prerequisite reference |
| `code-review-principles` skill | Review check — different purpose, kept as-is |

### Test taxonomy (unit / integration / E2E / browser)

| Location | Role |
|----------|------|
| `testing-principles` skill ← **authoritative** | Full taxonomy with definitions and examples |
| `java-dev`, `python-dev`, `ts-dev` skills | Via prerequisite (testing-principles) |

### Brainstorm before designing

| Location | Role |
|----------|------|
| `design-implementation.md` ## Before Designing ← **authoritative** | The norm |
| PLATFORM.md Development Session Protocol | One-line pointer |
| Project CLAUDE.md Development Workflow | Invocation hook (3 lines) — project-specific surface |

### TDD / tests before implementing

| Location | Role |
|----------|------|
| `design-implementation.md` ## Before Implementing ← **authoritative** | The norm |
| PLATFORM.md Development Session Protocol | One-line pointer |
| Project CLAUDE.md Development Workflow | Invocation hook — project-specific surface |

### Code review before committing

| Location | Role |
|----------|------|
| `code-review-principles` skill ← **authoritative** | Full review process and checklist |
| Project CLAUDE.md Development Workflow | Invocation hook — project-specific surface |

### Commit / issue linking

| Location | Role |
|----------|------|
| `design-implementation.md` ## Commits ← **authoritative** | The norm ("every commit references an issue") |
| Project CLAUDE.md Work Tracking | Adds specific format (Refs #N, Closes #N) — acceptable, extends the norm |

### Never-dogma / challenge protocols

| Location | Role |
|----------|------|
| `design-implementation.md` ## Protocols Are Not Dogma ← **authoritative** | General principle |
| PLATFORM.md Protocol preamble | One sentence in context — kept for in-situ reminder |

### Documentation drift

| Location | Role |
|----------|------|
| `design-implementation.md` ## Documentation ← **authoritative** | The norm |
| Project CLAUDE.md Development Workflow | Living docs list — project-specific, extends the norm |

### Platform coherence protocol (casehubio-specific)

| Location | Role |
|----------|------|
| `PLATFORM.md` ← **authoritative** | Full 6-step protocol |
| All casehubio project CLAUDE.md | Reference via local path |
| Prompt snippet | Reminder to read it at session start |

### Behavioral norms (engagement, directness, no sycophancy)

| Location | Role |
|----------|------|
| `~/.claude/engagement.md` ← **authoritative** | Full engagement rules |
| Not in any skill or project CLAUDE.md | — |

### Document content boundaries

| Location | Role |
|----------|------|
| `~/.claude/document-boundaries.md` ← **authoritative** | What belongs in written artifacts |
| Not in any skill or project CLAUDE.md | — |

### Skill invocation chain

| Location | Role |
|----------|------|
| `java-dev` Skill Chaining section | Partial — Java only |
| Project CLAUDE.md Development Workflow | Invocation hooks — partial |
| **Gap**: no single document shows the full chain | Tracked in parent#13 |

---

## Known Duplications (to resolve in parent#13 restructuring phase)

| Topic | Where duplicated | Status |
|-------|-----------------|--------|
| IntelliJ guidance | 4 places: ide-tooling + design-implementation.md + java-dev + python-dev + ts-dev | Partially resolved — language skills now use prerequisites |
| Skill invocation chain | Scattered, no authoritative source | Open gap |
| java-dev monolithic structure | IntelliJ section at line ~386, fades mid-session | Deferred to restructuring decision |

---

## Adding New Guidance — Checklist

Before adding anything:

1. **Check this map** — does the topic already have an authoritative location?
2. **If yes** — add a pointer there, not new content
3. **If no** — decide which layer owns it (see Layer Architecture above)
4. **Update this map** — add the new topic before committing
5. **One authoritative location only** — pointers are fine, duplicates are not
