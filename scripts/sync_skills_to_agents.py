"""把全域 skills（~/.gemini/config/skills）以「實體副本」同步到 Claude Code / Codex 各自的使用者層級 skill 目錄。

原則：Antigravity（~/.gemini/config/skills）是唯一管理 skills 的地方；
  - Antigravity：直接讀 ~/.gemini/config/skills（不鏡像到 ~/.gemini/antigravity/skills）
  - Cursor：由 sync_skills_to_cloud_repos.sync_local_cursor_user_dirs 同步實體副本到 ~/.cursor/skills
  - Claude Code / Codex：本腳本同步實體副本到 TARGETS（不再使用 Directory Junction）
  - Grok：~/.grok/config.toml 的 [skills].paths 已掛全域目錄（不需同步）

規則：
  - 副本以 frontmatter `name` 命名，內容為過濾後的輕量複製（排除 .venv、node_modules、>256KB、副檔名黑名單、點檔）。
  - 由本腳本管理的副本（記錄在 .antigravity-junctions.json，mode=copy）每次整份重建；
  - 目的地若是 Junction/Symlink 且名稱在來源內：只移除連結本身（不碰目標內容），改放實體副本；
  - 目的地若是「非本腳本管理的實體資料夾」（例：claude-seo 系列、ponytail*）一律不碰，只回報。
  - 來源只取固定深度（避免穿越 skill 內的 .venv / node_modules）。

用法：python sync_skills_to_agents.py [--dry-run] [--prune]
  --prune  移除各目標中「由本腳本管理」且來源已不存在的副本
"""
import argparse
import json
import os
import re
import shutil
from pathlib import Path

HOME = Path.home()
GLOBAL_SKILLS = HOME / ".gemini" / "config" / "skills"
PLUGIN_ROOT = HOME / ".gemini" / "config" / "plugins"
TARGETS = {
    "claude": HOME / ".claude" / "skills",
    "codex": HOME / ".codex" / "skills",
}
MANIFEST_NAME = ".antigravity-junctions.json"  # 檔名沿用舊版以相容；內容改記 {"name": {"src":..., "mode":"copy"}}
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", ".unlighthouse", ".claude-plugin", ".github", "evals"}
SKIP_EXTS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".pkl", ".db", ".sqlite", ".zip", ".tar", ".gz"}
MAX_FILE_BYTES = 256 * 1024
# 固定深度：頂層 skill、容器型 skill（taste-skill/skills/*）、plugin skill
SOURCE_PATTERNS = [(GLOBAL_SKILLS, "*/SKILL.md"), (GLOBAL_SKILLS, "*/skills/*/SKILL.md"),
                   (PLUGIN_ROOT, "*/skills/SKILL.md"), (PLUGIN_ROOT, "*/skills/*/SKILL.md")]


def read_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
    if not text.startswith("---"):
        return ""
    m = re.search(r"(?m)^name:\s*(.*)$", text[: text.find("\n---", 3)])
    return m.group(1).strip().strip("'\"") if m else ""


def collect_sources() -> tuple[dict[str, Path], list[dict]]:
    """回傳 {skill_name: 實體路徑}；頂層優先於巢狀，先到先得。"""
    chosen: dict[str, Path] = {}
    problems: list[dict] = []
    for root, pattern in SOURCE_PATTERNS:
        if not root.exists():
            continue
        for skill_md in sorted(root.glob(pattern)):
            name = read_name(skill_md)
            real = Path(os.path.realpath(skill_md.parent))
            if not NAME_RE.match(name):
                problems.append({"dir": str(skill_md.parent), "name": name, "reason": "invalid_name"})
            elif name in chosen:
                if os.path.normcase(str(chosen[name])) != os.path.normcase(str(real)):
                    problems.append({"dir": str(skill_md.parent), "name": name, "reason": f"duplicate_of:{chosen[name]}"})
            else:
                chosen[name] = real
    return chosen, problems


def is_link(path: Path) -> bool:
    return path.is_junction() or path.is_symlink()


def copy_skill(src_dir: Path, dst_dir: Path) -> int:
    copied = 0
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".bsk")]
        target_root = dst_dir / Path(root).relative_to(src_dir)
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
            shutil.copy2(src_f, target_root / f)
            copied += 1
    return copied


def remove_link(path: Path) -> None:
    if path.is_junction():
        os.rmdir(path)  # 只移除 Junction 本身，不碰目標內容
    else:
        path.unlink()


def sync_target(target_root: Path, sources: dict[str, Path], dry_run: bool, prune: bool) -> dict:
    report = {"copied": 0, "links_replaced": 0, "skipped_real_dir": [], "pruned": [], "errors": []}
    target_root.mkdir(parents=True, exist_ok=True)
    manifest_path = target_root / MANIFEST_NAME
    try:
        old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    except (OSError, ValueError):
        old = {}
    managed = {k: v for k, v in old.items() if isinstance(v, dict) and v.get("mode") == "copy"}

    for name, src in sorted(sources.items()):
        dest = target_root / name
        try:
            if is_link(dest):
                if not dry_run:
                    remove_link(dest)
                report["links_replaced"] += 1
            elif dest.exists():
                if name not in managed:
                    report["skipped_real_dir"].append(name)
                    continue
                if not dry_run:
                    shutil.rmtree(dest)
            if not dry_run:
                copy_skill(src, dest)
            managed[name] = {"src": str(src), "mode": "copy"}
            report["copied"] += 1
        except OSError as e:
            report["errors"].append({"name": name, "error": str(e)})

    if prune:
        for name in list(managed):
            if name not in sources:
                dest = target_root / name
                if dest.exists() and not dry_run:
                    shutil.rmtree(dest, ignore_errors=True)
                report["pruned"].append(name)
                managed.pop(name)

    if not dry_run:
        manifest_path.write_text(json.dumps(managed, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def run(dry_run: bool = False, prune: bool = False) -> dict:
    sources, problems = collect_sources()
    result = {"sources": len(sources), "problems": problems}
    for label, root in TARGETS.items():
        if not root.parent.exists():  # 該工具未安裝（例如沒有 ~/.codex）就不建立目錄
            result[label] = {"skipped": f"{root.parent} 不存在"}
            continue
        result[label] = sync_target(root, sources, dry_run, prune)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.dry_run, args.prune), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
