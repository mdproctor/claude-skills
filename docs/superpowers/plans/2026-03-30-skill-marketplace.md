# Skill Marketplace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI-based marketplace enabling users to install individual skills from a monorepo with automatic dependency resolution.

**Architecture:** Three-layer system - development monorepo (source of truth), published monorepo + registry (distribution), user installation directory (consumption). CLI uses git sparse checkout for granular installation.

**Tech Stack:** Python 3.9+, git CLI, JSON for metadata/registry, pytest for testing

---

## File Structure

**New files to create:**
- `scripts/generate_skill_metadata.py` - Generates skill.json for all skills
- `scripts/marketplace/__init__.py` - Package marker
- `scripts/marketplace/cli.py` - CLI entry point (install/uninstall/list)
- `scripts/marketplace/registry.py` - Registry fetch/parse operations
- `scripts/marketplace/installer.py` - Git sparse checkout installation
- `scripts/marketplace/dependency_resolver.py` - Dependency graph resolution
- `scripts/marketplace/validator.py` - Skill validation
- `tests/marketplace/__init__.py` - Test package marker
- `tests/marketplace/test_metadata_generator.py` - Metadata generation tests
- `tests/marketplace/test_registry.py` - Registry operation tests
- `tests/marketplace/test_installer.py` - Installation tests
- `tests/marketplace/test_dependency_resolver.py` - Dependency resolution tests
- `tests/marketplace/test_validator.py` - Validation tests
- `tests/marketplace/test_cli_integration.py` - End-to-end CLI tests
- `tests/marketplace/fixtures/` - Test fixtures (sample registry, skills)

**Files to modify:**
- None (all new functionality)

---

### Task 1: Metadata Generation - Skill Scanner

**Files:**
- Create: `scripts/generate_skill_metadata.py`
- Test: `tests/marketplace/test_metadata_generator.py`

- [ ] **Step 1: Write failing test for skill scanning**

```python
# tests/marketplace/test_metadata_generator.py
import pytest
from pathlib import Path
import tempfile
import shutil

def test_scan_finds_skill_directories():
    """Scanner should find directories containing SKILL.md files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test skill directories
        (tmpdir / "java-dev").mkdir()
        (tmpdir / "java-dev" / "SKILL.md").write_text("---\nname: java-dev\n---\n")

        (tmpdir / "quarkus-flow-dev").mkdir()
        (tmpdir / "quarkus-flow-dev" / "SKILL.md").write_text("---\nname: quarkus-flow-dev\n---\n")

        # Create non-skill directory (should be excluded)
        (tmpdir / "scripts").mkdir()
        (tmpdir / "scripts" / "test.py").write_text("# not a skill")

        from scripts.generate_skill_metadata import scan_for_skills

        skills = scan_for_skills(tmpdir)

        assert len(skills) == 2
        assert tmpdir / "java-dev" in skills
        assert tmpdir / "quarkus-flow-dev" in skills
        assert tmpdir / "scripts" not in skills
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_scan_finds_skill_directories -v`
Expected: `ModuleNotFoundError: No module named 'scripts.generate_skill_metadata'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/generate_skill_metadata.py
from pathlib import Path
from typing import List

def scan_for_skills(root_dir: Path) -> List[Path]:
    """
    Scan directory for skill directories (containing SKILL.md).

    Excludes: .git, docs, scripts, tests, __pycache__
    """
    excluded_dirs = {'.git', 'docs', 'scripts', 'tests', '__pycache__', '.claude'}
    skills = []

    for item in root_dir.iterdir():
        if not item.is_dir():
            continue
        if item.name in excluded_dirs:
            continue
        if (item / "SKILL.md").exists():
            skills.append(item)

    return sorted(skills)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_scan_finds_skill_directories -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_skill_metadata.py tests/marketplace/test_metadata_generator.py
git commit -m "feat(marketplace): add skill scanner for metadata generation"
```

---

### Task 2: Metadata Generation - Frontmatter Parser

**Files:**
- Modify: `scripts/generate_skill_metadata.py`
- Test: `tests/marketplace/test_metadata_generator.py`

- [ ] **Step 1: Write failing test for frontmatter parsing**

```python
# tests/marketplace/test_metadata_generator.py (add to existing file)
def test_parse_frontmatter_extracts_name():
    """Parser should extract name from SKILL.md frontmatter"""
    skill_md = """---
name: java-dev
description: >
  Use when writing Java code
---

# Java Development

Content here...
"""
    from scripts.generate_skill_metadata import parse_frontmatter

    name = parse_frontmatter(skill_md)

    assert name == "java-dev"


def test_parse_frontmatter_raises_on_missing_name():
    """Parser should raise error if name field missing"""
    skill_md = """---
description: No name field
---
"""
    from scripts.generate_skill_metadata import parse_frontmatter

    with pytest.raises(ValueError, match="Missing 'name' field"):
        parse_frontmatter(skill_md)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_parse_frontmatter -v`
Expected: `AttributeError: module has no attribute 'parse_frontmatter'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/generate_skill_metadata.py (add to existing file)
import re

def parse_frontmatter(skill_md_content: str) -> str:
    """
    Parse SKILL.md frontmatter to extract name.

    Args:
        skill_md_content: Full SKILL.md file content

    Returns:
        Skill name from frontmatter

    Raises:
        ValueError: If frontmatter missing or name field not found
    """
    # Extract frontmatter between --- markers
    match = re.match(r'^---\s*\n(.*?)\n---', skill_md_content, re.DOTALL)
    if not match:
        raise ValueError("No frontmatter found in SKILL.md")

    frontmatter = match.group(1)

    # Extract name field
    name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    if not name_match:
        raise ValueError("Missing 'name' field in frontmatter")

    return name_match.group(1).strip()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_parse_frontmatter -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_skill_metadata.py tests/marketplace/test_metadata_generator.py
git commit -m "feat(marketplace): add frontmatter parser for skill name"
```

---

### Task 3: Metadata Generation - Dependency Parser

**Files:**
- Modify: `scripts/generate_skill_metadata.py`
- Test: `tests/marketplace/test_metadata_generator.py`

- [ ] **Step 1: Write failing test for dependency parsing**

```python
# tests/marketplace/test_metadata_generator.py (add to existing file)
def test_parse_dependencies_finds_single_dependency():
    """Parser should extract dependencies from Prerequisites section"""
    skill_md = """---
name: quarkus-flow-dev
---

## Prerequisites

**This skill builds on [`java-dev`]**.

Apply all rules from java-dev.
"""
    from scripts.generate_skill_metadata import parse_dependencies

    deps = parse_dependencies(skill_md)

    assert deps == ["java-dev"]


def test_parse_dependencies_finds_multiple_dependencies():
    """Parser should extract multiple dependencies"""
    skill_md = """---
name: quarkus-flow-testing
---

## Prerequisites

**This skill builds on [`java-dev`] and [`quarkus-flow-dev`]**.
"""
    from scripts.generate_skill_metadata import parse_dependencies

    deps = parse_dependencies(skill_md)

    assert set(deps) == {"java-dev", "quarkus-flow-dev"}


def test_parse_dependencies_returns_empty_for_no_prereqs():
    """Parser should return empty list if no Prerequisites section"""
    skill_md = """---
name: java-dev
---

# Java Development

No prerequisites.
"""
    from scripts.generate_skill_metadata import parse_dependencies

    deps = parse_dependencies(skill_md)

    assert deps == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_parse_dependencies -v`
