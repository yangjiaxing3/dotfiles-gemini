---
name: skp-to-cad-ministorage
description: "Use when converting SketchUp (.skp) models into multi-layer CAD (.dxf/.dwg) with mini-storage layouts. SketchUp轉CAD/迷你倉排櫃"
---

# SketchUp to CAD & Mini-Storage Layout Skill (`skp2cad`)

This skill converts any SketchUp `.skp` model (up to SketchUp 2026+ format) or Trimble Connect Web Share URL into a clean, multi-layer 2D CAD drawing (`.dxf` + `.dwg` + `.png` + `.svg`) with structural beam clear-height analysis and optional automated mini-storage (迷你倉庫) cabinet layout planning.

## Installed Components

- **SketchUp C SDK Binaries (`SketchUpAPI.dll` + Python 3.14 Cython bindings)**:
  `C:\Users\Jiaxing\.gemini\antigravity\bin\skp2cad\`
- **Converter & Layout Engine (`skp2cad.py`)**:
  `C:\Users\Jiaxing\.gemini\antigravity\bin\skp2cad\skp2cad.py`
- **CAD Engine (`cadcraft-cli.exe` & `cadcraft.exe`)**:
  `c:\Users\Jiaxing\Documents\GitHub\CADCraft\target\release\cadcraft-cli.exe`

## Usage Commands

### 1. Convert `.skp` or SketchUp Share URL to Base Architectural CAD Plan
```powershell
& "C:\Users\Jiaxing\AppData\Local\Python\bin\python.exe" `
  "C:\Users\Jiaxing\.gemini\antigravity\bin\skp2cad\skp2cad.py" `
  "<PATH_OR_SHARE_URL>" `
  -o "temp\base_plan.dxf"
```

### 2. Generate Mini-Storage (迷你倉庫) Cabinet Layout Plan
```powershell
& "C:\Users\Jiaxing\AppData\Local\Python\bin\python.exe" `
  "C:\Users\Jiaxing\.gemini\antigravity\bin\skp2cad\skp2cad.py" `
  "<PATH_OR_SHARE_URL>" `
  -o "temp\ministorage_plan.dxf" `
  --plan-storage
```

## Storeasy (收多易) CAD Layer & Module Standard (Units: `mm`)

| Layer | Color | Linetype | Description |
|---|---|---|---|
| `0` | White (7) | Continuous | Interior floor boundary & exterior wall lines (`Z=0`) |
| `A-COLS` | Red (1) | Continuous | Structural interior & perimeter columns |
| `A-HATC` | Grey (8) | Continuous | `ANSI31` column section hatches |
| `A-DOOR` | Green (3) | Continuous | Building entrance / exit doors & clear openings |
| `A-BEAM` | Yellow (2) | Dashed | Overhead structural beams & clear soffit heights (`H=2620~3350mm`) |
| `櫃` | Blue (5) | Continuous | Storeasy cabinet outlines & internal extension split lines (`+650/+656mm`) |
| `動線` | Magenta (6) | Continuous | Door symbols: apex pointing INTO the cabinet door edge (base on aisle side); single triangle (`△`) for `<=1000mm`, double triangle (`M`) for `>=1492mm` |
| `編號` | White (7) | Continuous | Unit IDs (`KS501`, `TD500`, `ZD640`, `CD572`) |
| `文字` | Green (3) | Continuous | Tier type: `單` (single-tier tall unit) or `雙` (double-tier upper/lower unit) |
| `標註` | Grey (8) | Continuous | Inside-cabinet width & depth labels (`922`, `1492`, `1792`, `1200`, `650`...) |
| `DIM1` | Cyan (4) | Continuous | Aisle width & building span dimensions |

## Storeasy (收多易) Mandatory Layout Rules (十大排櫃與製圖鐵律)

1. **櫃子與櫃子之間距離 `10 mm`、離建築牆柱距離 `20 mm`（雙線獨立框畫法）**：
   - 每一個倉位皆繪製獨立藍框（圖層 `櫃`），**櫃子與櫃子之間（包含左右相鄰、背靠背相鄰、以及主倉與後方層板框之間）一律留設 `10 mm` 間距**；倉位離所有建築外牆、內牆、四週壁柱、以及場內獨立立柱（如 `C1~C4`）則退縮間隔 `20 mm`。
