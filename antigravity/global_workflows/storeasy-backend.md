---
description: 按需調用收多易後端 FastAPI、通路促銷、迷你倉圖表、CAD 與報表技能，不佔常駐額度
---

# /storeasy-backend 工作流

1. 依任務類型前往 `~/.gemini/config/skills/` 按需讀取對應技能：
   - **通路促銷與同步**：`storeasy-channel-operations/SKILL.md`
   - **迷你倉營運與 D3 圖表**：`storeasy-mini-warehouse-viz/SKILL.md`、`d3-data-visualization/SKILL.md`
   - **SketchUp 轉 CAD 排櫃**：`skp-to-cad-ministorage/SKILL.md`
   - **Python / FastAPI / BigQuery**：`fastapi-templates/SKILL.md`、`managing-python-dependencies/SKILL.md`、`developing-with-bigquery/SKILL.md`
   - **文件與報表匯出**：`xlsx/SKILL.md`、`pdf/SKILL.md`、`docx/SKILL.md`
2. 若搭配 `/swarm` 或 `/multi-agent-mode`，將所需技能路徑寫入對應 Worker 的 `brief` 中按需載入。
