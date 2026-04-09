# Garden Workflows

Full step-by-step instructions for all garden operations. Referenced by `garden/SKILL.md`.

---

## CAPTURE

**Submit a specific known entry — the default operation.**

### Step 0 — Assign GE-ID (before anything else)

Every submission needs an ID before it's written.

1. Read the current counter:
   ```bash
   grep "Last assigned ID" ~/claude/knowledge-garden/GARDEN.md
   ```
2. Increment by 1. Pad to 4 digits: GE-0001, GE-0042, GE-0100.
3. Note the new ID — it goes in the submission filename and header.
4. Update GARDEN.md immediately:
   ```bash
   # sed or direct edit: "Last assigned ID: GE-XXXX" → "Last assigned ID: GE-YYYY"
   ```
5. Stage the GARDEN.md change — it will be committed with the submission in Step 7.

**Race condition note:** If two Claudes submit simultaneously, one git commit will conflict on GARDEN.md. The loser must rebase: re-read the counter, take the next ID, update their submission file and filename, and re-commit.

### Step 1 — Classify, score, and filter

First, classify the type:
- **gotcha** — something that went wrong in a non-obvious way
- **technique** — a non-obvious approach that worked
- **undocumented** — something that exists and works but isn't in the docs

Is it cross-project? (Not tied to one specific codebase's logic.) If no → skip.

Then compute the Garden Score from conversation context:

| Dimension | Score (1–3) |
|-----------|-------------|
| Non-obviousness | |
| Discoverability | |
| Breadth | |
| Pain / Impact | |
| Longevity | |
| **Total** | **/15** |

Use the score to decide how to proceed:
- **12–15** → offer confidently: "Worth adding to the garden as a [type] — scored [N]/15."
- **8–11** → offer with brief framing: "This is borderline ([N]/15) — here's the case for and against including it."
- **5–7** → only offer if the case for is genuinely compelling; name the reservation
- **<5** → don't submit; optionally note "I considered submitting X but it didn't meet the bar ([N]/15)"

### Step 1b — Light duplicate check (index scan only)

Before drafting, do a quick scan for obvious conflicts:

1. Extract the technology/stack from the entry being prepared
2. Read GARDEN.md index — find entries in the same technology category
3. Compare titles: if any existing entry title is very similar, flag it:
   > "This looks similar to GE-XXXX [title] — is this a new angle or the same thing?"
   - If same thing → stop; offer REVISE instead (use that GE-ID as Target ID)
   - If different → proceed; note which IDs were checked (for CHECKED.md update in Step 7)
4. Do NOT read garden detail files — index only. The merge Claude handles deeper checks.

Record: which existing GE-IDs were scanned (even if no conflicts found).

### Step 2 — Duplicate awareness check (context only, no reads)

Ask: is any garden content already in context from this session?
- Searched the garden earlier → you know what's there; if the new knowledge **enriches** an existing entry → pivot to **REVISE** instead of CAPTURE
- Already submitted this entry this session → skip it
- Neither → proceed without reading anything; let the merge handle it

**CAPTURE vs REVISE decision:**
- New fact, new bug, new technique with no existing entry → **CAPTURE**
- Solution / alternative / update for a known existing entry → **REVISE**
- Uncertain → proceed with CAPTURE; MERGE Claude will recognise it as an enrichment

Do NOT run `grep -r` across the garden. Do NOT read garden files.

### Step 3 — Extract the 8 fields from conversation context

Work from what's already known. Ask only for what's genuinely unclear.

| Field | Extract from |
|-------|-------------|
| Title | The surprising thing itself |
| Stack | Tools, libraries, versions mentioned |
| Symptom | What was observed / error messages |
| Context | When it occurs, what setup triggers it |
| What was tried | Failed approaches in the session |
| Root cause | The diagnosis reached |
| Fix | The working solution with code |
| Why non-obvious | Why the obvious approach failed |

### Step 4 — Determine the suggested target (don't read, just reason)

Based on the technology stack, suggest the likely destination:

| Technology | Suggested target |
|-----------|-----------------|
| AppKit, WKWebView, NSTextField, GCD | `macos-native-appkit/appkit-panama-ffm.md` |
| Panama FFM, jextract, upcalls | `java-panama-ffm/native-image-patterns.md` |
| GraalVM native image | `graalvm-native-image/<topic>.md` |
| Quarkus | `quarkus/<topic>.md` |
| Git, tmux, Docker, CLI tools (any type) | `tools/<tool>.md` |
| Techniques spanning multiple technologies | `tools/<problem-domain>.md` |
| Doesn't fit existing | `<new-descriptive-dir>/<topic>.md` |

This is a hint only — the merge Claude decides final placement.

**File headers:** If the submission targets a file that doesn't exist yet, note the required header:
- Gotcha-only file: `# <Technology> Gotchas`
- Technique-only file: `# <Technology> Techniques`
- Mixed file: `# <Technology> Gotchas and Techniques`

Technology headings use tool/library names, not problem-domain names:
- ✅ `# tmux Gotchas and Techniques`
- ❌ `# Headless Terminal Testing Techniques` (problem domain, not a technology)

### Step 5 — Draft and confirm

Draft the submission. Show it to the user:
> "Does this capture it accurately?"

Wait for confirmation before writing.

### Step 6 — Write the submission file

```bash
mkdir -p ~/claude/knowledge-garden/submissions
# write YYYY-MM-DD-<project>-GE-XXXX-<slug>.md
```

Add the GE-ID to the submission header (after **Date:**):
```
**Submission ID:** GE-XXXX
```

For REVISE submissions, also include:
```
**Target ID:** GE-YYYY  *(the existing entry being revised)*
```

### Step 7 — Commit

```bash
cd ~/claude/knowledge-garden
git add submissions/ GARDEN.md  # GARDEN.md because counter was updated
git commit -m "submit(<project>): GE-XXXX '<short title>'"
```

### Step 8 — Report back

Tell the user the submission file path and that it will be merged into the garden in the next MERGE session.

---

## SWEEP

**Systematically scan the current session for all three entry types.**

Use when: "sweep", "garden sweep", "scan for garden entries", or at the end of a session.

Unlike CAPTURE (where you provide the specific knowledge), SWEEP reviews the session from conversation memory and proposes findings. It covers all three categories explicitly so none are missed.

### Step 1 — Scan for Gotchas

Review the session for:
- Bugs whose symptom misled about the root cause
- Silent failures with no error or warning
- Things that required multiple failed approaches before the fix
- Workarounds for things that "should" work but don't

For each candidate, compute the Garden Score before proposing, then present:
*"During this session we hit [X] — the symptom was [Y] but the actual cause was [Z]. Scored [N]/15 — worth submitting as a gotcha?"*

Include the score and a one-line case for/against.

### Step 2 — Scan for Techniques

Review the session for:
- Solutions a skilled developer wouldn't naturally reach for
- Tool or API combinations used in undocumented or unexpected ways
- Patterns that solved a problem more elegantly than expected

For each candidate, compute the Garden Score before proposing, then present:
*"We used [approach] to [achieve outcome] — most developers would have [done it the hard way]. Scored [N]/15 — worth submitting as a technique?"*

### Step 3 — Scan for Undocumented

Review the session for:
- Flags, options, or behaviours only discoverable via source code
- Features that work but have no official documentation
- Things discovered through trial and error or commit history

For each candidate, compute the Garden Score before proposing, then present:
*"We discovered [X] — it exists and works but there's no documentation for it. Scored [N]/15 — worth submitting as undocumented?"*

**Score threshold during SWEEP:** Only propose candidates scoring ≥8. Below that, note briefly ("I considered [X] but it scored [N]/15 — below the bar").

### Step 4 — Submit confirmed entries

For each finding confirmed by the user: run the CAPTURE workflow with the specific content already known from context. Do NOT ask the user to re-describe things you already know.

### Step 5 — Report

Tell the user:
- How many candidates were found in each category
- How many were confirmed and submitted
- If nothing was found: "Nothing garden-worthy surfaced in this session across gotchas, techniques, or undocumented items."

> **SWEEP vs CAPTURE:** SWEEP for systematic coverage or session wrap-up. CAPTURE when you know exactly what to add.

---

## REVISE

**Submit an enrichment to an existing entry.**

Use when new knowledge enriches an existing entry rather than standing alone: a solution surfaces, an alternative is found, additional context emerges, or an entry's status changes.

### Step 1 — Identify the target entry

If the entry is already in context from this session, use that knowledge directly.

If you need to find it:
```bash
grep -r "keywords" ~/claude/knowledge-garden/ --include="*.md" \
  --exclude-dir=submissions -l
```
Then read only the specific entry:
```bash
grep -A 60 "## Entry Title" ~/claude/knowledge-garden/<path>.md
```

### Step 2 — Determine the revision kind

| Situation | Kind |
|-----------|------|
| Gotcha had no fix — now there's a real fix | `solution` |
| Entry has one solution — found a different approach | `alternative` |
| Same pattern in a different context | `variant` |
| Additional context, edge cases, or discovery | `update` |
| Bug fixed in a newer version | `resolved` |
| Feature removed or approach obsolete | `deprecated` |

### Step 3 — Draft and confirm

Draft the REVISE submission. Show it:
> "Does this accurately capture the new knowledge and how it enriches the existing entry?"

Wait for confirmation before writing.

### Step 4 — Write the submission file

```bash
mkdir -p ~/claude/knowledge-garden/submissions
# write YYYY-MM-DD-<project>-GE-XXXX-revise-<entry-slug>.md
```

Include "revise" in the filename so MERGE Claude identifies it immediately. The submission header must include both `**Submission ID:** GE-XXXX` (this revision) and `**Target ID:** GE-YYYY` (the existing entry being revised).

### Step 5 — Commit

```bash
cd ~/claude/knowledge-garden
git add submissions/ GARDEN.md
git commit -m "submit(<project>): GE-XXXX revise '<entry title>' — <what's new>"
```

### Step 6 — Report back

Tell the user what was submitted and what it adds to the existing entry.

---

## MERGE

**Integrate pending submissions into the garden.**

Run as a dedicated operation — ideally a session whose primary purpose is merging, with full context budget available for reading.

**When to run MERGE:**
- User says "merge the garden", "process garden submissions"
- There are several pending submissions (`ls ~/claude/knowledge-garden/submissions/`)
- Before a session that will need to search the garden for existing knowledge

### Step 0 — Drift check

Read GARDEN.md metadata header:
- `Entries merged since last sweep` vs `Drift threshold` (default: 10)

If threshold exceeded, offer to run DEDUPE before merging.

### Step 1 — List pending submissions

```bash
ls ~/claude/knowledge-garden/submissions/
```

### Step 2 — Read each submission

Read all submission files. They're compact by design.

### Step 3 — Load GARDEN.md index

```bash
cat ~/claude/knowledge-garden/GARDEN.md
```

Scan all three sections for entries similar to each submission.

### Step 4 — For likely duplicates: surgical read

```bash
grep -A 30 "## <existing title>" ~/claude/knowledge-garden/<file>.md
```

Don't load entire garden files — read only the sections that might overlap.

### Step 4b — Identify REVISE submissions

Check filenames for "revise". For each REVISE submission, read the target entry and integrate based on revision kind:

| Kind | How to integrate |
|------|-----------------|
| `solution` | Replace "None known" with solution; or restructure into Solution 1 / Solution 2 with pros/cons |
| `alternative` | Add `### Alternative — [brief name]` after existing Fix section with pros/cons |
| `variant` | Add `## Variant — [context]` section |
| `update` | Append to relevant section |
| `resolved` | Add `**Resolved in: vX.Y**` after Stack line; keep entry intact |
| `deprecated` | Add `**Deprecated:** [reason and date]` near top |

**Multiple solutions structure** (only when 2 or more exist):

```markdown
### Solution 1 — [brief descriptive name]
**Approach:** [one sentence]
**Pros:** [what makes it good]
**Cons/trade-offs:** [limitations]
[code block]

### Solution 2 — [brief descriptive name]
...
```

Single solutions don't get pros/cons. Do NOT retroactively reformat existing single-solution entries.

### Step 5 — Classify each submission

For each submission, check the Garden Score first, then classify:
- **New** — no matching entry; place in garden (subject to score threshold)
- **Duplicate** — identical to an existing entry; discard
- **Related** — overlaps; enrich or note the variant

### Step 5b — Medium duplicate check

For each submission classified as "New": read the first 30 lines of similar existing entries, compare, and log all comparisons to CHECKED.md (even distinct ones).

### Step 6 — Integrate new and related entries

Append to the appropriate garden file. Update GARDEN.md:

| Entry type | By Technology | By Symptom / Type | By Label |
|---|---|---|---|
| Gotcha | ✅ add | ✅ add | — |
| Technique | ✅ add | — | ✅ add |
| Undocumented | ✅ add | ✅ add | — |

Add `**ID:** GE-XXXX` to the entry header. Add compact score line at the end:
```
*Score: 11/15 · Included because: [reason] · Reservation: [none / reason]*
```

### Step 7 — Remove processed submissions

```bash
git rm ~/claude/knowledge-garden/submissions/<processed-file>.md
```

### Step 8 — Commit

```bash
git add .
git commit -m "merge: integrate N submissions — <brief summary>"
```

### Step 9 — Report

Tell the user how many submissions were merged, how many were duplicates/related, and which garden files were updated.

---

## DEDUPE

**Find and resolve duplicate entries among existing garden content.**

Use when: drift threshold exceeded (prompted by MERGE Step 0), or user explicitly requests.

### Step 1 — Load the index and pair log

Read GARDEN.md: enumerate all entries with GE-IDs, grouped by technology category.
Read CHECKED.md: build the set of already-verified pairs.

### Step 2 — Generate unchecked pairs per category

For each technology category, list all entries, generate within-category pairs, exclude pairs already in CHECKED.md. Cross-category pairs are never checked.

### Step 3 — Compare unchecked pairs

```bash
grep -A 40 "## Entry Title" ~/claude/knowledge-garden/<file>.md
```

Classify: **Distinct** / **Related** / **Duplicate**

### Step 4 — Resolve

For related pairs: add `**See also:** GE-XXXX [title]` to both entries.
For duplicates: present both to user, keep the more complete one, discard the other.

### Step 5 — Update CHECKED.md

```markdown
| GE-0003 × GE-0007 | distinct | YYYY-MM-DD | |
| GE-0004 × GE-0008 | related | YYYY-MM-DD | cross-referenced |
| GE-0005 × GE-0009 | duplicate-discarded | YYYY-MM-DD | GE-0005 kept |
```

### Step 6 — Reset drift counter

Update GARDEN.md metadata: `Last full DEDUPE sweep: YYYY-MM-DD` and `Entries merged since last sweep: 0`.

### Step 7 — Commit

```bash
git add .
git commit -m "dedupe: sweep N pairs — M related, K duplicates resolved"
```

### Step 8 — Report

How many pairs checked, how many distinct / related / duplicate, which files were updated.

---

## SEARCH

1. Read `GARDEN.md` — check By Technology, By Symptom / Type, and By Label sections
2. Follow the file link for full detail
3. If not in the index:
   ```bash
   grep -r "keywords" ~/claude/knowledge-garden/ --include="*.md" --exclude-dir=submissions
   ```
4. Return the full entry (Symptom + Root Cause + Fix + Why Non-obvious)
5. If the user just fixed something related, offer to submit the new knowledge

---

## IMPORT

**Import entries from project-level docs (e.g. `BUGS-AND-ODDITIES.md`):**

1. Read the source document
2. For each entry, classify CROSS-PROJECT or PROJECT-LOCAL
3. Show classifications, ask for confirmation
4. For cross-project entries: write a submission file per entry (CAPTURE flow)
5. Report: N submissions written, M skipped as project-specific
6. Suggest running MERGE when convenient