2. **加寬的倉位若為單門，能用 `922` 就先用**：
   - 單門倉位一律優先採用 `922 mm` 標準模數（減少非必要的 `772 mm`）。
3. **共用倉不加三角形、不印「共用」文字，僅用指向箭頭標示歸屬，且嚴格遵守模數配對鐵律**：
   - 每排收尾畸零格作為「共用倉」（併入相鄰主倉位使用），**絕對不畫門向三角形（`△`），也不印 `共用` 文字（僅保留面寬與深度尺寸標註）**，並從相鄰主倉位畫一道**指向箭頭（Arrow）**跨越 `10 mm` 雙線指入該共用倉。
   - **共用倉歸屬配對鐵律**：
     - 當共用倉歸屬給**單門主倉（`772` 或 `922`）**時，合併總寬（`w_main + 10 + w_shared`）**必須 `< 1492 mm`**（例如 `772 + 10 + 542 = 1324 < 1492`、`922 + 10 + 492 = 1424 < 1492`）；否則若 `>= 1492 mm`，實務上應直接改做 `1492` 或 `1792` 雙門主倉！
     - 較大的共用倉（`592`、`642`、`692`）僅能歸屬給**雙門主倉（`1492` 或 `1792`）**。
     - 每一排優先透過 `{1792, 1492, 1000, 922, 772}` 標準面寬模數的整數線性組合直接湊滿總寬（達成 **0 共用倉**），僅在無法整除時才於收尾配置 1 格標準共用倉。
4. **單門倉位長寬比盡量不要超過 `2:1`**：
   - 單門（`922 / 772 mm`）搭配之主倉深度（`main_d_mm`）不得超過長寬比 `2:1`。
5. **深度嚴格採用以下 8 種標準尺寸組合**：
   - 主倉深度（`main_d_mm`）與總深組合僅能從 **`1000`、`1100`、`1200`、`1450`、`1750`、`1900`、`2000`、`2100` (`mm`)** 標準尺寸中選用。
6. **加裝層板（`650` / `780 mm`）採獨立雙線框（與主倉及背靠背之間隔 `10 mm`）**：
   - 主倉後方加裝深度 **`650 mm` 或 `780 mm`** 的層板時，主倉框與層板框之間**留設 `10 mm` 雙線間距**（分別繪製獨立矩形框並各自標註深度）。
   - 中島左右封頭櫃（End-Caps）可利用上下走道餘量微幅延伸，以 100% 吻合收多易固定模數表。
7. **門向三角形尖端指向倉位門線**：
   - 單門畫 1 個三角形（`△`）、雙門（`>=1492 mm`）畫 2 個並列三角形（`M`），底邊在走道側、**尖端朝向倉位門線**。
8. **走道寬度壓緊於 `1200 mm ~ 1300 mm` 以最大化得房率**：
   - 所有主支走道寬度嚴格控制在 `1200 mm ~ 1300 mm`（最低絕對不低於 `1200 mm`），當出現非標準物料尺寸時，優先透過走道餘量外擴、內縮或調整其他倉位尺寸與位置，最大化平面得房率與雙層實質總出租面積。
9. **順應樑柱跨距並以樓板高度（如 `3800 mm`）最大化雙層倉位（`雙`）**：
   - 中島走向順應大樑與立柱軸線，並將場內獨立立柱（`C1~C4`）直接包覆嵌入雙層中島列內（離柱體退縮 `20 mm`）。
10. **四面靠牆與壁柱凹槽全面排滿倉位**：
    - 凡靠外牆或壁柱凹槽（西牆 3 處壁柱凹槽、東牆 3 處壁柱凹槽、南北牆凹槽與壁柱前），全部退縮 20 mm 貼牆排滿倉位，且確保橫向與縱向走道轉角 100% 暢通無阻擋。
