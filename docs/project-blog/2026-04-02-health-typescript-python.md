# cc-praxis — Health, TypeScript, and Python

**Date:** 2026-04-02
**Type:** phase-update

---

## What We Were Trying To Achieve

Two parallel goals this phase:

1. **Quality assurance** — the skills existed but there was no systematic way to verify they were internally consistent, correctly cross-referenced, and structurally sound. I wanted validators that would catch problems automatically.

2. **Expanding the language coverage** — cc-praxis was Java-first, but I wanted it to be generally useful. TypeScript/Node.js was the obvious next language to support, followed by Python.

## What We Believed Going In

I believed the quality problem was mostly about cross-references — ensuring that if skill A says it invokes skill B, then skill B says it's invoked by skill A. I expected to write a few simple validators.

For TypeScript, I believed it would be a fairly mechanical exercise: create the same set of skills as Java (dev, code-review, security-audit, dependency-update, project-health) and adapt the rules for TypeScript-specific concerns (strict mode, async patterns, prototype pollution, npm/yarn/pnpm).

## What We Tried and What Happened

**The quality framework grew much larger than planned.** What started as "a few validators" became 17 validators across three tiers:

- **COMMIT tier** (<2s): frontmatter, CSO compliance, references, naming, sections, structure, project-type list consistency, flowcharts, doc-structure, blog-commit format
- **PUSH tier** (<30s): cross-document consistency, temporal references, usability, edge cases, behaviour, README sync, web app sync
- **CI tier** (<5min): mypy, flake8, bandit for the Python tooling

The validators caught real problems every time I ran them. The cross-reference validator (`validate_references.py`) initially produced 48 false positives — it was scanning too broadly and flagging non-skill terms. We scoped it to the Skill Chaining sections only and added an allowlist of known non-skill terms. That got it to zero false positives.

The `validate_web_app.py` was a PUSH-tier addition: it reads SKILL.md files directly and compares against the web installer's CHAIN data, so any drift between the two is caught before push.

**project-health and project-refine** were the most design-intensive skills I'd written. Unlike the other skills that had fairly clear workflows, project-health needed to:
- Work across all project types
- Have a tier system (tier 1 = quick sanity check, tier 4 = deep analysis)
- Auto-chain to type-specific health skills at higher tiers
- Not overlap with project-refine (which is about improvement opportunities, not correctness)

I spent a lot of time on this design. There were five open questions in the design document at one point. We resolved them all by choosing Option B for routing (universal base, auto-chain to type-specific skills) and by drawing a clear line between "correctness" (project-health) and "improvement" (project-refine).

**TypeScript skills.** We created five: `ts-dev`, `ts-code-review`, `ts-security-audit`, `npm-dependency-update`, `ts-project-health`. The cross-referencing work we'd done for the Java skills had taught us what to do from the start — the TypeScript skills had correct bidirectional references from the first commit.

One unexpected problem: `ts-code-review` initially had `git-commit` in its `invoked_by` field via bidirectional inference. That created a false hierarchy — `git-commit` showing as a child of `ts-code-review` in the chain graph. We fixed it by making `git-commit` a BIDIRECTIONAL_EXEMPT skill; the chain doesn't force bidirectional inference through it.

**Python skills.** Five more: `python-dev`, `python-code-review`, `python-security-audit`, `pip-dependency-update`, `python-project-health`. Python's code review has specific concerns the Java and TypeScript ones don't: pickle deserialization, subprocess shell injection (which looks innocuous but isn't), the distinction between `subprocess.run(shell=True)` and using a list of arguments.

**GitHub Actions CI.** We added CI that runs the validators and tests on every push. First attempt failed because Puppeteer (used by the Mermaid validator) had Chrome sandbox issues in the CI environment. We fixed this by only treating an explicit "Parse error" from Mermaid as a syntax failure — not any Puppeteer crash.

## What Changed and Why

The health skill design pivoted several times. I initially tried to put all the type-specific checks into one universal `project-health` skill. That became unwieldy. We split it: `project-health` for universal correctness checks, separate `java-project-health`, `ts-project-health`, etc. for language-specific depth. The universal skill auto-chains to the right specialist at tier 3+.

The quality framework scope expanded because each validator revealed new problems I hadn't anticipated. That's how you know validators are working — they find things.

## What I Now Believe

Skills need a quality framework from the start, not as an afterthought. The validator infrastructure is what lets the collection grow without accumulating technical debt. Without it, every new skill I add could silently break cross-references or drift from the structural conventions.

The project-health / project-refine split is the right architecture. "Is this correct?" and "could this be better?" are genuinely different questions that deserve different answers. Mixing them causes confusion about what action to take.

---

**Next:** A different kind of tool. The skills were all text-based — you invoke them in a conversation. I wanted a visual interface for managing them. That idea became the web installer.
