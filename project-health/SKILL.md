---
name: project-health
description: >
  Use when correctness, completeness, or consistency of a project needs
  verification — "is the project healthy?", "pre-release check", "do a health
  check", "check docs are in sync", invokes /project-health. NOT for
  improvement suggestions (use project-refine for that).
---

# Project Health

Answer the question: **is this project correct, complete, and consistent?**

Runs universal quality checks that apply to every project type, then automatically
chains to the type-specific health skill based on the project type declared in CLAUDE.md.

---

## Step 0 — Read Project Type

Before any checks run, read the project type from CLAUDE.md:

```bash
grep -A 2 "## Project Type" CLAUDE.md 2>/dev/null
```

Extract the type: `skills` | `java` | `blog` | `custom` | `generic`

If CLAUDE.md is missing or has no Project Type, treat as `generic` and note it
as a `config` finding.

Store the type — type-aware checks (`primary-doc`, `artifacts`, `conventions`,
`framework`) use it throughout this skill.

---

## Step 1 — Determine Tier

Parse flags from the invocation:

| Flag | Tier | What runs |
|------|------|-----------|
| `--commit` | 1 | `validate_all.py --tier commit` only |
| `--standard` | 2 | Universal quality checks |
| `--prerelease` | 3 | Universal + type-specific quality checks |
| `--deep` | 4 | All of tier 3 + refinement questions |
| `--tier N` | N | Explicit tier (1–4) |

If no tier flag is given, prompt:

> **How thorough should this check be?**
>
> 1 — **Quick** — validators only (~30s)
> 2 — **Standard** — universal quality checks (~5 min)
> 3 — **Full** — universal + type-specific quality (~15 min)
> 4 — **Deep** — everything + refinement questions (~30 min)
>
> Enter 1–4 (default: 2):

Wait for response. If no response, use tier 2.

Also parse:
- `--save` → write report to `YYYY-MM-DD-health-report.md` after output
- Category names (e.g. `docs-sync consistency`) → run only those categories
- If categories specified without `--tier`, run at tier 2

---

## Step 2 — Tier 1: Run Automated Validators

**Always run first** (all tiers include this):

```bash
python scripts/validate_all.py --tier commit
```

If this script doesn't exist, note it as a `config` finding and skip.

Report output. If CRITICAL findings from validators → flag them.

For tier 1, **stop here**. Present findings and exit.

---

## Step 3 — Build Document Scan List

For tier 2+, build the scan scope before running checks.

**Always included:**
- All `.md` files (recursive) under `doc/`, `docs/`, `documentation/` (case-insensitive)
- Root-level `.md` files matching: `readme`, `overview`, `summary`, `index`, `contributing`,
  `governance`, `code_of_conduct`, `changelog`, `history`, `release`, `architecture`,
  `design`, `decisions`, `vision`, `philosophy`, `principles`, `api`, `schema`, `glossary`,
  `security`, `deployment`, `install`, `usage`, `troubleshooting`, `roadmap`, `spec`,
  `requirements`, `quality` (case-insensitive match on filename stem)
- Any root `.md` not on the list is still scanned
- Any `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md` anywhere in the tree

**Type-specific additions (use detected type from Step 0):**
- `skills` → all `SKILL.md` files in direct subdirectories
- `java` → `pom.xml`, `build.gradle`, Javadoc comments in `src/`
- `blog` → `_config.yml`, `_posts/`, `_layouts/`, `_includes/`
- `custom` → primary document path declared in CLAUDE.md

**User-configured additions:**
Read `## Health Check Configuration` from CLAUDE.md:
```
Additional doc paths: wiki/, design/
```
Add any listed paths to the scan scope.

---

## Step 4 — Read CLAUDE.md Health Configuration

```bash
grep -A 10 "## Health Check Configuration" CLAUDE.md 2>/dev/null
```

Parse:
- `Default checks:` → limit to these categories if no categories specified on invocation
- `Skip:` → exclude these categories even if requested
- `Additional doc paths:` → already applied in Step 3

If no configuration section, use built-in defaults: run all universal categories.

---

## Step 5 — Run Universal Checks

Run the applicable check categories at the requested tier. Skip categories listed
in `Skip:` from CLAUDE.md. If specific categories were requested, run only those.

