#!/usr/bin/env python3
"""
Agent Skills 全系統深度優化器 (scripts/optimize_all_skills.py)

落實文章四大黃金法則（方案 1：專案 + 全域雙層深度優化）：
1. Description 黃金重構：控制在 <= 135 字元，必備 `Use when` 主動偏見 + `Why` 推理目的 + `Not for` 對比邊界 + 繁中/英文雙語口語錨點。
2. Progressive Disclosure 三層架構：超過 260 行的 SKILL.md 自動將長篇附錄/範例抽離至 `references/detailed-guide.md`，主體控制在 < 220 行。
3. 植入 `## ⚠️ Gotchas (避坑指南)`：消除死板口號，補充真實踩雷邊界案例。
4. 消除雙胞胎分裂與 Context Budget 溢位截斷。
"""
from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOTS = [
    WORKSPACE_ROOT / ".agents" / "skills",
    WORKSPACE_ROOT / ".agent" / "skills",
    Path(r"C:\Users\Jiaxing\.gemini\config\skills"),
]
BACKUP_PATH = Path(
    r"C:\Users\Jiaxing\.gemini\antigravity\brain\3ce22dfd-0335-4198-beb3-cefee35bef0f\scratch\skills_backup.json"
)

# 黃金 Description 字典（<= 135 chars，包含 Use when + Why/Context + Not for + 繁中雙語觸發詞）
CURATED_DESCRIPTIONS: dict[str, str] = {
    "agency-taiwan-threads-strategist": (
        "Use when drafting Taiwan Threads posts with fact-first hooks, full-width punctuation, and zero fake drama. 台灣Threads社群貼文與互動文案"
    ),
    "agency-taiwan-zh-hant-editor": (
        "Use when rewriting UI copy, docs, or articles into natural Taiwan Traditional Chinese without translationese. 台灣繁體中文語感總編/消除翻譯腔"
    ),
    "cloud-databases-onboarding": (
        "Use when onboarding or provisioning Google Cloud databases (Cloud SQL, Spanner, AlloyDB, Firestore). GCP雲端資料庫開通與配置"
    ),
    "create-verification-skill": (
        "Use when generating a project-local verify-<app> E2E verification skill and feature test charter. 建立專案專屬E2E自動驗證Skill"
    ),
    "dataform-bigquery": (
        "Use when creating or optimizing Dataform SQLX ELT pipelines, actions, and source declarations in BigQuery. BigQuery Dataform資料管線開發"
    ),
    "dbt-bigquery": (
        "Use when creating, modifying, or optimizing dbt models, incremental SQL, and tests for BigQuery. BigQuery dbt模型開發與SQL優化"
    ),
    "e2e": (
        "Use when running end-to-end Playwright browser verification across user journeys and visual states. 端到端E2E瀏覽器驗證與回歸測試"
    ),
    "gcp-pipeline-orchestration": (
        "Use when orchestrating BigQuery, Dataform, or Dataproc workflows with Cloud Composer, Workflows, or Scheduler. GCP資料管線排程與編排"
    ),
    "gcp-spark": (
        "Use when building or configuring Serverless Spark or Dataproc PySpark jobs on Google Cloud. GCP Dataproc與Serverless Spark開發"
    ),
    "gcp-spark-observability": (
        "Use when monitoring GCP Spark job metrics, Cloud Logging, and driver/executor resource bottlenecks. GCP Spark監控與效能觀測"
    ),
    "gcp-spark-troubleshooting": (
        "Use when diagnosing GCP Spark OOM errors, shuffle skew, or failed Dataproc jobs. GCP Spark錯誤排查與OOM調優"
    ),
    "migrate-to-e2e": (
        "Use when migrating legacy manual or brittle UI tests to structured E2E verification charters. 舊版測試遷移至結構化E2E驗證"
    ),
    "reverse-engineer-anything": (
        "Use when reverse engineering native, managed, Electron, or packaged binaries with REA evidence tools. 逆向工程與二進位產物分析"
    ),
    # --- Storeasy & 專案核心工作流 Skills ---
    "multi-agent-mode": (
        "Use when tasks need 5-stage dialectical review (Sentinel/Ideation/Red Team/Synthesis/QA) to prevent blind spots. 多Agent模式/紅隊辯證/multi-agent"
    ),
    "fixer-prompt": (
        "Use when a bug or test fails 2+ times in a row or hits a dead loop to diagnose root causes from first principles. Fixer除錯/死循環修復/修不好"
    ),
    "graphify": (
        "Use when querying codebase architecture, file relationships, or symbol nodes via graph.json before grepping raw files. 專案架構查詢/節點關聯/知識圖譜"
    ),
    "storeasy-mini-warehouse-viz": (
        "Use when building or tuning mini-storage executive D3 charts comparing branch revenue, rented volume, and unit yield. 迷你倉主管分析圖/實收租金/每材實收"
    ),
    "storeasy-channel-operations": (
        "Use when implementing or reviewing StoreasyFMnew Channel Manager promotions, pricing sync, public-site propagation, or rollback. 通路促銷發布/價格同步"
    ),
    "storeasy-seo-looping": (
        "Use when designing multi-location mini-storage pages with dynamic semantic SEO loops to prevent doorway-page penalties. 多據點迷你倉SEO/防垃圾內容"
    ),
    "session-handoff": (
        "Use when wrapping up, pausing, or resuming a coding session to persist context in SESSION-HANDOFF.md. 開發交接/保存進度/结束session/handoff"
    ),
    "stage-gate-review": (
        "Use when a milestone (e.g. P0-1) finishes and requires 3-role read-only skeptical code review before advancing. 階段審查/懷疑式程式碼審查/stage-gate"
    ),
    "skillorchestrator": (
        "Use when orchestrating multi-skill Ruflo Swarm pipelines for iPhone/MacBook/3C recycling SEO, copy, and valuation. 二手回收Swarm協調/多技能調度"
    ),
    "us3c-seo-loop": (
        "Use when running the US3C 3D SEO flywheel combining GSC/GA4/Ads insights for 3C/phone recycling pages. 二手3C手機回收SEO飛輪/關鍵字佈局"
    ),
    "kiosk-image-optimizer": (
        "Use when compressing, resizing (<=1500px), and converting 24H recycling kiosk or branch photos to WebP (<=250KB). 門市回收機圖片壓縮/縮圖轉WebP"
    ),
    "skp-to-cad-ministorage": (
        "Use when converting SketchUp (.skp) models into multi-layer CAD (.dxf/.dwg) with mini-storage layouts. SketchUp轉CAD/迷你倉排櫃"
    ),
    # --- 前端、UI/UX 與視覺化 Skills ---
    "impeccable": (
        "Use when polishing or redesigning React UI/UX hierarchy, typography, and micro-interactions to fix AI slop. 美化React介面/Dashboard設計"
    ),
    "frontend-design": (
        "Use when building distinctive, production-grade web pages, React components, or dashboards with bespoke visual aesthetics. 前端介面設計/UI美化/網頁元件"
    ),
    "design-taste-frontend": (
        "Use when shipping landing pages or UI redesigns requiring anti-template design systems and visual audits. 高品味前端設計/反廉價AI模板"
    ),
    "taste-skill": (
        "Use when shipping landing pages or UI redesigns requiring anti-template design systems and visual audits. 高品味前端設計/反廉價AI模板"
    ),
    "emil-design-eng": (
        "Use when refining UI motion, spring physics, component tactile polish, and invisible interaction details. UI微互動/動畫細節/元件質感打磨"
    ),
    "d3-data-visualization": (
        "Use when building custom D3.js SVG/DOM charts, scales, annotations, and interactive data joins. Not for static diagrams. D3資料視覺化/互動圖表"
    ),
    "diagram-design": (
        "Use when generating architecture, flowchart, sequence, ER schema, Sankey, or Gantt diagrams as HTML/SVG/PNG/drawio. 系統架構圖/流程圖/ER圖繪製"
    ),
    "web-design-guidelines": (
        "Use when auditing UI code against Web Interface Guidelines, UX ergonomics, and keyboard/screen-reader accessibility. 介面規範審查/UX與無障礙檢查"
    ),
    "vercel-composition-patterns": (
        "Use when refactoring React components with boolean props into Compound Components or React 19 patterns. React複合元件重構/消除boolean props"
    ),
    "composition-patterns": (
        "Use when refactoring React components with boolean props into Compound Components or React 19 patterns. React複合元件重構/消除boolean props"
    ),
    "vercel-react-best-practices": (
        "Use when optimizing React/Next.js rendering performance, data fetching, bundle size, and hooks stability. React效能優化/Hooks最佳實踐"
    ),
    "react-best-practices": (
        "Use when optimizing React/Next.js rendering performance, data fetching, bundle size, and hooks stability. React效能優化/Hooks最佳實踐"
    ),
    "vercel-react-native-skills": (
        "Use when building or optimizing React Native / Expo mobile lists, native modules, and animations. React Native手機App開發與效能優化"
    ),
    "react-native-skills": (
        "Use when building or optimizing React Native / Expo mobile lists, native modules, and animations. React Native手機App開發與效能優化"
    ),
    "web-artifacts-builder": (
        "Use when creating multi-component interactive HTML/React/Tailwind/shadcn artifacts with complex state. 建立複雜互動式React/HTML元件成品"
    ),
    # --- 後端、資料庫、資安與測試 Skills ---
    "fastapi-templates": (
        "Use when scaffolding FastAPI backends with async dependency injection, Pydantic schemas, and error handling. FastAPI後端服務設計/非同步依賴注入"
    ),
    "security-audit": (
        "Use when auditing auth, file uploads, or APIs for SQL injection, path traversal, and vulnerabilities. 資安稽核/漏洞掃描/SQL Injection與Path Traversal"
    ),
    "accidental-data-loss-prevention": (
        "Use when running destructive SQL (DROP TABLE/TRUNCATE/DELETE) or cloud storage deletions to verify consent. 防資料誤刪/DROP TABLE與DELETE安全保護"
    ),
    "webapp-testing": (
        "Use when running Playwright automation to test local web UIs, capture screenshots, and check console errors. Playwright前端UI自動化測試與截圖"
    ),
    "browser-act": (
        "Use when automating authenticated browser sessions, extracting JS-rendered pages, or capturing XHR/HAR traffic via CLI. 瀏覽器自動化擷取/登入操作/截圖"
    ),
    "browser-act-skill-forge": (
        "Use when forging reusable website scraping or API automation skill packages from browser-act exploration. 網站API探勘與可重用爬蟲Skill鍛造"
    ),
    "mcp-builder": (
        "Use when building MCP (Model Context Protocol) servers in FastMCP or TypeScript SDK to expose external tools. 建立MCP Server/串接第三方API"
    ),
    "workflow-automation": (
        "Use when designing durable background workflows with retries and persistence using Inngest, Temporal, or n8n. 持久化背景工作流/Inngest與Temporal"
    ),
    "managing-python-dependencies": (
        "Use when running pip install or adding Python packages to enforce project virtualenvs (.venv) over global installs. Python虛擬環境與套件依賴管理"
    ),
    # --- 文件、文案與辦公自動化 Skills ---
    "humanizer": (
        "Use when editing text to remove AI writing signs (em-dashes, rule-of-three, promotional fluff) so copy reads naturally. 去除AI生成痕跡/改寫得像真人書寫"
    ),
    "humanizer-zh-tw": (
        "Use when editing Traditional Chinese text to remove AI writing signs (破折號, 三段式排比, 宣傳腔) for natural human tone. 繁體中文去除AI生成痕跡/真人語氣"
    ),
    "pdf": (
        "Use when extracting text/tables from multi-page PDFs, merging/splitting PDF files, or filling PDF forms programmatically. PDF表格與文字提取/合併拆分PDF"
    ),
    "xlsx": (
        "Use when creating, analyzing, or formatting Excel (.xlsx/.csv) spreadsheets with formulas and financial number styles. Excel試算表報表匯出/公式與千分位格式"
    ),
    "docx": (
        "Use when creating or editing Word (.docx) documents with tracked changes, comments, and structured styles. Word文件生成與編輯/追蹤修訂"
    ),
    "doc-coauthoring": (
        "Use when co-authoring technical specs, RFCs, architecture proposals, or decision docs with iterative verification. 技術規格書與架構提案協作撰寫"
    ),
    "writing-plans": (
        "Use when planning multi-step features before coding to produce a file-by-file Implementation Plan. 撰寫分步實作計畫/Implementation Plan"
    ),
    "sparc-methodology": (
        "Use when tackling complex system designs via SPARC (Specification, Pseudocode, Architecture, Refinement, Completion). SPARC五階段系統開發與實作計畫"
    ),
    "tdd-workflow": (
        "Use when enforcing strict Red-Green-Refactor test-driven development cycles before writing production implementation. TDD測試驅動開發循環"
    ),
    # --- SEO 與內容增長系列 (濃縮並轉繁中雙語錨點) ---
    "seo-audit": (
        "Use when running a full-page or site-wide SEO audit covering Meta tags, JSON-LD, semantic headers, robots.txt, and CWV. 完整SEO審查/單頁與全站SEO檢查"
    ),
    "on-page-seo-auditor": (
        "Use when diagnosing why a single page dropped in rankings by auditing H1, title/meta, keywords, and links. 單頁on-page SEO審計/排名掉落診斷"
    ),
    "technical-seo-checker": (
        "Use when diagnosing Core Web Vitals (LCP/CLS), crawlability, robots.txt, sitemaps, or indexing errors. 技術SEO診斷/Core Web Vitals與索引檢查"
    ),
    "internal-linking-optimizer": (
        "Use when finding orphan pages and planning internal link architecture and anchor text authority flow. 孤島頁面偵測/站內連結與錨點權重規劃"
    ),
    "schema-markup-generator": (
        "Use when generating JSON-LD structured data for FAQ, HowTo, Article, Product, or LocalBusiness rich results. 產生JSON-LD結構化資料標記/FAQ"
    ),
    "geo-content-optimizer": (
        "Use when optimizing content to increase citation rates in ChatGPT, Perplexity, Gemini, and AI Overviews. AI搜尋引用優化/GEO優化/ChatGPT與Perplexity"
    ),
    "entity-optimizer": (
        "Use when building Knowledge Graph, Wikidata, and sameAs entity signals so AI engines recognize brand authority. 實體知識圖譜優化/AI品牌識別"
    ),
    "content-quality-auditor": (
        "Use when scoring articles against the 80-item CORE-EEAT rubric for publish readiness and factual authority. 內容品質與EEAT 80項評分審查"
    ),
    "domain-authority-auditor": (
        "Use when auditing domain trust and citation credibility via the 40-item CITE framework. 網域權威度與CITE可信度審計"
    ),
    "backlink-analyzer": (
        "Use when profiling external referring domains, anchor distribution, toxic backlinks, and competitor link gaps. 外部反向連結分析/外鏈權重缺口"
    ),
    "alert-manager": (
        "Use when configuring automated threshold alerts for future SEO ranking drops, traffic anomalies, or technical regressions. 設定SEO排名掉落預警與監控通知"
    ),
    "content-gap-analysis": (
        "Use when mapping competitor topic coverage to discover missing content themes and editorial calendar opportunities. 競品內容缺口分析/選題規劃"
    ),
    "content-refresher": (
        "Use when updating decaying or outdated articles to recover lost organic rankings and refresh GEO signals. 舊文翻新與流量衰退排名恢復"
    ),
    "meta-tags-optimizer": (
        "Use when rewriting Title tags, Meta descriptions, and Open Graph tags to maximize SERP click-through rate (CTR). Title與Meta標籤優化/提升點擊率"
    ),
    "seo-content-writer": (
        "Use when drafting net-new SEO articles or landing pages with intent-aligned headers, snippets, and EEAT evidence. 撰寫全新SEO文章與著陸頁文案"
    ),
    "serp-analysis": (
        "Use when analyzing SERP layout, AI Overviews, featured snippets, and search intent for a target query. SERP搜尋結果版面與意圖分析"
    ),
    "rank-tracker": (
        "Use when measuring keyword SERP position deltas over time across organic search and AI response engines. 關鍵字排名追蹤與變動分析"
    ),
    "performance-reporter": (
        "Use when compiling multi-metric monthly SEO stakeholder reports across traffic, rankings, and conversions. 產出SEO月報與多指標績效報告"
    ),
    "keyword-research": (
        "Use when discovering high-opportunity search terms, evaluating search volume/difficulty, and tagging keyword intent. 關鍵字研究與搜尋量評估"
    ),
    "keyword-clustering": (
        "Use when grouping keywords by search intent and mapping clusters to target URLs to prevent cannibalization. 關鍵字意圖聚類與頁面映射"
    ),
    "competitor-analysis": (
        "Use when dissecting a single competitor's organic keyword footprint, top pages, and backlink strategy. 單一競品自然流量與關鍵字深度剖析"
    ),
    "competitive-landscape": (
        "Use when mapping market-wide SEO leaders, share of voice, winning content themes, and strategic gaps. 產業SEO競爭版圖與市場缺口分析"
    ),
    "link-prospecting": (
        "Use when finding high-authority link prospects and drafting outreach from SERP and backlink signals. 外鏈潛在客戶開發與公關聯繫"
    ),
    "seo-coach": (
        "Use when guiding users step-by-step on which OpenSEO workflow, MCP data source, or search strategy to run next. SEO教練引導與下一步策略建議"
    ),
    "seo-project-setup": (
        "Use when initializing a local SEO workspace with brand positioning, target goals, and Search Console MCP intake. 初始化SEO專案空間與GSC串接"
    ),
    "notfair-seo-analysis": (
        "Use when running deep GSC + GA4 cross-channel organic search diagnostics and cannibalization checks. GSC與GA4跨渠道深度SEO分析"
    ),
    "seo-analysis": (
        "Use when running deep GSC + GA4 cross-channel organic search diagnostics and cannibalization checks. GSC與GA4跨渠道深度SEO分析"
    ),
    "google-ads-audit": (
        "Use when auditing Google Ads account health, wasted spend, quality scores, and onboarding business context. Google Ads廣告帳戶健檢與投放優化"
    ),
    # --- Agency 專家角色系列 (補齊 Use when 主動觸發條件與繁中雙語錨點) ---
    "agency-agents-orchestrator": (
        "Use when coordinating multi-agent development pipelines across architecture, UX, coding, and QA phases. 多代理開發流水線總指揮/orchestrator"
    ),
    "agency-engineering-backend-architect": (
        "Use when designing scalable backend architectures, FastAPI/Turso schemas, microservice boundaries, and API contracts. 後端系統架構設計/資料庫架構與API規劃"
    ),
    "agency-engineering-database-optimizer": (
        "Use when tuning slow SQL queries, designing PostgreSQL/Turso indexes, and normalizing schemas. SQL查詢加速/索引策略與Schema正規化"
    ),
    "agency-engineering-code-reviewer": (
        "Use when performing constructive code reviews focused on correctness, security, maintainability, and edge cases. 專業程式碼審查/Code Review/邏輯與邊界檢查"
    ),
    "agency-engineering-codebase-onboarding-engineer": (
        "Use when tracing unfamiliar code paths, mapping module dependencies, and explaining codebase facts to engineers. 陌生程式碼庫導覽/追蹤呼叫路徑與模組關聯"
    ),
    "agency-engineering-frontend-developer": (
        "Use when implementing modern React/TypeScript UI components, state hooks, and responsive web performance. 前端React/TS元件開發與狀態管理"
    ),
    "agency-engineering-devops-automator": (
        "Use when automating CI/CD pipelines, Docker/cloud deployments, and infrastructure provisioning scripts. CI/CD自動化部署與雲端運維"
    ),
    "agency-engineering-rapid-prototyper": (
        "Use when building fast proof-of-concept MVPs to validate product hypotheses with minimal boilerplate. 快速MVP原型驗證開發"
    ),
    "agency-engineering-technical-writer": (
        "Use when writing clear developer READMEs, API reference docs, and onboarding tutorials from source code. 撰寫開發者文件/API手冊與README"
    ),
    "agency-design-ui-designer": (
        "Use when establishing visual design tokens, color palettes, component libraries, and pixel-perfect UI layouts. UI視覺設計系統/配色與元件庫美化"
    ),
    "agency-design-ux-architect": (
        "Use when structuring UX information architecture, layout grids, user flows, and CSS foundation systems. UX資訊架構/版面格線與操作流程設計"
    ),
    "agency-design-whimsy-injector": (
        "Use when adding delightful micro-interactions, Easter eggs, and memorable brand personality to bland UIs. 注入品牌趣味微互動與驚喜細節"
    ),
    "agency-testing-accessibility-auditor": (
        "Use when auditing UI components against WCAG accessibility standards, keyboard navigation, and screen readers. 無障礙WCAG標準審查/鍵盤導航與螢幕閱讀器檢測"
    ),
    "agency-testing-api-tester": (
        "Use when validating REST/FastAPI endpoints, edge-case payloads, auth headers, and contract regressions. 後端API端點測試與邊界ペイロード驗證"
    ),
    "agency-testing-workflow-optimizer": (
        "Use when analyzing team or system workflows to eliminate bottlenecks and automate repetitive manual steps. 工作流程瓶頸分析與自動化提效"
    ),
    "agency-data-consolidation-agent": (
        "Use when aggregating multi-branch sales or operations metrics into unified executive summary views. 跨分店銷售與營運數據彙整儀表板"
    ),
    "agency-sales-data-extraction-agent": (
        "Use when extracting MTD/YTD sales KPIs and forecasts from Excel spreadsheets into reporting pipelines. Excel銷售指標提取與預測汇总"
    ),
    "agency-support-analytics-reporter": (
        "Use when turning raw business datasets into KPI dashboards, statistical insights, and decision reports. 商業數據統計分析與KPI決策報告"
    ),
    "agency-support-infrastructure-maintainer": (
        "Use when diagnosing server reliability, resource utilization, backup health, and operational stability. 伺服器穩定度與基礎設施運維監控"
    ),
    "agency-project-management-jira-workflow-steward": (
        "Use when enforcing traceable Git commits, PR templates, and branch workflows linked to issue trackers. Git提交規範與PR分支流程管理"
    ),
    "agency-academic-study-planner": (
        "Use when designing spaced-repetition and Feynman-method study schedules for exams or technical mastery. 費曼學習法與記憶曲線備考計畫"
    ),
    "agency-marketing-content-creator": (
        "Use when planning multi-channel brand storytelling and social copy tailored to platform audiences. 多渠道品牌故事與社群行銷文案創作"
    ),
    "agency-marketing-growth-hacker": (
        "Use when designing low-cost, high-ROI user acquisition and A/B conversion experiments. 低成本獲客實驗與轉化率增長駭客"
    ),
    "agency-marketing-seo-specialist": (
        "Use when formulating holistic organic search growth strategies combining technical SEO and content authority. 全域自然搜尋增長與SEO策略規劃"
    ),
    "agency-paid-media-creative-strategist": (
        "Use when crafting high-converting RSA ad copy and creative test matrices for Google/Meta Ads. 付費廣告RSA文案與素材測試策略"
    ),
    "agency-paid-media-tracking-specialist": (
        "Use when implementing GTM, GA4, Google Ads, or Meta CAPI conversion tracking tags and attribution. GTM/GA4與廣告轉化追蹤碼埋設"
    ),
    # --- Agent-* 10 個空殼技能修復 (賦予明確的觸發場景與負向邊界) ---
    "agent-arch-system-design": (
        "Use when drafting high-level distributed system architecture diagrams and service boundary specs. 分散式系統架構與服務邊界設計"
    ),
    "agent-code-analyzer": (
        "Use when performing static complexity analysis, dead-code detection, and technical debt audits. 程式碼複雜度分析與技術債盤點"
    ),
    "agent-coder": (
        "Use when implementing well-scoped feature modules with clean typing and unit test coverage. 模組功能實作與單元測試撰寫"
    ),
    "agent-dev-backend-api": (
        "Use when building RESTful or FastAPI endpoints, request validation schemas, and service-layer handlers. 後端REST/FastAPI接口開發與驗證"
    ),
    "agent-hierarchical-coordinator": (
        "Use when decomposing large multi-module epics into queen-worker subagent task trees. 階層式多代理任務拆解與協調"
    ),
    "agent-implementer-sparc-coder": (
        "Use when translating SPARC specifications and pseudocode into verified production code. 依SPARC規格轉譯生產級程式碼"
    ),
    "agent-performance-optimizer": (
        "Use when profiling CPU/memory bottlenecks, latency spikes, and frontend/backend execution speed. 系統效能瓶頸剖析與延遲優化"
    ),
    "agent-planner": (
        "Use when breaking down ambiguous requirements into dependency-ordered milestones and implementation plans. 需求拆解與分步實作計畫規劃"
    ),
    "agent-release-manager": (
        "Use when preparing semantic versioning changelogs, release checklists, and rollback plans. 版本發布檢查清單與Changelog管理"
    ),
    "agent-tester": (
        "Use when designing unit, integration, and edge-case regression test suites for new changes. 單元與整合回歸測試設計"
    ),
    # --- GCP / BigQuery / AI Memory 等全域技能濃縮 (< 130 chars) ---
    "building-data-apps": (
        "Use when building React/Vite or Streamlit data dashboards and AI chat interfaces backed by BigQuery/GCP. 建立GCP/BigQuery數據儀表板應用"
    ),
    "notebook-guidance": (
        "Use when creating or executing Jupyter notebooks (.ipynb) for data exploration and %%bqsql BigQuery analysis. Jupyter Notebook資料分析與視覺化"
    ),
    "gcp-dataflow": (
        "Use when building, packaging, or debugging Apache Beam pipelines and Flex Templates on Dataflow. GCP Dataflow資料管線"
    ),
    "discovering-gcp-data-assets": (
        "Use when searching or inspecting BigQuery datasets/tables, BigLake catalogs, or Spanner schemas in Google Cloud. 探索GCP BigQuery資料集與Schema"
    ),
    "ml-best-practices": (
        "Use when performing machine learning (clustering, classification, regression, forecasting) or statistical analysis. 機器學習建模與統計數據分析最佳實踐"
    ),
    "gcp-pipeline-resource-provisioning": (
        "Use when declaratively provisioning BigQuery, Dataform, or Dataproc resources via deployment.yaml. GCP資料管線資源宣告式部署"
    ),
    "gcp-spark": (
        "Use when authoring or optimizing PySpark/Spark SQL workloads on Dataproc Serverless or Managed Spark clusters. GCP PySpark/Dataproc巨量資料處理"
    ),
    "gcp-spark-troubleshooting": (
        "Use when performing root-cause analysis on failed Dataproc/PySpark jobs and driver event logs in GCS. PySpark/Dataproc任務失敗除錯"
    ),
    "gcp-pipeline-orchestration": (
        "Use when generating or updating Cloud Composer (Airflow) DAG orchestration definitions for data pipelines. Cloud Composer資料管線排程編排"
    ),
    "gcp-data-pipelines": (
        "Use when choosing or architecting end-to-end Google Cloud data pipelines across dbt, Dataform, Beam, or Spark. GCP端到端資料管線架構選型"
    ),
    "bigquery-data-transfer-service": (
        "Use when inspecting or configuring BigQuery Data Transfer Service (DTS) ingestion pipelines. BigQuery DTS資料匯入管線設定"
    ),
    "bigquery-sql": (
        "Use when writing or optimizing BigQuery SQL queries to reduce slot contention and bytes scanned. BigQuery SQL查詢效能與成本優化"
    ),
    "data-autocleaning": (
        "Use when building automated data cleaning, deduplication, and schema normalization rules in BigQuery/Dataform. 自動化資料清洗與正規化"
    ),
    "dataform-bigquery": (
        "Use when authoring SQLX transformations, assertions, and workflow_settings.yaml in BigQuery Dataform. BigQuery Dataform SQLX轉換管線"
    ),
    "dbt-bigquery": (
        "Use when creating, testing, or optimizing dbt models and macros targeting BigQuery. BigQuery dbt模型開發與優化"
    ),
    "schema-mapping": (
        "Use when documenting source-to-target ETL schema mapping manifestos across 3+ database tables. 跨資料表ETL Schema映射清單設計"
    ),
    "enforcing-resource-attribution": (
        "Use when running bq or gcloud CLI commands to attach mandatory cost-attribution labels safely. GCP CLI指令標籤與成本歸屬規範"
    ),
    "google-cloud-auth-verification": (
        "Use when verifying gcloud ADC credentials as Step 0 pre-flight check before touching BigQuery or GCS. GCP憑證與連線前置驗證"
    ),
    "agentic-rag": (
        "Use when implementing Agentic RAG pipelines with multi-step query rewriting, dynamic retrieval, and grounding checks. 動態檢索增強生成/Agentic RAG實作"
    ),
    "dispatching-parallel-agents": (
        "Use when splitting independent tasks across parallel Manager-Worker subagents to accelerate execution. 並行子代理分發與Manager-Worker協作"
    ),
    "subagent-driven-development": (
        "Use when executing multi-task implementation plans via isolated subagents with per-task code review. 子代理驅動之分步開發與審查"
    ),
    "swarm-orchestration": (
        "Use when coordinating 3+ file cross-module refactors using hierarchical multi-agent swarm topologies. 跨模組多檔案Swarm群體協作重構"
    ),
    "memory-management": (
        "Use when persisting or retrieving cross-session engineering patterns and decisions in AgentDB/hot-cache. 跨會話記憶檢索與經驗模式儲存"
    ),
    "agentdb-memory-patterns": (
        "Use when implementing persistent session and long-term vector memory patterns for stateful AI agents. AgentDB持久化記憶架構設計"
    ),
    "agentdb-learning": (
        "Use when configuring reinforcement learning plugins (Q-Learning, Actor-Critic) in AgentDB. AgentDB強化學習插件配置"
    ),
    "neural-training": (
        "Use when running SONA/MoE neural pattern consolidation and adaptive routing training. 神經模式訓練與自適應路由"
    ),
    "verification-quality": (
        "Use when running automated truth-scoring, post-implementation quality gates, and rollback checks. 交付品質驗證與自動回滾門禁"
    ),
    "awesome-antigravity": (
        "Use when looking up Antigravity IDE agent personas, mission templates, and troubleshooting patterns. Antigravity代理模板與排錯指南"
    ),
    "skill-repair": (
        "Use when diagnosing and repairing broken skill installations or manifest.json registrations. 修復損壞之Skill安裝與設定"
    ),
}

