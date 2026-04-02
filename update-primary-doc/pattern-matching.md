# update-primary-doc — Pattern Matching Reference

Referenced by `update-primary-doc/SKILL.md` Step 3.

---

## Section Matching

When sync rules specify a section like "Vision - Current Landscape", find it using:

1. **Exact heading match:** `## Current Landscape` or `### Current Landscape`
2. **Partial match:** `## Vision and Current Landscape`
3. **Subsection:** `## Vision` → `### Current Landscape`

**If section not found:**
Include in proposal that the section needs to be created.

**Multiple sections:**
If sync rule says "Methodology, Results", update both sections.

---

## File Pattern Examples

From Sync Rules table, column 1:

| Pattern | Matches | Doesn't Match |
|---------|---------|---------------|
| `catalog/*.md` | `catalog/project.md` | `docs/catalog/project.md`, `catalog/sub/project.md` |
| `catalog/**/*.md` | `catalog/sub/project.md` | `other/catalog/project.md` |
| `docs/*.md, *.yaml` | `docs/guide.md`, `api.yaml` | `docs/sub/guide.md` |
| `VISION.md` | `VISION.md` (exact) | `docs/VISION.md` |
| `*.java` | `Test.java` | `src/Test.java`, `Test.kt` |
| `src/**/*.java` | `src/com/example/Test.java` | `test/com/example/Test.java` |
