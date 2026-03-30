#!/usr/bin/env python3
"""
TIER: PRE-PUSH (30s budget)

Behavior consistency validator - checks documentation matches behavior.
"""
import sys
from pathlib import Path
from typing import List, Dict, Set
import re

def check_invocation_claims(skill_files: List[Path]) -> List[Dict]:
    """Verify 'invoked by X' claims are accurate."""
    issues = []

    # Build invocation graph
    claims = {}  # skill -> [claimed invokers]
    actual = {}  # skill -> [actual invokers]

    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        try:
            content = skill_file.read_text()
        except:
            continue

        # Extract "Invoked by" claims
        invoked_by_pattern = r'\*\*Invoked by:\*\*.*?`([^`]+)`'
        for match in re.finditer(invoked_by_pattern, content):
            invoker = match.group(1)
            if skill_name not in claims:
                claims[skill_name] = []
            claims[skill_name].append(invoker)

        # Extract actual invocations (skills this one calls)
        invoke_pattern = r'(?:invoke|chains to|follow).*?`([^`]+)`'
        for match in re.finditer(invoke_pattern, content, re.IGNORECASE):
            invoked = match.group(1)
            if invoked not in actual:
                actual[invoked] = []
            actual[invoked].append(skill_name)

    # Compare claims vs actual
    for skill, claimed_invokers in claims.items():
        actual_invokers = actual.get(skill, [])

        for claimed in claimed_invokers:
            if claimed not in actual_invokers:
                # Check if invoker skill exists
                invoker_file = Path(f"{claimed}/SKILL.md")
                if invoker_file.exists():
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'unverified_invocation_claim',
                        'skill': skill,
                        'claimed_invoker': claimed,
                        'message': f"{skill} claims invoked by {claimed}, but {claimed} doesn't reference it"
                    })

    return issues

def check_blocking_claims(skill_files: List[Path]) -> List[Dict]:
    """Verify 'blocks on CRITICAL' claims have blocking logic."""
    issues = []

    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        try:
            content = skill_file.read_text()
        except:
            continue

        # Look for blocking claims
        blocking_claims = [
            'blocks on CRITICAL',
            'block commit',
            'BLOCK if',
            'stop if CRITICAL',
        ]

        has_blocking_claim = any(claim in content for claim in blocking_claims)

        if has_blocking_claim:
            # Look for actual blocking logic
            blocking_patterns = [
                r'exit\s+1',
                r'sys\.exit\(1\)',
                r'return\s+1',
                r'if.*CRITICAL.*stop',
                r'if.*CRITICAL.*exit',
            ]

            has_blocking_logic = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in blocking_patterns
            )

            if not has_blocking_logic:
                issues.append({
                    'severity': 'WARNING',
                    'type': 'unimplemented_blocking',
                    'skill': skill_name,
                    'file': str(skill_file),
                    'message': f"{skill_name} claims to block on CRITICAL but no exit/stop logic found"
                })

    return issues

def check_validation_claims(skill_files: List[Path]) -> List[Dict]:
    """Verify validation claims have actual validation code."""
    issues = []

    validation_verbs = ['validates', 'checks', 'verifies', 'ensures']

    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        try:
            content = skill_file.read_text()
        except:
            continue

        # Find validation claims
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for verb in validation_verbs:
                if verb in line.lower() and any(word in line.lower() for word in ['must', 'should', 'always']):
                    # This is a validation claim
                    # Look for corresponding validation in next 20 lines
                    window = '\n'.join(lines[line_num:min(line_num+20, len(lines))])

                    # Check for validation patterns
                    has_validation = any([
                        'if' in window.lower(),
                        'check' in window.lower(),
                        'test' in window.lower(),
                        '```python' in window,
                        '```bash' in window,
                    ])

                    if not has_validation and 'example' not in line.lower():
                        issues.append({
                            'severity': 'NOTE',
                            'type': 'unimplemented_validation',
                            'skill': skill_name,
                            'file': str(skill_file),
                            'line': line_num,
                            'message': f"{skill_name}:{line_num}: Validation claim without implementation nearby"
                        })
                    break

    return issues

