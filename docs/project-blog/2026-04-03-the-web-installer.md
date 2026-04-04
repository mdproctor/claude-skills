# cc-praxis — The Web Installer

**Date:** 2026-04-03
**Type:** phase-update

---

## What We Were Trying To Achieve

The skills were working well, but managing them was entirely CLI-based. To install a bundle you ran a command. To see what was installed you ran another command. To understand how skills chain together you read Markdown.

I wanted something visual. A web app that showed all the skills, grouped by bundle, with live install state — what's installed, what's available, what's outdated. Something that could both serve as a landing page for the project (when hosted on GitHub Pages) and as a functional local installer (when served by a Python server).

## What We Believed Going In

I thought this would be a relatively contained frontend task. One HTML file, some CSS, JavaScript to call a local API. A few days of work.

What I hadn't accounted for was how much complexity lives in "show what's installed with live state" — especially when the install state needs to reflect real filesystem state, the bundle counts need to be accurate, the modal dialogs need to operate on exactly the skills that need operating, and the chain graph needs to be rendered inline as a visual dependency viewer.

## What We Tried and What Happened

**The single-file approach.** We built the entire UI as one `docs/index.html` file. It adapts based on context:
- On `localhost`: shows all three tabs (About, Browse, Install), install buttons are live
- On GitHub Pages: only About and Browse tabs are visible, Install tab is hidden

The context detection is a simple JavaScript check: `['localhost', '127.0.0.1', ''].includes(location.hostname)`. One file, two behaviours.

**The chain graph.** This was the most technically interesting part of the UI. Each skill card in the Browse view has a "Chain" button that inserts an inline row showing the skill's ancestry (from root) left-to-right, then its direct children (with grandchildren collapsible). We had several design pivots here:

- Started with a hover tooltip — rejected, too transient
- Tried a full modal — rejected, too heavy
- Landed on an inline row that inserts above or below the skill card depending on viewport position

The cycle guard was necessary to prevent circular references in the chain display. If `java-code-review → java-git-commit → java-code-review` would otherwise create an infinite loop in the rendered chain. We filter grandchildren that are already in the ancestry chain.

**Chaining data synchronisation.** The chain graph in `index.html` needed to match the chaining information in the SKILL.md files. We built a generator (`generate_web_app_data.py`) that reads all 43 SKILL.md files and regenerates the `CHAIN` JavaScript object, the `CHAINING_TRUTH` dictionary in the tests, and the overview card meta sections. The PUSH-tier validator (`validate_web_app.py`) checks that the HTML stays in sync.

**The web installer server.** `scripts/web_installer.py` is a Python HTTP server that serves `index.html` and provides a REST API:
- `GET /api/state` — returns installed skills and versions by scanning `~/.claude/skills/`
- `GET /api/marketplace` — returns the marketplace catalogue
- `POST /api/install` — runs `sync-local --skills <names> -y`
- `POST /api/uninstall` — runs `uninstall <skill>` for each skill
- `POST /api/update` — runs `sync-local --all -y`

The server also propagates `CLAUDE_SKILLS_DIR` as an environment variable to the subprocess, which is how the integration tests redirect installs to a temporary directory.

**The first live test broke immediately.** When I actually tried to use the web installer to install the Python bundle, I got an error: `sync-local: unrecognized arguments: --skills`. The `sync-local` command didn't take a `--skills` flag — I'd written the server to call a command that didn't exist.

The fix required adding `--skills` to `sync-local` in the installer script, then fixing the web installer to use it. The existing tests had been mocking `_run` so they never caught this.

**The bundle state was broken.** After fixing the install command, I discovered the bundle counts ("3 of 5 installed") in the Install tab were hardcoded HTML that never updated. The JavaScript `applyState()` function updated individual skill rows but not bundle-level state classes, counts, or button visibility. We fixed this by adding a `bundles` field to the `/api/state` response (computed from `marketplace.json`) and a `updateBundleStates()` function in the JavaScript.

**Three bundles had missing buttons.** The Principles bundle had no Uninstall button (hardcoded as "always empty"). The TypeScript bundle had no Install button (hardcoded as "always full"). The Python bundle had no Uninstall button. When I first tested the UI, you couldn't uninstall Python skills or install TypeScript ones at the bundle level at all.

**The bundle modal showed wrong counts.** With 2 of 5 Python skills installed, clicking the bundle Uninstall button showed "Uninstall 5 skills." It would have attempted to uninstall all 5, including the 3 that weren't installed. We fixed this by filtering `cfg.skills` against `INSTALLED` in `openModal()` — uninstall only includes skills that are actually installed, install only includes skills not yet installed.

## What Changed and Why

The scope expanded significantly. I started thinking about the web installer as a UI layer on top of the CLI. By the time it was done, it was a substantive piece of software with its own test suite: 55 server API tests, 40 real integration tests (running actual installs against a temp directory), and 38 Playwright browser tests.

The testing was necessary because the UI had subtle state management issues that only showed up in real usage. Mocking the subprocess calls hid real problems. The integration tests — which actually run `sync-local` against a temp directory — caught the `--skills` flag bug immediately.

## What I Now Believe

The web installer is where I learned the most about the gap between "the UI looks right" and "the UI is correct." The bundle counts, the modal skill lists, the button visibility — all of these had hardcoded values in the HTML mockup that made them look fine during development but were completely wrong once real install state was loaded.

The `CLAUDE_SKILLS_DIR` environment variable for redirecting installs in tests was the design decision that unlocked real integration testing. Without it, tests would have been limited to mocking the subprocess, which doesn't catch anything interesting.

---

**Next:** The web installer was working, but I also wanted to think about what it meant for users. That led to a broader UX review — and to extending the skill family in a different direction.
