#!/usr/bin/env python3
"""
Run regression tests to ensure known issues don't recur.

Usage:
    python scripts/testing/run_regression_tests.py              # Run all
    python scripts/testing/run_regression_tests.py --issue 001  # Run specific issue
    python scripts/testing/run_regression_tests.py --json       # JSON output
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import find_skills_root


def find_regression_tests() -> List[Path]:
    """Find all regression test files."""
    skills_root = find_skills_root()
    tests_dir = skills_root / 'tests' / 'regression'

    if not tests_dir.exists():
        return []

    return sorted(tests_dir.glob('issue-*.json'))


def load_regression_test(test_path: Path) -> Dict:
    """Load regression test from JSON file."""
    with open(test_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_test_case(test_case: Dict, test_path: Path) -> Dict:
    """
    Run a single test case from regression test.

    Returns:
        {
            'test_name': str,
            'command': str,
            'passed': bool,
            'exit_code': int,
            'output': str,
            'error': str
        }
    """
    test_name = test_case.get('test_name', 'unnamed')
    command = test_case.get('command', '')
    expected_exit_code = test_case.get('expected_exit_code', 0)
    expected_output_contains = test_case.get('expected_output_contains')
    expected_output_not_contains = test_case.get('expected_output_not_contains')

    try:
        # Run command from skills root
        skills_root = find_skills_root()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=skills_root,
            timeout=30
        )

        # Check exit code
        exit_code_match = result.returncode == expected_exit_code

        # Check output contains/not contains
        output_match = True
        if expected_output_contains:
            output_match = output_match and (expected_output_contains in result.stdout or expected_output_contains in result.stderr)
        if expected_output_not_contains:
            output_match = output_match and (expected_output_not_contains not in result.stdout and expected_output_not_contains not in result.stderr)

        passed = exit_code_match and output_match

        return {
            'test_name': test_name,
            'command': command,
            'passed': passed,
            'exit_code': result.returncode,
            'expected_exit_code': expected_exit_code,
            'output': result.stdout,
            'error': result.stderr,
            'exit_code_match': exit_code_match,
            'output_match': output_match
        }

    except subprocess.TimeoutExpired:
        return {
            'test_name': test_name,
            'command': command,
            'passed': False,
            'exit_code': -1,
            'expected_exit_code': expected_exit_code,
            'output': '',
            'error': 'Test timed out after 30 seconds',
            'exit_code_match': False,
            'output_match': False
        }
    except Exception as e:
        return {
            'test_name': test_name,
            'command': command,
            'passed': False,
            'exit_code': -1,
            'expected_exit_code': expected_exit_code,
            'output': '',
            'error': str(e),
            'exit_code_match': False,
            'output_match': False
        }


def run_regression_test(test_path: Path) -> Dict:
    """
    Run all test cases in a regression test.

    Returns:
        {
            'issue_id': str,
            'title': str,
            'test_cases': List[Dict],
            'passed': bool
        }
    """
    test_data = load_regression_test(test_path)

    issue_id = test_data.get('issue_id', 'unknown')
    title = test_data.get('title', 'Untitled')
    test_cases = test_data.get('test_cases', [])

    results = []
    for test_case in test_cases:
        result = run_test_case(test_case, test_path)
        results.append(result)

    all_passed = all(r['passed'] for r in results)

    return {
        'issue_id': issue_id,
        'title': title,
        'test_file': str(test_path.name),
        'test_cases': results,
        'passed': all_passed,
        'total_tests': len(results),
        'passed_tests': sum(1 for r in results if r['passed'])
    }


def print_results(results: List[Dict], verbose: bool = False):
    """Print test results in human-readable format."""
    print("\n" + "=" * 70)
    print("REGRESSION TEST RESULTS")
    print("=" * 70)

    total_issues = len(results)
    passed_issues = sum(1 for r in results if r['passed'])
    total_tests = sum(r['total_tests'] for r in results)
    passed_tests = sum(r['passed_tests'] for r in results)

    print(f"\nIssues tested: {total_issues}")
    print(f"Issues passed: {passed_issues}")
    print(f"Total test cases: {total_tests}")
    print(f"Passed test cases: {passed_tests}\n")

    print("-" * 70)

    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"\n{status} Issue #{result['issue_id']}: {result['title']}")
        print(f"  Test file: {result['test_file']}")
        print(f"  Test cases: {result['passed_tests']}/{result['total_tests']} passed")

        if verbose or not result['passed']:
            for test_case in result['test_cases']:
                tc_status = "✅" if test_case['passed'] else "❌"
                print(f"    {tc_status} {test_case['test_name']}")
                if not test_case['passed']:
                    print(f"       Command: {test_case['command']}")
                    print(f"       Expected exit: {test_case['expected_exit_code']}, Got: {test_case['exit_code']}")
                    if test_case['error']:
                        print(f"       Error: {test_case['error']}")

    print("\n" + "=" * 70)
    if passed_issues == total_issues:
        print("✅ ALL REGRESSION TESTS PASSED")
    else:
        print(f"❌ {total_issues - passed_issues} REGRESSION TEST(S) FAILED")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run regression tests for known issues',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--issue', help='Run specific issue number (e.g., 001)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    # Find regression tests
    test_files = find_regression_tests()

    if not test_files:
        print("No regression tests found in tests/regression/")
        sys.exit(0)

    # Filter by issue if specified
    if args.issue:
        test_files = [f for f in test_files if f.name.startswith(f'issue-{args.issue}')]
        if not test_files:
            print(f"No regression test found for issue {args.issue}")
            sys.exit(1)

    # Run tests
    results = []
    for test_file in test_files:
        if not args.json:
            print(f"Running {test_file.name}...", file=sys.stderr)
        result = run_regression_test(test_file)
        results.append(result)

    # Output results
    if args.json:
        output = {
            'total_issues': len(results),
            'passed_issues': sum(1 for r in results if r['passed']),
            'total_tests': sum(r['total_tests'] for r in results),
            'passed_tests': sum(r['passed_tests'] for r in results),
            'results': results
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(results, verbose=args.verbose)

    # Exit code
    all_passed = all(r['passed'] for r in results)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
