#!/usr/bin/env python3
"""
將本地全域 Rules 與 Skills（含最新 Lean-Triad、Ponytail、雙產業感知 Role-Scoped 技能矩陣、確定性路由器）
依「產業家族 (Storeasy 迷你倉家族 vs US3C 二手 3C 家族)」一鍵分流同步至專案 Git 倉庫、Cursor Cloud Agents 結構與跨機 AgentStores。

解決痛點：
1. Cursor Cloud Agents 運行於雲端隔離 Linux 容器 (/workspace)，無法讀取本機 Windows 之
   `~/.gemini/` 或 NTFS Directory Junctions。
2. 跨電腦（`DESKTOP-N1NJDUH` vs `YangPC`）開啟同一 Conversation ID / 分支（如 `cursor/seo-loop-warranty-67e6`）時：
   - 自動將受管控 Skills 寫入專案 `.agents/skills/`、實體目錄 `.cursor/skills/`（消除 Windows 下失效之 `120000` Git symlink）與 `.cursor/commands/`。
   - 同步寫入本機 Cursor 雲端同步倉 `AppData/Local/Cursor/AgentStores/cursor_agent_stores/u*/files/skills`，讓同一 Cursor 帳號跨電腦自動互通。
3. 雙產業專屬隔離（Industry-Scoped Skill & Rule Partitioning）：
   - Storeasy 迷你倉家族僅安裝「通用底座 + Storeasy 專屬技能與規則」，絕不混入二手 3C 回收技能。
   - US3C 二手 3C 家族僅安裝「通用底座 + US3C 專屬技能與規則」，絕不混入迷你倉排櫃與每材實收技能，且保留專案既有客製技能（如 `seo-looping`、`openseo-*`）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

HOME = Path.home()
GLOBAL_SKILLS_DIR = HOME / ".gemini" / "config" / "skills"
GLOBAL_SCRIPTS_DIR = HOME / ".gemini" / "scripts"
GLOBAL_CURSOR_RULES_DIR = HOME / ".cursor" / "rules"
GLOBAL_CURSOR_SKILLS_DIR = HOME / ".cursor" / "skills"
GLOBAL_CURSOR_COMMANDS_DIR = HOME / ".cursor" / "commands"
GITHUB_ROOT = HOME / "Documents" / "GitHub"

STOREASY_FAMILY_REPOS = [
    "Huanxin-3Dimen",
    "StoreasyFMnew",
    "storeasynewwebsite",
    "storeasycws",
    "STOREASY_IT",
    "Storeasyworkdivnew",
    "StoreasyFinHR",
    "YangsDriver",
    "3Dstorage",
    "storeasy-location-lens",
    "storeasy_group_ordering",
    "move-easy",
]

US3C_FAMILY_REPOS = [
    "us3c-next",
    "711us3cwebsite",
    "msi_us3c_recycle",
    "us3cdriverapp",
    "us3cwebsite-env",
    "us3c_mvp",
    "usdwarrantynew",
    "beikeshop_v3_jx",
    "us3c-shopee-dashboard",
    "iMCheck",
    "logistic_driver",
    "price_crawler",
    "Yangbiz",
]

SHARED_FAMILY_REPOS = [
    "YoloMono",
]

GENERIC_FAMILY_REPOS = [
    "CADCraft",
    "DesignCraft",
    "Yangs-BizMarketing",
    "botmemeory",
    "newphamasys",
    "sitemap",
]

ALL_MANAGED_REPOS = STOREASY_FAMILY_REPOS + US3C_FAMILY_REPOS + SHARED_FAMILY_REPOS + GENERIC_FAMILY_REPOS

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

STOREASY_ONLY_RULES = {"storeasy-domain-invariants.mdc"}
US3C_ONLY_RULES = {"us3c-domain-invariants.mdc", "us3c-incident-l-grades.mdc"}

# 曾下發至各專案但已在全域淘汰／改名之舊技能目錄，須自專案雙目錄與 Cursor 目錄清理
KNOWN_OBSOLETE_SKILL_DIRS = {
    "vercel-react-best-practices",
    "claude.ai",
    "agency-automation-governance-architect",
    "agency-engineering-data-engineer",
    "agency-engineering-incident-response-commander",
    "agency-engineering-minimal-change-engineer",
    "agency-engineering-sre",
    "agency-project-manager-senior",
    "agency-testing-evidence-collector",
    "bigquery-data-transfer-service",
    "building-data-apps",
    "cloud-databases-onboarding",
    "data-autocleaning",
    "dataform-bigquery",
    "dbt-bigquery",
    "discovering-gcp-data-assets",
    "enforcing-resource-attribution",
    "gcp-data-pipelines",
    "gcp-dataflow",
    "gcp-pipeline-orchestration",
    "gcp-pipeline-resource-provisioning",
    "gcp-spark",
    "gcp-spark-observability",
    "gcp-spark-troubleshooting",
    "ml-best-practices",
    "notebook-guidance",
    "schema-mapping",
}

# 供 Cursor 對話框輸入 `/` 直接彈出選單的核心與產業專屬 Slash Commands (.cursor/commands/*.md)
SHARED_SLASH_COMMAND_SKILLS = {
    "multi-agent-mode",
    "ponytail",
    "ponytail-audit",
    "ponytail-review",
    "ponytail-debt",
    "ponytail-gain",
    "graphify",
    "fixer-prompt",
    "stage-gate-review",
    "impeccable",
    "emil-design-eng",
    "diagram-design",
    "decisions-governance",
    "session-handoff",
    "subagent-driven-development",
    "dispatching-parallel-agents",
    "tdd-workflow",
    "agent-desktop",
    "webapp-testing",
    "security-audit",
    "critical-stress-test",
    "migration-refactoring",
    "writing-plans",
    "humanizer-zh-tw",
    "modern-web-guidance",
    "stageshow",
}

SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", ".unlighthouse", ".claude-plugin", ".github", "evals"}
SKIP_EXTS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".pkl", ".db", ".sqlite", ".zip", ".tar", ".gz"}
MAX_FILE_BYTES = 256 * 1024  # 256 KB 上限，避免大型二進位或快取檔進入 Git


def get_repo_family(repo_name: str) -> str:
    low = repo_name.lower()
    if repo_name in SHARED_FAMILY_REPOS or low == "yolomono":
        return "shared"
    if repo_name in GENERIC_FAMILY_REPOS:
        return "generic"
    if (
        repo_name in US3C_FAMILY_REPOS
        or "us3c" in low
        or "imcheck" in low
        or "beikeshop" in low
        or "warranty" in low
    ):
        return "us3c"
    return "storeasy"


def read_frontmatter_name(skill_md: Path) -> str:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
        if not text.startswith("---"):
            return skill_md.parent.name
        end = text.find("\n---", 3)
        if end < 0:
            return skill_md.parent.name
        m = re.search(r"(?m)^name:\s*(.*)$", text[3:end])
        if m:
            val = m.group(1).strip().strip("'\"")
            if re.match(r"^[a-z0-9-]{1,64}$", val):
                return val
    except Exception:
        # Fall back to directory name when SKILL.md frontmatter cannot be read
        pass
    return skill_md.parent.name


def copy_clean_skill_dir(src_dir: Path, dst_dir: Path, dry_run: bool = False) -> int:
    """僅複製純淨輕量的 Skill 檔案（SKILL.md、references、scripts 等），排除 .venv 與 node_modules。"""
    if not dry_run:
        try:
            if (dst_dir.is_symlink() or dst_dir.is_file()) and not dst_dir.is_dir():
                dst_dir.unlink(missing_ok=True)
        except OSError:
            # Ignore unlink errors on stale symlinks or files before overwriting skill directory
            pass
    copied = 0
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".bsk")]
        rel_root = Path(root).relative_to(src_dir)
        target_root = dst_dir / rel_root
        for f in files:
            if f.startswith("."):
                continue
            src_f = Path(root) / f
            if src_f.suffix.lower() in SKIP_EXTS:
                continue
            try:
                if src_f.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            if not dry_run:
                target_root.mkdir(parents=True, exist_ok=True)
            dst_f = target_root / f
            if dst_f.is_file():
                try:
                    if src_f.stat().st_size == dst_f.stat().st_size and src_f.read_bytes() == dst_f.read_bytes():
                        continue
                except OSError:
                    # Fall through to mtime/size check when direct byte comparison fails
                    pass
            if src_f.suffix.lower() == ".md" or not dst_f.exists() or src_f.stat().st_mtime > dst_f.stat().st_mtime or src_f.stat().st_size != dst_f.stat().st_size:
                if not dry_run:
                    shutil.copy2(src_f, dst_f)
                copied += 1
    return copied


def ensure_gitignore_allows_cloud_skills(repo: Path, dry_run: bool = False) -> bool:
    """修正阻擋 .cursor/rules 或 .agents/skills 上傳 GitHub 的 .gitignore 規則。"""
    gi = repo / ".gitignore"
    if not gi.is_file():
        return False
    original = gi.read_text(encoding="utf-8", errors="ignore")
    updated = original

    updated = re.sub(
        r"(?m)^\.agent/\s*\n\.agents/\s*$",
        ".agent/scratch/\n.agent/inbox/\n.agent/memory/\n.agents/scratch/\n.agents/inbox/\n.agents/memory/",
        updated,
    )
    updated = re.sub(
        r"(?m)^\.agents/\s*$",
        ".agents/scratch/\n.agents/inbox/\n.agents/memory/",
        updated,
    )
    if ".cursor/*" in updated and "!.cursor/rules" not in updated:
        updated = updated.replace(
            "!.cursor/skills",
            "!.cursor/skills\n!.cursor/rules\n!.cursor/environment.json",
        )
    updated = re.sub(r"(?m)^\.agent/skills/taste-skill/\s*\n?", "", updated)

    if updated != original:
        if not dry_run:
            gi.write_text(updated, encoding="utf-8")
        return True
    return False


def ensure_cursor_environment_json(repo: Path, dry_run: bool = False) -> bool:
    """建立或更新 .cursor/environment.json 供 Cursor Cloud Agents 啟動時自動執行 bootstrap（保留 Laravel 等無該檔之雲端 DB 設定）。"""
    env_json_path = repo / ".cursor" / "environment.json"
    if (repo / "artisan").is_file() and not env_json_path.is_file():
        return False
    cmd = "python3 scripts/bootstrap_cursor_cloud.py || python scripts/bootstrap_cursor_cloud.py || true"
    original_text = ""
    data = {}
    if env_json_path.is_file():
        try:
            original_text = env_json_path.read_text(encoding="utf-8")
            data = json.loads(original_text)
        except Exception:
            # Replace malformed environment.json with valid bootstrap configuration
            data = {}
    if "install" not in data:
        data["install"] = cmd
    elif "bootstrap_cursor_cloud.py" not in str(data.get("install", "")):
        data["install"] = f"{data['install']} && ({cmd})"
    new_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    changed = (not env_json_path.is_file()) or (new_text != original_text)
    if changed and not dry_run:
        env_json_path.parent.mkdir(parents=True, exist_ok=True)
        env_json_path.write_text(new_text, encoding="utf-8")
    return changed


def has_git_symlink_architecture(repo: Path) -> bool:
    """檢查該 Repo 是否採用 AGENTS.md 的 120000 Git symlink 單一真相源架構（.agents -> .agent）。"""
    import subprocess
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-s", ".agents", ".cursor/skills", ".cursor/commands"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return "120000" in out
    except Exception:
        return False


SSOT_BEGIN = "<!-- BEGIN_LEAN_TRIAD_SSOT -->"
SSOT_END = "<!-- END_LEAN_TRIAD_SSOT -->"

CANONICAL_AGENTS_SSOT_BLOCK = """<!-- BEGIN_LEAN_TRIAD_SSOT -->
## Cursor Cloud & Agent Skills (Lean-Triad 單一真相來源)

