# Skill Marketplace Design

**Date:** 2026-03-30
**Status:** Approved

## Overview

Transform the Claude Code skills collection from a monolithic installation into a granular marketplace where users can install individual skills or skill bundles. Enable mixing and matching specific skills, easier distribution to colleagues, and reduced bloat for users who don't need the full collection.

## Goals

1. **Granular installation** - Install only the skills you need (primary)
2. **Easy distribution** - Share specific skills without the full collection
3. **Reduce bloat** - Users working with Python don't need Java skills
4. **Automatic dependency resolution** - Installing `quarkus-flow-dev` auto-installs `java-dev`
5. **Community marketplace** - Enable others to publish and share skills

## Non-Goals

- Hosted service infrastructure (v1 uses static GitHub)
- Version conflict resolution (v1 rejects conflicts)
- Web UI for browsing (CLI-only for v1)
- Automated publishing (manual PR to registry for v1)

## Architecture

### Three-Layer Model

```
┌─────────────────────────────────────────┐
│  Layer 1: Development Repository        │
│  ~/projects/claude-skills/              │
│  (Source of truth, monorepo)            │
└─────────────────────────────────────────┘
                   │
                   │ git tag + push
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Layer 2: Distribution                   │
│  github.com/mdproctor/claude-skills     │
│  (Published monorepo)                   │
│  + claude-skill-registry/registry.json  │
└─────────────────────────────────────────┘
                   │
                   │ CLI install
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Layer 3: User Installation             │
│  ~/.claude/skills/.marketplace/         │
│  (Installed marketplace skills)         │
└─────────────────────────────────────────┘
```

### Layer 1: Development Repository (Source of Truth)

**Location:** Flexible, NOT the active `~/.claude/skills/` folder

Examples:
- `~/projects/claude-skills/` (local development)
- `~/code/my-skill-collection/`
- Any location you prefer

**Structure:** Current monorepo layout unchanged
```
claude-skills/
├── java-dev/
│   ├── SKILL.md
│   └── skill.json (generated)
├── quarkus-flow-dev/
│   ├── SKILL.md
│   ├── skill.json (generated)
│   └── funcDSL-reference.md
├── code-review-principles/
│   ├── SKILL.md
│   └── skill.json (generated)
├── scripts/
│   ├── validate_all.py
│   └── generate_skill_metadata.py (new)
├── CLAUDE.md
├── README.md
└── LICENSE
```

**Purpose:** Where you develop skills, run validation, commit changes

**Workflow:** Unchanged - existing git-commit, validation, testing all work as before

### Layer 2: Distribution (GitHub Monorepo)

**Published Monorepo:** `github.com/mdproctor/claude-skills`
- Same structure as Layer 1
- Tagged releases: `v1.0.0`, `v1.1.0`, `v1.2.0`
- Snapshot builds: `main` branch (latest)

**Registry Repository:** `github.com/mdproctor/claude-skill-registry`

Structure:
```
claude-skill-registry/
├── registry.json          # Central index
├── README.md              # Usage guide + publishing instructions
└── schemas/
    └── skill.schema.json  # Validation schema
```

**registry.json format:**
```json
{
  "version": "1.0",
  "updated": "2026-03-30T22:30:00Z",
  "skills": [
    {
      "name": "java-dev",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "java-dev",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "quarkus-flow-dev",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "quarkus-flow-dev",
      "defaultRef": "v1.2.0",
      "snapshotRef": "main"
    }
  ]
}
```

**Community skills:** Other authors can add their monorepos:
```json
{
  "name": "python-dev",
  "repository": "https://github.com/otheruser/python-skills",
  "path": "python-dev",
  "defaultRef": "v2.0.0",
  "snapshotRef": "develop"
}
```

### Layer 3: User Installation

**Location:** `~/.claude/skills/.marketplace/`

**Structure:**
```
~/.claude/skills/
├── .marketplace/              # Marketplace-installed (CLI-managed)
│   ├── java-dev/
│   │   ├── SKILL.md
│   │   └── skill.json
│   ├── quarkus-flow-dev/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   └── funcDSL-reference.md
│   └── code-review-principles/
│       ├── SKILL.md
│       └── skill.json
├── my-custom-skill/           # User's own skills (hand-managed)
│   └── SKILL.md
└── another-custom-skill/
    └── SKILL.md
```

