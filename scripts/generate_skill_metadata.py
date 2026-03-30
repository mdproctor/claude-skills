#!/usr/bin/env python3
"""
Skill Metadata Generator - Task 1: Skill Scanner

Scans a directory structure to find all skill directories (those containing SKILL.md files).
This is the foundation for the marketplace metadata generation system.

Part of the skill marketplace implementation (Task 1 of 20).
"""

import re
from pathlib import Path
from typing import List


def scan_for_skills(root_dir: Path) -> List[Path]:
    """
    Scan directory for skill directories (containing SKILL.md).

    Excludes: .git, docs, scripts, tests, __pycache__, .claude

    Args:
        root_dir: Directory to scan for skills

    Returns:
        Sorted list of skill directory paths
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
