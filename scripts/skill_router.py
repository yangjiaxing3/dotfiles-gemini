#!/usr/bin/env python3
"""
Deterministic Agent Skill Router & Linter (scripts/skill_router.py)

將「百級技能路由 (Skill Routing)」與「三層漸進式架構合規檢查 (Skill Linting)」
外包給確定性 Python 腳本，落實 Agent Skills 四大黃金工程法則：
1. Metadata (< 130 chars, Proactive Bias `Use when`, Why > MUST/NEVER, Contrastive boundary)
2. Progressive Disclosure (Metadata -> Concise Body < 300 lines -> On-demand references/scripts)
3. Deterministic Scripts + Gotchas section
4. Top-K Skill Routing for 90+ skills + 60/40 Train/Test Benchmark Evaluation

用法：
  python scripts/skill_router.py route "我要調整迷你倉主管分析圖，比較各分店實收租金"
  python scripts/skill_router.py lint
  python scripts/skill_router.py eval
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
HOME_DIR = Path.home()
LOCAL_DEFAULT_REPO = (
    HOME_DIR / "Documents" / "GitHub" / "Storeasyworkdivnew"
    if os.name == "nt"
    else SCRIPT_DIR.parent
)
# 若在任意專案或 Cursor Cloud Agent 容器下呼叫，優先掃描當前目錄 (cwd)，若無則回退至腳本所在專案或預設專案
CWD_PATH = Path.cwd()


def _has_skill_dir(base: Path) -> bool:
    for sub in (".cursor/skills", ".agents/skills", ".agent/skills"):
        try:
            if (base / sub).is_dir():
                return True
        except OSError:
            continue
    return False


if _has_skill_dir(CWD_PATH):
    WORKSPACE_ROOT = CWD_PATH
elif _has_skill_dir(SCRIPT_DIR.parent):
    WORKSPACE_ROOT = SCRIPT_DIR.parent
elif LOCAL_DEFAULT_REPO.exists():
    WORKSPACE_ROOT = LOCAL_DEFAULT_REPO
else:
    WORKSPACE_ROOT = CWD_PATH

DEFAULT_REPO = LOCAL_DEFAULT_REPO if LOCAL_DEFAULT_REPO.exists() else WORKSPACE_ROOT
GLOBAL_SKILLS_ROOT = HOME_DIR / ".gemini" / "config" / "skills"
CURSOR_USER_SKILLS_ROOT = HOME_DIR / ".cursor" / "skills"

US3C_REPO_NAMES = {
    "us3c-next",
    "711us3cwebsite",
    "msi_us3c_recycle",
    "us3cdriverapp",
    "us3cwebsite-env",
    "us3c_mvp",
    "usdwarrantynew",
    "beikeshop_v3_jx",
    "imcheck",
    "logistic_driver",
    "price_crawler",
    "yangbiz",
}

SHARED_REPO_NAMES = {
    "yolomono",
}

STOREASY_ONLY_SKILLS = {
    "storeasy-mini-warehouse-viz",
    "storeasy-channel-operations",
    "storeasy-seo-looping",
    "skp-to-cad-ministorage",
    "storeasy-location-migration",
}

US3C_ONLY_SKILLS = {
    "us3c-tradein-margin-pricing",
    "us3c-kiosk-driver-ops",
    "us3c-imcheck-device-qc",
    "us3c-swarm",
    "us3c-seo-loop",
    "skillorchestrator",
    "kiosk-image-optimizer",
    "social-listening-brief",
    "agent-reach",
    "sop-lesson",
    "seo-audit",
    "autojev",
    "autojev-completion-review",
    "autojev-model-router",
    "autojev-research-guard",
    "autojev-task-router",
    "autojev-tool-guard",
    "jev-typesafe",
    "jev",
    "typesafe-ai",
}

FIXED_CORE_SKILLS = ("ponytail", "security-audit", "bughunter")

BUGHUNTER_SKILLS_ROOT = HOME_DIR / "Documents" / "GitHub" / "Claude-BugHunter" / "skills"

DOCS_STYLE_EXTS = {".md", ".mdx", ".txt", ".rst"}
FRONTEND_EXTS = {".tsx", ".jsx", ".css", ".scss", ".html", ".vue", ".svelte"}
BACKEND_PYTHON_EXTS = {".py"}
BACKEND_CONFIG_EXTS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sql", ".sh", ".ps1"}
DATA_EXTS = {".xlsx", ".xlsm", ".csv", ".sql"}
MAX_EXCLUDED_NOISE = 25

FRONTEND_UI_SKILLS = {
    "stageshow",
    "impeccable",
    "design-taste-frontend",
    "frontend-design",
    "hallmark",
    "agency-design-ui-designer",
    "agency-design-ux-architect",
    "agency-engineering-frontend-developer",
    "emil-design-eng",
    "web-design-guidelines",
    "modern-web-guidance",
    "react-best-practices",
    "vercel-react-best-practices",
    "vercel-composition-patterns",
    "agency-testing-accessibility-auditor",
    "d3-data-visualization",
    "agent-desktop",
    "e2e",
    "webapp-testing",
    "parallel-debug-challenge",
}

SEO_COPY_SKILLS = {
    "seo",
    "seo-audit",
    "seo-page",
    "seo-schema",
    "seo-content",
    "seo-content-brief",
    "seo-content-writer",
    "seo-geo",
    "seo-technical",
    "seo-cluster",
    "seo-sxo",
    "seo-workflow-rules",
    "us3c-seo-loop",
    "storeasy-seo-looping",
    "on-page-seo-auditor",
    "technical-seo-checker",
    "content-quality-auditor",
    "content-refresher",
    "geo-content-optimizer",
    "entity-optimizer",
    "internal-linking-optimizer",
    "keyword-research",
    "keyword-clustering",
    "backlink-analyzer",
    "link-prospecting",
    "meta-tags-optimizer",
    "schema-markup-generator",
    "agency-marketing-seo-specialist",
    "agency-marketing-content-creator",
    "agency-marketing-data-seo-engineer",
    "agency-marketing-geo-aeo-specialist",
    "agency-marketing-growth-hacker",
    "agency-paid-media-creative-strategist",
    "agency-paid-media-tracking-specialist",
    "agency-taiwan-threads-strategist",
    "agency-taiwan-line-oa-operator",
    "agency-taiwan-ecommerce-operator",
    "agency-taiwan-b2b-sales-writer",
    "agency-taiwan-zh-hant-editor",
    "humanizer",
    "humanizer-zh-tw",
    "social-listening-brief",
}

# 角色正交白名單：僅限制具備明確職責邊界的核心工程/審查/規劃技能，確保 Planner 不誤拿實作、Executor 不誤拿審查
ROLE_SKILL_ALLOWLIST: dict[str, set[str]] = {
    "graphify": {"planner", "agent_0"},
    "writing-plans": {"planner", "refactor"},
    "agent-arch-system-design": {"planner"},
    "agency-engineering-backend-architect": {"planner"},
    "ponytail-audit": {"planner", "refactor"},
    "diagram-design": {"planner"},
    "sparc-methodology": {"planner"},
    "agent-planner": {"planner"},
    "ponytail-review": {"red_team", "decision", "refactor"},
    "stage-gate-review": {"red_team", "agent_0", "planner"},
    "agency-engineering-code-reviewer": {"red_team"},
    "agent-code-analyzer": {"red_team"},
    "agent-performance-optimizer": {"red_team", "executor", "executor_build"},
    "bughunter": {"red_team", "agent_0"},
    "security-audit": {"red_team", "agent_0", "executor", "executor_build", "decision", "planner", "refactor"},
    "ponytail": {"executor", "executor_build", "executor_verify", "refactor", "planner", "agent_0", "red_team", "decision"},
    "tdd-workflow": {"executor", "executor_verify", "refactor"},
    "fastapi-templates": {"executor", "executor_build", "refactor"},
    "agent-tester": {"executor", "executor_verify", "agent_0"},
    "agent-dev-backend-api": {"executor", "executor_build", "refactor"},
    "subagent-driven-development": {"executor", "executor_build", "refactor"},
    "agency-testing-api-tester": {"executor", "executor_verify", "red_team", "agent_0"},
    "verification-quality": {"executor", "executor_verify", "decision", "refactor"},
    "xlsx": {"agent_0", "planner", "red_team", "executor", "executor_build", "refactor"},
    "spreadsheet-reconciliation": {"agent_0", "planner", "red_team", "executor", "executor_build", "refactor", "decision"},
    "agency-data-consolidation-agent": {"planner", "executor", "executor_build", "refactor"},
    "eli5": {"refactor", "planner"},
    "accidental-data-loss-prevention": {"agent_0", "red_team", "executor", "executor_build"},
    "boundary-sentinel": {"agent_0"},
    "phase-0-boundary-sentinel": {"agent_0"},
    "ponytail-debt": {"agent_0", "refactor"},
}

ROLE_ALIAS_MAP: dict[str, str] = {
    "planner": "planner",
    "agent planner": "planner",
    "agent planner & re-planner": "planner",
    "executor_build": "executor_build",
    "c1": "executor_build",
    "phase c1": "executor_build",
    "executor_verify": "executor_verify",
    "c2": "executor_verify",
    "phase c2": "executor_verify",
    "executor": "executor",
    "agent executor": "executor",
    "agent executor & qa": "executor",
    "red_team": "red_team",
    "red-team": "red_team",
    "agent b": "red_team",
    "agent b red team": "red_team",
    "qa": "red_team",
    "agent_0": "agent_0",
    "agent 0": "agent_0",
    "agent 0 & e-spec": "agent_0",
    "spec": "agent_0",
    "refactor": "refactor",
    "agent c": "refactor",
    "agent d": "refactor",
    "agent c & d-refactor": "refactor",
    "decision": "decision",
    "agent decision": "decision",
}


def normalize_role_key(role: str | None) -> str | None:
    if not role:
        return None
    low = re.sub(r"\s*\([^)]*\)", "", role).strip().lower()
    if low in ROLE_ALIAS_MAP:
        return ROLE_ALIAS_MAP[low]
    for k, v in ROLE_ALIAS_MAP.items():
        if k in low:
            return v
    return low


def get_skill_allowed_roles(skill_name: str) -> set[str] | None:
    """回傳指定 skill 允許掛載的角色集合；若回傳 None 代表跨角色通用。"""
    key = skill_name.lower().strip()
    if key.startswith("hunt-"):
        return {"red_team", "agent_0"}
    return ROLE_SKILL_ALLOWLIST.get(key)


BUGHUNTER_RISK_RULES: list[dict[str, Any]] = [
    {
        "skill": "hunt-sqli",
        "keywords": ("sql", "sqlite", "select", "insert", "upsert", "db", "cursor", "execute", "orm", "query", "資料庫"),
        "file_patterns": (r"(db|repo|storage|store|sqlite|crawler|scraper|query)",),
        "diff_patterns": (r"\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\.execute\(|sqlite3",),
        "reason": "SQL / SQLite 查詢與資料寫入需檢查 SQL Injection 與參數化綁定",
    },
    {
        "skill": "hunt-auth-bypass",
        "keywords": ("auth", "login", "token", "session", "signature", "驗簽", "hmac", "webhook", "api key", "bearer", "middleware", "驗證"),
        "file_patterns": (r"(auth|login|webhook|middleware|security|session)",),
        "diff_patterns": (r"verify_signature|hmac|Authorization|X-Line-Signature|Depends\(",),
        "reason": "認證、Middleware 或 Webhook 驗簽路徑需檢查 Auth Bypass 與時序攻擊",
    },
    {
        "skill": "hunt-idor",
        "keywords": ("idor", "user_id", "tenant", "org_id", "owner", "權限", "越權", "他人", "訂單", "明細", "lookup"),
        "file_patterns": (r"(?:^|/)(?:api|routers?|endpoints?|orders?|quotes?|tickets?)(?:/|\.py$|$)",),
        "diff_patterns": (r"/(users|orders|quotes|items|records)/\{|\b(user_id|tenant_id|account_id)\b",),
        "reason": "API 資源識別與 ID 查詢需檢查 IDOR 越權存取防護",
    },
    {
        "skill": "hunt-business-logic",
        "keywords": ("計價", "報價", "估價", "折扣", "扣款", "上限", "下限", "價格", "金額", "毛利", "進位", "pricing", "quote", "discount", "margin", "formula", "calculator", "auto_quote"),
        "file_patterns": (r"(quote|pricing|calc|calculator|margin|discount|billing|invoice|templates)",),
        "diff_patterns": (r"min_floor|discount|deduction|max_price|cap|ratio|margin|round",),
        "reason": "報價、扣款與毛利計算邏輯需檢查負數金額、邊界繞過與進位誤差",
    },
    {
        "skill": "hunt-api-misconfig",
        "keywords": ("cors", "fastapi", "openapi", "swagger", "endpoint", "header", "rate limit", "limiter", "0.0.0.0", "config", "端點"),
        "file_patterns": (r"(?:^|/)(?:api|routers?|fastapi|endpoints?|app|main|config)(?:/|\.py$|$)",),
        "diff_patterns": (r"CORSMiddleware|allow_origins|APIRouter|FastAPI|rate_limit",),
        "reason": "FastAPI 路由、CORS、Rate Limit 與錯誤資訊揭露需檢查 API Misconfiguration",
    },
    {
        "skill": "hunt-exceptional-conditions",
        "keywords": ("exception", "error", "fallback", "retry", "catch", "fail-open", "except", "nan", "inf", "邊界異常", "例外"),
        "file_patterns": (r"(parser|service|client|worker|calculator|pipeline)",),
        "diff_patterns": (r"except\s+|try:|fallback|raise\s+",),
        "reason": "例外處理與 Fallback 路徑需檢查 Fail-Open 放行與 NaN/異常崩潰",
    },
    {
        "skill": "hunt-race-condition",
        "keywords": ("race", "concurrent", "async", "lock", "upsert", "idempotent", "併發", "競爭", "重複提交", "atomic", "transaction"),
        "file_patterns": (r"(worker|queue|sync|upsert|lock|transaction|job)",),
        "diff_patterns": (r"asyncio|threading|Lock|ON CONFLICT|BEGIN IMMEDIATE|concurrent",),
        "reason": "併發讀寫、非同步佇列與 Upsert 操作需防範 Race Condition / TOCTOU",
    },
    {
        "skill": "hunt-xss",
        "keywords": ("xss", "html", "svg", "dangerouslysetinnerhtml", "innerhtml", "script", "markdown", "render", "前端渲染"),
        "file_patterns": (r"(\.tsx$|\.jsx$|\.html$|\.vue$|frontend|components)",),
        "diff_patterns": (r"dangerouslySetInnerHTML|innerHTML|sanitize|<script|html\.escape",),
        "reason": "前端 DOM 與動態內容渲染需檢查 XSS 腳本注入風險",
    },
    {
        "skill": "hunt-csrf",
        "keywords": ("csrf", "cookie", "samesite", "form", "credentials", "跨域表單"),
        "file_patterns": (r"(cookie|session|auth|form)",),
        "diff_patterns": (r"set_cookie|SameSite|csrf|credentials:\s*['\"]include",),
        "reason": "Cookie Session 與狀態變更表單需檢查 CSRF 防護",
    },
    {
        "skill": "hunt-ssrf",
        "keywords": ("ssrf", "url", "fetch", "requests", "httpx", "curl", "crawler", "redirect", "proxy", "playwright", "爬蟲"),
        "file_patterns": (r"(crawler|scraper|fetch|http|client|proxy)",),
        "diff_patterns": (r"httpx\.|requests\.|urllib|aiohttp|fetch\(",),
        "reason": "爬蟲與外部 URL 抓取需防範 SSRF（阻擋內網 IP 與 Metadata 端點）",
    },
    {
        "skill": "hunt-lfi",
        "keywords": ("path", "read_file", "pathlib", "traversal", "lfi", "download", "export", "zip", "路徑穿越"),
        "file_patterns": (r"(file|export|import|download|storage|io|loader)",),
        "diff_patterns": (r"Path\(|open\(|send_file|FileResponse|\.\./",),
        "reason": "動態路徑讀檔與匯出功能需防範 Path Traversal / LFI 越界讀取",
    },
    {
        "skill": "hunt-file-upload",
        "keywords": ("upload", "multipart", "xlsm", "xlsx", "pdf", "mime", "上傳", "附件"),
        "file_patterns": (r"(upload|media|image|import|attachment)",),
        "diff_patterns": (r"UploadFile|multipart|filename|content_type",),
        "reason": "檔案上傳與樣板匯入需檢查副檔名白名單、MIME 驗證與大小上限",
    },
    {
        "skill": "hunt-jwt-crypto",
        "keywords": ("jwt", "crypto", "encrypt", "decrypt", "dpapi", "secret", "hash", "sha256", "aes", "金鑰"),
        "file_patterns": (r"(secret|crypto|token|jwt|security|key)",),
        "diff_patterns": (r"jwt|CryptProtectData|sha256|Fernet|AES",),
        "reason": "JWT、雜湊與機密憑證儲存需檢查弱演算法與金鑰安全邊界",
    },
    {
        "skill": "hunt-oauth",
        "keywords": ("oauth", "oidc", "sso", "pkce", "redirect_uri", "client_secret"),
        "file_patterns": (r"(oauth|sso|oidc)",),
        "diff_patterns": (r"redirect_uri|code_verifier|oauth|client_secret",),
        "reason": "OAuth / SSO 授權回呼流程需檢查 redirect_uri 嚴格比對與 state 校驗",
    },
    {
        "skill": "hunt-llm-ai",
        "keywords": ("llm", "prompt", "agent", "mcp", "rag", "openai", "gemini", "qwen", "grok", "injection", "line oa", "客服"),
        "file_patterns": (r"(agent|prompt|llm|ai|mcp|router|gate|line_oa)",),
        "diff_patterns": (r"system_prompt|user_prompt|chat/completions|generateContent",),
        "reason": "LLM / Agent 系統提示與外部輸入需防範 Prompt Injection 與過度工具權限",
    },
]


def detect_workspace_family(workspace_root: Path | None = None) -> str:
    root = workspace_root or WORKSPACE_ROOT
    name_low = root.name.lower()
    if name_low in SHARED_REPO_NAMES:
        return "shared"
    if (
        name_low in US3C_REPO_NAMES
        or "us3c" in name_low
        or "imcheck" in name_low
        or "beikeshop" in name_low
        or "warranty" in name_low
    ):
        return "us3c"
    return "storeasy"


def build_skill_roots(workspace_root: Path) -> list[tuple[str, Path]]:
    """依 Antigravity 與 Cursor Cloud Agents 優先序 (.agents -> .agent -> .cursor -> global -> cursor_user) 組出指定工作區的 Skill 掃描根目錄。"""
    roots: list[tuple[str, Path]] = []
    for label, p in (
        ("workspace_.agents", workspace_root / ".agents" / "skills"),
        ("workspace_.agent", workspace_root / ".agent" / "skills"),
        ("workspace_.cursor", workspace_root / ".cursor" / "skills"),
        ("global_config", GLOBAL_SKILLS_ROOT),
        ("cursor_user", CURSOR_USER_SKILLS_ROOT),
    ):
        try:
            if p.is_dir():
                roots.append((label, p))
        except OSError:
            continue
    return roots


# NOTE: route / lint 反映「當前所在專案」，因此依 cwd 決定工作區
SKILL_ROOTS = build_skill_roots(WORKSPACE_ROOT)
# NOTE: eval 資料集在本機綁定 DEFAULT_REPO，在雲端 Cursor Cloud Agent 容器則自動對齊當前 WORKSPACE_ROOT
EVAL_SKILL_ROOTS = build_skill_roots(DEFAULT_REPO)
EVAL_DATASET_PATH = (
    SCRIPT_DIR / "skill_eval_dataset.json"
    if (SCRIPT_DIR / "skill_eval_dataset.json").exists()
    else DEFAULT_REPO / "scripts" / "skill_eval_dataset.json"
)

# 雙語領域意圖同義詞擴充表（將確定性語意映射外包給腳本，避免 LLM 在中英夾雜時漏判）
INTENT_SYNONYMS: dict[str, list[str]] = {
    "多 agent": ["multi-agent-mode", "swarm", "orchestrator", "辯證", "紅隊", "red team"],
    "多代理": ["multi-agent-mode", "skillorchestrator", "swarm"],
    "紅隊": ["multi-agent-mode", "red team", "skeptical", "批判"],
    "fixer": ["fixer-prompt", "死循環", "連續失敗", "從零診斷", "修不好"],
    "修不好": ["fixer-prompt", "deadloop", "debug"],
    "死循環": ["fixer-prompt", "loop"],
    "架構": ["graphify", "backend-architect", "system-design", "codebase-onboarding"],
    "節點": ["graphify", "knowledge graph", "graph.json"],
    "關聯": ["graphify", "shortest_path", "query_graph"],
    "迷你倉": ["storeasy-mini-warehouse-viz", "skp-to-cad-ministorage", "storeasy-seo-looping"],
    "主管分析圖": ["storeasy-mini-warehouse-viz", "d3-data-visualization"],
    "每材實收": ["storeasy-mini-warehouse-viz", "已出租材積", "實收租金"],
    "ai 生成痕跡": ["humanizer", "humanizer-zh-tw", "破折號", "三段式"],
    "真人寫": ["humanizer", "humanizer-zh-tw"],
    "handoff": ["session-handoff", "SESSION-HANDOFF.md", "wrap up", "保存進度"],
    "結束": ["session-handoff", "wrap up"],
    "stage-gate": ["stage-gate-review", "階段審查", "skeptical review"],
    "程式碼審查": ["stage-gate-review", "agency-engineering-code-reviewer", "github-code-review"],
    "channel manager": ["storeasy-channel-operations", "促銷", "發布", "官網"],
    "促銷": ["storeasy-channel-operations", "campaigns", "promotions"],
    "二手回收": ["skillorchestrator", "us3c-seo-loop", "kiosk-image-optimizer"],
    "二手手機": ["us3c-seo-loop", "us3c-tradein-margin-pricing", "skillorchestrator", "seo-audit"],
    "手機回收": ["us3c-seo-loop", "agent-reach", "us3c-kiosk-driver-ops", "skillorchestrator"],
    "保固": ["us3c-seo-loop", "us3c-imcheck-device-qc", "seo-schema"],
    "商品頁": ["us3c-seo-loop", "seo-page", "seo-schema", "on-page-seo-auditor"],
    "swarm": ["skillorchestrator", "swarm-orchestration", "multi-agent-mode"],
    "排名掉了": ["on-page-seo-auditor", "content-refresher", "alert-manager"],
    "單頁": ["on-page-seo-auditor", "seo-audit"],
    "孤島頁面": ["internal-linking-optimizer", "orphan pages", "內鏈"],
    "站內連結": ["internal-linking-optimizer", "internal linking"],
    "fastapi": ["fastapi-templates", "agency-engineering-backend-architect", "agent-dev-backend-api"],
    "後端": ["agency-engineering-backend-architect", "fastapi-templates", "agent-dev-backend-api"],
    "sql": ["agency-engineering-database-optimizer", "bigquery-sql", "accidental-data-loss-prevention"],
    "索引": ["agency-engineering-database-optimizer", "index", "schema"],
    "跑太慢": ["agency-engineering-database-optimizer", "agent-performance-optimizer"],
    "美化": ["stageshow", "impeccable", "design-taste-frontend", "frontend-design", "agency-design-ui-designer"],
    "dashboard": ["stageshow", "impeccable", "frontend-design"],
    "動態 ui": ["stageshow", "impeccable", "design-taste-frontend", "emil-design-eng", "frontend-design"],
    "動態ui": ["stageshow", "impeccable", "design-taste-frontend", "emil-design-eng", "frontend-design"],
    "原件": ["stageshow", "impeccable", "design-taste-frontend", "emil-design-eng"],
    "元件": ["stageshow", "impeccable", "design-taste-frontend", "agency-engineering-frontend-developer"],
    "動畫": ["stageshow", "emil-design-eng", "impeccable", "design-taste-frontend"],
    "bento": ["stageshow", "impeccable", "design-taste-frontend", "frontend-design"],
    "stageshow": ["stageshow", "impeccable", "design-taste-frontend", "emil-design-eng"],
    "impeccable": ["impeccable", "stageshow", "design-taste-frontend"],
    "taste": ["design-taste-frontend", "stageshow", "impeccable"],
    "drop table": ["accidental-data-loss-prevention", "delete", "truncate", "防誤刪"],
    "刪除資料表": ["accidental-data-loss-prevention"],
    "playwright": ["webapp-testing", "browser-act", "agent-desktop"],
    "e2e": ["agent-desktop", "e2e", "webapp-testing", "browser-act"],
    "agent-desktop": ["agent-desktop", "agent-browser", "snapshot", "結構化e2e"],
    "agent-browser": ["agent-desktop", "browser-act", "snapshot"],
    "ponytail": ["ponytail", "ponytail-review", "ponytail-audit", "ponytail-debt", "精簡程式碼", "反過度工程"],
    "簡化": ["ponytail", "ponytail-audit", "ponytail-review", "agency-engineering-minimal-change-engineer"],
    "精簡": ["ponytail", "ponytail-audit", "ponytail-review"],
    "過度工程": ["ponytail", "ponytail-review", "ponytail-audit", "yagni"],
    "yagni": ["ponytail", "ponytail-review", "ponytail-audit"],
    "死碼": ["ponytail-audit", "ponytail-review", "ponytail"],
    "shortcut": ["ponytail-debt", "ponytail"],
    "截圖": ["webapp-testing", "browser-act", "agent-desktop"],
    "webp": ["kiosk-image-optimizer", "縮圖", "壓縮"],
    "回收機": ["kiosk-image-optimizer", "us3c-seo-loop"],
    "json-ld": ["schema-markup-generator", "faq", "localbusiness", "結構化資料"],
    "結構化資料": ["schema-markup-generator"],
    "chatgpt": ["geo-content-optimizer", "entity-optimizer", "perplexity", "ai overviews", "引用"],
    "perplexity": ["geo-content-optimizer", "ai citations"],
    "sketchup": ["skp-to-cad-ministorage", ".skp", "cad", "dxf", "dwg"],
    "excel": ["xlsx", ".xlsx", "試算表", "公式"],
    "mcp": ["mcp-builder", "fastmcp", "model context protocol"],
    "wcag": ["agency-testing-accessibility-auditor", "無障礙", "螢幕閱讀器", "accessibility"],
    "無障礙": ["agency-testing-accessibility-auditor", "web-design-guidelines"],
    "compound components": ["vercel-composition-patterns", "composition-patterns", "boolean props"],
    "react 19": ["vercel-composition-patterns", "react-best-practices"],
    "inngest": ["workflow-automation", "temporal", "n8n", "背景工作流"],
    "pdf": ["pdf", "表格提取", "合併"],
    "多據點": ["storeasy-seo-looping", "防禦性", "垃圾內容"],
    "實作計畫": ["writing-plans", "sparc-methodology", "agent-planner", "implementation plan"],
    "資安": ["security-audit", "sql injection", "path traversal", "漏洞"],
    "漏洞": ["security-audit"],
    "core web vitals": ["technical-seo-checker", "lcp", "cls", "robots.txt", "sitemap"],
    "decisions.md": ["decisions-governance", "docs/decisions", "adr", "決策"],
    "為什麼這樣改": ["decisions-governance", "decisions.md", "adr"],
    "架構決策": ["decisions-governance", "decisions.md", "adr"],
    "adr": ["decisions-governance", "decisions.md", "docs/decisions"],
    "threads": ["agency-taiwan-threads-strategist", "agency-marketing-content-creator", "社群"],
    "line oa": ["agency-taiwan-line-oa-operator", "官方帳號", "圖文選單", "分眾推播"],
    "官方帳號": ["agency-taiwan-line-oa-operator", "line oa"],
    "蝦皮": ["agency-taiwan-ecommerce-operator", "momo", "pchome", "shopline", "電商"],
    "momo": ["agency-taiwan-ecommerce-operator", "蝦皮", "電商"],
    "b2b": ["agency-taiwan-b2b-sales-writer", "陌生開發", "提案簡報"],
    "台灣用語": ["agency-taiwan-zh-hant-editor", "humanizer-zh-tw", "繁體中文", "支語"],
    "翻譯腔": ["agency-taiwan-zh-hant-editor", "humanizer-zh-tw"],
    "fp&a": ["agency-data-consolidation-agent", "agency-support-analytics-reporter", "預算", "差異分析"],
    "預算": ["agency-data-consolidation-agent", "agency-support-analytics-reporter", "fp&a"],
    "定價": ["agency-sales-data-extraction-agent", "storeasy-channel-operations", "敏感度", "毛利"],
    "估價": ["agency-sales-data-extraction-agent", "skillorchestrator", "二手回收"],
    "coo": ["agency-testing-workflow-optimizer", "agency-agents-orchestrator", "瓶頸", "營運"],
    "營運": ["agency-testing-workflow-optimizer", "agency-data-consolidation-agent", "storeasy-channel-operations"],
    "瓶頸": ["agency-testing-workflow-optimizer", "流程", "自動化"],
    "geo": ["agency-marketing-geo-aeo-specialist", "geo-content-optimizer", "entity-optimizer"],
    "aeo": ["agency-marketing-geo-aeo-specialist", "agency-marketing-data-seo-engineer"],
    "rsa": ["agency-paid-media-creative-strategist", "廣告文案", "搜尋詞"],
    "capi": ["agency-paid-media-tracking-specialist", "gtm", "ga4", "轉換追蹤"],
    "gtm": ["agency-paid-media-tracking-specialist", "ga4", "capi"],
    "收購上限": ["us3c-tradein-margin-pricing", "收購定價尺", "marginobsboard", "毛利觀測"],
    "收購定價尺": ["us3c-tradein-margin-pricing", "marginobsboard", "收購上限"],
    "毛利觀測": ["us3c-tradein-margin-pricing", "marginobsboard", "soldsnapshot", "收購定價尺"],
    "舊換新": ["us3c-tradein-margin-pricing", "tradeinsnapshot", "auto_quote", "計價"],
    "機台": ["us3c-kiosk-driver-ops", "kiosk-image-optimizer", "r3", "l1", "l2"],
    "異常單": ["us3c-kiosk-driver-ops", "us3cdriverapp", "l1", "l2", "l3", "l4"],
    "司機": ["us3c-kiosk-driver-ops", "us3cdriverapp", "patrol", "取貨"],
    "imcheck": ["us3c-imcheck-device-qc", "blacklist", "黑名單", "securaze", "驗機"],
    "黑名單": ["us3c-imcheck-device-qc", "imcheck", "blacklist"],
    "驗機": ["us3c-imcheck-device-qc", "sop-lesson", "securaze", "qc"],
    "bunnit": ["social-listening-brief", "agent-reach", "kiosk-image-optimizer"],
    "社群討論": ["agent-reach", "social-listening-brief", "socialintelfixture"],
    "旁註": ["sop-lesson", "標註配方", "callout"],
    "bughunter": ["bughunter", "security-audit", "紅隊", "漏洞"],
    "權限": ["security-audit", "bughunter", "rbac", "idor"],
    "webhook": ["security-audit", "bughunter", "驗簽", "hmac"],
    "計價": ["us3c-tradein-margin-pricing", "auto_quote", "扣款", "毛利"],
    "報價公式": ["us3c-tradein-margin-pricing", "auto_quote", "計價", "bughunter"],
    "xss": ["bughunter", "security-audit", "dangerouslysetinnerhtml"],
    "sql injection": ["bughunter", "security-audit", "agency-engineering-database-optimizer"],
    "ssrf": ["bughunter", "security-audit", "爬蟲", "url"],
    "path traversal": ["bughunter", "security-audit", "路徑穿越", "檔案上傳"],
    "prompt injection": ["bughunter", "security-audit", "llm", "系統提示詞"],
    "idor": ["bughunter", "security-audit", "越權"],
    "越權": ["bughunter", "security-audit", "權限"],
    "白名單": ["security-audit", "bughunter"],
    "附件上傳": ["bughunter", "security-audit", "upload"],
    "mime": ["bughunter", "security-audit"],
    "xlsm": ["xlsx", "spreadsheet-reconciliation", "agency-sales-data-extraction-agent"],
    "薪資明細": ["xlsx", "spreadsheet-reconciliation", "agency-data-consolidation-agent"],
    "對帳": ["spreadsheet-reconciliation", "xlsx", "agency-data-consolidation-agent"],
    "勾稽": ["spreadsheet-reconciliation", "xlsx"],
    "合併儲存格": ["xlsx", "spreadsheet-reconciliation"],
    "隱藏列": ["spreadsheet-reconciliation", "xlsx"],
    "差異分析": ["spreadsheet-reconciliation", "agency-data-consolidation-agent"],
    "flux": ["spreadsheet-reconciliation", "variance"],
    "reconciliation": ["spreadsheet-reconciliation", "cross-footing"],
    "跨表對帳": ["spreadsheet-reconciliation", "xlsx"],
    "傳票": ["spreadsheet-reconciliation", "xlsx"],
    "實收業績": ["agency-data-consolidation-agent", "storeasy-mini-warehouse-viz", "spreadsheet-reconciliation"],
    "白話": ["eli5", "humanizer-zh-tw"],
    "ai 副駕": ["eli5", "agency-data-consolidation-agent"],
}


def parse_skill_file(path: Path, source_layer: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff").replace("\r\n", "\n")
    lines = text.splitlines()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    name = path.parent.name
    desc = ""
    if m:
        fm = m.group(1)
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        if nm:
            name = nm.group(1).strip().strip("\"'")
        dm = re.search(
            r"^description:\s*(?:>-\s*\n|\|\s*\n|>\s*\n)?(.*?)(?=\n[a-zA-Z0-9_-]+:|\Z)",
            fm,
            re.M | re.S,
        )
        if dm:
            raw_desc = dm.group(1).strip().strip("\"'")
            desc = re.sub(r"\s+", " ", raw_desc)

    skill_dir = path.parent
    has_scripts = (skill_dir / "scripts").is_dir()
    has_refs = (skill_dir / "references").is_dir()
    has_gotchas = bool(re.search(r"##\s*(?:⚠️\s*)?(?:Gotchas|避坑指南|Anti-Patterns|反模式)", text, re.I))
    has_use_when = bool(re.search(r"use when|use for|trigger|當使用者|適用於|use proactively|use this", desc, re.I))
    has_contrastive = bool(re.search(r"not for|do not use|don't use|skip when|非用於|不適用於", desc, re.I))
    must_count = len(re.findall(r"\b(?:MUST|ALWAYS|NEVER)\b", text))

    # Extract headings and trigger section for secondary indexing
    headings = " ".join(re.findall(r"^#+\s+(.+)$", text, re.M))
    skip_section_m = re.search(
        r"##\s*(?:⚠️\s*)?(?:When to Skip|Do Not Use|Non-Goals|Exclusion|不適用|何時跳過)[^\n]*\n(.*?)(?=\n##\s|\Z)",
        text,
        re.S | re.I,
    )
    skip_parts: list[str] = []
    if skip_section_m:
        skip_parts.append(skip_section_m.group(1).strip()[:400])
    desc_skip_m = re.search(
        r"(?:not for|do not use|don't use|skip when|非用於|不適用於)\s*([^.;\n]+)",
        desc,
        re.I,
    )
    if desc_skip_m:
        skip_parts.append(desc_skip_m.group(1).strip())
    skip_text = " ".join(skip_parts).lower()

    return {
        "name": name,
        "dir_name": path.parent.name,
        "source_layer": source_layer,
        "path": str(path),
        "description": desc,
        "desc_len": len(desc),
        "body_lines": len(lines),
        "has_scripts": has_scripts,
        "has_refs": has_refs,
        "has_gotchas": has_gotchas,
        "has_use_when": has_use_when,
        "has_contrastive": has_contrastive,
        "must_count": must_count,
        "headings": headings,
        "skip_text": skip_text,
    }


def extract_files_from_diff(diff_text: str) -> list[str]:
    """從 unified git diff 中擷取異動檔案路徑（去重且保留順序）。"""
    if not diff_text:
        return []
    files: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        candidate = ""
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                candidate = parts[3]
        elif line.startswith("+++ "):
            candidate = line[4:].strip()
        if not candidate or candidate == "/dev/null":
            continue
        if candidate.startswith(("a/", "b/")):
            candidate = candidate[2:]
        if candidate not in seen:
            seen.add(candidate)
            files.append(candidate)
    return files


def infer_file_signals(changed_files: list[str] | None) -> dict[str, Any]:
    """依據異動檔案路徑與副檔名推論架構邊界與強化詞彙訊號（50% 檔案權重來源）。"""
    cleaned = [f.strip().replace("\\", "/") for f in (changed_files or []) if f and f.strip()]
    if not cleaned:
        return {
            "files": [],
            "exts": [],
            "is_docs_only": False,
            "has_frontend": False,
            "has_backend_python": False,
            "is_pure_backend_python": False,
            "has_code_without_frontend": False,
            "has_tests": False,
            "has_data": False,
            "has_security_surface": False,
            "domain_hints": [],
            "boost_skills": {},
            "signal_tokens": [],
        }

    exts = sorted({Path(f).suffix.lower() for f in cleaned if Path(f).suffix})
    low_paths = [f.lower() for f in cleaned]

    is_docs_only = all(Path(f).suffix.lower() in DOCS_STYLE_EXTS for f in cleaned)
    has_frontend = any(
        Path(f).suffix.lower() in FRONTEND_EXTS
        or any(seg in f for seg in ("/frontend/", "/components/", "/pages/", "/src/app/", "/views/"))
        for f in low_paths
    )
    has_backend_python = any(Path(f).suffix.lower() in BACKEND_PYTHON_EXTS for f in cleaned)
    has_code_without_frontend = bool(cleaned) and has_backend_python and not has_frontend
    is_pure_backend_python = (
        bool(cleaned)
        and has_backend_python
        and all(Path(f).suffix.lower() in (BACKEND_PYTHON_EXTS | BACKEND_CONFIG_EXTS) for f in cleaned)
        and not has_frontend
    )
    has_tests = any(
        "tests/" in f or "/test_" in f or f.startswith("test_") or ".test." in f or ".spec." in f
        for f in low_paths
    )
    has_data = any(
        Path(f).suffix.lower() in DATA_EXTS
        or any(k in f for k in ("sqlite", ".db", "excel", "xlsm", "xlsx", "payroll", "executive_analytics", "store_performance", "reconcil"))
        for f in low_paths
    )
    has_security_surface = any(
        re.search(r"(api|router|auth|webhook|secret|gate|quote|calc|pricing|db|storage|crawler|scraper)", f)
        for f in low_paths
    )

    domain_hints: list[str] = []
    boost_skills: dict[str, float] = {}
    signal_tokens: list[str] = []

    def _add_boost(skill: str, weight: float) -> None:
        boost_skills[skill] = max(boost_skills.get(skill, 0.0), weight)

    if has_backend_python:
        domain_hints.append("backend_api")
        signal_tokens.extend(["python"])
        _add_boost("ponytail", 8.0)

    if any(re.search(r"(api/|routers/|endpoint|fastapi|webhook)", f) for f in low_paths):
        domain_hints.append("backend_api")
        signal_tokens.extend(["fastapi", "api", "endpoint", "後端"])
        _add_boost("fastapi-templates", 11.0)
        _add_boost("agency-testing-api-tester", 10.0)
        _add_boost("security-audit", 9.0)
        _add_boost("bughunter", 9.0)

    if any(re.search(r"(pricing|calc|calculator|margin|templates\.py)", f) for f in low_paths):
        domain_hints.append("data_analysis")
        signal_tokens.extend(["計價", "毛利", "收購定價尺"])
        _add_boost("us3c-tradein-margin-pricing", 14.0)
        _add_boost("ponytail", 8.0)

    if any(re.search(r"(upload|importer)", f) for f in low_paths):
        signal_tokens.extend(["upload", "xlsx", "security"])
        _add_boost("security-audit", 12.0)
        _add_boost("bughunter", 12.0)
        _add_boost("xlsx", 9.0)

    if any(re.search(r"(crawler|scraper|http_client)", f) for f in low_paths):
        signal_tokens.extend(["security", "ssrf"])
        _add_boost("security-audit", 12.0)
        _add_boost("bughunter", 12.0)

    if any(re.search(r"(auth|middleware|security|gate|line_oa/agent)", f) for f in low_paths):
        signal_tokens.extend(["security", "bughunter", "auth"])
        _add_boost("security-audit", 11.0)
        _add_boost("bughunter", 11.0)

    if any(re.search(r"(db|sqlite|storage|repository)", f) for f in low_paths):
        signal_tokens.extend(["sql", "sqlite", "資料庫"])
        _add_boost("agency-engineering-database-optimizer", 10.0)
        _add_boost("security-audit", 8.0)

    if has_tests:
        domain_hints.append("debug")
        signal_tokens.extend(["pytest", "test", "tdd"])
        _add_boost("tdd-workflow", 11.0)
        _add_boost("agent-tester", 10.0)
        _add_boost("verification-quality", 8.0)

    if has_frontend:
        domain_hints.append("ui_frontend")
        signal_tokens.extend(["ui", "react", "frontend", "css", "介面"])
        _add_boost("modern-web-guidance", 10.0)
        _add_boost("web-design-guidelines", 10.0)
        _add_boost("impeccable", 9.0)
        _add_boost("react-best-practices", 9.0)

    if has_data:
        domain_hints.append("data_analysis")
        signal_tokens.extend(["excel", "xlsx", "數據", "報表", "對帳", "勾稽"])
        _add_boost("xlsx", 9.0)
        _add_boost("spreadsheet-reconciliation", 10.0)
        _add_boost("agency-data-consolidation-agent", 7.0)

    if is_docs_only:
        signal_tokens.extend(["文件", "架構", "決策"])
        _add_boost("decisions-governance", 8.0)
        _add_boost("diagram-design", 8.0)

    # Deduplicate domain_hints keeping order
    dedup_domains: list[str] = []
    for d in domain_hints:
        if d not in dedup_domains:
            dedup_domains.append(d)

    return {
        "files": cleaned,
        "exts": exts,
        "is_docs_only": is_docs_only,
        "has_frontend": has_frontend,
        "has_backend_python": has_backend_python,
        "has_code_without_frontend": has_code_without_frontend,
        "is_pure_backend_python": is_pure_backend_python,
        "has_tests": has_tests,
        "has_data": has_data,
        "has_security_surface": has_security_surface,
        "domain_hints": dedup_domains,
        "boost_skills": boost_skills,
        "signal_tokens": signal_tokens,
    }


def select_bughunter_skills(
    query: str = "",
    changed_files: list[str] | None = None,
    diff_text: str = "",
    max_skills: int = 2,
) -> list[dict[str, Any]]:
    """
    依 Prompt、異動檔案路徑與 Diff 風險特徵，從外部 Claude-BugHunter Vault 動態挑選 1~2 個最對題 hunt-* 技能。
    只回傳路徑與風險理由，不複製任何 Vault 檔案進專案或全域庫。
    """
    merged_files = list(changed_files or [])
    for df in extract_files_from_diff(diff_text):
        if df not in merged_files:
            merged_files.append(df)

    file_signals = infer_file_signals(merged_files)
    q_low = (query or "").lower()
    explicit_security_q = bool(
        re.search(r"security|bughunter|xss|sqli|sql injection|idor|ssrf|csrf|lfi|驗簽|漏洞|資安|越權", q_low)
    )

    if file_signals["is_docs_only"] and not explicit_security_q:
        return []

    files_joined = "\n".join(merged_files).lower()
    scored: list[tuple[float, int, dict[str, Any], list[str]]] = []

    for rule in BUGHUNTER_RISK_RULES:
        score = 0.0
        file_hits = 0
        matched_signals: list[str] = []

        kw_hits = [kw for kw in rule["keywords"] if kw in q_low]
        if kw_hits:
            score += min(9.0, len(kw_hits) * 3.0)
            matched_signals.append("query:" + ",".join(kw_hits[:3]))

        for pat in rule["file_patterns"]:
            if files_joined and re.search(pat, files_joined, re.I):
                score += 4.5
                file_hits += 1
                matched_signals.append(f"file:{pat}")
                break

        if diff_text:
            for pat in rule["diff_patterns"]:
                if re.search(pat, diff_text, re.I):
                    score += 3.5
                    matched_signals.append(f"diff:{pat}")
                    break

        if score >= 3.0:
            scored.append((round(score, 2), file_hits, rule, matched_signals))

    scored.sort(key=lambda item: (-item[0], -item[1], item[2]["skill"]))
    vault_root = BUGHUNTER_SKILLS_ROOT.resolve()
    selected: list[dict[str, Any]] = []
    for score, _fh, rule, signals in scored[: max(0, max_skills)]:
        skill_md = (BUGHUNTER_SKILLS_ROOT / rule["skill"] / "SKILL.md").resolve()
        if not skill_md.is_relative_to(vault_root):
            continue
        checklist_summary = ""
        if skill_md.is_file():
            try:
                raw = skill_md.read_text(encoding="utf-8", errors="ignore")[:3000]
                body = re.sub(r"^---\s*\n.*?\n---\s*", "", raw, count=1, flags=re.S)
                bullets: list[str] = []
                for ln in body.splitlines():
                    st = ln.strip()
                    if not st or st.startswith(("#", "---", "```")):
                        continue
                    if st.startswith(("-", "*", "1.", "2.", "3.", "4.")) or len(st) >= 18:
                        clean = re.sub(r"\s+", " ", st.lstrip("-*0123456789. ")).strip()
                        if clean and clean not in bullets:
                            bullets.append(clean[:85])
                        if len(bullets) >= 3:
                            break
                checklist_summary = " | ".join(bullets)[:220]
            except OSError as exc:
                print(f"[skill_router] bughunter summary skipped: {exc}", file=sys.stderr)
        selected.append({
            "name": rule["skill"],
            "score": score,
            "reason": rule["reason"],
            "matched_signals": signals,
            "skill_path": str(skill_md),
            "exists_locally": skill_md.is_file(),
            "checklist_summary": checklist_summary,
        })
    return selected


def load_active_skills(
    deduplicate: bool = True,
    roots: list[tuple[str, Path]] | None = None,
    family_filter: bool = True,
) -> list[dict[str, Any]]:
    """依 Antigravity 優先序 (.agents -> .agent -> global) 載入 Skills；自動依產業家族 (storeasy vs us3c) 過濾跨行業技能。"""
    by_name: dict[str, dict[str, Any]] = {}
    skills: list[dict[str, Any]] = []
    family = detect_workspace_family(WORKSPACE_ROOT)
    excluded = (
        set()
        if family == "shared"
        else (STOREASY_ONLY_SKILLS if family == "us3c" else US3C_ONLY_SKILLS)
    )
    for layer_name, root in (roots if roots is not None else SKILL_ROOTS):
        if not root.exists():
            continue
        for p_str in sorted(glob.glob(str(root / "*" / "SKILL.md"))):
            p = Path(p_str)
            if p.parent.name.startswith("source-command-"):
                continue
            try:
                if getattr(p.parent, "is_junction", lambda: False)():
                    continue
            except OSError:
                pass
            item = parse_skill_file(p, layer_name)
            if family_filter and (item["name"] in excluded or item["dir_name"] in excluded):
                continue
            if deduplicate:
                cur = by_name.get(item["name"])
                if cur is not None:
                    if layer_name == "global_config":
                        cur_has_zh = bool(re.search(r"[\u4e00-\u9fff]", cur["description"]))
                        new_has_zh = bool(re.search(r"[\u4e00-\u9fff]", item["description"]))
                        new_is_clean = item["desc_len"] <= 160 and item["has_use_when"]
                        cur_is_bloated_or_old = (
                            (cur["desc_len"] > 180)
                            or (not cur["has_use_when"])
                            or (new_has_zh and not cur_has_zh)
                        )
                        if new_is_clean and cur_is_bloated_or_old:
                            cur["description"] = item["description"]
                            cur["desc_len"] = item["desc_len"]
                            cur["has_use_when"] = item["has_use_when"]
                            cur["has_contrastive"] = item["has_contrastive"]
                            cur["metadata_upgraded_from"] = "global_config"
                    continue
                by_name[item["name"]] = item
            skills.append(item)
    return skills


def tokenize(text: str) -> list[str]:
    text = text.lower()
    # English words / hyphenated terms + Chinese character bigrams & unigrams
    en_tokens = re.findall(r"[a-z0-9][a-z0-9._-]*", text)
    zh_chars = re.findall(r"[\u4e00-\u9fff]", text)
    zh_bigrams = [zh_chars[i] + zh_chars[i + 1] for i in range(len(zh_chars) - 1)]
    return en_tokens + zh_chars + zh_bigrams


class SkillRouter:
    """
    針對 50~150+ 個 Skills 的確定性輕量路由器：
    結合 BM25 (Name + Description 加權) 與雙語意圖同義詞擴充，
    在 10ms 內篩選出 Top-K 個最相關 Skills。
    """

    def __init__(self, skills: list[dict[str, Any]], use_synonyms: bool = True):
        self.skills = skills
        self.use_synonyms = use_synonyms
        self.docs: list[Counter[str]] = []
        self.doc_lens: list[int] = []
        self.df: Counter[str] = Counter()

        for s in skills:
            # Name tokens weight 4x, Description tokens weight 2x
            name_toks = tokenize(s["name"].replace("-", " ") + " " + s["dir_name"].replace("-", " ")) * 4
            desc_toks = tokenize(s["description"]) * 2
            doc_tokens = name_toks + desc_toks
            c = Counter(doc_tokens)
            self.docs.append(c)
            self.doc_lens.append(len(doc_tokens) or 1)
            for t in c.keys():
                self.df[t] += 1

        self.avgdl = sum(self.doc_lens) / max(1, len(self.doc_lens))
        self.N = len(skills)

    def route_with_diagnostics(
        self,
        query: str,
        top_k: int = 5,
        *,
        changed_files: list[str] | None = None,
        diff_text: str = "",
        role: str | None = None,
        min_score: float = 0.0,
        relative_cutoff: float = 0.0,
        apply_negative_guard: bool = True,
        include_bughunter: bool = True,
    ) -> dict[str, Any]:
        q_lower = query.lower()
        merged_files = list(changed_files or [])
        for df in extract_files_from_diff(diff_text):
            if df not in merged_files:
                merged_files.append(df)

        file_signals = infer_file_signals(merged_files)
        explicit_ui_or_seo = bool(
            re.search(
                r"(?:^|[^a-z])(ui|ux|css|tsx|jsx|react|frontend|html|seo|gsc|ga4|serp|sitemap|json-ld|blog|article|threads|bento)(?:$|[^a-z])|版面|按鈕|樣式|文案|社群|行銷|排版|商品頁|頁面",
                q_lower,
            )
        )
        pure_backend_query_hint = (
            bool(
                re.search(
                    r"(\.py\b|sqlite|upsert|fastapi|webhook|驗簽|計價公式|報價公式|sql injection|pytest|端點|cursor|資料庫)",
                    q_lower,
                )
            )
            and not explicit_ui_or_seo
        )

        expanded_parts = [query]
        boost_skill_names: set[str] = set()

        if self.use_synonyms:
            for key, syns in INTENT_SYNONYMS.items():
                if key in q_lower:
                    expanded_parts.extend(syns)
                    for syn in syns:
                        boost_skill_names.add(syn.lower())

        if file_signals["signal_tokens"]:
            expanded_parts.extend(file_signals["signal_tokens"])

        q_tokens = tokenize(" ".join(expanded_parts))
        q_counts = Counter(q_tokens)
        raw_q_tokens = {t for t in tokenize(query) if len(t) >= 2}
        norm_role = normalize_role_key(role)
        ws_family = detect_workspace_family(WORKSPACE_ROOT)

        k1 = 1.5
        b = 0.75
        has_file_context = bool(merged_files)
        intent_weight = 0.65 if has_file_context else 1.0
        scores: list[tuple[float, dict[str, Any]]] = []
        excluded_noise: list[dict[str, str]] = []

        for idx, s in enumerate(self.skills):
            s_name_l = s["name"].lower()
            s_dir_l = s["dir_name"].lower()
            explicit_named = (s_name_l in q_lower) or (s_dir_l in q_lower)

            # Layer 3a: Role-Scoped Orthogonal Filter
            if norm_role:
                allowed_roles = get_skill_allowed_roles(s["name"])
                if allowed_roles is not None and norm_role not in allowed_roles:
                    excluded_noise.append({"skill": s["name"], "reason": f"role_mismatch:{norm_role}"})
                    continue

            # Layer 2a: Negative Guard (純後端 / 混合後端程式碼 / 純文件情境阻擋跨領域噪音)
            if apply_negative_guard and not explicit_named:
                is_backend_ctx = (
                    file_signals["is_pure_backend_python"]
                    or file_signals.get("has_code_without_frontend", False)
                )
                if (is_backend_ctx and not explicit_ui_or_seo) or pure_backend_query_hint:
                    if s_name_l in FRONTEND_UI_SKILLS or s_name_l in SEO_COPY_SKILLS or s_name_l.startswith("seo-"):
                        excluded_noise.append({"skill": s["name"], "reason": "pure_backend_excludes_ui_seo"})
                        continue
                if s_name_l.startswith(("gcp-", "dbt-")):
                    q_and_files = q_lower + "\n" + "\n".join(merged_files).lower()
                    if not re.search(r"\b(?:gcp|bigquery|dbt|spark|dataflow|composer)\b", q_and_files):
                        excluded_noise.append({"skill": s["name"], "reason": "context_excludes_cloud_warehouse"})
                        continue
                if s_name_l == "kiosk-image-optimizer":
                    q_and_files = q_lower + "\n" + "\n".join(merged_files).lower()
                    if not re.search(r"\b(?:webp|image|kiosk)\b|縮圖|壓縮|圖片|門市圖", q_and_files):
                        excluded_noise.append({"skill": s["name"], "reason": "context_excludes_kiosk_image"})
                        continue
                if s_name_l == "spreadsheet-reconciliation":
                    q_and_files = q_lower + "\n" + "\n".join(merged_files).lower()
                    if not re.search(
                        r"\b(?:xlsx?|xlsm|csv|reconcil|flux|payroll)\b|對帳|勾稽|薪資|傳票|獎金|財務|試算表|隱藏列|小計|總帳",
                        q_and_files,
                    ):
                        excluded_noise.append({"skill": s["name"], "reason": "context_excludes_reconciliation"})
                        continue
                if file_signals["is_docs_only"] and not explicit_ui_or_seo:
                    if s_name_l in (FRONTEND_UI_SKILLS - {"diagram-design", "d3-data-visualization"}) or s_name_l in {"fastapi-templates", "tdd-workflow"}:
                        excluded_noise.append({"skill": s["name"], "reason": "docs_only_excludes_impl"})
                        continue

            doc = self.docs[idx]
            dl = self.doc_lens[idx]
            bm25_score = 0.0
            for t, qf in q_counts.items():
                if t not in doc:
                    continue
                df = self.df[t]
                idf = math.log(1.0 + (self.N - df + 0.5) / (df + 0.5))
                tf = doc[t]
                denom = tf + k1 * (1.0 - b + b * (dl / self.avgdl))
                bm25_score += idf * ((tf * (k1 + 1.0)) / denom) * (1.0 + 0.2 * min(qf, 3))

            score = bm25_score * intent_weight

            if explicit_named:
                score += 18.0
            if self.use_synonyms and (s_name_l in boost_skill_names or s_dir_l in boost_skill_names):
                score += 12.0 * intent_weight

            # Layer 1a: 50% File-Path Dominant Signal
            if has_file_context:
                file_boost = file_signals["boost_skills"].get(s_name_l) or file_signals["boost_skills"].get(s_dir_l) or 0.0
                score += file_boost * 1.25

            # Layer 1c: 15% Industry Family Bias (乘性放大且設底線，避免對低分無關技能灌水)
            if score >= 4.0:
                if ws_family == "us3c" and s_name_l.startswith("us3c-"):
                    score *= 1.12
                elif ws_family == "storeasy" and s_name_l.startswith("storeasy-"):
                    score *= 1.12

            # Penalty for overly bloated descriptions (> 250 chars; protect security-audit authoritative wording)
            if s["desc_len"] > 250 and s_name_l not in {"security-audit"}:
                score *= 0.85
            if not s["has_use_when"]:
                score *= 0.80

            # Layer 2b: "When to Skip / Not for" Contrastive Guard
            if apply_negative_guard and s.get("skip_text"):
                skip_tokens = {
                    t for t in tokenize(s["skip_text"])
                    if len(t) >= 3 and t not in {"not", "for", "use", "when", "with", "skip", "only"}
                }
                overlap = raw_q_tokens & skip_tokens
                if len(overlap) >= 2:
                    score *= 0.15
                    excluded_noise.append({
                        "skill": s["name"],
                        "reason": "when_to_skip_overlap:" + ",".join(sorted(overlap)[:3]),
                    })

            scores.append((round(score, 3), s))

        scores.sort(key=lambda x: -x[0])

        # Layer 3b: Precision Score Threshold & Relative Cutoff
        top_score = scores[0][0] if scores else 0.0
        filtered_scores: list[tuple[float, dict[str, Any]]] = []
        if (min_score > 0.0 or relative_cutoff > 0.0) and top_score <= 0.0:
            filtered_scores = []
        else:
            for sc, s in scores:
                if min_score > 0.0 and sc < min_score:
                    continue
                if relative_cutoff > 0.0 and top_score > 0.0 and sc < top_score * relative_cutoff:
                    continue
                filtered_scores.append((sc, s))

        results = []
        for sc, s in filtered_scores[:top_k]:
            results.append({
                "name": s["name"],
                "dir_name": s["dir_name"],
                "score": sc,
                "source_layer": s["source_layer"],
                "desc_len": s["desc_len"],
                "body_lines": s["body_lines"],
                "description": s["description"],
                "path": s["path"],
            })

        bh_allowed = include_bughunter and (norm_role in {None, "red_team", "agent_0"})
        bughunter_skills = (
            select_bughunter_skills(query, changed_files=merged_files, diff_text=diff_text, max_skills=2)
            if bh_allowed
            else []
        )

        return {
            "results": results,
            "file_signals": file_signals,
            "excluded_noise": excluded_noise[:MAX_EXCLUDED_NOISE],
            "bughunter": bughunter_skills,
        }

    def route(
        self,
        query: str,
        top_k: int = 5,
        *,
        changed_files: list[str] | None = None,
        diff_text: str = "",
        role: str | None = None,
        min_score: float = 0.0,
        relative_cutoff: float = 0.0,
        apply_negative_guard: bool = True,
    ) -> list[dict[str, Any]]:
        return self.route_with_diagnostics(
            query,
            top_k=top_k,
            changed_files=changed_files,
            diff_text=diff_text,
            role=role,
            min_score=min_score,
            relative_cutoff=relative_cutoff,
            apply_negative_guard=apply_negative_guard,
        )["results"]


def run_lint() -> dict[str, Any]:
    active = load_active_skills(deduplicate=True, family_filter=True)
    all_files = load_active_skills(deduplicate=False, family_filter=True)
    total_desc_chars = sum(s["desc_len"] for s in active)
    over_140_desc = [s for s in active if s["desc_len"] > 140]
    missing_use_when = [s for s in active if not s["has_use_when"]]
    over_300_body = [s for s in active if s["body_lines"] > 300]
    missing_gotchas_ws = [
        s for s in active if s["source_layer"].startswith("workspace") and not s["has_gotchas"]
    ]

    summary = {
        "workspace_family": detect_workspace_family(WORKSPACE_ROOT),
        "total_skill_files": len(all_files),
        "unique_active_skills": len(active),
        "duplicate_skill_files": len(all_files) - len(active),
        "total_active_desc_chars": total_desc_chars,
        "avg_desc_chars": round(total_desc_chars / max(1, len(active)), 1),
        "desc_over_140_count": len(over_140_desc),
        "missing_use_when_count": len(missing_use_when),
        "body_over_300_lines_count": len(over_300_body),
        "workspace_missing_gotchas_count": len(missing_gotchas_ws),
    }
    return summary


def run_eval(use_synonyms: bool = True, workspace_root: Path | None = None) -> dict[str, Any]:
    target_root = workspace_root.resolve() if workspace_root is not None else None
    eval_roots = build_skill_roots(target_root) if target_root is not None else EVAL_SKILL_ROOTS
    skills = load_active_skills(deduplicate=True, roots=eval_roots, family_filter=False)
    available_names = {s["name"].lower() for s in skills} | {s["dir_name"].lower() for s in skills}
    router = SkillRouter(skills, use_synonyms=use_synonyms)
    dataset = json.loads(EVAL_DATASET_PATH.read_text(encoding="utf-8"))
    queries = [
        q for q in dataset["queries"]
        if any(e.lower() in available_names for e in q["expected_skills"])
    ]

    metrics: dict[str, Any] = {
        "train": {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0, "selected_total": 0, "relevant_hits": 0},
        "test": {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0, "selected_total": 0, "relevant_hits": 0},
        "overall": {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0, "selected_total": 0, "relevant_hits": 0},
        "misses": [],
        "forbidden_eval": {"total": 0, "false_positive_count": 0, "false_positive_rate": 0.0, "misses": []},
        "bughunter_eval": {"total": 0, "passed": 0, "accuracy": None, "misses": []},
    }

    for q in queries:
        split = q["split"]
        changed_files = q.get("files")
        diff_text = q.get("diff", "")
        role = q.get("role")
        expected = {e.lower() for e in q["expected_skills"]}
        relevant = expected | {a.lower() for a in q.get("acceptable_skills", [])}

        top5 = router.route(
            q["query"],
            top_k=5,
            changed_files=changed_files,
            diff_text=diff_text,
            role=role,
        )
        trimmed = router.route(
            q["query"],
            top_k=3,
            changed_files=changed_files,
            diff_text=diff_text,
            role=role,
            min_score=4.5,
            relative_cutoff=0.55,
        ) or top5[:1]

        pred_names = []
        for r in top5:
            pred_names.append(r["name"].lower())
            pred_names.append(r["dir_name"].lower())

        top1_set = {top5[0]["name"].lower(), top5[0]["dir_name"].lower()} if top5 else set()
        top3_set = set()
        for r in top5[:3]:
            top3_set.add(r["name"].lower())
            top3_set.add(r["dir_name"].lower())
        top5_set = set(pred_names)

        h1 = bool(expected & top1_set)
        h3 = bool(expected & top3_set)
        h5 = bool(expected & top5_set)

        trim_hits = sum(
            1 for r in trimmed if (r["name"].lower() in relevant or r["dir_name"].lower() in relevant)
        )

        for bucket in (split, "overall"):
            metrics[bucket]["total"] += 1
            if h1:
                metrics[bucket]["hit_at_1"] += 1
            if h3:
                metrics[bucket]["hit_at_3"] += 1
            if h5:
                metrics[bucket]["hit_at_5"] += 1
            metrics[bucket]["selected_total"] += len(trimmed)
            metrics[bucket]["relevant_hits"] += trim_hits

        if not h3:
            metrics["misses"].append({
                "id": q["id"],
                "split": split,
                "query": q["query"],
                "expected": q["expected_skills"],
                "predicted_top3": [r["name"] for r in top5[:3]],
            })

        forbidden = {f.lower() for f in q.get("forbidden_skills", [])}
        if forbidden:
            metrics["forbidden_eval"]["total"] += 1
            fp_hits = sorted(forbidden & top3_set)
            if fp_hits:
                metrics["forbidden_eval"]["false_positive_count"] += 1
                metrics["forbidden_eval"]["misses"].append({
                    "id": q["id"],
                    "query": q["query"],
                    "forbidden_matched": fp_hits,
                    "predicted_top3": [r["name"] for r in top5[:3]],
                })

        if "expected_bughunter" in q:
            metrics["bughunter_eval"]["total"] += 1
            expected_bh = [b.lower() for b in q["expected_bughunter"]]
            pred_bh_items = select_bughunter_skills(
                q["query"],
                changed_files=changed_files,
                diff_text=diff_text,
                max_skills=2,
            )
            pred_bh = [x["name"].lower() for x in pred_bh_items]
            if not expected_bh:
                bh_ok = len(pred_bh) == 0
            else:
                bh_ok = bool(set(pred_bh) & set(expected_bh))
            if bh_ok:
                metrics["bughunter_eval"]["passed"] += 1
            else:
                metrics["bughunter_eval"]["misses"].append({
                    "id": q["id"],
                    "query": q["query"],
                    "expected_bughunter": q["expected_bughunter"],
                    "predicted_bughunter": pred_bh,
                })

    for bucket in ("train", "test", "overall"):
        tot = max(1, metrics[bucket]["total"])
        sel_tot = max(1, metrics[bucket]["selected_total"])
        metrics[bucket]["recall_at_1"] = round(metrics[bucket]["hit_at_1"] / tot * 100, 1)
        metrics[bucket]["recall_at_3"] = round(metrics[bucket]["hit_at_3"] / tot * 100, 1)
        metrics[bucket]["recall_at_5"] = round(metrics[bucket]["hit_at_5"] / tot * 100, 1)
        metrics[bucket]["precision_at_3"] = round(metrics[bucket]["relevant_hits"] / sel_tot * 100, 1)

    forb_tot = metrics["forbidden_eval"]["total"]
    metrics["forbidden_eval"]["false_positive_rate"] = (
        round(metrics["forbidden_eval"]["false_positive_count"] / forb_tot * 100, 1) if forb_tot else 0.0
    )
    bh_tot = metrics["bughunter_eval"]["total"]
    metrics["bughunter_eval"]["accuracy"] = (
        round(metrics["bughunter_eval"]["passed"] / bh_tot * 100, 1) if bh_tot else None
    )

    metrics["forbidden_false_positive_count"] = metrics["forbidden_eval"]["false_positive_count"]
    metrics["forbidden_false_positive_rate"] = metrics["forbidden_eval"]["false_positive_rate"]
    metrics["precision_at_3"] = metrics["overall"]["precision_at_3"]
    metrics["eval_workspace_root"] = str(target_root if target_root is not None else DEFAULT_REPO)
    metrics["eval_skill_count"] = len(skills)
    return metrics


def _read_git_diff_head() -> str:
    import subprocess
    try:
        cp = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
            check=False,
        )
        return cp.stdout or ""
    except Exception as exc:
        print(f"[skill_router] git diff skipped: {exc}", file=sys.stderr)
        return ""


def main():
    parser = argparse.ArgumentParser(description="Agent Skill Router & Benchmark Evaluator")
    sub = parser.add_subparsers(dest="cmd")

    p_route = sub.add_parser("route", help="Route a user prompt to Top-K skills")
    p_route.add_argument("query", type=str, help="User prompt")
    p_route.add_argument("--top-k", type=int, default=5)
    p_route.add_argument("--files", nargs="*", default=[], help="Changed file paths for path-weighted routing")
    p_route.add_argument("--git-diff", action="store_true", help="Include git diff HEAD files and hunks")
    p_route.add_argument("--role", type=str, default="", help="Target role (planner/executor/red_team/agent_0/refactor/decision)")
    p_route.add_argument("--min-score", type=float, default=0.0, help="Minimum score cutoff")
    p_route.add_argument("--relative-cutoff", type=float, default=0.0, help="Relative score cutoff against top1 (e.g. 0.55)")
    p_route.add_argument("--bughunter", action="store_true", help="Output full diagnostics including Claude-BugHunter hunt-* mapping")

    sub.add_parser("lint", help="Lint all workspace and global skills against Progressive Disclosure rules")

    p_eval = sub.add_parser("eval", help="Run 60/40 benchmark evaluation")
    p_eval.add_argument("--raw-desc-only", action="store_true", help="Disable synonym router to test raw description quality")
    p_eval.add_argument("--workspace", type=str, default="", help="Override workspace root for eval skill pool (e.g. .)")

    args = parser.parse_args()
    if args.cmd == "route":
        skills = load_active_skills(deduplicate=True)
        router = SkillRouter(skills, use_synonyms=True)
        diff_txt = _read_git_diff_head() if args.git_diff else ""
        if args.bughunter:
            diag = router.route_with_diagnostics(
                args.query,
                top_k=args.top_k,
                changed_files=args.files or None,
                diff_text=diff_txt,
                role=args.role or None,
                min_score=args.min_score,
                relative_cutoff=args.relative_cutoff,
            )
            print(json.dumps(diag, ensure_ascii=False, indent=2))
        else:
            res = router.route(
                args.query,
                top_k=args.top_k,
                changed_files=args.files or None,
                diff_text=diff_txt,
                role=args.role or None,
                min_score=args.min_score,
                relative_cutoff=args.relative_cutoff,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "lint":
        print(json.dumps(run_lint(), ensure_ascii=False, indent=2))
    elif args.cmd == "eval":
        ws_path = Path(args.workspace) if getattr(args, "workspace", "") else None
        print(json.dumps(run_eval(use_synonyms=not args.raw_desc_only, workspace_root=ws_path), ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
