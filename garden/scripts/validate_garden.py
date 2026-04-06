#!/usr/bin/env python3
"""
Garden integrity validator.

Checks:
1. Every entry in garden files has **ID:** GE-XXXX
2. All GE-IDs are unique across the garden
3. Every GARDEN.md index entry with GE-ID prefix points to an existing entry
4. GARDEN.md counter >= highest GE-ID found in garden files
5. Every GE-ID in a garden file appears in the By Technology section (not just By Label)
6. CHECKED.md pairs reference only valid GE-IDs
7. DISCARDED.md entries reference valid submission GE-IDs
8. Submission files in submissions/ include Submission ID header

Usage: python3 validate_garden.py [garden_root] [--verbose]
       garden_root defaults to ~/claude/knowledge-garden/

Exit codes: 0=clean, 1=errors found, 2=warnings only
"""

import re
import sys
from pathlib import Path

# Garden root: first non-flag positional argument, or default convention
_args = [a for a in sys.argv[1:] if not a.startswith('--')]
GARDEN_ROOT = Path(_args[0]).expanduser().resolve() if _args else Path.home() / "claude" / "knowledge-garden"

GARDEN_MD = GARDEN_ROOT / "GARDEN.md"
CHECKED_MD = GARDEN_ROOT / "CHECKED.md"
DISCARDED_MD = GARDEN_ROOT / "DISCARDED.md"
SUBMISSIONS_DIR = GARDEN_ROOT / "submissions"
EXCLUDE_DIRS = {'.git', 'submissions', 'scripts'}

GE_ID_PATTERN = re.compile(r'GE-(\d{4})')

errors = []
warnings = []
info = []
verbose = '--verbose' in sys.argv


def log_error(msg):
    errors.append(f"ERROR: {msg}")

def log_warning(msg):
    warnings.append(f"WARNING: {msg}")

def log_info(msg):
    if verbose:
        info.append(f"  {msg}")


def get_garden_counter() -> int | None:
    """Read Last assigned ID from GARDEN.md metadata."""
    if not GARDEN_MD.exists():
        log_error("GARDEN.md not found")
        return None
    content = GARDEN_MD.read_text()
    m = re.search(r'\*\*Last assigned ID:\*\*\s*(GE-(\d{4}))', content)
    if not m:
        log_error("GARDEN.md has no 'Last assigned ID' metadata")
        return None
    return int(m.group(2))


def get_garden_index_ids() -> dict[str, str]:
    """Return {ge_id: entry_title} from GARDEN.md index lines (all sections)."""
    if not GARDEN_MD.exists():
        return {}
    results = {}
    content = GARDEN_MD.read_text()
    for m in re.finditer(r'-\s+(GE-\d{4})\s+\[([^\]]+)\]', content):
        results[m.group(1)] = m.group(2)
    return results


def get_by_technology_ids() -> set[str]:
    """Return GE-IDs that appear in the By Technology section of GARDEN.md."""
    if not GARDEN_MD.exists():
        return set()
    content = GARDEN_MD.read_text()
    m = re.search(r'## By Technology\n(.*?)(?:\n---)', content, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'GE-\d{4}', m.group(1)))


def scan_garden_entry_ids() -> dict[str, list[str]]:
    """Scan all garden files (not submissions) for **ID:** GE-XXXX."""
    all_ids: dict[str, list[str]] = {}
    for path in GARDEN_ROOT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in ("GARDEN.md", "CHECKED.md", "DISCARDED.md"):
            continue
        content = path.read_text()
        for m in re.finditer(r'^\*\*ID:\*\*\s+(GE-\d{4})', content, re.MULTILINE):
            ge_id = m.group(1)
            all_ids.setdefault(ge_id, []).append(str(path.relative_to(GARDEN_ROOT)))
    return all_ids


def get_checked_pairs() -> list[tuple[str, str]]:
    """Return list of (id_a, id_b) pairs from CHECKED.md."""
    if not CHECKED_MD.exists():
        return []
    pairs = []
    content = CHECKED_MD.read_text()
    for m in re.finditer(r'\|\s*(GE-\d{4})\s*[×x]\s*(GE-\d{4})\s*\|', content):
        pairs.append((m.group(1), m.group(2)))
    return pairs


