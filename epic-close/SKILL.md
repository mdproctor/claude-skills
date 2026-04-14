---
name: epic-close
description: >
  Use when closing an epic — user says "close epic", "finish epic", "wrap up
  epic", or invokes /epic-close. NOT automatic — only on explicit user request.
---

# Epic Close

Closes the current epic: routes artifacts to declared destinations, merges
the design journal into the project DESIGN.md, posts specs to the GitHub
issue, and handles branch cleanup.

Requires CWD to be the workspace and `design/.meta` to exist (created by
`epic-start`).

---

## Workflow

### Step 1 — Read .meta and routing config

```bash
cat design/.meta
```

Extract: `epic`, `project-sha`, `issue` (may be empty).

Read project path from workspace CLAUDE.md:
```bash
grep "add-dir" CLAUDE.md | head -1 | sed 's/.*add-dir //'
```

Read GitHub repo from workspace CLAUDE.md `## Work Tracking` → `GitHub repo:` line:
```bash
grep "GitHub repo:" CLAUDE.md | head -1 | sed 's/.*GitHub repo: *//'
```

#### Step 1a — Read Layer 2 (global routing default)

```bash
grep -A 5 "^## Routing$" "$HOME/.claude/CLAUDE.md" 2>/dev/null \
  | grep "^\*\*Default destination:\*\*" \
  | sed 's/\*\*Default destination:\*\* *//'
```

Valid values: `workspace` or `project` only. If the value is anything else, warn:
```
⚠️ Invalid global routing value '<X>' in ~/.claude/CLAUDE.md ## Routing.
   Valid values: project | workspace
   Ignoring Layer 2 — falling through to Layer 1.
```
If the `## Routing` section is absent or has no valid `**Default destination:**` line,
Layer 2 is considered absent.

#### Step 1b — Read Layer 3 (workspace per-artifact overrides)

```bash
grep -A 30 "^## Routing$" "$WORKSPACE/CLAUDE.md" 2>/dev/null
```

Parse the markdown table for per-artifact rows. Valid values per cell:
`workspace`, `project`, `alternative <path>`.

**Deprecated vocabulary check:** If the routing config (Layer 2 or Layer 3) contains
any of the following, warn before using the value:
- `base` — deprecated alias; use `project` or `workspace`
- `project repo` — deprecated phrase; use `project`
- A table key named `design-journal` — deprecated key; use `journal`

Warn for each deprecated value found:
```
⚠️ Routing config uses deprecated value '<X>'.
   Replace with: project | workspace | alternative <path>
   Falling through to next layer for this artifact.
```

If Layer 3 is absent or empty, skip to Layer 2.

### Step 2 — Inventory artifacts

```bash
ls adr/ 2>/dev/null | grep -v INDEX.md      # ADRs
ls blog/ 2>/dev/null | grep -v INDEX.md     # Blog entries
ls snapshots/ 2>/dev/null | grep -v INDEX.md  # Snapshots
ls specs/ 2>/dev/null                        # Specs (user selects)
cat design/JOURNAL.md 2>/dev/null            # Journal
```

### Step 3 — Generate journal merge preview

Retrieve baseline project DESIGN.md at the recorded SHA:

```bash
git -C <project-path> show <project-sha>:DESIGN.md 2>/dev/null || echo "(no DESIGN.md at baseline)"
```

Read current `<project-path>/DESIGN.md`.

Read `design/JOURNAL.md` — extract all `§Section` anchors from entry headers
(lines matching `^### .* · §`).

For each anchored section: note the baseline content, the current project content,
and the journal narrative. This forms the merge preview.

If `design/JOURNAL.md` has no `§Section` entries → skip journal merge in the plan.

### Step 4 — Ask user to select specs

If an issue number exists in `design/.meta` and issue tracking is enabled:

Present list of files in `specs/`:

```
Select specs to post to GitHub issue #<N>:
  1. <filename>
  2. <filename>
  ...

Enter numbers (e.g. "1 2"), "all", or "none":
```

If no issue or tracking disabled → skip this step silently.

### Step 5 — Resolve destinations

Apply the three-layer routing algorithm for each artifact type with files present:

1. **Layer 3 check:** If a per-artifact row exists in the Layer 3 workspace CLAUDE.md
   `## Routing` table and the value is valid → use that value.
2. **Layer 2 check:** Else if Layer 2 is present and has a valid `**Default destination:**`
   line → use that value for this artifact.
3. **Layer 1 default:** Else → use `project`.

Edge cases:
- `alternative <path>` is valid at Layer 3 only; if seen at Layer 2, warn and fall to Layer 1.
- `alternative` without a path → invalid; warn and fall to next layer.
- Any deprecated vocabulary (see Step 1b) → warn and fall to next layer.

After resolving all artifacts, show the routing table and the layer source for each:

```
Resolved routing for this epic:
  adr       → workspace   (Layer 3 workspace override)
  blog      → project     (Layer 1 default)
  design    → workspace   (Layer 2 global default)
  snapshots → project     (Layer 1 default)

Proceed? (y/n)
```

Do not proceed until the user confirms. If the user says `n`, stop and let them fix
their routing config before re-running.

Detect destination capability for each resolved path:

```bash
detect_capability() {
  local dest="$1"
  if [ -d "$dest/.git" ]; then
    if git -C "$dest" remote get-url origin &>/dev/null 2>&1; then
      echo "remote-git"
    else
      echo "local-git"
    fi
  else
    echo "filesystem"
  fi
}
```

### Step 6 — Present close plan and prompt