def check_example_syntax(skill_files: List[Path]) -> List[Dict]:
    """Check if code examples have basic syntax correctness."""
    issues = []

    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        try:
            content = skill_file.read_text()
        except:
            continue

        # Extract bash code blocks
        bash_blocks = re.finditer(r'```bash\n(.*?)```', content, re.DOTALL)
        for match in bash_blocks:
            code = match.group(1)

            # Common bash syntax errors
            if re.search(r'\[\s*\$\w+\s*==', code):
                issues.append({
                    'severity': 'WARNING',
                    'type': 'bash_syntax_error',
                    'skill': skill_name,
                    'message': f"{skill_name}: Bash comparison may fail - use quotes around variables"
                })

            if 'git commit -m "' in code and 'git commit -m "$(' in code:
                # Mixed quote styles might break
                issues.append({
                    'severity': 'NOTE',
                    'type': 'bash_quote_mixing',
                    'skill': skill_name,
                    'message': f"{skill_name}: Mixed quote styles in git commit command"
                })

    return issues

def check_always_never_claims(skill_files: List[Path]) -> List[Dict]:
    """Check if 'always' and 'never' claims have enforcement."""
    issues = []

    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        try:
            content = skill_file.read_text()
        except:
            continue

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Find "always X" or "never Y" claims
            if re.search(r'\b(always|never)\b', line, re.IGNORECASE):
                # Skip headers, examples, comments
                if line.strip().startswith(('#', '>', '//')) or 'example' in line.lower():
                    continue

                # Look for enforcement in surrounding context
                context_start = max(0, line_num - 3)
                context_end = min(len(lines), line_num + 10)
                context = '\n'.join(lines[context_start:context_end])

                # Check for enforcement patterns
                has_enforcement = any([
                    re.search(r'\bif\b', context, re.IGNORECASE),
                    re.search(r'\bcheck\b', context, re.IGNORECASE),
                    re.search(r'\bverify\b', context, re.IGNORECASE),
                    re.search(r'\bexit\b', context),
                    re.search(r'\bstop\b', context, re.IGNORECASE),
                ])

                if not has_enforcement:
                    issues.append({
                        'severity': 'NOTE',
                        'type': 'unenforced_rule',
                        'skill': skill_name,
                        'file': str(skill_file),
                        'line': line_num,
                        'message': f"{skill_name}:{line_num}: 'Always/Never' rule without enforcement"
                    })

    return issues

def main():
    """Main entry point."""
    base_dir = Path('.')

    # Find all SKILL.md files
    skill_files = list(base_dir.glob('*/SKILL.md'))

    all_issues = []

    print("Behavior Consistency Check", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Checking {len(skill_files)} skills for behavioral consistency...", file=sys.stderr)

    all_issues.extend(check_invocation_claims(skill_files))
    all_issues.extend(check_blocking_claims(skill_files))
    all_issues.extend(check_validation_claims(skill_files))
    all_issues.extend(check_example_syntax(skill_files))
    all_issues.extend(check_always_never_claims(skill_files))

    # Categorize issues
    critical = [i for i in all_issues if i['severity'] == 'CRITICAL']
    warnings = [i for i in all_issues if i['severity'] == 'WARNING']
    notes = [i for i in all_issues if i['severity'] == 'NOTE']

    if not all_issues:
        print("✅ Behavior consistent with documentation", file=sys.stderr)
        sys.exit(0)

    if critical:
        print(f"\n❌ CRITICAL: {len(critical)}", file=sys.stderr)
        for issue in critical:
            print(f"  - {issue['message']}", file=sys.stderr)

    if warnings:
        print(f"\n⚠️  WARNING: {len(warnings)}", file=sys.stderr)
        # Show first 10 warnings
        for issue in warnings[:10]:
            print(f"  - {issue['message']}", file=sys.stderr)
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more warnings", file=sys.stderr)

    if notes:
        print(f"\nℹ️  NOTE: {len(notes)}", file=sys.stderr)
        # Show first 5 notes
        for issue in notes[:5]:
            print(f"  - {issue['message']}", file=sys.stderr)
        if len(notes) > 5:
            print(f"  ... and {len(notes) - 5} more notes", file=sys.stderr)

    # Exit code: 1 for CRITICAL, 2 for WARNING only, 0 for NOTE only
    if critical:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
