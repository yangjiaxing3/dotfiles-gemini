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

ALL_MANAGED_REPOS = STOREASY_FAMILY_REPOS + US3C_FAMILY_REPOS

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
}

SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", ".unlighthouse", ".claude-plugin", ".github", "evals"}
SKIP_EXTS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".pkl", ".db", ".sqlite", ".zip", ".tar", ".gz"}
MAX_FILE_BYTES = 256 * 1024  # 256 KB 上限，避免大型二進位或快取檔進入 Git


def get_repo_family(repo_name: str) -> str:
    low = repo_name.lower()
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
        pass
    return skill_md.parent.name


def copy_clean_skill_dir(src_dir: Path, dst_dir: Path) -> int:
    """僅複製純淨輕量的 Skill 檔案（SKILL.md、references、scripts 等），排除 .venv 與 node_modules。"""
    try:
        if (dst_dir.is_symlink() or dst_dir.is_file()) and not dst_dir.is_dir():
            dst_dir.unlink(missing_ok=True)
    except OSError:
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
            target_root.mkdir(parents=True, exist_ok=True)
            dst_f = target_root / f
            if src_f.suffix.lower() == ".md" or not dst_f.exists() or src_f.stat().st_mtime > dst_f.stat().st_mtime or src_f.stat().st_size != dst_f.stat().st_size:
                shutil.copy2(src_f, dst_f)
                copied += 1
    return copied


def ensure_gitignore_allows_cloud_skills(repo: Path) -> bool:
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
        gi.write_text(updated, encoding="utf-8")
        return True
    return False


