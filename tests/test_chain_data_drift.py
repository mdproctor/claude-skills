#!/usr/bin/env python3
"""
Tests for Section 4.2 of the web installer test spec:
Validates that the const CHAIN object in docs/index.html matches
the CHAINING_TRUTH dict in this test suite.

These tests catch drift between the JS chain graph data and the
Python ground truth, without requiring any server to be running.
"""

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.test_mockup_chaining import ALL_SKILLS, CHAINING_TRUTH


# ── Parser for the JS CHAIN object ───────────────────────────────────────────

def parse_chain_from_html(html_path: Path) -> dict:
    """
    Extract and parse the const CHAIN = {...}; block from index.html.

    The JS object uses single-quoted string keys and Python-style list notation
    (from the generator). We convert it to valid JSON by normalising quotes,
    then parse with json.loads.

    Returns {skill_name: {'parents': [...], 'children': [...]}, ...}
    """
    html = html_path.read_text(encoding='utf-8')
    m = re.search(r'const CHAIN\s*=\s*\{([\s\S]*?)\};\s*\n', html)
    if not m:
        raise ValueError('const CHAIN not found in index.html')

    block = m.group(1)

    # Parse each entry: 'name': {parents:[...],children:[...]}
    chain: dict = {}
    for entry in re.finditer(
        r"'([^']+)':\s*\{parents:\[([^\]]*)\],children:\[([^\]]*)\]\}",
        block,
    ):
        name     = entry.group(1)
        parents  = [s.strip(" '") for s in entry.group(2).split(',') if s.strip(" '")]
        children = [s.strip(" '") for s in entry.group(3).split(',') if s.strip(" '")]
        chain[name] = {'parents': parents, 'children': children}

    return chain


HTML_PATH = REPO_ROOT / 'docs' / 'index.html'
CHAIN = parse_chain_from_html(HTML_PATH)


# ── 4.2.1 CHAIN.parents matches CHAINING_TRUTH.invoked_by ────────────────────

class TestChainParentsMatchTruth(unittest.TestCase):
    """
    4.2.1 — For every skill, CHAIN[S].parents == CHAINING_TRUTH[S].invoked_by.

    CHAIN.parents uses invoked_by semantics: the set of skills that invoke this one.
    """

    def test_every_skill_parents_match_invoked_by(self):
        mismatches = []
        for skill in sorted(ALL_SKILLS):
            if skill not in CHAIN:
                continue  # caught by test_4_2_3
            if skill not in CHAINING_TRUTH:
                continue

            chain_parents = set(CHAIN[skill]['parents'])
            truth_invoked = set(CHAINING_TRUTH[skill]['invoked_by'])

            missing = truth_invoked - chain_parents
            extra   = chain_parents - truth_invoked

            if missing or extra:
                mismatches.append(
                    f"  [{skill}] parents mismatch: "
                    f"missing={sorted(missing)}, extra={sorted(extra)}"
                )

        if mismatches:
            self.fail(
                'CHAIN.parents drifted from CHAINING_TRUTH.invoked_by:\n'
                + '\n'.join(mismatches)
                + '\n\nFix: run  python3 scripts/generate_web_app_data.py'
            )


# ── 4.2.2 CHAIN.children matches CHAINING_TRUTH.chains_to ───────────────────

class TestChainChildrenMatchTruth(unittest.TestCase):
    """
    4.2.2 — For every skill, CHAIN[S].children == CHAINING_TRUTH[S].chains_to.
    """

    def test_every_skill_children_match_chains_to(self):
        mismatches = []
        for skill in sorted(ALL_SKILLS):
            if skill not in CHAIN:
                continue
            if skill not in CHAINING_TRUTH:
                continue

            chain_children = set(CHAIN[skill]['children'])
            truth_chains   = set(CHAINING_TRUTH[skill]['chains_to'])

            missing = truth_chains - chain_children
            extra   = chain_children - truth_chains

            if missing or extra:
                mismatches.append(
                    f"  [{skill}] children mismatch: "
                    f"missing={sorted(missing)}, extra={sorted(extra)}"
                )

        if mismatches:
            self.fail(
                'CHAIN.children drifted from CHAINING_TRUTH.chains_to:\n'
                + '\n'.join(mismatches)
                + '\n\nFix: run  python3 scripts/generate_web_app_data.py'
            )


# ── 4.2.3 All skills in ALL_SKILLS appear in CHAIN ───────────────────────────

class TestChainHasAllSkills(unittest.TestCase):
    """
    4.2.3 — Every skill in ALL_SKILLS appears as a key in the CHAIN object.
    """

    def test_chain_has_all_skills(self):
        missing = sorted(ALL_SKILLS - set(CHAIN.keys()))
        if missing:
            self.fail(
                f'Skills in ALL_SKILLS missing from CHAIN in index.html: {missing}\n'
                'Fix: run  python3 scripts/generate_web_app_data.py'
            )

    def test_chain_keys_are_known_skills(self):
        """No unknown skill names in CHAIN (catches stale entries)."""
        unknown = sorted(set(CHAIN.keys()) - ALL_SKILLS)
        if unknown:
            self.fail(
                f'Unknown skills in CHAIN (not in ALL_SKILLS): {unknown}\n'
                'Fix: update ALL_SKILLS in test_mockup_chaining.py and '
                'scripts/generate_web_app_data.py'
            )


# ── 4.2.4 CHAIN data is internally consistent ─────────────────────────────────

class TestChainInternalConsistency(unittest.TestCase):
    """
    Bidirectional consistency within CHAIN itself:
    if A is in B.parents, then B must be in A.children.
    """

    def test_chain_is_bidirectionally_consistent(self):
        violations = []
        for skill, data in CHAIN.items():
            for parent in data['parents']:
                if parent in CHAIN:
                    if skill not in CHAIN[parent]['children']:
                        violations.append(
                            f"  {skill} has parent {parent}, "
                            f"but {parent}.children does not include {skill}"
                        )

        if violations:
            self.fail(
                'CHAIN is not internally bidirectional:\n' + '\n'.join(violations)
            )


if __name__ == '__main__':
    unittest.main()