> 本區塊由 `scripts/sync_skills_to_cloud_repos.py` 與 `scripts/bootstrap_cursor_cloud.py` 自 `~/.gemini/GEMINI.md` 及 `.cursor/rules/engineering-core.mdc` 自動同步鎖定；請勿單獨手改，避免本機與雲端規則分裂。

- **常駐底層引擎與受保護禁區**：`🧭 Graphify 圖譜導航` + `🧰 Role-Scoped Skills 動態掛載` + `✂️ Ponytail 極簡守則` 為常駐引擎；嚴禁簡化 3D 空間幾何／財務計價／硬體 IoT FOV 校準與跨庫 API 契約。刪減 `> 15` 行、移除抽象層／檔案或指定 `/multi-agent-mode` 時強制執行 `python3 scripts/multi_model_gate.py review --prompt "..." --git-diff --output temp_multi_review.json`（Plan／子代理優先 → 官方直連 → OpenRouter；Qwen 預設使用 `qwen4-max-preview`（備援 `qwen-max`））。
- **確定性門禁與技能路由**：
  - 改碼後強制執行確定性檢查：`python3 scripts/rule_lint.py --git-diff`（自動攔截 UI Emoji、按鈕過長或缺 `aria-label`/`title`、`<input type="date" lang="en" />` 缺漏、`dangerouslySetInnerHTML`、`.skip`／空 `catch` 與 `TODO:`/`FIXME:`/`HACK:`/`XXX:` 藉口註解；僅允許 `// shortcut: <上限條件>, <何時該升級>`）。
  - 前端 UI 遵循 `stageshow` × `impeccable` × `design-taste-frontend`（詳見 `.cursor/rules/react-typescript.mdc`）；精簡按鈕時**嚴禁刪除**不可逆風險警告、交易計價／稅額條件、合規聲明與專案 SEO/GEO 訊號。
  - 檢索最佳技能：`python3 scripts/skill_router.py route "<任務描述>"` | 預覽技能矩陣：`python3 scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`
