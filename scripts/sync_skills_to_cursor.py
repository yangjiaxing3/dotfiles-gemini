"""將 Antigravity 的 skills 以 Directory Junction 鏡像到 Cursor 原生 skill 目錄 (~/.cursor/skills)。

設計原則：
- 單一真相來源：不複製檔案，Junction 指回 ~/.gemini/config/skills，更新一處即全域同步。
- 冪等：已存在且指向相同目標的 Junction 直接略過；可重複執行。
- 附加且不破壞：若 ~/.cursor/skills 已有同名「實體資料夾」，絕不覆寫，只回報。
- Junction 以 frontmatter `name` 命名，因為 Cursor 以資料夾名作為 skill 識別。
- Antigravity 內建 skills（builtin）依賴 Antigravity 專屬工具/UI，不鏡像。

用法：python sync_skills_to_cursor.py [--dry-run] [--prune]
  --prune  移除 ~/.cursor/skills 中指向已不存在來源的失效 Junction
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

HOME = Path.home()
CURSOR_SKILLS = HOME / ".cursor" / "skills"
GLOBAL_SKILLS = HOME / ".gemini" / "config" / "skills"
PLUGIN_ROOT = HOME / ".gemini" / "config" / "plugins"
MANIFEST = CURSOR_SKILLS / ".antigravity-junctions.json"
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
SKIP_PARTS = {".venv", "node_modules", ".git"}


def read_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    for line in text[3:end].splitlines():
        m = re.match(r"^name:\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("'\"")
    return ""


def collect_sources() -> tuple[dict, list]:
    """回傳 {skill_name: source_dir} 與衝突/無效清單。頂層優先於巢狀，先到先得。"""
    chosen: dict[str, Path] = {}
    problems = []
    candidates = []
    for root in (GLOBAL_SKILLS, PLUGIN_ROOT):
        if not root.exists():
            continue
        for skill_md in root.rglob("SKILL.md"):
            if SKIP_PARTS & set(skill_md.relative_to(root).parts):
                continue
            depth = len(skill_md.relative_to(root).parts)
            candidates.append((0 if root == GLOBAL_SKILLS else 1, depth, str(skill_md), skill_md))
    for _, _, _, skill_md in sorted(candidates):
        name = read_name(skill_md)
        if not NAME_RE.match(name):
            problems.append({"dir": str(skill_md.parent), "name": name, "reason": "invalid_name"})
            continue
        if name in chosen:
            problems.append({"dir": str(skill_md.parent), "name": name, "reason": f"duplicate_of:{chosen[name]}"})
            continue
        chosen[name] = skill_md.parent
    return chosen, problems


def junction_target(path: Path) -> str | None:
    try:
        if path.is_junction():
            return os.path.realpath(path)
    except OSError:
        return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune", action="store_true")
    args = parser.parse_args()

    CURSOR_SKILLS.mkdir(parents=True, exist_ok=True)
    sources, problems = collect_sources()
    report = {"created": [], "already_ok": [], "skipped_existing_real_dir": [], "retargeted": [], "pruned": [], "problems": problems}

    for name, src in sorted(sources.items()):
        dest = CURSOR_SKILLS / name
        src_real = os.path.realpath(src)
        if dest.exists() or dest.is_junction():
            current = junction_target(dest)
            if current is None:
                report["skipped_existing_real_dir"].append(name)
                continue
            if os.path.normcase(current) == os.path.normcase(src_real):
                report["already_ok"].append(name)
                continue
            # NOTE: 只會重導「Junction」，實體資料夾永遠不碰
            if not args.dry_run:
                os.rmdir(dest)
            report["retargeted"].append(name)
        if not args.dry_run:
            res = subprocess.run(["cmd", "/c", "mklink", "/J", str(dest), src_real], capture_output=True, text=True)
            if res.returncode != 0:
                report["problems"].append({"dir": src_real, "name": name, "reason": f"mklink_failed:{res.stderr.strip()}"})
                continue
        report["created"].append(name)

    if args.prune:
        for child in CURSOR_SKILLS.iterdir():
            if child.is_junction() and not Path(os.path.realpath(child)).exists():
                if not args.dry_run:
                    os.rmdir(child)
                report["pruned"].append(child.name)

    if not args.dry_run:
        managed = {n: str(p) for n, p in sources.items() if junction_target(CURSOR_SKILLS / n)}
        MANIFEST.write_text(json.dumps(managed, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({k: (len(v) if k in ("already_ok", "created") else v) for k, v in report.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
