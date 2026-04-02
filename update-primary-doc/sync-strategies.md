# update-primary-doc — Sync Strategies Reference

Referenced by `update-primary-doc/SKILL.md` Step 4.

Different strategies produce different behaviors when analyzing changes.

---

### bidirectional-consistency

**Philosophy:** Primary document and files stay synchronized bidirectionally.

**Rules:**
- New file → Add corresponding entry to primary doc
- File removed → Remove or mark deprecated in primary doc
- File modified → Update description/status in primary doc
- Section modified → Note in proposal, but don't modify files

**Use cases:** Working groups (catalog ↔ vision), documentation hubs

---

### research-progress

**Philosophy:** Primary document tracks research progress, files are evidence.

**Rules:**
- New analysis/experiment → Add to Methodology or Results section
- Paper added → Add to Bibliography section
- Data file added → Update Data Sources section
- Conclusion changes in files → Update Conclusions section

**Use cases:** Academic research, thesis projects

---

### api-spec-sync

**Philosophy:** Primary document is the spec, files implement it.

**Rules:**
- openapi.yaml changes → Update API Endpoints section
- example files added → Add to Examples section
- schema changes → Update Data Models section
- Spec changes → Note but don't auto-update (spec is authoritative)

**Use cases:** API documentation, OpenAPI specs

---

### architectural-changes

**Philosophy:** Primary document describes architecture, files implement it.

**Rules:**
- New service/component → Add to Architecture section
- Integration added → Update Integration Patterns
- Config changes → Note in Configuration section
- Removal → Mark as deprecated or remove from architecture

**Use cases:** Architecture Decision Records, system design docs

---

### Custom strategies

Users can define custom strategies in CLAUDE.md. If the strategy name is not one of
the above, use generic logic:
- Match files against patterns
- Propose additions for new files
- Propose updates for modified files
- Note removals
