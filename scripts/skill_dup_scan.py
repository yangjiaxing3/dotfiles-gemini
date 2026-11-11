#!/usr/bin/env python3
"""找出同名出現在多個「/」選單來源的 skill / command / workflow / rule，並依工具分組統計。
用法：python skill_dup_scan.py
"""
import os, re
from collections import Counter
from pathlib import Path
H = Path.home()
def fm(p):
    try:
        m = re.search(r'^name:\s*["\']?([^\r\n"\']+)', p.read_text('utf-8', errors='ignore')[:2000], re.M)
        return m.group(1).strip() if m else None
    except Exception: return None
def skills(d):
    return {(fm(s / 'SKILL.md') or s.name).lower() for s in d.iterdir() if s.is_dir() and (s / 'SKILL.md').is_file()} if d.is_dir() else set()
def mds(d, ext=('.md',)):
    return {f.stem.lower() for f in d.iterdir() if f.is_file() and f.suffix in ext} if d.is_dir() else set()
TOOLS = {
    'Antigravity': {'config/skills': skills(H/'.gemini/config/skills'), 'antigravity/skills(legacy)': skills(H/'.gemini/antigravity/skills'),
                    'global_workflows': mds(H/'.gemini/antigravity/global_workflows'), 'antigravity-ide/workflows': mds(H/'.gemini/antigravity-ide/global_workflows')},
    'Cursor': {'~/.cursor/skills': skills(H/'.cursor/skills'), '~/.cursor/commands': mds(H/'.cursor/commands'), '~/.cursor/rules': mds(H/'.cursor/rules', ('.mdc', '.md')),
               '~/.agents/skills': skills(H/'.agents/skills'), '~/.claude/skills(第三方匯入)': skills(H/'.claude/skills'), '~/.codex/skills(第三方匯入)': skills(H/'.codex/skills')},
    'Cursor(關閉第三方匯入後)': {'~/.cursor/skills': skills(H/'.cursor/skills'), '~/.cursor/commands': mds(H/'.cursor/commands'), '~/.agents/skills': skills(H/'.agents/skills')},
    'Codex': {'~/.codex/skills': skills(H/'.codex/skills'), '~/.agents/skills': skills(H/'.agents/skills')},
    'Claude': {'~/.claude/skills': skills(H/'.claude/skills'), '~/.claude/commands': mds(H/'.claude/commands')},
}
for tool, srcs in TOOLS.items():
    names = {}
    for k, v in srcs.items():
        for n in v: names.setdefault(n, []).append(k)
    d = {n: s for n, s in names.items() if len(s) > 1}
    print(f"[{tool}] 來源數量:", {k: len(v) for k, v in srcs.items()}, "| 重複名稱數:", len(d))
    for p, c in Counter(tuple(s) for s in d.values()).most_common(4): print("   ", c, "x", " + ".join(p))
