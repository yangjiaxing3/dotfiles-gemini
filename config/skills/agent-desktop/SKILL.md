---
name: agent-desktop
description: "''Use when running desktop or web E2E UI checks via @ref accessibility snapshots with agent-desktop/agent-browser. 桌面與網頁結構化E2E驗..."
---

# Agent Desktop & Agent Browser 結構化 E2E 與多 Agent 對比協議

本技能整合 Vercel Labs 的 **`agent-desktop`**（跨平台原生桌面 UIA 無障礙樹 CLI）與 **`agent-browser`**（瀏覽器 DOM/Accessibility 快照 CLI），供所有 AI Agents（Antigravity、Cursor、Gemini CLI、Claude Code、Codex、Grok）以 **`Observe (Snapshot @ref) -> Act -> Verify`** 迴圈取代傳統「手寫 150 行 Playwright 腳本 + 盲目全螢幕截圖」。

## 為什麼優先使用 Snapshot `@ref` 迴圈 (Why)

1. **節省 80%~90% Token 與時間**：`snapshot` 直接回傳結構化 JSON 與穩定元素參照碼（如 `@s8f3k2p9:e8` 或 `@e2`），不必每次載入數 MB 的 PNG 截圖消耗 Vision Context。
2. **零 Timeout 卡死 (`STALE_REF` 保護)**：當畫面發生變動或被遮罩蓋住時，CLI 會立即回傳 `STALE_REF` 或 `AMBIGUOUS_TARGET`，不會像傳統 Playwright 卡死 30 秒。
3. **多 Agent 精準 Diff**：Phase B (紅隊) 與 Phase E (QA) 可直接比對修改前後的 Snapshot JSON 結構樹，100% 驗證按鈕、狀態徽章與欄位數值，只在最終存證時拍 1 張截圖。

---

## 工具分工矩陣：何時用 `agent-browser` vs `agent-desktop`

| 目標場景 | 首選 CLI | 核心優勢與原因 |
| :--- | :--- | :--- |
| **Web 應用 E2E（React / Vite / FastAPI 後台）** | `agent-browser` | 透過 Headless Daemon / CDP 直接讀取 DOM 與無障礙樹，**不會搶奪使用者本機滑鼠或切換前景視窗**。 |
| **Windows 原生桌面應用（Flutter Windows / CAD / SketchUp / 系統視窗）** | `agent-desktop` | 直接對接 Windows UI Automation (UIA)，可跨視窗操作原生對話框、檔案選擇器、剪貼簿與桌面軟體。 |

---

## 核心操作迴圈 (The Observe -> Act -> Verify Loop)

### A. Web 端極速 E2E (`agent-browser`)

```powershell
# 1. 觀察 (Observe)：開啟網址並只擷取可互動元素 (@e1, @e2...)，重導向至暫存檔防爆 Token
agent-browser open http://localhost:5173/settings/floorplans/101/3d
agent-browser snapshot -i > temp_web_snap.txt

# 2. 行動 (Act)：直接針對 Snapshot 中的 @ref 或語意角色操作
agent-browser click @e5
agent-browser find role button click --name "建立報修任務"

# 3. 驗證與單次存證 (Verify)：再次擷取結構確認狀態變更，最後只拍 1 張驗收圖
agent-browser snapshot -i > temp_web_after.txt
agent-browser screenshot C:/path/to/final_proof.png
```

### B. 原生桌面端極速自動化 (`agent-desktop`)

```powershell
# 1. 檢查權限與列出執行中視窗
agent-desktop status
agent-desktop list-windows --app "Code"

# 2. 擷取指定視窗的無障礙樹 Snapshot JSON（含 @s...:e... 穩定參照）
agent-desktop snapshot --app "storeasy_it" > temp_desktop_snap.json

# 3. 使用語意化無頭點擊（預設不移動實體滑鼠游標）與狀態驗證
agent-desktop click @s8f3k2p9:e8
agent-desktop is visible @s8f3k2p9:e12
agent-desktop screenshot --app "storeasy_it" C:/path/to/desktop_proof.png
```

---

## 進階參考手冊 (Layer 3 On-Demand References)

需要查詢完整旗標或平台細節時，請按需讀取本技能目錄下的 `references/`（或執行 `agent-desktop skills get <name>`）：
- `references/desktop-core.md`：`agent-desktop` 核心 Snapshot/Ref 迴圈與重試規則。
- `references/windows-platform.md`：Windows UIA 權限、PowerShell 引號規範、UIPI 提權注意事項。
- `references/workflows.md`：標準跨視窗與表單驗證工作流。
- `references/commands-observation.md` / `references/commands-interaction.md` / `references/commands-system.md`：完整指令規格。

---

## ⚠️ Gotchas (避坑指南)

- **終端機輸出保護**：對大型畫面執行 `agent-desktop snapshot` 或 `agent-browser snapshot` 時，**強制重導向至暫存檔**（如 `> temp_snap.json`）再用讀檔工具檢視，嚴禁直接把幾千行 UI 樹印在 stdout。
- **預設無頭語意操作 vs `--headed`**：`agent-desktop click` 預設走 UIA `InvokePattern`（不移動實體滑鼠）；只有在目標元件不支援無障礙 Invoke、或需要測試 `drag` / `hover` / `double-click` 時，才加上 `--headed`。
- **遇到 `STALE_REF` 立即重抓 `snapshot`**：絕對不要對舊的 `@ref` 硬猜或盲目重試，收到 `STALE_REF` 代表 UI 已更新，重新執行一次 `snapshot` 即可取得最新參照。
- **WebGL `<canvas>`（如 3D Sitemap）驗證法則**：無障礙樹看不到 `<canvas>` 內部的 Three.js Mesh，請透過外層同步暴露的 DOM 徽章與屬性（如 `3d-stats-iot-health`、`3d-device-row-*`）進行結構化驗證，再搭配 1 張 `screenshot` 驗證 3D 畫面。
