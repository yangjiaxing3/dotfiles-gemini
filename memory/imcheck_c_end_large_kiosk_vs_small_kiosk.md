---
id: mem-imcheck-c-end-large-kiosk-vs-small-kiosk
brand: us3c
tier: L2_DECISION
status: active
valid_from: "2026-11-17"
scope_repos: [Yangs-BizMarketing, iMCheck, us3c-next]
---

# [Correct-Pattern] iMCheck 對 C 端一律使用立式大機台 ＋ 單幕嚴禁雙標籤搶焦點

## Context

- 訂立日期：2026-11-17（使用者明確指示放入跨會話記憶）
- 適用專案：`Yangs-BizMarketing`（`us3c` 工作艙）與所有 `iMCheck` / `US3C` 短影音、型錄及海報製作任務

## ❌ [Anti-Pattern 錯誤模式]

1. **對 C 端消費者誤用合作門市「桌面小機台」**：
   - 在面向一般消費者的 `iMCheck` 短影音、社群圖卡或落地頁介紹中，誤放入 `public/us3c/drive-assets/gallary-visuals/US3C_機台_透明背景_指定QR_yoO0.png`（該機台是合作 3C 通路門市櫃檯由店員輔助操作的**桌面小型回收機台**）。
2. **同一幕同時出現雙膠囊標籤搶奪視覺焦點**：
   - 例如在手機實機截圖卡片底部疊加一顆膠囊標籤（如「權限全部開啟」），同時在畫面下方又放 `KeyCaptionBar` 實心膠囊（如「原機直接測」），導致垂直軸線上出現兩顆同色系膠囊，讓觀眾視線分散、看不到真正重點。

## ✅ [Correct-Pattern 正確作法]

1. **C 端消費者視角一律展示「立式大型 AI 回收機台」**：
   - 標準實景／示意圖來源：`public/us3c/drive-assets/gallary-visuals/US3C版大機台-示意圖(新)_8naf.png`（深墨綠格紋機身、頂部燈箱「AI估價 3分鐘撥款」、正面大觸控螢幕與下方舊機回收艙）。
   - 影片／深色底片尾合成專用透明去背檔：`public/us3c/logos/us3c-large-kiosk-cutout.png`。
   - 原則：凡面向 C 端展示「居家預先檢測完，帶報告去門市／據點機台 3 分鐘入帳」時，一律放這座**立式大機台**；桌面小機台 `US3C_機台_透明背景_指定QR_yoO0.png` **僅限 B2B 合作 3C 店家專員現場折抵**教學影片使用。
2. **單幕唯一重點標籤鐵律（Single Focal Tag）**：
   - 每個畫面／每一幕最多只保留 **1 個**強調膠囊標籤或 CTA 行動按鈕。
   - 真實手機 App 截圖本身已有清晰文字與狀態，**嚴禁在手機框內部下方額外貼覆蓋式膠囊**，避免與底部 `KeyCaptionBar` 雙標籤打架。