- **任務結案白話總結與人機雙讀（`/eli5` × `/ponytail`）**：
  - 改碼與簡化走 `/ponytail`；每次完整任務交付之「**完成項目**」與「**重點任務總結**」（含 PR 摘要、SOP、故障復盤及 `// shortcut:` 說明）一律套用 `/eli5`——先用白話講清對使用者的實際影響與前後差異，同時保留檔案路徑／API 原文供工程追溯，絕不在演算法／契約層稀釋精度。
  - 更新 `README.md` 採雙層標準：上半部給人看（`/eli5` 白話定位與流程＋`/diagram-design` 中文架構圖 `nodes <= 9, edges <= 12`），下半部給 AI／工程師看（全庫真實結構、啟動測試指令與跨庫紅線；詳見 `~/.gemini/memory/eli5_ponytail_readme_dual_reading.md`）。
- **收尾誠實揭露與極簡防重複回條（Final-Turn Compact Lean-Triad Receipt）**：
  - **🚫 嚴禁輸出回條之場景（防 Token 浪費）**：等待背景任務（`run_command` / `Shell` / subagent）完成的中繼進度回覆、純合併／部署狀態回報、澄清提問、純問答或閒聊，或**同一任務無新程式碼變更時，絕對禁止附上執行回條**。
  - **🚫 嚴禁正文與回條內容重複（Anti-Duplication Rule）**：回條每欄僅限填寫**關鍵字、路徑、行數或指令結果**（每欄 `<= 60` 字），**嚴禁把正文寫過的結論、PR 編號或背景敘述重抄進回條**；反之，已寫入回條的測試通過數、行數統計與略過邊界，正文**不再重複條列**。
  - **✅ 最終交付格式**（僅在「任務最終完成交付」結尾輸出一次精簡逐行版回條）：
    ```markdown
    ---
    **🛡️ Lean-Triad**
    - 🧰 **Skills**：`<Skills>`
    - 🧭 **Graphify**：`<節點 / update>`
    - ✂️ **Ponytail**：`+<新增> / -<刪除> 行 (shortcut: <無或註記>)`
    - ⚖️ **Gate & QA**：`<multi_model_gate 真實 verdict/score/req_ids（若未跑腳本強制填「未執行 multi_model_gate」，嚴禁單一模型自評冒充）＋ 測試通過數>`
    - ⚠️ **邊界**：`<略過項目與風險>`
    ```
