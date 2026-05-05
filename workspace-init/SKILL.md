---
name: workspace-init
description: >
  Use when explicitly creating a new companion workspace from scratch —
  user invokes /workspace-init or says "init workspace for [project]" or
  "create workspace for [project]". NOT for questions about workspaces, NOT
  for ongoing use, NOT for modifying existing workspaces. One-time setup only.
---

# Workspace Init

Creates a companion workspace at `~/claude/private/<project>/` or
`~/claude/public/<project>/`. If the project belongs to a family of
related projects, the workspace can be nested under a shared parent folder
(e.g. `~/claude/private/casehub/claudony/`). Run once per project, per machine.

After running, open Claude in the workspace — CLAUDE.md instructs Claude to
`add-dir` the project automatically at session start.

---

## Workflow

### Step 1 — Detect context before asking anything

**Run detection first, then ask only what's needed.** Never ask for inputs
before understanding the project structure.

```bash
PROJECT_PATH=$(pwd)   # or from invocation argument if provided
PROJECT_NAME=$(basename "$PROJECT_PATH")
PROJECT_PARENT_DIR=$(dirname "$PROJECT_PATH")
INFERRED_PARENT=$(basename "$PROJECT_PARENT_DIR")

# Detect if the folder name is a Maven structural convention, not a real project name
case "$PROJECT_NAME" in
  parent|bom|build|root|aggregator)
    MAVEN_STRUCTURAL_NAME=true
    ;;
esac

# Ignore generic/system parent directory names
case "$INFERRED_PARENT" in
  src|projects|code|repos|dev|home|Users|claude|private|public|workspace|workspaces|".")
    INFERRED_PARENT=""
    ;;
esac

# Infer GitHub owner from existing project remote
GITHUB_OWNER=$(git -C "$PROJECT_PATH" remote get-url origin 2>/dev/null \
  | sed 's|.*github.com[:/]\([^/]*\)/.*|\1|')
```

**If `MAVEN_STRUCTURAL_NAME=true`** (folder is `parent`, `bom`, etc.):
> "This project folder is named `<name>` which looks like a Maven structural
> convention, not the real project name. The workspace should be named after
> the family — inferred as `<INFERRED_PARENT>` from the parent directory.
>
> Confirm workspace name: **`<INFERRED_PARENT>`**? (YES / different name)"

**Otherwise** confirm the inferred name:
> "Workspace name: **`<PROJECT_NAME>`** — confirm? (YES / different name)"

Then ask:
1. **Privacy** — `private` or `public`?
2. **Workspace repo tag** — ask tag and position together as two separate questions
   in the same prompt. Both are required before proceeding.

   **Question A — Tag:**
   > "Workspace repos use a tag to distinguish them from project repos.
   > Default: **`wsp`**
   >
   >   1. `wsp`  *(default)*  → e.g. wsp-casehub, wsp-casehub-engine
   >   2. `ws`                → e.g. ws-casehub, ws-casehub-engine
   >   3. `wrk`               → e.g. wrk-casehub, wrk-casehub-engine
   >   4. Custom — type your own"

   **Question B — Position (ask immediately after tag, do not skip):**
   > "Use the tag as a prefix or postfix?
   >   1. **prefix** *(default)* → tag first: `wsp-casehub`, `wsp-casehub-work`
   >   2. **postfix**            → tag last:  `casehub-wsp`, `casehub-work-wsp`
   >                               (tag always at the very end, after the full name)"

   Both questions must be answered before moving on. Set `REPO_NAME` for each workspace:
   - Prefix: `<TAG>-<family>` for root, `<TAG>-<family>-<child>` for children
   - Postfix: `<family>-<TAG>` for root, `<family>-<child>-<TAG>` for children

   Tag is always the outermost element — never inserted between family and child name.

3. **GitHub remote URL** for the workspace repo — optional.
   Show the suggested default using the resolved `REPO_NAME`:
   `github.com/<GITHUB_OWNER>/<REPO_NAME>`
   > "(YES to use this, or provide a different URL, or leave blank to add later)"

**If a GitHub URL is provided or confirmed**, check whether the repo already exists:

