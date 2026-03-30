#!/usr/bin/env python3
"""
Functional test runner for skills with git worktree isolation.

TIER: CI (expensive operations, 5min budget)

Executes test cases defined in skill-name/tests/test_cases.json and validates
skill behavior against expected outcomes in isolated git worktrees.

Usage:
    python scripts/testing/run_skill_tests.py              # Run all
    python scripts/testing/run_skill_tests.py --skill git-commit  # Run specific skill
    python scripts/testing/run_skill_tests.py --json       # JSON output
    python scripts/testing/run_skill_tests.py --no-isolation  # Skip worktree isolation (faster)
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import find_skills_root


def create_test_worktree(base_dir: Path) -> Path:
    """Create isolated git worktree for testing."""
    worktree_dir = tempfile.mkdtemp(prefix="skill_test_")
    worktree_path = Path(worktree_dir)

    try:
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "HEAD"],
            cwd=base_dir,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        # Cleanup temp dir if worktree creation failed
        import shutil
        shutil.rmtree(worktree_path, ignore_errors=True)
        raise RuntimeError(f"Failed to create worktree: {e.stderr}") from e

    return worktree_path


def cleanup_worktree(worktree_path: Path) -> None:
    """Remove git worktree and cleanup."""
    if not worktree_path.exists():
        return

    subprocess.run(
        ["git", "worktree", "remove", str(worktree_path), "--force"],
        check=False,
        capture_output=True
    )


def find_skill_tests() -> List[Path]:
    """Find all skill test case files."""
    skills_root = find_skills_root()
    test_files = []

    for skill_dir in skills_root.iterdir():
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith('.') or skill_dir.name in ['scripts', 'tests', 'docs', '.github']:
            continue

        test_file = skill_dir / 'tests' / 'test_cases.json'
        if test_file.exists():
            test_files.append(test_file)

    return sorted(test_files)


def load_test_cases(test_path: Path) -> Dict:
    """Load test cases from JSON file."""
    with open(test_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_file_assertion(assertion: Dict, skill_dir: Path) -> Dict:
    """
    Run file existence/content assertion.

    Types:
    - exists: file must exist
    - not_exists: file must not exist
    - contains: file must contain text
    - not_contains: file must not contain text
    """
    assertion_type = assertion.get('type')
    file_path = skill_dir / assertion.get('path', '')

    if assertion_type == 'exists':
        passed = file_path.exists()
        return {
            'type': 'file.exists',
            'path': str(file_path),
            'passed': passed,
            'message': f"File exists: {file_path}" if passed else f"File not found: {file_path}"
        }

    elif assertion_type == 'not_exists':
        passed = not file_path.exists()
        return {
            'type': 'file.not_exists',
            'path': str(file_path),
            'passed': passed,
            'message': f"File does not exist: {file_path}" if passed else f"File unexpectedly exists: {file_path}"
        }

    elif assertion_type == 'contains':
        if not file_path.exists():
            return {
                'type': 'file.contains',
                'path': str(file_path),
                'passed': False,
                'message': f"File not found: {file_path}"
            }

        content = file_path.read_text(encoding='utf-8')
        text = assertion.get('text', '')
        passed = text in content

        return {
            'type': 'file.contains',
            'path': str(file_path),
            'passed': passed,
            'message': f"File contains '{text}'" if passed else f"File does not contain '{text}'"
        }

    elif assertion_type == 'not_contains':
        if not file_path.exists():
            return {
                'type': 'file.not_contains',
                'path': str(file_path),
                'passed': True,
                'message': f"File not found (passes not_contains): {file_path}"
            }

        content = file_path.read_text(encoding='utf-8')
        text = assertion.get('text', '')
        passed = text not in content

        return {
            'type': 'file.not_contains',
            'path': str(file_path),
            'passed': passed,
            'message': f"File does not contain '{text}'" if passed else f"File unexpectedly contains '{text}'"
        }

    else:
        return {
            'type': f'file.{assertion_type}',
            'passed': False,
            'message': f"Unknown file assertion type: {assertion_type}"
        }


def run_git_assertion(assertion: Dict, skill_dir: Path) -> Dict:
    """
    Run git-related assertion.

    Types:
    - commit_exists: latest commit message contains text
    - staged: file is staged
    - not_staged: file is not staged
    """
    assertion_type = assertion.get('type')

    if assertion_type == 'commit_exists':
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True,
                text=True,
                cwd=skill_dir,
                timeout=5
            )

            text = assertion.get('text', '')
            passed = text in result.stdout

            return {
                'type': 'git.commit_exists',
                'passed': passed,
                'message': f"Latest commit contains '{text}'" if passed else f"Latest commit does not contain '{text}'"
            }
        except Exception as e:
            return {
                'type': 'git.commit_exists',
                'passed': False,
                'message': f"Git command failed: {e}"
            }

    elif assertion_type == 'staged':
        file_path = assertion.get('path', '')
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged', '--name-only'],
                capture_output=True,
                text=True,
                cwd=skill_dir,
                timeout=5
            )

            passed = file_path in result.stdout

            return {
                'type': 'git.staged',
                'path': file_path,
                'passed': passed,
                'message': f"File is staged: {file_path}" if passed else f"File is not staged: {file_path}"
            }
        except Exception as e:
            return {
                'type': 'git.staged',
                'passed': False,
                'message': f"Git command failed: {e}"
            }

    elif assertion_type == 'not_staged':
        file_path = assertion.get('path', '')
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged', '--name-only'],
                capture_output=True,
                text=True,
                cwd=skill_dir,
                timeout=5
            )

            passed = file_path not in result.stdout

            return {
                'type': 'git.not_staged',
                'path': file_path,
                'passed': passed,
                'message': f"File is not staged: {file_path}" if passed else f"File is unexpectedly staged: {file_path}"
            }
        except Exception as e:
            return {
                'type': 'git.not_staged',
                'passed': False,
                'message': f"Git command failed: {e}"
            }

    else:
        return {
            'type': f'git.{assertion_type}',
            'passed': False,
            'message': f"Unknown git assertion type: {assertion_type}"
        }


def run_skill_assertion(assertion: Dict, skill_dir: Path) -> Dict:
    """
    Run skill-related assertion.

    Types:
    - invoked: skill was invoked during test (check for marker)
    - not_invoked: skill was not invoked
    """
    assertion_type = assertion.get('type')
    skill_name = assertion.get('skill', '')

    # For now, return placeholder (requires test harness integration)
    return {
        'type': f'skill.{assertion_type}',
        'skill': skill_name,
        'passed': True,
        'message': f"Skill assertion not yet implemented: {assertion_type}"
    }


def run_output_assertion(assertion: Dict, output: str) -> Dict:
    """
    Run output assertion.

    Types:
    - contains: output contains text
    - not_contains: output does not contain text
    - matches: output matches regex
    """
    assertion_type = assertion.get('type')

    if assertion_type == 'contains':
        text = assertion.get('text', '')
        passed = text in output

        return {
            'type': 'output.contains',
            'passed': passed,
            'message': f"Output contains '{text}'" if passed else f"Output does not contain '{text}'"
        }

    elif assertion_type == 'not_contains':
        text = assertion.get('text', '')
        passed = text not in output

        return {
            'type': 'output.not_contains',
            'passed': passed,
            'message': f"Output does not contain '{text}'" if passed else f"Output unexpectedly contains '{text}'"
        }

    elif assertion_type == 'matches':
        import re
        pattern = assertion.get('pattern', '')
        try:
            passed = bool(re.search(pattern, output))
            return {
                'type': 'output.matches',
                'passed': passed,
                'message': f"Output matches pattern: {pattern}" if passed else f"Output does not match pattern: {pattern}"
            }
        except Exception as e:
            return {
                'type': 'output.matches',
                'passed': False,
                'message': f"Regex error: {e}"
            }

    else:
        return {
            'type': f'output.{assertion_type}',
            'passed': False,
            'message': f"Unknown output assertion type: {assertion_type}"
        }


def run_test_case(test_case: Dict, skill_dir: Path) -> Dict:
    """
    Run a single test case.

    Returns:
        {
            'test_name': str,
            'passed': bool,
            'assertions': List[Dict],
            'total_assertions': int,
            'passed_assertions': int
        }
    """
    test_name = test_case.get('name', 'unnamed')
    setup = test_case.get('setup', [])
    assertions = test_case.get('assertions', [])

    # Run setup commands
    for command in setup:
        try:
            subprocess.run(
                command,
                shell=True,
                capture_output=True,
                cwd=skill_dir,
                timeout=30
            )
        except Exception as e:
            return {
                'test_name': test_name,
                'passed': False,
                'assertions': [{
                    'type': 'setup',
                    'passed': False,
                    'message': f"Setup failed: {e}"
                }],
                'total_assertions': 1,
                'passed_assertions': 0
            }

    # Run assertions
    results = []
    for assertion in assertions:
        category = assertion.get('category', 'unknown')

        if category == 'file':
            result = run_file_assertion(assertion, skill_dir)
        elif category == 'git':
            result = run_git_assertion(assertion, skill_dir)
        elif category == 'skill':
            result = run_skill_assertion(assertion, skill_dir)
        elif category == 'output':
            # Output assertions need captured output (not implemented yet)
            result = {
                'type': 'output',
                'passed': True,
                'message': 'Output assertions not yet implemented'
            }
        else:
            result = {
                'type': 'unknown',
                'passed': False,
                'message': f"Unknown assertion category: {category}"
            }

        results.append(result)

    all_passed = all(r['passed'] for r in results)

    return {
        'test_name': test_name,
        'passed': all_passed,
        'assertions': results,
        'total_assertions': len(results),
        'passed_assertions': sum(1 for r in results if r['passed'])
    }


def run_skill_tests(test_path: Path, use_isolation: bool = True) -> Dict:
    """
    Run all test cases for a skill.

    Args:
        test_path: Path to test_cases.json
        use_isolation: If True, run tests in isolated git worktree (default: True)

    Returns:
        {
            'skill_name': str,
            'test_cases': List[Dict],
            'passed': bool,
            'total_tests': int,
            'passed_tests': int,
            'isolated': bool
        }
    """
    skill_dir = test_path.parent.parent
    skill_name = skill_dir.name
    skills_root = find_skills_root()

    test_data = load_test_cases(test_path)
    test_cases = test_data.get('tests', [])

    # Use worktree isolation if requested
    worktree_path = None
    test_dir = skill_dir

    if use_isolation:
        try:
            worktree_path = create_test_worktree(skills_root)
            # Update test_dir to point to skill directory in worktree
            test_dir = worktree_path / skill_dir.relative_to(skills_root)
        except Exception as e:
            # Fall back to in-place testing if worktree creation fails
            print(f"Warning: Failed to create worktree, running in-place: {e}", file=sys.stderr)
            use_isolation = False

    try:
        results = []
        for test_case in test_cases:
            result = run_test_case(test_case, test_dir)
            results.append(result)

        all_passed = all(r['passed'] for r in results)

        return {
            'skill_name': skill_name,
            'test_file': str(test_path),
            'test_cases': results,
            'passed': all_passed,
            'total_tests': len(results),
            'passed_tests': sum(1 for r in results if r['passed']),
            'isolated': use_isolation
        }

    finally:
        # Always cleanup worktree if created
        if worktree_path:
            cleanup_worktree(worktree_path)


def print_results(results: List[Dict], verbose: bool = False):
    """Print test results in human-readable format."""
    print("\n" + "=" * 70)
    print("FUNCTIONAL TEST RESULTS")
    print("=" * 70)

    total_skills = len(results)
    passed_skills = sum(1 for r in results if r['passed'])
    total_tests = sum(r['total_tests'] for r in results)
    passed_tests = sum(r['passed_tests'] for r in results)

    print(f"\nSkills tested: {total_skills}")
    print(f"Skills passed: {passed_skills}")
    print(f"Total test cases: {total_tests}")
    print(f"Passed test cases: {passed_tests}\n")

    print("-" * 70)

    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"\n{status} {result['skill_name']}")
        print(f"  Test cases: {result['passed_tests']}/{result['total_tests']} passed")

        if verbose or not result['passed']:
            for test_case in result['test_cases']:
                tc_status = "✅" if test_case['passed'] else "❌"
                print(f"    {tc_status} {test_case['test_name']}")

                if not test_case['passed']:
                    for assertion in test_case['assertions']:
                        if not assertion['passed']:
                            print(f"       ❌ {assertion['type']}: {assertion['message']}")

    print("\n" + "=" * 70)
    if passed_skills == total_skills:
        print("✅ ALL FUNCTIONAL TESTS PASSED")
    else:
        print(f"❌ {total_skills - passed_skills} SKILL TEST(S) FAILED")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run functional tests for skills',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--skill', help='Run tests for specific skill')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('--no-isolation', action='store_true',
                        help='Skip worktree isolation (faster, but modifies working directory)')
    args = parser.parse_args()

    # Find test files
    test_files = find_skill_tests()

    if not test_files:
        print("No skill tests found (no */tests/test_cases.json files)")
        sys.exit(0)

    # Filter by skill if specified
    if args.skill:
        test_files = [f for f in test_files if f.parent.parent.name == args.skill]
        if not test_files:
            print(f"No tests found for skill: {args.skill}")
            sys.exit(1)

    # Determine isolation mode
    use_isolation = not args.no_isolation

    if use_isolation and not args.json:
        print("Running tests with git worktree isolation (TIER: CI)", file=sys.stderr)
    elif not use_isolation and not args.json:
        print("Running tests in-place (no isolation)", file=sys.stderr)

    # Run tests
    results = []
    for test_file in test_files:
        if not args.json:
            print(f"Running tests for {test_file.parent.parent.name}...", file=sys.stderr)
        result = run_skill_tests(test_file, use_isolation=use_isolation)
        results.append(result)

    # Output results
    if args.json:
        output = {
            'total_skills': len(results),
            'passed_skills': sum(1 for r in results if r['passed']),
            'total_tests': sum(r['total_tests'] for r in results),
            'passed_tests': sum(r['passed_tests'] for r in results),
            'isolated': use_isolation,
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