Expected: `AttributeError: module has no attribute 'parse_dependencies'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/generate_skill_metadata.py (add to existing file)
def parse_dependencies(skill_md_content: str) -> List[str]:
    """
    Parse SKILL.md to extract dependency skill names.

    Looks for Prerequisites section with patterns like:
    - "builds on [`java-dev`]"
    - "extends [`code-review-principles`]"

    Args:
        skill_md_content: Full SKILL.md file content

    Returns:
        List of dependency skill names
    """
    # Find Prerequisites section
    prereq_match = re.search(
        r'^## Prerequisites\s*\n(.*?)(?=^##|\Z)',
        skill_md_content,
        re.MULTILINE | re.DOTALL
    )

    if not prereq_match:
        return []

    prereq_section = prereq_match.group(1)

    # Extract skill names from backtick references: [`skill-name`]
    dependencies = re.findall(r'\[`([^`]+)`\]', prereq_section)

    return dependencies
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_parse_dependencies -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_skill_metadata.py tests/marketplace/test_metadata_generator.py
git commit -m "feat(marketplace): add dependency parser from Prerequisites section"
```

---

### Task 4: Metadata Generation - skill.json Generator

**Files:**
- Modify: `scripts/generate_skill_metadata.py`
- Test: `tests/marketplace/test_metadata_generator.py`

- [ ] **Step 1: Write failing test for skill.json generation**

```python
# tests/marketplace/test_metadata_generator.py (add to existing file)
import json

def test_generate_skill_json_creates_metadata():
    """Generator should create valid skill.json file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create skill directory with SKILL.md
        skill_dir = tmpdir / "java-dev"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: java-dev
---

# Java Development
""")

        from scripts.generate_skill_metadata import generate_skill_json

        generate_skill_json(
            skill_dir=skill_dir,
            repository_url="https://github.com/mdproctor/claude-skills",
            version="1.0.0",
            dependencies=[]
        )

        # Verify skill.json created
        skill_json_path = skill_dir / "skill.json"
        assert skill_json_path.exists()

        # Verify content
        with open(skill_json_path) as f:
            data = json.load(f)

        assert data == {
            "name": "java-dev",
            "version": "1.0.0",
            "repository": "https://github.com/mdproctor/claude-skills",
            "dependencies": []
        }


