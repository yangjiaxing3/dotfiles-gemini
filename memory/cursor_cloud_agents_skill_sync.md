# Cursor Cloud Agents 全域 Skills 與 Lean-Triad 同步架構

## `[Anti-Pattern 錯誤模式]`
- 僅將全域規則（如 `Lean-Triad`、`Ponytail`、強制執行回條、角色×任務動態技能矩陣）與 Skills 存放在本機 Windows 的 `C:\Users\Jiaxing\.gemini\` 或透過 NTFS Directory Junction (`mklink /J`) 映射至 `C:\Users\Jiaxing\.cursor\skills\`。
- 在 `.cursor/rules/*.mdc` 與 `skill_router.py` 寫死 `C:\Users\Jiaxing\...` 本機絕對路徑。
- 在 `.gitignore` 中忽略 `.agent/`、`.agents/` 或 `.cursor/*`（未放行 `!.cursor/rules`）。
- **後果**：當 **Cursor Cloud Agents（Background / Remote Cloud Agents）** 在雲端隔離 Linux 容器 (`/workspace`) 執行 `git clone` 時，完全讀不到本機 `C:\Users\Jiaxing\...` 磁碟與 NTFS Junction，導致 `Lean-Triad` 與 158 個全域 Skills 失效。

## `[Correct-Pattern 正確作法]`
1. **跨平台雙棲路由器與會審閘門 (`scripts/skill_router.py` & `scripts/multi_model_gate.py`)**：
   - 自動偵測執行環境（Linux 容器 `/workspace` vs Windows 本機），優先掃描專案內 `.agents/skills`、`.agent/skills`、`.cursor/skills`，本機再補充 `~/.gemini/config/skills`。
2. **雲端與本機雙軌相容之 `.cursor/rules/*.mdc`**：
   - `engineering-core.mdc` 與 `skill-routing-and-swarm-v3.mdc` 直接內嵌完整 `Lean-Triad` 常駐引擎、`Ponytail` 極簡守則、`Role-Scoped × Task-Aware Skill Binding` 矩陣與 `🛡️ Lean-Triad 執行回條`，並優先使用專案相對路徑 `python scripts/skill_router.py` 與 `python scripts/multi_model_gate.py`。
3. **容器啟動自動掛載 (`.cursor/environment.json` + `scripts/bootstrap_cursor_cloud.py`)**：
   - 雲端 Linux 容器啟動時自動將專案內 `.agents/skills`、`.cursor/rules`、`scripts/` 連結至容器內的 `~/.cursor/skills`、`~/.gemini/config/skills` 與 `~/.gemini/scripts`。
4. **一鍵同步腳本 (`C:\Users\Jiaxing\.gemini\scripts\sync_skills_to_cloud_repos.py`)**：
   - 任何全域 Skill 或 Rule 更新後，執行：
     ```powershell
     python C:\Users\Jiaxing\.gemini\scripts\sync_skills_to_cloud_repos.py
     ```
   - 自動將 13 個 `.cursor/rules/*.mdc`、跨平台腳本與 158 個通過 Linter 門禁（0 超標、Recall@3 100%）的純淨輕量 Skills 同步至 `Huanxin-3Dimen` 與 Storeasy 聯動家族全部 7 個專案的 `.agents/skills/` 與 `.cursor/skills/`。
