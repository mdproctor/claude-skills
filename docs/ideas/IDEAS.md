# Idea Log

Undecided possibilities — things worth remembering but not yet decided.
Promote to an ADR when ready to decide; discard when no longer relevant.

---

## 2026-04-04 — Dual-repo model for epic-scoped developer work

**Priority:** medium
**Status:** active

A developer working on a long-running epic uses two repos: the main project
repo (code + finalized artifacts) and a personal session repo (WIP snapshots,
idea-log entries, in-flight ADRs, DESIGN-DELTA.md). At epic close, curated
artifacts are published to the main project; noise stays in the session repo.
The DESIGN-DELTA.md evolves throughout the epic as a draft of changes planned
for the main DESIGN.md.

**Context:** Arose during a review of the 7 methodology skills (idea-log, adr,
design-snapshot, update-claude-md, java-update-design, update-primary-doc,
issue-workflow) — noticed that all of them write directly into the project repo,
creating noise during exploratory/WIP phases. Also prompted by thinking about
co-worker collaboration: multiple developers on the same epic could each have
their own session repo and reconcile at integration time. Revisit alongside
issue/epic grouping work and co-worker collaboration model.

**Promoted to:** *(leave blank — fill if promoted to ADR or task)*
