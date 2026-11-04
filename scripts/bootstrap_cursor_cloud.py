#!/usr/bin/env python3
"""
Cursor Cloud Agents 容器啟動自動掛載腳本 (scripts/bootstrap_cursor_cloud.py)

當 Cursor Cloud Agent 在雲端隔離 Linux 容器 (/workspace) 啟動時：
1. 自動將當前專案內的 `.agents/skills` (或 `.cursor/skills`) 掛載/鏡像至容器內的：
   - `~/.cursor/skills`
   - `~/.gemini/config/skills`
   - `.cursor/skills`
2. 自動將當前專案內的 `.cursor/rules` 掛載/鏡像至容器內的 `~/.cursor/rules`。
3. 自動將當前專案內的 `scripts/skill_router.py`、`scripts/multi_model_gate.py`、`scripts/skill_eval_dataset.json`
   鏡像至 `~/.gemini/scripts/`。

如此一來，無論 Prompt、Rule 或 Agent 呼叫的是專案相對路徑 (`scripts/skill_router.py`、`.cursor/skills/`)
還是全域路徑 (`~/.gemini/scripts/skill_router.py`、`~/.cursor/skills/`)，在雲端容器與本機皆 100% 暢通！
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
HOME = Path.home()


def _safe_link_or_copy_dir(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    try:
        if os.path.realpath(src) == os.path.realpath(dst) and dst.exists():
            return
    except OSError:
        pass
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.is_file():
        dst.unlink(missing_ok=True)
    if not dst.exists():
        try:
            os.symlink(src, dst, target_is_directory=True)
            return
        except OSError:
            pass
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if target.exists():
            continue
        try:
            os.symlink(item, target, target_is_directory=item.is_dir())
        except OSError:
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            elif item.is_file():
                shutil.copy2(item, target)


def main() -> None:
    repo_skills = REPO_ROOT / ".agents" / "skills"
    if not repo_skills.is_dir():
        repo_skills = REPO_ROOT / ".cursor" / "skills"

    if repo_skills.is_dir():
        _safe_link_or_copy_dir(repo_skills, REPO_ROOT / ".cursor" / "skills")
        _safe_link_or_copy_dir(repo_skills, HOME / ".cursor" / "skills")
        _safe_link_or_copy_dir(repo_skills, HOME / ".gemini" / "config" / "skills")

    repo_rules = REPO_ROOT / ".cursor" / "rules"
    if repo_rules.is_dir():
        _safe_link_or_copy_dir(repo_rules, HOME / ".cursor" / "rules")

    gemini_scripts = HOME / ".gemini" / "scripts"
    gemini_scripts.mkdir(parents=True, exist_ok=True)
    for fname in ("skill_router.py", "multi_model_gate.py", "skill_eval_dataset.json", "bootstrap_cursor_cloud.py"):
        src_f = SCRIPT_DIR / fname
        dst_f = gemini_scripts / fname
        if src_f.is_file():
            try:
                if os.path.realpath(src_f) != os.path.realpath(dst_f):
                    shutil.copy2(src_f, dst_f)
            except OSError:
                pass

    print(f"[CursorCloudBootstrap] Ready: repo={REPO_ROOT.name}, skills={repo_skills}")


if __name__ == "__main__":
    main()
