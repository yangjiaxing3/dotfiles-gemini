---
name: us3c-kiosk-driver-ops
description: "'Use when working on US3C 24H recycling kiosks, R3 5-stage APIs, L1-L4 incidents, or us3cdriverapp pickup sync. 智慧回收機台與司機巡檢聯動'"
---

# US3C 智慧回收機台 (N1)、5 大 API 閉環與司機巡檢取件聯動

本技能規範 `us3c-next`（總部機台後台）、`us3cdriverapp`（司機巡視與取件 App）與 `logistic_driver`（路線排程）之間的硬體 API 閉環、異常單等級與雙倉同步鐵律。

## 1. 智慧回收機台 5 大真實生產 API 閉環

1. **Stage 1（機台現場回收與快存櫃管理）**：
   - `API 1`：機台清單與門市大盤 (`get_kiosk_machine_list.php`)
   - `API 2`：機台 R3 待處理回收訂單 (`get_r3_order.php`)
2. **Stage 2（雙軌硬體檢測與影像存證）**：
   - `API 3`：Securaze 資料抹除與 iMCheck 硬體檢測 (`securaze_deviceidquery_proxy.php`)
   - `API 4`：Kiosk 現場雙視角相機拍照與 AI 外觀損傷判定 (`kiosk_deviceidquery_proxy.php`)
3. **Stage 3（最終鑑定審核）**：
   - `API 5`：US3C 最終鑑定審核與估價綜合報告（`get_appraisal_info`，強制驗證 MD5 Checksum）。

## 2. [CRITICAL] 異常單 `L1~L4` 與巡視步驟 `S1~S4` 雙倉同輪修改鐵律

`us3c-next` 與 `us3cdriverapp` 共用 Supabase `machine_incidents` 與 `machine_inspections` 資料表：

| 代號體系 | 適用範圍 | 定義與規範 |
| :--- | :--- | :--- |
| **`S1 ~ S4` 步驟** | 巡視流程分組 | `S1` 感應打卡、`S2` 實體外觀與環境、`S3` 核心硬體與功能、`S4` 其他回報（**維持 S，不可改為 L**） |
| **`L1 ~ L4` 評等** | 檢查項結果 & 異常單嚴重度 (`severity`) | **`L1`** 停機/安全異常、**`L2`** 服務異常需維修、**`L3`** 日常維護、**`L4`** 正常/已排除（**全面使用 L**，讀取舊 `S1~S4` 時透過 `normalizeIncidentSeverity` 正規化為 `L1~L4`） |

- **強制雙倉同步**：凡修改異常單、巡視評等或 `machine_incidents.severity`，**必須在同一輪同步修改 `us3c-next` 與 `us3cdriverapp` 的 UI 與 Payload**，嚴禁只改單邊導致開單失敗。

## 3. 司機取貨、60s 動態 PIN 與倉儲硬體安全

- **頂欄即時通知 (`NavCountBadge`)**：機台儀表板（未結 `machine_incidents`）與機台取貨（未完成 `shipping_tasks`）採 60 秒輪詢＋Supabase Realtime 雙軌刷新。
- **倉內硬體橋接**：電子標籤 `tag-bridge`（TCP `2000` / REST `8006`）與打包秤重站 `weigh-station`（REST `8005`）僅限區網或本機存取；`TAG_API_TOKEN` 嚴禁加上 `VITE_` 前綴暴露於前端。

## ⚠️ Gotchas (避坑指南)
- **禁止假資料 Fallback**：門市預約 `/store/booking` 或機台狀態讀取失敗時，只准顯示明確錯誤訊息，嚴禁回退至假資料欺騙營運人員。
- **終端機輸出保護 (Context Overflow Prevention)**：查詢機台日誌或訂單快照時，禁止直接將巨量 JSON 印到 stdout。
- **零區防禦與 Port 禁令**：嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)；路線優化服務固定使用 Port `8003`。