For **tier 2**: quality items only (pass/fail checks).
For **tier 4**: quality items + refinement questions (judgment items).

### `docs-sync` — Documentation Accuracy

**Quality**
- [ ] Code behaviour matches what docs describe
- [ ] No "planned" / "not yet implemented" language for things that already exist
- [ ] Component and artifact counts are correct everywhere stated
- [ ] Version numbers consistent across all places they appear
- [ ] URLs and external references are correct and reachable
- [ ] No stale "TODO" or "coming soon" references for completed work
- [ ] Release status language matches actual state
- [ ] Temporal claims still accurate ("as of Q1 2026", "in the last 6 months")
- [ ] Code examples and output samples match what the code actually produces
- [ ] Environment variable names, config keys, and file paths match actual source

**Refinement (tier 4 only)**
- [ ] Over-explained sections where the code is self-evident?
- [ ] Detail level appropriate for intended audience?
- [ ] Could prose be replaced with a table or example easier to scan?
- [ ] Sections whose purpose overlaps enough to merge?

---

### `consistency` — Internal Consistency

**Quality**
- [ ] No contradictions between any two documents on the same topic
- [ ] No duplicate information that could drift (same content in 2+ places)
- [ ] Section naming conventions followed consistently
- [ ] Recurring structural elements use consistent formatting
- [ ] Severity levels (CRITICAL/WARNING/NOTE) used consistently
- [ ] Terminology consistent throughout (e.g. "invoke" not mixed with "call")
- [ ] Same concept named the same way across all audience levels

**Refinement (tier 4 only)**
- [ ] Scattered terminology that could be unified in a glossary?
- [ ] Sections saying the same thing in different words that should merge?
- [ ] Inconsistent formatting that adds cognitive load?

---

### `logic` — Workflow Logic & UX

**Quality**
- [ ] No workflow step references a script or file that doesn't exist
- [ ] No workflow step requires an external tool without verifying it's installed
- [ ] Hook outputs are directive (ACTION REQUIRED) not just informational
- [ ] Hook doesn't fire on non-git directories
- [ ] No workflow blocks progress without giving the user a way forward
- [ ] Error messages include recovery steps
- [ ] No redundant checks (same thing checked twice in same flow)
- [ ] Chained workflows don't create infinite loops
- [ ] Exit codes consistent and documented
- [ ] Workflow steps requiring user judgment specify clear decision criteria
- [ ] Ordered workflows document what happens if steps are skipped or reordered

**Refinement (tier 4 only)**
- [ ] Steps that could be combined without losing clarity?
- [ ] Prompts or confirmations asked more times than necessary?
- [ ] Multi-step flows reducible by inferring answers from context?
- [ ] Technical error messages where plain language would serve better?

---

### `config` — Project Configuration Health

**Quality**
- [ ] CLAUDE.md exists and has `## Project Type`
- [ ] Project type is one of: skills, java, blog, custom, generic
- [ ] Required primary artifacts for the project type exist
- [ ] `## Commit Messages` section present (no-AI-attribution rule)
- [ ] `## Work Tracking` present if team collaboration is needed (advisory)

**Refinement (tier 4 only)**
- [ ] CLAUDE.md overloaded with sections that could be removed or consolidated?
- [ ] Sections so rarely changed they could be simplified?
- [ ] Sync Rules table (type: custom) expressible more concisely?

---

### `security` — Security & Safety

**Quality**
- [ ] No hardcoded tokens, passwords, or API keys in any file
- [ ] Shell scripts quote variables to prevent word splitting
- [ ] No `rm -rf` without explicit path validation
- [ ] No `eval` of untrusted input
- [ ] All executable scripts have correct permissions
- [ ] No secrets in git history (check recent commits)
- [ ] Scripts validate inputs before acting on them
- [ ] External tool dependencies documented or checked before use
- [ ] Scripts that write files check the target directory exists first
- [ ] Relative paths in scripts work regardless of calling directory

**Refinement (tier 4 only)**
- [ ] Scripts doing more than necessary (smaller attack surface)?
- [ ] Complex shell logic replaceable with easier-to-audit Python?

---

### `release` — Release Readiness

*Run at tier 3+ or when explicitly requested.*

