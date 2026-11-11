#!/usr/bin/env python3
"""找出同名出現在多個「/」選單來源的 skill / command / workflow / rule，並依工具分組統計。
用法：python skill_dup_scan.py [--workspaces] [--prune-workflows REPO[,REPO...]]
  --workspaces        另掃 ~/Documents/GitHub/* 的 .agent(s)/workflows 與同名 skill（唯讀）
  --prune-workflows   只刪指定 repo 內「與 skill 同名」的 .agent(s)/workflows/*.md（工作樹刪除，不 commit；請先自行備份）
"""
import sys
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


def workspace_scan(prune=None):
    root = H / 'Documents' / 'GitHub'
    glob = skills(H/'.gemini/config/skills') | {p.name.lower() for p in (H/'.gemini/config/skills').iterdir() if p.is_dir()} if (H/'.gemini/config/skills').is_dir() else set()
    tot = 0
    print("\n[Workspace] repo | workflows twins(同名 skill) | .agent+.agents/skills 同名重複 | .cursor/commands")
    for repo in sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        local = set()
        for s in ('.agent/skills', '.agents/skills', '.cursor/skills'): local |= skills(repo/s)
        names = glob | local
        twins = 0
        for wd in ('.agent/workflows', '.agents/workflows'):
            d = repo / wd
            if not d.is_dir(): continue
            for f in list(d.glob('*.md')):
                if f.stem.lower() in names:
                    twins += 1
                    if prune is not None and repo.name in prune: f.unlink()
        both = len(skills(repo/'.agent/skills') & skills(repo/'.agents/skills'))
        cmds = len(mds(repo/'.cursor/commands'))
        if twins or both or cmds:
            print(f"  {repo.name:28s} twins={twins:3d} agent∩agents skills={both:3d} commands={cmds:3d}" + ("  [已刪 twins]" if prune is not None and repo.name in prune and twins else ""))
        tot += twins
    print("  workflow twins 合計:", tot)

if '--workspaces' in sys.argv or '--prune-workflows' in sys.argv:
    pr = None
    if '--prune-workflows' in sys.argv:
        i = sys.argv.index('--prune-workflows'); pr = set(sys.argv[i+1].split(',')) if i+1 < len(sys.argv) else set()
    workspace_scan(pr)
