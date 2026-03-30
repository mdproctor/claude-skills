#!/usr/bin/env python3
"""
Document Group Caching

Caches discovered document groups to avoid re-parsing on every sync.
Cache is stored in .doc-cache.json (gitignored).

Cache invalidation:
- Primary file structure changed (sha256 mismatch)
- Cache older than 24 hours
- Cache file corrupted
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

CACHE_FILE = Path(".doc-cache.json")
CACHE_MAX_AGE_HOURS = 24


def get_cached_group(primary_file: Path):
    """
    Load cached DocumentGroup if valid.

    Args:
        primary_file: Primary document path

    Returns:
        DocumentGroup if cached and valid, None otherwise
    """
    # Import here to avoid circular dependency
    from scripts.document_discovery import DocumentGroup, ModuleFile

    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        # Cache corrupted, delete and return None
        CACHE_FILE.unlink(missing_ok=True)
        return None

    primary_str = str(primary_file.resolve())

    if primary_str not in cache_data:
        return None

    entry = cache_data[primary_str]

    # Check if cache is stale
    if is_cache_stale_entry(entry):
        return None

    # Check if cache_key matches (file structure changed)
    current_key = compute_cache_key(primary_file)
    if entry.get('cache_key') != current_key:
        return None

    # Reconstruct DocumentGroup from cache
    try:
        modules = [
            ModuleFile(
                path=Path(m['path']),
                relationship=m['relationship']
            )
            for m in entry.get('modules', [])
        ]

        group = DocumentGroup(
            primary_file=Path(entry['primary']),
            modules=modules,
            discovered_via=entry.get('discovered_via', 'auto'),
            cache_key=entry.get('cache_key', '')
        )

        return group

    except (KeyError, TypeError):
        # Cache entry malformed
        return None


def cache_group(group) -> None:
    """
    Save DocumentGroup to cache.

    Args:
        group: DocumentGroup to cache
    """
    # Load existing cache or create new
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            cache_data = {}
    else:
        cache_data = {}

    # Add/update entry
    primary_str = str(group.primary_file.resolve())

    cache_data[primary_str] = {
        'primary': str(group.primary_file),
        'modules': [
            {
                'path': str(m.path),
                'relationship': m.relationship
            }
            for m in group.modules
        ],
        'discovered_via': group.discovered_via,
        'cache_key': group.cache_key,
        'timestamp': datetime.now().isoformat()
    }

    # Write cache
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    except IOError as e:
        # Cache write failed, log but don't crash
        import sys
        print(f"⚠️  Warning: Failed to write cache: {e}", file=sys.stderr)


def invalidate_cache(primary_file: Path) -> None:
    """
    Clear cache entry for a primary file.

    Args:
        primary_file: Primary document path
    """
    if not CACHE_FILE.exists():
        return

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    primary_str = str(primary_file.resolve())

    if primary_str in cache_data:
        del cache_data[primary_str]

        # Write back
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except IOError:
            pass


def compute_cache_key(primary_file: Path) -> str:
    """
    Compute SHA256 of primary file structure (links, includes, section refs).
    Changes when file references change, not when content changes.

    Args:
        primary_file: Primary document path

    Returns:
        SHA256 hash as hex string
    """
    if not primary_file.exists():
        return ""

    # Read file and extract only the structural elements
    with open(primary_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract structural elements for hashing
    structural_content = []

    # Extract all markdown links
    import re
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    structural_content.extend(str(link) for link in links)

    # Extract include directives
    includes = re.findall(r'<!--\s*include:\s*([^\s]+)\s*-->', content, re.IGNORECASE)
    structural_content.extend(includes)

    # Extract section references
    section_refs = re.findall(r'§\s+[^(]+\s+(?:in|\()\s*([^\s)]+\.md)', content)
    structural_content.extend(section_refs)

    # Hash the structural content
    content_to_hash = '\n'.join(sorted(structural_content))
    return hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()


def is_cache_stale_entry(entry: dict) -> bool:
    """
    Check if cache entry is stale (older than CACHE_MAX_AGE_HOURS).

    Args:
        entry: Cache entry dict

    Returns:
        True if stale, False if still valid
    """
    if 'timestamp' not in entry:
        return True

    try:
        timestamp = datetime.fromisoformat(entry['timestamp'])
        age = datetime.now() - timestamp
        return age > timedelta(hours=CACHE_MAX_AGE_HOURS)
    except (ValueError, TypeError):
        return True