**Key separation:**
- `.marketplace/` = CLI-managed, don't hand-edit
- Root level = user's custom skills, safe to edit

## Skill Packaging Format

### skill.json Metadata

**Minimal metadata (as decided):**

```json
{
  "name": "java-dev",
  "version": "1.0.0",
  "repository": "https://github.com/mdproctor/claude-skills",
  "dependencies": []
}
```

**With dependencies:**
```json
{
  "name": "quarkus-flow-dev",
  "version": "1.2.0",
  "repository": "https://github.com/mdproctor/claude-skills",
  "dependencies": [
    {
      "name": "java-dev",
      "repository": "https://github.com/mdproctor/claude-skills",
      "ref": "v1.0.0"
    }
  ]
}
```

**Snapshot version (during development):**
```json
{
  "name": "quarkus-flow-dev",
  "version": "1.3.0-SNAPSHOT",
  "repository": "https://github.com/mdproctor/claude-skills",
  "dependencies": [
    {
      "name": "java-dev",
      "repository": "https://github.com/mdproctor/claude-skills",
      "ref": "main"
    }
  ]
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Skill identifier (matches directory name and SKILL.md frontmatter) |
| `version` | string | Yes | Semver or semver-SNAPSHOT |
| `repository` | string | Yes | GitHub repository URL |
| `dependencies` | array | Yes | Array of dependency objects (empty if none) |
| `dependencies[].name` | string | Yes | Dependency skill name |
| `dependencies[].repository` | string | Yes | Dependency repository URL |
| `dependencies[].ref` | string | Yes | Git tag, branch, or commit SHA |

### Validation Rules

- `name` must match directory name and SKILL.md frontmatter
- `version` must be valid semver or semver-SNAPSHOT
- `dependencies` must reference existing skills
- Circular dependencies rejected
- All `ref` values must exist in repository

### Generation

**Automated via script:**
```bash
python scripts/generate_skill_metadata.py
```

**What it does:**
1. Scans all `*/SKILL.md` files
2. Extracts `name` from frontmatter
3. Generates `version` from current git tag (or SNAPSHOT if untagged)
4. Parses Prerequisites section:
   - Detects patterns like "This skill builds on [`java-dev`]"
   - Converts to dependency entries
5. Generates/updates `skill.json` in each directory
6. Validates no circular dependencies

**Example output:**
```bash
$ python scripts/generate_skill_metadata.py

Generating skill metadata...
  ✓ java-dev → skill.json (v1.0.0, 0 dependencies)
  ✓ quarkus-flow-dev → skill.json (v1.2.0, 1 dependency: java-dev)
  ✓ code-review-principles → skill.json (v1.0.0, 0 dependencies)
  ✓ quarkus-flow-testing → skill.json (v1.1.0, 2 dependencies: java-dev, quarkus-flow-dev)

Generated metadata for 20 skills.
Commit these changes before tagging release.
```

## CLI Design

### Command: `claude skill install <skill-name> [--snapshot]`

**Install stable version (default):**
```bash
$ claude skill install quarkus-flow-dev

Resolving dependencies...
  quarkus-flow-dev v1.2.0 requires:
    - java-dev v1.0.0

Installing dependencies:
  ✓ java-dev v1.0.0
  ✓ quarkus-flow-dev v1.2.0

Installed 2 skills to ~/.claude/skills/.marketplace/
```

**Install snapshot version:**
```bash
$ claude skill install quarkus-flow-dev --snapshot

Resolving dependencies...
  quarkus-flow-dev main (snapshot) requires:
    - java-dev main (snapshot)

⚠️  Warning: Snapshots may be unstable. Use stable releases for production.

Installing dependencies:
  ✓ java-dev main (snapshot)
  ✓ quarkus-flow-dev main (snapshot)