DEFAULT_GOTCHAS_BY_CATEGORY = {
    "storeasy": """## ⚠️ Gotchas (避坑指南)
- **雙軌資料表同步陷阱**：Storeasy 同時存在 `workdiv_orders` (`Order`) 與 `workdiv_quote_orders` (`QuoteOrder`)，更新狀態或退件原因時務必透過 `order_lifecycle_service` 同步雙表，禁止只改單邊。
- **單位「式/一式」防呆**：工程報價若單位為「式」或「一式」，必須標記 `unit_mismatch=True` 並阻斷跨單位直接均價比較（交由 JEV 適格性引擎判別）。
- **原生日期選擇器語系**：前端所有 `<input type="date" />` 必須加上 `lang="en"`，避免繁中瀏覽器出現 `yyyy/月/dd` 破版。
""",
    "seo": """## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
""",
    "frontend": """## ⚠️ Gotchas (避坑指南)
- **禁止廉價 AI 模板感 (Anti-Slop)**：避免過度使用無意義的紫藍漸層、千篇一律的三欄卡片與脫離業務語境的假數字。
- **日期與表單無障礙**：所有 `<input type="date" lang="en" />` 強制加註 `lang="en"`；互動按鈕需具備明確 `title` 或 `aria-label` 與鍵盤焦點狀態。
""",
    "general": """## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
""",
}


