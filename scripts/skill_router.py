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


def detect_workspace_family(workspace_root: Path | None = None) -> str:
    root = workspace_root or WORKSPACE_ROOT
    name_low = root.name.lower()
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
    "dashboard": ["stageshow", "impeccable", "frontend-design", "building-data-apps"],
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
    "react 19": ["vercel-composition-patterns", "vercel-react-best-practices"],
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
    "舊換新": ["us3c-tradein-margin-pricing", "tradeinsnapshot", "us3c-seo-loop", "skillorchestrator"],
    "機台": ["us3c-kiosk-driver-ops", "kiosk-image-optimizer", "r3", "l1", "l2"],
    "異常單": ["us3c-kiosk-driver-ops", "us3cdriverapp", "l1", "l2", "l3", "l4"],
    "司機": ["us3c-kiosk-driver-ops", "us3cdriverapp", "patrol", "取貨"],
    "imcheck": ["us3c-imcheck-device-qc", "blacklist", "黑名單", "securaze", "驗機"],
    "黑名單": ["us3c-imcheck-device-qc", "imcheck", "blacklist"],
    "驗機": ["us3c-imcheck-device-qc", "sop-lesson", "securaze", "qc"],
    "bunnit": ["social-listening-brief", "agent-reach", "kiosk-image-optimizer"],
    "社群討論": ["agent-reach", "social-listening-brief", "socialintelfixture"],
    "旁註": ["sop-lesson", "標註配方", "callout"],
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
    has_use_when = bool(re.search(r"use when|trigger|當使用者|適用於|use proactively|use this", desc, re.I))
    has_contrastive = bool(re.search(r"not for|do not use|don't use|skip when|非用於|不適用於", desc, re.I))
    must_count = len(re.findall(r"\b(?:MUST|ALWAYS|NEVER)\b", text))

    # Extract headings and trigger section for secondary indexing
    headings = " ".join(re.findall(r"^#+\s+(.+)$", text, re.M))

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
    }


