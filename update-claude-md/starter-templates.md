# CLAUDE.md Starter Templates

Used by `update-claude-md` Step 1 when CLAUDE.md doesn't exist and needs to be created.

---

## Skills Repository

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Type

**Type:** skills

## Repository Purpose

[Brief description of what this skills collection provides]

## Skill Architecture

### Frontmatter Requirements

[YAML frontmatter structure and CSO rules]

### Naming Conventions

[Skill naming patterns - generic vs specific]

### Skill Chaining

[How skills reference each other]

## Editing Skills

[Guidelines for modifying skills]

## Key Skills

[List of important skills and their purposes]

## Project Artifacts

Paths that are project content (not workspace noise). Skills use this to avoid
filtering or dropping commits that touch these paths.

| Path | What it is |
|------|------------|
| `docs/adr/` | Architecture decision records |
| `CLAUDE.md` | Project conventions (build, test, naming) |

## Work Tracking

**Issue tracking:** enabled
**GitHub repo:** [owner/repo]
**Changelog:** GitHub Releases (run `gh release create --generate-notes` at milestones)

**Automatic behaviours (Claude follows these when this section is present):**
- Before starting any significant task, check if it spans multiple concerns.
  If it does, help break it into separate issues before beginning work.
- When staging changes before a commit, check if they span multiple issues.
  If they do, suggest splitting the commit using `git add -p`.
```

---

## Code Repository

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Type

**Type:** [skills | java | blog | custom | generic]

## Repository Purpose

[What this project does]

## Development Commands

**Build:**
```bash
[build command]
```

**Test:**
```bash
[test command]
```

**Run:**
```bash
[run command]
```

## Testing Patterns

[Testing framework, conventions, key patterns]

## Code Organization

[Package structure, module organization, naming conventions]

## Configuration

[Environment variables, config files, setup requirements]

## Project Artifacts

Paths that are project content (not workspace noise). Skills use this to avoid
filtering or dropping commits that touch these paths.

| Path | What it is |
|------|------------|
| `docs/adr/` | Architecture decision records |
| `CLAUDE.md` | Project conventions (build, test, naming) |

## Work Tracking

**Issue tracking:** enabled
**GitHub repo:** [owner/repo]
**Changelog:** GitHub Releases (run `gh release create --generate-notes` at milestones)

**Automatic behaviours (Claude follows these when this section is present):**
- Before starting any significant task, check if it spans multiple concerns.
  If it does, help break it into separate issues before beginning work.
- When staging changes before a commit, check if they span multiple issues.
  If they do, suggest splitting the commit using `git add -p`.
```
