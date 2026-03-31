# Claude Skill Registry

Central registry for Claude Code skills marketplace.

## Using the Registry

**Install skills:**
```bash
scripts/claude-skill install java-dev
scripts/claude-skill install quarkus-flow-dev --snapshot
```

**List installed:**
```bash
scripts/claude-skill list
```

**Uninstall:**
```bash
scripts/claude-skill uninstall java-dev
```

## Publishing Skills

### Prerequisites

1. Skills in GitHub repository (monorepo or individual repos)
2. Each skill has:
   - `SKILL.md` with valid frontmatter
   - `skill.json` generated via `scripts/generate_skill_metadata.py`
3. Repository tagged with version (e.g., `v1.0.0`)

### Publishing Steps

1. **Generate metadata:**
   ```bash
   cd ~/projects/your-skills-repo
   python scripts/generate_skill_metadata.py
   git add */skill.json
   git commit -m "build: generate skill metadata"
   ```

2. **Tag release:**
   ```bash
   git tag v1.0.0
   git push origin main --tags
   ```

3. **Update registry:**
   - Fork `github.com/mdproctor/claude-skill-registry`
   - Edit `registry.json`, add skill entry:
     ```json
     {
       "name": "your-skill-name",
       "repository": "https://github.com/yourusername/your-repo",
       "path": "your-skill-name",
       "defaultRef": "v1.0.0",
       "snapshotRef": "main"
     }
     ```
   - Submit pull request

4. **Wait for approval:**
   - Maintainers review PR
   - Once merged, skill available in marketplace

## Registry Format

```json
{
  "version": "1.0",
  "updated": "2026-03-30T22:30:00Z",
  "skills": [
    {
      "name": "skill-directory-name",
      "repository": "https://github.com/user/repo",
      "path": "skill-directory-name",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    }
  ]
}
```

**Fields:**
- `name`: Skill identifier (must match directory name)
- `repository`: GitHub repository URL
- `path`: Subdirectory path within repository
- `defaultRef`: Git tag for stable version
- `snapshotRef`: Git branch for development snapshots

## Skill Metadata Format

Each skill requires `skill.json`:

```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "repository": "https://github.com/user/repo",
  "dependencies": [
    {
      "name": "dependency-skill",
      "repository": "https://github.com/user/repo",
      "ref": "v1.0.0"
    }
  ]
}
```

Generated via `scripts/generate_skill_metadata.py`.

## Versioning

**Stable releases:** Use semver tags (`v1.0.0`, `v1.1.0`)
- Recommended for production use
- Listed as `defaultRef` in registry

**Snapshots:** Use branch references (`main`, `develop`)
- Active development, may be unstable
- Install via `--snapshot` flag
- Listed as `snapshotRef` in registry

## Support

Questions or issues:
- Registry issues: `github.com/mdproctor/claude-skill-registry/issues`
- CLI issues: `github.com/mdproctor/claude-skills/issues`
