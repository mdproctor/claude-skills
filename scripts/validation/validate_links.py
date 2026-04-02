#!/usr/bin/env python3
"""
TIER: PUSH (<30s with parallel requests)

External URL validator — checks all markdown files for broken links.
Reports WARNING (not CRITICAL) since URLs can be temporarily unavailable.
"""

import sys
import re
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.common import (
    ValidationIssue, ValidationResult, Severity,
    find_skills_root, print_summary
)

# Domains that are placeholders or intentionally unreachable
SKIP_DOMAINS = {'example.com', 'localhost', '127.0.0.1', '0.0.0.0'}

# Template markers that indicate a URL is not a real URL
TEMPLATE_MARKERS = ('{', '<', '[')

# Trailing punctuation to strip from extracted URLs
TRAILING_PUNCT = '.,:;!?)}>'

# HTTP status codes that indicate bot-blocking (treat as OK)
BOT_BLOCKING_CODES = {403, 429, 503}

USER_AGENT = 'cc-praxis-validator/1.0'

URL_PATTERN = re.compile(r'https?://[^\s\)\]\>"\']+')


def find_all_md_files(root: Path) -> List[Path]:
    """Find all .md files under root, skipping .git/ directories."""
    md_files = []
    for md_file in root.rglob('*.md'):
        if '.git' not in md_file.parts:
            md_files.append(md_file)
    return sorted(md_files)


def extract_urls_from_file(file_path: Path) -> List[Tuple[str, int]]:
    """Extract (url, line_number) pairs from a markdown file."""
    urls = []
    try:
        lines = file_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return urls

    for line_no, line in enumerate(lines, 1):
        for match in URL_PATTERN.finditer(line):
            url = match.group(0).rstrip(TRAILING_PUNCT)

            # Skip template placeholders
            if any(marker in url for marker in TEMPLATE_MARKERS):
                continue

            # Skip known skip domains
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                hostname = parsed.hostname or ''
            except Exception:
                continue

            if any(hostname == domain or hostname.endswith('.' + domain)
                   for domain in SKIP_DOMAINS):
                continue

            urls.append((url, line_no))

    return urls


def check_url(url: str) -> Tuple[str, bool, str]:
    """
    Check a single URL. Returns (url, is_ok, reason).
    is_ok=True means no issue should be reported.
    """
    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={'User-Agent': USER_AGENT},
            stream=True,  # Avoid downloading full body
        )
        response.close()
        status = response.status_code

        if 200 <= status < 400:
            return url, True, ''
        if status in BOT_BLOCKING_CODES:
            return url, True, ''  # Treat bot-blocking as OK
        return url, False, f'HTTP {status}'

    except requests.exceptions.Timeout:
        return url, False, 'Connection timed out'
    except requests.exceptions.ConnectionError as exc:
        return url, False, f'Connection error: {exc}'
    except requests.exceptions.RequestException as exc:
        return url, False, f'Request failed: {exc}'


def validate_links(file_paths: List[Path]) -> ValidationResult:
    """Check all external URLs in the given markdown files."""
    result = ValidationResult(
        validator_name='External Link Validation',
        files_checked=len(file_paths),
    )

    # Collect all (url, file_path, line_no) triples, deduplicated by URL
    url_to_locations: Dict[str, List[Tuple[Path, int]]] = {}
    for file_path in file_paths:
        for url, line_no in extract_urls_from_file(file_path):
            url_to_locations.setdefault(url, []).append((file_path, line_no))

    if not url_to_locations:
        return result

    # Check each unique URL in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {
            executor.submit(check_url, url): url
            for url in url_to_locations
        }
        for future in as_completed(future_to_url):
            url, is_ok, reason = future.result()
            if not is_ok:
                # Report the first occurrence only (file + line) for brevity
                file_path, line_no = url_to_locations[url][0]
                result.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    file_path=str(file_path),
                    line_number=line_no,
                    message=f'Broken link: {url} — {reason}',
                    fix_suggestion='Verify the URL is correct or remove/update the link',
                ))

    return result


def main():
    """Main validation entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate external URLs in markdown files')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('files', nargs='*', help='Specific files to check (default: all .md files)')
    args = parser.parse_args()

    if args.files:
        file_paths = [Path(f) for f in args.files]
    else:
        root = find_skills_root()
        file_paths = find_all_md_files(root)

    result = validate_links(file_paths)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_summary(result, verbose=args.verbose)

    sys.exit(result.exit_code)


if __name__ == '__main__':
    main()