def ensure_cursor_environment_json(repo: Path) -> None:
    """建立或更新 .cursor/environment.json 供 Cursor Cloud Agents 啟動時自動執行 bootstrap（保留 Laravel 等無該檔之雲端 DB 設定）。"""
    env_json_path = repo / ".cursor" / "environment.json"
    if (repo / "artisan").is_file() and not env_json_path.is_file():
        return
    env_json_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = "python3 scripts/bootstrap_cursor_cloud.py || python scripts/bootstrap_cursor_cloud.py || true"
    data = {}
    if env_json_path.is_file():
        try:
            data = json.loads(env_json_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    if "install" not in data:
        data["install"] = cmd
    elif "bootstrap_cursor_cloud.py" not in str(data.get("install", "")):
        data["install"] = f"{data['install']} && ({cmd})"
    env_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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

- **常駐底層引擎**：`🧭 Graphify 圖譜導航` + `🧰 Role-Scoped Skills 動態掛載` + `✂️ Ponytail 極簡守則` 為常駐引擎；刪減 `> 15` 行、移除抽象層／檔案或指定 `/multi-agent-mode` 時強制執行 `python3 scripts/multi_model_gate.py review --prompt "..." --git-diff --output temp_multi_review.json`。
- **確定性路由與多模型門禁**：
  - 檢索最佳技能：`python3 scripts/skill_router.py route "<任務描述>"`
  - 預覽角色×任務技能矩陣：`python3 scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`
- **全域 UI 圖示與極簡按鈕鐵律（`impeccable` × `stageshow` × `design-taste-frontend`）**：
  - **嚴禁 UI Emoji**：頁面標題、KPI、徽章、按鈕、表格與提示文字一律禁止使用 Emoji；視覺引導統一使用乾淨 SVG 或 `lucide-react` 圖示。
  - **按鈕限 2～4 字或純 Icon**：操作按鈕強制精簡為 **2～4 個字**（如 `新增批次`、`匯出 Excel`、`顯示月薪`）或純 SVG Icon 按鈕（必備 `title` 與 `aria-label`），並移除重複標題語意的冗餘說明文字。
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
    - ⚖️ **Gate & QA**：`<會審門禁與測試通過數>`
    - ⚠️ **邊界**：`<略過項目與風險>`
    ```
<!-- END_LEAN_TRIAD_SSOT -->"""


def sync_ssot_rules_from_gemini_md() -> bool:
    """
    確保本機單一真相來源 ~/.gemini/GEMINI.md、~/.gemini/cursor-rules/engineering-core.mdc 與
    ~/.cursor/rules/engineering-core.mdc 的回條與防重複規範完全一致，消除覆蓋回退。
    """
    gemini_rules_dir = HOME / ".gemini" / "cursor-rules"
    gemini_rules_dir.mkdir(parents=True, exist_ok=True)
    GLOBAL_CURSOR_RULES_DIR.mkdir(parents=True, exist_ok=True)

    src_mdc = gemini_rules_dir / "engineering-core.mdc"
    dst_mdc = GLOBAL_CURSOR_RULES_DIR / "engineering-core.mdc"

    if dst_mdc.is_file() and (not src_mdc.is_file() or "Anti-Duplication Rule" not in src_mdc.read_text(encoding="utf-8")):
        if "Anti-Duplication Rule" in dst_mdc.read_text(encoding="utf-8"):
            shutil.copy2(dst_mdc, src_mdc)

    for mdc in gemini_rules_dir.glob("*.mdc"):
        shutil.copy2(mdc, GLOBAL_CURSOR_RULES_DIR / mdc.name)
    return True


def ensure_agents_md_ssot(repo: Path) -> bool:
    """
    將 Lean-Triad 單一真相來源區塊自動注入專案根目錄 AGENTS.md（Cursor Cloud Agents 唯一必讀系統提示檔）。
    若原本已有舊版 `## Lean-Triad 執行回條` 或 `## Cursor Cloud & Agent Skills (Lean-Triad)` 則原位替換為受管區塊。
    """
    agents_md = repo / "AGENTS.md"
    if not agents_md.is_file():
        agents_md.write_text(f"# AGENTS.md — {repo.name}\n\n{CANONICAL_AGENTS_SSOT_BLOCK}\n", encoding="utf-8")
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
        agents_md.write_text(updated, encoding="utf-8")
        return True
    return False


def sync_repo(repo: Path, global_skills: list[Path], rules_only: bool = False) -> dict:
    family = get_repo_family(repo.name)
    excluded_skills = STOREASY_ONLY_SKILLS if family == "us3c" else US3C_ONLY_SKILLS
    excluded_rules = STOREASY_ONLY_RULES if family == "us3c" else US3C_ONLY_RULES
    uses_git_symlinks = has_git_symlink_architecture(repo)

    if not uses_git_symlinks:
        for rel in (".agents", ".cursor", ".cursor/skills", ".cursor/rules", ".cursor/commands", ".agents/skills"):
            p = repo / rel
            try:
                if (p.is_file() or p.is_symlink()) and not p.is_dir():
                    p.unlink(missing_ok=True)
            except OSError:
                pass

    gitignore_fixed = ensure_gitignore_allows_cloud_skills(repo)

    # 1. 依產業家族同步 .cursor/rules/*.mdc，並清理另一產業之專屬規則檔（保留專案自有規則如 usd-shop.mdc）
    rules_dst = repo / ".cursor" / "rules"
    rules_dst.mkdir(parents=True, exist_ok=True)
    for old_rule in excluded_rules:
        (rules_dst / old_rule).unlink(missing_ok=True)

    rules_synced = 0
    if GLOBAL_CURSOR_RULES_DIR.is_dir():
        for mdc in GLOBAL_CURSOR_RULES_DIR.glob("*.mdc"):
            if mdc.name in excluded_rules:
                continue
            shutil.copy2(mdc, rules_dst / mdc.name)
            rules_synced += 1

    # 2. 同步跨平台腳本至 scripts/
    scripts_dst = repo / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for fname in (
        "skill_router.py",
        "multi_model_gate.py",
        "skill_eval_dataset.json",
        "bootstrap_cursor_cloud.py",
        "sync_skills_to_cloud_repos.py",
    ):
        src_f = GLOBAL_SCRIPTS_DIR / fname
        if src_f.is_file():
            try:
                if os.path.realpath(src_f) != os.path.realpath(scripts_dst / fname):
                    shutil.copy2(src_f, scripts_dst / fname)
            except OSError:
                pass

    # 1b. 自動同步專案根目錄 AGENTS.md 的受管單一真相來源區塊 (SSOT)
    agents_md_updated = ensure_agents_md_ssot(repo)

    # 3. 同步 .cursor/environment.json
    ensure_cursor_environment_json(repo)

    if rules_only:
        return {
            "repo": repo.name,
            "family": family,
            "rules_synced": rules_synced,
            "agents_md_ssot_updated": agents_md_updated,
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
        primary_skills_dst.mkdir(parents=True, exist_ok=True)
        for child in list(primary_skills_dst.iterdir()):
            if (child.name in excluded_skills or child.name.startswith("source-command-")) and child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
        skill_count = 0
        for s_dir in family_skills:
            fm_name = read_frontmatter_name(s_dir / "SKILL.md")
            # 移除同 frontmatter name 但不同資料夾名稱的重複舊目錄
            if s_dir.name != fm_name and (primary_skills_dst / s_dir.name).is_dir() and (primary_skills_dst / fm_name).is_dir():
                shutil.rmtree(primary_skills_dst / s_dir.name, ignore_errors=True)
            target_dir_name = s_dir.name if (primary_skills_dst / s_dir.name).is_dir() else fm_name
            copy_clean_skill_dir(s_dir, primary_skills_dst / target_dir_name)
            skill_count += 1
        return {
            "repo": repo.name,
            "family": family,
            "architecture": "git-symlink-single-source",
            "rules_synced": rules_synced,
            "commands_synced": 0,
            "skills_synced": skill_count,
            "gitignore_fixed": gitignore_fixed,
        }

    agents_skills_dst = repo / ".agents" / "skills"
    cursor_skills_dst = repo / ".cursor" / "skills"
    agents_skills_dst.mkdir(parents=True, exist_ok=True)
    cursor_skills_dst.mkdir(parents=True, exist_ok=True)

    same_target = False
    try:
        same_target = agents_skills_dst.resolve() == cursor_skills_dst.resolve()
    except OSError:
        same_target = False

    legacy_agent_skills = repo / ".agent" / "skills"
    has_legacy = False
    try:
        has_legacy = legacy_agent_skills.is_dir() and legacy_agent_skills.resolve() != agents_skills_dst.resolve()
    except OSError:
        has_legacy = False

    # 僅移除「對立產業專屬技能」(excluded_skills) 與重複之 source-command-*，保留專案既有客製技能（如 seo-looping, openseo-*）
    cleanup_dirs = [agents_skills_dst]
    if not same_target:
        cleanup_dirs.append(cursor_skills_dst)
    if has_legacy:
        cleanup_dirs.append(legacy_agent_skills)
    for sub_dir in cleanup_dirs:
        for child in list(sub_dir.iterdir()):
            if (child.name in excluded_skills or child.name.startswith("source-command-")) and child.is_dir():
                shutil.rmtree(child, ignore_errors=True)

    skill_count = 0
    for s_dir in family_skills:
        dir_name = s_dir.name
        fm_name = read_frontmatter_name(s_dir / "SKILL.md")
        copy_clean_skill_dir(s_dir, agents_skills_dst / dir_name)
        if not same_target:
            copy_clean_skill_dir(s_dir, cursor_skills_dst / fm_name)
        if has_legacy:
            copy_clean_skill_dir(s_dir, legacy_agent_skills / dir_name)
        skill_count += 1

    # 若 .agents/skills 內還有專案自有客製技能（如 seo-looping, openseo-*），同步鏡像一份到實體 .cursor/skills
    if not same_target:
        for existing_dir in agents_skills_dst.iterdir():
            if existing_dir.is_dir() and (existing_dir / "SKILL.md").is_file():
                fm_name = read_frontmatter_name(existing_dir / "SKILL.md")
                if fm_name not in excluded_skills and not (cursor_skills_dst / fm_name).exists():
                    copy_clean_skill_dir(existing_dir, cursor_skills_dst / fm_name)

    # 5. 同步 .cursor/commands/*.md（讓 Cursor 輸入 `/` 直接跳出核心與產業專屬技能選單；保留既有 symlink 如 us3c-next）
    commands_dst = repo / ".cursor" / "commands"
    commands_synced = 0
    is_cmd_link = False
    try:
        is_cmd_link = commands_dst.is_symlink() or commands_dst.is_junction()
    except OSError:
        is_cmd_link = False

    if not is_cmd_link:
        commands_dst.mkdir(parents=True, exist_ok=True)
        allowed_cmds = SHARED_SLASH_COMMAND_SKILLS | (
            US3C_ONLY_SKILLS if family == "us3c" else STOREASY_ONLY_SKILLS
        )
        for old_cmd in list(commands_dst.glob("*.md")):
            if old_cmd.stem in excluded_skills:
                old_cmd.unlink(missing_ok=True)
        for s_dir in family_skills:
            fm_name = read_frontmatter_name(s_dir / "SKILL.md")
            if fm_name in allowed_cmds or s_dir.name in allowed_cmds:
                shutil.copy2(s_dir / "SKILL.md", commands_dst / f"{fm_name}.md")
                commands_synced += 1

    return {
        "repo": repo.name,
        "family": family,
        "rules_synced": rules_synced,
        "commands_synced": commands_synced,
        "skills_synced": skill_count,
        "gitignore_fixed": gitignore_fixed,
    }


def sync_local_cursor_user_dirs(global_skills: list[Path]) -> dict:
    """
    1. 修復本機 Windows ~/.cursor/skills 的 NTFS Directory Junction 陷阱，轉為真實實體目錄。
       不再把 SKILL.md 複製成 ~/.cursor/commands/*.md（會與同名 skill 在「/」選單重複）；
       並清除先前由本腳本產生、內容與 SKILL.md 完全相同的 command 副本（自訂 command 不動）。
    2. 同步至 Cursor 跨機雲端 AgentStore (`LOCALAPPDATA/Cursor/AgentStores/cursor_agent_stores/u*/files/skills`)，
       讓同一 Cursor 帳號在 `DESKTOP-N1NJDUH` 與 `YangPC` 之間自動雲端同步 User Skills。
    """
    GLOBAL_CURSOR_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CURSOR_RULES_DIR.mkdir(parents=True, exist_ok=True)
    for mdc in (HOME / ".gemini" / "cursor-rules").glob("*.mdc"):
        shutil.copy2(mdc, GLOBAL_CURSOR_RULES_DIR / mdc.name)

    removed_junctions = 0
    for item in list(GLOBAL_CURSOR_SKILLS_DIR.iterdir()):
        try:
            if item.is_junction():
                os.rmdir(item)
                removed_junctions += 1
            elif item.is_symlink() or item.is_file():
                item.unlink(missing_ok=True)
                removed_junctions += 1
        except OSError:
            pass

    valid_names: set[str] = set()
    for d in global_skills:
        fm = read_frontmatter_name(d / "SKILL.md")
        valid_names.add(fm)
        copy_clean_skill_dir(d, GLOBAL_CURSOR_SKILLS_DIR / fm)

    for child in list(GLOBAL_CURSOR_SKILLS_DIR.iterdir()):
        if child.name not in valid_names and child.is_dir():
            shutil.rmtree(child, ignore_errors=True)

    cmd_pruned = 0
    if GLOBAL_CURSOR_COMMANDS_DIR.is_dir():
        for d in global_skills:
            fm = read_frontmatter_name(d / "SKILL.md")
            twin = GLOBAL_CURSOR_COMMANDS_DIR / f"{fm}.md"
            try:
                if twin.is_file() and twin.read_bytes() == (d / "SKILL.md").read_bytes():
                    twin.unlink()
                    cmd_pruned += 1
            except OSError:
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
            store_skills_dir.mkdir(parents=True, exist_ok=True)
            for d in global_skills:
                fm = read_frontmatter_name(d / "SKILL.md")
                copy_clean_skill_dir(d, store_skills_dir / fm)
                agent_store_synced += 1

    return {
        "removed_junctions": removed_junctions,
        "user_cursor_skills": len(valid_names),
        "cursor_command_copies_pruned": cmd_pruned,
        "agent_store_skills_synced": agent_store_synced,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync industry-scoped rules & skills to repos for Cursor Cloud Agents")
    parser.add_argument("--repo", type=str, default="all", help="Repo name, 'storeasy', 'us3c', or 'all'")
    parser.add_argument("--rules-only", action="store_true", help="Fast mode: sync only .cursor/rules, AGENTS.md SSOT block, and scripts/")
    args = parser.parse_args()

    if args.repo == "all":
        target_names = ALL_MANAGED_REPOS
    elif args.repo == "storeasy":
        target_names = STOREASY_FAMILY_REPOS
    elif args.repo == "us3c":
        target_names = US3C_FAMILY_REPOS
    else:
        target_names = [args.repo]
    repos = [GITHUB_ROOT / name for name in target_names if (GITHUB_ROOT / name).is_dir()]

    global_skills = sorted(
        [
            d
            for d in GLOBAL_SKILLS_DIR.iterdir()
            if d.is_dir() and not d.is_junction() and (d / "SKILL.md").is_file()
        ],
        key=lambda x: x.name,
    )

    sync_ssot_rules_from_gemini_md()
    user_cursor_sync = {"mode": "rules_only"} if args.rules_only else sync_local_cursor_user_dirs(global_skills)

    results = []
    for repo in repos:
        results.append(sync_repo(repo, global_skills, rules_only=args.rules_only))

    print(
        json.dumps(
            {
                "total_master_skills": len(global_skills),
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
