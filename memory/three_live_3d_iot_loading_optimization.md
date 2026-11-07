# Three-Live 啟發之 3D / CAD / IoT 前後端極速載入優化模式 (CADCraft × STOREASY_IT × StoreasyFMnew)

> 萃取自 `StoreasyFMnew` 快存櫃 3D 模擬器優化實戰（Commit `31416ad0`, `c6b94d86`, `1d3bd462`, `5313eb74`）。
> 實測成效：首屏 JS Bundle 縮減 **75.6%** (`1,547 kB` ➔ `377 kB`)、3D 測試與貼圖生成提速 **39.1%** (`1,967ms` ➔ `1,197ms`)、點擊格位/設備切換 **0ms 無閃爍**。

---

## 一、核心 Anti-Patterns vs Correct-Patterns（6 大黃金法則）

### 1. 路由級別切斷 Three.js / CAD 引擎靜態引入鏈 (`manualChunks` + `React.lazy`)
- **[Anti-Pattern]**：在頂層 `App.tsx` 或 `AppRouter.tsx` 靜態 `import` 含有 `three`、`@react-three/fiber`、`dxf-parser` 或 `echarts` 的重型頁面，導致使用者連開登入頁或一般列表頁都必須下載並解析 `1.5MB+` 的 3D 引擎。
- **[Correct-Pattern]**：
  1. 在 `vite.config.ts` 配置 `manualChunks`，將 `three` / `@react-three` 獨立為 `vendor-three`、圖表庫獨立為 `vendor-echarts`、UI 庫獨立為 `vendor-mui`，利用瀏覽器長效快取。
  2. 所有 3D / CAD / IoT 地圖頁面一律在 Router 層使用 `React.lazy(() => import(...))` + `<Suspense>` 按需載入。

### 2. WebGL 場景持久化與選中狀態原地更新 (Scene Persistence over Recreate)
- **[Anti-Pattern]**：把 `selectedId` / `hoveredId` / `activeLayer` 放進初始化 `new THREE.WebGLRenderer()` 與建立 Mesh 的主 `useEffect` 依賴陣列中，導致每次點擊一個櫃位、CAD 圖元或 IoT 設備，就銷毀重建整個 WebGL Context 與數十張 Canvas 貼圖（造成畫面閃白與 GPU 記憶體抖動）。
- **[Correct-Pattern]**：
  1. 主 WebGL `useEffect` **只依賴幾何結構資料**（如 `[builtLineup, resolvedCells]` 或 `[cadEntities]`）。
  2. 將 `selectedId` 存入 `selectedIdRef`，並透過 `selectionSyncRef.current` 暴露場景內的局部材質更新函式；當 `selectedId` 改變時，僅在獨立的輕量 `useEffect` 中原地切換目標 Mesh 的 `material.map`、`edgeMat.color` 與 `hoverFrame.visible`（耗時 `< 0.5ms`）。

### 3. Canvas 貼圖池化 (`TEXTURE_POOL`) + 惰性生成 (`Lazy Hover Texture`) + `2x` HiDPI
- **[Anti-Pattern]**：每次渲染對每個格位/設備同時繪製 `normalTex` 與 `hoverTex` 兩張 `3x` 超採樣 Canvas，且未做快取，70 個格位瞬間產生 140 次高解析 2D Canvas 繪圖阻塞主執行緒。
- **[Correct-Pattern]**：
  1. **模組級快取池 (`Map<string, THREE.CanvasTexture>`)**：以 `id|type|size|status|isSelected` 為 Key 快取 `CanvasTexture`，且快取池內的貼圖不在組件 unmount 時誤呼叫 `dispose()`。
  2. **惰性高亮貼圖 (`getHoverTex`)**：首屏只生成 `normalTex`；`hoverTex` 封裝為 getter，**只有當使用者真正選中或滑鼠停留滿 320ms (`Dwell-to-Highlight`) 時才按需生成**，首屏貼圖繪製量直接減半 (`-50%`)。
  3. **HiDPI 倍率鎖定 `2x`**：較 `3x` 減少 **55%** 像素填充量，同時在 Retina 螢幕維持同等銳利度；大尺寸面（如 L/M 櫃門）的標籤尺寸需設 `Math.min(maxPx, cellW * ratio)` 物理上限防止貼紙放大變形。

