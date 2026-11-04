---
name: storeasy-seo-looping
description: "Use when designing multi-location mini-storage pages with dynamic semantic SEO loops to prevent doorway-page penalties. 多據點迷你倉SEO/防垃圾內容"
---

# Storeasy 多據點 SEO 迴圈（防門頁）

只換地名/店名的據點頁 = Google 眼中的 Doorway Pages。每一頁都要有**不同的切入意圖、在地事實與主打服務**，且同一據點每次重新產生結果必須相同（冪等）。

## 五個核心原則

1. **Spintax 引擎**：模板可寫 `{迷你倉|個人倉庫|小型倉庫}`，由解析器依據點 ID 的**穩定雜湊**選字（實作見下方）。文案與程式解耦。
2. **高熵模板**：至少 6–8 種敘事切入（搬家裝潢過渡、換季收納、小資擴充、事實陳述…），動詞與介系詞也要抽換。目標：同類頁面文字重複率 < 20%。
3. **主打服務輪替**：依穩定雜湊讓不同據點主打不同細分（個人倉、企業微型倉、重機車位、恆溫恆濕倉），整個網域分區攔截不同搜尋意圖。
4. **長尾詞由意圖缺口注入**：從 GSC / Ads / 缺口報告取高轉換長尾詞（24H 門禁、代收包裹、除濕防霉），平均分散放在標題/描述尾端。
5. **主體清晰、不排他**：寫「中和恆溫個人倉庫」，不寫「中和自助倉」；寫「主打重機車位、個人倉儲空間」，不寫「只租重機」。

## 多倉型頁面的四層細化

1. **搜尋視角分流**：同一倉型依比價、防霉、搬家急用、換季收納等視角產生不同標題，不用 `[地區] [倉型] 出租｜Storeasy` 死板格式。
2. **倉型關鍵字隔離**：

| 倉型 | 核心訴求 | 必含關鍵字 |
| :--- | :--- | :--- |
| 個人倉／換季衣物 | 恆溫除濕、防黴、24H 存取 | 迷你倉、個人倉庫、空間收納 |
| 企業倉／文件帳冊 | 消防合格、機密防護、代收發 | 企業倉庫、工商資料安全、發票報帳 |
| 特殊倉（重機/紅酒/收藏） | 15℃ 恆溫恆濕、獨立車位、高額保險 | 重機車位、紅酒倉、高價收藏品倉 |

3. **三段式描述合成**：`痛點 Hook（10 種）` + `Storeasy 硬體優勢（10 種）` + `線上看倉/24H CTA（10 種）`，可組出 1,000 種以上。
4. **倉型身分門禁**：產出前檢查跨倉型污染（重機頁出現「換季衣物」、企業倉頁缺「企業倉庫」），**命中就拋錯阻斷**，不靜默修正。

7 大 TA 人格與範例 Title/Description 見 [references/ta-persona-matrix.md](references/ta-persona-matrix.md)，撰寫 Hook 時再讀。

## 穩定 Spintax 實作（Python）

```python
import hashlib
import random
import re

SPIN = re.compile(r"\{([^{}]+)\}")

def spin(template: str, store_id: str, salt: str = "") -> str:
    # 為什麼用 sha256：內建 hash() 每個行程都會隨機化，重新產生時頁面會變動
    seed = int(hashlib.sha256(f"{store_id}:{salt}".encode()).hexdigest(), 16)
    rng = random.Random(seed)  # 獨立 RNG，不污染全域 random 狀態
    while SPIN.search(template):  # 由內而外，支援巢狀 {a|{b|c}}
        template = SPIN.sub(lambda m: rng.choice(m.group(1).split("|")), template)
    return template
```

`salt` 用欄位名（如 `"title"`、`"desc"`），讓同一據點的不同欄位選到不同字。

## ⚠️ Gotchas (避坑指南)

- **重複率要量測，不要憑感覺**：產出後對同倉型頁面兩兩計算相似度（如 shingle Jaccard），超過門檻的據點列出來重寫。
- **在地事實不能編**：交通、地標、坪數、價格只用資料庫/後台的真實值；沒有資料就省略該句，不要生成看似合理的內容。
- **改模板會改變所有頁面**：模板或 salt 變動等同全站內容改版，要先抽樣預覽並記錄版本，避免一次大量變動排名。
