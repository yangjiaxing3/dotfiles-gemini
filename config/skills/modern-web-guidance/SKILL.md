---
name: modern-web-guidance
description: "Use when building or auditing HTML/CSS/JS UI, <dialog>, forms, IME, tables, or CWV. 現代Web原生平台與無障礙規範"
---

# Modern Web Guidance

在實作或審查任何網頁 UI、表單、彈窗、響應式表格、CSS 動畫或效能（LCP / INP / CLS）任務時，優先查閱 Google Chrome `modern-web-guidance` 標準指南，以原生 Web 平台能力取代過時 JS/CSS Hack。

## 核心工作流

1. **檢索對應指南**：使用 2–5 個純平台名詞檢索（不含框架名或業務名詞）：
   ```powershell
   npx.cmd -y modern-web-guidance@latest search "<query>"
   ```
2. **讀取完整實作與相容性規則**：
   ```powershell
   npx.cmd -y modern-web-guidance@latest retrieve "<guide-id>"
   ```
3. **掃描既有舊式寫法（僅於全盤現代化審查時使用）**：
   ```powershell
   npx.cmd -y modern-web-guidance@latest legacy-scan <dir> --json
   ```

## 本專案關鍵對齊準則（與 SSR SEO/GEO 並存）

- **彈窗 Top-Layer**：優先使用原生 `<dialog>`（`showModal()`）與 `overscroll-behavior: contain`，禁止手寫 `fixed inset-0` 遮罩或竄改 `document.body.style.overflow`（在 Vitest JSDOM 須加 `typeof dialog.showModal === 'function'` 守衛）。
- **繁中 IME 與表單**：自訂 `Enter` 監聽必檢 `if (e.nativeEvent.isComposing || e.keyCode === 229) return;`；日期欄位強制 `<input type="date" lang="en" />`；多行 `<textarea>` 優先採 `field-sizing: content`。
- **手風琴與折疊**：`<summary>` 內嚴禁放 `<h2>`–`<h4>` 或 `<a>`；手動折疊須同步 `aria-expanded`，收合區加 `inert` 阻擋隱藏焦點，且**嚴禁對 SEO/GEO 文字加 `opacity: 0` 或 `visibility: hidden`**。
- **響應式表格與捲軸**：捲動表格外框補 `tabIndex={0} role="region" aria-label="..."`；優先採 `@container` 卡片堆疊；捲軸使用標準 `scrollbar-width` / `scrollbar-color`（WebKit 偽元素需配 `@supports not (scrollbar-color: auto)`）。
- **CWV 與動態減量**：首屏 LCP 圖加 `fetchPriority="high"` 與 `width`/`height`，下方圖加 `loading="lazy"`；禁止 `animation: ... !important` 擊穿 `prefers-reduced-motion: reduce`。

## ⚠️ Gotchas (避坑指南)
- **SEO/GEO 內容護欄**：切勿對 `.summary-grid`、`[data-answer-summary]`、價格表或 FAQ 套用 `content-visibility: auto` 或 `display: none`，以免影響錨點跳轉與爬蟲索引。
- **JSDOM 測試容錯**：JSDOM 尚未完整實作 `HTMLDialogElement.prototype.showModal()` 與 `close()`，呼叫前必先檢查型別並提供 `open` 屬性回退。
- **Windows CLI 執行與輸出保護**：Windows 請呼叫 `npx.cmd`；執行 `legacy-scan --json` 時強制導向暫存檔，避免大量 JSON 撐爆上下文。
