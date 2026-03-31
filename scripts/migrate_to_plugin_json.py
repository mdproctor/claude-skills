#!/usr/bin/env python3
"""
Migrate skill.json to .claude-plugin/plugin.json (official format).
"""

import json
from pathlib import Path

def migrate_skill(skill_dir: Path) -> None:
    """Convert skill.json to .claude-plugin/plugin.json."""
    skill_json = skill_dir / "skill.json"
    if not skill_json.exists():
        return

    # Read old format
    with open(skill_json) as f:
        data = json.load(f)

    # Extract dependencies
    deps = []
    for dep in data.get("dependencies", []):
        if isinstance(dep, dict):
            deps.append({
                "name": dep["name"],
                "version": "1.0.0"  # Default version
            })
        else:
            deps.append({"name": dep, "version": "1.0.0"})

    # Read SKILL.md for description
    skill_md = skill_dir / "SKILL.md"
    description = ""
    if skill_md.exists():
        with open(skill_md) as f:
            for line in f:
                if line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                    break

    # Create new format
    plugin_json = {
        "name": data["name"],
        "description": description,
        "version": data.get("version", "1.0.0")
    }

    if deps:
        plugin_json["dependencies"] = deps

    # Write to .claude-plugin/plugin.json
    plugin_dir = skill_dir / ".claude-plugin"
    plugin_dir.mkdir(exist_ok=True)

    with open(plugin_dir / "plugin.json", "w") as f:
        json.dump(plugin_json, f, indent=2)

    print(f"✅ Migrated {skill_dir.name}")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent

    for skill_dir in repo_root.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            migrate_skill(skill_dir)