```bash
gh repo view <owner>/<REPO_NAME> --json name,description 2>/dev/null && echo "exists" || echo "not found"
```

Handle each case:

- **Repo doesn't exist** → create it at Step 8 as normal.

- **Repo exists and looks like a workspace** (has CLAUDE.md, HANDOFF.md, or
  workspace-style description) → offer to clone and use it:
  > "Found existing repo `wsp-<workspace-name>` on GitHub. Clone and use it
  > as the workspace? This skips creation and resumes from the existing state.
  > (YES / no — create fresh instead)"
  If YES: `git clone git@github.com:<owner>/wsp-<workspace-name> <LOCAL_PATH>` then skip Steps 2–8.

- **Repo exists but is NOT a workspace** (no workspace markers found) → offer:
  > "⚠️ `wsp-<workspace-name>` already exists on GitHub but doesn't look like
  > a workspace repo. Options:
  > 1. **Delete and recreate** — `gh repo delete <owner>/wsp-<workspace-name> --yes` then continue
  > 2. **Exit** — abort and resolve manually"
  Wait for choice. If 2, stop immediately.

### Step 1a — Detect project family

Run immediately after Step 1 context detection. The detection already has
`PROJECT_PARENT_DIR` and `INFERRED_PARENT` from Step 1.

**Infer the potential parent name from the project path:**

```bash
# Already computed in Step 1:
# PROJECT_PARENT_DIR, INFERRED_PARENT
```

If `INFERRED_PARENT` is non-empty, run two checks in order:

**Check A — Existing family workspace folder:**

```bash
FAMILY_PATH=~/claude/<privacy>/$INFERRED_PARENT
FAMILY_MEMBERS=""
if [ -d "$FAMILY_PATH" ]; then
  FAMILY_MEMBERS=$(find "$FAMILY_PATH" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | sort | tr '\n' ', ' | sed 's/,$//')
fi
```

If `$FAMILY_MEMBERS` is non-empty (the family folder already exists with at least one member):

Find repos in the family directory that don't yet have a child workspace:
```bash
MISSING=$(find "$PROJECT_PARENT_DIR" -maxdepth 1 -mindepth 1 -type d | while read d; do
  name=$(basename "$d")
  [ -d "$d/.git" ] && [ ! -d "$FAMILY_PATH/$name" ] && echo "$name"
done | sort)
```

Present:

> "Found an existing family workspace at `~/claude/<privacy>/<INFERRED_PARENT>/` containing: `<FAMILY_MEMBERS>`.
>
> Repos without a workspace yet: `<MISSING>` (or "all accounted for" if none)
>
> 1. **All missing** — create workspaces for all repos not yet set up
> 2. **Just this one** — add `<project>/` to the family
> 3. **Flat** — no family grouping"

If 1 → set `BATCH_REPOS=<MISSING repos>`, set `BASE=~/claude/<privacy>/<INFERRED_PARENT>/<project>`, run batch.
If 2 → set `BASE=~/claude/<privacy>/<INFERRED_PARENT>/<project>` and proceed to Step 1b.
If 3 → use flat path `BASE=~/claude/<privacy>/<project>` and proceed to Step 2.

**Check B — Sibling git repos in same parent directory (no existing family workspace):**

Only run Check B if Check A did not trigger (no existing family folder found).

```bash
SIBLING_COUNT=$(find "$PROJECT_PARENT_DIR" -maxdepth 2 -mindepth 2 -name ".git" -type d 2>/dev/null | wc -l | tr -d ' ')
```

If `$SIBLING_COUNT` is greater than 1, list the sibling repos:

```bash
SIBLINGS=$(find "$PROJECT_PARENT_DIR" -maxdepth 1 -mindepth 1 -type d | while read d; do
  [ -d "$d/.git" ] && basename "$d"
done | sort)
```

Present:

> "Your project lives in `<PROJECT_PARENT_DIR>` alongside `<SIBLING_COUNT>` other git repos — this looks like a project family named `<INFERRED_PARENT>`:
>
> `<SIBLINGS listed one per line>`
>
> How would you like to set up workspaces?
>
> 1. **All** — create workspaces for every repo in the family (runs this workflow for each in sequence)
> 2. **Select** — choose which repos to include now; others can be added later
> 3. **Just this one** — create only `<project>/`, nest it under the family folder
> 4. **Flat** — no family grouping, use `~/claude/<privacy>/<project>/`"

