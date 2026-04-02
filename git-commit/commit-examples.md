# git-commit — Commit Message Examples

Referenced by `git-commit/SKILL.md` for concrete examples of well-formed commits.

---

**Simple feature:**
```
feat(cli): add --verbose flag for detailed output
```

**Bug fix with context:**
```
fix(parser): handle empty input without crashing

Previously would throw NullPointerException when input was empty.
Now returns empty result gracefully.

Fixes #42
```

**Breaking change:**
```
feat(api)!: migrate from v1 to v2 endpoints

BREAKING CHANGE: all /api/v1/* endpoints removed. Use /api/v2/* instead.
See migration guide in docs/MIGRATION.md
```

**Documentation update:**
```
docs(readme): add installation instructions for Windows
```

**Refactoring:**
```
refactor(utils): extract validation logic to separate module

No functional changes, improves testability and reusability.
```

**Cross-cutting change (no scope):**
```
feat: add project type taxonomy and routing

Updated 13 files across multiple components.
No single scope accurately describes all changes.
```

**Dependency update:**
```
build(deps): upgrade Quarkus from 3.8.1 to 3.10.0

Updated quarkus.version property and verified compatibility.
All tests pass with new platform version.
```
