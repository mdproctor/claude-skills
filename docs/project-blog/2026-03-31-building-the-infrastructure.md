# cc-praxis — Building the Infrastructure

**Date:** 2026-03-31
**Type:** phase-update

---

## What We Were Trying To Achieve

Skills are only useful if they're actually installed. After the first nine skills existed, I needed a way to distribute and install them — ideally without requiring anyone (including me) to clone a repo and manually copy files around.

The goal: a marketplace-style system where you add a single plugin registry entry and then install individual skills or curated bundles. Claude Code has a plugin marketplace mechanism; I wanted cc-praxis to live there.

## What We Believed Going In

I assumed the install mechanism would be straightforward. Claude Code has a `~/.claude/plugins/cache/` directory managed by the marketplace. We'd put the skills there and everything would work.

We also assumed the marketplace structure was flexible enough to support bundles — groups of skills that belong together (like "Java/Quarkus bundle" or "foundation principles bundle"). That assumption turned out to be correct but required more infrastructure than I expected.

## What We Tried and What Happened

**First attempt: symlinks from the repo to the plugin cache.** We wrote a sync script that symlinked skill directories into `~/.claude/plugins/cache/`. This failed — Claude Code doesn't follow symlinks in the skills directory. Skills are silently ignored if they're symlinked. We discovered this the hard way after thinking everything was working.

**Second attempt: copy directly to plugin cache.** This worked, but the plugin cache has a specific versioned directory structure (`cache/<marketplace>/<plugin>/<version>/`) and required registration in `installed_plugins.json`. It was more complex than it needed to be.

**Final approach: `~/.claude/skills/` directly.** Claude Code auto-discovers skills in this directory — no registration needed. We wrote a `claude-skill` installer script that copies directly to `~/.claude/skills/`. Much simpler. We also added a `sync-local` command for local development, so editing a skill and seeing the effect immediately requires only one command.

The installer became a real tool: `install`, `install-all`, `sync-local`, `list`, `uninstall`. We also added an `install-skills` skill — a wizard Claude runs to set up the environment interactively — and an `uninstall-skills` companion.

**The session-start hook** was a key addition I hadn't planned for. When you start a new Claude Code session in a directory that doesn't have a `CLAUDE.md`, it would be useful to have Claude prompt you to set up the project type. We added a hook script that fires at session start and does exactly this. The hook itself lives in `~/.claude/hooks/` and is installed by the `install-skills` wizard.

**Mermaid migration.** All the flowcharts had been in GraphViz dot format. We moved everything to Mermaid. Not a small job — nine skills, each with at least one diagram. But Mermaid is what Claude Code renders natively, so it was necessary.

**The rename: claude-skills → cc-praxis.** The original name was too generic. "cc-praxis" (Claude Code praxis — the practice of Claude Code) felt more distinctive and memorable. We renamed the repo, updated all the documentation, and changed the marketplace entry.

**Project type taxonomy.** This was a bigger design decision than it first appeared. The skills behave differently depending on the project type: `java` projects get `java-git-commit` (with DESIGN.md sync), `blog` projects get `blog-git-commit` (with content-type conventions), `custom` projects get `custom-git-commit` (with user-defined primary doc sync). We formalised this as a taxonomy with a routing table, so `git-commit` reads the project type and delegates correctly.

**The no-AI-attribution rule.** One rule I added explicitly and conspicuously: commit messages must never mention AI attribution ("Co-Authored-By: Claude", "AI-assisted:", etc.). This rule kept getting violated — not maliciously, just because the default behaviour of some tooling is to add it. I added it to the pre-commit checklist in CLAUDE.md, made it prominent in the git-commit skill, and flagged it as a critical violation. It still got violated a few times after that.

## What Changed and Why

The install mechanism pivoted twice. First away from symlinks (didn't work), then away from the plugin cache (too complex). Landing on `~/.claude/skills/` was the right call — it's what Claude Code was designed for.

The project type taxonomy was a pivot in scope. I'd started thinking of the skills as "Java skills." By the time I'd built the routing logic, it was clear the collection was meant to be a general-purpose framework — Java is just the most complete implementation. This had implications for everything that came after.

## What I Now Believe

The infrastructure turned out to be as important as the skills themselves. Without a reliable install mechanism and session-start hook, the skills would only work for me — someone who set everything up manually. With it, anyone can add the marketplace entry and have a working installation within minutes.

The project type taxonomy was the right abstraction level. Trying to make one `git-commit` skill that handles all project types directly would have been a mess. Routing to specialists based on CLAUDE.md declaration keeps each skill focused.

---

**Next:** With infrastructure in place, I wanted to see how well the skills actually worked. The answer: pretty well, but the quality framework was incomplete. I needed a way to find and fix drift.
