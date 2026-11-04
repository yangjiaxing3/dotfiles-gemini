---
name: stage-gate-review
description: "Use when a milestone (e.g. P0-1) finishes and requires 3-role read-only skeptical code review before advancing. 階段審查/懷疑式程式碼審查/stage-gate"
---

# Stage-Gate Skeptical Review

Read the canonical workflow at `.agents/workflows/stage-gate-review.md` completely before acting. Treat that file as the single source of truth.

## Trigger

Activate automatically when a staged development plan (P0-1/P0-2… phases or an equivalent task list) completes a stage, or when the user says 「stage-gate review」、「階段審查」、「skeptical review」、or asks for a multi-skill code review at a stage boundary.

## Execution Summary

1. **Gate rule**: unresolved 🔴 blocks entry to the next stage; review agents are strictly read-only; fixes are done by the orchestrator (review/fix separation); every "the test will catch it" claim must be proven by a mutation check (break on purpose → test red → restore).
2. **Step 0**: confirm stage deliverables committed; collect file list, stage spec/acceptance criteria, hard boundaries, and the known test-debt list.
3. **Step 1**: pick 3 different agency-* skill roles by stage type (backend/contract → code-reviewer + backend-architect + api-tester; frontend → code-reviewer + ui-designer + ux-architect; data/perf → code-reviewer + database-optimizer + api-tester).
4. **Step 2**: spawn the 3 agents in parallel with skeptical instructions, file:line evidence requirements, 🔴/🟡/💭 grading, ~600-word cap, and a Go/No-Go verdict.
5. **Step 3–4**: converge findings (≥2 agents = high confidence); defer out-of-scope findings to later-stage backlog; 🔴 must be fixed this round.
6. **Step 5–6**: fix → re-run tests → mutation-verify each new gate → re-run stage acceptance (including "forbidden files diff empty" clauses) → commit → update SESSION-HANDOFF and memory.

## Rules

- All analysis and output in 繁體中文.
- Never let a review agent write files; never skip the mutation verification for test-hardening fixes.
- Do not run this workflow for single-file small fixes or hotfixes.

## ⚠️ Gotchas (避坑指南)
- **雙軌資料表同步陷阱**：Storeasy 同時存在 `workdiv_orders` (`Order`) 與 `workdiv_quote_orders` (`QuoteOrder`)，更新狀態或退件原因時務必透過 `order_lifecycle_service` 同步雙表，禁止只改單邊。
- **單位「式/一式」防呆**：工程報價若單位為「式」或「一式」，必須標記 `unit_mismatch=True` 並阻斷跨單位直接均價比較（交由 JEV 適格性引擎判別）。
- **原生日期選擇器語系**：前端所有 `<input type="date" />` 必須加上 `lang="en"`，避免繁中瀏覽器出現 `yyyy/月/dd` 破版。
