#!/usr/bin/env python3
"""全域確定性規則檢查腳本 rule_lint.py 的完整單元與整合測試。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import rule_lint  # noqa: E402


class RuleLintUnitTests(unittest.TestCase):
    """驗證 6 大確定性規則的正反案例、邊界條件與防誤判能力。"""

    def test_ui_no_emoji_positive_and_exemptions(self) -> None:
        bad_tsx = (
            "// 🚀 註解裡的 Emoji 應忽略\n"
            "{/* 🔥 JSX 註解裡的 Emoji 應忽略 */}\n"
            "export function Demo() {\n"
            "  const hint = '⚠️ 注意事項';\n"
            "  return <div>It's OK → ← ↑ ↓ ✓ ✗ <span>🔥 熱賣</span></div>;\n"
            "}\n"
        )
        violations = rule_lint.lint_file_content("src/Demo.tsx", bad_tsx)
        self.assertEqual([v["line"] for v in violations], [4, 5])
        self.assertTrue(all(v["rule_id"] == "UI_NO_EMOJI" for v in violations))
        self.assertIn("pulsoicon-react", violations[0]["fix_hint"])

        # 純標點箭頭與勾叉必須放行
        clean_tsx = "export const Arrows = () => <span>→ ← ↑ ↓ ✓ ✗</span>;\n"
        self.assertEqual(rule_lint.lint_file_content("src/Arrows.tsx", clean_tsx), [])

        # .vue / .svelte 同樣受保護，且忽略 HTML 註解
        vue_src = (
            "<template>\n"
            "  <!-- 🎉 註解放行 -->\n"
            "  <p>✅ 完成</p>\n"
            "</template>\n"
        )
        vue_violations = rule_lint.lint_file_content("src/Comp.vue", vue_src)
        self.assertEqual(len(vue_violations), 1)
        self.assertEqual(vue_violations[0]["line"], 3)

        # 測試檔 *.test.tsx 與非 UI 副檔名 .ts 必須豁免
        self.assertEqual(rule_lint.lint_file_content("src/Demo.test.tsx", bad_tsx), [])
        self.assertEqual(rule_lint.lint_file_content("src/logic.ts", "const x = '🚀';\n"), [])

    def test_ui_icon_btn_a11y_single_and_multiline(self) -> None:
        tsx = (
            "export function Toolbar({ onSave, onDelete, label }: any) {\n"
            "  const sample = '<button><Save /></button>';\n"
            "  return (\n"
            "    <div>\n"
            "      <button onClick={() => onSave(1)}><Save className=\"w-4 h-4\" /></button>\n"
            "      <Button\n"
            "        variant=\"ghost\"\n"
            "        onClick={() => onDelete(1)}\n"
            "      >\n"
            "        {/* 僅含 SVG 無文字 */}\n"
            "        <svg viewBox=\"0 0 24 24\"><path d=\"M0 0\" /></svg>\n"
            "      </Button>\n"
            "      <button aria-label=\"儲存資料\" onClick={onSave}><Save /></button>\n"
            "      <button title=\"刪除項目\" onClick={onDelete}><Trash2 /></button>\n"
            "      <button onClick={onSave}><Save /> 儲存</button>\n"
            "      <button onClick={onSave}><Save />{label}</button>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )
        violations = rule_lint.lint_file_content("src/Toolbar.tsx", tsx)
        self.assertEqual(len(violations), 2)
        self.assertEqual([v["rule_id"] for v in violations], ["UI_ICON_BTN_A11Y", "UI_ICON_BTN_A11Y"])
        self.assertEqual([v["line"] for v in violations], [5, 6])
        self.assertIn("aria-label", violations[0]["fix_hint"])

    def test_ui_compact_button_and_protected_risk_keywords(self) -> None:
        tsx = (
            "export function Actions({ saving }: { saving: boolean }) {\n"
            "  return (\n"
            "    <div>\n"
            "      <button>立即點擊這裡產生全部月份報表</button>\n"
            "      <Button><span>匯出所有客戶完整交易明細表</span></Button>\n"
            "      <button>匯出全部報表</button>\n"
            "      <button>新增批次</button>\n"
            "      <button>{saving ? '正在儲存全部交易資料請稍候' : '儲存'}</button>\n"
            "      <button>此操作刪除後無法復原請確認</button>\n"
            "      <button>送出後不可逆轉請再次檢查資料</button>\n"
            "      <button>立即刪除這筆過期的訂單紀錄</button>\n"
            "      <button>計算含稅總金額並開立電子發票</button>\n"
            "      <button>我已閱讀並同意全部會員規範</button>\n"
            "      <button>確認接受本服務條款並立即啟用</button>\n"
            "      <button>立即簽署正式合作合約並送出</button>\n"
            "      <button>確認作廢此張已開立之發票</button>\n"
            "      <button>確認沖銷本筆應收帳款紀錄</button>\n"
            "      <button>確認執行本日門市日結帳作業</button>\n"
            "      <button>確認核銷這筆待處理預付款項</button>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )
        violations = rule_lint.lint_file_content("src/Actions.tsx", tsx)
        self.assertEqual(len(violations), 2)
        self.assertEqual([v["rule_id"] for v in violations], ["UI_COMPACT_BUTTON", "UI_COMPACT_BUTTON"])
        self.assertEqual([v["line"] for v in violations], [4, 5])

    def test_web_date_input_lang_and_dangerous_html(self) -> None:
        tsx = (
            "export function Form({ html }: { html: string }) {\n"
            "  return (\n"
            "    <form>\n"
            "      <input type=\"date\" className=\"border\" />\n"
            "      <input\n"
            "        type={'date'}\n"
            "        name=\"end\"\n"
            "      />\n"
            "      <input type=\"date\" lang=\"en\" />\n"
            "      <input type={'date'} lang={'en'} />\n"
            "      {/* <input type=\"date\" /> dangerouslySetInnerHTML */}\n"
            "      <div dangerouslySetInnerHTML={{ __html: html }} />\n"
            "    </form>\n"
            "  );\n"
            "}\n"
        )
        violations = rule_lint.lint_file_content("src/Form.tsx", tsx)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in violations],
            [
                ("WEB_DATE_INPUT_LANG", 4),
                ("WEB_DATE_INPUT_LANG", 5),
                ("WEB_NO_DANGEROUS_HTML", 12),
            ],
        )

        # .html 與 .vue 同樣適用 WEB_* 規則
        html_src = "<form><input type='date'><input type='date' lang='en'></form>\n"
        html_v = rule_lint.lint_file_content("public/index.html", html_src)
        self.assertEqual([(v["rule_id"], v["line"]) for v in html_v], [("WEB_DATE_INPUT_LANG", 1)])

    def test_test_no_skip_python_and_js_with_string_protection(self) -> None:
        py_test = (
            "import pytest\n"
            "import unittest\n"
            "\n"
            "# @pytest.mark.skip 註解不可誤報\n"
            'TEXT_SAMPLE = "@pytest.mark.skip @unittest.skip pytest.skip(\'x\')"\n'
            'FSTR_SAMPLE = f"pytest.skip({1 + 1})"\n'
            "\n"
            "@pytest.mark.skip(reason='broken')\n"
            "def test_one():\n"
            "    assert True\n"
            "\n"
            "@unittest.skip('later')\n"
            "def test_two():\n"
            "    assert True\n"
            "\n"
            "def test_three():\n"
            "    pytest.skip('runtime skip')\n"
        )
        py_v = rule_lint.lint_file_content("tests/test_sample.py", py_test)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in py_v],
            [("TEST_NO_SKIP", 8), ("TEST_NO_SKIP", 12), ("TEST_NO_SKIP", 17)],
        )
        # 非測試檔即使有字串也不會報 TEST_NO_SKIP
        self.assertEqual(rule_lint.lint_file_content("src/helper.py", py_test), [])

        js_test = (
            "// it.skip('ignored comment', () => {})\n"
            "const str = \"test.skip('ignored string')\";\n"
            "it.skip('a', () => {});\n"
            "test.skip('b', () => {});\n"
            "describe.skip('c', () => {});\n"
            "xit('d', () => {});\n"
            "xtest('e', () => {});\n"
            "xdescribe('f', () => {});\n"
        )
        js_v = rule_lint.lint_file_content("src/foo.spec.ts", js_test)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in js_v],
            [("TEST_NO_SKIP", ln) for ln in (3, 4, 5, 6, 7, 8)],
        )

    def test_no_silent_catch_python_and_js(self) -> None:
        py_src = (
            "import logging\n"
            "\n"
            "def bad_pass():\n"
            "    try:\n"
            "        1 / 0\n"
            "    except ZeroDivisionError:\n"
            "        pass\n"
            "\n"
            "def bad_ellipsis():\n"
            "    try:\n"
            "        1 / 0\n"
            "    except Exception:\n"
            "        ...\n"
            "\n"
            "def good_commented():\n"
            "    try:\n"
            "        1 / 0\n"
            "    except ZeroDivisionError:\n"
            "        # 明確記錄原因即可豁免\n"
            "        pass\n"
            "\n"
            "def good_logged():\n"
            "    try:\n"
            "        1 / 0\n"
            "    except ZeroDivisionError as exc:\n"
            "        logging.warning('err: %s', exc)\n"
        )
        py_v = rule_lint.lint_file_content("src/service.py", py_src)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in py_v],
            [("NO_SILENT_CATCH", 6), ("NO_SILENT_CATCH", 12)],
        )

        js_src = (
            "const msg = 'catch (e) {}';\n"
            "// catch (e) {}\n"
            "try { a(); } catch (e) {}\n"
            "try { b(); } catch {\n"
            "}\n"
            "try { c(); } catch (err) { /* 故意忽略非關鍵快取 */ }\n"
        )
        js_v = rule_lint.lint_file_content("src/service.ts", js_src)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in js_v],
            [("NO_SILENT_CATCH", 3), ("NO_SILENT_CATCH", 4)],
        )

    def test_no_excuse_comment_and_shortcut_validation(self) -> None:
        py_src = (
            'TEXT_1 = "# TODO: 字串不可誤判"\n'
            'TEXT_2 = """\n'
            "FIXME: 多行字串不可誤判\n"
            'temporary workaround\n'
            '"""\n'
            "# TODO: 真實註解應攔截\n"
            "# fixme: 小寫也應攔截\n"
            "# HACK: 臨時寫法\n"
            "# XXX: 問題標記\n"
            "# This is a temporary workaround for bug\n"
            "# quick fix before demo\n"
            "# will fix later\n"
            "# shortcut: 缺逗號與升級時機\n"
            "# shortcut: a, 條件太短\n"
            "# shortcut: 記憶體上限 500 筆, 超過時改用分頁查詢\n"
        )
        py_v = rule_lint.lint_file_content("src/mod.py", py_src)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in py_v],
            [("NO_EXCUSE_COMMENT", ln) for ln in (6, 7, 8, 9, 10, 11, 12, 13, 14)],
        )

        ts_src = (
            "const s1 = '// TODO: 字串內不可誤判';\n"
            "const s2 = `/* FIXME: 樣板字串不可誤判 */`;\n"
            "const re = /\\/\\* TODO: 不可誤判 \\*\\//;\n"
            "const url = 'https://example.com/TODO:1';\n"
            "// TODO: 真實單行註解應攔截\n"
            "/*\n"
            " * line 7 ok\n"
            " * FIXME: 多行註解應精準報第 8 行\n"
            " */\n"
            "// shortcut: 單頁最多 100 列, 超過改為虛擬捲動\n"
            "// shortcut: broken_format\n"
        )
        ts_v = rule_lint.lint_file_content("src/mod.ts", ts_src)
        self.assertEqual(
            [(v["rule_id"], v["line"]) for v in ts_v],
            [
                ("NO_EXCUSE_COMMENT", 5),
                ("NO_EXCUSE_COMMENT", 8),
                ("NO_EXCUSE_COMMENT", 11),
            ],
        )


