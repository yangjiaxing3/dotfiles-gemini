#!/usr/bin/env python3
"""Scale x Risk Tiered Change Gate (Tier 0-3) - pure stdlib."""
from __future__ import annotations

import argparse, datetime as dt, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any

MAX_SCAN_BYTES = 64 * 1024
FAKE_REQ_IDS = {"", "cursor-plan-delegated", "unknown", "none", "null", "n/a", "delegated"}
TIER_NUM = {f"{p}{i}": i for p in ("T", "S", "R") for i in range(4)}
HEX40_RE = re.compile(r"^[0-9a-fA-F]{40}$")

P1_SELF_SCRIPTS = re.compile(r"(?:^|/)(?:tier_gate|rule_lint|multi_model_gate|skill_router|sync_skills_to_cloud_repos|bootstrap_cursor_cloud)\.py$", re.I)
P1_PROTECTED = re.compile(
    r"(?:^|/)(?:GEMINI\.md|AGENTS\.md|DECISIONS\.md|vercel\.json|cross-repo-edges\.[^/]+|repo-registry\.[^/]+)$|(?:^|/)\.cursor/rules/[^/]+\.mdc$|(?:^|/)cursor-rules/[^/]+\.mdc$"
    r"|(?:^|/)\.agents?/skills/(?:stage-gate-review|verification-quality|phase-0-boundary-sentinel|boundary-sentinel)/SKILL\.md$|(?:^|/)docs/[^/]*contract[^/]*\.md$|(?:^|/)backend/app/models/|(?:^|/)\.github/", re.I)
KNOWN_MIRROR_SYMLINK = re.compile(r"^(?:\.agents(?:/|$)|\.cursor/(?:skills|commands)(?:/|$))", re.I)
P2_NOISE = re.compile(
    r"(?:^|/)(?:package-lock\.json|pnpm-lock\.yaml|yarn\.lock|uv\.lock|poetry\.lock)$|\.lock$|(?:^|/)(?:node_modules|\.venv|venv|dist|build|graphify-out|__pycache__)/|\.tsbuildinfo$|\.min\.(?:js|css)$"
    r"|(?:^|/)docs/diagrams/[^/]+\.(?:png|svg)$|(?:^|/)\.agents/|(?:^|/)\.cursor/(?:skills/|commands/|environment\.json$)|(?:^|/)\.agent/skills/", re.I)
SECRET_UNTRACKED = re.compile(r"(?:^|/)\.env(?:\.[^/]+)?$|\.(?:pem|key|p12|pfx)$|\.dpapi\.xml$|(?:^|/)[^/]*(?:secret|credential)[^/]*\.(?:env|json|yaml|yml|txt)$", re.I)
TEST_RE = re.compile(r"(?:^|/)(?:tests?|__tests__)/|(?:^|/)test_[^/]+\.py$|\.(?:test|spec)\.[jt]sx?$|(?:^|/)conftest\.py$", re.I)
PURE_DOC_RE = re.compile(r"\.(?:md|mdx|txt)$", re.I)
PURE_STYLE_RE = re.compile(r"\.(?:css|scss|less|svg|png|jpe?g|webp|ico|woff2?)$", re.I)
UI_VIEW_RE = re.compile(r"(?:^|/)src/(?:components|pages|views|layouts|styles|ui)/.*\.(?:tsx|jsx|css|scss)$|\.(?:tsx|jsx|d\.ts)$", re.I)
UI_3D_FILE_RE = re.compile(r"(?:3d|simulator|cad|canvas)", re.I)
UI_3D_OPS_RE = re.compile(r"\b(?:Math\.|Matrix|Vector|Raycaster|Box3|intersects|dxf)\b")
UI_R3_SEC_RE = re.compile(r"localStorage\.(?:get|set)Item\([^)]*token|jwtDecode|crypto\.subtle|\bHMAC\b|dangerouslySetInnerHTML")
UI_R2_IO_RE = re.compile(r"\b(?:fetch\(|axios\.|apiClient\.|new\s+FormData|postMessage\()")

