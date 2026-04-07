# Hortora — The Garden Grows Up

**Date:** 2026-04-07
**Type:** phase-update

---

## What I came in to fix: the retrieval problem

The knowledge garden has 78 entries and retrieval is already showing strain. The current model loads GARDEN.md — all titles — then loads the full domain file, then greps for the entry. As the garden grows, that gets worse. I wanted to fix it before it became too expensive to refactor.

That's not quite what happened.

## Three hours in, it was no longer a retrieval fix

I brought Claude in to design the v2 structure. Within the first hour we'd solved the retrieval problem itself — one file per entry, multi-level indexes, `_summaries/` as a 100-token retrieval layer, `git cat-file --batch` for fetching multiple entries in one network round-trip. The three-tier algorithm is clean: if you know the technology, grep the domain index (under 1,500 tokens); if you know the symptom pattern, check the label index; if you're genuinely lost, scan all summaries — bounded at roughly 30,000 tokens for 300 entries, regardless of garden size.

Then we didn't stop.

The GitHub backend followed — sparse blobless clones, GitHub Issues as GE-IDs to avoid the concurrent-PR counter collision problem, CI automation that does zero-token validation before anything touches the garden. Then federation: canonical, child, and peer gardens with distinct governance contracts, where a child garden can enrich public parent entries with local context without the parent ever knowing the child exists. Then a nine-phase implementation roadmap where some capabilities are explicitly labelled "evergreen and never finished."

At some point it stopped being a retrieval fix and became a product vision.

Andrej Karpathy published something strikingly similar four days before this session — git-backed markdown, no vector database, LLM maintains the index. Claude checked this independently. His system is individual, personal, ungoverned. The gap — multi-contributor governance, quality lifecycle, deduplication, federation — is what we spent the afternoon designing.

## Finding a name: the validation took three rounds

Midway through I decided we needed a name. Rigorous validation matters — several names I liked turned out to be taken by active AI tools.

Cairn was an active AI software engineering agent. Mycelium was a live AI config orchestrator in exactly the same space. Grok suggested Sylvara as its top pick. Claude ran independent searches. Sylvara.ai is a live AI automation agency. Grok didn't know.

We landed on Hortora — from *hortus*, Latin for garden, with an ending that hints at oracle. The etymology gives you something to say: a garden you tend, an oracle you consult.

## The spec exists. The garden doesn't yet.

The document is 3,300 lines with 10 embedded diagrams. Claude generated the HTML visuals; we used Playwright to screenshot each one and embed the PNGs directly into the Typora document.

Phase 1 is next: migrate the 78 existing entries to the v2 structure. One file per entry, YAML frontmatter, multi-level indexes. The spec earns its keep when the first entries live inside it.
