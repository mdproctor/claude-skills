# cc-praxis — The Methodology Family

**Date:** 2026-04-04
**Type:** phase-update

---

## What We Were Trying To Achieve

The original cc-praxis skills were all about *how to work with code* — reviews, commits, dependency updates, observability. But there's a whole class of work that isn't code: the design decisions, the ideas that aren't ready to act on, the moments when the project pivots, the hard-won knowledge that gets re-discovered by the next person.

I wanted skills for that. A family of tools for capturing design thinking as it happens — not in hindsight.

At the same time, I wanted to properly review the web installer UX. We'd built it to work; now I wanted it to be good.

## What We Believed Going In

I thought the methodology skills would be fairly independent. `adr` already existed. I'd add `design-snapshot` (freeze design state) and `idea-log` (park undecided ideas) and that would probably be enough.

I also thought the UX review would surface mostly small things — button placement, text clarity. That turned out to be true, but there were more of them than I expected, and several went deeper than I anticipated.

## What We Tried and What Happened

**The design thinking trio.** We landed on three skills that together cover the full space:

- `idea-log` — undecided possibilities. Park the "what if we..." thoughts before they evaporate. Mutable, informal.
- `adr` — individual decisions. Formal, immutable once written, structured for archival.
- `design-snapshot` — full design state at a moment. Immutable record. "Here's where the project is right now."

The relationship between them is what makes them a family rather than three independent tools. Ideas get promoted to ADRs when they're ready to decide. Snapshots reference ADRs rather than duplicating them. A snapshot review can surface new ideas for the log.

When I reviewed the chaining, I found the connections were poorly documented. `design-snapshot` didn't mention `idea-log` at all. `adr` didn't point back to `idea-log` for pre-decision thinking. I rewired all seven methodology skills (adding `project-blog` and `knowledge-garden` later) so they explicitly reference each other.

**`project-blog`** came from a request to support a kind of writing that none of the other skills covered: an ongoing development diary written in the moment, not in hindsight. Not a polished retrospective. Not an ADR. Not a snapshot. The lived experience of building something — including the things you believed that turned out to be wrong.

The key principle: correction entries never edit the original. If the entry from March 29th said "I believe X" and X turned out to be wrong, the April entry says "we were wrong about X, here's why" — but the March entry stands as written. The historical record matters.

**`knowledge-garden`** was a different kind of skill. Three separate Claude instances had been asked to design and build a knowledge garden concept — a machine-wide library of hard-won technical gotchas. I reviewed all three designs and synthesised them.

The most important contribution from those sessions: the *proactive trigger*. The reactive trigger ("add this to the garden") is easy. The proactive trigger — where the skill fires *without being asked* when a debugging session reveals something non-obvious — is what makes it genuinely valuable. Signs: multiple approaches tried before the fix, something works in JVM but silently fails in native image, user says "that took way too long."

The garden itself already existed at `~/claude/knowledge-garden/` with real entries. I created `GARDEN.md` with a dual index — by technology AND by symptom type. The same entry is findable by "I'm working with AppKit" and by "something is silently failing with no error."

**UX review of the web installer.** We did a systematic review across three dimensions: ergonomics, aesthetics, user flow.

Issues we fixed:
- Stats on the About page were stale: "33 skills, 2 languages, 163 tests" when the real numbers were 43, 3, and 295+
- Python was still showing as "COMING SOON" even though it shipped completely
- The "Install Now →" button on GitHub Pages silently redirected back to About (useless)
- The "Auto-refreshing" label with a pulsing dot was a leftover from the mockup — the page doesn't auto-refresh
- Bundles were collapsed by default in the Install tab, hiding all skills
- No way to install a skill directly from the Browse tab — required switching tabs
- The sync bar showed "15 of 33 installed" as hardcoded HTML even after state loaded
- Partial bundle state used amber (warning colour) when partial install is just a status, not a problem

The biggest flow issue: getting from About to Browse to Install required multiple tab switches and expand clicks. We added a quick-action Install/Uninstall button directly on Browse overview cards, removing the need to context-switch to the Install tab just to act on a skill.

We also added a persistent success banner. Previously the only feedback after installing was a 3-second toast that was easy to miss if you weren't watching exactly then. The banner stays until dismissed.

**The consistency audit.** After adding all the new skills, I asked a different Claude to audit everything for consistency. It found five gaps:
- `cc-praxis-ui` was missing from ALL_SKILLS (so it had no overview card, no install row, wasn't counted)
- `idea-log` and `project-blog` were missing from the Extras bundle in the Install tab
- README Layer 7 said "7 skills" but had 8 rows
- Hero stats were out of date
- The `install-individual` config covered only 8 skills instead of all 14

All five fixed in a single commit.

## What Changed and Why

The methodology family grew beyond the original three skills. `project-blog` came from a specific user request. `knowledge-garden` came from synthesising three external Claude sessions' designs. Both added value that wasn't in the original scope.

The UX review was more substantive than I expected. The visual issues were mostly small, but the flow issues were real — specifically the "Browse to Install requires tab switching" problem. Adding install buttons to Browse cards changed the fundamental usage pattern.

The consistency audit revealed that the infrastructure (ALL_SKILLS, overview cards, install rows) wasn't keeping up with the skills I was adding. We needed a way to catch this earlier. The answer is: run the audit after every new skill addition, not as a separate pass afterward.

## What I Now Believe

The methodology family — `idea-log`, `adr`, `design-snapshot`, `project-blog`, `knowledge-garden` — is now cc-praxis's most distinctive feature. The code-related skills (reviews, commits, dependency management) exist in other forms elsewhere. The methodology tools for capturing design thinking in real time, preserving what you believed before you knew better, building a cross-project library of hard-won knowledge — that's the part I haven't seen done this way elsewhere.

The web installer is genuinely useful, but it's only as correct as the state it reflects. Getting bundle counts, button visibility, and modal skill lists to accurately reflect real install state required more work than building the UI itself.

---

**Next:** We're at 43 skills spanning Java, TypeScript, Python, and a full methodology family. The next question is what gets added versus what gets refined — and whether the dual-repo idea for epic-scoped developer work becomes something more concrete.
