---
name: workspace-init
description: >
  Use when a project has no companion workspace yet — user says "init
  workspace", "set up workspace", "create workspace for <project>", or
  invokes /workspace-init. NOT for day-to-day workspace use — one-time
  only, each machine independently.
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

### Step 1 — Gather inputs

Ask the user for:
1. **Project name** — workspace directory name (e.g. `cc-praxis`)
2. **Privacy** — `private` or `public`
3. **Absolute path to project** — where it lives or will live
4. **GitHub remote URL** for the workspace repo — optional; can add later

Check the project path state:

```bash
if [ -d "<project-path>" ]; then
  echo "Project directory exists"
  if [ -d "<project-path>/.git" ]; then
    echo "Git repo: yes"
  else
    echo "Git repo: no (fine — workspace-init does not require one)"
  fi
else
  echo "Project directory does not exist yet — recording intended path only"
fi
```

Confirm with the user before proceeding. The workspace can be created
regardless of whether the project directory or git repo exists.

### Step 1a — Detect project family

Run this detection **immediately after Step 1**, before creating anything.
The goal: infer whether this project belongs to a family and offer a nested
workspace path if so.

**Infer the potential parent name from the project path:**

```bash
PROJECT_PARENT_DIR=$(dirname "<project-path>")
INFERRED_PARENT=$(basename "$PROJECT_PARENT_DIR")

# Ignore generic/system directory names that don't signal a family
case "$INFERRED_PARENT" in
  src|projects|code|repos|dev|home|Users|claude|private|public|workspace|workspaces|".")
    INFERRED_PARENT=""
    ;;
esac
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

**If neither check triggers:** proceed directly to Step 2 with `BASE=~/claude/<privacy>/<project>`.

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

| Artifact   | Destination |
|------------|-------------|
| adr        | project     |
| blog       | project     |
| design     | project     |
| snapshots  | project     |

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

**If CLAUDE.md is committed**, present:
> "CLAUDE.md is committed to git (`<size>` bytes). Migrate it to the workspace?
> This will append its content to `workspace/CLAUDE.md`, remove it from the
> project repo with `git rm`, commit the deletion, then create a symlink back.
> (YES / no)"

If YES:
```bash
# Append project CLAUDE.md content to workspace CLAUDE.md (below routing header)
echo -e "\n---\n" >> "$BASE/CLAUDE.md"
cat "<project-path>/CLAUDE.md" >> "$BASE/CLAUDE.md"

# Remove from project and commit
git -C "<project-path>" rm CLAUDE.md
git -C "<project-path>" commit -m "chore: migrate CLAUDE.md to workspace"

# Create symlink so opening Claude in the project still loads full config
ln -sf "$BASE/CLAUDE.md" "<project-path>/CLAUDE.md"
echo "CLAUDE.md" >> "<project-path>/.git/info/exclude"
```

If no: skip the symlink. Tell the user:
> "CLAUDE.md stays in the project repo. Open Claude in the workspace dir —
> `add-dir` will load the project including its CLAUDE.md."

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

If the user provided a GitHub remote URL:

```bash
git remote add origin <github-remote-url>
git push -u origin main
```

If no remote URL provided, tell the user:
> Remote not configured. When ready:
> ```bash
> git remote add origin <your-github-url>
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
# Root-level handovers
[ -f "<project-path>/HANDOFF.md" ]  && git -C "<project-path>" ls-files --error-unmatch HANDOFF.md  2>/dev/null && FOUND+=("HANDOFF.md → HANDOFF.md")
[ -f "<project-path>/HANDOVER.md" ] && git -C "<project-path>" ls-files --error-unmatch HANDOVER.md 2>/dev/null && FOUND+=("HANDOVER.md → HANDOFF.md")

# docs/ artifacts
[ -d "<project-path>/docs/design-snapshots" ]  && FOUND+=("docs/design-snapshots/ → snapshots/")
[ -d "<project-path>/docs/adr" ]               && FOUND+=("docs/adr/ → adr/")
[ -d "<project-path>/docs/blog" ]              && FOUND+=("docs/blog/ → blog/")
[ -d "<project-path>/docs/_posts" ]            && FOUND+=("docs/_posts/ → blog/")
[ -d "<project-path>/docs/handoffs" ]          && FOUND+=("docs/handoffs/ → handoffs/")
[ -f "<project-path>/docs/ideas/IDEAS.md" ]    && FOUND+=("docs/ideas/IDEAS.md → IDEAS.md")
[ -d "<project-path>/docs/superpowers/specs" ] && FOUND+=("docs/superpowers/specs/ → specs/")
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

If YES (or after selection is confirmed), for each item:
```bash
# 1. Copy to workspace (example for adr/)
cp -r "<project-path>/docs/adr/." "$BASE/adr/"

# 2. Remove from project
git -C "<project-path>" rm -r docs/adr

# ... repeat for each selected item
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