**If 1 (All):**
Set `BATCH_REPOS=<all siblings including current project>`. Set `BASE=~/claude/<privacy>/<INFERRED_PARENT>/<project>`. Run Step 1b to create the family root, then run the full workspace-init workflow (Steps 2–10) for each repo in `BATCH_REPOS` in sequence. Skip any repo that already has a workspace.

**If 2 (Select):**
Show numbered list of siblings, user picks. Set `BATCH_REPOS=<selected + current project>`. Proceed as per option 1 for the selected set.

**If 3 (Just this one):**
Set `BASE=~/claude/<privacy>/<INFERRED_PARENT>/<project>` and proceed to Step 1b then Step 2.

**If 4 (Flat):**
Use flat path `BASE=~/claude/<privacy>/<project>` and proceed to Step 2.

**If neither check triggers:** proceed directly to Step 1.5 with `BASE=~/claude/<privacy>/<project>`.

### Step 1.5 — Show plan and confirm before executing anything

**This step always runs before any files are created, moved, or committed.**

Scan each repo in `BATCH_REPOS` (or just the current project if no batch) for
methodology artifacts using the Step 9 detection logic — but do NOT execute
anything yet. Build the full plan and present it to the user.

Present the plan in this format:

```
WORKSPACE INIT PLAN
══════════════════════════════════════════════════════════════════

FAMILY ROOT  ~/claude/<privacy>/<INFERRED_PARENT>/    (new git repo)
  CLAUDE.md      family workspace hub
  .gitignore     excludes child workspace dirs
  adr/  blog/  snapshots/  specs/  plans/

CHILD WORKSPACES  (one git repo each)
  ~/claude/<privacy>/<INFERRED_PARENT>/engine/
  ~/claude/<privacy>/<INFERRED_PARENT>/work/
  ~/claude/<privacy>/<INFERRED_PARENT>/ledger/
  ...

CLAUDE.md HANDLING
┌──────────┬─────────────────────────────────────────────────────┐
│ Repo     │ Action                                              │
├──────────┼─────────────────────────────────────────────────────┤
│ engine   │ Migrate → workspace (git rm from project, symlink)  │
│ work     │ Migrate → workspace (git rm from project, symlink)  │
│ ledger   │ Migrate → workspace (git rm from project, symlink)  │
│ ...      │ ...                                                 │
└──────────┴─────────────────────────────────────────────────────┘
  Note: if you prefer to keep CLAUDE.md committed in any repo,
  say so and it will be skipped for that repo.

FILE MOVES  (copied to workspace, then git rm'd and committed in project)
┌──────────┬──────────────────────────────────┬──────────────────────────────┬────────┐
│ Repo     │ Source (project)                 │ Destination (workspace)      │ Files  │
├──────────┼──────────────────────────────────┼──────────────────────────────┼────────┤
│ work     │ HANDOFF.md                       │ work/HANDOFF.md              │ 1      │
│ work     │ blog/                            │ work/blog/                   │ 17     │
│ work     │ docs/superpowers/plans/          │ work/plans/                  │ 13     │
│ ledger   │ HANDOFF.md                       │ ledger/HANDOFF.md            │ 1      │
│ ledger   │ IDEAS.md                         │ ledger/IDEAS.md              │ 1      │
│ ledger   │ blog/                            │ ledger/blog/                 │ 20     │
│ ...      │ ...                              │ ...                          │ ...    │
└──────────┴──────────────────────────────────┴──────────────────────────────┴────────┘
  Each move: git rm in project → commit "chore: migrate methodology artifacts to workspace"

SESSION HISTORY MIGRATION
  ~/.claude/projects/<old-project-path>/ → ~/.claude/projects/<new-workspace-path>/
  (one migration per repo)

══════════════════════════════════════════════════════════════════
Total: <N> workspaces · <M> file moves · <K> git commits across <J> repos

Proceed with this plan? (YES / adjust / no)
```

