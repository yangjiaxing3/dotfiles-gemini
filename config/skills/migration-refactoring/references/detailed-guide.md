# Migration Refactoring — Phase 4 & 5 Detailed Reference

## Phase 4: 🛠️ SDD 交付模式 (Subagent-Driven Development)

### 執行順序（嚴格遵守）

1. CSS 基礎設施 (Design Tokens + Class)
2. 共用元件 (AlertModal, Layout, etc.)
3. 頁面元件 (由低耦合 → 高耦合)
4. 路由整合 (App.tsx 更新)
5. 反面模式掃描 + 修復

### 每個 Task 的執行循環

- Dispatch Implementer → 實作 + Self-review
- Dispatch Spec Reviewer (規格合規？)
- Dispatch Quality Reviewer (程式品質？)
- Mark Complete → 下一個 Task

### 移植專用檢查清單 (Per-Task)

- [ ] CSS 規範合規 (確認是否一致採用專案預設的 Tailwind 或 CSS Module)
- [ ] 圖示全部來自統一圖示庫 (`check-icons.cjs`)
- [ ] 無原生 alert/confirm (`grep alert(`)
- [ ] 所有 input 有 `box-sizing: border-box`
- [ ] 編譯轉譯成功 (HTTP 200 + body.length > 1000)

---

## Phase 5: 🔍 全量 E2E 驗證 (End-to-End Verification)

### Step 5.1: 靜態驗證

```bash
node e2e-test.cjs
node check-icons.cjs
grep -rn "alert(" --include="*.tsx" src/
```

### Step 5.2: 視覺驗證

依序測試每個路由：
1. 載入頁面，截圖。
2. 點擊每個主要按鈕/Tab，確認有反應。
3. 開啟所有 Modal，確認可正常關閉。
4. 檢查響應式（縮小視窗）。

### Step 5.3: 反面模式警告 (Anti-Patterns)

| ❌ 禁止 | ✅ 正確做法 |
| --- | --- |
| 只看 HTML 標題就開始寫 React | 逐行分析原始 JS 邏輯後再動手 |
| 未統一 CSS 策略便開工 | 遵循並貫徹專案既有的 CSS 框架 (如 Tailwind) |
| 用 `alert()` 做系統提示 | 使用共用的 `AlertModal` 元件 |
| 硬編碼 Mock 資料散落各元件 | 集中在頁面頂層，透過 props 傳遞 |
| 忽略原始頁面的空狀態設計 | 完整實作 Empty State / Loading / Error |
| 只做桌面版 | 確保 Mobile-first 響應式 |
| 移植後不跑 E2E | 每個 Task 完成後立即驗證 |
