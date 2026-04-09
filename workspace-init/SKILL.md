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
`~/claude/public/<project>/`. Run once per project, per machine.

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

### Step 2 — Create directory structure

```bash
BASE=~/claude/<privacy>/<project>
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

### Step 3b — Copy project DESIGN.md into workspace (if it exists)

```bash
if [ -f "<project-path>/DESIGN.md" ]; then
  cp "<project-path>/DESIGN.md" "$BASE/design/DESIGN.md"
  echo "Copied project DESIGN.md to workspace/design/DESIGN.md"
else
  cat > "$BASE/design/DESIGN.md" << 'EOF'
# Design

*Design document for this project. Updated during the epic; merged back to
the project at epic close. Git history records every change — no separate
delta files needed.*
EOF
  echo "Created design/DESIGN.md stub (project has no DESIGN.md yet)"
fi
```

### Step 4 — Create HANDOVER.md and IDEAS.md stubs

```bash
cat > "$BASE/HANDOVER.md" << 'EOF'
# Handover

No sessions yet.
EOF

cat > "$BASE/IDEAS.md" << 'EOF'
# Idea Log

Undecided possibilities — things worth remembering but not yet decided.
Promote to an ADR when ready to decide; discard when no longer relevant.
EOF
```

### Step 5 — Create workspace CLAUDE.md (routing hub)

```bash
cat > "$BASE/CLAUDE.md" << EOF
# <project> Workspace

**Project repo:** <absolute-path-to-project>
**Workspace type:** <private|public>

## Session Start

Run \`add-dir <absolute-path-to-project>\` before any other work.

## Artifact Locations

| Skill | Writes to |
|-------|-----------|
| brainstorming (specs) | \`specs/\` |
| writing-plans (plans) | \`plans/\` |
| handover | \`HANDOVER.md\` |
| idea-log | \`IDEAS.md\` |
| design-snapshot | \`snapshots/\` |
| java-update-design / update-primary-doc | \`design/DESIGN.md\` |
| adr | \`adr/\` |
| write-blog | \`blog/\` |

## Structure

- \`HANDOVER.md\` — session handover (single file, overwritten each session)
- \`IDEAS.md\` — idea log (single file)
- \`specs/\` — brainstorming / design specs (superpowers output)
- \`plans/\` — implementation plans (superpowers output)
- \`snapshots/\` — design snapshots with INDEX.md (auto-pruned, max 10)
- \`adr/\` — architecture decision records with INDEX.md
- \`blog/\` — project diary entries with INDEX.md

## Rules

- All methodology artifacts go here, not in the project repo
- Promotion to project repo is always explicit — never automatic
- Workspace branches mirror project branches — switch both together
EOF
```

### Step 6 — Create gitignored CLAUDE.md symlink in project

```bash
# Create the symlink
ln -sf "$BASE/CLAUDE.md" "<project-path>/CLAUDE.md"

# Hide it from git — ALWAYS use .git/info/exclude, never .gitignore
# Works for any project regardless of ownership (Drools, upstream repos, etc.)
echo "CLAUDE.md" >> "<project-path>/.git/info/exclude"
```

If the project directory does not exist yet, skip this step and tell the user:
> "Symlink skipped — project directory doesn't exist yet. Re-run
> `/workspace-init` after creating the project to add the symlink."

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

### Step 9 — Detect and offer to migrate existing artifacts

Check if the project has existing methodology artifacts in `docs/`:

```bash
FOUND=()
[ -d "<project-path>/docs/design-snapshots" ] && FOUND+=("design-snapshots → snapshots/")
[ -d "<project-path>/docs/adr" ]              && FOUND+=("adr/ → adr/")
[ -d "<project-path>/docs/blog" ]             && FOUND+=("blog/ → blog/")
[ -f "<project-path>/docs/ideas/IDEAS.md" ]   && FOUND+=("IDEAS.md → IDEAS.md")
[ -d "<project-path>/docs/superpowers/specs" ] && FOUND+=("specs/ → specs/")
[ -d "<project-path>/docs/superpowers/plans" ] && FOUND+=("plans/ → plans/")
```

If any found, present to the user:
> "Found existing methodology artifacts in `docs/`:
> - [list items]
>
> Migrate them to the workspace? (YES / no)"
>
> Migration moves the files; does not delete them from the project repo
> (user can do that manually after verifying).

### Step 10 — Confirm

> ✅ Workspace created at `~/claude/<privacy>/<project>/`
>
> **To start working:**
> 1. Open Claude in `~/claude/<privacy>/<project>/`
> 2. CLAUDE.md will instruct Claude to run `add-dir` on the project automatically
>
> **Symlink status:** CLAUDE.md in the project points to this workspace CLAUDE.md.
> Opening Claude in the project by mistake will still load full config.

---

## Success Criteria

- [ ] Directory exists at correct path with all subdirs
- [ ] `CLAUDE.md` contains session-start `add-dir` instruction and artifact locations table
- [ ] `HANDOVER.md` and `IDEAS.md` exist as stubs
- [ ] `snapshots/INDEX.md`, `adr/INDEX.md`, `blog/INDEX.md` exist
- [ ] `specs/` and `plans/` directories exist
- [ ] `.gitignore` exists
- [ ] CLAUDE.md symlink exists in project (if project dir existed)
- [ ] `CLAUDE.md` in `.git/info/exclude` of project (if project dir existed)
- [ ] Git repo initialised with initial commit
- [ ] Remote set and pushed (if URL provided)

---

## Skill Chaining

**Invoked by:** User directly at project setup time; session-start hook when
no workspace is detected

**Does not chain to anything** — one-time setup skill