R3_PATHS_GLOBAL = [
    ("R3:PATH_AUTH", re.compile(r"(?:^|/)(?:auth|security|rbac|middleware|oauth|jwt|crypto|secret|hmac|blacklist|requireauth)(?:[/_.-]|$)", re.I)),
    ("R3:PATH_SCHEMA", re.compile(r"(?:^|/)(?:migrations?|alembic|schema|turso|supabase|hrana)(?:[/_.-]|$)|turso_contract|create_turso_schema", re.I)),
    ("R3:MCP_OR_MEMORY_HUB", re.compile(r"memory[-_]?hub|mcp.*server|memory_hub_mcp", re.I)),
]
R3_PATHS_DOMAIN = [
    ("R3:PATH_FINANCE", re.compile(r"(?:pricing|auto_quote|calculator|financials|billing|invoice|payroll|finhr|reconcil|lease_?terms|supply_?ping|cabinet_?mix)", re.I)),
    ("R3:PATH_3D", re.compile(r"(?:3d|cad|dxf|bin_?pack|collision|raycast|fov|geometry|spatial)", re.I)),
]
R2_PATHS = [
    ("R2:PATH_API", re.compile(r"(?:^|/)(?:routers?|api|endpoints?|webhooks?|controllers?)/", re.I)),
    ("R2:PATH_EXT", re.compile(r"(?:^|/|_|-)(?:crawler|scraper|upload|import|export|proxy|r2|drive|line_oa|config|settings|env|cli|parser|indexer|mcp)(?:[/_.-]|$)", re.I)),
]
TOKEN_RE = re.compile(r"""('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`|/\*.*?\*/|(?:^|(?<=\s))(?://|#).*$)""")
R3_SQL_DDL = re.compile(r"\b(?:DROP|ALTER|TRUNCATE|CREATE)\s+TABLE\b|\bTRUNCATE\s+\w+", re.I)
R3_SQL_DEL = re.compile(r"\bDELETE\s+FROM\s+[`\"\[\]\w.]+", re.I)
R3_SQL_TAUT_WHERE = re.compile(r"\bWHERE\s+(?:1\s*=\s*1|true\b|'1'\s*=\s*'1'|\"1\"\s*=\s*\"1\")", re.I)
R3_AUTH_CODE = re.compile(r"\b(?:verify_signature|CryptProtectData|hmac\.|jwt\.|bcrypt|argon2|pbkdf2|hashlib\.|set_cookie|blacklist)\b")
R3_AUDIT_CODE = re.compile(r"\b(?:sha256|hash_chain|void_only)\b")
R3_FIN_CODE = re.compile(r"\b(?:net_rent|monthly_rent|rent_escalation|discount_rate|gross_margin|margin_rate|min_floor|deduction|auto_quote|buyout_price)\b")
R3_FIN_ZH = re.compile(r"只作廢不刪除|每坪租金|底限價|扣款")
R3_FIN_OP = re.compile(r"[+\-*/=<>]|Decimal|round\(|sum\(")
R3_3D_CODE = re.compile(r"\b(?:bin_?pack|bounding_?box|raycast|dxf|polyline|fov|quaternion|matrix4|intersectsBox|collision|(?:cabinet|storage|kiosk|unit)_slot)\b", re.I)
R2_CODE_IO = re.compile(r"\b(?:APIRouter|@router\.|sqlalchemy|sqlite3)\b|\.execute\(|\b(?:SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)\b", re.I)
ASSERT_RE = re.compile(r"\b(?:assert|expect\s*\(|pytest\.raises|assertEqual|assertTrue|assertFalse|assertRaises)\b")
TYPE_ONLY_LINE_RE = re.compile(r"^\s*(?:(?:export\s+)?(?:import\s+type\b|type\s+\w+|interface\s+\w+)|export\s+type\b|readonly\s+\w+|[\w?]+\s*:\s*[^(=;]+;?\s*$|//|\*|/\*|$)")
TYPE_FORBID_RE = re.compile(r"\(|\b(?:await|return|throw|new|fetch|axios|execute|DROP|TRUNCATE|DELETE|INSERT|UPDATE|crypto|HMAC)\b", re.I)
TIER_META = {
    "T0": (["ponytail"], ["rule_lint --git-diff", "existing-tests"]),
    "T1": (["ponytail", "tdd-workflow"], ["rule_lint --git-diff", "unit-tests-with-edge-case", "typecheck"]),
    "T2": (["ponytail-review", "verification-quality", "agency-engineering-code-reviewer"], ["rule_lint --git-diff", "multi_model_gate review", "independent-readonly-review", "real-data-spot-check", "adversarial-edge-cases>=5"]),
    "T3": (["stage-gate-review", "multi-agent-mode", "security-audit", "bughunter", "verification-quality", "ponytail-review"], ["rule_lint --git-diff", "multi_model_gate review --include-grok-api", "3-role-stage-gate-review", "real-corpus-audit", "fuzz-and-secret-scan"]),
}

