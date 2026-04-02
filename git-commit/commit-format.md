# git-commit — Commit Message Format

Referenced by `git-commit/SKILL.md` Step 3 when drafting the commit message.

---

## Format

```
<type>[optional scope]: <short imperative description>

[optional body — WHAT and WHY, not HOW, wrapped at 72 chars]

[optional footer — "Fixes #123", "BREAKING CHANGE: ...", etc.]
```

## Types

| Type | When to use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix or correcting unintended behaviour |
| `docs` | Documentation only (README, comments, guides) |
| `refactor` | Restructuring with no functional change |
| `test` | Adding or updating tests |
| `build` | Build system or dependency changes |
| `chore` | Maintenance with no production code change (CI, tooling, version bumps) |
| `style` | Formatting only, no logic change (whitespace, imports) |
| `perf` | Performance improvement |

> `fix` vs `refactor`: if it corrects wrong behaviour → `fix`. If behaviour was already correct but code is cleaner → `refactor`.

## Scopes (Optional)

**Scope indicates what changed.** Only use when it accurately summarizes the **entire commit**. If the scope only describes part of the changes, omit it.

**When scopes add value:**
- Large repos with clear modules: `feat(api): add export endpoint`, `fix(cli): handle empty input`
- Monorepos with packages: `feat(auth-service): add 2FA support`
- Component-specific changes: `docs(readme): add installation guide`
- Helps others search history: "show me all API changes"

**When to omit scope:**
- Changes span multiple unrelated components
- Scope would be vague: `(misc)`, `(various)`, `(stuff)` tells you nothing
- Small repos where component is obvious
- Cross-cutting changes: `feat: add project type taxonomy`

**Common scope patterns:**

| Repository Type | Scope Examples |
|---|---|
| Monorepo | Module/package names: `api`, `cli`, `web`, `auth-service` |
| Applications | Feature areas: `auth`, `search`, `config`, `ui` |
| Libraries | Components: `core`, `utils`, `parser`, `client` |
| Documentation | Document names: `readme`, `guide`, `tutorial` |
| Infrastructure | `ci`, `scripts`, `deps`, `infra` |

**Consistency matters:** If you use scopes, stick to established names.

> **When in doubt, omit the scope.** A clear description is better than a forced/inaccurate scope.

### Real Scope Decisions: Good vs Skip

| Situation | With Scope | Without Scope | Decision | Why |
|-----------|------------|---------------|----------|-----|
| Single file: `README.md` only | `docs(readme): add install guide` | `docs: add install guide` | **Use scope** | Specific, searchable, future readers can filter |
| One module: 3 files in `api/` | `feat(api): add export endpoint` | `feat: add export endpoint` | **Use scope** | All changes are API-related, scope is accurate |
| Cross-cutting: 13 files across 7 dirs | `feat(skills): add project taxonomy` | `feat: add project type taxonomy` | **Omit scope** | No single scope covers all changes, forced scope misleads |
| Refactor: 4 skills + README + CLAUDE.md | `refactor(docs): modularize sync` | `refactor: modularize readme sync` | **Omit scope** | Affects skills AND docs, `(docs)` is only partial truth |
| Mixed changes: 2 unrelated fixes | `fix(skills): implement adr + update readme` | Split into 2 commits | **Split commits** | Each fix should be separate commit, not forced into one scope |
| Vague grouping: "various cleanup" | `chore(misc): cleanup` | `chore: cleanup validation scripts` | **Omit scope, be specific** | `(misc)` adds no value, better description is the fix |
| Deep module: `auth/tokens/refresh.ts` | `fix(auth): handle token expiry` | `fix: handle token expiry in refresh flow` | **Use scope** | `auth` is the module, readers searching auth issues find this |

**Key pattern:** Scope is good when it's a **search filter**. Omit when it's just **ceremony**.

### Breaking changes

Add `!` after the type/scope and a `BREAKING CHANGE:` footer:
```
feat(api)!: replace REST endpoints with GraphQL

BREAKING CHANGE: all API clients must migrate to GraphQL schema.
Fixes #88
```
