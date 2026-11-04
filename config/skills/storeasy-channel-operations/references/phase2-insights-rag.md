# Phase 2 Insights and assistant audit

Verified against FM `b41857a01400859d5c20940ced23f7d7aded6a99` and website `ebe89253b7ceb3dbb1ed18c2285cc7464b57c40c` on 2026-07-12.

## Marketing Insights

The UI expects `visits`, `deposits`, `rents`, `churned_customers`, and an SEO metric array. The APIs return `funnel_by_location`, `unpaid_churned_customers`, and `{seo_metrics: data}`. Current zeros/empty tables are contract failure, not business evidence. The funnel also lacks campaign, promotion, channel, and UTM dimensions.

Evidence: `MarketingInsights.tsx:5-51,64-130`; `backend/app/routers/insights.py:13-83`.

## Agentic assistant

The backend is a bounded OpenAI tool-calling loop, not vector/embedding RAG. The UI sends `{message}` to relative `/api/rag/chat`; backend requires `{messages:[{role,content}]}`. Vite has no `/api` proxy. The route lacks route-level authorization, may expose internal notes, uses a synchronous client inside async code, and has no explicit timeout/token budget.

Evidence: `AgenticRagChat.tsx:37-42`; `rag_assistant.py:19-24,71-159`; `frontend/vite.config.ts`.

## Website SEO commit skepticism

The website commit changes H1, metadata, and two CTAs only on `/promotions`. The shared detail change is CMS-first loading, not a detail-page H1/CTA rewrite. New CTAs have no experiment identifier.

The repository lacks a page-level `/promotions` CTR/bounce baseline, MCP query trace, variant, window, and success threshold. “Based on MCP insights” is therefore not independently verifiable.

The index reads static `public/data`; details prefer FM CMS and then static fallback. Define index propagation and detail availability as separate publish gates.
