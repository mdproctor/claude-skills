"""
Utility functions for markdown content processing.
"""

import re


def normalize_anchor(text: str) -> str:
    """Convert heading text to a GitHub-style anchor fragment.

    Matches GitHub's anchor generation algorithm:
    - Lowercase
    - Remove non-word characters (except spaces and hyphens)
    - Replace spaces/hyphens with single hyphen
    - Strip leading/trailing hyphens

    Example: "Hello World!" -> "hello-world"
    """
    anchor = text.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[-\s]+', '-', anchor)
    return anchor.strip('-')