<!-- END_LEAN_TRIAD_SSOT -->"""


def sync_ssot_rules_from_gemini_md(dry_run: bool = False) -> dict:
    """
    確保本機單一真相來源 ~/.gemini/cursor-rules/*.mdc 與 ~/.cursor/rules/*.mdc 完全一致，
    避免覆蓋回退。支援 dry_run 預覽不寫入磁碟。
    """
    gemini_rules_dir = HOME / ".gemini" / "cursor-rules"
    if not dry_run:
        gemini_rules_dir.mkdir(parents=True, exist_ok=True)
        GLOBAL_CURSOR_RULES_DIR.mkdir(parents=True, exist_ok=True)

    src_mdc = gemini_rules_dir / "engineering-core.mdc"
    dst_mdc = GLOBAL_CURSOR_RULES_DIR / "engineering-core.mdc"

    if not src_mdc.is_file() and dst_mdc.is_file() and not dry_run:
        shutil.copy2(dst_mdc, src_mdc)

    planned_actions: list[dict[str, str]] = []
    if gemini_rules_dir.is_dir():
        for mdc in sorted(gemini_rules_dir.glob("*.mdc"), key=lambda p: p.name):
            target = GLOBAL_CURSOR_RULES_DIR / mdc.name
            if not target.is_file():
                action = "create"
            elif target.read_bytes() != mdc.read_bytes():
                action = "update"
            else:
                action = "unchanged"
            planned_actions.append({"file": mdc.name, "action": action})
            if not dry_run and action != "unchanged":
                shutil.copy2(mdc, target)

    return {
        "dry_run": dry_run,
        "source_dir": str(gemini_rules_dir),
        "target_dir": str(GLOBAL_CURSOR_RULES_DIR),
        "total_rules": len(planned_actions),
        "changed_count": sum(1 for item in planned_actions if item["action"] != "unchanged"),
        "planned_actions": planned_actions,
    }


def _iter_effective_global_rules() -> list[Path]:
    """收集欲同步至業務倉庫的 .mdc 來源檔（優先以 ~/.gemini/cursor-rules 為準，補充 ~/.cursor/rules 其他檔案）。"""
    merged: dict[str, Path] = {}
    if GLOBAL_CURSOR_RULES_DIR.is_dir():
        for mdc in GLOBAL_CURSOR_RULES_DIR.glob("*.mdc"):
            merged[mdc.name] = mdc
    gemini_rules_dir = HOME / ".gemini" / "cursor-rules"
    if gemini_rules_dir.is_dir():
        for mdc in gemini_rules_dir.glob("*.mdc"):
            merged[mdc.name] = mdc
    return [merged[k] for k in sorted(merged.keys())]


def ensure_agents_md_ssot(repo: Path, dry_run: bool = False, repo_name: str | None = None) -> bool:
    """
    將 Lean-Triad 單一真相來源區塊自動注入專案根目錄 AGENTS.md（Cursor Cloud Agents 唯一必讀系統提示檔）。
    若原本已有舊版 `## Lean-Triad 執行回條` 或 `## Cursor Cloud & Agent Skills (Lean-Triad)` 則原位替換為受管區塊。
    """
    target_name = repo_name or repo.name
    agents_md = repo / "AGENTS.md"
    if not agents_md.is_file():
        if not dry_run:
            agents_md.write_text(f"# AGENTS.md — {target_name}\n\n{CANONICAL_AGENTS_SSOT_BLOCK}\n", encoding="utf-8")
        return True

    original = agents_md.read_text(encoding="utf-8")
    updated = original

    if SSOT_BEGIN in updated and SSOT_END in updated:
        pattern = re.compile(
            re.escape(SSOT_BEGIN) + r".*?" + re.escape(SSOT_END),
            re.DOTALL,
        )
        updated = pattern.sub(CANONICAL_AGENTS_SSOT_BLOCK, updated)
    else:
        legacy_patterns = [
            re.compile(
                r"## Cursor Cloud & Agent Skills \(Lean-Triad[^\n]*\)\n.*?(?=\n## |\Z)",
                re.DOTALL,
            ),
            re.compile(
                r"## Lean-Triad 執行回條[^\n]*\n.*?(?=\n## |\Z)",
                re.DOTALL,
            ),
        ]
        replaced = False
        for lp in legacy_patterns:
            if lp.search(updated):
                updated = lp.sub(CANONICAL_AGENTS_SSOT_BLOCK + "\n", updated, count=1)
                replaced = True
                break
        if not replaced:
            if "\n## graphify" in updated:
                updated = updated.replace(
                    "\n## graphify",
                    f"\n{CANONICAL_AGENTS_SSOT_BLOCK}\n\n## graphify",
                    1,
                )
            else:
                updated = updated.rstrip() + f"\n\n{CANONICAL_AGENTS_SSOT_BLOCK}\n"

    if updated != original:
        if not dry_run:
            agents_md.write_text(updated, encoding="utf-8")
        return True
    return False


PRE_COMMIT_BEGIN = "# BEGIN_LEAN_TRIAD_RULE_LINT_HOOK"
PRE_COMMIT_END = "# END_LEAN_TRIAD_RULE_LINT_HOOK"
PRE_COMMIT_HOOK_BLOCK = """# BEGIN_LEAN_TRIAD_RULE_LINT_HOOK
_LT_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
_LT_LINT="$_LT_REPO_ROOT/scripts/rule_lint.py"
if [ ! -f "$_LT_LINT" ] || ! grep -q -- "--staged" "$_LT_LINT" 2>/dev/null; then
  [ -f "$HOME/.gemini/scripts/rule_lint.py" ] && _LT_LINT="$HOME/.gemini/scripts/rule_lint.py"
fi
if [ -f "$_LT_LINT" ]; then
  _LT_PY=""
  for _lt_cand in python3 python; do
    if command -v "$_lt_cand" >/dev/null 2>&1 && "$_lt_cand" -c "import sys" >/dev/null 2>&1; then
      _LT_PY="$_lt_cand"
      break
    fi
  done
  if [ -n "$_LT_PY" ]; then
    _lt_out="$("$_LT_PY" "$_LT_LINT" --git-diff --staged --repo "$_LT_REPO_ROOT" 2>&1)"
    _lt_rc=$?
    if [ "$_lt_rc" -ne 0 ]; then
      printf '%s\\n' "$_lt_out" | head -n 30
      echo "[pre-commit][Rule-Lint Gate] 發現違規（exit=$_lt_rc），請依上方提示修正後再 commit。"
      exit 1
    fi
  fi
fi
# END_LEAN_TRIAD_RULE_LINT_HOOK"""


def _is_junction(path: Path) -> bool:
    """Python 3.10+ 相容的 NTFS Junction 偵測（於 3.12+ 呼叫 is_junction，舊版回 False）。"""
    fn = getattr(path, "is_junction", None)
    if callable(fn):
        try:
            return bool(fn())
        except OSError:
            return False
    return False


def _remove_readonly_tree(path: Path) -> None:
    """移除目錄樹並在 Windows 遇唯讀屬性阻擋時先解除只讀旗標再重試刪除。"""
    import stat

    def _on_exc(func, target, _exc):
        try:
            os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
            func(target)
        except OSError:
            # Ignore locked files that remain inaccessible even after clearing read-only flag
            pass

    if path.is_symlink() or _is_junction(path):
        try:
            path.unlink()
        except OSError:
            os.rmdir(path)
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_on_exc)
    else:
        shutil.rmtree(path, onerror=lambda fn, tgt, ei: _on_exc(fn, tgt, ei[1]))


def _resolve_git_hooks_dir(repo: Path) -> Path | None:
    if not (repo / ".git").exists():
        return None
    import subprocess

    try:
        rel = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--git-path", "hooks"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if not rel:
            return None
        p = Path(rel)
        hooks_path = p.resolve() if p.is_absolute() else (repo / p).resolve()
        # 邊界守門：若設定了指向倉庫外部的 core.hooksPath，拒絕跨界寫入
        if not hooks_path.is_relative_to(repo.resolve()):
            return None
        return hooks_path
    except Exception:
        # Non-git directory or corrupted .git pointer file; skip hook injection safely
        return None


def ensure_git_pre_commit_rule_lint(repo: Path, dry_run: bool = False) -> bool:
    """以 Unix LF 無損將 rule_lint.py --staged 門禁掛入 .git/hooks/pre-commit，保留專案既有檢查。"""
    hooks_dir = _resolve_git_hooks_dir(repo)
    if hooks_dir is None:
        return False
    pre_commit = hooks_dir / "pre-commit"
    if pre_commit.is_file():
        raw_bytes = pre_commit.read_bytes()
        try:
            original = raw_bytes.decode("utf-8-sig", errors="strict").replace("\r\n", "\n")
        except UnicodeDecodeError:
            # Avoid corrupting legacy non-UTF-8 hook files
            return False
        if PRE_COMMIT_BEGIN in original and PRE_COMMIT_END in original:
            pattern = re.compile(
                re.escape(PRE_COMMIT_BEGIN) + r".*?" + re.escape(PRE_COMMIT_END),
                re.DOTALL,
            )
            updated = pattern.sub(lambda _: PRE_COMMIT_HOOK_BLOCK, original)
        elif re.search(r"\nexit 0[ \t]*\n?$", original):
            updated = re.sub(
                r"\nexit 0[ \t]*\n?$",
                lambda _: f"\n\n{PRE_COMMIT_HOOK_BLOCK}\nexit 0\n",
                original,
                count=1,
            )
        else:
            updated = original.rstrip() + f"\n\n{PRE_COMMIT_HOOK_BLOCK}\n"
        new_bytes = updated.encode("utf-8")
        changed = new_bytes != raw_bytes
    else:
        updated = f"#!/bin/sh\n{PRE_COMMIT_HOOK_BLOCK}\nexit 0\n"
        new_bytes = updated.encode("utf-8")
        changed = True

    if changed and not dry_run:
        hooks_dir.mkdir(parents=True, exist_ok=True)
        with pre_commit.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(updated)
        try:
            os.chmod(pre_commit, 0o755)
        except OSError:
            # Windows NTFS ignores POSIX executable bit; ignore chmod failure safely
            pass
    return changed


def sync_repo(repo: Path, global_skills: list[Path], rules_only: bool = False, dry_run: bool = False, repo_name: str | None = None) -> dict:
    target_name = repo_name or repo.name
    family = get_repo_family(target_name)
    if family == "shared":
        excluded_skills: set[str] = set()
        excluded_rules: set[str] = set()
    elif family == "generic":
        excluded_skills = STOREASY_ONLY_SKILLS | US3C_ONLY_SKILLS
        excluded_rules = STOREASY_ONLY_RULES | US3C_ONLY_RULES
    else:
        excluded_skills = STOREASY_ONLY_SKILLS if family == "us3c" else US3C_ONLY_SKILLS
        excluded_rules = STOREASY_ONLY_RULES if family == "us3c" else US3C_ONLY_RULES
    uses_git_symlinks = has_git_symlink_architecture(repo)
    planned_actions: list[str] = []

    if not uses_git_symlinks:
        for rel in (".agents", ".cursor", ".cursor/skills", ".cursor/rules", ".cursor/commands", ".agents/skills"):
            p = repo / rel
            try:
                if (p.is_file() or p.is_symlink()) and not p.is_dir():
                    planned_actions.append(f"cleanup:{rel}")
                    if not dry_run:
                        p.unlink(missing_ok=True)
            except OSError:
                # Ignore stat/unlink errors on broken paths during symlink cleanup
                pass

    gitignore_fixed = ensure_gitignore_allows_cloud_skills(repo, dry_run=dry_run)
    if gitignore_fixed:
        planned_actions.append("update:.gitignore")

    # 1. 依產業家族同步 .cursor/rules/*.mdc，並清理另一產業之專屬規則檔（保留專案自有規則如 usd-shop.mdc）
    rules_dst = repo / ".cursor" / "rules"
    if not dry_run:
        rules_dst.mkdir(parents=True, exist_ok=True)
    for old_rule in excluded_rules:
        old_path = rules_dst / old_rule
        if old_path.exists() or old_path.is_symlink():
            planned_actions.append(f"delete:.cursor/rules/{old_rule}")
            if not dry_run:
                old_path.unlink(missing_ok=True)

    rules_synced = 0
    for mdc in _iter_effective_global_rules():
        if mdc.name in excluded_rules:
            continue
        dst_rule = rules_dst / mdc.name
        needs_write = (not dst_rule.is_file()) or (dst_rule.read_bytes() != mdc.read_bytes())
        if needs_write:
            action_kind = "update" if dst_rule.is_file() else "create"
            planned_actions.append(f"{action_kind}:.cursor/rules/{mdc.name}")
            if not dry_run:
                shutil.copy2(mdc, dst_rule)
        rules_synced += 1

    # 2. 同步跨平台腳本至 scripts/（納入 rule_lint.py）
    scripts_dst = repo / "scripts"
    if not dry_run:
        scripts_dst.mkdir(parents=True, exist_ok=True)
    for fname in (
        "skill_router.py",
        "multi_model_gate.py",
        "rule_lint.py",
        "skill_eval_dataset.json",
        "bootstrap_cursor_cloud.py",
        "sync_skills_to_cloud_repos.py",
    ):
        src_f = GLOBAL_SCRIPTS_DIR / fname
        dst_f = scripts_dst / fname
        if src_f.is_file():
            try:
                if os.path.realpath(src_f) != os.path.realpath(dst_f):
                    needs_copy = (not dst_f.is_file()) or (dst_f.read_bytes() != src_f.read_bytes())
                    if needs_copy:
                        action_kind = "update" if dst_f.is_file() else "create"
                        planned_actions.append(f"{action_kind}:scripts/{fname}")
                        if not dry_run:
                            shutil.copy2(src_f, dst_f)
            except OSError:
                # Ignore path resolution or permission error when syncing helper scripts
                pass

    # 1b. 自動同步專案根目錄 AGENTS.md 的受管單一真相來源區塊 (SSOT)
    agents_existed = (repo / "AGENTS.md").is_file()
    agents_md_updated = ensure_agents_md_ssot(repo, dry_run=dry_run, repo_name=target_name)
    if agents_md_updated:
        planned_actions.append(f"{'update' if agents_existed else 'create'}:AGENTS.md")

    # 3. 同步 .cursor/environment.json
    env_existed = (repo / ".cursor" / "environment.json").is_file()
    env_json_updated = ensure_cursor_environment_json(repo, dry_run=dry_run)
    if env_json_updated:
        planned_actions.append(f"{'update' if env_existed else 'create'}:.cursor/environment.json")

    # 3b. 無損掛載 .git/hooks/pre-commit 的 rule_lint.py --staged 守門區塊
    pre_commit_updated = ensure_git_pre_commit_rule_lint(repo, dry_run=dry_run)
    if pre_commit_updated:
        planned_actions.append("update:.git/hooks/pre-commit")

    if rules_only:
        return {
            "repo": target_name,
            "family": family,
            "dry_run": dry_run,
            "rules_synced": rules_synced,
            "agents_md_ssot_updated": agents_md_updated,
            "env_json_updated": env_json_updated,
            "pre_commit_updated": pre_commit_updated,
            "gitignore_fixed": gitignore_fixed,
            "planned_actions": planned_actions,
            "mode": "rules_only",
        }

    # 4. 依產業家族過濾並同步專屬 Skills（若為 120000 Git symlink 架構則只寫入單一真相源 .agent/skills，防止雙倍/三倍重複掃描）
    family_skills = []
    for d in global_skills:
        dir_name = d.name
        fm_name = read_frontmatter_name(d / "SKILL.md")
        if dir_name in excluded_skills or fm_name in excluded_skills:
            continue
        family_skills.append(d)

    if uses_git_symlinks:
        primary_skills_dst = repo / ".agent" / "skills"
        if not dry_run:
            primary_skills_dst.mkdir(parents=True, exist_ok=True)
        if primary_skills_dst.is_dir():
            for child in list(primary_skills_dst.iterdir()):
                if child.name == ".datacloud_skills_manifest" and child.is_file():
                    planned_actions.append(f"delete:.agent/skills/{child.name}")
                    if not dry_run:
                        child.unlink(missing_ok=True)
                    continue
                if (
                    child.name in excluded_skills
                    or child.name in KNOWN_OBSOLETE_SKILL_DIRS
                    or child.name.startswith("source-command-")
                ) and child.is_dir():
                    planned_actions.append(f"delete:.agent/skills/{child.name}")
                    if not dry_run:
                        _remove_readonly_tree(child)
        skill_count = 0
        skill_files_changed = 0
        for s_dir in family_skills:
            fm_name = read_frontmatter_name(s_dir / "SKILL.md")
            if s_dir.name != fm_name and (primary_skills_dst / s_dir.name).is_dir() and (primary_skills_dst / fm_name).is_dir():
                planned_actions.append(f"delete:.agent/skills/{s_dir.name}")
                if not dry_run:
                    _remove_readonly_tree(primary_skills_dst / s_dir.name)
            target_dir_name = s_dir.name if (primary_skills_dst / s_dir.name).is_dir() else fm_name
            skill_files_changed += copy_clean_skill_dir(s_dir, primary_skills_dst / target_dir_name, dry_run=dry_run)
            skill_count += 1
        if skill_files_changed:
            planned_actions.append(f"sync_skill_files:.agent/skills ({skill_files_changed} files)")
        return {
            "repo": target_name,
            "family": family,
            "dry_run": dry_run,
            "architecture": "git-symlink-single-source",
            "rules_synced": rules_synced,
            "commands_synced": 0,
            "skills_synced": skill_count,
            "agents_md_ssot_updated": agents_md_updated,
            "pre_commit_updated": pre_commit_updated,
            "gitignore_fixed": gitignore_fixed,
            "planned_actions": planned_actions,
        }

    agents_skills_dst = repo / ".agents" / "skills"
    cursor_skills_dst = repo / ".cursor" / "skills"
    if not dry_run:
        agents_skills_dst.mkdir(parents=True, exist_ok=True)
        cursor_skills_dst.mkdir(parents=True, exist_ok=True)

    same_target = False
    try:
        same_target = agents_skills_dst.resolve() == cursor_skills_dst.resolve()
    except OSError:
        same_target = False

    # 清理非 Git-symlink 專案之舊版 .agent/skills（遷移專案獨有客製技能至 .agents/skills 後徹底刪除）
    legacy_agent_skills = repo / ".agent" / "skills"
    global_known_names: set[str] = set()
    for d in global_skills:
        global_known_names.add(d.name)
        global_known_names.add(read_frontmatter_name(d / "SKILL.md"))

    if legacy_agent_skills.is_dir():
        for child in list(legacy_agent_skills.iterdir()):
            if not child.is_dir() or not (child / "SKILL.md").is_file():
                continue
            if (
                child.name in excluded_skills
                or child.name in KNOWN_OBSOLETE_SKILL_DIRS
                or child.name.startswith("source-command-")
                or child.name in global_known_names
            ):
                continue
            child_fm = read_frontmatter_name(child / "SKILL.md")
            if child_fm in excluded_skills or child_fm in KNOWN_OBSOLETE_SKILL_DIRS or child_fm in global_known_names:
                continue
            if not (agents_skills_dst / child.name).exists():
                planned_actions.append(f"migrate:.agent/skills/{child.name}->.agents/skills/{child.name}")
                copy_clean_skill_dir(child, agents_skills_dst / child.name, dry_run=dry_run)
        planned_actions.append("delete:.agent/skills")
        if not dry_run:
            _remove_readonly_tree(legacy_agent_skills)
            legacy_agent_root = repo / ".agent"
            if legacy_agent_root.is_dir():
                try:
                    if not any(legacy_agent_root.iterdir()):
                        legacy_agent_root.rmdir()
                except OSError:
                    # Keep .agent directory when locked or still holding rules/workflows
                    pass

    cleanup_dirs = [agents_skills_dst]
    if not same_target:
        cleanup_dirs.append(cursor_skills_dst)
    for sub_dir in cleanup_dirs:
        if not sub_dir.is_dir():
            continue
        for child in list(sub_dir.iterdir()):
            if child.name == ".datacloud_skills_manifest" and child.is_file():
                planned_actions.append(f"delete:{sub_dir.relative_to(repo).as_posix()}/{child.name}")
                if not dry_run:
                    child.unlink(missing_ok=True)
                continue
            if (
                child.name in excluded_skills
                or child.name in KNOWN_OBSOLETE_SKILL_DIRS
                or child.name.startswith("source-command-")
            ) and child.is_dir():
                planned_actions.append(f"delete:{sub_dir.relative_to(repo).as_posix()}/{child.name}")
                if not dry_run:
                    _remove_readonly_tree(child)

    skill_count = 0
    skill_files_changed = 0
    for s_dir in family_skills:
        dir_name = s_dir.name
        fm_name = read_frontmatter_name(s_dir / "SKILL.md")
        skill_files_changed += copy_clean_skill_dir(s_dir, agents_skills_dst / dir_name, dry_run=dry_run)
        if not same_target:
            skill_files_changed += copy_clean_skill_dir(s_dir, cursor_skills_dst / fm_name, dry_run=dry_run)
        skill_count += 1

    if not same_target and agents_skills_dst.is_dir():
        for existing_dir in agents_skills_dst.iterdir():
            if existing_dir.is_dir() and (existing_dir / "SKILL.md").is_file():
                fm_name = read_frontmatter_name(existing_dir / "SKILL.md")
                if fm_name not in excluded_skills and not (cursor_skills_dst / fm_name).exists():
                    skill_files_changed += copy_clean_skill_dir(existing_dir, cursor_skills_dst / fm_name, dry_run=dry_run)

    if skill_files_changed:
        planned_actions.append(f"sync_skill_files:.agents/.cursor/skills ({skill_files_changed} files)")

    # 5. 同步 .cursor/commands/*.md（讓 Cursor 輸入 `/` 直接跳出核心與產業專屬技能選單；保留既有 symlink 如 us3c-next）
    commands_dst = repo / ".cursor" / "commands"
    commands_synced = 0
    is_cmd_link = False
    try:
        is_cmd_link = commands_dst.is_symlink() or _is_junction(commands_dst)
    except OSError:
        is_cmd_link = False

    if not is_cmd_link:
        if not dry_run:
            commands_dst.mkdir(parents=True, exist_ok=True)
        allowed_cmds = SHARED_SLASH_COMMAND_SKILLS | (
            (STOREASY_ONLY_SKILLS | US3C_ONLY_SKILLS)
            if family == "shared"
            else (US3C_ONLY_SKILLS if family == "us3c" else STOREASY_ONLY_SKILLS)
        )
        if commands_dst.is_dir():
            for old_cmd in list(commands_dst.glob("*.md")):
                if old_cmd.stem in excluded_skills:
                    planned_actions.append(f"delete:.cursor/commands/{old_cmd.name}")
                    if not dry_run:
                        old_cmd.unlink(missing_ok=True)
        for s_dir in family_skills:
            fm_name = read_frontmatter_name(s_dir / "SKILL.md")
            if fm_name in allowed_cmds or s_dir.name in allowed_cmds:
                src_cmd = s_dir / "SKILL.md"
                dst_cmd = commands_dst / f"{fm_name}.md"
                if (not dst_cmd.is_file()) or (dst_cmd.read_bytes() != src_cmd.read_bytes()):
                    planned_actions.append(f"{'update' if dst_cmd.is_file() else 'create'}:.cursor/commands/{fm_name}.md")
                    if not dry_run:
                        shutil.copy2(src_cmd, dst_cmd)
                commands_synced += 1

    return {
        "repo": target_name,
        "family": family,
        "dry_run": dry_run,
        "rules_synced": rules_synced,
        "commands_synced": commands_synced,
        "skills_synced": skill_count,
        "agents_md_ssot_updated": agents_md_updated,
        "pre_commit_updated": pre_commit_updated,
        "gitignore_fixed": gitignore_fixed,
        "planned_actions": planned_actions,
    }


def sync_local_cursor_user_dirs(global_skills: list[Path], dry_run: bool = False) -> dict:
    """
    1. 修復本機 Windows ~/.cursor/skills 的 NTFS Directory Junction 陷阱，轉為真實實體目錄。
       不再把 SKILL.md 複製成 ~/.cursor/commands/*.md（會與同名 skill 在「/」選單重複）；
       並清除先前由本腳本產生、內容與 SKILL.md 完全相同的 command 副本（自訂 command 不動）。
    2. 同步至 Cursor 跨機雲端 AgentStore (`LOCALAPPDATA/Cursor/AgentStores/cursor_agent_stores/u*/files/skills`)，
       讓同一 Cursor 帳號在 `DESKTOP-N1NJDUH` 與 `YangPC` 之間自動雲端同步 User Skills。
    """
    if not dry_run:
        GLOBAL_CURSOR_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        GLOBAL_CURSOR_RULES_DIR.mkdir(parents=True, exist_ok=True)
        for mdc in (HOME / ".gemini" / "cursor-rules").glob("*.mdc"):
            shutil.copy2(mdc, GLOBAL_CURSOR_RULES_DIR / mdc.name)

    removed_junctions = 0
    if GLOBAL_CURSOR_SKILLS_DIR.is_dir():
        for item in list(GLOBAL_CURSOR_SKILLS_DIR.iterdir()):
            try:
                if _is_junction(item):
                    if not dry_run:
                        os.rmdir(item)
                    removed_junctions += 1
                elif item.is_symlink() or item.is_file():
                    if not dry_run:
                        item.unlink(missing_ok=True)
                    removed_junctions += 1
            except OSError:
                # Ignore permission or filesystem error on junction/symlink inspection
                pass

    valid_names: set[str] = set()
    for d in global_skills:
        fm = read_frontmatter_name(d / "SKILL.md")
        valid_names.add(fm)
        copy_clean_skill_dir(d, GLOBAL_CURSOR_SKILLS_DIR / fm, dry_run=dry_run)

    if GLOBAL_CURSOR_SKILLS_DIR.is_dir():
        for child in list(GLOBAL_CURSOR_SKILLS_DIR.iterdir()):
            if child.name not in valid_names and child.is_dir():
                if not dry_run:
                    shutil.rmtree(child, ignore_errors=True)

    cmd_pruned = 0
    if GLOBAL_CURSOR_COMMANDS_DIR.is_dir():
        for d in global_skills:
            fm = read_frontmatter_name(d / "SKILL.md")
            twin = GLOBAL_CURSOR_COMMANDS_DIR / f"{fm}.md"
            try:
                if twin.is_file() and twin.read_bytes() == (d / "SKILL.md").read_bytes():
                    if not dry_run:
                        twin.unlink()
                    cmd_pruned += 1
            except OSError:
                # Ignore read/unlink error while pruning duplicate command copies
                pass

    # 同步至 Cursor AgentStores (u*/files/skills) 實現跨電腦 User Skills 雲端同步
    agent_store_synced = 0
    local_appdata = Path(os.environ.get("LOCALAPPDATA", str(HOME / "AppData" / "Local")))
    stores_root = local_appdata / "Cursor" / "AgentStores" / "cursor_agent_stores"
    if stores_root.is_dir():
        for u_dir in stores_root.glob("u*"):
            if not u_dir.is_dir():
                continue
            store_skills_dir = u_dir / "files" / "skills"
            if not dry_run:
                store_skills_dir.mkdir(parents=True, exist_ok=True)
            for d in global_skills:
                fm = read_frontmatter_name(d / "SKILL.md")
                copy_clean_skill_dir(d, store_skills_dir / fm, dry_run=dry_run)
                agent_store_synced += 1

    return {
        "dry_run": dry_run,
        "removed_junctions": removed_junctions,
        "user_cursor_skills": len(valid_names),
        "cursor_command_copies_pruned": cmd_pruned,
        "agent_store_skills_synced": agent_store_synced,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync industry-scoped rules & skills to repos for Cursor Cloud Agents")
    parser.add_argument("--repo", type=str, default="all", help="Repo name, 'storeasy', 'us3c', or 'all'")
    parser.add_argument("--rules-only", action="store_true", help="Fast mode: sync only .cursor/rules, AGENTS.md SSOT block, and scripts/")
    parser.add_argument("--local-cursor-only", action="store_true", help="Only sync ~/.gemini/cursor-rules/*.mdc to ~/.cursor/rules/*.mdc without touching external repos")
    parser.add_argument("--dry-run", action="store_true", help="Preview planned sync actions without writing or deleting any files on disk")
    args = parser.parse_args()

    local_rules_sync = sync_ssot_rules_from_gemini_md(dry_run=args.dry_run)
    if args.local_cursor_only:
        print(
            json.dumps(
                {
                    "mode": "local_cursor_only",
                    "dry_run": bool(args.dry_run),
                    "local_cursor_rules_sync": local_rules_sync,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.repo == "all":
        target_names = ALL_MANAGED_REPOS
    elif args.repo == "storeasy":
        target_names = STOREASY_FAMILY_REPOS
    elif args.repo == "us3c":
        target_names = US3C_FAMILY_REPOS
    elif args.repo == "generic":
        target_names = GENERIC_FAMILY_REPOS
    else:
        target_names = [args.repo]
    repos = [GITHUB_ROOT / name for name in target_names if (GITHUB_ROOT / name).is_dir()]

    global_skills = sorted(
        [
            d
            for d in GLOBAL_SKILLS_DIR.iterdir()
            if d.is_dir() and not _is_junction(d) and (d / "SKILL.md").is_file()
        ],
        key=lambda x: x.name,
    )

    user_cursor_sync = (
        {"mode": "rules_only", "dry_run": bool(args.dry_run)}
        if args.rules_only
        else sync_local_cursor_user_dirs(global_skills, dry_run=args.dry_run)
    )

    results = []
    for repo in repos:
        results.append(sync_repo(repo, global_skills, rules_only=args.rules_only, dry_run=args.dry_run))

    print(
        json.dumps(
            {
                "dry_run": bool(args.dry_run),
                "rules_only": bool(args.rules_only),
                "total_master_skills": len(global_skills),
                "local_cursor_rules_sync": local_rules_sync,
                "user_cursor_sync": user_cursor_sync,
                "storeasy_only_count": len(STOREASY_ONLY_SKILLS),
                "us3c_only_count": len(US3C_ONLY_SKILLS) - 1,  # jev-typesafe & jev alias
                "repos_synced": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