def _norm(p: str) -> str:
    s = p.strip()
    return re.sub(r"^(?:\./)+", "", (s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s).replace("\\", "/")).lstrip("/")

def _safe_print(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode(sys.stdout.encoding or "utf-8", errors="replace")); sys.stdout.buffer.flush()

def _validate_ref(ref: str | None) -> str | None:
    s = (ref or "").strip()
    if not s: return None
    if any(p.strip().startswith("-") for p in re.split(r"\.{2,3}", s, maxsplit=1) if p.strip()):
        raise ValueError(f"Unsafe git ref starting with '-': {ref}")
    return s

def _run_git(repo_root: Path, args: list[str], binary: bool = False) -> tuple[int, Any]:
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=false", "-C", str(repo_root), *args], capture_output=True, text=not binary, encoding=None if binary else "utf-8", errors=None if binary else "replace", timeout=20)
        return r.returncode, r.stdout
    except (OSError, subprocess.SubprocessError):
        return 1, b"" if binary else ""

def resolve_git_common_dir(repo_root: Path) -> Path | None:
    rc, out = _run_git(Path(repo_root), ["rev-parse", "--git-common-dir"])
    if rc != 0 or not out.strip(): return None
    p = Path(out.strip())
    return (Path(repo_root) / p).resolve() if not p.is_absolute() else p.resolve()

def _default_pass_file(git_common_dir: Path | None, anchor: Path) -> Path:
    if git_common_dir is not None: return git_common_dir / "lean_triad_gate_pass.json"
    return Path.home() / ".gemini" / "state" / "gate_pass" / f"{anchor.name}_{hashlib.sha256(str(anchor.resolve()).lower().encode('utf-8')).hexdigest()[:10]}.json"

def _is_pure_type_ts(lines: list[str]) -> bool:
    return bool(lines) and all(TYPE_ONLY_LINE_RE.match(ln) and not TYPE_FORBID_RE.search(ln) for ln in lines)

def _classify(norm_path: str, is_symlink: bool = False, changed_lines: list[str] | None = None) -> tuple[str, bool]:
    if P1_SELF_SCRIPTS.search(norm_path): return "R3_PROTECTED", True
    if P1_PROTECTED.search(norm_path): return "R3_PROTECTED", False
    if (is_symlink and KNOWN_MIRROR_SYMLINK.search(norm_path)) or P2_NOISE.search(norm_path): return "HARD_NOISE", False
    for name, rx in (("TEST", TEST_RE), ("PURE_DOC", PURE_DOC_RE), ("PURE_STYLE", PURE_STYLE_RE), ("UI_VIEW", UI_VIEW_RE)):
        if rx.search(norm_path): return name, False
    if norm_path.lower().endswith(".ts") and changed_lines and _is_pure_type_ts(changed_lines): return "UI_VIEW", False
    return "DOMAIN_CALC_BACKEND", False

def _strip_tokens(line: str) -> tuple[str, str]:
    no_cmt, code, pos = [], [], 0
    for m in TOKEN_RE.finditer(line):
        seg, tok = line[pos:m.start()], m.group(0)
        no_cmt.append(seg); code.append(seg)
        no_cmt.append(tok if tok[0] in ("'", '"', "`") else " ")
        code.append('""' if tok[0] in ("'", '"', "`") else " ")
        pos = m.end()
    no_cmt.append(line[pos:]); code.append(line[pos:])
    return "".join(no_cmt), "".join(code)

