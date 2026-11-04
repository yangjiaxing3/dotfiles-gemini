---
name: skillorchestrator
description: "Use when orchestrating multi-skill Ruflo Swarm pipelines for iPhone/MacBook/3C recycling SEO, copy, and valuation. 二手回收Swarm協調/多技能調度"
---

# Skill Orchestrator (iMSSO)

Read the canonical workflow at `.agents/workflows/skillorchestrator.md` completely before acting. Treat that file as the single source of truth. This skill exists so the workflow can be discovered and applied automatically inside this workspace.

## Trigger

Activate when the user mentions 「skillorchestrator」、「Swarm 技能協調」、「技能調度」, or asks to orchestrate multiple domain skills (競品/關鍵字、EEAT 內容、GEO/AEO、技術 SEO、監控預警) for a complex delivery.

## Execution Summary

1. **任務特徵分析**：依平台維度與業務維度解析指令，對照 workflow 中的技能路由表，挑出需掛載的 skills。
2. **Swarm 協作**：Manager 不單打獨鬥；用環境中可用的 subagent 工具（Agent tool）派發 Worker，各自掛載對應技能並共享狀態。
3. **品質門禁**：交付前核對多平台覆蓋性、EEAT 品質、追蹤碼與內鏈完整性、防越界（Boundary Sentinel）。
4. **死局逃脫**：Worker 自我修復上限 5 次、品質退回上限 3 次；超限即中止並改調 `fixer-prompt`（對應 skill：`fixer-prompt`）。

## Environment Adaptation

- Workflow 中的 `npx ruflo@latest` / `claude-flow` 指令在當前環境未必可用；以 Qoder 的 Agent tool（GeneralPurpose / CodeReview 等 subagent）等價模擬 spawn 與並行，維持「角色分工 + 共享狀態 + 門禁檢查」的核心結構。
- 記憶落盤改寫入本專案的 `SESSION-HANDOFF.md` 與 `.agent/memory/`（沿用既有慣例）。

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
