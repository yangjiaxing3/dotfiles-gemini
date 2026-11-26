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
5. 自動將當前專案內的 `scripts/skill_router.py`、`scripts/multi_model_gate.py`、`scripts/rule_lint.py`、`scripts/skill_eval_dataset.json`
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
GLOBAL_AGENTS_SSOT_TEMPLATE = HOME / ".gemini" / "templates" / "agents_ssot_block.md"

SYNCED_SCRIPTS = (
    "skill_router.py",
    "multi_model_gate.py",
    "rule_lint.py",
    "tier_gate.py",
    "skill_eval_dataset.json",
    "bootstrap_cursor_cloud.py",
    "sync_skills_to_cloud_repos.py",
)

SSOT_BEGIN = "<!-- BEGIN_LEAN_TRIAD_SSOT -->"
SSOT_END = "<!-- END_LEAN_TRIAD_SSOT -->"

# 防漂移備援：真相來源為 ~/.gemini/templates/agents_ssot_block.md，僅在雲端容器尚無該檔時退回使用
_FALLBACK_AGENTS_SSOT_BLOCK = """<!-- BEGIN_LEAN_TRIAD_SSOT -->
## Cursor Cloud & Agent Skills (Lean-Triad 單一真相來源)

> 本區塊由 `scripts/sync_skills_to_cloud_repos.py` 與 `scripts/bootstrap_cursor_cloud.py` 自 `~/.gemini/templates/agents_ssot_block.md`（同步自 `GEMINI.md` / `engineering-core.mdc`）自動鎖定；請勿單獨手改，避免本機與雲端規則分裂。

- **常駐底層引擎與受保護禁區**：`🧭 Graphify 圖譜導航` + `🧰 Role-Scoped Skills 動態掛載` + `✂️ Ponytail 極簡守則` 為常駐引擎；嚴禁簡化 3D 空間幾何／財務計價／硬體 IoT FOV 校準與跨庫 API 契約。
- **規模 × 風險分級強制複查門禁（Tier 0–3）**：
  - 交付前必執行 `python3 scripts/tier_gate.py assess --git-diff`（非 Git 目錄用 `--files <paths...>`；無 `scripts/` 用 `~/.gemini/scripts/tier_gate.py`），依 `required_tier = max(Scale, Risk)`（`S2+R2` 升 `T3`；4 層優先序：P1 保護清單 > P2 鎖檔/產物/symlink 排除 > P3 測試防偷刪/純文件 S1 帽 > P4 生產碼語境分軌）驗收，T2/T3 並跑 `python3 scripts/tier_gate.py verify-pass --git-diff`：
  | Tier | 規模（生產碼 `add+del` / 新增 / 刪減 / 檔數 / 新模組>=40行） | 風險自動升格（路徑或變動行，哪怕改 1 行；UI 純展示豁免裸詞） | 強制驗證與獨立複查（禁作者自寫 mock 驗收） |
  | :--- | :--- | :--- | :--- |
  | **T0** | `<=15` / `<=15` / `<=5` / `1` 檔 / `0` 新模組（純文案/CSS 上限 S1） | `R0` 純文案、註解、靜態樣式 | `rule_lint --git-diff` + 既有測試；免開子代理／多模型 |
  | **T1** | `16–60` / `16–50` / `6–15` / `1–2` 檔 / `0` 新模組 | `R1` 一般邏輯、UI 互動、一般測試 | `T0` + 補 `>=1` 失敗邊界單測 + 型別檢查（UI 補 `agent-desktop`/`e2e`） |
  | **T2** | `61–200` / `51–150` / `16–60` / `3–5` 檔 / `>=1` 新模組 | `R2` `routers/api/webhook/crawler/upload/config/parser/indexer/mcp`、SQL 查詢寫入、測試刪斷言 `>15` 行 | `T1` + `multi_model_gate review`（`PASS`/`PASS_DEGRADED`）+ **1 名獨立唯讀複查者** + 真實資料抽核 + `>=5` 對抗邊界 |
  | **T3** | `>200` / `>150` / `>60` / `>=6` 檔 / `>=2` 新模組（或單檔 `>=150` 行）或 `S2+R2` | `R3` `auth/security/rbac/secret/blacklist`、`migrations/turso/supabase/DDL/破壞性SQL`、門禁與規則自身（`GEMINI.md`/`AGENTS.md`/`DECISIONS.md`/`.cursor/rules/*`/`tier_gate`/`rule_lint`/`multi_model_gate`）、`3D/DXF/FOV/財務計價/薪資/sha256/只作廢不刪除`、跨 repo 契約 | `T2` + `multi_model_gate review --include-grok-api`（`PASS`/`PASS_DEGRADED`）+ **3 角色唯讀 `stage-gate-review`**（邏輯破壞/真實語料稽核/對抗 Fuzz 與密鑰掃描；Python I/O 補 CP950 實測）；0 CRITICAL/HIGH 方可放行 |
  - **模型調度三鐵律與降級協議**：Grok 走 Cursor Plan / `grok.exe` Plan；Gemini 外部腳本清空 API Key 優先 `agy.exe --mode plan` → 失敗才退 DPAPI 官方直連 → OpenRouter；Qwen 預設 `qwen4-max-preview`（備 `qwen-max`）。外部 API 故障時具 `>=2` 異質供應商且 0 紅燈並由異質紅隊補位可降級 `PASS_DEGRADED`；全斷網僅限人類設 `LEAN_TRIAD_BYPASS_REASON` 留痕，嚴禁 AI 自填。
  - **反偽造獨立複查鐵律**：獨立複查僅認 Swarm `board#seq`（`agent != author`）、Subagent ID 或 `multi_model_gate` 真實 `request_id`，**硬拒** `cursor-plan-delegated` / `unknown` 與同 Context 自演；T3 缺獨立唯讀角色禁止宣告完成。
- **確定性門禁與技能路由**：
  - 改碼後必跑 `python3 scripts/rule_lint.py --git-diff`（攔截 UI Emoji、按鈕過長/缺 A11y、`<input type="date" lang="en" />`、`.skip`/空 `catch`、`TODO:`/`FIXME:`/`HACK:`/`XXX:`、裸 `bool(str)`/缺 UTF-8/密鑰字面值；僅允許 `// shortcut: <上限條件>, <何時該升級>`）。
  - 前端 UI 遵循 `stageshow` × `impeccable` × `design-taste-frontend`（`.cursor/rules/react-typescript.mdc`）；精簡時禁刪不可逆警告、交易計價/稅額、合規聲明與 SEO/GEO 訊號。
  - 技能檢索：`python3 scripts/skill_router.py route "<任務描述>"` | 技能矩陣：`python3 scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`
- **任務結案白話總結與人機雙讀（`/eli5` × `/ponytail`）**：
  - 改碼走 `/ponytail`；結案之「完成項目」與「重點任務總結」走 `/eli5`（先白話說明影響與差異，再保留檔案路徑／API 原文，不稀釋演算法／契約精度）。
  - `README.md` 採雙層標準：上半部給人看（`/eli5` 白話＋`/diagram-design` 中文架構圖 `nodes <= 9, edges <= 12`），下半部給 AI／工程師看（全庫真實結構、啟動測試指令與跨庫紅線）。
- **收尾誠實揭露與極簡防重複回條（Final-Turn Compact Lean-Triad Receipt）**：
  - **🚫 禁輸出場景**：中繼進度、純合併/部署回報、澄清提問、純問答閒聊，或無新程式碼變更時禁附回條。**🚫 防重複**：每欄僅填關鍵字/路徑/行數/結果（`<= 60` 字），正文與回條不互抄。
  - **✅ 最終交付格式**（僅在最終完成交付結尾輸出一次；T2/T3 缺真實 `req`、`pass:` 或獨立複查一律視為未驗收）：
    ```markdown
    ---
    **🛡️ Lean-Triad**
    - 🧰 **Skills**：`<Skills>`
    - 🧭 **Graphify**：`<節點 / update>`
    - ✂️ **Ponytail**：`+<新增> / -<刪除> 行 (shortcut: <無或註記>)`
    - ⚖️ **Gate & QA**：`<tier_token> | gate:<PASS|PASS_DEGRADED|T0-T1免跑>(score, req=<id1,id2>) | review:<board#seq|subagent:id|NONE> | pass:<path|N/A> | tests:<n/n>`
    - ⚠️ **邊界**：`<略過項目與風險>`
    ```
<!-- END_LEAN_TRIAD_SSOT -->"""


