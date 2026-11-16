---
name: graphify
description: "Use when mapping codebase architecture, god nodes, or call paths via graphify-out/ knowledge graph. 知識圖譜/依賴分析/graphify"
---

# /graphify — 程式碼與文件知識圖譜導航

將程式碼、文件與多媒體轉成持久化知識圖譜（`graphify-out/`），產出互動式 HTML、`graph.json` 與 `GRAPH_REPORT.md`（含 God Nodes、社群偵測與跨檔案呼叫鏈）。

## 核心工作流

1. **優先查圖譜，不盲掃整個 Repo**：
   - 若工作區已有 `graphify-out/GRAPH_REPORT.md`，提問或架構分析前先讀 `GRAPH_REPORT.md` 與 `graph.json`，鎖定 God Nodes 與受影響的 callers。
2. **常用指令**：
   - `/graphify` — 針對當前目錄執行完整建圖流程。
   - `/graphify <path>` — 針對指定目錄建圖。
   - `/graphify --update` — 程式碼修改後增量更新既有圖譜，避免整庫重跑。
   - `/graphify --obsidian` — 匯出 Obsidian Vault 格式筆記。
3. **進階參數與完整流程規範**：
   - 需要完整管線步驟、AST/LLM 萃取參數、社群演算法與 GraphRAG 查詢細節時，按需讀取 `references/detailed-guide.md`。

## ⚠️ Gotchas (避坑指南)

- **勿直接傾印整份 `graph.json` 至終端機**：大型專案圖譜體積大，僅擷取 `GRAPH_REPORT.md` 或特定子圖節點，避免 Context Overflow。
- **程式碼重構後記得增量更新**：只讀過時的 `graphify-out/` 會遺漏新呼叫鏈；大改後請補跑 `--update`。
- **嚴禁把整座專案丟進 Prompt**：先用圖譜確認 God Nodes 與邊界，再帶入直接相關的檔案與型別即可。
