---
name: ponytail-debt
description: "''Use when scanning and listing shortcut: or ponytail: deferral comments into a tracked technical debt ledger. 盤點shortcut技術債清單''"
---

Every deliberate ponytail shortcut is marked with a `shortcut:` comment naming
its ceiling and upgrade path (older code may say `ponytail:`). This collects them into one ledger so a deferral
can't quietly become permanent.

## Scan

Grep the repo for comment markers, skipping `.git` and everything the
`.gitignore` files ignore (dependencies, build output, caches, in any stack):

`git grep --no-index --exclude-standard -nE '(#|//|/[*]) ?(shortcut|ponytail):'`  (add other comment prefixes if your stack uses them)

If the user names their own marker word (`/ponytail-debt TODO`), grep for that word instead.

Each hit is one ledger row. The comment prefix keeps prose that merely mentions
the convention out of the ledger. Skip hits that are not a deferral, like a note
about a keyboard shortcut.

## Output

One row per marker, grouped by file:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

The convention is `shortcut: <ceiling>, <upgrade path>`, so pull the ceiling
and the trigger straight from the comment. Want an owner per row too? add
`git blame -L<line>,<line>`.

Flag the rot risk: any marker comment that names no upgrade path or
trigger gets a `no-trigger` tag, those are the ones that silently rot.

End with `<N> markers, <M> with no trigger.` Nothing found: `No shortcut debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist it, ask and it writes the
ledger to a file (e.g. `PONYTAIL-DEBT.md`). One-shot.

## ⚠️ Gotchas (避坑指南)
- **語言覆寫原則**：技術債清冊一律以**極簡繁體中文**輸出，並標註哪些 `shortcut:` 缺少升級觸發條件（`no-trigger`）。
- **排除一般文字誤判**：只掃描註解符號（`#`、`//`、`/*`）開頭的 `shortcut:` 或 `ponytail:` 標記，忽略說明文件或鍵盤快捷鍵 (keyboard shortcut) 的一般敘述。
