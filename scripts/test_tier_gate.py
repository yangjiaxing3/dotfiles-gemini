#!/usr/bin/env python3
"""Regression & unit tests for tier_gate.py."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import tier_gate  # noqa: E402

WORKDIV_REPO = Path(r"c:\Users\Jiaxing\Documents\GitHub\Storeasyworkdivnew")
MEMORY_HUB_DIR = Path(r"C:\Users\Jiaxing\.gemini\memory-hub")


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    return r.stdout


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("# init\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: init")
    return repo


# 1. Storeasyworkdivnew 近 30 筆歷史 commits 實測：純 UI/CSS/Logo commit R3 誤報率 == 0%
def test_workdiv_recent_30_commits_ui_zero_r3_false_positive() -> None:
    assert WORKDIV_REPO.is_dir(), f"Missing repo: {WORKDIV_REPO}"
    log_out = _git(WORKDIV_REPO, "log", "-n", "30", "--no-merges", "--format=%H|%s")
    commits = [line.split("|", 1) for line in log_out.splitlines() if "|" in line]
    assert len(commits) >= 15

    pure_ui_checked = 0
    ui_r3_false_positives: list[tuple[str, str, list[str]]] = []
    for sha, subject in commits:
        # Check parent exists
        try:
            _git(WORKDIV_REPO, "rev-parse", f"{sha}~1")
        except subprocess.CalledProcessError:
            continue
        changed_files = [
            f.strip().replace("\\", "/")
            for f in _git(WORKDIV_REPO, "diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines()
            if f.strip()
        ]
        if not changed_files:
            continue
        is_pure_ui_css_logo = all(
            f.endswith((".css", ".scss", ".svg", ".png", ".tsx", ".jsx"))
            and not f.startswith("backend/")
            and "3d" not in f.lower()
            and "simulator" not in f.lower()
            and "cad" not in f.lower()
            for f in changed_files
        )
        if not is_pure_ui_css_logo:
            continue
        pure_ui_checked += 1
        res = tier_gate.assess_tier(WORKDIV_REPO, git_diff=True, base=f"{sha}~1..{sha}")
        if res["risk_tier"] == "R3":
            ui_r3_false_positives.append((sha[:7], subject, res["risk_reasons"]))

    assert pure_ui_checked >= 3, f"Expected >=3 pure UI/CSS/Logo commits in last 30, got {pure_ui_checked}"
    assert ui_r3_false_positives == [], f"Pure UI/CSS/Logo commits falsely flagged R3: {ui_r3_false_positives}"


# 2. Phase 1 非 Git 案例：memory_hub_indexer.py + memory_hub_mcp.py 必判 T3
def test_phase1_nongit_memory_hub_must_be_t3() -> None:
    f1 = MEMORY_HUB_DIR / "memory_hub_indexer.py"
    f2 = MEMORY_HUB_DIR / "memory_hub_mcp.py"
    assert f1.is_file() and f2.is_file()

    res = tier_gate.assess_tier(files=[str(f1), str(f2)])
    assert res["required_tier"] == "T3"
    assert res["scale_tier"] == "S3"
    assert res["risk_tier"] == "R3"
    assert res["tier_token"].startswith("T3[S3/R3#")
    assert len(res["prod_diff_fingerprint"]) == 12
    for key in (
        "required_tier", "scale_tier", "risk_tier", "tier_token", "prod_diff_fingerprint",
        "test_integrity_snapshot", "metrics", "risk_reasons", "controlled_files",
        "required_skills", "required_checks", "git_common_dir", "default_pass_file",
    ):
        assert key in res
    assert "cp950-cli-smoke-test" in res["required_checks"]


# 3. .cursor/rules/engineering-core.mdc 不被鏡像排除吞掉，必判 R3
def test_cursor_rules_mdc_not_excluded_and_flagged_r3(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rule_file = repo / ".cursor" / "rules" / "engineering-core.mdc"
    rule_file.parent.mkdir(parents=True)
    rule_file.write_text("# core rule\n", encoding="utf-8")
    # Also add a mirror skill under .cursor/skills/ which MUST be excluded
    mirror_skill = repo / ".cursor" / "skills" / "demo" / "SKILL.md"
    mirror_skill.parent.mkdir(parents=True)
    mirror_skill.write_text("# mirror\n", encoding="utf-8")

    res = tier_gate.assess_tier(repo, git_diff=True)
    assert res["risk_tier"] == "R3"
    assert res["required_tier"] == "T3"
    assert ".cursor/rules/engineering-core.mdc" in res["controlled_files"]
    assert ".cursor/skills/demo/SKILL.md" not in res["controlled_files"]
    assert res["metrics"]["excluded_files"] >= 1


# 4. 過 gate 後補寫測試放行，但過 gate 後偷刪 assert 必被 verify_pass 攔截
def test_post_gate_add_tests_passes_but_deleting_assert_blocks(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    # Create R3 file + test file with 2 assertions
    auth_file = repo / "backend" / "app" / "auth" / "guard.py"
    auth_file.parent.mkdir(parents=True)
    auth_file.write_text("def verify(x):\n    return bool(x)\n", encoding="utf-8")
    test_file = repo / "backend" / "tests" / "test_guard.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok():\n    assert 1 == 1\n    assert 2 == 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat: add guard")

    # Modify auth file (R3)
    auth_file.write_text("def verify(x):\n    return x is not None\n", encoding="utf-8")
    ass = tier_gate.assess_tier(repo, git_diff=True)
    assert ass["required_tier"] == "T3"

    pass_file = Path(ass["default_pass_file"])
    pass_file.write_text(json.dumps({
        "prod_diff_fingerprint": ass["prod_diff_fingerprint"],
        "required_tier": ass["required_tier"],
        "verdict": "PASS",
        "request_ids": ["req_real_001"],
        "test_integrity_snapshot": ass["test_integrity_snapshot"],
    }), encoding="utf-8")

    # (a) Adding MORE tests & README docs after gate MUST still pass
    test_file.write_text(
        "def test_ok():\n    assert 1 == 1\n    assert 2 == 2\n    assert 3 == 3\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# updated docs\n", encoding="utf-8")
    v_add = tier_gate.verify_pass(pass_file, repo_root=repo, git_diff=True)
    assert v_add["ok"] is True
    assert v_add["exit_code"] == 0

    # Update pass snapshot to record the 3 assertions, then secretly delete assertions
    ass2 = tier_gate.assess_tier(repo, git_diff=True)
    assert ass2["test_integrity_snapshot"]["test_assertions_min"] == 3
    pass_file.write_text(json.dumps({
        "prod_diff_fingerprint": ass2["prod_diff_fingerprint"],
        "required_tier": ass2["required_tier"],
        "verdict": "PASS",
        "request_ids": ["req_real_001"],
        "test_integrity_snapshot": ass2["test_integrity_snapshot"],
    }), encoding="utf-8")

    # (b) Deleting assertions after gate MUST be blocked!
    test_file.write_text("def test_ok():\n    pass\n", encoding="utf-8")
    v_del = tier_gate.verify_pass(pass_file, repo_root=repo, git_diff=True)
    assert v_del["ok"] is False
    assert v_del["action"] == "block"
    assert v_del["exit_code"] == 1
    assert any("test_assertions_decreased" in r for r in v_del["reasons"])


# 5. cursor-plan-delegated 假 request_id 必被攔截；PASS_DEGRADED 帶真實 request_id 放行
def test_fake_request_id_rejected_and_pass_degraded_accepted(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    sec = repo / "backend" / "app" / "security" / "hmac_check.py"
    sec.parent.mkdir(parents=True)
    sec.write_text("def check():\n    return True\n", encoding="utf-8")
    ass = tier_gate.assess_tier(repo, git_diff=True)
    assert ass["required_tier"] == "T3"

    pf = tmp_path / "pass.json"
    # Fake request_id -> BLOCK
    pf.write_text(json.dumps({
        "prod_diff_fingerprint": ass["prod_diff_fingerprint"],
        "required_tier": "T3",
        "verdict": "PASS",
        "request_ids": ["cursor-plan-delegated"],
    }), encoding="utf-8")
    v_fake = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True)
    assert v_fake["ok"] is False
    assert v_fake["exit_code"] == 1
    assert "fake_or_empty_request_id" in v_fake["reasons"]

    # PASS_DEGRADED with real request_id -> PASS
    pf.write_text(json.dumps({
        "prod_diff_fingerprint": ass["prod_diff_fingerprint"],
        "required_tier": "T3",
        "verdict": "PASS_DEGRADED",
        "request_ids": ["chatcmpl-8afe1a89-d880-92d5-8c3b-fe886854f4a7"],
    }), encoding="utf-8")
    v_deg = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True)
    assert v_deg["ok"] is True
    assert v_deg["exit_code"] == 0


# 6. 破壞性 SQL (DELETE FROM users; 無 WHERE) 必判 R3
def test_destructive_sql_without_where_is_r3(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    svc = repo / "backend" / "app" / "services" / "cleanup.py"
    svc.parent.mkdir(parents=True)
    svc.write_text('def wipe(conn):\n    conn.execute("DELETE FROM users;")\n', encoding="utf-8")

    res = tier_gate.assess_tier(repo, git_diff=True)
    assert res["risk_tier"] == "R3"
    assert res["required_tier"] == "T3"
    assert any("R3:DESTRUCTIVE_SQL" in r for r in res["risk_reasons"])


# 7. 以 PYTHONIOENCODING=cp950 實跑 CLI assess 不崩潰
def test_cli_assess_under_cp950_does_not_crash(tmp_path: Path) -> None:
    f = tmp_path / "繁中模組_測試.py"
    f.write_text("# 繁體中文註解 🚀\ndef hello():\n    return '你好世界'\n", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp950"

    for fmt in ("json", "text"):
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "tier_gate.py"), "assess", "--files", str(f), "--format", fmt],
            capture_output=True, env=env, timeout=15,
        )
        assert r.returncode == 0, f"CP950 failed ({fmt}): {r.stderr.decode('cp950', errors='replace')}"
        assert r.stdout.strip()


# 8. Extra invariants: worktree common_dir, covered_head, r3-enforce warn on T2, bypass log, working==staged fp
def test_covered_head_and_r3_enforce_modes_and_bypass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    assert tier_gate.resolve_git_common_dir(repo) == (repo / ".git").resolve()

    # Branch with an old T3 commit, then advance covered_head so next tiny edit is T0
    _git(repo, "checkout", "-b", "feat/demo")
    auth = repo / "backend" / "app" / "auth" / "old.py"
    auth.parent.mkdir(parents=True)
    auth.write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat: old auth change")
    head_sha = _git(repo, "rev-parse", "HEAD").strip()

    # Without covered_head, cumulative diff from main is T3
    ass_before = tier_gate.assess_tier(repo, git_diff=True)
    assert ass_before["required_tier"] == "T3"

    # Write valid PASS + 40-hex covered_head into default_pass_file -> old debt cleared
    pf = Path(ass_before["default_pass_file"])
    pf.write_text(json.dumps({"verdict": "PASS", "covered_head": head_sha}), encoding="utf-8")
    css = repo / "src" / "styles" / "tiny.css"
    css.parent.mkdir(parents=True)
    css.write_text(".a { margin: 4px; }\n", encoding="utf-8")
    ass_after = tier_gate.assess_tier(repo, git_diff=True)
    assert ass_after["required_tier"] == "T0"
    assert ass_after["risk_tier"] == "R0"

    # Fingerprint consistency between working tree and staged (CRLF vs LF)
    api = repo / "backend" / "app" / "routers" / "items.py"
    api.parent.mkdir(parents=True)
    api.write_bytes(b"from fastapi import APIRouter\r\nrouter = APIRouter()\r\n")
    ass_wt = tier_gate.assess_tier(repo, git_diff=True, staged=False)
    _git(repo, "add", str(css), str(api))
    ass_st = tier_gate.assess_tier(repo, git_diff=True, staged=True)
    assert ass_wt["required_tier"] == "T2"
    assert ass_wt["prod_diff_fingerprint"] == ass_st["prod_diff_fingerprint"]

    # r3-enforce mode: T2 without pass -> action="warn", exit_code=0
    v_t2 = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True, staged=True, tier_mode="r3-enforce")
    assert v_t2["ok"] is False
    assert v_t2["action"] == "warn"
    assert v_t2["exit_code"] == 0

    # Bypass env var logs to lean_triad_bypass.log and sets action="warn"
    monkeypatch.setenv("LEAN_TRIAD_BYPASS_REASON", "emergency hotfix")
    v_bp = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True, staged=True, tier_mode="enforce")
    assert v_bp["ok"] is True
    assert v_bp["action"] == "warn"
    assert (repo / ".git" / "lean_triad_bypass.log").is_file()


# 9. #143 CRITICAL/HIGH: non-dict JSON, missing/invalid tier, corrupted test_integrity_snapshot
@pytest.mark.parametrize("bad_json", ["null", "[]", "123", '"ok"'])
def test_verify_pass_rejects_non_dict_json(tmp_path: Path, bad_json: str) -> None:
    repo = _init_repo(tmp_path)
    sec = repo / "backend" / "app" / "security" / "check.py"
    sec.parent.mkdir(parents=True)
    sec.write_text("x = 1\n", encoding="utf-8")
    pf = tmp_path / "pass.json"
    pf.write_text(bad_json, encoding="utf-8")
    v = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True)
    assert v["ok"] is False and v["exit_code"] == 1
    assert "pass_file_not_object" in v["reasons"]


def test_verify_pass_rejects_missing_tier_and_corrupt_snapshot(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    sec = repo / "backend" / "app" / "security" / "check.py"
    sec.parent.mkdir(parents=True)
    sec.write_text("x = 1\n", encoding="utf-8")
    ass = tier_gate.assess_tier(repo, git_diff=True)
    pf = tmp_path / "pass.json"

    # Missing/invalid required_tier + non-int test_assertions_min must block without crashing
    pf.write_text(json.dumps({
        "prod_diff_fingerprint": ass["prod_diff_fingerprint"],
        "required_tier": "INVALID_TIER",
        "verdict": "PASS",
        "request_ids": ["req_real_999"],
        "test_integrity_snapshot": {"test_assertions_min": "abc", "test_del_max": "xyz"},
    }), encoding="utf-8")
    v = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True)
    assert v["ok"] is False and v["exit_code"] == 1
    assert any("invalid_or_missing_tier" in r for r in v["reasons"])
    assert "invalid_test_integrity_snapshot" in v["reasons"]


# 10. #143 HIGH: effective_base + base_ref prevents covered_head self-invalidation on feature branch
def test_verify_pass_uses_base_ref_no_covered_head_self_invalidation(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-b", "feat/branch-base")
    f1 = repo / "backend" / "app" / "security" / "c1.py"
    f1.parent.mkdir(parents=True)
    f1.write_text("def a(): return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat: c1")
    c1_sha = _git(repo, "rev-parse", "HEAD").strip()

    # Working tree R3 edit on top of C1
    f2 = repo / "backend" / "app" / "security" / "wt.py"
    f2.write_text("def b(): return 2\n", encoding="utf-8")
    ass = tier_gate.assess_tier(repo, git_diff=True)
    assert ass["effective_base"] is not None

    pf = Path(ass["default_pass_file"])
    pf.write_text(json.dumps({
        "prod_diff_fingerprint": ass["prod_diff_fingerprint"],
        "required_tier": ass["required_tier"],
        "verdict": "PASS",
        "request_ids": ["req_real_base"],
        "base_ref": ass["effective_base"],
        "covered_head": c1_sha,
        "test_integrity_snapshot": ass["test_integrity_snapshot"],
    }), encoding="utf-8")
    v = tier_gate.verify_pass(pf, repo_root=repo, git_diff=True)
    assert v["ok"] is True and v["exit_code"] == 0


# 11. #144 CRITICAL: >512KB large untracked file is NOT invisible or DELETED
def test_large_file_over_512kb_hashed_streaming_and_tracked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    big = repo / "backend" / "app" / "services" / "big_data.py"
    big.parent.mkdir(parents=True)
    big.write_bytes(b"x = 1\n" * 100_000)  # ~600KB
    ass1 = tier_gate.assess_tier(repo, git_diff=True)
    assert "backend/app/services/big_data.py" in ass1["controlled_files"]
    assert ass1["scale_tier"] == "S3"
    assert ass1["metrics"]["prod_add"] >= 100_000

    # Changing 1 byte at the tail MUST change prod_diff_fingerprint (proving not DELETED)
    with big.open("ab") as fh:
        fh.write(b"y = 2\n")
    ass2 = tier_gate.assess_tier(repo, git_diff=True)
    assert ass1["prod_diff_fingerprint"] != ass2["prod_diff_fingerprint"]


# 12. #144 CRITICAL: string-before-comment lexer, Chinese finance keywords, audit keywords, SQL WHERE 1=1
def test_lexer_order_chinese_finance_audit_and_tautology_sql(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    p1 = repo / "backend" / "app" / "services" / "sneaky.py"
    p1.parent.mkdir(parents=True)
    p1.write_text('x = " // "; conn.execute("DROP TABLE users;")\n', encoding="utf-8")
    assert tier_gate.assess_tier(repo, git_diff=True)["risk_tier"] == "R3"

    p1.write_text('conn.execute("DELETE FROM users WHERE 1=1")\n', encoding="utf-8")
    r_taut = tier_gate.assess_tier(repo, git_diff=True)
    assert r_taut["risk_tier"] == "R3" and any("R3:DESTRUCTIVE_SQL" in r for r in r_taut["risk_reasons"])

    p1.write_text('POLICY = "只作廢不刪除"\n', encoding="utf-8")
    assert tier_gate.assess_tier(repo, git_diff=True)["risk_tier"] == "R3"

    p1.write_text('def tag(void_only):\n    return void_only\n', encoding="utf-8")
    assert tier_gate.assess_tier(repo, git_diff=True)["risk_tier"] == "R3"


# 13. #144 CRITICAL/HIGH: non-mirror symlink not ignored, Chinese+space git paths, --base injection, P1 bare script & .agents/skills
def test_symlink_escape_cjk_space_paths_ref_injection_and_p1_rules(tmp_path: Path) -> None:
    # (a) Non-mirror symlink MUST NOT be classified HARD_NOISE
    cat_evil, _ = tier_gate._classify("backend/app/services/link.py", is_symlink=True)
    assert cat_evil == "DOMAIN_CALC_BACKEND"
    cat_mirror, _ = tier_gate._classify(".agents/skills/demo/SKILL.md", is_symlink=True)
    assert cat_mirror == "HARD_NOISE"
    # P1 beats P2 even for .agents/skills/stage-gate-review/SKILL.md
    cat_p1_plural, _ = tier_gate._classify(".agents/skills/stage-gate-review/SKILL.md", is_symlink=True)
    assert cat_p1_plural == "R3_PROTECTED"
    # P1 bare self-script without scripts/ prefix
    cat_bare, skip_bare = tier_gate._classify("tier_gate.py", is_symlink=False)
    assert cat_bare == "R3_PROTECTED" and skip_bare is True

    # (b) Git Chinese + space path works cleanly without quotepath corruption
    repo = _init_repo(tmp_path)
    cjk = repo / "backend" / "app" / "services" / "租約 檔案.py"
    cjk.parent.mkdir(parents=True)
    cjk.write_text("def calc():\n    return 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat: add cjk file")
    cjk.write_text('def calc():\n    return "每坪租金"\n', encoding="utf-8")
    ass = tier_gate.assess_tier(repo, git_diff=True)
    assert "backend/app/services/租約 檔案.py" in ass["controlled_files"]
    assert ass["risk_tier"] == "R3"

    # (c) --base starting with '-' rejected (anti git argument injection)
    with pytest.raises(ValueError):
        tier_gate.assess_tier(repo, git_diff=True, base="--output=evil")


# 14. #158 CRITICAL/HIGH: --files preserves parent path, TYPE_ONLY_RE no bypass, git fail-closed, main...HEAD, covered_head verdict & broken symlink
def test_round2_fixes_files_path_type_only_fail_closed_triple_dot_and_dir(tmp_path: Path) -> None:
    # (a) --files preserves parent dir (backend/app/models/order.py -> P1 R3)
    model_f = tmp_path / "backend" / "app" / "models" / "order.py"
    model_f.parent.mkdir(parents=True)
    model_f.write_text("class Order:\n    pass\n", encoding="utf-8")
    r_files = tier_gate.assess_tier(tmp_path, files=[str(model_f)])
    assert r_files["risk_tier"] == "R3"
    assert any("backend/app/models/order.py" in p for p in r_files["controlled_files"])

    # (b) TYPE_ONLY_RE cannot be bypassed by leading '{' with destructive SQL
    repo = _init_repo(tmp_path)
    ts_f = repo / "src" / "lib" / "sneaky.ts"
    ts_f.parent.mkdir(parents=True)
    ts_f.write_text('{ await db.execute("DROP TABLE users"); }\n', encoding="utf-8")
    r_ts = tier_gate.assess_tier(repo, git_diff=True)
    assert r_ts["risk_tier"] == "R3" and any("R3:DESTRUCTIVE_SQL" in x for x in r_ts["risk_reasons"])

    # (c) Git error (invalid --base) fails CLOSED as R3:GIT_ERROR (never T0)
    r_err = tier_gate.assess_tier(repo, git_diff=True, base="nonexistent_ref_xyz")
    assert r_err["risk_tier"] == "R3" and r_err["required_tier"] == "T3"
    assert any("R3:GIT_ERROR" in x for x in r_err["risk_reasons"])

    # (d) main...HEAD triple-dot splits cleanly (same fp as main..HEAD, not DELETED)
    _git(repo, "checkout", "-b", "feat/triple")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat: commit sneaky")
    r_two = tier_gate.assess_tier(repo, git_diff=True, base="main..HEAD")
    r_three = tier_gate.assess_tier(repo, git_diff=True, base="main...HEAD")
    assert r_two["prod_diff_fingerprint"] == r_three["prod_diff_fingerprint"]

    # (e) covered_head without verdict PASS or non-40-hex SHA is ignored
    pf = Path(r_three["default_pass_file"])
    head_sha = _git(repo, "rev-parse", "HEAD").strip()
    pf.write_text(json.dumps({"verdict": "BLOCK", "covered_head": head_sha}), encoding="utf-8")
    assert tier_gate.assess_tier(repo, git_diff=True)["risk_tier"] == "R3"
    pf.write_text(json.dumps({"verdict": "PASS", "covered_head": "HEAD"}), encoding="utf-8")
    assert tier_gate.assess_tier(repo, git_diff=True)["risk_tier"] == "R3"

    # (f) --dir tolerates broken symlinks and does not crash
    scan_dir = tmp_path / "scan_target"
    scan_dir.mkdir()
    (scan_dir / "ok.py").write_text("x = 1\n", encoding="utf-8")
    try:
        os.symlink(tmp_path / "does_not_exist.py", scan_dir / "broken.py")
    except OSError:
        # Windows 無開發者模式權限時可能無法建立 symlink，略過此步仍驗證正常掃描
        broken_created = False
    else:
        broken_created = True
    assert isinstance(broken_created, bool)
    r_dir = tier_gate.assess_tier(target_dir=str(scan_dir), since_hours=12)
    assert "ok.py" in r_dir["controlled_files"]


