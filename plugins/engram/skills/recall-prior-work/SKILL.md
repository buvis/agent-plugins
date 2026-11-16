---
name: recall-prior-work
description: Use before a broad search for prior decisions, past sessions, history, or cross-repo "where/why" questions. Triggers on "have we done this before", "why did we", "where else", "which repo".
---

Ask engram before you sweep repositories with `rg`, `grep`, or `git log`.

```bash
engram query --scope repo "<question in plain words>" -k 5
engram query --scope portfolio "<question in plain words>" -k 5
```

- Use `--scope repo` for a question about the current repository only; use `--scope portfolio` when the answer may live in another repo, past session, or cross-repo decision.
- Each hit line is `rank score path:start-end heading`; read the cited lines before relying on them.
- Engram indexes code, PRDs, memory, and past agent sessions; it does not replace `rg` inside a file already known.
- A nonzero `engram status --scope portfolio` means the index is stale; say so when citing a hit.