class GitDiffAndCliTests(unittest.TestCase):
    """驗證 lint_git_diff 新增行精準定位、CLI exit code 與自我狗食檢查。"""

    def test_lint_git_diff_targets_only_added_lines_and_ignores_deleted_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True)
            # 第 2 行是既有的舊違規（未被 diff 觸及，不可誤報）；第 6 行是新增的違規
            tsx_content = (
                "export function Page() {\n"
                "  const oldBad = <div>🔥 舊有違規</div>;\n"
                "  const ok = <span>正常文字</span>;\n"
                "  return (\n"
                "    <div>\n"
                "      <Button onClick={() => 1}><Save /></Button>\n"
                "      <input\n"
                "        type=\"date\"\n"
                "        name=\"d\"\n"
                "      />\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            (root / "src" / "Page.tsx").write_text(tsx_content, encoding="utf-8")

            # 同時測試 hunk 內出現 +++i; 不會誤判為新檔頭，以及 /dev/null 刪除檔被忽略
            (root / "src" / "calc.ts").write_text(
                "let i = 0;\n++i;\n", encoding="utf-8"
            )

            diff_text = (
                "diff --git a/src/Removed.tsx b/src/Removed.tsx\n"
                "deleted file mode 100644\n"
                "--- a/src/Removed.tsx\n"
                "+++ /dev/null\n"
                "@@ -1,2 +0,0 @@\n"
                "-const x = '🔥';\n"
                "-// TODO: gone\n"
                "diff --git a/src/Page.tsx b/src/Page.tsx\n"
                "--- a/src/Page.tsx\n"
                "+++ b/src/Page.tsx\n"
                "@@ -5,2 +5,4 @@\n"
                "     <div>\n"
                "+      <Button onClick={() => 1}><Save /></Button>\n"
                "       <input\n"
                "+        type=\"date\"\n"
                "diff --git a/src/calc.ts b/src/calc.ts\n"
                "--- a/src/calc.ts\n"
                "+++ b/src/calc.ts\n"
                "@@ -1 +1,2 @@\n"
                " let i = 0;\n"
                "+++i;\n"
            )

            report = rule_lint.lint_git_diff(diff_text, repo_root=root)
            self.assertFalse(report["passed"])
            self.assertEqual(report["files_checked"], 2)
            self.assertEqual(report["error_count"], 2)
            self.assertEqual(report["warning_count"], 0)
            self.assertEqual(
                [(v["file"], v["rule_id"], v["line"]) for v in report["violations"]],
                [
                    ("src/Page.tsx", "UI_ICON_BTN_A11Y", 6),
                    ("src/Page.tsx", "WEB_DATE_INPUT_LANG", 8),
                ],
            )

    def test_cli_exit_codes_text_format_and_stdin(self) -> None:
        script_path = SCRIPTS_DIR / "rule_lint.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_file = root / "Bad.tsx"
            good_file = root / "Good.tsx"
            bad_file.write_text(
                "export const Bad = () => <button><Plus /></button>;\n",
                encoding="utf-8",
            )
            good_file.write_text(
                "export const Good = () => <button aria-label='新增'><Plus /></button>;\n",
                encoding="utf-8",
            )

            res_bad = subprocess.run(
                [sys.executable, str(script_path), "--files", str(bad_file), "--format", "text"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_bad.returncode, 1)
            self.assertIn(f"[ERROR][UI_ICON_BTN_A11Y] {bad_file}:1 —", res_bad.stdout)
            self.assertIn("  ↳ Snippet: ", res_bad.stdout)
            self.assertIn("  ↳ 修復指引: ", res_bad.stdout)

            res_good = subprocess.run(
                [sys.executable, str(script_path), "--files", str(good_file), "--format", "json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_good.returncode, 0)
            good_json = json.loads(res_good.stdout)
            self.assertTrue(good_json["passed"])
            self.assertEqual(good_json["error_count"], 0)

            res_stdin = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--stdin",
                    "--filename",
                    "src/Input.tsx",
                    "--format",
                    "json",
                ],
                input="export const D = () => <input type='date' />;\n",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_stdin.returncode, 1)
            stdin_json = json.loads(res_stdin.stdout)
            self.assertFalse(stdin_json["passed"])
            self.assertEqual(stdin_json["violations"][0]["rule_id"], "WEB_DATE_INPUT_LANG")

    def test_cli_git_diff_with_real_git_repo_and_commit_filter(self) -> None:
        script_path = SCRIPTS_DIR / "rule_lint.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Tester"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)

            (repo / "clean.py").write_text("x = 1\n", encoding="utf-8")
            (repo / "bad.py").write_text("y = 2\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)

            (repo / "bad.py").write_text(
                "def f():\n    try:\n        return 1\n    except ValueError:\n        pass\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", str(repo), "add", "bad.py"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "bad"], check=True, capture_output=True)

            # 檢查指定 commit 且帶 --paths 過濾
            res_commit = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--git-diff",
                    "--repo",
                    str(repo),
                    "--commit",
                    "HEAD",
                    "--paths",
                    "bad.py",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_commit.returncode, 1)
            data = json.loads(res_commit.stdout)
            self.assertEqual(data["error_count"], 1)
            self.assertEqual(data["violations"][0]["rule_id"], "NO_SILENT_CATCH")

            # 工作區乾淨時 --git-diff 應回傳 0
            res_clean = subprocess.run(
                [sys.executable, str(script_path), "--git-diff", "--repo", str(repo), "--format", "json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_clean.returncode, 0)
            self.assertTrue(json.loads(res_clean.stdout)["passed"])

            # 新增未追蹤檔案時，未指定 --commit 的 --git-diff 必須一併檢查（並忽略快取與依賴目錄）
            (repo / "src").mkdir()
            (repo / "src" / "NewBad.tsx").write_text(
                "export const Bad = () => <span>🔥 新檔漏網測試</span>;\n",
                encoding="utf-8",
            )
            (repo / ".venv").mkdir()
            (repo / ".venv" / "ignored.py").write_text(
                "try:\n    x = 1\nexcept ValueError:\n    pass\n",
                encoding="utf-8",
            )
            (repo / "node_modules").mkdir()
            (repo / "node_modules" / "pkg.tsx").write_text(
                "export const Pkg = () => <span>🚀</span>;\n",
                encoding="utf-8",
            )
            (repo / "notes.md").write_text("🚀 markdown\n", encoding="utf-8")

            res_untracked = subprocess.run(
                [sys.executable, str(script_path), "--git-diff", "--repo", str(repo), "--format", "json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_untracked.returncode, 1)
            untracked_data = json.loads(res_untracked.stdout)
            self.assertEqual(untracked_data["files_checked"], 1)
            self.assertEqual(untracked_data["error_count"], 1)
            self.assertEqual(untracked_data["violations"][0]["file"], "src/NewBad.tsx")
            self.assertEqual(untracked_data["violations"][0]["rule_id"], "UI_NO_EMOJI")

            # 指定 --commit 時不應納入工作區未追蹤檔案
            res_commit_clean = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--git-diff",
                    "--repo",
                    str(repo),
                    "--commit",
                    "HEAD",
                    "--paths",
                    "bad.py",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(res_commit_clean.returncode, 1)
            self.assertEqual(
                [v["file"] for v in json.loads(res_commit_clean.stdout)["violations"]],
                ["bad.py"],
            )

    def test_self_dogfooding(self) -> None:
        """腳本本身與本測試檔案必須 0 違規通過 rule_lint 自我檢查。"""
        for filename in ("rule_lint.py", "test_rule_lint.py"):
            path = SCRIPTS_DIR / filename
            content = path.read_text(encoding="utf-8")
            violations = rule_lint.lint_file_content(filename, content)
            self.assertEqual(violations, [], f"{filename} 不得有任何自我檢查違規: {violations}")


if __name__ == "__main__":
    unittest.main()