```
Epic close plan — <epic-name>

  Artifact routing
  ├── adr/<N files>            → <destination>  [<capability>]
  ├── blog/<N files>           → <destination>  [<capability>]
  └── design/JOURNAL.md        → <destination>  [<capability>]

  Journal merge
  ├── §<Section1>              <one-line change summary>
  └── §<Section2>              <one-line change summary>

  GitHub issue #<N>
  ├── Post: <selected spec filenames>
  └── Close issue

  Branch cleanup
  └── <epic-name> (project + workspace) — prompt after

  (Skipped sections show "(skipped — nothing to do)")

Approve all, or go step by step? (all / step)
```

### Step 7a — "all" path

Execute all steps in order. On any failure: continue remaining steps, report at the end.

**Artifact promotion:**
For each artifact file and its resolved destination:
```bash
mkdir -p "<dest>"
cp "<file>" "<dest>/"
```

If `local-git` or `remote-git`:
```bash
git -C "<dest>" add .
git -C "<dest>" commit -m "feat: promote <artifact-type> from <project> epic <epic-name>"
```

If `remote-git`:
```bash
git -C "<dest>" push
```

**Journal merge:**
1. Read baseline: `git -C <project-path> show <project-sha>:DESIGN.md` — extract the `§Section` content from the baseline
2. Read the same section from the current project `DESIGN.md` — note independent changes on main
3. Apply journal narrative to the current section, incorporating independent changes
4. Write the merged result back to `<project-path>/DESIGN.md`
5. Re-read each updated `§Section` in the project `DESIGN.md`; confirm it reflects the journal narrative. Report any section that looks wrong before continuing.
6. Commit:
   ```bash
   git -C <project-path> add DESIGN.md
   git -C <project-path> commit -m "docs(<epic-name>): apply design journal — <date>"
   ```

**Spec posting:**
For each selected spec:
```bash
SUMMARY=$(head -30 "<spec-file>" | grep -A5 "## Problem\|## Summary" | tail -5)
BODY=$(cat "<spec-file>")

gh issue comment <issue> --repo <owner>/<repo> --body "## Design Spec — <filename>

${SUMMARY}

<details>
<summary>Full spec (click to expand)</summary>

${BODY}

</details>"
```

**Close issue:**
```bash
gh issue close <issue> --repo <owner>/<repo>
```

**Final report:**
```
✅ <N> ADRs promoted → <destination>
✅ Journal merged → project DESIGN.md
✅ Spec posted to #<N>, issue closed
❌ Push failed — <dest> has no network. Run: git -C <dest> push
```

### Step 7b — "step" path

**Phase 1 — Artifact routing**

Show what will be promoted where. Prompt: "Promote artifacts? (y/n)"

If yes: execute promotion for all artifact types (same logic as Step 7a).
Report results. Prompt: "Continue to journal merge? (y/n)"

**Phase 2 — Journal merge**

For each `§Section` in the journal, show:

```
§<SectionName> (journal — last updated <date>):
  <journal narrative>

Current project §<SectionName>:
  <current content>

Will update §<SectionName> with journal narrative,
preserving any independent main-branch changes.
```

Prompt: "Apply journal merge? (y/n)"

If yes:
1. Apply all section updates to `<project-path>/DESIGN.md`
2. Post-merge verification: re-read each updated section, confirm it reflects the journal. Report any section that looks wrong.
3. Commit:
   ```bash
   git -C <project-path> add DESIGN.md
   git -C <project-path> commit -m "docs(<epic-name>): apply design journal — <date>"
   ```

Prompt: "Continue to GitHub posting? (y/n)"

**Phase 3 — GitHub posting and cleanup**

Post each selected spec as a comment (same format as Step 7a).
Close the issue.
Prompt: "Continue to branch cleanup? (y/n)"

### Step 8 — Branch cleanup (both paths)

Prompt:
```
Delete epic branches?
  project: <epic-name>
  workspace: <epic-name>

  y → delete both, return to main
  n → keep both; mark epic as closed
```

If `y`:
```bash
git -C <project-path> checkout main
git -C <project-path> branch -d <epic-name>
git checkout main
git branch -d <epic-name>
```

If `n`: create `EPIC-CLOSED.md` in workspace branch root:
```markdown
# Epic Closed — <epic-name>
**Date:** <today>
**Issue:** #<N>
**Status:** Closed — branch retained for inspection
```

```bash
git add EPIC-CLOSED.md
git commit -m "docs(<epic-name>): mark epic as closed"
```

---

## Edge Cases

| Situation | Behaviour |
|-----------|-----------|
| No `design/JOURNAL.md` entries | Skip journal merge step; mark `(skipped)` in plan |
| No files in `specs/` | Skip spec selection step |
| No issue in `.meta` or tracking disabled | Skip all GitHub steps silently |
| Destination path doesn't exist | `mkdir -p <dest>` before promoting |
| Push fails (no network) | Report failure with manual resolution command; continue |
| Project has no `DESIGN.md` | Skip journal merge; note in summary |
| `design/JOURNAL.md` after close | Remains in workspace git history; not promoted to project repo |

---

## Success Criteria

- [ ] All artifacts promoted to declared destinations (or failures reported with resolution commands)
- [ ] Journal merged into project `DESIGN.md`, user confirmed
- [ ] Post-merge verification: each `§Section` anchor confirmed in updated doc
- [ ] Selected spec(s) posted to GitHub issue
- [ ] GitHub issue closed (if tracking enabled)
- [ ] Branch cleanup resolved — both branches deleted or `EPIC-CLOSED.md` created
- [ ] Workspace and project both on `main`

---

## Skill Chaining

**Invoked by:** User directly at epic close via `/epic-close`

**Chains from:** [`epic-start`] — which created `design/.meta` and `design/JOURNAL.md`

**Reads output of:** [`java-update-design`] and [`update-primary-doc`] from `design/JOURNAL.md`