def test_generate_skill_json_includes_dependencies():
    """Generator should include dependency references"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        skill_dir = tmpdir / "quarkus-flow-dev"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: quarkus-flow-dev
---

## Prerequisites

**This skill builds on [`java-dev`]**.
""")

        from scripts.generate_skill_metadata import generate_skill_json

        generate_skill_json(
            skill_dir=skill_dir,
            repository_url="https://github.com/mdproctor/claude-skills",
            version="1.2.0",
            dependencies=[
                {
                    "name": "java-dev",
                    "repository": "https://github.com/mdproctor/claude-skills",
                    "ref": "v1.0.0"
                }
            ]
        )

        skill_json_path = skill_dir / "skill.json"
        with open(skill_json_path) as f:
            data = json.load(f)

        assert data["dependencies"] == [
            {
                "name": "java-dev",
                "repository": "https://github.com/mdproctor/claude-skills",
                "ref": "v1.0.0"
            }
        ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_generate_skill_json -v`
Expected: `AttributeError: module has no attribute 'generate_skill_json'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/generate_skill_metadata.py (add to existing file)
import json
from typing import Dict, Any

def generate_skill_json(
    skill_dir: Path,
    repository_url: str,
    version: str,
    dependencies: List[Dict[str, str]]
) -> None:
    """
    Generate skill.json metadata file.

    Args:
        skill_dir: Path to skill directory
        repository_url: GitHub repository URL
        version: Skill version (semver or semver-SNAPSHOT)
        dependencies: List of dependency objects with name, repository, ref
    """
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_content = skill_md_path.read_text()

    # Extract name from frontmatter
    name = parse_frontmatter(skill_md_content)

    # Create metadata object
    metadata = {
        "name": name,
        "version": version,
        "repository": repository_url,
        "dependencies": dependencies
    }

    # Write skill.json
    skill_json_path = skill_dir / "skill.json"
    with open(skill_json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_generate_skill_json -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_skill_metadata.py tests/marketplace/test_metadata_generator.py
git commit -m "feat(marketplace): add skill.json generator"
```

---

### Task 5: Metadata Generation - Main CLI

**Files:**
- Modify: `scripts/generate_skill_metadata.py`
- Test: `tests/marketplace/test_metadata_generator.py`

- [ ] **Step 1: Write failing test for main function**

```python
# tests/marketplace/test_metadata_generator.py (add to existing file)
def test_main_generates_metadata_for_all_skills():
    """Main function should generate skill.json for all discovered skills"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create multiple skills
        for skill_name in ["java-dev", "quarkus-flow-dev"]:
            skill_dir = tmpdir / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"""---
name: {skill_name}
---

# Skill
""")

        from scripts.generate_skill_metadata import main

        # Run main with test directory
        result = main(
            root_dir=tmpdir,
            repository_url="https://github.com/test/repo",
            version="1.0.0"
        )

        # Verify skill.json created for each
        assert (tmpdir / "java-dev" / "skill.json").exists()
        assert (tmpdir / "quarkus-flow-dev" / "skill.json").exists()

        # Verify return value
        assert result == 2  # Number of skills processed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_main_generates_metadata -v`
Expected: `AttributeError: module has no attribute 'main'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/generate_skill_metadata.py (add to existing file)
import sys

def main(
    root_dir: Path = None,
    repository_url: str = "https://github.com/mdproctor/claude-skills",
    version: str = "1.0.0-SNAPSHOT"
) -> int:
    """
    Generate skill.json metadata for all skills in repository.

    Args:
        root_dir: Root directory to scan (default: script parent directory)
        repository_url: GitHub repository URL
        version: Default version for skills

    Returns:
        Number of skills processed
    """
    if root_dir is None:
        root_dir = Path(__file__).parent.parent

    print(f"Scanning for skills in {root_dir}...")
    skills = scan_for_skills(root_dir)
    print(f"Found {len(skills)} skills\n")

    if not skills:
        print("No skills found.")
        return 0

    print("Generating skill metadata...")

    for skill_dir in skills:
        skill_md_path = skill_dir / "SKILL.md"
        skill_md_content = skill_md_path.read_text()

        # Extract name
        name = parse_frontmatter(skill_md_content)

        # Extract dependencies
        dep_names = parse_dependencies(skill_md_content)

        # Build dependency objects (simplified for v1 - all same repo, version TBD)
        dependencies = [
            {
                "name": dep_name,
                "repository": repository_url,
                "ref": "main"  # Snapshot for now
            }
            for dep_name in dep_names
        ]

        # Generate skill.json
        generate_skill_json(
            skill_dir=skill_dir,
            repository_url=repository_url,
            version=version,
            dependencies=dependencies
        )

        deps_str = f", {len(dependencies)} dependencies" if dependencies else ", 0 dependencies"
        print(f"  ✓ {name}/skill.json (v{version}{deps_str})")

    print(f"\nGenerated metadata for {len(skills)} skills.")
    return len(skills)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/marketplace/test_metadata_generator.py::test_main_generates_metadata -v`
Expected: PASS

- [ ] **Step 5: Test manually**

Run: `cd /Users/mdproctor/.claude/skills && python scripts/generate_skill_metadata.py`
Expected: Output showing all skills with generated skill.json files

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_skill_metadata.py tests/marketplace/test_metadata_generator.py
git commit -m "feat(marketplace): add main CLI for metadata generation"
```

---

### Task 6: Registry Operations - Fetcher

**Files:**
- Create: `scripts/marketplace/registry.py`
- Test: `tests/marketplace/test_registry.py`

- [ ] **Step 1: Write failing test for registry fetching**

```python
# tests/marketplace/test_registry.py
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

def test_fetch_registry_downloads_from_github():
    """Fetcher should download registry.json from GitHub raw URL"""
    mock_response = Mock()
    mock_response.text = json.dumps({
        "version": "1.0",
        "updated": "2026-03-30T22:30:00Z",
        "skills": []
    })
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response) as mock_get:
        from scripts.marketplace.registry import fetch_registry

        registry = fetch_registry()

        # Verify correct URL called
        mock_get.assert_called_once_with(
            "https://raw.githubusercontent.com/mdproctor/claude-skill-registry/main/registry.json",
            timeout=30
        )

        # Verify parsed data
        assert registry["version"] == "1.0"
        assert "skills" in registry


def test_fetch_registry_raises_on_network_error():
    """Fetcher should raise clear error on network failure"""
    with patch('requests.get', side_effect=Exception("Network error")):
        from scripts.marketplace.registry import fetch_registry

        with pytest.raises(RuntimeError, match="Failed to fetch registry"):
            fetch_registry()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_registry.py::test_fetch_registry -v`
Expected: `ModuleNotFoundError: No module named 'scripts.marketplace.registry'`

- [ ] **Step 3: Create package structure**

```bash
mkdir -p scripts/marketplace
touch scripts/marketplace/__init__.py
mkdir -p tests/marketplace
touch tests/marketplace/__init__.py
```

- [ ] **Step 4: Write minimal implementation**

```python
# scripts/marketplace/registry.py
import json
import requests
from typing import Dict, Any

REGISTRY_URL = "https://raw.githubusercontent.com/mdproctor/claude-skill-registry/main/registry.json"

def fetch_registry(registry_url: str = REGISTRY_URL) -> Dict[str, Any]:
    """
    Fetch registry.json from GitHub.

    Args:
        registry_url: URL to registry.json (default: official registry)

    Returns:
        Parsed registry data

    Raises:
        RuntimeError: If fetch or parse fails
    """
    try:
        response = requests.get(registry_url, timeout=30)
        response.raise_for_status()
        return json.loads(response.text)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch registry from {registry_url}: {e}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_registry.py::test_fetch_registry -v`
Expected: PASS (both tests)

- [ ] **Step 6: Commit**

```bash
git add scripts/marketplace/ tests/marketplace/test_registry.py
git commit -m "feat(marketplace): add registry fetcher"
```

---

### Task 7: Registry Operations - Skill Lookup

**Files:**
- Modify: `scripts/marketplace/registry.py`
- Test: `tests/marketplace/test_registry.py`

- [ ] **Step 1: Write failing test for skill lookup**

```python
# tests/marketplace/test_registry.py (add to existing file)
def test_find_skill_returns_entry_when_found():
    """Lookup should return skill entry from registry"""
    registry = {
        "version": "1.0",
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

    from scripts.marketplace.registry import find_skill

    entry = find_skill(registry, "java-dev")

    assert entry["name"] == "java-dev"
    assert entry["defaultRef"] == "v1.0.0"


def test_find_skill_raises_when_not_found():
    """Lookup should raise error if skill not in registry"""
    registry = {
        "version": "1.0",
        "skills": []
    }

    from scripts.marketplace.registry import find_skill

    with pytest.raises(ValueError, match="Skill 'unknown-skill' not found"):
        find_skill(registry, "unknown-skill")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_registry.py::test_find_skill -v`
Expected: `AttributeError: module has no attribute 'find_skill'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/registry.py (add to existing file)
def find_skill(registry: Dict[str, Any], skill_name: str) -> Dict[str, Any]:
    """
    Find skill entry in registry by name.

    Args:
        registry: Parsed registry data
        skill_name: Name of skill to find

    Returns:
        Skill registry entry

    Raises:
        ValueError: If skill not found
    """
    for skill in registry["skills"]:
        if skill["name"] == skill_name:
            return skill

    raise ValueError(f"Skill '{skill_name}' not found in registry")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_registry.py::test_find_skill -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/registry.py tests/marketplace/test_registry.py
git commit -m "feat(marketplace): add skill lookup in registry"
```

---

### Task 8: Dependency Resolver - Graph Builder

**Files:**
- Create: `scripts/marketplace/dependency_resolver.py`
- Test: `tests/marketplace/test_dependency_resolver.py`

- [ ] **Step 1: Write failing test for dependency graph**

```python
# tests/marketplace/test_dependency_resolver.py
import pytest
from unittest.mock import Mock, patch

def test_build_graph_single_skill_no_deps():
    """Graph builder should handle skill with no dependencies"""
    mock_skill_json = {
        "name": "java-dev",
        "version": "1.0.0",
        "repository": "https://github.com/mdproctor/claude-skills",
        "dependencies": []
    }

    with patch('scripts.marketplace.dependency_resolver.fetch_skill_metadata', return_value=mock_skill_json):
        from scripts.marketplace.dependency_resolver import build_dependency_graph

        graph = build_dependency_graph("java-dev", registry={})

        assert len(graph) == 1
        assert graph[0]["name"] == "java-dev"
        assert graph[0]["dependencies"] == []


def test_build_graph_with_single_dependency():
    """Graph builder should resolve single dependency"""
    java_dev_metadata = {
        "name": "java-dev",
        "version": "1.0.0",
        "repository": "https://github.com/mdproctor/claude-skills",
        "dependencies": []
    }

    quarkus_flow_metadata = {
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

    def mock_fetch(repo, path, ref):
        if path == "quarkus-flow-dev":
            return quarkus_flow_metadata
        elif path == "java-dev":
            return java_dev_metadata
        raise ValueError(f"Unknown skill: {path}")

    with patch('scripts.marketplace.dependency_resolver.fetch_skill_metadata', side_effect=mock_fetch):
        from scripts.marketplace.dependency_resolver import build_dependency_graph

        graph = build_dependency_graph("quarkus-flow-dev", registry={})

        # Should include both skills
        assert len(graph) == 2

        # java-dev should come first (dependency)
        assert graph[0]["name"] == "java-dev"
        assert graph[1]["name"] == "quarkus-flow-dev"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_dependency_resolver.py::test_build_graph -v`
Expected: `ModuleNotFoundError: No module named 'scripts.marketplace.dependency_resolver'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/dependency_resolver.py
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any

def fetch_skill_metadata(repository: str, path: str, ref: str) -> Dict[str, Any]:
    """
    Fetch skill.json from GitHub repository using sparse checkout.

    Args:
        repository: GitHub repository URL
        path: Subdirectory path within repo
        ref: Git reference (tag, branch, commit)

    Returns:
        Parsed skill.json metadata
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", repository], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], cwd=tmpdir, check=True, capture_output=True)

        # Configure sparse checkout for skill.json only
        sparse_file = tmpdir / ".git" / "info" / "sparse-checkout"
        sparse_file.write_text(f"{path}/skill.json\n")

        # Fetch
        subprocess.run(["git", "fetch", "--depth=1", "origin", ref], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "checkout", ref], cwd=tmpdir, check=True, capture_output=True)

        # Read skill.json
        skill_json_path = tmpdir / path / "skill.json"
        with open(skill_json_path) as f:
            return json.load(f)


def build_dependency_graph(
    skill_name: str,
    registry: Dict[str, Any],
    repository: str = "https://github.com/mdproctor/claude-skills",
    ref: str = "main"
) -> List[Dict[str, Any]]:
    """
    Build dependency graph for skill, resolving transitive dependencies.

    Args:
        skill_name: Name of skill to install
        registry: Registry data (for looking up skills)
        repository: Default repository URL
        ref: Default git reference

    Returns:
        List of skills in dependency order (dependencies first)
    """
    visited = set()
    graph = []

    def visit(name: str, repo: str, git_ref: str):
        if name in visited:
            return

        visited.add(name)

        # Fetch metadata
        metadata = fetch_skill_metadata(repo, name, git_ref)

        # Visit dependencies first
        for dep in metadata.get("dependencies", []):
            visit(dep["name"], dep["repository"], dep["ref"])

        # Add to graph after dependencies
        graph.append(metadata)

    visit(skill_name, repository, ref)
    return graph
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_dependency_resolver.py::test_build_graph -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/dependency_resolver.py tests/marketplace/test_dependency_resolver.py
git commit -m "feat(marketplace): add dependency graph builder"
```

---

### Task 9: Dependency Resolver - Conflict Detection

**Files:**
- Modify: `scripts/marketplace/dependency_resolver.py`
- Test: `tests/marketplace/test_dependency_resolver.py`

- [ ] **Step 1: Write failing test for conflict detection**

```python
# tests/marketplace/test_dependency_resolver.py (add to existing file)
def test_detect_conflict_raises_on_version_mismatch():
    """Conflict detector should raise error when same skill required with different refs"""
    from scripts.marketplace.dependency_resolver import detect_conflicts

    graph = [
        {
            "name": "java-dev",
            "version": "1.0.0",
            "dependencies": [],
            "ref": "v1.0.0"
        },
        {
            "name": "java-dev",
            "version": "2.0.0",
            "dependencies": [],
            "ref": "v2.0.0"
        }
    ]

    with pytest.raises(RuntimeError, match="Dependency conflict"):
        detect_conflicts(graph)


def test_detect_conflict_passes_on_same_ref():
    """Conflict detector should allow same skill with same ref"""
    from scripts.marketplace.dependency_resolver import detect_conflicts

    graph = [
        {
            "name": "java-dev",
            "version": "1.0.0",
            "dependencies": [],
            "ref": "v1.0.0"
        },
        {
            "name": "quarkus-flow-dev",
            "version": "1.2.0",
            "dependencies": [],
            "ref": "v1.2.0"
        }
    ]

    # Should not raise
    detect_conflicts(graph)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_dependency_resolver.py::test_detect_conflict -v`
Expected: `AttributeError: module has no attribute 'detect_conflicts'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/dependency_resolver.py (add to existing file)
def detect_conflicts(graph: List[Dict[str, Any]]) -> None:
    """
    Detect version conflicts in dependency graph.

    In v1, we reject any conflicts (same skill, different refs).

    Args:
        graph: Dependency graph

    Raises:
        RuntimeError: If conflict detected
    """
    seen = {}

    for skill in graph:
        name = skill["name"]
        ref = skill.get("ref", skill.get("version"))

        if name in seen:
            if seen[name] != ref:
                raise RuntimeError(
                    f"Dependency conflict: '{name}' required with both "
                    f"'{seen[name]}' and '{ref}'. "
                    f"Cannot install multiple versions of the same skill."
                )
        else:
            seen[name] = ref
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_dependency_resolver.py::test_detect_conflict -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/dependency_resolver.py tests/marketplace/test_dependency_resolver.py
git commit -m "feat(marketplace): add dependency conflict detection"
```

---

### Task 10: Installer - Git Sparse Checkout

**Files:**
- Create: `scripts/marketplace/installer.py`
- Test: `tests/marketplace/test_installer.py`

- [ ] **Step 1: Write failing test for installation**

```python
# tests/marketplace/test_installer.py
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

def test_install_skill_downloads_to_marketplace():
    """Installer should download skill to .marketplace directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        skill_metadata = {
            "name": "java-dev",
            "version": "1.0.0",
            "repository": "https://github.com/mdproctor/claude-skills",
            "dependencies": []
        }

        # Mock git operations to avoid actual network calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            # Create fake SKILL.md and skill.json in temp location
            with patch('scripts.marketplace.installer.fetch_skill_files') as mock_fetch:
                fake_skill_dir = Path(tmpdir) / "temp_skill"
                fake_skill_dir.mkdir()
                (fake_skill_dir / "SKILL.md").write_text("---\nname: java-dev\n---\n")
                (fake_skill_dir / "skill.json").write_text('{"name":"java-dev"}')
                mock_fetch.return_value = fake_skill_dir

                from scripts.marketplace.installer import install_skill

                install_skill(
                    skill_metadata=skill_metadata,
                    marketplace_dir=marketplace_dir,
                    ref="v1.0.0"
                )

                # Verify installed
                installed_dir = marketplace_dir / "java-dev"
                assert installed_dir.exists()
                assert (installed_dir / "SKILL.md").exists()
                assert (installed_dir / "skill.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/marketplace/test_installer.py::test_install_skill -v`
Expected: `ModuleNotFoundError: No module named 'scripts.marketplace.installer'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/installer.py
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

def fetch_skill_files(repository: str, path: str, ref: str) -> Path:
    """
    Fetch skill files from GitHub using sparse checkout.

    Args:
        repository: GitHub repository URL
        path: Subdirectory path within repo
        ref: Git reference

    Returns:
        Path to temporary directory containing skill files
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="claude-skill-install-"))

    try:
        # Initialize git
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", repository], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], cwd=tmpdir, check=True, capture_output=True)

        # Configure sparse checkout
        sparse_file = tmpdir / ".git" / "info" / "sparse-checkout"
        sparse_file.write_text(f"{path}/*\n")

        # Fetch
        subprocess.run(["git", "fetch", "--depth=1", "origin", ref], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "checkout", ref], cwd=tmpdir, check=True, capture_output=True)

        return tmpdir / path
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Failed to fetch skill from {repository}/{path}@{ref}: {e}")


