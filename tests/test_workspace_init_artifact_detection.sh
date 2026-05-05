#!/bin/bash
# Test: workspace-init Step 9 artifact detection covers both root-level and docs/ locations.
# Regression test for the gap where root-level adr/, blog/ etc. were not detected.
#
# This script simulates the detection logic from workspace-init/SKILL.md Step 9
# and verifies it finds all expected artifact locations.

set -e

PASS=0
FAIL=0

check() {
  local description="$1"
  local expected="$2"
  local actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  ✅ $description"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $description"
    echo "     expected: $expected"
    echo "     actual:   $actual"
    FAIL=$((FAIL + 1))
  fi
}

# ── Setup: create a mock repo with the claudony-style split layout ───────────

TMPDIR=$(mktemp -d)
PROJECT="$TMPDIR/mock-repo"
mkdir -p "$PROJECT"
cd "$PROJECT"
git init -q
git config user.email "test@test.com"
git config user.name "Test"

# Root-level artifacts (pre-docs/ convention)
mkdir -p "$PROJECT/adr"
echo "# ADR 001" > "$PROJECT/adr/adr-001.md"
mkdir -p "$PROJECT/blog"
echo "# Blog 1" > "$PROJECT/blog/2026-01-01-entry.md"

# docs/ artifacts (newer convention)
mkdir -p "$PROJECT/docs/adr"
echo "# ADR 002" > "$PROJECT/docs/adr/adr-002.md"
mkdir -p "$PROJECT/docs/blog"
echo "# Blog 2" > "$PROJECT/docs/blog/2026-02-01-entry.md"
mkdir -p "$PROJECT/docs/_posts"
echo "# Post" > "$PROJECT/docs/_posts/2026-03-01-post.md"
mkdir -p "$PROJECT/docs/superpowers/specs"
echo "# Spec" > "$PROJECT/docs/superpowers/specs/spec-001.md"
mkdir -p "$PROJECT/docs/superpowers/plans"
echo "# Plan" > "$PROJECT/docs/superpowers/plans/plan-001.md"

# Root-level handover and ideas
echo "# Handoff" > "$PROJECT/HANDOFF.md"
echo "# Ideas" > "$PROJECT/IDEAS.md"
git -C "$PROJECT" add "$PROJECT/IDEAS.md" 2>/dev/null || true

# docs/specs (design specs, not project requirements)
mkdir -p "$PROJECT/docs/specs"
echo "# Design spec" > "$PROJECT/docs/specs/2026-01-01-feature-design.md"

# Commit everything so ls-files works
git add -A
git commit -q -m "init"

# ── Run the detection logic from SKILL.md Step 9 ────────────────────────────

echo ""
echo "Testing artifact detection logic (Step 9)..."
echo ""

FOUND=()

# Root-level handovers and ideas
[ -f "$PROJECT/HANDOFF.md" ]  && git -C "$PROJECT" ls-files --error-unmatch HANDOFF.md  2>/dev/null && FOUND+=("HANDOFF.md → HANDOFF.md")
[ -f "$PROJECT/HANDOVER.md" ] && git -C "$PROJECT" ls-files --error-unmatch HANDOVER.md 2>/dev/null && FOUND+=("HANDOVER.md → HANDOFF.md")
[ -f "$PROJECT/IDEAS.md" ]    && git -C "$PROJECT" ls-files --error-unmatch IDEAS.md    2>/dev/null && FOUND+=("IDEAS.md → IDEAS.md")

# Root-level artifact directories — adr/ excluded (project knowledge, stays in repo)
[ -d "$PROJECT/blog" ]        && FOUND+=("blog/ → blog/")
[ -d "$PROJECT/specs" ]       && FOUND+=("specs/ → specs/")
[ -d "$PROJECT/plans" ]       && FOUND+=("plans/ → plans/")
[ -d "$PROJECT/snapshots" ]   && FOUND+=("snapshots/ → snapshots/")

# docs/ artifacts
[ -d "$PROJECT/docs/design-snapshots" ]  && FOUND+=("docs/design-snapshots/ → snapshots/")
# docs/adr/ excluded — ADRs are project knowledge, not workspace artifacts
[ -d "$PROJECT/docs/blog" ]              && FOUND+=("docs/blog/ → blog/")
[ -d "$PROJECT/docs/_posts" ]            && FOUND+=("docs/_posts/ → blog/")
[ -d "$PROJECT/docs/specs" ]             && FOUND+=("docs/specs/ → specs/")
[ -d "$PROJECT/docs/superpowers/specs" ] && FOUND+=("docs/superpowers/specs/ → specs/")
[ -d "$PROJECT/docs/superpowers/plans" ] && FOUND+=("docs/superpowers/plans/ → plans/")

# ── Assertions ───────────────────────────────────────────────────────────────

found_str="${FOUND[*]}"

check "Detects root-level HANDOFF.md"                        "yes" "$(echo "$found_str" | grep -q 'HANDOFF.md → HANDOFF.md' && echo yes || echo no)"
check "Detects root-level IDEAS.md"                          "yes" "$(echo "$found_str" | grep -q 'IDEAS.md → IDEAS.md' && echo yes || echo no)"
check "Does NOT migrate root-level adr/ (stays in project)"  "no"  "$(echo "$found_str" | grep -q 'adr/ → adr/' && echo yes || echo no)"
check "Does NOT migrate docs/adr/ (stays in project)"        "no"  "$(echo "$found_str" | grep -q 'docs/adr/ → adr/' && echo yes || echo no)"
check "Detects root-level blog/"                             "yes" "$(echo "$found_str" | grep -q 'blog/ → blog/' && echo yes || echo no)"
check "Detects docs/blog/"                                   "yes" "$(echo "$found_str" | grep -q 'docs/blog/ → blog/' && echo yes || echo no)"
check "Detects docs/_posts/"                                 "yes" "$(echo "$found_str" | grep -q 'docs/_posts/ → blog/' && echo yes || echo no)"
check "Detects docs/specs/ (design specs)"                   "yes" "$(echo "$found_str" | grep -q 'docs/specs/ → specs/' && echo yes || echo no)"
check "Detects docs/superpowers/specs/"                      "yes" "$(echo "$found_str" | grep -q 'docs/superpowers/specs/ → specs/' && echo yes || echo no)"
check "Detects docs/superpowers/plans/"                      "yes" "$(echo "$found_str" | grep -q 'docs/superpowers/plans/ → plans/' && echo yes || echo no)"
check "Detects BOTH root blog/ AND docs/blog/ (split pattern)" "yes" \
  "$(echo "$found_str" | grep -q 'blog/ → blog/' && echo "$found_str" | grep -q 'docs/blog/ → blog/' && echo yes || echo no)"

# ── Cleanup ──────────────────────────────────────────────────────────────────

cd /
rm -rf "$TMPDIR"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