def _scan_risk(norm_path: str, category: str, skip_self: bool, changed_lines: list[str]) -> tuple[int, list[str]]:
    if category == "R3_PROTECTED":
        return 3, [f"{'R3:GATE_SELF_MOD' if skip_self else 'R3:PROTECTED_ALLOWLIST'}:{norm_path}"]
    if category in ("HARD_NOISE", "PURE_DOC", "PURE_STYLE"):
        return 0, []
    reasons: list[str] = []
    risk = 0
    for tag, rx in R3_PATHS_GLOBAL:
        if rx.search(norm_path):
            risk, reasons = 3, reasons + [f"{tag}:{norm_path}"]
    if category == "UI_VIEW":
        risk = max(risk, 1 if changed_lines else 0)
        is_3d = bool(UI_3D_FILE_RE.search(norm_path))
        for raw in changed_lines:
            no_cmt, _ = _strip_tokens(raw)
            if not no_cmt.strip(): continue
            if R3_SQL_DDL.search(no_cmt) or (R3_SQL_DEL.search(no_cmt) and (not re.search(r"\bWHERE\b", no_cmt, re.I) or R3_SQL_TAUT_WHERE.search(no_cmt))):
                return 3, reasons + [f"R3:DESTRUCTIVE_SQL:{norm_path}"]
            if (is_3d and UI_3D_OPS_RE.search(no_cmt)) or UI_R3_SEC_RE.search(no_cmt):
                return 3, reasons + [f"R3:UI_SENSITIVE:{norm_path}"]
            if UI_R2_IO_RE.search(no_cmt) and risk < 2:
                risk, reasons = 2, reasons + [f"R2:UI_IO:{norm_path}"]
        return risk, reasons
    risk = max(risk, 1)
    for tag, rx in R3_PATHS_DOMAIN:
        if rx.search(norm_path): risk, reasons = 3, reasons + [f"{tag}:{norm_path}"]
    if risk < 2:
        for tag, rx in R2_PATHS:
            if rx.search(norm_path): risk, reasons = 2, reasons + [f"{tag}:{norm_path}"]
    if skip_self: return risk, reasons
    for raw in changed_lines:
        no_cmt, code = _strip_tokens(raw)
        if not no_cmt.strip(): continue
        if R3_SQL_DDL.search(no_cmt) or (R3_SQL_DEL.search(no_cmt) and (not re.search(r"\bWHERE\b", no_cmt, re.I) or R3_SQL_TAUT_WHERE.search(no_cmt))): return 3, reasons + [f"R3:DESTRUCTIVE_SQL:{norm_path}"]
        if R3_AUTH_CODE.search(code) or ("Authorization" in no_cmt and "Bearer" in no_cmt): return 3, reasons + [f"R3:AUTH_CODE:{norm_path}"]
        if R3_AUDIT_CODE.search(code) or R3_FIN_ZH.search(no_cmt): return 3, reasons + [f"R3:AUDIT_OR_FIN_ZH:{norm_path}"]
        if R3_FIN_CODE.search(code) and R3_FIN_OP.search(code): return 3, reasons + [f"R3:FIN_CALC:{norm_path}"]
        if R3_3D_CODE.search(code): return 3, reasons + [f"R3:3D_CALC:{norm_path}"]
        if risk < 2 and R2_CODE_IO.search(no_cmt): risk, reasons = 2, reasons + [f"R2:CODE_IO_SQL:{norm_path}"]
    return risk, reasons

def _parse_unified_diff(diff_text: str) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    cur: str | None = None
    in_hunk = False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            in_hunk = False
            m = re.match(r'^diff --git (?:"a/[^"]+"|a/.+?) (?:"b/([^"]+)"|b/(.+))$', line)
            cur = _norm(m.group(1) or m.group(2)) if m else None
            if cur:
                files.setdefault(cur, {"add": 0, "del": 0, "lines": [], "add_lines": [], "del_lines": [], "is_new": False, "is_del": False, "is_symlink": False})
        elif cur is None:
            continue
        elif not in_hunk and line.startswith(("+++ b/", '+++ "b/')):
            real = _norm(line[6:] if line.startswith("+++ b/") else line[7:-1])
            if real and real != cur:
                files[real] = files.pop(cur); cur = real
        elif not in_hunk and line.startswith(("new file mode ", "deleted file mode ")):
            files[cur]["is_new" if line.startswith("new") else "is_del"] = True
            files[cur]["is_symlink"] = files[cur]["is_symlink"] or ("120000" in line)
        elif not in_hunk and line.startswith(("old mode 120000", "new mode 120000", "index ")) and " 120000" in line:
            files[cur]["is_symlink"] = True
        elif line.startswith("@@ "):
            in_hunk = True
        elif in_hunk and line.startswith("+"):
            b = line[1:]; files[cur]["add"] += 1; files[cur]["lines"].append(b); files[cur]["add_lines"].append(b)
        elif in_hunk and line.startswith("-"):
            b = line[1:]; files[cur]["del"] += 1; files[cur]["lines"].append(b); files[cur]["del_lines"].append(b)
    return files

def _hash_stream_crlf_lf(path: Path) -> str:
    h, prev_cr = hashlib.sha256(), False
    with path.open("rb") as fh:
        while chunk := fh.read(65536):
            if prev_cr: chunk, prev_cr = b"\r" + chunk, False
            if chunk.endswith(b"\r"): prev_cr, chunk = True, chunk[:-1]
            h.update(chunk.replace(b"\r\n", b"\n"))
    if prev_cr: h.update(b"\r")
    return h.hexdigest()