def get_discarded_ids() -> list[tuple[str, str]]:
    """Return list of (discarded_ge_id, conflicts_with_ge_id) from DISCARDED.md."""
    if not DISCARDED_MD.exists():
        return []
    results = []
    content = DISCARDED_MD.read_text()
    for m in re.finditer(r'\|\s*(GE-\d{4})\s*\|\s*(GE-\d{4})\s*\|', content):
        results.append((m.group(1), m.group(2)))
    return results


def get_submission_ids() -> dict[str, str]:
    """Return {ge_id: filename} for submissions that declare a Submission ID."""
    results = {}
    if not SUBMISSIONS_DIR.exists():
        return results
    for path in SUBMISSIONS_DIR.glob("*.md"):
        content = path.read_text()
        m = re.search(r'^\*\*Submission ID:\*\*\s+(GE-\d{4})', content, re.MULTILINE)
        if m:
            results[m.group(1)] = path.name
    return results


def validate():
    print(f"Validating garden at {GARDEN_ROOT}\n")

    # 1. Scan garden entry IDs
    entry_ids = scan_garden_entry_ids()
    log_info(f"Found {len(entry_ids)} GE-IDs in garden entries")

    # 2. Check uniqueness
    for ge_id, files in entry_ids.items():
        if len(files) > 1:
            log_error(f"{ge_id} appears in multiple files: {', '.join(files)}")

    # 3. Check counter consistency
    counter = get_garden_counter()
    if counter is not None and entry_ids:
        highest = max(int(gid[3:]) for gid in entry_ids)
        if counter < highest:
            log_error(f"GARDEN.md counter GE-{counter:04d} is BELOW highest entry ID GE-{highest:04d}")
        else:
            log_info(f"Counter GE-{counter:04d} >= highest entry GE-{highest:04d} ✓")

    # 4. Check GARDEN.md index vs actual entries (whole index)
    index_ids = get_garden_index_ids()
    log_info(f"Found {len(index_ids)} GE-IDs in GARDEN.md index")
    for ge_id, title in index_ids.items():
        if ge_id not in entry_ids:
            log_error(f"Index references {ge_id} ({title!r}) but no matching **ID:** in any garden file")
    for ge_id in entry_ids:
        if ge_id not in index_ids:
            log_warning(f"{ge_id} exists in a garden file but is missing from GARDEN.md index")

    # 4b. Check By Technology section specifically
    # Appearing in By Label or By Symptom/Type alone is not sufficient
    tech_ids = get_by_technology_ids()
    log_info(f"Found {len(tech_ids)} GE-IDs in By Technology section")
    for ge_id in entry_ids:
        if ge_id not in tech_ids:
            log_error(f"{ge_id} is missing from GARDEN.md By Technology section"
                      f" (By Label/Symptom alone is not sufficient)")

    # 5. Check CHECKED.md pairs reference valid IDs
    all_known_ids = set(entry_ids.keys()) | set(get_submission_ids().keys())
    for id_a, id_b in get_checked_pairs():
        if id_a not in all_known_ids:
            log_warning(f"CHECKED.md references {id_a} which is not in garden entries or submissions")
        if id_b not in all_known_ids:
            log_warning(f"CHECKED.md references {id_b} which is not in garden entries or submissions")

    # 6. Check DISCARDED.md conflicts point to real entries
    for discarded, conflicts_with in get_discarded_ids():
        if conflicts_with not in entry_ids:
            log_error(f"DISCARDED.md: {discarded} conflicts with {conflicts_with} but {conflicts_with} not found in garden")

    # 7. Check submissions have IDs
    if SUBMISSIONS_DIR.exists():
        sub_files = list(SUBMISSIONS_DIR.glob("*.md"))
        missing_id = [f.name for f in sub_files
                      if not re.search(r'\*\*Submission ID:\*\*', f.read_text())]
        if missing_id:
            log_warning(f"Submissions missing Submission ID header: {', '.join(missing_id)}")

    # Report
    print("\n".join(info))
    if errors:
        print()
        for e in errors:
            print(e)
    if warnings:
        print()
        for w in warnings:
            print(w)
    if not errors and not warnings:
        print("✅ Garden integrity check passed — no issues found")
    elif not errors:
        print(f"\n⚠️  {len(warnings)} warning(s), no errors")
    else:
        print(f"\n❌ {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        sys.exit(1)
    elif warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    validate()
