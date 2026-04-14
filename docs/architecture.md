# cc-praxis — Skills Architecture

> For installation and getting started: [README.md](../README.md) · For the full skill catalog: [skills-catalog.md](skills-catalog.md)

---

## Skills Architecture

This collection follows a **layered architecture** where foundation skills provide universal principles, and specialized skills extend them for specific languages, frameworks, and workflows.

### Layer 1: Commit Workflow (4 skills)

**Pattern:** Router → Specialized Handlers

| Skill | Purpose | Project Types |
|-------|---------|---------------|
| **git-commit** | Entry point, routes based on project type | skills, generic |
| **java-git-commit** | Java-specific commits with DESIGN.md sync | java |
| **custom-git-commit** | User-configured commits with primary doc sync | custom |

### Layer 2: Documentation Sync (4 skills)

**Pattern:** Document Type Specialists

| Skill | Document | Project Types | Auto-Invoked By |
|-------|----------|---------------|-----------------|
| **update-claude-md** | CLAUDE.md (workflows) | all | git-commit, java-git-commit, custom-git-commit |
| **java-update-design** | DESIGN.md (architecture) | java | java-git-commit |
| **readme-sync.md** | README.md (skill catalog) | skills | git-commit |
| **update-primary-doc** | User-configured doc | custom | custom-git-commit |

### Layer 3: Review (2 skills)

**Pattern:** Domain-Specific Review Specialists

| Skill | Reviews | Auto-Invoked By | Blocks On |
|-------|---------|-----------------|-----------|
| **java-code-review** | Java code quality | java-git-commit | CRITICAL findings |
| **java-security-audit** | OWASP Top 10 | java-code-review | Security vulnerabilities |

**Note:** SKILL.md validation for type: skills repositories is handled by the skill-validation.md workflow (not a portable skill), automatically invoked by git-commit when SKILL.md files are staged.

### Layer 4: Principles (4 skills)

**Pattern:** Universal Foundations (Referenced, Not Invoked)

| Skill | Domain | Extended By |
|-------|--------|-------------|
| **code-review-principles** | Universal code review | java-code-review, ts-code-review, python-code-review |
| **security-audit-principles** | Universal OWASP Top 10 | java-security-audit, ts-security-audit, python-security-audit |
| **dependency-management-principles** | Universal BOM patterns | maven-dependency-update, npm-dependency-update, pip-dependency-update |
| **observability-principles** | Universal logging/tracing/metrics | quarkus-observability |

### Layer 5: Java/Quarkus Development (4 skills)

**Pattern:** Layered Specialization

| Skill | Purpose | Builds On |
|-------|---------|-----------|
| **java-dev** | Java development foundation | (base layer) |
| **quarkus-flow-dev** | Quarkus Flow workflows | java-dev |
| **quarkus-flow-testing** | Workflow testing | java-dev, quarkus-flow-dev |
| **quarkus-observability** | Quarkus observability config | observability-principles |

### Layer 6: Utilities (9 skills)

| Skill | Purpose | Builds On |
|-------|---------|-----------|
| **maven-dependency-update** | Maven BOM management | dependency-management-principles |
| **adr** | Architecture Decision Records | (standalone) |
| **design-snapshot** | Immutable dated design state record | (standalone) |
| **idea-log** | Living log for undecided possibilities | (standalone) |
| **write-blog** | Living project diary — decisions, pivots, and discoveries in the moment | (standalone) |
| **publish-blog** | Routes blog entries to external git destinations via blog-routing.yaml | write-blog |
| **forage** | Cross-project library of hard-won bugs, gotchas, and unexpected behaviours. Session-time: CAPTURE, SWEEP, SEARCH, REVISE. Dedup via harvest. | (standalone, writes to ~/.hortora/garden/) |

### Layer 7: Health & Quality (8 skills)

| Skill | Purpose | Builds On |
|-------|---------|-----------|
| **project-health** | Universal correctness and consistency checks | (standalone) |
| **project-refine** | Improvement opportunities and bloat reduction | (standalone) |
| **skills-project-health** | Skills repo health checks | project-health |
| **java-project-health** | Java project health checks | project-health |
| **blog-project-health** | Blog project health checks | project-health |
| **custom-project-health** | Custom project health checks | project-health |
| **ts-project-health** | TypeScript/Node.js health checks | project-health |
| **python-project-health** | Python health checks | project-health |

### Layer 8: TypeScript/Node.js Development (4 skills)

| Skill | Purpose | Builds On |
|-------|---------|-----------|
| **ts-dev** | TypeScript development guidance | (standalone) |
| **ts-code-review** | TypeScript code review | code-review-principles |
| **ts-security-audit** | TypeScript/Node.js OWASP security audit | security-audit-principles |
| **npm-dependency-update** | npm/yarn/pnpm dependency management | dependency-management-principles |

### Layer 9: Python Development (5 skills)

| Skill | Purpose | Builds On |
|-------|---------|-----------|
| **python-dev** | Python development guidance | (standalone) |
| **python-code-review** | Python code review | code-review-principles |
| **python-security-audit** | Python OWASP security audit | security-audit-principles |
| **pip-dependency-update** | pip/poetry/pipenv dependency management | dependency-management-principles |
| **python-project-health** | Python project health checks | project-health |