- **YES** → execute everything as shown
- **adjust** → user specifies changes (e.g. "don't migrate engine CLAUDE.md", "skip connectors")
  Apply adjustments, re-show the updated plan, ask again
- **no** → abort, nothing written

**Do not create any directories, move any files, or run any git commands
until the user confirms with YES.**

### Step 1b — Create or update family workspace root

**Only runs when Step 1a resolved to a nested path (user said YES to family grouping).**

The family root `~/claude/<privacy>/<INFERRED_PARENT>/` is itself a workspace — opening
Claude there gives cross-repo context. It has its own CLAUDE.md distinct from the
per-repo child workspaces.

```bash
FAMILY_ROOT=~/claude/<privacy>/<INFERRED_PARENT>
FAMILY_CLAUDE="$FAMILY_ROOT/CLAUDE.md"
```

**If `FAMILY_CLAUDE` does not exist — create it:**

Scan for all sibling git repos in the same parent directory:
```bash
SIBLINGS=$(find "$PROJECT_PARENT_DIR" -maxdepth 1 -mindepth 1 -type d | while read d; do
  [ -d "$d/.git" ] && basename "$d"
done | sort | tr '\n' ' ')
```

Draft the family CLAUDE.md and show to user for acceptance before writing:

```
# <INFERRED_PARENT> Family Workspace

**Workspace type:** <private|public>

## Member Repos

| Repo | Local path | Child workspace |
|------|-----------|-----------------|
| <project> | <project-path> | `<INFERRED_PARENT>/<project>/` |
<one row per sibling found, marking those without a child workspace as "—">

Note: repos without a child workspace can still be loaded with add-dir on demand.

## Session Start

Open Claude here for cross-repo work. Load the repos relevant to your session:
  add-dir <path-to-repo-1>
  add-dir <path-to-repo-2>

## Shared Artifacts

Family-level artifacts (cross-repo ADRs, plans, design docs) accumulate here.
Per-repo artifacts live in each child workspace.

| Skill | Writes to |
|-------|-----------|
| adr | `adr/` |
| design-snapshot | `snapshots/` |
| write-blog | `blog/` |
| handover | `HANDOFF.md` |
| idea-log | `IDEAS.md` |
```

Create the standard artifact directories at the family root too:
```bash
mkdir -p "$FAMILY_ROOT/adr" "$FAMILY_ROOT/snapshots" "$FAMILY_ROOT/blog" \
         "$FAMILY_ROOT/specs" "$FAMILY_ROOT/plans"
```

Write the family root `.gitignore` — ignores all child workspace directories so
the family repo tracks only family-level artifacts, not the nested repos:

```bash
# Collect all sibling repo names (the same list used in the member repos table)
SIBLING_NAMES=$(find "$PROJECT_PARENT_DIR" -maxdepth 1 -mindepth 1 -type d | while read d; do
  [ -d "$d/.git" ] && basename "$d"
done | sort)

cat > "$FAMILY_ROOT/.gitignore" << EOF
# Child workspace repos — each has its own git history
$(echo "$SIBLING_NAMES" | sed 's|^|/|')

# OS / editor noise
.DS_Store
*.swp
EOF
```

This prevents git from seeing child workspace directories as untracked content
or accidentally registering them as submodules. Each child repo commits to its
own history independently.

**If `FAMILY_CLAUDE` already exists — update the member repos table:**

Add the new repo to the table if not already listed. Show the proposed change and
ask for acceptance before writing. Never overwrite the whole file — only update the
member repos table row.

### Step 2 — Create directory structure

```bash
# BASE is set in Step 1a (flat or nested under parent)
mkdir -p "$BASE/snapshots" "$BASE/adr" "$BASE/blog" "$BASE/specs" "$BASE/plans" "$BASE/design"
```

### Step 3 — Create INDEX.md in multi-file folders

```bash
cat > "$BASE/snapshots/INDEX.md" << 'EOF'
# Snapshots Index

| File | Date | Topic |
|------|------|-------|
EOF

cat > "$BASE/adr/INDEX.md" << 'EOF'
# ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
EOF

cat > "$BASE/blog/INDEX.md" << 'EOF'
# Blog Index

| File | Date | Title |
|------|------|-------|
EOF
```