11. **梁柱穿過倉位中間之兩大標準對策**：
    - 嚴禁讓大樑壓在雙層倉或半層倉的門片正中間，必須擇一處理：(1) **下方直接做成單層倉位 單（2.3 m）**；或 (2) **調整梁柱旁 3~4 個倉位固定門寬，並以「單門＋黃色側板」讓梁柱 100% 落在黃色側板位置**。
12. **入口旁「刷卡 Kiosk、手拖車、電動升降梯」標準配置、移除 1~2 倉位騰出凹槽與分合規則**：
    - **嚴禁擋住入口動線**：推車、升降機與 Kiosk **絕對不能擋在出入口正前方動線上**，必須放在「**入口旁**」——因此排櫃時**會移除入口旁靠牆的 1 ~ 2 個倉位**，騰出退入牆邊、與鄰櫃切齊的專用設備停放凹槽（地面貼黃黑警示貼紙）。
    - **a. 刷卡 Kiosk 機台**：佔地約 **30 × 30 cm (300 × 300 mm)**，設於入口旁凹槽側邊。
    - **b. 手拖車（藍色平台推車）**：約 **寬 100 cm × 深 110 cm (1000 × 1100 mm)**，放在入口旁凹槽左側。
    - **c. 電動升降梯（上下層專用）**：約 **寬 100 cm × 深 130 cm (1000 × 1300 mm)**，放在最靠近有上下層（雙 / 半）的位置（入口旁凹槽右側）。
    - **分合原則**：一般移除入口旁 2 個倉位將手拖車（左）與電動升降梯（右）併排放在一起；**但若雙層倉位距離入口太遠（> 5 m），電動升降梯就不跟手拖車放一起**（入口旁僅移除 1 倉放拖車，另於最靠近雙層倉位處移除 1 倉放電動升降梯）。

## Storeasy Fixed Cabinet Modules (`mm`)

- **Fixed Main Widths (`mm`)**:
  - Double-door (`M`): `1792`, `1492` (pitch `1802 / 1502 mm` with `10 mm` cabinet-to-cabinet gap).
  - Single-door (`△`, aspect ratio `<= 2:1`): `1000`, **`922`** (prioritized), `772`.
- **Fixed Shared Filler Widths (`共用倉`, no triangle, no `共用` text, ownership arrow from neighbor)**:
  - `692`, `642`, `592`, `542`, `492`, `442` (must satisfy `w_owner + 10 + w_shared < 1492` whenever `w_owner` is a single-door `772` or `922`).
- **Fixed Standard Depths (`mm`)**: `1000`, `1100`, `1200`, `1450`, `1750`, `1900`, `2000`, `2100`.
- **Fixed Separate Shelf Box Depths (`mm`)**: `650`, `780` (with `10 mm` double-line gap between main box and shelf box).

## Zero-Shot Maximum Efficiency Algorithm (空白 CAD 直達極限坪效三階段演算法)

1. **Stage 1: 全域切齊基準線鎖定 (Anchor-Line Extraction)**
   - 先將外牆內縮 `20 mm`、獨立立柱外擴 `20 mm`。
   - **綠色界線 ($X_{\text{green}}$)**：切齊場內貫穿南北的立柱柱面與主出入口邊緣（如 `X = 17860`），作為中島右側切齊線。
   - **水藍色界線 ($X_{\text{cyan}}$)**：由西牆退縮 `20 mm` + 西壁櫃深 (`1200 mm`) + 走道 `1300 mm` 直接鎖定（如 `X = 2520`）。
   - 兩界線內倉位對齊綠線後向左側水藍線擴展；綠線右側區域向綠線處擴展（保留 `1300 mm` 走道）。
2. **Stage 2: Y 軸深度 1D 切分與立柱包夾 (Column-Wrapping Phase Alignment)**
   - 將場內獨立立柱（`C1~Cn`）包入雙排背靠背中島內，使中島的 `10 mm` 背靠背分界縫貼齊立柱頂緣 `+20 mm` 或底緣 `-20 mm`（一排完整跨柱、一排於柱左/柱右分段，立柱 0 走道浪費）。
   - 組合單排深 $d + (10 + f)$ 與雙排中島深（`2210`、`2310`、`3660 mm`），將所有橫向走道壓緊於 `1300 ~ 1340 mm`。
