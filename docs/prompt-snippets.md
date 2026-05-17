# Prompt Snippets

Ready-to-paste workflow prompts for Claude Code sessions. These apply to any project using cc-praxis skills.

---

## Standard development workflow

Paste at the start of any session involving designing or building:

```
invoke work-start first — if it reports no active epic, invoke /epic begin for issue-scoped work (or superpowers:using-git-worktrees for exploratory work) before proceeding; never implement on main. superpowers:brainstorming before designing — any deferred concerns or out-of-scope items must be captured as GitHub issues before leaving brainstorming, not just noted in the spec. superpowers:test-driven-development before implementing. [java-dev|python-dev|ts-dev] for all [Java|Python|TypeScript]. superpowers:requesting-code-review before committing — any finding Minor or above that isn't fixed this session must be captured as a GitHub issue before sign-off; batch related nits into a single issue. implementation-doc-sync after.

[describe the issue or feature here]
```

Replace `[java-dev|python-dev|ts-dev]` with the appropriate dev skill for the project.

---

## What each instruction does

| Instruction | What it enforces |
|-------------|-----------------|
| `work-start` | Platform coherence, protocol checks, issue confirmation, IntelliJ MCP verification |
| `superpowers:brainstorming` | Explore problem space before committing to a design; deferred/out-of-scope items → GitHub issues before leaving brainstorming |
| `superpowers:test-driven-development` | Tests planned alongside code, not after |
| `java-dev` / `python-dev` / `ts-dev` | Language rules + loads `testing-principles` and `ide-tooling` as prerequisites |
| `superpowers:requesting-code-review` | Review gate before any commit; unfixed findings Minor or above → GitHub issue(s) before sign-off |
| `implementation-doc-sync` | Checks only docs touched this session, not the whole project |

---

## Notes

- `~/.claude/prompt-snippets.md` previously held a general snippet; that content is now superseded by `work-start` and `ide-tooling` — this file is the canonical replacement
- Project-specific extensions (if any) belong alongside the project's docs and should reference this file