Installed 2 skills to ~/.claude/skills/.marketplace/
```

**Behavior:**
1. Fetch registry.json from GitHub
2. Find skill entry (name → repository + path + ref)
3. Download skill.json to inspect dependencies
4. Build dependency graph (topological sort)
5. Check for conflicts (same skill, different versions)
6. Download each skill via git sparse checkout (dependency-first order)
7. Validate SKILL.md + skill.json for each
8. Install to `.marketplace/<skill-name>/`
9. Report installation summary

**Error cases:**
- Skill not found in registry → error
- Dependency conflict → error with explanation
- Download fails → rollback partial install
- Validation fails → remove files, report error

### Command: `claude skill uninstall <skill-name>`

**Basic uninstall:**
```bash
$ claude skill uninstall java-dev

⚠️  Warning: The following skills depend on java-dev:
  - quarkus-flow-dev
  - java-code-review
  - quarkus-flow-testing

Uninstall anyway? (y/N): n
Cancelled.
```

**Forced uninstall:**
```bash
$ claude skill uninstall java-dev

⚠️  Warning: The following skills depend on java-dev:
  - quarkus-flow-dev
  - java-code-review
  - quarkus-flow-testing

Uninstall anyway? (y/N): y
Removing java-dev...
✓ Uninstalled java-dev from ~/.claude/skills/.marketplace/

⚠️  The following skills may not work correctly:
  - quarkus-flow-dev
  - java-code-review
  - quarkus-flow-testing
```

**Behavior:**
1. Check if skill exists in `.marketplace/`
2. Scan all other installed skills for dependencies
3. If dependencies found, warn and prompt
4. Remove skill directory
5. Report what was removed

### Command: `claude skill list`

**Output:**
```bash
$ claude skill list

Installed skills:
  code-review-principles  v1.0.0
  java-dev                v1.0.0
  java-code-review        v1.1.0  (depends on: code-review-principles, java-dev)
  quarkus-flow-dev        main (snapshot)  (depends on: java-dev)
  quarkus-flow-testing    v1.1.0  (depends on: java-dev, quarkus-flow-dev)

5 skills installed
```

**Behavior:**
1. Scan `.marketplace/` directory
2. Read skill.json from each skill
3. Display table: name, version, dependencies (sorted alphabetically)

## Dependency Resolution

### Resolution Algorithm

**When user runs `claude skill install quarkus-flow-dev`:**

1. **Fetch registry entry:**
   - Read registry.json from GitHub
   - Find `quarkus-flow-dev` entry
   - Get repository URL, path, defaultRef

2. **Download metadata:**
   - Use git sparse checkout to download `quarkus-flow-dev/skill.json` only
   - Parse dependencies array

3. **Recursive dependency fetching:**
   ```
   quarkus-flow-dev v1.2.0
     └─ java-dev v1.0.0
          └─ (no dependencies)
   ```
   - Fetch `java-dev/skill.json`
   - Continue recursively until all dependencies resolved

4. **Conflict detection:**
   - Build dependency tree
   - Check for version conflicts (same skill, different refs)
   - **If conflict found:** Error and abort
   - **No version range resolution in v1** - exact match only

5. **Topological sort:**
   - Order: `java-dev` first, then `quarkus-flow-dev`
   - Ensures dependencies installed before dependents

6. **Installation:**
   - For each skill in sorted order:
     - Download via git sparse checkout
     - Validate SKILL.md + skill.json
     - Copy to `.marketplace/<skill-name>/`

7. **Success report:**
   - List all installed skills with versions

### Conflict Handling (v1)

**Scenario: Two skills require different versions of same dependency**

```bash
$ claude skill install quarkus-flow-dev
# Requires java-dev v1.0.0

$ claude skill install some-other-skill
# Requires java-dev v2.0.0
```

**CLI behavior:**
```
❌ Conflict detected:
  quarkus-flow-dev requires java-dev v1.0.0
  some-other-skill requires java-dev v2.0.0

Cannot install multiple versions of the same skill.

Solutions:
  1. Check if skills have newer versions with compatible dependencies
  2. Install only one of the conflicting skills
  3. Contact skill authors to align dependency versions