def _hash_snapshot(repo_root: Path | None, rel_or_abs: str, *, staged: bool, head_ref: str | None, is_del: bool) -> str:
    if is_del: return "DELETED"
    if repo_root is not None and (head_ref or staged):
        rc, data = _run_git(repo_root, ["show", f"{head_ref}:{rel_or_abs}" if head_ref else f":{rel_or_abs}"], binary=True)
        return "DELETED" if rc != 0 else hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
    p = Path(rel_or_abs) if Path(rel_or_abs).is_absolute() else ((repo_root or Path.cwd()) / rel_or_abs)
    try: return _hash_stream_crlf_lf(p) if p.is_file() else "DELETED"
    except OSError: return "DELETED"

def _read_text_bounded(repo_root: Path | None, rel_or_abs: str, *, staged: bool, head_ref: str | None, is_del: bool) -> str:
    if is_del: return ""
    if repo_root is not None and (head_ref or staged):
        rc, data = _run_git(repo_root, ["show", f"{head_ref}:{rel_or_abs}" if head_ref else f":{rel_or_abs}"], binary=True)
        return data[:MAX_SCAN_BYTES].decode("utf-8", errors="replace") if rc == 0 else ""
    p = Path(rel_or_abs) if Path(rel_or_abs).is_absolute() else ((repo_root or Path.cwd()) / rel_or_abs)
    try:
        if not p.is_file(): return ""
        with p.open("rb") as fh: return fh.read(MAX_SCAN_BYTES).decode("utf-8", errors="replace")
    except OSError: return ""

def _read_new_file_entry(fp: Path) -> dict[str, Any]:
    with fp.open("rb") as fh:
        head = fh.read(MAX_SCAN_BYTES)
        extra_lines = sum(chunk.count(b"\n") for chunk in iter(lambda: fh.read(65536), b""))
    lines = head.decode("utf-8", errors="replace").splitlines()
    return {"add": len(lines) + extra_lines, "del": 0, "lines": lines, "add_lines": lines, "del_lines": [], "is_new": True, "is_del": False, "is_symlink": fp.is_symlink()}