def pick_gotchas(skill_name: str) -> str:
    n = skill_name.lower()
    if any(k in n for k in ["storeasy", "mini-warehouse", "skp-to-cad", "fixer", "multi-agent", "stage-gate", "handoff"]):
        return DEFAULT_GOTCHAS_BY_CATEGORY["storeasy"]
    if any(k in n for k in ["seo", "keyword", "serp", "backlink", "link", "content", "meta-tags", "schema-markup", "geo-", "entity-", "rank-", "competit", "us3c", "skillorchestrator"]):
        return DEFAULT_GOTCHAS_BY_CATEGORY["seo"]
    if any(k in n for k in ["frontend", "ui", "ux", "impeccable", "taste", "react", "d3", "diagram", "web-"]):
        return DEFAULT_GOTCHAS_BY_CATEGORY["frontend"]
    return DEFAULT_GOTCHAS_BY_CATEGORY["general"]


def synthesize_fallback_description(name: str, old_desc: str) -> str:
    clean = re.sub(r"\s+", " ", old_desc).strip()
    if not re.search(r"use when|trigger|當使用者|適用於", clean, re.I):
        clean = f"Use when tasks involve {name.replace('-', ' ')}: {clean}"
    if len(clean) > 130:
        clean = clean[:127].rstrip(" ,;.") + "..."
    return clean


