---
description: 使用本機已登入之 ego-browser (Chromium) 執行網頁操作、表單填寫、截圖與實機 QA 檢測
---

# /ego-browser 工作流

1. 先讀取 `ego-browser` skill（`.agent/skills/ego-browser/SKILL.md` 或 `~/.gemini/config/skills/ego-browser/SKILL.md`）。
2. 執行 `ego-browser skill` 取得當前安裝版本對應之完整指令手冊（若輸出截斷則導向 `$env:TEMP\ego-browser-skill.md` 分段讀取）。
3. 依使用者需求透過 `ego-browser` CLI 操作已登入瀏覽器、擷取畫面或執行網頁驗證，操作完成後彙整實測證據回報。