(`specs/`, `plans/`, and `design/` need no INDEX.md — superpowers and design skills manage them directly.)

The `design/` directory is intentionally left empty at workspace init. `epic`
creates `design/JOURNAL.md` and `design/.meta` when an epic branch begins.

### Step 4 — Create HANDOFF.md and IDEAS.md stubs

```bash
cat > "$BASE/HANDOFF.md" << 'EOF'
# Handoff

No sessions yet.
EOF

cat > "$BASE/IDEAS.md" << 'EOF'
# Idea Log

Undecided possibilities — things worth remembering but not yet decided.
Promote to an ADR when ready to decide; discard when no longer relevant.
EOF
```

### Step 5 — Create workspace CLAUDE.md (routing hub)

Draft the base CLAUDE.md content, then **show it to the user and ask for
acceptance before writing**. Never write CLAUDE.md without confirmation.

Draft:

```
# <project> Workspace

**Project repo:** <absolute-path-to-project>
**Workspace type:** <private|public>

## Session Start

Run `add-dir <absolute-path-to-project>` before any other work.

## Artifact Locations

| Skill | Writes to |
|-------|-----------|
| brainstorming (specs) | `specs/` |
| writing-plans (plans) | `plans/` |
| handover | `HANDOFF.md` |
| idea-log | `IDEAS.md` |
| design-snapshot | `snapshots/` |
| java-update-design / update-primary-doc | `design/JOURNAL.md` (created by `epic`) |
| adr | `adr/` |
| write-blog | `blog/` |

## Structure

- `HANDOFF.md` — session handover (single file, overwritten each session)
- `IDEAS.md` — idea log (single file)
- `specs/` — brainstorming / design specs (superpowers output)
- `plans/` — implementation plans (superpowers output)
- `snapshots/` — design snapshots with INDEX.md (auto-pruned, max 10)
- `adr/` — architecture decision records with INDEX.md
- `blog/` — project diary entries with INDEX.md

## Rules

- All methodology artifacts go here, not in the project repo
- Promotion to project repo is always explicit — never automatic
- Workspace branches mirror project branches — switch both together

## Routing

Per-artifact routing destinations (optional). If absent, all artifacts route to the project repo.

| Artifact   | Destination | Notes |
|------------|-------------|-------|
| adr        | project     | lands in `docs/adr/` |
| blog       | project     | |
| design     | project     | |
| snapshots  | project     | |
| specs      | project     | lands in `docs/specs/` — design specs are project knowledge |

Valid destinations: `project` · `workspace` · `alternative ~/path/to/repo/`

To set a global default across all workspaces, add to `~/.claude/CLAUDE.md`:
\`\`\`markdown
## Routing
**Default destination:** workspace
\`\`\`
Global valid values: `workspace` or `project` only (no alternative at global level).
```

> **Note:** `epic` reads the routing config at branch creation time. If `design → workspace`,
> it records the workspace/main HEAD SHA as the design baseline instead of the project HEAD SHA.
> Configure routing before starting your first epic.

Present to the user:
> "Here is the proposed workspace CLAUDE.md. Accept, or tell me what to change:
> (YES / edit)"

Apply the accepted or tailored version. Only write the file once confirmed.

### Step 5b — Offer optional CLAUDE.md additions

After the base CLAUDE.md is confirmed, offer each optional addition
individually. Show the proposed content, ask for acceptance or tailoring.
Never add anything without confirmation.

**Option 1 — Proactive handover on context pressure:**

> "Add proactive handover suggestion? When the conversation gets long, Claude
> will suggest writing a handover before context is lost.
>
> Proposed addition to workspace CLAUDE.md:
> ```
> ## Context Management
>
> If the conversation is getting very long or you notice context pressure,
> proactively suggest writing a handover before continuing.
> ```
> (YES / no / edit)"

If accepted (or tailored), append to workspace CLAUDE.md.

**Pattern for future options:** add new options here following the same
show-and-confirm pattern. Each option is independent — accepting one does
not imply accepting others.

