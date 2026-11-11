#!/usr/bin/env python3
"""
Cursor Cloud Agents 容器啟動自動掛載與單一真相來源 (SSOT) 自癒腳本 (scripts/bootstrap_cursor_cloud.py)

當 Cursor Cloud Agent 在雲端隔離 Linux 容器 (/workspace) 啟動時（由 `.cursor/environment.json` 觸發）：
1. 自動將當前專案內的 `.agents/skills` (或 `.cursor/skills`) 掛載/鏡像至容器內的：
   - `~/.cursor/skills`
   - `~/.gemini/config/skills`
   - `.cursor/skills`
2. 自動將當前專案內的 `.cursor/rules` 掛載/鏡像至容器內的 `~/.cursor/rules` 與 `~/.gemini/cursor-rules`。
3. 若容器內不存在 `~/.gemini/GEMINI.md`（雲端 Linux 環境無本機 Windows 路徑），自動由專案內
   `.cursor/rules/engineering-core.mdc` 建立 `~/.gemini/GEMINI.md` 鏡像，徹底消除雲端與本機路徑落差。
4. 自動校驗並同步專案根目錄 `AGENTS.md` 的受管區塊 `<!-- BEGIN_LEAN_TRIAD_SSOT --> ... <!-- END_LEAN_TRIAD_SSOT -->`，
   確保雲端系統提示唯一載入的 `AGENTS.md` 與 `.cursor/rules/engineering-core.mdc` 永遠 100% 同源不分裂。
5. 自動將當前專案內的 `scripts/skill_router.py`、`scripts/multi_model_gate.py`、`scripts/skill_eval_dataset.json`
   鏡像至 `~/.gemini/scripts/`。
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
HOME = Path.home()

SSOT_BEGIN = "<!-- BEGIN_LEAN_TRIAD_SSOT -->"
SSOT_END = "<!-- END_LEAN_TRIAD_SSOT -->"

CANONICAL_AGENTS_SSOT_BLOCK = """<!-- BEGIN_LEAN_TRIAD_SSOT -->
## Cursor Cloud & Agent Skills (Lean-Triad 單一真相來源)

> 本區塊由 `scripts/sync_skills_to_cloud_repos.py` 與 `scripts/bootstrap_cursor_cloud.py` 自 `~/.gemini/GEMINI.md` 及 `.cursor/rules/engineering-core.mdc` 自動同步鎖定；請勿單獨手改，避免本機與雲端規則分裂。

- **常駐底層引擎**：`🧭 Graphify 圖譜導航` + `🧰 Role-Scoped Skills 動態掛載` + `✂️ Ponytail 極簡守則` 為常駐引擎；刪減 `> 15` 行、移除抽象層／檔案或指定 `/multi-agent-mode` 時強制執行 `python3 scripts/multi_model_gate.py review --prompt "..." --git-diff --output temp_multi_review.json`。
- **確定性路由與多模型門禁**：
  - 檢索最佳技能：`python3 scripts/skill_router.py route "<任務描述>"`
  - 預覽角色×任務技能矩陣：`python3 scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`
- **全域 UI 圖示與極簡按鈕鐵律（`impeccable` × `stageshow` × `design-taste-frontend`）**：
  - **嚴禁 UI Emoji**：頁面標題、KPI、徽章、按鈕、表格與提示文字一律禁止使用 Emoji；視覺引導統一使用乾淨 SVG 或 `lucide-react` 圖示。
  - **按鈕限 2～4 字或純 Icon**：操作按鈕強制精簡為 **2～4 個字**（如 `新增批次`、`匯出 Excel`、`顯示月薪`）或純 SVG Icon 按鈕（必備 `title` 與 `aria-label`），並移除重複標題語意的冗餘說明文字。
- **收尾誠實揭露與極簡防重複回條（Final-Turn Compact Lean-Triad Receipt）**：
  - **🚫 嚴禁輸出回條之場景（防 Token 浪費）**：等待背景任務（`run_command` / `Shell` / subagent）完成的中繼進度回覆、純合併／部署狀態回報、澄清提問、純問答或閒聊，或**同一任務無新程式碼變更時，絕對禁止附上執行回條**。
  - **🚫 嚴禁正文與回條內容重複（Anti-Duplication Rule）**：回條每欄僅限填寫**關鍵字、路徑、行數或指令結果**（每欄 `<= 60` 字），**嚴禁把正文寫過的結論、PR 編號或背景敘述重抄進回條**；反之，已寫入回條的測試通過數、行數統計與略過邊界，正文**不再重複條列**。
  - **✅ 最終交付格式**（僅在「任務最終完成交付」結尾輸出一次精簡逐行版回條）：
    ```markdown
    ---
    **🛡️ Lean-Triad**
    - 🧰 **Skills**：`<Skills>`
    - 🧭 **Graphify**：`<節點 / update>`
    - ✂️ **Ponytail**：`+<新增> / -<刪除> 行 (shortcut: <無或註記>)`
    - ⚖️ **Gate & QA**：`<會審門禁與測試通過數>`
    - ⚠️ **邊界**：`<略過項目與風險>`
    ```