3. **Stage 3: X 軸平移背包動態規劃 (Shifted-Pitch 1D DP)**
   - 利用代數平移 $\tilde{L} = L + 10$、$\tilde{w}_i = w_i + 10$ 消除 $(k-1)\times 10$ 間距耦合項，透過尾數同餘（除 `1000` 外步進尾數恆為 `2`）在走道微調視窗 $\delta_L \in [0, 20]\text{ mm}$ 內，於 `< 1 ms` 求得 0 非標尺寸、最少共用倉的全局最優解。

## Storeasy Unit Numbering & Route Polyline Standard (倉位編號與引導線規則)

1. **僅主倉編號（共用倉與加裝層板框不編號）**：
   - 凡透過指向箭頭（Merge Arrow）歸屬主倉的「後方 `650/780` 層板框」與「側面 `442~692` 共用倉」，一律與主倉合併計為同一單元，**不編獨立倉位號碼**；引導線直接跳過共用倉與層板框，僅串接具門向三角形（`△`/`M`）的主倉中心。
2. **「倉位編號引導線 (`TRUTH_ROUTE` / `PREDICTION_ROUTE`)」單走道 U 型巡迴法則**：
   - **起點**：由主入口側第一排外圍靠牆倉位起算第 1 號（如 `HD1 ~ HD6`）。
   - **走道內 U-Turn 去回程（嚴禁跨背靠背隔板跳躍）**：進入一條走道後，先沿走道一側（如北側排，門朝走道）由頭走到尾連續編號；至走道盡頭後 **U-Turn 跨過走道至正對面排**（南側排，門朝同一走道）折返連續編號。
   - **封頭櫃與靠牆櫃過渡**：出走道後順著中島封頭櫃（End-Caps）或外牆櫃滑入下一條平行走道，依「先橫向主區 $\to$ 後縱向次區 $\to$ 邊角區」巡迴全場。
3. **投影排序與慣性巡迴演算法 (`pyautocad`)**：
   - 若圖面繪有 `*ROUTE*` 圖層聚合線，按主倉中心於聚合線上的正交投影累積弧長（`accumulated_dist_along_route`）排序編號；若無引導線，採 `Adaptive Inertia TSP`（$\text{Cost} = \text{dist}^2 \times 100^{(1-\cos\theta)/2}$）自動繪出引導線並編號。
4. **編號格式、上下層同號對位（`D` / `U`）、禁忌跳號與字體方向**：
   - **上下層對位鐵律**：前綴為 `{店碼}D`（下層／單層，如從 **`MD1700`** 起編）；凡標註為 **`雙`（雙層倉）** 者，其正上方之上層倉位直接同號對位為 **`{店碼}U`**（例如下層 `MD1706` 對應上層 **`MU1706`**；`單` 層倉則僅有 `MDxxxx`）。
   - 支援排除 `["004", "013", "044", "444", "4444"]` 等忌諱號；文字置於主倉框正中央（`Alignment = 10`）；直立倉（$H > 1.2 W$）文字打直 `90°/270°`，橫向倉文字水平 `0°/180°`。

## 3D Clear-Height ($Z$), Volume (`才`) & Upper/Lower Tier Pricing Standard (高度、材積與上下層定價鐵律)

1. **立體淨高 ($Z$) 對應倉位高度 ($H$) 規則**：
   - **`單`（單層倉，高 `2300 mm = 2.3 m`）**：僅有 `{店碼}Dxxxx`。
   - **`半`（半層倉，下層 `1400 mm = 1.4 m` + 上層 `1400 mm = 1.4 m`）**：當樑下淨高 $Z \in [2950, 3350]\text{ mm}$ 且倉位深度設計為 **`1000 mm (1.0 m)`** 時可規劃上下 `1.4 m` 半層倉（`3350 mm` 壓樑區僅能做半層倉或 `2.3 m` 單層倉，不可做全高雙層倉）。
   - **`雙`（全高雙層倉，下層 `2000 mm = 2.0 m` + 上層 `1800 mm = 1.8 m`）**：當上方淨高 $Z \ge 3800\text{ mm}$ 時配置。
