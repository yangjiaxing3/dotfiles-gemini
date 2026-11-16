#!/usr/bin/env python3
"""CI helper: copy global skills into <target>/.agents/skills ONLY.

Used by .github/workflows/sync-skills-to-repos.yml. Never touches .cursor/ or .agent/.
Exit codes: 0 ok (changes may or may not exist), 3 target skipped (.agents is a symlink).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", ".unlighthouse", ".claude-plugin", ".github", "evals"}
SKIP_EXTS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".pkl", ".db", ".sqlite", ".zip", ".tar", ".gz"}
MAX_FILE_BYTES = 256 * 1024


def copy_clean(src: Path, dst: Path) -> int:
    n = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".bsk")]
        out = dst / Path(root).relative_to(src)
        for f in files:
            p = Path(root) / f
            if f.startswith(".") or p.suffix.lower() in SKIP_EXTS or p.stat().st_size > MAX_FILE_BYTES:
                continue
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out / f)
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="dotfiles-gemini/config/skills")
    ap.add_argument("--target", required=True, help="checked-out target repo root")
    ap.add_argument("--include", default="", help="comma list; empty = all global skills")
    ap.add_argument("--exclude", default="", help="comma list of skill dirs never written (opposite-industry skills)")
    a = ap.parse_args()

    src, target = Path(a.src), Path(a.target)
    agents = target / ".agents"
    if agents.is_symlink():
        print(f"SKIP: {agents} is a symlink (.agents -> .agent); refusing to write through it")
        return 3
    if (target / ".agents" / "skills").is_symlink():
        print("SKIP: .agents/skills is a symlink")
        return 3

    include = {x.strip() for x in a.include.split(",") if x.strip()}
    exclude = {x.strip() for x in a.exclude.split(",") if x.strip()}
    dst_root = agents / "skills"
    dst_root.mkdir(parents=True, exist_ok=True)

    all_skills = sorted(d for d in src.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
    chosen = [d for d in all_skills if (not include or d.name in include) and d.name not in exclude]
    missing = include - {d.name for d in all_skills}
    if missing:
        print(f"WARN: include names not found in global set: {sorted(missing)}")

    # Remove opposite-industry skills and duplicated source-command-* (same cleanup as the legacy script).
    for child in list(dst_root.iterdir()):
        if child.is_dir() and (child.name in exclude or child.name.startswith("source-command-")):
            shutil.rmtree(child, ignore_errors=True)

    files = 0
    for d in chosen:
        if (dst_root / d.name).exists():
            shutil.rmtree(dst_root / d.name)  # replace whole skill dir so deletions propagate
        files += copy_clean(d, dst_root / d.name)
    print(f"synced {len(chosen)} skills, {files} files -> {dst_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
