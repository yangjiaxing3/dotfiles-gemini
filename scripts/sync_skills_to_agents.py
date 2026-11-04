"""把全域 skills（~/.gemini/config/skills）以 Directory Junction 鏡像到各智能體的使用者層級 skill 目錄。

單一真相來源：每個 skill 只有一份實體；其他位置都是 Junction，更新一處即全部同步。
  - Antigravity：直接讀 ~/.gemini/config/skills（不需鏡像）
  - Grok：~/.grok/config.toml 的 [skills].paths 已掛全域目錄（不需鏡像）
  - Cursor / Claude Code / Codex：鏡像到下方 TARGETS

規則：
  - 冪等：已指向正確目標的 Junction 略過。
  - 只新增或重導 Junction；同名「實體資料夾」一律不碰，只回報（例外類 skill 依此受保護）。
  - Junction 以 frontmatter `name` 命名（Cursor 以資料夾名為識別）。
  - 來源只取固定深度（避免穿越 skill 內的 .venv / node_modules）。

用法：python sync_skills_to_agents.py [--dry-run] [--prune]
  --prune  移除各目標中「由本腳本管理」且來源已不存在的失效 Junction
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

HOME = Path.home()
GLOBAL_SKILLS = HOME / ".gemini" / "config" / "skills"
PLUGIN_ROOT = HOME / ".gemini" / "config" / "plugins"
TARGETS = {
    "cursor": HOME / ".cursor" / "skills",
    "claude": HOME / ".claude" / "skills",
    "codex": HOME / ".codex" / "skills",
}
MANIFEST_NAME = ".antigravity-junctions.json"
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
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


def link_target(path: Path) -> str | None:
    return os.path.realpath(path) if (path.is_junction() or path.is_symlink()) else None


def sync_target(target_root: Path, sources: dict[str, Path], dry_run: bool, prune: bool) -> dict:
    report = {"created": 0, "already_ok": 0, "retargeted": [], "skipped_real_dir": [], "pruned": [], "errors": []}
    target_root.mkdir(parents=True, exist_ok=True)
    manifest_path = target_root / MANIFEST_NAME
    managed = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    for name, src in sorted(sources.items()):
        dest = target_root / name
        current = link_target(dest)
        if dest.exists() or current:
            if current is None:
                # 目的地就是唯一實體本身（例：claude-seo 系列實體在 ~/.claude/skills）
                if os.path.normcase(os.path.realpath(dest)) == os.path.normcase(str(src)):
                    report["already_ok"] += 1
                    continue
                report["skipped_real_dir"].append(name)
                continue
            if os.path.normcase(current) == os.path.normcase(str(src)):
                report["already_ok"] += 1
                managed[name] = str(src)
                continue
            if not dry_run:
                os.rmdir(dest)  # 只移除 Junction 本身，不碰目標內容
            report["retargeted"].append(name)
        if not dry_run:
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(dest), str(src)], capture_output=True, text=True)
            if r.returncode != 0:
                report["errors"].append({"name": name, "stderr": r.stderr.strip()})
                continue
        managed[name] = str(src)
        report["created"] += 1

    if prune:
        for name in list(managed):
            dest = target_root / name
            if name not in sources and link_target(dest) and not Path(os.path.realpath(dest)).exists():
                if not dry_run:
                    os.rmdir(dest)
                report["pruned"].append(name)
                managed.pop(name)

    if not dry_run:
        manifest_path.write_text(json.dumps(managed, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune", action="store_true")
    args = parser.parse_args()

    sources, problems = collect_sources()
    result = {"sources": len(sources), "problems": problems}
    for label, root in TARGETS.items():
        result[label] = sync_target(root, sources, args.dry_run, args.prune)
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