Installation aborted.
```

**For v1: Reject conflicts, require manual resolution.**

(Future enhancement: Version ranges, multiple versions in isolated namespaces)

### Dependency Reference Format

**Git references in dependencies:**
- **Tag:** `"v1.0.0"`, `"v2.1.3"` (recommended for stability)
- **Branch:** `"main"`, `"develop"` (snapshots)
- **Commit SHA:** `"a1b2c3d4e5f6..."` (pinning to exact state)

**Examples:**

**Stable dependency:**
```json
"dependencies": [
  {
    "name": "java-dev",
    "repository": "https://github.com/mdproctor/claude-skills",
    "ref": "v1.0.0"
  }
]
```

**Snapshot dependency:**
```json
"dependencies": [
  {
    "name": "java-dev",
    "repository": "https://github.com/mdproctor/claude-skills",
    "ref": "main"
  }
]
```

**Pinned to commit:**
```json
"dependencies": [
  {
    "name": "java-dev",
    "repository": "https://github.com/mdproctor/claude-skills",
    "ref": "a1b2c3d4e5f67890abcdef1234567890abcdef12"
  }
]
```

## Installation Mechanism

### Git Sparse Checkout Strategy

**Why sparse checkout:**
- Downloads only specific subdirectory from monorepo
- Avoids cloning entire repository (saves bandwidth, time)
- Native git feature, well-supported and reliable
- Works with any git hosting (GitHub, GitLab, etc.)

### Installation Process for Single Skill

**Installing `java-dev v1.0.0`:**

```bash
# 1. Create temporary directory
TEMP_DIR=$(mktemp -d /tmp/claude-skill-install-XXXXXX)
cd $TEMP_DIR

# 2. Initialize git repo
git init

# 3. Add remote
git remote add origin https://github.com/mdproctor/claude-skills

# 4. Enable sparse checkout
git config core.sparseCheckout true

# 5. Specify path to download (only java-dev subdirectory)
echo "java-dev/*" > .git/info/sparse-checkout

# 6. Fetch specific ref (tag v1.0.0)
git fetch --depth=1 origin v1.0.0

# 7. Checkout files
git checkout v1.0.0

# 8. Validate
if [ ! -f java-dev/SKILL.md ]; then
  echo "Error: SKILL.md not found"
  exit 1
fi

if [ ! -f java-dev/skill.json ]; then
  echo "Error: skill.json not found"
  exit 1
fi