### Step 6 — Handle CLAUDE.md in project

If the project directory does not exist yet, skip this step and tell the user:
> "Symlink skipped — project directory doesn't exist yet. Re-run
> `/workspace-init` after creating the project to add the symlink."

Otherwise, check whether CLAUDE.md is committed to git:

```bash
git -C "<project-path>" ls-files --error-unmatch CLAUDE.md 2>/dev/null && echo "committed" || echo "not committed"
```

**If CLAUDE.md is committed**, present both options clearly:

> "CLAUDE.md is committed to git (`<size>` bytes). Where should it live?
>
> **A — Migrate to workspace** *(recommended)*
>    Content moves to workspace CLAUDE.md. Removed from project repo with `git rm`.
>    Symlink created: `project/CLAUDE.md → workspace/CLAUDE.md`
>    Opening Claude anywhere loads the same config.
>
> **B — Keep in project repo**
>    CLAUDE.md stays committed in the project. The workspace CLAUDE.md will
>    `@include` it explicitly so both directions load the full config.
>    Link direction: `workspace/CLAUDE.md` includes `@<project-path>/CLAUDE.md`
>
> Reply **A** or **B**:"

**If A (migrate to workspace):**
```bash
# Append project CLAUDE.md content to workspace CLAUDE.md
echo -e "\n---\n" >> "$BASE/CLAUDE.md"
cat "<project-path>/CLAUDE.md" >> "$BASE/CLAUDE.md"

# Remove from project and commit
git -C "<project-path>" rm CLAUDE.md
git -C "<project-path>" commit -m "chore: migrate CLAUDE.md to workspace"

# Create symlink so opening Claude in the project still loads full config
ln -sf "$BASE/CLAUDE.md" "<project-path>/CLAUDE.md"
echo "CLAUDE.md" >> "<project-path>/.git/info/exclude"
```

**If B (keep in project repo):**
```bash
# Add @include of the project CLAUDE.md to the workspace CLAUDE.md
echo "" >> "$BASE/CLAUDE.md"
echo "@<project-path>/CLAUDE.md" >> "$BASE/CLAUDE.md"
```
Tell the user:
> "CLAUDE.md stays in the project repo. The workspace CLAUDE.md now includes
> it via `@<project-path>/CLAUDE.md` — opening Claude in either location
> loads the full config."

**If CLAUDE.md is not committed**, create the symlink as normal:
```bash
ln -sf "$BASE/CLAUDE.md" "<project-path>/CLAUDE.md"
echo "CLAUDE.md" >> "<project-path>/.git/info/exclude"
```

### Step 7 — Create .gitignore for workspace

```bash
cat > "$BASE/.gitignore" << 'EOF'
.DS_Store
EOF
```

### Step 8 — Initialise git and push

```bash
cd "$BASE"
git init
git add .
git commit -m "init: workspace for <project>"
```

If the user provided a GitHub remote URL, create the repo and push:

```bash
gh repo create <owner>/<REPO_NAME> --private --description "Workspace for <workspace-name>" 2>/dev/null || true
git remote add origin git@github.com:<owner>/<REPO_NAME>.git
git push -u origin main
```

If no remote URL provided, tell the user:
> Remote not configured. When ready (using your chosen tag `<REPO_NAME>`):
> ```bash
> gh repo create <owner>/<REPO_NAME> --private
> git remote add origin git@github.com:<owner>/<REPO_NAME>.git
> git push -u origin main
> ```

### Step 9b — Migrate Claude session history and memory

Claude Code stores per-project conversation history and auto-memory keyed to
the working directory path. Without migration, opening Claude in the workspace
loses all previous sessions.

Derive the old and new project data paths from the directory paths:

```bash
OLD_KEY=$(echo "$PROJECT_PATH" | sed 's|^/||' | tr '/' '-')
NEW_KEY=$(echo "$BASE" | sed 's|^/||' | tr '/' '-')
OLD_DIR="$HOME/.claude/projects/$OLD_KEY"
NEW_DIR="$HOME/.claude/projects/$NEW_KEY"
```

If old data exists and new location is empty, migrate it:

