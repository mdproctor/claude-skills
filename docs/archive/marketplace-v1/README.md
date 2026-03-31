# Archived: Original Marketplace Implementation (v1)

This directory contains documentation for the original custom marketplace implementation that was replaced in March 2026.

## What Was Archived

**Original implementation (~2,800 lines):**
- Custom `registry.json` format
- Custom `skill.json` format
- 6 Python modules (installer, validator, cli, dependency_resolver, registry)
- 7 test files (~1,600 lines)
- Separate `claude-skill-registry` repository

**Replaced with (230 lines):**
- Official `.claude-plugin/marketplace.json` format
- Official `.claude-plugin/plugin.json` format
- Single `scripts/claude-skill` file
- Single repository architecture

## Files in This Archive

- `2026-03-30-skill-marketplace.md` - Original implementation plan
- `2026-03-30-skill-marketplace-design.md` - Original design specification

## Why It Was Replaced

1. **Code reduction:** 92% reduction (2,800 → 230 lines)
2. **Official formats:** Aligned with Claude Code standards
3. **Single repository:** Eliminated sync issues between two repos
4. **Preserved features:** Circular dependency detection, resolution, conflict handling
5. **Migration path:** When official dependency support arrives, zero breaking changes

## Current Implementation

See:
- `.claude-plugin/marketplace.json` - Official catalog format
- `scripts/claude-skill` - Minimal installer (230 lines)
- `RELEASE.md` - Development workflow
- `docs/marketplace/REGISTRY.md` - Usage guide

## Date Archived

March 31, 2026