# 9. Copy to final location
INSTALL_DIR="$HOME/.claude/skills/.marketplace/java-dev"
mkdir -p "$INSTALL_DIR"
cp -r java-dev/* "$INSTALL_DIR/"

# 10. Cleanup temp directory
cd /
rm -rf "$TEMP_DIR"

echo "✓ Installed java-dev v1.0.0"
```

### Installation Directory Structure

**Before installation:**
```
~/.claude/skills/
├── my-custom-skill/
│   └── SKILL.md
└── another-skill/
    └── SKILL.md
```

**After `claude skill install quarkus-flow-dev` (with dependencies):**
```
~/.claude/skills/
├── .marketplace/              # NEW: Marketplace-installed skills
│   ├── java-dev/              # Dependency, auto-installed
│   │   ├── SKILL.md
│   │   └── skill.json
│   └── quarkus-flow-dev/      # Requested skill
│       ├── SKILL.md
│       ├── skill.json
│       └── funcDSL-reference.md
├── my-custom-skill/           # User's custom skills (unchanged)
│   └── SKILL.md
└── another-skill/
    └── SKILL.md
```

**Key points:**
- `.marketplace/` is auto-created on first install
- Each skill gets its own subdirectory
- Supporting files (like funcDSL-reference.md) copied if present
- User's custom skills remain in root, unaffected

### Validation After Installation

**Each installed skill is validated:**

1. ✅ **SKILL.md exists**
   - Check file presence
   - Validate YAML frontmatter (name field required)

2. ✅ **skill.json exists**
   - Check file presence
   - Validate JSON syntax
   - Validate schema (name, version, repository, dependencies fields)

3. ✅ **Name consistency**
   - skill.json name matches directory name
   - SKILL.md frontmatter name matches skill.json name

4. ✅ **No file conflicts**
   - Skill directory doesn't already exist (unless upgrading)
   - No partial installations from failed previous attempts

**If validation fails:**
- Rollback: Remove partially installed files
- Report specific error to user
- Do not leave broken state

**Example validation error:**
```bash
$ claude skill install broken-skill

Downloading broken-skill v1.0.0...
✓ Downloaded

Validating...
❌ Validation failed: SKILL.md frontmatter missing 'name' field

Cleaning up...
Installation aborted.
```

## Publishing Workflow

### Versioning Strategy

**Two tracks:**

1. **Stable releases** - Tagged versions
   - Format: `v1.0.0`, `v1.1.0`, `v2.0.0` (semver)
   - For published, tested versions
   - Recommended for production use
   - Listed in registry as `defaultRef`

2. **Snapshot builds** - Branch references
   - Format: `main`, `develop`, `feature-xyz`
   - Latest commits, may be unstable
   - For active development and rapid iteration
   - Listed in registry as `snapshotRef`

**Why snapshots:**
- Avoid version number bloat during rapid development
- Users can opt-in to bleeding edge
- Smooth path from development to stable release

### Developer Workflow (Your Perspective)

**Step 1: Develop skills in monorepo**
```bash
# Your development location (flexible, NOT ~/.claude/skills)
cd ~/projects/claude-skills/

# Make changes
vim java-dev/SKILL.md
vim java-dev/SKILL.md

# Commit to main (no tagging yet)
git add java-dev/
git commit -m "feat(java-dev): add new safety pattern"
git push origin main

# Users on snapshots get this immediately via 'main' branch
```

**Step 2: Generate skill.json metadata (before release)**
```bash
# Run metadata generator script
python scripts/generate_skill_metadata.py

# Output:
# Generating skill metadata...
#   ✓ java-dev → skill.json (v1.0.0, 0 dependencies)
#   ✓ quarkus-flow-dev → skill.json (v1.2.0, 1 dependency: java-dev)
#   ...
# Generated metadata for 20 skills.
# Commit these changes before tagging release.

# Commit generated metadata
git add */skill.json
git commit -m "build: generate skill metadata for v1.3.0"
```

**Step 3: Tag stable release**
```bash
# Tag the monorepo
git tag v1.3.0
git push origin main --tags

# This creates a stable reference users can install
```

**Step 4: Update registry**
```bash
# Clone registry repo
cd ~/projects/
git clone https://github.com/mdproctor/claude-skill-registry
cd claude-skill-registry

# Edit registry.json
vim registry.json

# Update defaultRef for changed skills:
# "defaultRef": "v1.2.0" → "v1.3.0"

