#!/usr/bin/env python3
"""
Validate blog commit messages against blog-git-commit conventions.

Blog commits use a subset of Conventional Commits adapted for content:

  <type>[optional scope]: <description>

  [optional body]

Types:
  post    — new blog post added to _posts/
  edit    — update to an existing published post
  draft   — work-in-progress post (not yet published)
  asset   — images, CSS, JS, or other non-post files
  config  — _config.yml, layouts, includes, Gemfile changes

Differences from code commit conventions:
  - Subject max is 72 chars (not 50) — blog titles are naturally longer
  - No imperative mood requirement — titles are descriptive, not commands
  - No BREAKING CHANGE footer — not applicable to content
  - Types are content-specific, not code-change-specific

Exit codes: 0 = valid · 1 = invalid (prints errors)
"""

import re
import sys
from pathlib import Path

VALID_TYPES = {'post', 'edit', 'draft', 'asset', 'config'}
MAX_SUBJECT_LENGTH = 72

_SUBJECT_RE = re.compile(r'^(\w+)(?:\(([^)]*)\))?!?:\s*(.*)$')


def validate_blog_commit(message: str) -> list[str]:
    """
    Validate a blog commit message string.
    Returns a list of error strings — empty list means valid.
    """
    errors = []
    message = message.strip()

    if not message:
        return ["Commit message is empty"]

    lines = message.splitlines()
    subject = lines[0]

    # Parse subject line
    match = _SUBJECT_RE.match(subject)
    if not match:
        return [
            f"Subject must follow '<type>[scope]: <description>'. Got: '{subject}'\n"
            f"  Valid types: {', '.join(sorted(VALID_TYPES))}"
        ]

    type_ = match.group(1)
    scope = match.group(2)   # None if no scope
    description = match.group(3)

    # Validate type
    if type_ not in VALID_TYPES:
        errors.append(
            f"Invalid type '{type_}'. "
            f"Blog commits must use: {', '.join(sorted(VALID_TYPES))}\n"
            f"  (Code types like feat/fix/refactor/docs do not apply to blog posts)"
        )

    # Validate scope — if present must be non-empty
    if scope is not None and not scope.strip():
        errors.append("Scope cannot be empty. Use 'post(java): ...' or 'post: ...' (no parens)")

    # Validate description
    if not description.strip():
        errors.append("Description cannot be empty after the colon")
    elif description.endswith('.'):
        errors.append(
            "Description should not end with a period\n"
            "  (Exception: trailing ? is fine for question-form titles)"
        )

    # Validate subject length
    if len(subject) > MAX_SUBJECT_LENGTH:
        errors.append(
            f"Subject line is {len(subject)} chars (max {MAX_SUBJECT_LENGTH}): '{subject}'"
        )

    # Validate body separation
    if len(lines) > 1 and lines[1].strip() != '':
        errors.append(
            "Second line must be blank — separate subject from body with an empty line"
        )

    return errors


def main() -> int:
    if len(sys.argv) == 2:
        # Validate a file (e.g. git commit-msg hook)
        msg = Path(sys.argv[1]).read_text()
    elif not sys.stdin.isatty():
        msg = sys.stdin.read()
    else:
        print("Usage: validate_blog_commit.py <commit-msg-file>", file=sys.stderr)
        print("       echo 'post: add guide' | validate_blog_commit.py", file=sys.stderr)
        return 1

    errors = validate_blog_commit(msg)
    if errors:
        print("❌ Invalid blog commit message:", file=sys.stderr)
        for e in errors:
            print(f"  • {e}", file=sys.stderr)
        return 1

    print("✅ Blog commit message is valid")
    return 0


if __name__ == '__main__':
    sys.exit(main())