def load_canonical_agents_ssot_block() -> str:
    """優先自單一真相模板 ~/.gemini/templates/agents_ssot_block.md 載入受管區塊，缺檔才退回 inline fallback。"""
    if GLOBAL_AGENTS_SSOT_TEMPLATE.is_file():
        try:
            text = GLOBAL_AGENTS_SSOT_TEMPLATE.read_text(encoding="utf-8").strip()
            if SSOT_BEGIN in text and SSOT_END in text:
                return text
        except OSError:
            # Fall back to inline SSOT block when template file cannot be read
            pass
    return _FALLBACK_AGENTS_SSOT_BLOCK


CANONICAL_AGENTS_SSOT_BLOCK = load_canonical_agents_ssot_block()


def _safe_link_or_copy_dir(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    try:
        if os.path.realpath(src) == os.path.realpath(dst) and dst.exists():
            return
    except OSError:
        # Ignore realpath resolution errors on dangling symlinks and continue
        pass
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.is_file():
        dst.unlink(missing_ok=True)
    if not dst.exists():
        try:
            os.symlink(src, dst, target_is_directory=True)
            return
        except OSError:
            # Fall back to per-item copy or symlink when directory symlink is unsupported
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
    ssot_block = load_canonical_agents_ssot_block()
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
        updated = pattern.sub(lambda _: ssot_block, updated)
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
                updated = lp.sub(lambda _: ssot_block + "\n", updated, count=1)
                replaced = True
                break
        if not replaced:
            if "\n## graphify" in updated:
                updated = updated.replace(
                    "\n## graphify",
                    f"\n{ssot_block}\n\n## graphify",
                    1,
                )
            else:
                updated = updated.rstrip() + f"\n\n{ssot_block}\n"

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
    for fname in SYNCED_SCRIPTS:
        src_f = SCRIPT_DIR / fname
        dst_f = gemini_scripts / fname
        if src_f.is_file():
            try:
                if os.path.realpath(src_f) != os.path.realpath(dst_f):
                    shutil.copy2(src_f, dst_f)
            except OSError:
                # Ignore permission or symlink path resolution errors on read-only mount
                pass

    print(f"[CursorCloudBootstrap] Ready: repo={REPO_ROOT.name}, skills={repo_skills}")


if __name__ == "__main__":
    main()