def optimize_skill_file(path: Path, backup_dict: dict[str, str]) -> dict[str, int]:
    raw_orig = path.read_text(encoding="utf-8", errors="ignore")
    if str(path) not in backup_dict:
        backup_dict[str(path)] = raw_orig

    raw_text = raw_orig.lstrip("\ufeff").replace("\r\n", "\n")
    dir_name = path.parent.name
    m = re.match(r"^---\s*\n(.*?)\n---[ \t]*\n?(.*)$", raw_text, re.S)
    if not m:
        # Handle files without frontmatter by wrapping them with standard frontmatter
        skill_name = dir_name
        body_text = raw_text
        fm_text = f"name: {skill_name}\ndescription: {skill_name}"
    else:
        fm_text, body_text = m.group(1), m.group(2)
        nm = re.search(r"^name:\s*(.+)$", fm_text, re.M)
        skill_name = nm.group(1).strip().strip("\"'") if nm else dir_name

    # Unify duplicate twin names so Antigravity deduplicates properly
    if dir_name == "humanizer" and skill_name == "humanizer-zh-tw":
        skill_name = "humanizer"

    # Choose curated concise description (<= 135 chars)
    new_desc = CURATED_DESCRIPTIONS.get(skill_name) or CURATED_DESCRIPTIONS.get(dir_name)
    if not new_desc:
        dm = re.search(
            r"^description:\s*(?:>-\s*\n|\|\s*\n|>\s*\n)?(.*?)(?=\n[a-zA-Z0-9_-]+:|\Z)",
            fm_text,
            re.M | re.S,
        )
        old_desc = dm.group(1).strip() if dm else ""
        new_desc = synthesize_fallback_description(skill_name, old_desc)

    # Rebuild clean YAML frontmatter (keep extra safe single-line keys like license if present)
    extra_fm_lines = []
    for line in fm_text.splitlines():
        if re.match(r"^(?:license|version|compatibility):", line.strip()):
            extra_fm_lines.append(line.strip())

    # Escape quotes in description if needed
    safe_desc = new_desc.replace('"', "'")
    new_fm_lines = [
        "---",
        f"name: {skill_name}",
        f'description: "{safe_desc}"',
        *extra_fm_lines,
        "---",
    ]

    # Progressive Disclosure: if total lines > 260, extract lines after line 150 into references/detailed-guide.md
    body_lines = body_text.splitlines()
    extracted_ref = False
    if len(body_lines) > 240:
        # Find a clean markdown section boundary around line 120..170
        split_idx = 140
        for i in range(110, min(180, len(body_lines))):
            if body_lines[i].startswith("## "):
                split_idx = i
                break

        kept_lines = body_lines[:split_idx]
        moved_lines = body_lines[split_idx:]

        ref_dir = path.parent / "references"
        ref_dir.mkdir(parents=True, exist_ok=True)
        ref_file = ref_dir / "detailed-guide.md"
        ref_header = f"# {skill_name} — Detailed Reference & Extended Examples\n\n"
        ref_file.write_text(ref_header + "\n".join(moved_lines) + "\n", encoding="utf-8")

        kept_lines.append("")
        kept_lines.append("## Progressive Disclosure References (On-Demand)")
        kept_lines.append(
            "- Detailed templates, extended examples, and deep-dive checklists have been moved to "
            "[references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. "
            "Load that file via `view_file` only when needed."
        )
        body_lines = kept_lines
        extracted_ref = True

    joined_body = "\n".join(body_lines).strip()

    # Ensure Gotchas section exists
    if not re.search(r"##\s*(?:⚠️\s*)?(?:Gotchas|避坑指南|Anti-Patterns|反模式)", joined_body, re.I):
        joined_body = joined_body + "\n\n" + pick_gotchas(skill_name).strip()

    final_text = "\n".join(new_fm_lines) + "\n\n" + joined_body + "\n"
    path.write_text(final_text, encoding="utf-8")
    return {
        "changed": 1,
        "extracted_ref": 1 if extracted_ref else 0,
        "new_desc_len": len(safe_desc),
        "new_body_lines": len(final_text.splitlines()),
    }


