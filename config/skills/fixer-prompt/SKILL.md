---
name: fixer-prompt
description: "Use when a bug or test fails 2+ times in a row or hits a dead loop to diagnose root causes from first principles. Fixer除錯/死循環修復/修不好"
---

# Fixer：第一性原理診斷

被叫出來代表前一輪已經在同一個錯誤上卡住，思路被鎖死。**不要沿用先前的假設與修法**，只帶三樣東西：原始任務目標、失敗指令、完整錯誤輸出。

## 何時啟動

- 同一個測試/型別檢查/建置連續失敗 2 次以上，或修 A 壞 B 來回打轉。
- 使用者說「叫 Fixer」、「從零診斷」、「用第一性原理修」。
- `multi-agent-mode` 的 Phase 4/5 判定需要救援。

## 六步驟（不可跳步）

1. **重現**：親自執行失敗指令（`pytest`、`npm test`、`npx tsc --noEmit`…），把完整輸出導向檔案再讀，避免洗版。
2. **溯源**：把錯誤路徑經過的每個檔案從頭讀完，不只看報錯那幾行。
3. **定位真因**：寫出一句「實際導致錯誤的根本原因是 ____」。寫不出來就回到步驟 2，不准猜。
4. **最小修補**：只改真因所在的那一層。若真因在資料/表示法的產生端，就修產生端，不要在下游補丁。
5. **驗證**：重跑同一個指令，附上修補前後的輸出對比。再跑一次相鄰的檢查，確認沒有修 A 壞 B。
6. **萃取經驗**：輸出下列區塊，供寫入 `~/.gemini/memory/`：

```markdown
<PatternExtract>
- Anti-Pattern: …（造成錯誤的做法）
- Correct-Pattern: …（正確做法）
- Tags: #python #react …
</PatternExtract>
```

## 停止條件

- 同一個真因假設驗證失敗 2 次 → **停止修改**，回報已排除的假設、目前證據與需要使用者提供的資訊。
- 修補需要改到測試本身的期望值 → 先說明理由並取得同意。

## 絕對禁止（Anti-Cheating）

- 刪除測試、放寬或刪除斷言、加 `skip` / `xfail`。
- 用 `try/except`、`try/catch`、`IFERROR` 把錯誤吞掉。
- 只為了讓輸出變綠而寫死期望值。

**修程式邏輯，不修計分板。**

## ⚠️ Gotchas (避坑指南)

- **錯誤訊息不等於真因**：`KeyError`、`undefined` 常是上游資料形狀錯了；先印出實際資料形狀再判斷。
- **快取與舊產物**：修了卻沒變化時，先排除 `__pycache__`、`.next`、`dist`、測試快照等舊產物，再懷疑邏輯。
- **環境不同**：確認執行的直譯器/Node 版本與專案鎖定版本一致（例如 Windows 上 `python` 可能是空的 Store alias）。