```bash
if [ -d "$OLD_DIR" ] && [ ! -d "$NEW_DIR" ]; then
  mv "$OLD_DIR" "$NEW_DIR"
  echo "Migrated Claude session history and memory to workspace path."
elif [ ! -d "$OLD_DIR" ]; then
  echo "No existing Claude project data found — nothing to migrate."
elif [ -d "$NEW_DIR" ]; then
  echo "Workspace project data already exists at $NEW_DIR — skipping migration."
fi
```

This step runs unconditionally — session continuity is not optional.

### Step 9 — Detect and offer to migrate existing artifacts

Scan for existing methodology artifacts across the project:

```bash
FOUND=()
# Root-level handovers and ideas
[ -f "<project-path>/HANDOFF.md" ]  && git -C "<project-path>" ls-files --error-unmatch HANDOFF.md  2>/dev/null && FOUND+=("HANDOFF.md → HANDOFF.md")
[ -f "<project-path>/HANDOVER.md" ] && git -C "<project-path>" ls-files --error-unmatch HANDOVER.md 2>/dev/null && FOUND+=("HANDOVER.md → HANDOFF.md")
[ -f "<project-path>/IDEAS.md" ]    && git -C "<project-path>" ls-files --error-unmatch IDEAS.md    2>/dev/null && FOUND+=("IDEAS.md → IDEAS.md")

# Root-level artifact directories (common in repos that predate docs/ convention)
# Note: adr/ excluded — project knowledge, stays in repo.
# Note: specs/ excluded — design specs are project knowledge; they explain why the
#   code is shaped the way it is and are useful for future contributors. New specs
#   are written to the workspace during active work, then merged to the project repo
#   via epic-close when the work ships.
[ -d "<project-path>/blog" ]        && FOUND+=("blog/ → blog/")
[ -d "<project-path>/plans" ]       && FOUND+=("plans/ → plans/")
[ -d "<project-path>/snapshots" ]   && FOUND+=("snapshots/ → snapshots/")

# docs/ artifacts
# Note: docs/adr/ and docs/specs/ excluded — both are project knowledge, not workspace artifacts.
[ -d "<project-path>/docs/design-snapshots" ]  && FOUND+=("docs/design-snapshots/ → snapshots/")
[ -d "<project-path>/docs/blog" ]              && FOUND+=("docs/blog/ → blog/")
[ -d "<project-path>/docs/_posts" ]            && FOUND+=("docs/_posts/ → blog/")
[ -d "<project-path>/docs/handoffs" ]          && FOUND+=("docs/handoffs/ → handoffs/")
[ -f "<project-path>/docs/ideas/IDEAS.md" ]    && FOUND+=("docs/ideas/IDEAS.md → IDEAS.md")
[ -d "<project-path>/docs/superpowers/plans" ] && FOUND+=("docs/superpowers/plans/ → plans/")

# Hidden directories
[ -d "<project-path>/.superpowers/brainstorm" ] && FOUND+=(".superpowers/brainstorm/ → specs/")
```

If any found, present the list and ask:
> "Found existing methodology artifacts:
> - [list items]
>
> Migrate them to the workspace? This will copy each to the workspace,
> remove it from the project repo with `git rm`, and commit the deletion.
> (YES / no / select)"

**Merge warning:** If both a root-level and a `docs/` location map to the same
workspace destination (e.g. `adr/` AND `docs/adr/` both → `adr/`), flag this
before copying:
> "⚠️ Both `adr/` and `docs/adr/` exist and both map to `adr/` in the workspace.
> Files with the same name will be overwritten by the second copy.
> Review for filename collisions before proceeding? (YES / no)"

Copy root-level first, then `docs/` so that `docs/` content takes precedence
in any collision. After copying, report any files that were overwritten.

If YES (or after selection is confirmed), for each item:
```bash
# 1. Copy to workspace (merges into destination dir)
cp -r "<project-path>/adr/." "$BASE/adr/"

# 2. Remove from project
git -C "<project-path>" rm -r adr

# ... repeat for each selected item, root-level before docs/
```

Then commit all removals in one go:
```bash
git -C "<project-path>" commit -m "chore: migrate methodology artifacts to workspace"
```

