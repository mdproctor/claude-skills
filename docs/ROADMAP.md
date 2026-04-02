# cc-praxis Roadmap

Planned improvements to the skill collection and validation framework.
These are aspirational items — not committed timelines.

---

## Validation Framework

### Phase 1: Refinement (Medium Priority)
- `generate_report.py` — Comprehensive reporting (JSON/HTML/Markdown, CI integration)
- Refine `validate_cross_document.py` — Distinguish scope names from skill references (reduce false positives)
- `validate_links.py` — External URL validation (PUSH/CI tier)
- Usability improvements — Break up dense paragraphs across skills
- Error handling improvements — Add checks to bash blocks and file operations

### Phase 2: Enhanced Analysis (Low Priority)
- `validate_examples.py` — Code example syntax + optional execution
- Prose quality analysis — Passive voice detection, sentence length
- `find_duplicates.py` — Corpus-wide duplication detection
- `check_terminology.py` — Terminology consistency across documents
- markdownlint integration
- Spelling/grammar (aspell, LanguageTool)

### Phase 3: Aspirational
- Self-testing examples (CI integration for code snippets)
- Readability scoring (textstat, Flesch-Kincaid)
- Accessibility compliance (WCAG)
- Visual aids quality checks (alt text, contrast)

---

## Skill Collection

### Planned Checks (project-health roadmap)

**Phase 1: High-Impact (Next)**
- Cross-document consistency (contradictions)
- Dangling references ("see § Missing")
- Terminology consistency
- Example validation (syntax + execution)

**Phase 2: Medium-Impact**
- Prose quality (passive voice, ambiguous pronouns)
- Duplication across corpus (fuzzy matching)
- Readability scoring (grade level)
- Grammar checking (LanguageTool)
