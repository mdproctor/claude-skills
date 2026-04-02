# Custom Projects Guide

Detailed configuration guidance for type: custom projects.
Referenced from `docs/PROJECT-TYPES.md`.

---

## Growing Your Sync Rules: Evolution Example

A working group catalog typically starts simple and grows over time.

**Scenario:** Your custom project starts small, then grows.

**Initial Sync Rules (Phase 1 - Discovery):**

```markdown
**Sync Rules:**
| Changed Files | Document Section | Update Type |
|---------------|------------------|-------------|
| `docs/catalog/*.md` | Section 2 "Projects" | Add/update catalog entries |
| `examples/*/README.md` | Section 3 "Examples" | Mark completed examples |
```

**Project grows. Phase 2 adds decision tracking:**

```markdown
**Sync Rules:**
| Changed Files | Document Section | Update Type |
|---------------|------------------|-------------|
| `docs/catalog/*.md` | Section 2 "Projects" | Add/update catalog entries |
| `examples/*/README.md` | Section 3 "Examples" | Mark completed examples |
| `decisions/*.md` | Section 4 "Decisions" | Document architectural choices |
```

**Phase 3 adds integration demos:**

```markdown
**Sync Rules:**
| Changed Files | Document Section | Update Type |
|---------------|------------------|-------------|
| `docs/catalog/*.md` | Section 2 "Projects" | Add/update catalog entries |
| `examples/*/README.md` | Section 3 "Examples" | Mark completed examples |
| `decisions/*.md` | Section 4 "Decisions" | Document architectural choices |
| `integrations/*/config.yaml` | Section 5 "Integrations" | Add integration patterns |
| `docs/roadmap.md` | Section 6 "Future Work" | Sync upcoming milestones |
```

**How to expand safely:**

1. **Add new rows, don't replace the table**
   - Existing rules continue working
   - New patterns are additive
   - No disruption to current sync behavior

2. **Test with one new row first**
   - Make a change matching the new pattern
   - Run custom-git-commit
   - Verify primary doc updates correctly
   - Then add more rules

3. **Update milestone when appropriate**
   - Phase 1 → Phase 2: Update milestone
   - Helps track progress in commit messages
   - Documents evolution of the project

4. **Keep Consistency Checks current**
   - Add checks for new sections: "All integrations reference valid catalog entries"
   - Remove checks for deprecated sections
   - Ensures primary doc stays coherent

**Common mistakes to avoid:**

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Replacing entire table | Loses existing sync patterns | Add new rows at bottom |
| Overlapping patterns | Two rules match same file → conflict | Make patterns mutually exclusive |
| Vague "Update Type" | `update-primary-doc` doesn't know what to do | Be specific: "Add entry", "Update status", "Document pattern" |
| Not testing incrementally | All 5 new rules at once → hard to debug | Add 1 rule, test, then add next |

**Result:** Your Sync Rules evolve with your project. Start simple, grow as needed, no skill changes required.