**Note on handovers:** If both `HANDOFF.md` and `HANDOVER.md` exist, use the
more recent file as `workspace/HANDOFF.md` and discard the older one.

### Step 10 — Confirm

> ✅ Workspace created at `~/claude/<privacy>/<project>/`
>
> **To start working:**
> 1. Open Claude in `~/claude/<privacy>/<project>/`
> 2. CLAUDE.md will instruct Claude to run `add-dir` on the project automatically
>
> **Symlink status:** CLAUDE.md in the project points to this workspace CLAUDE.md.
> Opening Claude in the project by mistake will still load full config.
>
> **Tip:** This skill is large and one-off. Run `/clear` now to free up context
> before starting real work.

### Step 10b — Offer issue tracking setup

Check if Work Tracking is already configured:

```bash
grep -q "Issue tracking.*enabled" CLAUDE.md 2>/dev/null && echo "configured" || echo "not configured"
```

If already configured → skip silently.

If not configured, ask:

> **Set up GitHub issue tracking? (YES / n)**
>
> Links all commits to GitHub issues automatically — clean release notes,
> enforced issue creation before coding starts, commit split detection.
>
> Default: **YES** — type **YES** to enable, type **n** to skip.

If YES → invoke the `issue-workflow` skill (Phase 0 runs automatically).
If n → skip. Do not ask again this session.

### Step 10c — Offer superpowers installation

Check if superpowers is already installed:

```bash
python3 -c "
import json, os
s = json.load(open(os.path.expanduser('~/.claude/settings.json')))
enabled = s.get('enabledPlugins', {})
print('installed' if 'superpowers@claude-plugins-official' in enabled else 'not installed')
"
```

If already installed → skip silently.

If not installed, ask:

> **Install superpowers? (YES / n)**
>
> Superpowers adds structured workflows for TDD, debugging, brainstorming,
> code review, and more — loaded automatically when relevant.
>
> Default: **YES** — type **YES** to install, type **n** to skip.

If YES:

> To install superpowers, run this slash command in Claude Code:
> ```
> /plugin install superpowers
> ```
> This installs from the official Claude Code plugin marketplace. Once installed,
> superpowers skills are available immediately — no restart needed.

If n → skip. Do not ask again this session.

---

## Success Criteria

- [ ] Project family detection ran (Step 1a): existing family folder checked, sibling repos checked
- [ ] `BASE` path is correct: flat (`~/claude/<privacy>/<project>/`) or nested (`~/claude/<privacy>/<parent>/<project>/`) per user choice
- [ ] Family root CLAUDE.md created or updated (Step 1b) if nested path chosen: member repos table includes new repo, artifact dirs exist at family root
- [ ] Family root `.gitignore` written with all sibling repo names — child workspaces excluded from family repo tracking
- [ ] Directory exists at correct path with all subdirs
- [ ] `CLAUDE.md` contains session-start `add-dir` instruction and artifact locations table
- [ ] `HANDOFF.md` and `IDEAS.md` exist as stubs
- [ ] `snapshots/INDEX.md`, `adr/INDEX.md`, `blog/INDEX.md` exist
- [ ] `specs/` and `plans/` directories exist
- [ ] `.gitignore` exists
- [ ] CLAUDE.md handled: migrated (symlink + .git/info/exclude) or left committed per user choice
- [ ] Claude session history and memory migrated to workspace-keyed path (`~/.claude/projects/`)
- [ ] Existing methodology artifacts offered for migration; selected ones copied and `git rm`'d with single commit
- [ ] Git repo initialised with initial commit
- [ ] Remote set and pushed (if URL provided)
- [ ] Issue tracking offered; configured via `issue-workflow` Phase 0 if accepted
- [ ] Superpowers offered; install command shown if not already installed

---

## Skill Chaining

**Invoked by:** User directly at project setup time; session-start hook when
no workspace is detected

**Invokes (optional):** `issue-workflow` Phase 0 — if user accepts the offer in Step 10b; superpowers install command shown (user must run `/plugin install superpowers` manually) — if user accepts the offer in Step 10c
