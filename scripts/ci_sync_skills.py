#!/usr/bin/env python3
"""CI helper: copy global skills into <target>/.agents/skills ONLY.

Used by .github/workflows/sync-skills-to-repos.yml. Never touches .cursor/ or .agent/.
Exit codes: 0 ok (changes may or may not exist), 3 target skipped (.agents is a symlink).
"""
from __future__ import annotations

import argparse
import fnmatch
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

# Basename patterns the dotfiles-gemini .gitignore keeps out of config/skills (mirror of its rules).
GITIGNORED_PATTERNS = ["package-lock.json", ".env", ".env.*", "*.pem", "*.key", "*.pfx", "*.p12", "*.sqlite", "*.db",
                       "*.pyc", "*.pyo", "*.zip", "*.gz", "*.tar", "*.mp4", "credentials*", "secrets*"]


def protected_in_target(rel: Path, size: int) -> bool:
    """True if a target-only file could never have come from the sync, so it must never be deleted."""
    if any(part in SKIP_DIRS or part.startswith(".bsk") for part in rel.parts[:-1]):
        return True
    name = rel.name
    if name.startswith(".") or Path(name).suffix.lower() in SKIP_EXTS or size > MAX_FILE_BYTES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in GITIGNORED_PATTERNS)


def sync_skill(src: Path, dst: Path) -> tuple[int, int]:
    """Copy eligible files src -> dst (overwrite). Delete a dst file only if it is absent from src
    AND it would have been eligible to sync. Skipped-by-size/ext/.gitignore files are left untouched."""
    copied = copy_clean(src, dst)
    deleted = 0
    if dst.is_dir():
        for p in sorted(dst.rglob("*"), reverse=True):
            rel = p.relative_to(dst)
            if p.is_file():
                if (src / rel).exists() or protected_in_target(rel, p.stat().st_size):
                    continue
                p.unlink()
                deleted += 1
            elif p.is_dir() and not any(p.iterdir()):
                p.rmdir()
    return copied, deleted


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

    files = removed = 0
    for d in chosen:
        c, r = sync_skill(d, dst_root / d.name)
        files += c
        removed += r
    print(f"synced {len(chosen)} skills, {files} files copied, {removed} stale files removed -> {dst_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
