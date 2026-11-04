#!/usr/bin/env python3
"""
跨電腦 Antigravity 全域 Skills / Rules / Workflows 雙向同步工具 (Jiaxing PC <-> YangPC)

支援兩種同步通道：
1. GitHub 單一真相倉庫 (`https://github.com/yangjiaxing3/dotfiles-gemini.git` -> `~/.gemini`)
2. Dropbox 即時同步映像 (`Dropbox/Projects/antigravity-global-sync/`)

在來源電腦 (Jiaxing PC) 執行：
    python C:\\Users\\Jiaxing\\.gemini\\scripts\\sync_yangpc_antigravity.py --export

在目標電腦 (YangPC) 執行（任選其一）：
    方式 A (Dropbox 一鍵安裝)：雙擊執行 `Dropbox\\Projects\\antigravity-global-sync\\sync_to_yangpc.bat`
    方式 B (Git Pull + 套用)：
        git -C "$HOME\\.gemini" pull origin master
        python "$HOME\\.gemini\\scripts\\sync_yangpc_antigravity.py" --apply
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HOME = Path.home()
GEMINI_DIR = HOME / ".gemini"
CURSOR_DIR = HOME / ".cursor"

SKIP_DIRS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "__pycache__",
    ".unlighthouse",
    ".claude-plugin",
    ".github",
    "evals",
}
SKIP_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".pkl",
    ".db",
    ".sqlite",
    ".zip",
    ".tar",
    ".gz",
}
MAX_FILE_BYTES = 256 * 1024  # 256 KB 上限，避免大型二進位檔進入 Git / Dropbox


def copy_clean_tree(src_dir: Path, dst_dir: Path) -> int:
    """複製純淨目錄樹（排除 .venv、node_modules 與超大型二進位檔）。"""
    if not src_dir.is_dir():
        return 0
    copied = 0
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".bsk")]
        rel_root = Path(root).relative_to(src_dir)
        target_root = dst_dir / rel_root
        for f in files:
            if f.startswith(".") and f not in (".gitignore",):
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
            shutil.copy2(src_f, dst_f)
            copied += 1
    return copied


def adapt_home_paths_in_file(file_path: Path, target_home: Path) -> bool:
    """將文字設定檔中寫死的 C:\\Users\\Jiaxing 自動替換為目標電腦之家目錄（如 C:\\Users\\YangPC）。"""
    if not file_path.is_file() or file_path.suffix.lower() not in (".md", ".mdc", ".json", ".ps1"):
        return False
    target_home_str = str(target_home)
    if target_home_str.lower() == r"c:\users\jiaxing":
        return False
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        updated = content.replace(r"C:\Users\Jiaxing", target_home_str)
        updated = updated.replace("C:/Users/Jiaxing", target_home_str.replace("\\", "/"))
        updated = updated.replace("c:/Users/Jiaxing", target_home_str.replace("\\", "/"))
        updated = updated.replace(r"c:\Users\Jiaxing", target_home_str)
        if updated != content:
            file_path.write_text(updated, encoding="utf-8")
            return True
    except Exception:
        pass
    return False


def export_bundle(dropbox_sync_dir: Path) -> dict:
    """從當前電腦匯出完整全域 Skills / Rules / Workflows 至 ~/.gemini/cursor-rules 與 Dropbox 同步目錄。"""
    cursor_rules_mirror = GEMINI_DIR / "cursor-rules"
    cursor_rules_mirror.mkdir(parents=True, exist_ok=True)
    cursor_rules_count = 0
    if (CURSOR_DIR / "rules").is_dir():
        for mdc in (CURSOR_DIR / "rules").glob("*.mdc"):
            shutil.copy2(mdc, cursor_rules_mirror / mdc.name)
            cursor_rules_count += 1

    dropbox_sync_dir.mkdir(parents=True, exist_ok=True)
    # 1. 複製核心單檔
    for fname in ("GEMINI.md", "README.md", "WALKTHROUGH_SWARM_V3_AND_SKILLS.md", "settings.json", ".gitignore"):
        src_f = GEMINI_DIR / fname
        if src_f.is_file():
            shutil.copy2(src_f, dropbox_sync_dir / fname)

    # 2. 複製子資料夾
    sub_counts = {}
    for rel_sub in (
        "rules",
        "hooks",
        "scripts",
        "memory",
        "cursor-rules",
        "antigravity/global_workflows",
        "config/skills",
    ):
        src_sub = GEMINI_DIR / rel_sub
        dst_sub = dropbox_sync_dir / rel_sub
        if src_sub.is_dir():
            sub_counts[rel_sub] = copy_clean_tree(src_sub, dst_sub)

    # 3. 產生 YangPC 一鍵安裝批次檔與說明
    bat_content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "echo ============================================================\r\n"
        "echo [Antigravity Global Sync] 正在將全域 Skills 與 Rules 同步至本機 (%USERPROFILE%)...\r\n"
        "echo ============================================================\r\n"
        "where python >nul 2>nul\r\n"
        "if %ERRORLEVEL% EQU 0 (\r\n"
        "    python \"%~dp0scripts\\sync_yangpc_antigravity.py\" --apply --source \"%~dp0\"\r\n"
        ") else (\r\n"
        "    py -3 \"%~dp0scripts\\sync_yangpc_antigravity.py\" --apply --source \"%~dp0\"\r\n"
        ")\r\n"
        "echo.\r\n"
        "echo [完成] 請重新啟動 Antigravity / Cursor 以載入最新 217 個全域 Skills！\r\n"
        "pause\r\n"
    )
    (dropbox_sync_dir / "sync_to_yangpc.bat").write_text(bat_content, encoding="utf-8")

    return {
        "mode": "export",
        "cursor_rules_mirrored": cursor_rules_count,
        "dropbox_sync_dir": str(dropbox_sync_dir),
        "copied_files_by_subdir": sub_counts,
    }


def apply_bundle(source_dir: Path) -> dict:
    """在目標電腦（如 YangPC）將全域 Skills / Rules / Workflows 套用至 ~/.gemini、~/.gemini/antigravity 與 ~/.cursor。"""
    source_dir = source_dir.resolve()
    target_gemini = HOME / ".gemini"
    target_gemini.mkdir(parents=True, exist_ok=True)

    # 若來源不是 ~/.gemini 本身（例如從 Dropbox 執行），先複製至 ~/.gemini
    if source_dir != target_gemini.resolve():
        for fname in ("GEMINI.md", "README.md", "WALKTHROUGH_SWARM_V3_AND_SKILLS.md", "settings.json"):
            src_f = source_dir / fname
            if src_f.is_file():
                shutil.copy2(src_f, target_gemini / fname)
        for rel_sub in (
            "rules",
            "hooks",
            "scripts",
            "memory",
            "cursor-rules",
            "antigravity/global_workflows",
            "config/skills",
        ):
            src_sub = source_dir / rel_sub
            if src_sub.is_dir():
                copy_clean_tree(src_sub, target_gemini / rel_sub)

    # 確保 ~/.gemini/antigravity/skills 與 ~/.gemini/config/skills 100% 對齊
    cfg_skills = target_gemini / "config" / "skills"
    ag_skills = target_gemini / "antigravity" / "skills"
    ag_skills.mkdir(parents=True, exist_ok=True)
    skill_dirs = []
    if cfg_skills.is_dir():
        for s_dir in sorted(cfg_skills.iterdir()):
            if s_dir.is_dir() and not s_dir.is_junction() and (s_dir / "SKILL.md").is_file():
                copy_clean_tree(s_dir, ag_skills / s_dir.name)
                skill_dirs.append(s_dir)

    # 同步 Cursor 全域規則 (~/.cursor/rules/*.mdc)
    cursor_rules_src = target_gemini / "cursor-rules"
    cursor_rules_dst = HOME / ".cursor" / "rules"
    cursor_rules_dst.mkdir(parents=True, exist_ok=True)
    if cursor_rules_src.is_dir():
        for mdc in cursor_rules_src.glob("*.mdc"):
            shutil.copy2(mdc, cursor_rules_dst / mdc.name)

    # 自動適配目標電腦之家目錄路徑（例如 C:\Users\Jiaxing -> C:\Users\YangPC）
    adapted_files = 0
    for check_root in (
        target_gemini / "GEMINI.md",
        target_gemini / "settings.json",
        target_gemini / "rules",
        target_gemini / "hooks",
        target_gemini / "memory",
        target_gemini / "antigravity" / "global_workflows",
        cursor_rules_dst,
    ):
        if check_root.is_file():
            if adapt_home_paths_in_file(check_root, HOME):
                adapted_files += 1
        elif check_root.is_dir():
            for f in check_root.rglob("*"):
                if f.is_file() and adapt_home_paths_in_file(f, HOME):
                    adapted_files += 1

    # 呼叫 sync_skills_to_cloud_repos.py 內建之本機 Cursor 真實目錄同步與 sync_skills_to_agents.py
    scripts_dir = target_gemini / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    cursor_sync_info = {}
    try:
        import sync_skills_to_cloud_repos as sscr

        cursor_sync_info = sscr.sync_local_cursor_user_dirs(skill_dirs)
    except Exception as e:
        cursor_sync_info = {"error": str(e)}

    return {
        "mode": "apply",
        "target_home": str(HOME),
        "antigravity_config_skills": len(skill_dirs),
        "antigravity_internal_skills": len(skill_dirs),
        "home_paths_adapted": adapted_files,
        "cursor_user_sync": cursor_sync_info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync global Antigravity skills between Jiaxing PC and YangPC")
    parser.add_argument("--export", action="store_true", help="Export global skills to Dropbox & cursor-rules")
    parser.add_argument("--apply", action="store_true", help="Apply global skills to local Antigravity & Cursor")
    parser.add_argument(
        "--source",
        type=str,
        default=str(GEMINI_DIR),
        help="Source bundle directory when running --apply",
    )
    parser.add_argument(
        "--dropbox-dir",
        type=str,
        default=str(HOME / "Dropbox" / "Projects" / "antigravity-global-sync"),
        help="Dropbox target folder for --export",
    )
    args = parser.parse_args()

    if args.export:
        res = export_bundle(Path(args.dropbox_dir))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.apply:
        res = apply_bundle(Path(args.source))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
