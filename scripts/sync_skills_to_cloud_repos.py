#!/usr/bin/env python3
"""
將本地全域 Rules 與 Skills（含最新 Lean-Triad、Ponytail、雙產業感知 Role-Scoped 技能矩陣、確定性路由器）
依「產業家族 (Storeasy 迷你倉家族 vs US3C 二手 3C 家族)」一鍵分流同步至專案 Git 倉庫與 Cursor Cloud Agents 結構。

解決痛點：
1. Cursor Cloud Agents 運行於雲端隔離 Linux 容器 (/workspace)，無法讀取本機 Windows 之
   `C:\\Users\\Jiaxing\\.gemini\\` 或 NTFS Directory Junctions。
2. 雙產業專屬隔離（Industry-Scoped Skill & Rule Partitioning）：
   - Storeasy 迷你倉家族僅安裝「通用底座 + Storeasy 專屬技能與規則」，絕不混入二手 3C 回收技能。
   - US3C 二手 3C 家族僅安裝「通用底座 + US3C 專屬技能與規則」，絕不混入迷你倉排櫃與每材實收技能。
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
    if repo_name in US3C_FAMILY_REPOS or "us3c" in repo_name.lower() or "imcheck" in repo_name.lower():
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
    """建立或更新 .cursor/environment.json 供 Cursor Cloud Agents 啟動時自動執行 bootstrap。"""
    env_json_path = repo / ".cursor" / "environment.json"
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


def sync_repo(repo: Path, global_skills: list[Path]) -> dict:
    family = get_repo_family(repo.name)
    excluded_skills = STOREASY_ONLY_SKILLS if family == "us3c" else US3C_ONLY_SKILLS
    excluded_rules = STOREASY_ONLY_RULES if family == "us3c" else US3C_ONLY_RULES

    for rel in (".agents", ".cursor", ".cursor/skills", ".cursor/rules", ".cursor/commands", ".agents/skills"):
        p = repo / rel
        try:
            if (p.is_file() or p.is_symlink()) and not p.is_dir():
                p.unlink(missing_ok=True)
        except OSError:
            pass

    gitignore_fixed = ensure_gitignore_allows_cloud_skills(repo)

    # 1. 依產業家族同步 .cursor/rules/*.mdc，並清理另一產業之專屬規則檔
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
            shutil.copy2(src_f, scripts_dst / fname)

    # 3. 同步 .cursor/environment.json
    ensure_cursor_environment_json(repo)

    # 4. 依產業家族過濾並同步專屬 Skills 至 .agents/skills 與 .cursor/skills
    family_skills = []
    for d in global_skills:
        dir_name = d.name
        fm_name = read_frontmatter_name(d / "SKILL.md")
        if dir_name in excluded_skills or fm_name in excluded_skills:
            continue
        family_skills.append(d)

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

    valid_dir_names = {d.name for d in family_skills}
    valid_fm_names = {read_frontmatter_name(d / "SKILL.md") for d in family_skills}
    cleanup_pairs = [(agents_skills_dst, valid_dir_names)]
    if not same_target:
        cleanup_pairs.append((cursor_skills_dst, valid_fm_names | valid_dir_names))
    if has_legacy:
        cleanup_pairs.append((legacy_agent_skills, valid_dir_names))
    for sub_dir, allowed in cleanup_pairs:
        for child in list(sub_dir.iterdir()):
            if child.name not in allowed and child.is_dir():
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
            if old_cmd.stem not in allowed_cmds:
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
    修復本機 Windows ~/.cursor/skills 的 NTFS Directory Junction 陷阱：
    Node.js fs.readdirSync(..., { withFileTypes: true }) 對 Windows Junction 回傳 dirent.isDirectory() === false，
    導致 Cursor 桌面端忽略所有 Junction 技能！此函式將 ~/.cursor/skills 轉為真實實體目錄，並同步 ~/.cursor/commands/*.md。
    """
    GLOBAL_CURSOR_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CURSOR_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)

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

    allowed_cmds = SHARED_SLASH_COMMAND_SKILLS | STOREASY_ONLY_SKILLS | US3C_ONLY_SKILLS
    cmd_count = 0
    for d in global_skills:
        fm = read_frontmatter_name(d / "SKILL.md")
        if fm in allowed_cmds or d.name in allowed_cmds:
            shutil.copy2(d / "SKILL.md", GLOBAL_CURSOR_COMMANDS_DIR / f"{fm}.md")
            cmd_count += 1

    return {
        "removed_junctions": removed_junctions,
        "user_cursor_skills": len(valid_names),
        "user_cursor_commands": cmd_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync industry-scoped rules & skills to repos for Cursor Cloud Agents")
    parser.add_argument("--repo", type=str, default="all", help="Repo name, 'storeasy', 'us3c', or 'all'")
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

    user_cursor_sync = sync_local_cursor_user_dirs(global_skills)

    results = []
    for repo in repos:
        results.append(sync_repo(repo, global_skills))

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