def load_active_skills(
    deduplicate: bool = True,
    roots: list[tuple[str, Path]] | None = None,
    family_filter: bool = True,
) -> list[dict[str, Any]]:
    """依 Antigravity 優先序 (.agents -> .agent -> global) 載入 Skills；自動依產業家族 (storeasy vs us3c) 過濾跨行業技能。"""
    seen_names: set[str] = set()
    skills: list[dict[str, Any]] = []
    family = detect_workspace_family(WORKSPACE_ROOT)
    excluded = STOREASY_ONLY_SKILLS if family == "us3c" else US3C_ONLY_SKILLS
    for layer_name, root in (roots if roots is not None else SKILL_ROOTS):
        if not root.exists():
            continue
        for p_str in sorted(glob.glob(str(root / "*" / "SKILL.md"))):
            p = Path(p_str)
            if p.parent.name.startswith("source-command-"):
                continue
            try:
                if p.parent.is_junction():
                    continue
            except OSError:
                pass
            item = parse_skill_file(p, layer_name)
            if family_filter and (item["name"] in excluded or item["dir_name"] in excluded):
                continue
            if deduplicate:
                if item["name"] in seen_names:
                    continue
                seen_names.add(item["name"])
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

    def route(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        q_lower = query.lower()
        expanded_parts = [query]
        boost_skill_names: set[str] = set()

        if self.use_synonyms:
            for key, syns in INTENT_SYNONYMS.items():
                if key in q_lower:
                    expanded_parts.extend(syns)
                    for syn in syns:
                        boost_skill_names.add(syn.lower())

        q_tokens = tokenize(" ".join(expanded_parts))
        q_counts = Counter(q_tokens)

        k1 = 1.5
        b = 0.75
        scores: list[tuple[float, dict[str, Any]]] = []

        for idx, s in enumerate(self.skills):
            doc = self.docs[idx]
            dl = self.doc_lens[idx]
            score = 0.0
            for t, qf in q_counts.items():
                if t not in doc:
                    continue
                df = self.df[t]
                idf = math.log(1.0 + (self.N - df + 0.5) / (df + 0.5))
                tf = doc[t]
                denom = tf + k1 * (1.0 - b + b * (dl / self.avgdl))
                score += idf * ((tf * (k1 + 1.0)) / denom) * (1.0 + 0.2 * min(qf, 3))

            # Direct name / trigger phrase bonus in description
            s_name_l = s["name"].lower()
            s_dir_l = s["dir_name"].lower()
            if s_name_l in q_lower or s_dir_l in q_lower:
                score += 18.0
            if self.use_synonyms and (s_name_l in boost_skill_names or s_dir_l in boost_skill_names):
                score += 12.0

            # Penalty for overly bloated descriptions (> 250 chars) that dilute specificity
            if s["desc_len"] > 250:
                score *= 0.85
            # Penalty for missing "Use when / Trigger" proactive bias
            if not s["has_use_when"]:
                score *= 0.80

            scores.append((round(score, 3), s))

        scores.sort(key=lambda x: -x[0])
        results = []
        for sc, s in scores[:top_k]:
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
        return results


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


def run_eval(use_synonyms: bool = True) -> dict[str, Any]:
    skills = load_active_skills(deduplicate=True, roots=EVAL_SKILL_ROOTS, family_filter=False)
    available_names = {s["name"].lower() for s in skills} | {s["dir_name"].lower() for s in skills}
    router = SkillRouter(skills, use_synonyms=use_synonyms)
    dataset = json.loads(EVAL_DATASET_PATH.read_text(encoding="utf-8"))
    queries = [
        q for q in dataset["queries"]
        if any(e.lower() in available_names for e in q["expected_skills"])
    ]

    metrics = {
        "train": {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0},
        "test": {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0},
        "overall": {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "hit_at_5": 0},
        "misses": [],
    }

    for q in queries:
        split = q["split"]
        expected = {e.lower() for e in q["expected_skills"]}
        top5 = router.route(q["query"], top_k=5)
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

        for bucket in (split, "overall"):
            metrics[bucket]["total"] += 1
            if h1:
                metrics[bucket]["hit_at_1"] += 1
            if h3:
                metrics[bucket]["hit_at_3"] += 1
            if h5:
                metrics[bucket]["hit_at_5"] += 1

        if not h3:
            metrics["misses"].append({
                "id": q["id"],
                "split": split,
                "query": q["query"],
                "expected": q["expected_skills"],
                "predicted_top3": [r["name"] for r in top5[:3]],
            })

    for bucket in ("train", "test", "overall"):
        tot = max(1, metrics[bucket]["total"])
        metrics[bucket]["recall_at_1"] = round(metrics[bucket]["hit_at_1"] / tot * 100, 1)
        metrics[bucket]["recall_at_3"] = round(metrics[bucket]["hit_at_3"] / tot * 100, 1)
        metrics[bucket]["recall_at_5"] = round(metrics[bucket]["hit_at_5"] / tot * 100, 1)

    metrics["eval_workspace_root"] = str(DEFAULT_REPO)
    metrics["eval_skill_count"] = len(skills)
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Agent Skill Router & Benchmark Evaluator")
    sub = parser.add_subparsers(dest="cmd")

    p_route = sub.add_parser("route", help="Route a user prompt to Top-K skills")
    p_route.add_argument("query", type=str, help="User prompt")
    p_route.add_argument("--top-k", type=int, default=5)

    sub.add_parser("lint", help="Lint all workspace and global skills against Progressive Disclosure rules")

    p_eval = sub.add_parser("eval", help="Run 60/40 benchmark evaluation")
    p_eval.add_argument("--raw-desc-only", action="store_true", help="Disable synonym router to test raw description quality")

    args = parser.parse_args()
    if args.cmd == "route":
        skills = load_active_skills(deduplicate=True)
        router = SkillRouter(skills, use_synonyms=True)
        res = router.route(args.query, top_k=args.top_k)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "lint":
        print(json.dumps(run_lint(), ensure_ascii=False, indent=2))
    elif args.cmd == "eval":
        print(json.dumps(run_eval(use_synonyms=not args.raw_desc_only), ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
