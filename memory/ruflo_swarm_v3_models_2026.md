---
id: mem-ruflo-swarm-v3-models-2026
brand: shared-eng
tier: L2_DECISION
status: voided
valid_from: "2026-10-01"
scope_repos: []
---

# Ruflo Swarm V3 最新模型基準記憶 (2026-10)

> **[VOIDED / 已作廢]** 本檔所載 2026-10 舊世代模型矩陣已作廢，已被現行 `~/.gemini/GEMINI.md` 之 Ruflo Swarm V3 模型基準（`gemini-4-neon-xhigh` / `gemini-4-hydrogen-xhigh` / `grok-4.7` / `qwen4-max-preview`）取代；依「只作廢不刪除」鐵律保留原文供歷史追溯，請勿再引用。

> **[Anti-Pattern 錯誤模式]**
> 誤用舊世代模型名稱（如 `claude-3-5-sonnet`、`deepseek-flash` 或舊版 `grok-4.6`）配置多代理工作流，導致紅隊審查與重構能力未對齊最新算力。

> **[Correct-Pattern 正確作法]**
> 全域 (`~/.gemini/GEMINI.md`、`~/.cursor/rules/skill-routing-and-swarm-v3.mdc`、`/multi-agent-mode`、`/skillorchestrator`) 統一鎖定 2026 最新世代主力模型矩陣：
> - **多模態與百萬 Context 架構發想 (`Agent A` / `Agent C` / `Agent E`)**：**`gemini-4-carbon`**（全面取代舊版 `gemini-4-argon`）
> - **魔鬼代言人紅隊批判 (`Agent B` / `Agent E`)**：**`grok-4.7`**（注意：**Grok 4.7** 為最新模型，全面取代 `grok-4.6`）
> - **跨模組重構、繁中精準結構化與 Fixer 除錯救援 (`Agent D` / `Agent C`)**：**`qwen-3.8-max`**
> - **零區安全守門、日常快改與極速 CoT 邏輯推理 (`Agent 0` / `Agent D` / `Agent E`)**：**`deepseek-flash`**
> - **量化風險與比對適格性校準 (System 1 Calibrated Judgments)**：TypeSafe **`jev-1.13.0` (`jev-latest`)**