# Commit and push (or submit PR if collaborative)
git add registry.json
git commit -m "feat: publish v1.3.0 release"
git push origin main
```

### Metadata Generation Script

**What `generate_skill_metadata.py` does:**

1. **Scan for skills:**
   - Find all directories with `SKILL.md` files
   - Exclude `.git/`, `docs/`, `scripts/`, etc.

2. **Extract metadata:**
   - Parse SKILL.md frontmatter for `name`
   - Determine version from git tags (or SNAPSHOT if untagged)
   - Parse Prerequisites section for dependencies

3. **Dependency detection:**
   - Search for patterns: `builds on [\`java-dev\`]`
   - Extract skill names from backtick references
   - Look up referenced skills for repository URL

4. **Generate skill.json:**
   - Create/update skill.json in each directory
   - Include name, version, repository, dependencies

5. **Validation:**
   - Check for circular dependencies
   - Ensure all referenced dependencies exist
   - Validate JSON syntax

6. **Output:**
   - Report what was generated
   - Flag any errors or warnings

**Example run:**
```bash
$ python scripts/generate_skill_metadata.py

Scanning for skills...
Found 20 skills

Analyzing dependencies...
  java-dev: no dependencies
  quarkus-flow-dev: depends on java-dev
  quarkus-flow-testing: depends on java-dev, quarkus-flow-dev
  java-code-review: depends on code-review-principles, java-dev
  ...

Generating skill.json files...
  ✓ code-review-principles/skill.json (v1.0.0, 0 deps)
  ✓ java-dev/skill.json (v1.0.0, 0 deps)
  ✓ quarkus-flow-dev/skill.json (v1.2.0, 1 dep)
  ✓ quarkus-flow-testing/skill.json (v1.1.0, 2 deps)
  ...

Generated metadata for 20 skills.
No errors detected.

Next steps:
  1. Review generated skill.json files
  2. Commit changes: git add */skill.json && git commit -m "build: generate skill metadata"
  3. Tag release: git tag v1.3.0 && git push --tags
  4. Update registry defaultRef to v1.3.0
```

### Publishing Checklist

**Before publishing a new stable release:**

- [ ] All skills have valid SKILL.md frontmatter
- [ ] Run validation: `python scripts/validate_all.py`
- [ ] All validation passes (no CRITICAL/WARNING)
- [ ] Generate metadata: `python scripts/generate_skill_metadata.py`
- [ ] Review generated skill.json files
- [ ] Commit metadata: `git add */skill.json && git commit -m "build: generate skill metadata for vX.Y.Z"`
- [ ] Tag release: `git tag vX.Y.Z`
- [ ] Push tags: `git push origin main --tags`
- [ ] Update registry: Edit `registry.json`, update `defaultRef` to new tag
- [ ] Submit registry PR (or push if you have access)
- [ ] Verify installation: `claude skill install <skill-name>` (test locally)

### Snapshot Workflow (Rapid Development)

**During active development:**
```bash
# Work on feature
vim java-dev/SKILL.md
git commit -m "wip: experimenting with new pattern"
git push origin main

# No tagging, no metadata generation needed
# 'main' branch is the snapshot
# Users running --snapshot get updates immediately
```

**When feature stabilizes:**
```bash
# Generate metadata (updates to non-SNAPSHOT version)
python scripts/generate_skill_metadata.py --release

# This changes skill.json:
# "version": "1.3.0-SNAPSHOT" → "version": "1.3.0"

git add */skill.json
git commit -m "release: v1.3.0"
git tag v1.3.0
git push origin main --tags

# Update registry defaultRef
```

## Migration Strategy

### Phase 1: Preparation (Current Monorepo)

**No changes to current workflow yet.**

1. ✅ Choose development location (e.g., `~/projects/claude-skills/`)
2. ✅ Move current `~/.claude/skills/` to development location (if desired)
3. ✅ Continue development as normal

### Phase 2: Add Packaging (Monorepo Enhancement)

**Add marketplace metadata to existing skills.**

1. **Create metadata generation script:**
   - `scripts/generate_skill_metadata.py`
   - Implement dependency parsing from Prerequisites sections
   - Implement skill.json generation

2. **Generate initial metadata:**
   ```bash
   python scripts/generate_skill_metadata.py
   # Generates skill.json for all 20+ skills
   ```

3. **Validate generated metadata:**
   ```bash
   git diff  # Review all skill.json files
   # Check dependencies are correct
   # Verify no circular dependencies
   ```

4. **Commit metadata:**
   ```bash
   git add */skill.json
   git commit -m "build: add skill.json metadata for marketplace"
   ```

### Phase 3: Create Registry

**Set up the central registry repository.**

1. **Create registry repo:**
   ```bash
   mkdir claude-skill-registry
   cd claude-skill-registry
   git init
   ```

2. **Create registry.json:**
   - List all skills from monorepo
   - Set initial versions (all stable releases or all snapshots)
   - Include repository URLs

3. **Add documentation:**
   - README.md: How to use the marketplace
   - README.md: How to publish skills
   - schemas/skill.schema.json: Validation schema

4. **Publish registry:**
   ```bash
   git add .
   git commit -m "feat: initial skill registry"
   # Push to github.com/mdproctor/claude-skill-registry
   ```

### Phase 4: Build CLI Tool

**Implement the marketplace CLI.**

1. **CLI implementation:**
   - `claude skill install <name>`
   - `claude skill uninstall <name>`
   - `claude skill list`
   - Registry fetching
   - Git sparse checkout installation
   - Dependency resolution

2. **Testing:**
   - Test installation of individual skills
   - Test dependency resolution
   - Test snapshot vs stable installation
   - Test uninstall with dependency warnings
   - Test conflict detection

3. **Integration:**
   - Ensure CLI integrates with Claude Code harness
   - Verify installed skills from `.marketplace/` are loaded
   - Test interaction with custom user skills

### Phase 5: Migration (User Perspective)

**How users migrate from monorepo to marketplace:**

**Option A: Fresh start (recommended)**
```bash
# Backup existing skills
mv ~/.claude/skills ~/.claude/skills.backup

# Install only what you need
claude skill install java-dev
claude skill install quarkus-flow-dev

# Restore custom skills
cp -r ~/.claude/skills.backup/my-custom-skill ~/.claude/skills/
```

**Option B: Hybrid approach**
```bash
# Keep existing monorepo skills in place
# Install marketplace skills to .marketplace/
claude skill install python-dev  # From community

# Both sets of skills coexist
```

**Option C: Full monorepo install (power users)**
```bash
# Clone full monorepo to ~/.claude/skills/
git clone https://github.com/mdproctor/claude-skills ~/.claude/skills/development

# Use all skills from development directory
```

## Security Considerations

### Code Execution Risk

**Skills are code** - they guide Claude's behavior and can be malicious.

**Mitigations:**
1. **Manual registry curation** - Only trusted skills in official registry
2. **GitHub-based trust** - Users can inspect source before installing
3. **No automatic code execution** - Skills are markdown, not executable
4. **Review before install** - CLI shows what will be installed

### Supply Chain Attacks

**Risk:** Malicious actor compromises skill repository, pushes malicious update

**Mitigations:**
1. **Git commit signing** - Verify author identity (future enhancement)
2. **Snapshot warnings** - Warn users snapshots are less stable
3. **Version pinning** - Users control when to upgrade
4. **Manual registry updates** - New skills/versions reviewed before registry update

### Dependency Confusion

**Risk:** Attacker creates skill with same name in different repository

**Mitigations:**
1. **Registry as source of truth** - CLI only installs from registry-listed repos
2. **Name uniqueness** - Registry enforces unique skill names
3. **Repository URL in metadata** - Full qualification prevents confusion

## Future Enhancements (Out of Scope for v1)

### Version Range Support
```json
"dependencies": [
  {
    "name": "java-dev",
    "repository": "https://github.com/mdproctor/claude-skills",
    "ref": "^1.0.0"  // Any 1.x version
  }
]
```

### Skill Search
```bash
claude skill search quarkus
# Shows all skills matching "quarkus"
```

### Update Detection
```bash
claude skill outdated
# Shows skills with newer versions available
```

### Hosted Registry API
- Web UI for browsing skills
- Download statistics
- Skill ratings/reviews
- Automated publishing via GitHub Actions

### Multi-Version Support
- Install multiple versions side-by-side
- Namespace isolation
- Per-project skill configurations

## Success Criteria

**v1 is successful when:**

1. ✅ Users can install individual skills via CLI
2. ✅ Dependencies auto-resolve and install
3. ✅ Snapshot and stable versions both work
4. ✅ Users can uninstall skills cleanly
5. ✅ Community members can publish skills to registry
6. ✅ Developer workflow unchanged (continue in monorepo)
7. ✅ No disruption to existing monorepo users
8. ✅ Documentation clear for both publishing and installing

**Metrics:**
- Time to install skill: <30 seconds (including dependencies)
- Zero conflicts for skills in official registry
- All 20+ existing skills packaged and installable
- At least 1 community-published skill within 3 months

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Git sparse checkout doesn't work on all platforms | High | Low | Test on macOS, Linux, Windows; fallback to full clone if needed |
| Registry becomes stale, out of sync with repos | Medium | Medium | Automate registry updates via GitHub Actions (future) |
| Dependency conflicts become common | High | Medium | Enforce compatibility testing before registry acceptance |
| Users accidentally install untrusted skills | High | Low | Manual registry curation, clear warnings in CLI |
| Metadata generation script has bugs | Medium | Medium | Comprehensive testing, validation against known-good data |
| CLI complexity overwhelms simple use cases | Low | Low | Keep CLI minimal (3 commands), defer advanced features |

## Open Questions

None - all questions resolved during brainstorming phase.

## Appendix: Examples

### Example 1: Installing a Skill with Dependencies

```bash
$ claude skill install quarkus-flow-testing

Fetching registry...
✓ Registry loaded

Resolving dependencies...
  quarkus-flow-testing v1.1.0 requires:
    - java-dev v1.0.0
    - quarkus-flow-dev v1.2.0
  quarkus-flow-dev v1.2.0 requires:
    - java-dev v1.0.0

Installation plan:
  1. java-dev v1.0.0
  2. quarkus-flow-dev v1.2.0
  3. quarkus-flow-testing v1.1.0

Proceed? (Y/n): y

Installing java-dev v1.0.0...
✓ Downloaded from https://github.com/mdproctor/claude-skills
✓ Validated
✓ Installed to ~/.claude/skills/.marketplace/java-dev/

Installing quarkus-flow-dev v1.2.0...
✓ Downloaded from https://github.com/mdproctor/claude-skills
✓ Validated
✓ Installed to ~/.claude/skills/.marketplace/quarkus-flow-dev/

Installing quarkus-flow-testing v1.1.0...
✓ Downloaded from https://github.com/mdproctor/claude-skills
✓ Validated
✓ Installed to ~/.claude/skills/.marketplace/quarkus-flow-testing/

Successfully installed 3 skills.
```

### Example 2: Publishing a New Skill

**Developer creates a new skill in monorepo:**

```bash
cd ~/projects/claude-skills/

# Create new skill directory
mkdir python-dev
cd python-dev

# Write SKILL.md
cat > SKILL.md <<EOF
---
name: python-dev
description: >
  Use when writing Python code, debugging, or refactoring.
---

# Python Development

Expert Python development with focus on...
EOF

# Generate metadata
cd ..
python scripts/generate_skill_metadata.py

# Output:
# Scanning for skills...
# Found 21 skills (new: python-dev)
#
# Generating skill.json files...
#   ✓ python-dev/skill.json (v1.0.0-SNAPSHOT, 0 deps)
#   ...

# Commit
git add python-dev/
git commit -m "feat(python-dev): initial Python development skill"
git push origin main

# Tag stable release when ready
git tag v1.4.0
git push origin main --tags

# Update registry
cd ~/projects/claude-skill-registry/
vim registry.json
# Add:
# {
#   "name": "python-dev",
#   "repository": "https://github.com/mdproctor/claude-skills",
#   "path": "python-dev",
#   "defaultRef": "v1.4.0",
#   "snapshotRef": "main"
# }

git add registry.json
git commit -m "feat: add python-dev skill v1.4.0"
git push origin main
```

### Example 3: Community Member Publishing Skill

**External contributor:**

```bash
# Create their own skills monorepo
mkdir python-skills
cd python-skills

# Create skill
mkdir python-testing
cd python-testing
# ... create SKILL.md, skill.json ...

# Publish to their GitHub
git init
git add .
git commit -m "feat: initial release"
git remote add origin https://github.com/otheruser/python-skills
git push -u origin main
git tag v1.0.0
git push --tags

# Submit PR to registry
# Fork github.com/mdproctor/claude-skill-registry
# Add entry to registry.json:
# {
#   "name": "python-testing",
#   "repository": "https://github.com/otheruser/python-skills",
#   "path": "python-testing",
#   "defaultRef": "v1.0.0",
#   "snapshotRef": "main"
# }

# Submit PR → reviewed → merged → available in marketplace
```

Users can now install:
```bash
claude skill install python-testing
```

## Conclusion

This design enables a granular, user-controlled marketplace for Claude Code skills while preserving the monorepo development workflow. The hybrid approach (monorepo source + individual distribution) balances developer productivity with user flexibility.

**Next steps:** Write implementation plan covering CLI tool development, metadata generation script, registry setup, and migration guide.
