# Claude Skill Marketplace

Official Claude Code marketplace using standard `marketplace.json` format.

## Using the Marketplace

**Official Claude Code discovery:**
```bash
/plugin marketplace add github.com/mdproctor/claude-skills
```

**Install with dependency resolution:**
```bash
git clone https://github.com/mdproctor/claude-skills
cd claude-skills
scripts/claude-skill install java-dev
scripts/claude-skill install quarkus-flow-dev  # Auto-installs java-dev dependency
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
   - `.claude-plugin/plugin.json` with metadata

### Publishing Steps

1. **Create plugin metadata:**
   ```bash
   cd your-skill-name
   mkdir -p .claude-plugin
   cat > .claude-plugin/plugin.json <<EOF
   {
     "name": "your-skill-name",
     "description": "Your skill description",
     "version": "1.0.0",
     "dependencies": [
       {
         "name": "dependency-skill",
         "version": "1.0.0"
       }
     ]
   }
   EOF
   ```

2. **Tag release:**
   ```bash
   git add .claude-plugin/plugin.json
   git commit -m "feat: add your-skill-name"
   git tag v1.0.0
   git push origin main --tags
   ```

3. **Update marketplace:**
   - Fork `github.com/mdproctor/claude-skills`
   - Edit `.claude-plugin/marketplace.json`, add plugin entry:
     ```json
     {
       "name": "your-skill-name",
       "source": "https://github.com/mdproctor/claude-skills",
       "path": "your-skill-name",
       "description": "Your skill description",
       "version": "1.0.0"
     }
     ```
   - Submit pull request

4. **Wait for approval:**
   - Maintainers review PR
   - Once merged, skill available in marketplace

## Marketplace Format (Official)

`.claude-plugin/marketplace.json`:

```json
{
  "name": "mdproctor-skills",
  "description": "Java/Quarkus development skills for Claude Code",
  "owner": {
    "name": "Mark Proctor",
    "url": "https://github.com/mdproctor"
  },
  "plugins": [
    {
      "name": "skill-name",
      "source": "https://github.com/mdproctor/claude-skills",
      "path": "skill-name",
      "description": "Skill description",
      "version": "1.0.0"
    }
  ]
}
```

**Fields:**
- `name`: Marketplace identifier
- `description`: Marketplace description
- `owner`: Maintainer information
- `plugins`: Array of plugin entries

## Plugin Metadata Format (Official)

Each skill has `.claude-plugin/plugin.json`:

```json
{
  "name": "skill-name",
  "description": "Skill description",
  "version": "1.0.0",
  "dependencies": [
    {
      "name": "dependency-skill",
      "version": "1.0.0"
    }
  ]
}
```

**Note:** The `dependencies` field is an extension until official Claude Code support arrives. See [Issue #9444](https://github.com/anthropics/claude-code/issues/9444) and [Issue #27113](https://github.com/anthropics/claude-code/issues/27113).

## Versioning

**Stable releases:** Use semver tags (`v1.0.0`, `v1.1.0`)
- Recommended for production use
- Update `version` field in plugin.json

**Snapshots:** Use branch references (`main`, `develop`)
- Active development, may be unstable
- Version contains `-SNAPSHOT` suffix

## Support

Questions or issues:
- Marketplace issues: `github.com/mdproctor/claude-skills/issues`
