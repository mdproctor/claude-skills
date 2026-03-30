#!/usr/bin/env python3
"""
Skill Metadata Generator - Task 1: Skill Scanner

Scans a directory structure to find all skill directories (those containing SKILL.md files).
This is the foundation for the marketplace metadata generation system.

Part of the skill marketplace implementation (Task 1 of 20).
"""

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
