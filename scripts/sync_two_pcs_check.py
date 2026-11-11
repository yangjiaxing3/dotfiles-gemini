#!/usr/bin/env python3
"""兩台電腦 skills / rules 一致性檢查。
用法：
  python sync_two_pcs_check.py manifest <out.json>      # 在每台電腦各跑一次
  python sync_two_pcs_check.py compare <a.json> <b.json> # 比對（路徑 C:\\Users\\<home> 與 CRLF 先正規化）
"""
import hashlib, json, os, re, sys
from pathlib import Path
HOME = Path.home()
SKIP = {".venv", "venv", "node_modules", ".git", "__pycache__", ".unlighthouse", ".claude-plugin", ".github"}
TEXT = {".md", ".mdc", ".json", ".ps1", ".py", ".ts", ".tsx", ".js", ".css", ".txt", ".yml", ".yaml", ".html", ".svg", ".sh", ".mjs", ".jsx", ".mdx", ".sql", ".toml", ".jsonc"}
ROOTS = {
    "gemini/config/skills": HOME / ".gemini/config/skills",
    "gemini/antigravity/skills": HOME / ".gemini/antigravity/skills",
    "gemini/global_workflows": HOME / ".gemini/antigravity/global_workflows",
    "gemini/cursor-rules-mirror": HOME / ".gemini/cursor-rules",
    "cursor/rules": HOME / ".cursor/rules",
    "cursor/skills": HOME / ".cursor/skills",
    "gemini/GEMINI.md": HOME / ".gemini/GEMINI.md",
}
HOME_RE = re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]+(?:Jiaxing|" + re.escape(HOME.name.encode()) + rb")", re.I)
def norm(data, ext):
    """文字檔：CRLF->LF，並把 C:\\Users\\Jiaxing 與本機家目錄都視為 <HOME>（apply 只改寫部分副檔名，.py/.ts 內的寫死路徑屬預期差異）。"""
    if ext not in TEXT and b"\0" in data[:8192]: return data  # 二進位
    return HOME_RE.sub(b"<HOME>", data.replace(b"\r\n", b"\n"))
def sha(b): return hashlib.sha256(b).hexdigest()
def manifest():
    out = {"home": str(HOME), "files": {}}
    for key, root in ROOTS.items():
        files = [root] if root.is_file() else ([] if not root.exists() else
            [Path(d) / f for d, ds, fs in os.walk(root) if not ds.__setitem__(slice(None), [x for x in ds if x not in SKIP]) for f in fs])
        for p in files:
            try: raw = p.read_bytes()
            except OSError: continue
            rel = key if root.is_file() else key + "/" + p.relative_to(root).as_posix()
            out["files"][rel] = {"raw": sha(raw), "norm": sha(norm(raw, p.suffix.lower()))}
    return out
ROOT_KEYS = list(ROOTS)
def compare(a, b):
    A, B = a["files"], b["files"]
    groups = {}
    def g(k): return k.split("/")[0] + "/" + k.split("/")[1] if k.count("/") >= 1 else k
    for k in sorted(set(A) | set(B)):
        grp = next((r for r in sorted(ROOT_KEYS, key=len, reverse=True) if k == r or k.startswith(r + "/")), k)
        s = groups.setdefault(grp, {"A": 0, "B": 0, "same_raw": 0, "same_norm_only": 0, "diff": [], "only_A": [], "only_B": []})
        if k in A: s["A"] += 1
        if k in B: s["B"] += 1
        if k in A and k in B:
            if A[k]["raw"] == B[k]["raw"]: s["same_raw"] += 1
            elif A[k]["norm"] == B[k]["norm"]: s["same_norm_only"] += 1
            else: s["diff"].append(k)
        elif k in A: s["only_A"].append(k)
        else: s["only_B"].append(k)
    total_bad = 0
    for grp, s in groups.items():
        bad = len(s["diff"]) + len(s["only_A"]) + len(s["only_B"]); total_bad += bad
        print(f"{grp}: A={s['A']} B={s['B']} 完全相同={s['same_raw']} 僅路徑/換行差異={s['same_norm_only']} 內容不同={len(s['diff'])} 只在A={len(s['only_A'])} 只在B={len(s['only_B'])}")
        for k in s["diff"][:15]: print("   DIFF  ", k)
        for k in s["only_A"][:15]: print("   ONLY_A", k)
        for k in s["only_B"][:15]: print("   ONLY_B", k)
    print("剩餘差異總數:", total_bad)
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "manifest":
        Path(sys.argv[2]).write_text(json.dumps(manifest()), encoding="utf-8"); print("ok", sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "compare":
        sys.stdout.reconfigure(encoding="utf-8")
        compare(json.loads(Path(sys.argv[2]).read_text("utf-8")), json.loads(Path(sys.argv[3]).read_text("utf-8")))
    else: print(__doc__)