**Quality**
- [ ] No SNAPSHOT, dev, or alpha markers in release artifacts
- [ ] All component versions consistent and intentional
- [ ] GitHub labels set up for release note generation
- [ ] `gh release create --generate-notes` would produce meaningful output
- [ ] No obviously incomplete components (stubs, placeholders, empty sections)
- [ ] All tests passing
- [ ] Release notes reference the issues or PRs being released
- [ ] Release notes don't claim fixes/features not in this release

**Refinement (tier 4 only)**
- [ ] Would generated release notes tell a coherent story?
- [ ] GitHub issue titles good enough to serve as changelog entries?
- [ ] Could versioning strategy be simplified?

---

### `user-journey` — End User Experience

*Run at tier 3+ or when explicitly requested.*

**Quality**
- [ ] Getting started path documented and works end-to-end
- [ ] First meaningful action is guided
- [ ] Setup prompts are clear and skippable where optional
- [ ] Error messages explain what went wrong and how to recover
- [ ] No dead ends — every failure state has a next step
- [ ] Entry points (commands, slash commands, scripts) work as documented
- [ ] Getting started validated from a fresh environment
- [ ] Documented error recovery steps actually resolve the stated error

**Refinement (tier 4 only)**
- [ ] Required setup steps that could be inferred or automated?
- [ ] Onboarding sequence longer than necessary?
- [ ] Optional prompts surfaced too early in the flow?

---

### `git` — Repository State

*Run when explicitly requested or `--deep`.*

**Quality**
- [ ] No uncommitted changes that should be committed
- [ ] No stale git worktrees
- [ ] Tags consistent with marketplace/package versions (for release)
- [ ] No merge conflict markers in tracked files
- [ ] Branch is up to date with remote

**Refinement (tier 4 only)**
- [ ] Branching strategy more complex than team size justifies?
- [ ] Branches or worktrees that outlived their purpose?

---

### `primary-doc` — Primary Document Accuracy

**Quality** (apply to the correct artifact for the detected project type)
- [ ] Primary document exists
- [ ] Content accurately describes what the project currently does
- [ ] No sections describe features or workflows that no longer exist
- [ ] Referenced files, paths, and modules within the document still exist
- [ ] Terminology matches what is actually used in the codebase

**Refinement (tier 4 only)**
- [ ] Appropriate size, or should it be split into focused modules?
- [ ] Sections so rarely updated they've become stale noise?
- [ ] Structure could be reorganised to match how readers navigate it?

---

### `artifacts` — Required Artifacts Exist

**Quality** (apply to the correct artifact list for the detected project type)
- [ ] All required files and directories exist
- [ ] Required configuration files are present and parseable
- [ ] Any artifact referenced in CLAUDE.md actually exists at the declared path
- [ ] No required artifact is empty, stubbed, or placeholder only
- [ ] No required artifact appears abandoned

**Refinement (tier 4 only)**
- [ ] Any required artifact significantly larger than it needs to be?
- [ ] Required artifacts that have become redundant and could be retired?

---

### `conventions` — Conventions Declared and Followed

**Quality**
- [ ] Project-specific conventions documented in CLAUDE.md or referenced doc
- [ ] Commit messages follow the declared conventions for this project type
- [ ] File naming follows declared conventions
- [ ] No convention documented but never followed, or followed but never documented
- [ ] Declared conventions that can be enforced automatically are enforced by tooling

**Refinement (tier 4 only)**
- [ ] Conventions so obvious they don't need documentation?
- [ ] Conventions so complex they suggest the underlying approach should simplify?
- [ ] Conventions that conflict with each other subtly?

---

### `framework` — Framework Pattern Correctness

*Run at tier 3+ or when explicitly requested.*

**Quality**
- [ ] Code examples use patterns correct for the declared framework
- [ ] Documented workflows account for framework-specific constraints
- [ ] No guidance recommends an approach the framework explicitly discourages
- [ ] Framework-specific annotations, decorators, or conventions used correctly in examples
- [ ] Patterns are current for the version of the framework in use

**Refinement (tier 4 only)**
- [ ] Framework-specific guidance scattered or consolidated?
- [ ] Framework patterns documented that are never actually used?
- [ ] Could framework guidance link to authoritative external docs?

---

## Step 6 — Chain to Type-Specific Skill (Tier 3+)