def sync_workspace_duplicate_dirs():
    """
    若 .agent/skills/<name>/SKILL.md 與 .agents/skills/<name>/SKILL.md 同時存在，
    以 .agents/skills/<name>/SKILL.md 為單一真相來源同步，確保不會因為內容或 name 不同而雙重載入。
    """
    dot_agents = WORKSPACE_ROOT / ".agents" / "skills"
    dot_agent = WORKSPACE_ROOT / ".agent" / "skills"
    synced = 0
    if dot_agents.exists() and dot_agent.exists():
        for p_agents in dot_agents.glob("*/SKILL.md"):
            dname = p_agents.parent.name
            p_agent = dot_agent / dname / "SKILL.md"
            if p_agent.exists():
                p_agent.write_text(p_agents.read_text(encoding="utf-8"), encoding="utf-8")
                synced += 1
    return synced


def main():
    backup_dict: dict[str, str] = {}
    total_changed = 0
    total_extracted = 0

    for root in SKILL_ROOTS:
        if not root.exists():
            continue
        for p_str in sorted(glob.glob(str(root / "*" / "SKILL.md"))):
            res = optimize_skill_file(Path(p_str), backup_dict)
            total_changed += res.get("changed", 0)
            total_extracted += res.get("extracted_ref", 0)

    synced = sync_workspace_duplicate_dirs()

    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_text(json.dumps(backup_dict, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "optimized_skill_files": total_changed,
                "progressive_disclosure_refs_extracted": total_extracted,
                "synced_workspace_twins": synced,
                "backup_saved": str(BACKUP_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
