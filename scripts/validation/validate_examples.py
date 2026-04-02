#!/usr/bin/env python3
"""
TIER: PUSH

Code example syntax validator — checks fenced code blocks in SKILL.md files.

Checks:
- All code fences are balanced (no unclosed ```) — CRITICAL
- YAML blocks (```yaml) are valid YAML — WARNING
- JSON blocks (```json) are valid JSON — WARNING

Blocks containing template markers ({...}, <...>, [...placeholder...]) are
skipped — they are intentionally not valid syntax.
"""

import sys
import re
import json
import yaml
from pathlib import Path
from typing import List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import (
    ValidationIssue, ValidationResult, Severity,
    find_all_skill_files, print_summary
)

# Regex to detect template markers inside a block
# Matches: {anything}, <word>, [Add ..., [Your ..., [TODO ...
TEMPLATE_PATTERNS = [
    re.compile(r'\{[^}]*\}'),                   # {placeholder}
    re.compile(r'<[A-Za-z][^>]*>'),             # <placeholder>
    re.compile(r'\[(?:Add|Your|TODO)\b'),        # [Add ..., [Your ..., [TODO
]


def has_template_markers(block: str) -> bool:
    """Return True if the block contains template/placeholder content."""
    return any(pattern.search(block) for pattern in TEMPLATE_PATTERNS)


def extract_fenced_blocks(content: str) -> List[Tuple[str, str, int]]:
    """
    Extract fenced code blocks from markdown content.

    Returns list of (language, block_content, start_line_number) tuples.
    Only returns blocks where the fence opens with a known language tag.
    """
    blocks = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match an opening fence: optional leading spaces, ```, language tag
        fence_open = re.match(r'^(`{3,})(\w+)?\s*$', line.strip())
        if fence_open:
            fence_chars = fence_open.group(1)  # the actual backtick sequence
            lang = (fence_open.group(2) or '').lower()
            start_line = i + 1  # 1-based
            block_lines = []
            i += 1
            closed = False
            while i < len(lines):
                closing_candidate = lines[i].strip()
                if closing_candidate == fence_chars:
                    closed = True
                    i += 1
                    break
                block_lines.append(lines[i])
                i += 1

            if closed and lang in ('yaml', 'json'):
                block_content = '\n'.join(block_lines)
                blocks.append((lang, block_content, start_line))
        else:
            i += 1

    return blocks


def check_balanced_fences(content: str, file_path: Path) -> List[ValidationIssue]:
    """Check that all code fences are balanced (even number of ``` markers)."""
    issues = []
    lines = content.splitlines()

    fence_count = 0
    open_line = None

    for line_no, line in enumerate(lines, 1):
        if re.match(r'^\s*`{3,}', line):
            fence_count += 1
            if fence_count % 2 == 1:
                open_line = line_no  # opening fence
            else:
                open_line = None    # closed

    if fence_count % 2 != 0:
        issues.append(ValidationIssue(
            severity=Severity.CRITICAL,
            file_path=str(file_path),
            line_number=open_line,
            message='Unclosed code fence (odd number of ``` markers)',
            fix_suggestion='Add a closing ``` to the last unclosed code block',
        ))

    return issues


def check_yaml_block(block: str, file_path: Path, start_line: int) -> Optional[ValidationIssue]:
    """Validate a YAML fenced block. Returns an issue or None."""
    if has_template_markers(block):
        return None
    try:
        yaml.safe_load(block)
        return None
    except yaml.YAMLError as exc:
        return ValidationIssue(
            severity=Severity.WARNING,
            file_path=str(file_path),
            line_number=start_line,
            message=f'Invalid YAML in code block: {exc}',
            fix_suggestion='Fix the YAML syntax or add template markers if this is a placeholder example',
        )


def check_json_block(block: str, file_path: Path, start_line: int) -> Optional[ValidationIssue]:
    """Validate a JSON fenced block. Returns an issue or None."""
    if has_template_markers(block):
        return None
    try:
        json.loads(block)
        return None
    except json.JSONDecodeError as exc:
        return ValidationIssue(
            severity=Severity.WARNING,
            file_path=str(file_path),
            line_number=start_line,
            message=f'Invalid JSON in code block: {exc}',
            fix_suggestion='Fix the JSON syntax or add template markers if this is a placeholder example',
        )


def validate_skill_file(skill_path: Path) -> List[ValidationIssue]:
    """Validate all code examples in a single SKILL.md file."""
    issues: List[ValidationIssue] = []

    try:
        content = skill_path.read_text(encoding='utf-8')
    except Exception as exc:
        issues.append(ValidationIssue(
            severity=Severity.WARNING,
            file_path=str(skill_path),
            line_number=None,
            message=f'Could not read file: {exc}',
        ))
        return issues

    # 1. Check for balanced fences (CRITICAL)
    issues.extend(check_balanced_fences(content, skill_path))

    # 2. Extract and validate yaml/json blocks
    for lang, block_content, start_line in extract_fenced_blocks(content):
        if lang == 'yaml':
            issue = check_yaml_block(block_content, skill_path, start_line)
        elif lang == 'json':
            issue = check_json_block(block_content, skill_path, start_line)
        else:
            continue

        if issue is not None:
            issues.append(issue)

    return issues


def main():
    """Main validation entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate code examples in SKILL.md files'
    )
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('files', nargs='*', help='Specific SKILL.md files to check')
    args = parser.parse_args()

    if args.files:
        skill_files = [Path(f) for f in args.files]
    else:
        skill_files = find_all_skill_files()

    all_issues: List[ValidationIssue] = []
    for skill_path in skill_files:
        all_issues.extend(validate_skill_file(skill_path))

    result = ValidationResult(
        validator_name='Code Example Syntax Validation',
        issues=all_issues,
        files_checked=len(skill_files),
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_summary(result, verbose=args.verbose)

    sys.exit(result.exit_code)


if __name__ == '__main__':
    main()