<!-- END_LEAN_TRIAD_SSOT -->"""


def _safe_link_or_copy_dir(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    try:
        if os.path.realpath(src) == os.path.realpath(dst) and dst.exists():
            return
    except OSError:
        pass
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.is_file():
        dst.unlink(missing_ok=True)
    if not dst.exists():
        try:
            os.symlink(src, dst, target_is_directory=True)
            return
        except OSError:
            pass
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if target.exists():
            continue
        try:
            os.symlink(item, target, target_is_directory=item.is_dir())
        except OSError:
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            elif item.is_file():
                shutil.copy2(item, target)


def ensure_agents_md_ssot(repo_root: Path) -> bool:
    """確保專案根目錄 AGENTS.md 內嵌與 engineering-core.mdc 一致的受管 SSOT 區塊。"""
    agents_md = repo_root / "AGENTS.md"
    if not agents_md.is_file():
        return False
    original = agents_md.read_text(encoding="utf-8")
    updated = original

    if SSOT_BEGIN in updated and SSOT_END in updated:
        pattern = re.compile(
            re.escape(SSOT_BEGIN) + r".*?" + re.escape(SSOT_END),
            re.DOTALL,
        )
        updated = pattern.sub(CANONICAL_AGENTS_SSOT_BLOCK, updated)
    else:
        # 替換舊版未受管的手寫段落（例如 `## Lean-Triad 執行回條` 或 `## Cursor Cloud & Agent Skills (Lean-Triad)`）
        legacy_patterns = [
            re.compile(
                r"## Cursor Cloud & Agent Skills \(Lean-Triad[^\n]*\)\n.*?(?=\n## |\Z)",
                re.DOTALL,
            ),
            re.compile(
                r"## Lean-Triad 執行回條[^\n]*\n.*?(?=\n## |\Z)",
                re.DOTALL,
            ),
        ]
        replaced = False
        for lp in legacy_patterns:
            if lp.search(updated):
                updated = lp.sub(CANONICAL_AGENTS_SSOT_BLOCK + "\n", updated, count=1)
                replaced = True
                break
        if not replaced:
            if "\n## graphify" in updated:
                updated = updated.replace(
                    "\n## graphify",
                    f"\n{CANONICAL_AGENTS_SSOT_BLOCK}\n\n## graphify",
                    1,
                )
            else:
                updated = updated.rstrip() + f"\n\n{CANONICAL_AGENTS_SSOT_BLOCK}\n"

    if updated != original:
        agents_md.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    repo_skills = REPO_ROOT / ".agents" / "skills"
    if not repo_skills.is_dir():
        repo_skills = REPO_ROOT / ".cursor" / "skills"

    if repo_skills.is_dir():
        _safe_link_or_copy_dir(repo_skills, REPO_ROOT / ".cursor" / "skills")
        _safe_link_or_copy_dir(repo_skills, HOME / ".cursor" / "skills")
        _safe_link_or_copy_dir(repo_skills, HOME / ".gemini" / "config" / "skills")

    repo_rules = REPO_ROOT / ".cursor" / "rules"
    if repo_rules.is_dir():
        _safe_link_or_copy_dir(repo_rules, HOME / ".cursor" / "rules")
        _safe_link_or_copy_dir(repo_rules, HOME / ".gemini" / "cursor-rules")

    # 若在雲端 Linux 容器內不存在 ~/.gemini/GEMINI.md，自動由專案內 engineering-core.mdc 建立鏡像
    gemini_md = HOME / ".gemini" / "GEMINI.md"
    eng_core = repo_rules / "engineering-core.mdc"
    if not gemini_md.is_file() and eng_core.is_file():
        gemini_md.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(eng_core, gemini_md)

    ensure_agents_md_ssot(REPO_ROOT)

    gemini_scripts = HOME / ".gemini" / "scripts"
    gemini_scripts.mkdir(parents=True, exist_ok=True)
    for fname in ("skill_router.py", "multi_model_gate.py", "skill_eval_dataset.json", "bootstrap_cursor_cloud.py"):
        src_f = SCRIPT_DIR / fname
        dst_f = gemini_scripts / fname
        if src_f.is_file():
            try:
                if os.path.realpath(src_f) != os.path.realpath(dst_f):
                    shutil.copy2(src_f, dst_f)
            except OSError:
                pass

    print(f"[CursorCloudBootstrap] Ready: repo={REPO_ROOT.name}, skills={repo_skills}")


if __name__ == "__main__":
    main()
