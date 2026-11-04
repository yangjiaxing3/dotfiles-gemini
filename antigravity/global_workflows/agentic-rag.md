---
name: agentic-rag
description: "Use when implementing Agentic RAG pipelines with multi-step query rewriting, dynamic retrieval, and grounding checks. 動態檢索增強生成/Agentic RAG實作"
---

// turbo-all

# Agentic RAG (Retrieval-Augmented Generation — Ruflo Swarm V3)

This skill implements an "Agentic" approach to RAG, where retrieval is treated as an active tool loop (`Thought -> Retrieve -> Calibrate -> Synthesize`) rather than a single-shot passive lookup.

## Core Principles

1. **Tool-Based Retrieval**: Retrieval (`graphify query`, SQL/FTS search, vector lookup) is invoked dynamically by the Agent.
2. **Multi-Hop Reasoning Loop**: The Agent iteratively refines queries based on intermediate observations.
3. **Calibrated Grounding**: Candidate chunks are scored for comparability/relevance before final synthesis.

## Workflow & Ruflo Swarm V3 Model Routing

### 1. Assessment
- **Trigger**: User asks a question requiring multi-hop codebase knowledge (`graph.json`) or domain data (`Turso` / historical quotes) not in current context.

### 2. The Reasoning & Retrieval Loop (ToolLoop — `DeepSeek-V4.1-Flash` + `jev-1.13.0`)
- **Swarm Routing for Retrieval**: Multi-hop query formulation and tool calling require sub-second latency and high-speed Chain-of-Thought:
  - **Command**: `npx ruflo@latest agent spawn -t searcher --model DeepSeek-V4.1-Flash`
  - **Calibration**: Pair with TypeSafe **`jev-1.13.0`** (`evaluate_comparability` / `score`) to filter out low-relevance or mismatched-unit candidates before synthesis.
  - **Why**: `DeepSeek-V4.1-Flash` executes rapid iterative retrieval loops at minimal latency, while `jev-1.13.0` prevents noisy chunks from polluting the synthesizer context.

### 3. Deep Synthesis & Adversarial Fact-Check (`gemini-4-argon` + `grok-4.7`)
- **Swarm Routing for Synthesis**: Once curated context pieces are gathered, hand them over to the 1M+ context flagship model for synthesis, backed by red-team hallucination checking:
  - **Command**: `npx ruflo@latest agent spawn -t analyst --model gemini-4-argon` (or `--model qwen-3.8-max` for structured Traditional Chinese reports)
  - **Adversarial Verification**: `npx ruflo@latest agent spawn -t reviewer --model grok-4.7` (audits citations and flags ungrounded claims).
  - **Why**: `gemini-4-argon` connects cross-module dependencies across massive contexts, while `grok-4.7` ensures zero hallucinated citations.

## Best Practices for the Agent
- **Graph-First Retrieval**: When `graphify-out/graph.json` exists, query graph nodes/paths first before raw text grep.
- **Source Verification**: Always link exact file paths and line numbers (`[file.py](file:///path/to/file.py#L10-L20)`).
- **Explicit Reasoning Traces**: State *why* each retrieval hop is executed.

## ⚠️ Gotchas (避坑指南)
- **禁止單次盲搜即下結論**：遇到跨表或跨模組問題（如 `Order` 與 `QuoteOrder`），必須追蹤上下游依賴鏈，不可只看第一個命中片段。
- **終端機輸出保護 (Context Overflow Prevention)**：檢索資料庫或 API 時務必加上 `LIMIT` 或導向暫存檔，禁止將整張表直接印到 stdout。