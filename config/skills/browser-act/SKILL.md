---
name: browser-act
description: "Use when automating authenticated browser sessions, extracting JS-rendered pages, or capturing XHR/HAR traffic via CLI. 瀏覽器自動化擷取/登入操作/截圖"
version: "2.0.2"
---

# browser-act

Browser automation CLI for AI agents. Runs a full browser engine: navigation &
interaction, data extraction & network capture, screenshots, form automation,
multi-browser parallel operation, user-configured proxy support, and
human-agent collaboration.

### Features

- Lightweight extraction — fast JS-rendered content fetch without opening a browser session, advanced WebFetch/curl replacement
- Session management — multi-browser isolation, multi-account parallel operation
- Verification assistance — when automation encounters interactive challenges, assists completion with user authorization
- Complex interaction — DOM content extraction, screenshots, form filling, file upload
- Human-agent collaboration — headed mode + remote assist for manual steps
- Safety controls — Confirmation Gate protocol requires explicit user approval before browser creation, deletion, and sensitive operations
- Universal compatibility — works with Cursor, Claude Code, Codex, Windsurf, etc.

Install: `uv tool install browser-act-cli --python 3.12`

## Start here

This file is a discovery stub, not the usage guide. After loading this
skill, immediately run the following to get the actual workflow content:

```bash
browser-act get-skills core --skill-version 2.0.2
```

The CLI serves skill content that always matches the installed version,
so instructions never go stale. Do NOT truncate the output — none of
which are available through `--help`.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
