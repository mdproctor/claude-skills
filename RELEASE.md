# Release Workflow

This repository uses **trunk-based development with git tags** for version management.

## Development Workflow

**Normal development (on main):**

```bash
# Work on main branch
git checkout main

# Make changes to skills
vim java-dev/SKILL.md
vim java-dev/.claude-plugin/plugin.json

# Commit changes
git add java-dev/
git commit -m "feat(java-dev): add new feature"
git push origin main
```

**Key principle:** main branch may have WIP/unstable code between releases. This is expected and fine.

## Releasing a New Version

**When a skill is stable and ready for users:**

1. **Update version in plugin.json:**
   ```bash
   vim java-dev/.claude-plugin/plugin.json
   # Change version: "1.0.0" → "1.1.0"
   git commit -am "chore(java-dev): bump version to 1.1.0"
   ```

2. **Create and push git tag:**
   ```bash
   git tag v1.1.0 -a -m "Release v1.1.0: java-dev improvements"
   git push origin main --tags
   ```

3. **Update marketplace.json (if needed):**
   ```bash
   # If this is a new major version or description changed
   vim .claude-plugin/marketplace.json
   # Update version field for the skill
   git commit -am "chore: update marketplace catalog to v1.1.0"
   git push origin main
   ```

## Version Strategy

**Semantic versioning (semver):**
- `1.0.0` → `1.0.1` - Bug fixes, patches
- `1.0.0` → `1.1.0` - New features, backwards compatible
- `1.0.0` → `2.0.0` - Breaking changes

**Git tags:**
- Format: `v1.0.0` (with `v` prefix)
- Annotated tags: `git tag -a v1.0.0 -m "Release message"`
- Lightweight tags work but annotated preferred

**Snapshot versions:**
- Use `-SNAPSHOT` suffix during development: `1.1.0-SNAPSHOT`
- Remove `-SNAPSHOT` when tagging release
- Users can install snapshots with `--snapshot` flag

## How Users Install

**Stable (default):**
```bash
scripts/claude-skill install java-dev
# Fetches from git tag v1.0.0
```

**Snapshot (latest main):**
```bash
scripts/claude-skill install java-dev --snapshot
# Fetches from main branch HEAD
```

## Marketplace Catalog vs. Repository State

**This is normal and expected:**

| Location | State During Development |
|----------|-------------------------|
| **main branch** | Working on v1.1.0-SNAPSHOT (WIP) |
| **marketplace.json** | References v1.0.0 (last stable) |
| **Latest git tag** | v1.0.0 |

**After release:**

| Location | State After Tagging v1.1.0 |
|----------|---------------------------|
| **main branch** | v1.1.0 (now stable) |
| **marketplace.json** | Updated to reference v1.1.0 |
| **Latest git tag** | v1.1.0 |

## Release Checklist

Before tagging a release:

- [ ] All tests pass (if applicable)
- [ ] plugin.json version updated
- [ ] SKILL.md documentation current
- [ ] No WIP commits on main
- [ ] Dependencies versions pinned (not `-SNAPSHOT`)

Tag release:

- [ ] `git tag v1.x.x -a -m "Release message"`
- [ ] `git push origin --tags`
- [ ] Update marketplace.json (if needed)

Verify:

- [ ] Tag visible on GitHub: `https://github.com/mdproctor/claude-skills/releases`
- [ ] Test install: `scripts/claude-skill install <skill-name>`

## Multi-Skill Releases

**Releasing multiple skills at once:**

If you've updated several skills and want to release them together:

1. Update all plugin.json versions
2. Create one tag for the repository state
3. Update marketplace.json with all new versions
4. Document which skills changed in tag message:

```bash
git tag v1.2.0 -a -m "Release v1.2.0

Skills updated:
- java-dev: 1.0.0 → 1.1.0 (new features)
- quarkus-flow-dev: 1.0.0 → 1.0.1 (bug fixes)
"
```

## First Release (v1.0.0)

For the initial marketplace release:

1. Ensure all skills have plugin.json with version "1.0.0"
2. Ensure marketplace.json lists all skills
3. Tag repository:
   ```bash
   git tag v1.0.0 -a -m "Initial marketplace release"
   git push origin main --tags
   ```

## FAQ

**Q: Can I develop on main while v1.0.0 is the stable release?**  
A: Yes! Tags freeze a point in time. Users installing stable get v1.0.0 from the tag, not from main.

**Q: Should marketplace.json always match plugin.json versions?**  
A: Not necessarily. marketplace.json is the catalog users see. It should reference the latest **stable tagged release**. plugin.json can be ahead (with `-SNAPSHOT`) during development.

**Q: How do I test a skill before releasing?**  
A: Install from local directory or use `--snapshot` flag to test from main branch.

**Q: What if I need to hotfix v1.0.0 after v1.1.0 is released?**  
A: Create a branch from the v1.0.0 tag, apply fix, tag as v1.0.1. This is rare with trunk-based development.
