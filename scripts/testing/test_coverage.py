#!/usr/bin/env python3
"""
Generate test coverage report for skills.

Shows which skills have functional tests, regression test coverage,
and overall test coverage metrics.

Usage:
    python scripts/testing/test_coverage.py --report
    python scripts/testing/test_coverage.py --json
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import find_all_skill_files, get_skill_name_from_path, find_skills_root


def is_user_invocable(skill_name: str, skill_content: str) -> bool:
    """
    Check if skill is user-invocable (vs auto-invoked).

    User-invocable skills are listed in available skills or
    can be invoked with /skill-name.
    """
    # Check if skill description mentions user invocation
    if 'user says' in skill_content.lower() or 'user invokes' in skill_content.lower():
        return True

    # Check Skill Chaining section
    if 'can be invoked independently' in skill_content.lower():
        return True

    # Auto-invoked skills mention "invoked by" or "automatic"
    if 'automatically invoked' in skill_content.lower() or 'auto-invoked' in skill_content.lower():
        return False

    # Default: assume user-invocable
    return True


def has_functional_tests(skill_name: str) -> bool:
    """Check if skill has functional test cases."""
    skills_root = find_skills_root()
    skill_dir = skills_root / skill_name

    # Check for tests/test_cases.json
    test_file = skill_dir / 'tests' / 'test_cases.json'
    return test_file.exists()


def get_functional_test_count(skill_name: str) -> int:
    """Get number of functional test cases."""
    skills_root = find_skills_root()
    test_file = skills_root / skill_name / 'tests' / 'test_cases.json'

    if not test_file.exists():
        return 0

    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data.get('tests', []))
    except:
        return 0


def get_regression_test_coverage() -> Dict[str, List[str]]:
    """
    Get regression test coverage.

    Returns dict of issue_id -> list of skills it validates
    """
    skills_root = find_skills_root()
    regression_dir = skills_root / 'tests' / 'regression'

    if not regression_dir.exists():
        return {}

    coverage = {}
    for test_file in regression_dir.glob('issue-*.json'):
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                issue_id = data.get('issue_id', 'unknown')

                # Extract affected skills from test cases
                skills = set()
                for test_case in data.get('test_cases', []):
                    command = test_case.get('command', '')
                    # Try to extract skill name from command
                    # e.g., "python scripts/validation/validate_cso.py skill-name/"
                    if '/' in command:
                        parts = command.split('/')
                        for part in parts:
                            if part.endswith('.py') or part.endswith('/'):
                                continue
                            # This might be a skill name
                            skill_candidate = part.strip()
                            if skill_candidate and not skill_candidate.startswith('-'):
                                skills.add(skill_candidate)

                coverage[issue_id] = list(skills)
        except:
            continue

    return coverage


def generate_coverage_report() -> Dict:
    """Generate complete test coverage report."""
    skill_files = find_all_skill_files()

    user_invocable = []
    auto_invoked = []

    for skill_path in skill_files:
        skill_name = get_skill_name_from_path(skill_path)

        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        is_user = is_user_invocable(skill_name, content)
        has_tests = has_functional_tests(skill_name)
        test_count = get_functional_test_count(skill_name)

        skill_info = {
            'name': skill_name,
            'has_functional_tests': has_tests,
            'test_count': test_count,
            'coverage_percent': 100 if has_tests else 0
        }

        if is_user:
            user_invocable.append(skill_info)
        else:
            auto_invoked.append(skill_info)

    # Get regression test coverage
    regression_coverage = get_regression_test_coverage()

    # Calculate overall metrics
    total_skills = len(user_invocable) + len(auto_invoked)
    user_with_tests = sum(1 for s in user_invocable if s['has_functional_tests'])
    auto_with_tests = sum(1 for s in auto_invoked if s['has_functional_tests'])
    total_with_tests = user_with_tests + auto_with_tests

    overall_coverage = (total_with_tests / total_skills * 100) if total_skills > 0 else 0

    return {
        'user_invocable_skills': user_invocable,
        'auto_invoked_skills': auto_invoked,
        'regression_coverage': regression_coverage,
        'metrics': {
            'total_skills': total_skills,
            'user_invocable_count': len(user_invocable),
            'auto_invoked_count': len(auto_invoked),
            'user_with_tests': user_with_tests,
            'auto_with_tests': auto_with_tests,
            'total_with_tests': total_with_tests,
            'overall_coverage_percent': round(overall_coverage, 1),
            'regression_test_count': len(regression_coverage)
        }
    }


def print_report(report: Dict):
    """Print coverage report in human-readable format."""
    metrics = report['metrics']

    print("\n" + "=" * 70)
    print("SKILL TEST COVERAGE REPORT")
    print("=" * 70)

    print(f"\nTotal skills: {metrics['total_skills']}")
    print(f"User-invocable: {metrics['user_invocable_count']}")
    print(f"Auto-invoked: {metrics['auto_invoked_count']}")
    print(f"\nSkills with tests: {metrics['total_with_tests']}/{metrics['total_skills']} ({metrics['overall_coverage_percent']}%)")

    # User-invocable skills
    print("\n" + "-" * 70)
    print("USER-INVOCABLE SKILLS")
    print("-" * 70)

    for skill in sorted(report['user_invocable_skills'], key=lambda x: x['name']):
        status = "✅" if skill['has_functional_tests'] else "❌"
        test_info = f"{skill['test_count']} tests" if skill['has_functional_tests'] else "no tests"
        print(f"  {status} {skill['name']:30} {test_info}")

    print(f"\nCoverage: {metrics['user_with_tests']}/{metrics['user_invocable_count']} " +
          f"({round(metrics['user_with_tests']/metrics['user_invocable_count']*100) if metrics['user_invocable_count'] > 0 else 0}%)")

    # Auto-invoked skills
    print("\n" + "-" * 70)
    print("AUTO-INVOKED SKILLS")
    print("-" * 70)

    for skill in sorted(report['auto_invoked_skills'], key=lambda x: x['name']):
        status = "✅" if skill['has_functional_tests'] else "❌"
        test_info = f"{skill['test_count']} tests" if skill['has_functional_tests'] else "no tests"
        print(f"  {status} {skill['name']:30} {test_info}")

    print(f"\nCoverage: {metrics['auto_with_tests']}/{metrics['auto_invoked_count']} " +
          f"({round(metrics['auto_with_tests']/metrics['auto_invoked_count']*100) if metrics['auto_invoked_count'] > 0 else 0}%)")

    # Regression tests
    print("\n" + "-" * 70)
    print("REGRESSION TEST COVERAGE")
    print("-" * 70)

    regression = report['regression_coverage']
    print(f"\nKnown issues: {len(regression)}")
    for issue_id, skills in sorted(regression.items()):
        skills_str = ', '.join(skills) if skills else 'general validation'
        print(f"  Issue #{issue_id}: {skills_str}")

    print(f"\nRegression tests: {len(regression)}")

    # Overall
    print("\n" + "=" * 70)
    print(f"OVERALL COVERAGE: {metrics['overall_coverage_percent']}% ({metrics['total_with_tests']}/{metrics['total_skills']} skills)")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate test coverage report')
    parser.add_argument('--report', action='store_true', help='Generate coverage report')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    # Generate report
    report = generate_coverage_report()

    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == '__main__':
    main()