def install_skill(
    skill_metadata: Dict[str, Any],
    marketplace_dir: Path,
    ref: str
) -> None:
    """
    Install skill to marketplace directory.

    Args:
        skill_metadata: Skill metadata (name, repository, etc.)
        marketplace_dir: Path to .marketplace directory
        ref: Git reference to install
    """
    name = skill_metadata["name"]
    repository = skill_metadata["repository"]

    # Fetch files
    temp_skill_dir = fetch_skill_files(repository, name, ref)

    try:
        # Copy to marketplace
        install_dir = marketplace_dir / name
        if install_dir.exists():
            shutil.rmtree(install_dir)

        shutil.copytree(temp_skill_dir, install_dir)
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_skill_dir.parent, ignore_errors=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/marketplace/test_installer.py::test_install_skill -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/installer.py tests/marketplace/test_installer.py
git commit -m "feat(marketplace): add git sparse checkout installer"
```

---

### Task 11: Validator - Skill Validation

**Files:**
- Create: `scripts/marketplace/validator.py`
- Test: `tests/marketplace/test_validator.py`

- [ ] **Step 1: Write failing test for validation**

```python
# tests/marketplace/test_validator.py
import pytest
import tempfile
import json
from pathlib import Path

def test_validate_skill_passes_for_valid_skill():
    """Validator should pass for skill with SKILL.md and skill.json"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "java-dev"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("""---