2. **營業尺寸與最後材積公式**：
   - $\text{實際容積 (m}^3\text{)} = W_{\text{m}} \times L_{\text{m}} \times H_{\text{m}}$；$\text{實際材積} = \text{實際容積} \times 35.3146$。
   - **$\text{最後材積 (才)} = \text{MROUND}(\text{ROUNDDOWN}(\text{實際材積}, 0), 5)$**（先無條件捨去小數點，再以 `5 才` 四捨五入）。
   - $\text{月租表價} = \text{ROUND}(\text{最後材積} \times \text{每才單價}, -1)$（季繳 95 折、半年 9 折、年繳 85 折/8 折皆四捨五入至十位數）。
3. **新據點（含上下層）五步定價 SOP**：
   - **Step 1（鎖定同生活圈錨定店）**：選取同行政區/相鄰生活圈具完整上下層之分店群（如桃園中壢區錨定 **中壢+平鎮新富+南崁**；台北市松山區錨定 **松山一～四店+中山八德+內湖/南港二店**）。
   - **Step 2（建立下層 `D` 基準單價曲線）**：由錨定店 `下層` 各才數實測單價建立平滑單調遞減曲線。
   - **Step 3（以「同櫃號對位 `xD` vs `xU`」決定上層 `U` 單價，嚴禁拿「同才數跨櫃」誤算價差）**：
     - 同一個雙層櫃因上層較矮、才數較小，必須用正則 `^[A-Z]([DU])(\d+)$` 比對**同櫃位上下層單價差**（桃園區穩定為 **`-14.1% ~ -16.6%`**；台北市松山區 `45~85才` 為 **`-12.5% ~ -15.0%`**、`90~145才` 為 **`-15.0% ~ -18.5%`**、`150~250才` 為 **`-19.0% ~ -23.0%`**），並直接貼齊同區鄰店上層實測價格帶。
   - **Step 4（跨區域價格階層防線）**：全級距（特別是 `80 才` 以上）強制滿足 `北市核心(松山/中山/大安) > 北市外圍與竹科(內湖/南港/新竹) > 新北核心(板橋/中和新店) > 桃園(平鎮/南崁/中壢) > 新北蛋白(三重/淡水)`。
   - **Step 5（月租表價嚴格單調遞增門禁）**：確保隨才數增加，每才單價單調不增、月租表價嚴格單調遞增（0 倒掛）。

## ⚠️ Gotchas (避坑指南)
- **上層定價三大盲點（嚴禁重犯）**：(1) 嚴禁拿「同才數（小底面積高單價下層 vs 大底面積上層）」算上下層價差 %，否則會多扣 `4%~5%` 材積級距差；(2) 嚴禁混入新北早期舊店（中和/三重湯城 `-26%~-33%`）拉低平均；(3) 嚴禁在原本較低的下層基準店單價上又套用放大折扣（雙重打折導致 `80 才+` 低於三重/淡水）。
- **單線共壁與非標尺寸幻覺**：嚴禁畫 `0 mm` 單線共壁或自創 `1120` 深、`504` 寬等非標尺寸；差幾公分時必須向走道餘量借位或重組同排模數。
- **共用倉配對違規**：單門（`772/922`）配共用倉時若 `w_main + 10 + w_shared >= 1492`，必須直接改做 `1492/1792` 雙門主倉。
- **雙軌資料表同步陷阱**：Storeasy 同時存在 `workdiv_orders` (`Order`) 與 `workdiv_quote_orders` (`QuoteOrder`)，更新狀態或退件原因時務必透過 `order_lifecycle_service` 同步雙表，禁止只改單邊。
- **單位「式/一式」防呆**：工程報價若單位為「式」或「一式」，必須標記 `unit_mismatch=True` 並阻斷跨單位直接均價比較（交由 JEV 適格性引擎判別）。
- **原生日期選擇器語系**：前端所有 `<input type="date" />` 必須加上 `lang="en"`，避免繁中瀏覽器出現 `yyyy/月/dd` 破版。