def _resolve_cumulative_base(repo_root: Path, pass_file: Path) -> str | None:
    if pass_file.is_file():
        try:
            pdata = json.loads(pass_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pdata = None
        if isinstance(pdata, dict) and pdata.get("verdict") in ("PASS", "PASS_DEGRADED"):
            cov = pdata.get("covered_head")
            if isinstance(cov, str) and HEX40_RE.fullmatch(cov.strip()) and _run_git(repo_root, ["merge-base", "--is-ancestor", cov.strip(), "HEAD"])[0] == 0:
                return cov.strip()
    rc, branch = _run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0 and branch.strip() not in ("", "HEAD", "main", "master"):
        for cand in ("main", "master", "origin/main", "origin/master"):
            rc2, mb = _run_git(repo_root, ["merge-base", "HEAD", cand])
            if rc2 == 0 and mb.strip(): return mb.strip()
    return None

def _collect_git_changes(repo_root: Path, base: str | None, staged: bool, pass_file: Path) -> tuple[dict[str, dict[str, Any]], str | None, str | None, str | None]:
    safe_base = _validate_ref(base)
    if safe_base and ".." in safe_base:
        parts = re.split(r"\.{2,3}", safe_base, maxsplit=1)
        rc, txt = _run_git(repo_root, ["diff", "--no-renames", "-U0", safe_base, "--"])
        if rc != 0: return {}, None, safe_base, f"R3:GIT_ERROR:diff_failed:{safe_base}"
        return _parse_unified_diff(txt), (parts[1].strip() or "HEAD"), safe_base, None
    if staged:
        rc, txt = _run_git(repo_root, ["diff", "--cached", "--no-renames", "-U0", "--"])
        if rc != 0: return {}, None, None, "R3:GIT_ERROR:diff_cached_failed"
        return _parse_unified_diff(txt), None, None, None
    eff_base = safe_base or _resolve_cumulative_base(repo_root, pass_file)
    rc, txt = _run_git(repo_root, ["diff", "--no-renames", "-U0", eff_base or "HEAD", "--"])
    if rc != 0:
        if eff_base:
            return {}, None, eff_base, f"R3:GIT_ERROR:diff_failed:{eff_base}"
        rc_c, txt = _run_git(repo_root, ["diff", "--cached", "--no-renames", "-U0", "--"])
        if rc_c != 0:
            return {}, None, None, "R3:GIT_ERROR:diff_head_failed"
    changes = _parse_unified_diff(txt)
    rc_u, untracked = _run_git(repo_root, ["ls-files", "--others", "--exclude-standard"])
    if rc_u != 0:
        return changes, None, eff_base, "R3:GIT_ERROR:ls_files_failed"
    for np in (_norm(x) for x in untracked.splitlines() if x.strip()):
        fp = repo_root / np
        try:
            if np in changes or SECRET_UNTRACKED.search(np) or not fp.is_file(): continue
            changes[np] = _read_new_file_entry(fp)
        except OSError:
            continue
    return changes, None, eff_base, None

def _collect_nongit_files(paths: list[Path], base_dir: Path | None) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    base_res = base_dir.resolve() if base_dir is not None else None
    for fp in sorted(paths, key=lambda p: (p.is_symlink(), str(p))):
        try:
            if not fp.is_file(): continue
            fp_res = fp.resolve()
        except OSError:
            continue
        key = _norm(str(fp_res))
        if base_res is not None:
            try:
                key = _norm(str(fp_res.relative_to(base_res)))
            except ValueError:
                key = _norm(str(fp_res))
        if SECRET_UNTRACKED.search(key) or (key in changes and not changes[key]["is_symlink"]): continue
        try:
            entry = _read_new_file_entry(fp)
        except OSError:
            continue
        entry["_abs"] = fp_res
        changes[key] = entry
    return changes

def _safe_anchor(resolved: list[Path], fallback: Path) -> Path:
    if not resolved: return fallback
    try:
        return Path(os.path.commonpath([str(p.parent) for p in resolved]))
    except ValueError:
        return fallback

def assess_tier(repo_root: Path | None = None, *, git_diff: bool = True, base: str | None = None, staged: bool = False, files: list[str] | None = None, target_dir: str | None = None, since_hours: float | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    git_common = None if (files or target_dir) else resolve_git_common_dir(root)
    head_ref: str | None = None
    eff_base: str | None = None
    git_err: str | None = None
    if files:
        resolved = [Path(f).resolve() for f in files]
        pass_file = _default_pass_file(None, _safe_anchor(resolved, root))
        changes = _collect_nongit_files(resolved, root)
    elif target_dir:
        anchor = Path(target_dir).resolve()
        pass_file = _default_pass_file(None, anchor)
        cutoff = (dt.datetime.now().timestamp() - since_hours * 3600.0) if since_hours is not None else 0.0
        found: list[Path] = []
        for dp, dns, fns in os.walk(anchor, followlinks=False):
            dns[:] = [d for d in dns if d not in (".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build")]
            for fn in fns:
                fp = Path(dp) / fn
                try:
                    if fp.is_symlink() and not fp.resolve().is_relative_to(anchor): continue
                    if cutoff == 0.0 or fp.stat().st_mtime >= cutoff: found.append(fp)
                except OSError:
                    continue
        changes = _collect_nongit_files(found, anchor)
    else:
        pass_file = _default_pass_file(git_common, root)
        changes, head_ref, eff_base, git_err = _collect_git_changes(root, base, staged, pass_file) if (git_diff and git_common) else ({}, None, None, None)
    prod_add = prod_del = prod_files = new_mods = max_new = test_del = test_asserts = excluded = max_risk = 0
    controlled, fp_entries, test_files, risk_reasons = [], [], [], []
    all_docs_or_styles, has_non_test_prod, has_py = True, False, False
    if git_err:
        max_risk = 3; risk_reasons.append(git_err)
    for path_key in sorted(changes):
        info = changes[path_key]
        cat, skip_self = _classify(path_key, info.get("is_symlink", False), info.get("lines"))
        if cat == "HARD_NOISE":
            excluded += 1; continue
        if cat == "TEST":
            test_files.append(path_key); test_del += info["del"]
            if info["del"] > 15 or sum(len(ASSERT_RE.findall(ln)) for ln in info["del_lines"]) > sum(len(ASSERT_RE.findall(ln)) for ln in info["add_lines"]):
                max_risk = max(max_risk, 2); risk_reasons.append(f"R2:TEST_ASSERTION_REDUCTION:{path_key}")
            txt = _read_text_bounded(None if "_abs" in info else root, str(info.get("_abs", path_key)), staged=staged, head_ref=head_ref, is_del=info["is_del"])
            test_asserts += len(ASSERT_RE.findall(txt))
            continue
        has_non_test_prod, has_py = True, has_py or path_key.lower().endswith(".py")
        all_docs_or_styles = all_docs_or_styles and (cat in ("PURE_DOC", "PURE_STYLE"))
        prod_add += info["add"]; prod_del += info["del"]; prod_files += 1
        if info["is_new"] and cat not in ("PURE_DOC", "PURE_STYLE") and info["add"] >= 40:
            new_mods += 1; max_new = max(max_new, info["add"])
        r_val, r_why = _scan_risk(path_key, cat, skip_self, info["lines"])
        max_risk = max(max_risk, r_val); risk_reasons.extend(r_why)
        if cat != "PURE_DOC":
            controlled.append(path_key)
            h = _hash_snapshot(None if "_abs" in info else root, str(info.get("_abs", path_key)), staged=staged, head_ref=head_ref, is_del=info["is_del"])
            fp_entries.append(f"{path_key}:{h}")
    churn = prod_add + prod_del
    scale = 3 if (churn > 200 or prod_add > 150 or prod_del > 60 or prod_files >= 6 or new_mods >= 2 or max_new >= 150) else (2 if (churn > 60 or prod_add > 50 or prod_del > 15 or prod_files >= 3 or new_mods >= 1) else (1 if (churn > 15 or prod_add > 15 or prod_del > 5 or prod_files >= 2) else 0))
    scale = min(scale, 1) if (has_non_test_prod and all_docs_or_styles) else scale
    req = 3 if (scale >= 2 and max_risk >= 2) else max(scale, max_risk)
    fp = hashlib.sha256("\n".join(sorted(fp_entries)).encode("utf-8")).hexdigest()[:12]
    req_t, scale_t, risk_t = f"T{req}", f"S{scale}", f"R{max_risk}"
    skills, checks = list(TIER_META[req_t][0]), list(TIER_META[req_t][1]) + (["cp950-cli-smoke-test"] if req_t == "T3" and has_py else [])
    return {
        "required_tier": req_t, "scale_tier": scale_t, "risk_tier": risk_t, "tier_token": f"{req_t}[{scale_t}/{risk_t}#{fp}]", "prod_diff_fingerprint": fp,
        "effective_base": eff_base,
        "test_integrity_snapshot": {"test_files": sorted(test_files), "test_assertions_min": test_asserts, "test_del_max": test_del},
        "metrics": {"prod_add": prod_add, "prod_del": prod_del, "prod_churn": churn, "prod_files": prod_files, "new_prod_modules": new_mods, "max_new_module_lines": max_new, "test_del": test_del, "excluded_files": excluded},
        "risk_reasons": risk_reasons, "controlled_files": sorted(controlled), "required_skills": skills, "required_checks": checks,
        "git_common_dir": str(git_common) if git_common else None, "default_pass_file": str(pass_file),
    }

def verify_pass(pass_file: Path | None = None, *, repo_root: Path | None = None, git_diff: bool = True, staged: bool = False, files: list[str] | None = None, tier_mode: str = "r3-enforce") -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    git_common = None if files else resolve_git_common_dir(root)
    anchor = _safe_anchor([Path(f).resolve() for f in files], root) if files else root
    pf = Path(pass_file) if pass_file else _default_pass_file(git_common, anchor)
    pre_data, pre_err = None, None
    if pf.is_file():
        try:
            pre_data = json.loads(pf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pre_err = "pass_file_invalid_json"
    pinned_base = None
    if isinstance(pre_data, dict) and git_diff and not staged and not files:
        br = pre_data.get("base_ref")
        if isinstance(br, str) and br.strip() and not br.strip().startswith("-"): pinned_base = br.strip()
    ass = assess_tier(repo_root, git_diff=git_diff, base=pinned_base, staged=staged, files=files)
    req_t, risk_t = ass["required_tier"], ass["risk_tier"]
    if TIER_NUM[req_t] < 2:
        return {"ok": True, "action": "pass", "exit_code": 0, "reasons": [], "assessment": ass, "pass_file": str(pf)}
    bypass = os.environ.get("LEAN_TRIAD_BYPASS_REASON", "").strip()
    if bypass:
        log_path = (Path(ass["git_common_dir"]) if ass["git_common_dir"] else pf.parent) / "lean_triad_bypass.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{dt.datetime.now(dt.timezone.utc).isoformat()} | {ass['tier_token']} | reason={bypass}\n")
        return {"ok": True, "bypassed": True, "action": "warn", "exit_code": 0, "reasons": [f"bypassed:{bypass}"], "assessment": ass, "pass_file": str(pf)}
    failures: list[str] = []
    if not pf.is_file(): failures.append("pass_file_missing")
    elif pre_err: failures.append(pre_err)
    elif not isinstance(pre_data, dict): failures.append("pass_file_not_object")
    else:
        data = pre_data
        if data.get("prod_diff_fingerprint") != ass["prod_diff_fingerprint"]: failures.append("fingerprint_mismatch")
        if data.get("verdict") not in ("PASS", "PASS_DEGRADED"): failures.append(f"invalid_verdict:{data.get('verdict')}")
        raw_ids = data.get("request_ids")
        if not isinstance(raw_ids, list) or not raw_ids: failures.append("missing_request_ids")
        elif any(str(x).strip().lower() in FAKE_REQ_IDS for x in raw_ids) or not any(str(x).strip() for x in raw_ids): failures.append("fake_or_empty_request_id")
        p_tier = data.get("required_tier") or data.get("gate_tier")
        if not isinstance(p_tier, str) or p_tier not in TIER_NUM: failures.append(f"invalid_or_missing_tier:{p_tier}")
        elif TIER_NUM[p_tier] < TIER_NUM[req_t]: failures.append(f"tier_insufficient:{p_tier}<{req_t}")
        p_snap = data.get("test_integrity_snapshot") if "test_integrity_snapshot" in data else data
        if not isinstance(p_snap, dict):
            failures.append("invalid_test_integrity_snapshot")
        else:
            try:
                cur_snap, min_a = ass["test_integrity_snapshot"], int(p_snap.get("test_assertions_min", 0) or 0)
                max_d = None if p_snap.get("test_del_max") is None else int(p_snap.get("test_del_max"))
                if cur_snap["test_assertions_min"] < min_a: failures.append(f"test_assertions_decreased:{cur_snap['test_assertions_min']}<{min_a}")
                if max_d is not None and cur_snap["test_del_max"] > max_d: failures.append(f"test_del_increased:{cur_snap['test_del_max']}>{max_d}")
            except (TypeError, ValueError):
                failures.append("invalid_test_integrity_snapshot")
    if not failures:
        return {"ok": True, "action": "pass", "exit_code": 0, "reasons": [], "assessment": ass, "pass_file": str(pf)}
    block = (tier_mode == "enforce") or (tier_mode == "r3-enforce" and (req_t == "T3" or risk_t == "R3"))
    return {"ok": False, "action": "block" if block else "warn", "exit_code": 1 if block else 0, "reasons": failures, "assessment": ass, "pass_file": str(pf)}

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tier_gate.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_a = sub.add_parser("assess")
    for flag, kw in (("--git-diff", {"action": "store_true"}), ("--base", {}), ("--staged", {"action": "store_true"}), ("--files", {"nargs": "+"}), ("--dir", {"dest": "target_dir"}), ("--since-hours", {"type": float}), ("--repo-root", {}), ("--format", {"choices": ("json", "text"), "default": "json"})):
        p_a.add_argument(flag, **kw)
    p_v = sub.add_parser("verify-pass")
    for flag, kw in (("--pass-file", {}), ("--git-diff", {"action": "store_true"}), ("--staged", {"action": "store_true"}), ("--files", {"nargs": "+"}), ("--repo-root", {}), ("--tier-mode", {"choices": ("r3-enforce", "enforce", "warn"), "default": "r3-enforce"})):
        p_v.add_argument(flag, **kw)
    ns = ap.parse_args(argv)
    rr = Path(ns.repo_root) if ns.repo_root else None
    if ns.cmd == "assess":
        res = assess_tier(rr, git_diff=ns.git_diff or not (ns.files or ns.target_dir), base=ns.base, staged=ns.staged, files=ns.files, target_dir=ns.target_dir, since_hours=ns.since_hours)
        _safe_print(f"{res['tier_token']} | prod={res['metrics']['prod_churn']} ({res['metrics']['prod_files']}f) | reasons={'; '.join(res['risk_reasons']) or 'none'}" if ns.format == "text" else json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    res = verify_pass(Path(ns.pass_file) if ns.pass_file else None, repo_root=rr, git_diff=ns.git_diff or not ns.files, staged=ns.staged, files=ns.files, tier_mode=ns.tier_mode)
    _safe_print(json.dumps(res, ensure_ascii=False, indent=2))
    return int(res["exit_code"])

if __name__ == "__main__":
    raise SystemExit(main())