### 4. 幾何與空間演算法 $O(1)$ 預篩選 (Early Spatial Rejection)
- **[Anti-Pattern]**：在推薦規格、碰撞檢測或 CAD 圖元拾取時，對所有候選目標無差別執行 $O(N^3)$ 的 3D Bin Packing (`calculatePositions`) 或複雜多邊形交集運算。
- **[Correct-Pattern]**：在進入核心幾何演算法前，先做 **$O(1)$ 體積總和與最大單邊包絡盒 (Bounding Box) 預篩選**（例如：`if (specVol < totalItemsVol || specMaxEdge < minRequiredMaxEdge) continue;`），在不犧牲任何物理精度的前提下砍掉 60%~80% 無謂運算。

### 5. 前後端 Stale-While-Revalidate (0 秒本地骨架 + 後端記憶體 TTL 快取)
- **[Anti-Pattern]**：
  - 前端：`{isLoading || isFetching ? <Loader /> : <Grid />}`，因為慢速外部 IoT/QSS API 未返回就把整個畫面擋在轉圈圈；同時全域 `Context` 與子頁面在掛載時各發一次查詢造成雙重 API 競爭。
  - 後端：每次收到前端請求都無快取直打外部慢速硬體/PHP API。
- **[Correct-Pattern]**：
  1. **前端 0 秒骨架**：只要本地已有預設排櫃/CAD 結構或快取資料 (`items.length > 0`)，**0 秒立即渲染完整格位與 3D 畫面**，僅在標題列顯示輕量 `即時狀態同步中...` 微標；API 返回後再平滑疊加狀態。
  2. **後端 60s TTL 快取 + `?refresh=true` 強制穿透**：後端端點加入記憶體 TTL 快取（60 秒），並提供 `?refresh=true` 參數供前端「↻ 刷新」按鈕或硬體操作（如遠端開門/重啟設備）後強制穿透更新。

### 6. UI/UX 減法與畫布操作防誤觸 (`/impeccable` + `/content-quality-auditor`)
- **畫布焦點與 2 秒停留防誤觸控制 (`Dwell-to-Highlight -> Click-to-Activate`)**：
  1. 3D/CAD 畫布預設關閉滾輪縮放（避免頁面捲動時誤觸）；**點擊畫布才啟用 (`active`) 3D 操作，且僅在按下 `Esc` 鍵時結束 (`inactivate`) 操作**。
  2. **停留滿 2 秒 (`2000ms`) 才 Highlight，Highlight 後短按才 Activate 設備**：`mouseover` 停留在設備/櫃門上滿 `2000ms` 才觸發 Highlight；只有已處於 Highlight 狀態的設備，短按點擊才會觸發 `onSelect` / Activate。
  3. **點擊並 Hold 住（或拖曳調整視角）不計入 Dwell**：在 `pointerdown` 與 `isPointerHeld` 期間（或按住超過 `240ms` / 移動距離 `> 6px`），視為使用者在調整 Canvas 視角，立即取消計時器且絕不觸發設備選取。
- **緊湊狀態卡片防重複與防空行**：
  1. 狀態小卡片移除硬撐高度的 `min-h-[54px] justify-between`，改用 `flex flex-col gap-1 py-1.5 px-2`，消除上下兩列之間無意義的空白行。
  2. 左下角狀態標籤加 `shrink-0 whitespace-nowrap` 防止被截斷成 `承...`；右下角承租人/備註若為泛用占位字（如 `'承租中會員'`）則隱藏，避免同一張卡片出現兩個「承租中...」。
- **現場設備清單 Section 自動收合與預設不展開單卡**：
  1. 預設 `selectedIotAssetId = null`（嚴禁任何一張設備卡片 default 處於 expand 狀態）。
  2. 當使用者點擊任一「櫃位」查看細節時，「現場設備清單」section 必須自動 collapse (`setIsIotSectionCollapsed(true)`)，將右側空間讓給櫃位細節。
- **統一全站數字字型（100% 對齊 StoreasyFMnew）**：
  - 移除 `JetBrains Mono`，將 `frontend/index.html`、`frontend/src/index.css` 與 Canvas 2D 貼圖的 `--font-primary`、`--font-mono` 及 `.num / .mono / .amt / .finhr-kpi-val / .font-mono` 全部統一為 `'Inter', 'Noto Sans TC', system-ui, sans-serif` 搭配 `font-variant-numeric: tabular-nums`，消除同畫面出現兩種數字字型的割裂感。
- **視覺降噪**：獨立 3D 模擬子頁移除無關的右側欄；左側欄刪除冗長說明段落，一律收斂為精準短句並將詳細規格/公式收納至 `"i"` (`InfoTooltip`) 懸浮提示中。
- **原生語音驅動 (`Live Voice-to-3D`)**：利用瀏覽器原生 `SpeechRecognition` (`zh-TW`) 零依賴實現語音輸入自動轉指令並驅動 3D 場景。