name: java-dev
---

# Java Development
""")

        (skill_dir / "skill.json").write_text(json.dumps({
            "name": "java-dev",
            "version": "1.0.0",
            "repository": "https://github.com/test/repo",
            "dependencies": []
        }))

        from scripts.marketplace.validator import validate_skill

        # Should not raise
        validate_skill(skill_dir)


def test_validate_skill_raises_on_missing_skill_md():
    """Validator should raise if SKILL.md missing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "java-dev"
        skill_dir.mkdir()

        from scripts.marketplace.validator import validate_skill

        with pytest.raises(ValueError, match="SKILL.md not found"):
            validate_skill(skill_dir)


def test_validate_skill_raises_on_missing_skill_json():
    """Validator should raise if skill.json missing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "java-dev"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: java-dev\n---\n")

        from scripts.marketplace.validator import validate_skill

        with pytest.raises(ValueError, match="skill.json not found"):
            validate_skill(skill_dir)


def test_validate_skill_raises_on_name_mismatch():
    """Validator should raise if skill.json name doesn't match directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "java-dev"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("---\nname: java-dev\n---\n")
        (skill_dir / "skill.json").write_text(json.dumps({
            "name": "wrong-name",
            "version": "1.0.0",
            "repository": "https://github.com/test/repo",
            "dependencies": []
        }))

        from scripts.marketplace.validator import validate_skill

        with pytest.raises(ValueError, match="Name mismatch"):
            validate_skill(skill_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_validator.py::test_validate_skill -v`
Expected: `ModuleNotFoundError: No module named 'scripts.marketplace.validator'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/validator.py
import json
import re
from pathlib import Path

def validate_skill(skill_dir: Path) -> None:
    """
    Validate skill directory contains valid SKILL.md and skill.json.

    Args:
        skill_dir: Path to skill directory

    Raises:
        ValueError: If validation fails
    """
    # Check SKILL.md exists
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        raise ValueError(f"SKILL.md not found in {skill_dir}")

    # Check skill.json exists
    skill_json_path = skill_dir / "skill.json"
    if not skill_json_path.exists():
        raise ValueError(f"skill.json not found in {skill_dir}")

    # Parse skill.json
    try:
        with open(skill_json_path) as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in skill.json: {e}")

    # Validate required fields
    if "name" not in metadata:
        raise ValueError("skill.json missing 'name' field")

    # Validate name matches directory
    expected_name = skill_dir.name
    actual_name = metadata["name"]
    if actual_name != expected_name:
        raise ValueError(
            f"Name mismatch: directory is '{expected_name}' but "
            f"skill.json has '{actual_name}'"
        )

    # Parse frontmatter from SKILL.md
    skill_md_content = skill_md_path.read_text()
    match = re.match(r'^---\s*\n(.*?)\n---', skill_md_content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md missing frontmatter")

    frontmatter = match.group(1)
    name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    if not name_match:
        raise ValueError("SKILL.md frontmatter missing 'name' field")

    frontmatter_name = name_match.group(1).strip()
    if frontmatter_name != actual_name:
        raise ValueError(
            f"Name mismatch: SKILL.md has '{frontmatter_name}' but "
            f"skill.json has '{actual_name}'"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_validator.py::test_validate_skill -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/validator.py tests/marketplace/test_validator.py
git commit -m "feat(marketplace): add skill validation"
```

---

### Task 12: CLI - Install Command

**Files:**
- Create: `scripts/marketplace/cli.py`
- Test: `tests/marketplace/test_cli_integration.py`

- [ ] **Step 1: Write failing integration test for install**

```python
# tests/marketplace/test_cli_integration.py
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

def test_cli_install_downloads_skill_with_dependencies():
    """CLI install should fetch skill and dependencies"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        # Mock registry
        mock_registry = {
            "version": "1.0",
            "skills": [
                {
                    "name": "java-dev",
                    "repository": "https://github.com/mdproctor/claude-skills",
                    "path": "java-dev",
                    "defaultRef": "v1.0.0"
                },
                {
                    "name": "quarkus-flow-dev",
                    "repository": "https://github.com/mdproctor/claude-skills",
                    "path": "quarkus-flow-dev",
                    "defaultRef": "v1.2.0"
                }
            ]
        }

        with patch('scripts.marketplace.cli.fetch_registry', return_value=mock_registry):
            with patch('scripts.marketplace.cli.build_dependency_graph') as mock_graph:
                with patch('scripts.marketplace.cli.install_skill') as mock_install:
                    with patch('scripts.marketplace.cli.validate_skill') as mock_validate:
                        # Mock dependency graph
                        mock_graph.return_value = [
                            {
                                "name": "java-dev",
                                "version": "1.0.0",
                                "repository": "https://github.com/mdproctor/claude-skills",
                                "dependencies": []
                            },
                            {
                                "name": "quarkus-flow-dev",
                                "version": "1.2.0",
                                "repository": "https://github.com/mdproctor/claude-skills",
                                "dependencies": [{"name": "java-dev"}]
                            }
                        ]

                        from scripts.marketplace.cli import install_command

                        result = install_command("quarkus-flow-dev", marketplace_dir, snapshot=False)

                        # Verify both skills installed
                        assert mock_install.call_count == 2
                        assert result == 0  # Success exit code
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/marketplace/test_cli_integration.py::test_cli_install -v`
Expected: `ModuleNotFoundError: No module named 'scripts.marketplace.cli'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/cli.py
import sys
from pathlib import Path
from typing import Optional

from scripts.marketplace.registry import fetch_registry, find_skill
from scripts.marketplace.dependency_resolver import build_dependency_graph, detect_conflicts
from scripts.marketplace.installer import install_skill
from scripts.marketplace.validator import validate_skill

def install_command(
    skill_name: str,
    marketplace_dir: Path,
    snapshot: bool = False
) -> int:
    """
    Install skill and dependencies.

    Args:
        skill_name: Name of skill to install
        marketplace_dir: Path to .marketplace directory
        snapshot: If True, use snapshotRef instead of defaultRef

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        print(f"Fetching registry...")
        registry = fetch_registry()
        print("✓ Registry loaded\n")

        print(f"Resolving dependencies...")
        skill_entry = find_skill(registry, skill_name)

        ref = skill_entry["snapshotRef"] if snapshot else skill_entry["defaultRef"]
        repository = skill_entry["repository"]
        path = skill_entry["path"]

        graph = build_dependency_graph(
            skill_name=path,
            registry=registry,
            repository=repository,
            ref=ref
        )

        # Show dependency tree
        if len(graph) > 1:
            print(f"  {skill_name} requires:")
            for skill in graph[:-1]:  # All except the requested skill
                print(f"    - {skill['name']} ({skill.get('version', ref)})")

        print(f"\nInstallation plan:")
        for i, skill in enumerate(graph, 1):
            version = skill.get('version', ref)
            print(f"  {i}. {skill['name']} {version}")

        # Detect conflicts
        detect_conflicts(graph)

        # Confirm
        response = input("\nProceed? (Y/n): ")
        if response.lower() == 'n':
            print("Cancelled.")
            return 1

        # Install each skill
        print()
        for skill in graph:
            skill_name_install = skill["name"]
            skill_version = skill.get("version", ref)

            print(f"Installing {skill_name_install} {skill_version}...")

            install_skill(
                skill_metadata=skill,
                marketplace_dir=marketplace_dir,
                ref=ref
            )

            # Validate
            validate_skill(marketplace_dir / skill_name_install)

            print(f"✓ Validated")
            print(f"✓ Installed to {marketplace_dir}/{skill_name_install}/\n")

        print(f"Successfully installed {len(graph)} skill(s).")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/marketplace/test_cli_integration.py::test_cli_install -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/cli.py tests/marketplace/test_cli_integration.py
git commit -m "feat(marketplace): add CLI install command"
```

---

### Task 13: CLI - Uninstall Command

**Files:**
- Modify: `scripts/marketplace/cli.py`
- Test: `tests/marketplace/test_cli_integration.py`

- [ ] **Step 1: Write failing test for uninstall**

```python
# tests/marketplace/test_cli_integration.py (add to existing file)
def test_cli_uninstall_removes_skill():
    """CLI uninstall should remove skill directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        # Create installed skill
        skill_dir = marketplace_dir / "java-dev"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: java-dev\n---\n")

        from scripts.marketplace.cli import uninstall_command

        with patch('builtins.input', return_value='y'):  # Auto-confirm
            result = uninstall_command("java-dev", marketplace_dir)

        # Verify removed
        assert not skill_dir.exists()
        assert result == 0


def test_cli_uninstall_warns_about_dependents():
    """CLI uninstall should warn if other skills depend on it"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        # Create java-dev
        java_dev = marketplace_dir / "java-dev"
        java_dev.mkdir()
        (java_dev / "SKILL.md").write_text("---\nname: java-dev\n---\n")
        (java_dev / "skill.json").write_text(json.dumps({
            "name": "java-dev",
            "version": "1.0.0",
            "dependencies": []
        }))

        # Create quarkus-flow-dev that depends on java-dev
        quarkus = marketplace_dir / "quarkus-flow-dev"
        quarkus.mkdir()
        (quarkus / "SKILL.md").write_text("---\nname: quarkus-flow-dev\n---\n")
        (quarkus / "skill.json").write_text(json.dumps({
            "name": "quarkus-flow-dev",
            "version": "1.2.0",
            "dependencies": [{"name": "java-dev"}]
        }))

        from scripts.marketplace.cli import uninstall_command

        # Cancel uninstall
        with patch('builtins.input', return_value='n'):
            result = uninstall_command("java-dev", marketplace_dir)

        # Verify not removed
        assert java_dev.exists()
        assert result == 1  # Cancelled
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_cli_integration.py::test_cli_uninstall -v`
Expected: `AttributeError: module has no attribute 'uninstall_command'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/cli.py (add to existing file)
import shutil
import json

def find_dependents(skill_name: str, marketplace_dir: Path) -> list:
    """
    Find installed skills that depend on given skill.

    Args:
        skill_name: Name of skill to check
        marketplace_dir: Path to .marketplace directory

    Returns:
        List of dependent skill names
    """
    dependents = []

    for skill_dir in marketplace_dir.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_json_path = skill_dir / "skill.json"
        if not skill_json_path.exists():
            continue

        with open(skill_json_path) as f:
            metadata = json.load(f)

        for dep in metadata.get("dependencies", []):
            if dep["name"] == skill_name:
                dependents.append(metadata["name"])
                break

    return dependents


def uninstall_command(skill_name: str, marketplace_dir: Path) -> int:
    """
    Uninstall skill from marketplace.

    Args:
        skill_name: Name of skill to uninstall
        marketplace_dir: Path to .marketplace directory

    Returns:
        Exit code (0 = success, 1 = error/cancelled)
    """
    try:
        skill_dir = marketplace_dir / skill_name

        if not skill_dir.exists():
            print(f"Skill '{skill_name}' not installed.")
            return 1

        # Check for dependents
        dependents = find_dependents(skill_name, marketplace_dir)

        if dependents:
            print(f"\n⚠️  Warning: The following skills depend on {skill_name}:")
            for dep in dependents:
                print(f"  - {dep}")
            print()

        response = input(f"Uninstall anyway? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 1

        # Remove directory
        shutil.rmtree(skill_dir)
        print(f"Removing {skill_name}...")
        print(f"✓ Uninstalled {skill_name} from {marketplace_dir}/")

        if dependents:
            print(f"\n⚠️  The following skills may not work correctly:")
            for dep in dependents:
                print(f"  - {dep}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_cli_integration.py::test_cli_uninstall -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/cli.py tests/marketplace/test_cli_integration.py
git commit -m "feat(marketplace): add CLI uninstall command"
```

---

### Task 14: CLI - List Command

**Files:**
- Modify: `scripts/marketplace/cli.py`
- Test: `tests/marketplace/test_cli_integration.py`

- [ ] **Step 1: Write failing test for list**

```python
# tests/marketplace/test_cli_integration.py (add to existing file)
from io import StringIO

def test_cli_list_displays_installed_skills(capsys):
    """CLI list should display all installed skills with versions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        # Create installed skills
        java_dev = marketplace_dir / "java-dev"
        java_dev.mkdir()
        (java_dev / "SKILL.md").write_text("---\nname: java-dev\n---\n")
        (java_dev / "skill.json").write_text(json.dumps({
            "name": "java-dev",
            "version": "1.0.0",
            "dependencies": []
        }))

        quarkus = marketplace_dir / "quarkus-flow-dev"
        quarkus.mkdir()
        (quarkus / "SKILL.md").write_text("---\nname: quarkus-flow-dev\n---\n")
        (quarkus / "skill.json").write_text(json.dumps({
            "name": "quarkus-flow-dev",
            "version": "1.2.0",
            "dependencies": [{"name": "java-dev"}]
        }))

        from scripts.marketplace.cli import list_command

        result = list_command(marketplace_dir)

        # Capture output
        captured = capsys.readouterr()

        # Verify output contains skills
        assert "java-dev" in captured.out
        assert "1.0.0" in captured.out
        assert "quarkus-flow-dev" in captured.out
        assert "1.2.0" in captured.out
        assert "depends on: java-dev" in captured.out
        assert result == 0


def test_cli_list_handles_empty_marketplace(capsys):
    """CLI list should handle empty marketplace gracefully"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        from scripts.marketplace.cli import list_command

        result = list_command(marketplace_dir)

        captured = capsys.readouterr()
        assert "0 skills installed" in captured.out
        assert result == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/marketplace/test_cli_integration.py::test_cli_list -v`
Expected: `AttributeError: module has no attribute 'list_command'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/marketplace/cli.py (add to existing file)
def list_command(marketplace_dir: Path) -> int:
    """
    List installed skills.

    Args:
        marketplace_dir: Path to .marketplace directory

    Returns:
        Exit code (0 = success)
    """
    try:
        if not marketplace_dir.exists():
            print("No skills installed.")
            print("\n0 skills installed")
            return 0

        skills = []

        for skill_dir in sorted(marketplace_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_json_path = skill_dir / "skill.json"
            if not skill_json_path.exists():
                continue

            with open(skill_json_path) as f:
                metadata = json.load(f)

            skills.append(metadata)

        if not skills:
            print("No skills installed.")
            print("\n0 skills installed")
            return 0

        print("Installed skills:")

        for skill in skills:
            name = skill["name"]
            version = skill.get("version", "unknown")
            dependencies = skill.get("dependencies", [])

            # Format output
            output = f"  {name:<30} {version}"

            if dependencies:
                dep_names = [dep["name"] for dep in dependencies]
                output += f"  (depends on: {', '.join(dep_names)})"

            print(output)

        print(f"\n{len(skills)} skill(s) installed")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/marketplace/test_cli_integration.py::test_cli_list -v`
Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/cli.py tests/marketplace/test_cli_integration.py
git commit -m "feat(marketplace): add CLI list command"
```

---

### Task 15: CLI - Main Entry Point

**Files:**
- Modify: `scripts/marketplace/cli.py`
- Test: Manual testing

- [ ] **Step 1: Write main entry point**

```python
# scripts/marketplace/cli.py (add to existing file)
import argparse

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="claude-skill",
        description="Claude Code skill marketplace CLI"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("skill", help="Skill name to install")
    install_parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Install snapshot version instead of stable"
    )
    install_parser.add_argument(
        "--marketplace-dir",
        type=Path,
        default=Path.home() / ".claude" / "skills" / ".marketplace",
        help="Marketplace directory (default: ~/.claude/skills/.marketplace)"
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a skill")
    uninstall_parser.add_argument("skill", help="Skill name to uninstall")
    uninstall_parser.add_argument(
        "--marketplace-dir",
        type=Path,
        default=Path.home() / ".claude" / "skills" / ".marketplace",
        help="Marketplace directory"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List installed skills")
    list_parser.add_argument(
        "--marketplace-dir",
        type=Path,
        default=Path.home() / ".claude" / "skills" / ".marketplace",
        help="Marketplace directory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Ensure marketplace directory exists
    marketplace_dir = args.marketplace_dir
    if args.command in ["install", "list"]:
        marketplace_dir.mkdir(parents=True, exist_ok=True)

    # Route to command
    if args.command == "install":
        return install_command(args.skill, marketplace_dir, args.snapshot)
    elif args.command == "uninstall":
        return uninstall_command(args.skill, marketplace_dir)
    elif args.command == "list":
        return list_command(marketplace_dir)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make CLI executable**

```bash
chmod +x scripts/marketplace/cli.py
```

- [ ] **Step 3: Create convenience script**

```bash
# Create scripts/claude-skill
cat > scripts/claude-skill << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.marketplace.cli import main

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x scripts/claude-skill
```

- [ ] **Step 4: Test manually**

Run: `scripts/claude-skill --help`
Expected: Help text showing install, uninstall, list commands

Run: `scripts/claude-skill list`
Expected: "No skills installed" (or list of installed skills)

- [ ] **Step 5: Commit**

```bash
git add scripts/marketplace/cli.py scripts/claude-skill
git commit -m "feat(marketplace): add main CLI entry point"
```

---

### Task 16: Documentation - README for Registry

**Files:**
- Create: `docs/marketplace/REGISTRY.md`

- [ ] **Step 1: Write registry documentation**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
mkdir -p docs/marketplace
git add docs/marketplace/REGISTRY.md
git commit -m "docs(marketplace): add registry usage and publishing guide"
```

---

### Task 17: Documentation - Update Main README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add marketplace section to README**

```markdown
# README.md (add after "Getting Started" section)

## Installing Individual Skills

**Install the marketplace CLI:**

The skill marketplace is built into this repository. Clone it to get started:

```bash
git clone https://github.com/mdproctor/claude-skills.git ~/claude-skills-dev
cd ~/claude-skills-dev
```

**Install specific skills:**

```bash
# Install stable version
scripts/claude-skill install java-dev

# Install snapshot (latest development)
scripts/claude-skill install quarkus-flow-dev --snapshot

# List installed skills
scripts/claude-skill list

# Uninstall
scripts/claude-skill uninstall java-dev
```

**Installed skills location:** `~/.claude/skills/.marketplace/`

**Dependencies:** Automatically resolved and installed.

**See:** [Registry Documentation](docs/marketplace/REGISTRY.md) for publishing your own skills.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): add marketplace installation instructions"
```

---

### Task 18: Integration Testing - End-to-End

**Files:**
- Create: `tests/marketplace/test_e2e.py`

- [ ] **Step 1: Write end-to-end test**

```python
# tests/marketplace/test_e2e.py
import pytest
import tempfile
import json
import subprocess
from pathlib import Path

@pytest.mark.slow
def test_e2e_install_real_skill():
    """End-to-end test: Install real skill from GitHub (requires network)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        # Run CLI
        result = subprocess.run(
            [
                "python",
                "scripts/marketplace/cli.py",
                "install",
                "code-review-principles",
                "--marketplace-dir",
                str(marketplace_dir)
            ],
            input="y\n",  # Auto-confirm
            capture_output=True,
            text=True
        )

        # Verify success
        assert result.returncode == 0

        # Verify files exist
        skill_dir = marketplace_dir / "code-review-principles"
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "skill.json").exists()

        # Verify metadata
        with open(skill_dir / "skill.json") as f:
            metadata = json.load(f)

        assert metadata["name"] == "code-review-principles"


@pytest.mark.slow
def test_e2e_full_workflow():
    """End-to-end: Install, list, uninstall"""
    with tempfile.TemporaryDirectory() as tmpdir:
        marketplace_dir = Path(tmpdir) / ".marketplace"
        marketplace_dir.mkdir()

        # Install
        install_result = subprocess.run(
            [
                "python",
                "scripts/marketplace/cli.py",
                "install",
                "code-review-principles",
                "--marketplace-dir",
                str(marketplace_dir)
            ],
            input="y\n",
            capture_output=True,
            text=True
        )
        assert install_result.returncode == 0

        # List
        list_result = subprocess.run(
            [
                "python",
                "scripts/marketplace/cli.py",
                "list",
                "--marketplace-dir",
                str(marketplace_dir)
            ],
            capture_output=True,
            text=True
        )
        assert list_result.returncode == 0
        assert "code-review-principles" in list_result.stdout

        # Uninstall
        uninstall_result = subprocess.run(
            [
                "python",
                "scripts/marketplace/cli.py",
                "uninstall",
                "code-review-principles",
                "--marketplace-dir",
                str(marketplace_dir)
            ],
            input="y\n",
            capture_output=True,
            text=True
        )
        assert uninstall_result.returncode == 0
        assert not (marketplace_dir / "code-review-principles").exists()
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/marketplace/test_e2e.py -v -m slow`
Expected: PASS (requires network connection)

- [ ] **Step 3: Commit**

```bash
git add tests/marketplace/test_e2e.py
git commit -m "test(marketplace): add end-to-end integration tests"
```

---

### Task 19: Final Testing - All Tests

**Files:**
- None (running existing tests)

- [ ] **Step 1: Run all marketplace tests**

Run: `pytest tests/marketplace/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run metadata generation test**

Run: `pytest tests/marketplace/test_metadata_generator.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Manual smoke test - generate metadata**

Run: `cd /Users/mdproctor/.claude/skills && python scripts/generate_skill_metadata.py`
Expected: Generates skill.json for all ~20 skills, no errors

- [ ] **Step 5: Manual smoke test - list (empty)**

Run: `scripts/claude-skill list`
Expected: Shows installed skills or "No skills installed"

---

### Task 20: Create Initial Registry

**Files:**
- Create: `registry-template.json` (template for external registry repo)

- [ ] **Step 1: Generate registry template**

```json
{
  "version": "1.0",
  "updated": "2026-03-30T00:00:00Z",
  "skills": [
    {
      "name": "code-review-principles",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "code-review-principles",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "security-audit-principles",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "security-audit-principles",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "dependency-management-principles",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "dependency-management-principles",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "observability-principles",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "observability-principles",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
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
    },
    {
      "name": "quarkus-flow-testing",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "quarkus-flow-testing",
      "defaultRef": "v1.1.0",
      "snapshotRef": "main"
    },
    {
      "name": "quarkus-observability",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "quarkus-observability",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "java-code-review",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "java-code-review",
      "defaultRef": "v1.1.0",
      "snapshotRef": "main"
    },
    {
      "name": "java-security-audit",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "java-security-audit",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "git-commit",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "git-commit",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "java-git-commit",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "java-git-commit",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "custom-git-commit",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "custom-git-commit",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "java-update-design",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "java-update-design",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "update-claude-md",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "update-claude-md",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "update-primary-doc",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "update-primary-doc",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "maven-dependency-update",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "maven-dependency-update",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    },
    {
      "name": "adr",
      "repository": "https://github.com/mdproctor/claude-skills",
      "path": "adr",
      "defaultRef": "v1.0.0",
      "snapshotRef": "main"
    }
  ]
}
```

- [ ] **Step 2: Save as template**

```bash
# Save in docs for reference (actual registry lives in separate repo)
git add registry-template.json
git commit -m "feat(marketplace): add registry template with all skills"
```

---

## Self-Review

**Spec coverage check:**

- ✅ Metadata generation: Tasks 1-5 (scan, parse frontmatter, parse dependencies, generate JSON, main CLI)
- ✅ Registry operations: Tasks 6-7 (fetch, lookup)
- ✅ Dependency resolution: Tasks 8-9 (graph builder, conflict detection)
- ✅ Installation: Task 10 (git sparse checkout)
- ✅ Validation: Task 11 (SKILL.md + skill.json validation)
- ✅ CLI commands: Tasks 12-14 (install, uninstall, list)
- ✅ CLI entry point: Task 15 (main, argparse)
- ✅ Documentation: Tasks 16-17 (registry docs, README)
- ✅ Testing: Tasks 18-19 (E2E, full suite)
- ✅ Registry creation: Task 20 (template)

**Placeholder scan:** None found - all code blocks complete, all commands specified.

**Type consistency:** Verified across tasks:
- `skill.json` format consistent (name, version, repository, dependencies)
- `registry.json` format consistent (version, updated, skills[])
- Function signatures match between definition and usage
- Path types consistent (Path objects, not strings)

**No gaps identified.**

---

## Success Criteria

Implementation is complete when:

- ✅ `scripts/generate_skill_metadata.py` generates valid skill.json for all skills
- ✅ `scripts/claude-skill install <name>` downloads and installs skills
- ✅ `scripts/claude-skill uninstall <name>` removes skills cleanly
- ✅ `scripts/claude-skill list` shows installed skills
- ✅ Dependencies auto-resolve and install in correct order
- ✅ Conflicts detected and rejected with clear error messages
- ✅ All tests pass (unit + integration + E2E)
- ✅ Documentation complete (REGISTRY.md, README.md updates)
- ✅ Registry template created for all existing skills
