# update-primary-doc — Worked Examples

Referenced by `update-primary-doc/SKILL.md`.

---

### Example 1: Working Group Catalog Sync

**CLAUDE.md Sync Rules:**
```markdown
| Changed Files | Document Section | Update Type |
|---------------|------------------|-------------|
| catalog/*.md | Vision - Current Landscape | Add project summary |
| docs/working-group/meeting-notes/*.md | Governance - Working Group | Add meeting summary |
```

**Staged files:**
- `catalog/langchain4j.md` (new file)

**Proposal:**
```markdown
## Primary Document Sync Proposal

**Primary Document:** docs/quarkus-ai-vision.md
**Sync Strategy:** bidirectional-consistency

### Proposed Changes

#### Section: Vision - Current Landscape

**Reason:** catalog/langchain4j.md (new) - New project cataloged

**Proposed update:**
**LangChain4j Integration**
- Primary repository for LLM integrations in Quarkus
- Maintained by [maintainer name]
- Status: Active, production-ready

**Update type:** Add new entry
```

---

### Example 2: Research Thesis Sync

**CLAUDE.md Sync Rules:**
```markdown
| Changed Files | Document Section | Update Type |
|---------------|------------------|-------------|
| experiments/*.py | Methodology - Experiments | Document experiment |
| papers/*.pdf | Bibliography | Add citation |
| data/*.csv | Data Sources | Add dataset reference |
```

**Staged files:**
- `experiments/baseline-test.py` (new file)

**Proposal:**
```markdown
## Primary Document Sync Proposal

**Primary Document:** THESIS.md
**Sync Strategy:** research-progress

### Proposed Changes

#### Section: Methodology - Experiments

**Reason:** experiments/baseline-test.py (new) - New experiment added

**Proposed update:**
##### Baseline Performance Test

Experimental validation of baseline model performance across standard benchmarks.

**Implementation:** `experiments/baseline-test.py`
**Date:** 2026-03-30
**Status:** Initial results pending

**Update type:** Add new entry
```

---

### Example 3: API Documentation Sync

**CLAUDE.md Sync Rules:**
```markdown
| Changed Files | Document Section | Update Type |
|---------------|------------------|-------------|
| openapi.yaml | API Endpoints | Sync endpoint documentation |
| examples/*.json | Examples | Add example |
```

**Staged files:**
- `openapi.yaml` (modified - new /users endpoint)

**Proposal:**
```markdown
## Primary Document Sync Proposal

**Primary Document:** docs/api-design.md
**Sync Strategy:** api-spec-sync

### Proposed Changes

#### Section: API Endpoints

**Reason:** openapi.yaml modified - New endpoint added: POST /users

**Proposed update:**
##### POST /users

Creates a new user account.

**Request:**
- `email` (string, required)
- `name` (string, required)
- `role` (string, optional)

**Response:** 201 Created with User object

**Spec reference:** openapi.yaml line 145

**Update type:** Add new entry
```