At tier 3 and 4, after universal checks complete, automatically invoke the
type-specific health skill in the same session:

| Project type | Invoke |
|---|---|
| `skills` | `skills-project-health` |
| `java` | `java-project-health` |
| `blog` | `blog-project-health` |
| `custom` | `custom-project-health` |
| `generic` | Skip — universal checks only |

The type-specific skill's output is appended to the report. Do NOT redirect the
user to run a separate command — chain automatically.

If the type-specific skill does not exist yet, note it as a LOW finding:
> [config] Type-specific health skill `{type}-project-health` not yet available

---

## Step 7 — Present Report

```
## project-health report — [categories run] — tier [N]

### CRITICAL (must fix)
- [category] finding description

### HIGH (should fix)
- [category] finding description

### MEDIUM (worth fixing)
- [category] finding description

### LOW (nice to fix)
- [category] finding description

### PASS
✅ category1, category2, ...
```

Universal findings have no extra prefix. Type-specific findings are prefixed
with `[type]` (e.g. `[java]`). If no findings in a severity level, omit that section.

---

## Step 8 — Offer Auto-Fix (Mechanical Issues Only)

For mechanical findings (wrong count in README, stale version number, missing
`commands/<name>.md`), offer:

> **Auto-fixable findings detected.**
>
> Would you like me to apply mechanical fixes now?
> - [list of specific fixes]
>
> **(YES / NO — judgment calls are never auto-applied)**

Wait for response. Apply only on YES. Never auto-apply.

---

## Step 9 — Save Report (if --save)

If `--save` was passed, write findings to a date-prefixed file:

```bash
# Format: YYYY-MM-DD-health-report.md
```

Tell user:
> Report saved to `YYYY-MM-DD-health-report.md`. This file is gitignored by default.

Verify `.gitignore` includes `*-health-report.md` or similar. If not, suggest adding it.

---

## Invocation Examples

```bash
# Prompted for tier
/project-health

# Named tier aliases
/project-health --commit        # tier 1 — validators only
/project-health --standard      # tier 2 — universal checks
/project-health --prerelease    # tier 3 — universal + type-specific
/project-health --deep          # tier 4 — everything + refinement

# Explicit tier
/project-health --tier 3

# Specific categories
/project-health docs-sync consistency
/project-health docs-sync --tier 1

# Save report
/project-health --prerelease --save
```

---

## Common Pitfalls

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Running type-specific checks before reading project type | Checks have no context | Always read project type in Step 0 first |
| Reporting "plans to implement" as bugs | Intentional design language | Distinguish docs describing intent vs. describing current state |
| Auto-fixing judgment findings | Judgment calls require human decision | Only auto-fix mechanical findings, always with YES confirmation |
| Skipping chain to type-specific skill at tier 3+ | Incomplete health picture | Chain is mandatory at tier 3+ unless type is generic |
| Treating all findings as equal | CRITICAL blocks release, LOW does not | Use severity consistently |
| Running `docs-sync` without reading the actual source files | Can't verify claims without reading | Read code and docs together |

---

## Success Criteria

Health check is complete when:

- ✅ Project type read from CLAUDE.md before any checks ran
- ✅ Tier confirmed (via flag or prompt)
- ✅ All applicable universal categories checked at the requested tier
- ✅ Type-specific skill chained at tier 3+ (or skipped for generic)
- ✅ Report presented with findings grouped by severity
- ✅ Mechanical auto-fix offered (not applied without YES)
- ✅ Report saved if `--save` was passed

**Not complete until** all applicable categories checked and report presented.

---

## Skill Chaining

**Invoked by:**
- User says "health check", "is the project healthy", "pre-release check", or invokes `/project-health`
- Type-specific health skills invoke this as their prerequisite foundation
- Other skills (e.g. `git-commit`) can suggest `/project-health --commit` after significant changes

**Chains to (at tier 3+):**
- `skills-project-health` — for type: skills
- `java-project-health` — for type: java
- `blog-project-health` — for type: blog
- `custom-project-health` — for type: custom

**Companion skill:**
- [`project-refine`] — once health is green, use project-refine for improvement opportunities (bloat, structure, deduplication). They share the same CLAUDE.md Health Check Configuration section.
