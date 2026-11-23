#!/usr/bin/env python3
"""全域確定性規則檢查腳本 (Rule Lint Gate)。

僅使用 Python >= 3.10 標準庫，針對程式碼與 Unified Git Diff 執行確定性規則檢查，
攔截 UI Emoji、缺 A11y 純圖示按鈕、過長操作按鈕文案、不當 date/HTML 寫法、
測試跳過作弊、靜默吞錯以及未獲授權之藉口註解。
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 副檔名與規則常數定義
# ---------------------------------------------------------------------------

UI_EMOJI_EXTS = frozenset({".tsx", ".jsx", ".vue", ".svelte"})
UI_JSX_EXTS = frozenset({".tsx", ".jsx"})
WEB_EXTS = frozenset({".tsx", ".jsx", ".html", ".vue"})
PY_EXTS = frozenset({".py"})
JS_EXTS = frozenset({".ts", ".tsx", ".js", ".jsx"})
RELEVANT_EXTS = UI_EMOJI_EXTS | UI_JSX_EXTS | WEB_EXTS | PY_EXTS | JS_EXTS
IGNORED_MIRROR_TOP_DIRS = frozenset({".agent", ".agents", ".cursor"})
IGNORED_UNTRACKED_DIRS = frozenset(
    {
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".git",
        ".agent",
        ".agents",
        ".cursor",
        "dist",
        "build",
        ".next",
        ".turbo",
        ".cache",
        "coverage",
    }
)

# 排除純標點與箭頭符號：→ (\u2192), ← (\u2190), ↑ (\u2191), ↓ (\u2193), ✓ (\u2713), ✗ (\u2717)
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U0001F1E6-\U0001F1FF"
    "\U0001F000-\U0001F02F"
    "\U0001F0A0-\U0001F0FF"
    "\u2600-\u2712"
    "\u2714-\u2716"
    "\u2718-\u27BF"
    "\u231A-\u231B"
    "\u23E9-\u23F3"
    "\u23F8-\u23FA"
    "\u2B50\u2B55"
    "]"
)

CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")
PROTECTED_RISK_KEYWORDS = (
    "無法復原",
    "不可逆",
    "刪除",
    "稅",
    "同意",
    "條款",
    "合約",
    "作廢",
    "沖銷",
    "結帳",
    "核銷",
)

A11Y_ATTR_RE = re.compile(r"\b(?:aria-label|title)\s*=")
DATE_TYPE_ATTR_RE = re.compile(
    r"""\btype\s*=\s*(?:["']date["']|\{\s*["']date["']\s*\})"""
)
LANG_EN_ATTR_RE = re.compile(
    r"""\blang\s*=\s*(?:["']en["']|\{\s*["']en["']\s*\})"""
)
DANGEROUS_HTML_RE = re.compile(r"\bdangerouslySetInnerHTML\b")
NT_DOLLAR_RE = re.compile(r"NT\$")
SIDE_STRIPE_RE = re.compile(r"\bborder-l-[248]\b")
BLOCKQUOTE_TAG_RE = re.compile(r"<blockquote\b", re.IGNORECASE)
PLAIN_LOADING_JSX_RE = re.compile(
    r">\s*[^<>{}\n]{0,12}(?:載入中|讀取中|資料載入|Loading\.\.\.)[^<>{}\n]{0,6}\s*<"
)
LOADING_COMPONENT_RE = re.compile(
    r"Loader|Spinner|LoadingSvg|StatusStates|animate-spin|Skeleton"
)

JS_SKIP_RE = re.compile(
    r"\b(?:(?:it|test|describe)\.skip|x(?:it|test|describe))\s*\("
)
JS_EMPTY_CATCH_RE = re.compile(r"\bcatch\s*(?:\([^)]*\))?\s*\{\s*\}")

EXCUSE_COMMENT_RE = re.compile(
    r"(?:\b(?:TODO|FIXME|HACK|XXX)\s*:|\b(?:temporary\s+workaround|quick\s+fix|fix\s+later)\b)",
    re.IGNORECASE,
)
SHORTCUT_PREFIX_RE = re.compile(r"\bshortcut\s*:", re.IGNORECASE)
SHORTCUT_VALID_RE = re.compile(r"\bshortcut:\s*([^,\n]+),\s*\S+")

URL_SCHEME_BEFORE_SLASH_RE = re.compile(r"(?:https?|wss?|ftp|file|mailto|tel|data):$", re.IGNORECASE)
REGEX_PRECEDING_WORDS = frozenset(
    {"return", "typeof", "void", "delete", "case", "yield", "await", "throw", "in", "of", "else"}
)

# 規則說明與單行修復指引集中管理
RULE_META: dict[str, tuple[str, str]] = {
    "UI_NO_EMOJI": (
        "UI 元件不可使用 Emoji 圖示字元，應使用一致的向量圖示系統。",
        "移除 Emoji，改用 pulsoicon-react 或 lucide-react 同名 SVG 圖示（w-4 h-4 strokeWidth={1.75}）。",
    ),
    "UI_ICON_BTN_A11Y": (
        "純圖示按鈕缺少無障礙說明屬性（aria-label 與 title 不可同時缺席）。",
        '補齊 aria-label="2～4字動賓短語" 與 title="2～4字動賓短語"。',
    ),
    "UI_COMPACT_BUTTON": (
        "操作按鈕純靜態中文字數超過 6 字且不含受保護風險關鍵詞，過於冗長。",
        "操作按鈕文案精簡為 2～4 字動賓結構（如 新增批次、匯出報表、儲存資料），勿刪風險警告。",
    ),
    "UI_NO_NT_DOLLAR": (
        "介面金額與格式化輸出禁止使用 NT$，全系統金額一律使用 $。",
        "將 NT$ 改為 $（如 $1,000、$/坪、$/才）。",
    ),
    "UI_NO_SIDE_STRIPE": (
        "禁止於卡片或面板使用側邊粗色條（border-l-2 / border-l-4 / border-l-8）。",
        "改用單層實色卡片搭配 1px 細邊框與柔和語意底色。",
    ),
    "UI_NO_PLAIN_TEXT_LOADING": (
        "禁止僅以純文字顯示載入狀態（如「載入中」），違反 DESIGN.md 載入元件規範。",
        "改用 SectionLoader、LoadingSpinner 或 LoadingSvg 動態骨架元件。",
    ),
    "WEB_DATE_INPUT_LANG": (
        '日期輸入框 <input type="date"> 缺少 lang="en" 屬性，會導致跨語系瀏覽器顯示與輸入行為不一致。',
        '補上 lang="en" 屬性（例如 <input type="date" lang="en" />）。',
    ),
    "WEB_NO_DANGEROUS_HTML": (
        "使用 dangerouslySetInnerHTML 會直接暴露 XSS 注入風險並繞過 React DOM 安全轉義。",
        "移除 dangerouslySetInnerHTML，改用純 React JSX 元件或結構化資料渲染。",
    ),
    "TEST_NO_SKIP": (
        "禁止使用 skip 標記跳過測試案例，必須修復程式邏輯或測試資料使斷言通過。",
        "移除 skip 標記（@pytest.mark.skip / @unittest.skip / pytest.skip / .skip），修復測試或實作。",
    ),
    "NO_SILENT_CATCH": (
        "禁止空白 catch 或無說明註解的 except: pass 靜默吞掉例外。",
        "補上明確錯誤處理（記錄日誌或重新拋出），若確屬預期忽略則加註清楚原因。",
    ),
    "NO_EXCUSE_COMMENT": (
        "禁止新增逃生門／藉口註解（TODO/FIXME/HACK/XXX/workaround）或格式不合規的 shortcut 註解。",
        "移除藉口註解並立即處理問題；若確有場景上限，改用合法格式「shortcut: <上限條件>, <何時該升級>」。",
    ),
    "NO_EXCUSE_COMMENT_SHORTCUT": (
        "shortcut 註解未包含有效上限條件與升級時機。",
        "補足 shortcut 註解格式為「shortcut: <上限條件(>=2字)>, <何時該升級>」。",
    ),
}


@dataclass(slots=True)
class _JsScanResult:
    """JS/TS/JSX/Vue/HTML 單趟詞法掃描結果。"""

    comment_masked: str
    string_masked: str
    code_only: str
    comments: list[tuple[int, str]]


@dataclass(slots=True)
class _JsxElement:
    """解析後的 JSX/HTML 標籤結構。"""

    tag_name: str
    attrs: str
    inner_raw: str
    start_line: int
    end_line: int
    is_self_closing: bool


# ---------------------------------------------------------------------------
# 基礎路徑與文字輔助
# ---------------------------------------------------------------------------


def _normalize_rel_path(rel_path: str) -> Path:
    return Path(rel_path.replace("\\", "/"))


def _is_ignored_mirror_path(rel_path: str) -> bool:
    """檢查路徑是否位於受管技能／規則鏡像目錄（.agent/.agents/.cursor），避免被 diff 門禁誤報。"""
    parts = _normalize_rel_path(rel_path).parts
    return bool(parts and parts[0] in IGNORED_MIRROR_TOP_DIRS)


def _is_test_file(rel_path: str) -> bool:
    name = _normalize_rel_path(rel_path).name.lower()
    return (
        ".test." in name
        or ".spec." in name
        or (name.startswith("test_") and name.endswith(".py"))
        or name.endswith("_test.py")
    )


def _line_offsets(content: str) -> list[int]:
    """回傳每一行（1-based 對應索引 i-1）在 content 中的起始字元位移。"""
    offsets = [0]
    for idx, ch in enumerate(content):
        if ch == "\n":
            offsets.append(idx + 1)
    return offsets


def _offset_to_line(offsets: list[int], pos: int) -> int:
    """利用二分搜尋將字元位移轉換為 1-based 行號。"""
    lo, hi = 0, len(offsets) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if offsets[mid] <= pos:
            lo = mid + 1
        else:
            hi = mid - 1
    return hi + 1


def _make_snippet(lines: list[str], line_no: int) -> str:
    if 1 <= line_no <= len(lines):
        raw = lines[line_no - 1].strip()
    else:
        raw = ""
    if len(raw) > 140:
        return raw[:137] + "..."
    return raw


def _make_violation(
    rule_id: str,
    rel_path: str,
    line_no: int,
    lines: list[str],
    *,
    meta_key: str | None = None,
    severity: str = "error",
) -> dict[str, Any]:
    why, fix_hint = RULE_META[meta_key or rule_id]
    return {
        "rule_id": rule_id,
        "severity": severity,
        "file": rel_path,
        "line": line_no,
        "snippet": _make_snippet(lines, line_no),
        "why": why,
        "fix_hint": fix_hint,
    }


def _pick_report_line(start_line: int, end_line: int, added_lines: set[int] | None) -> int | None:
    """若 added_lines 為 None 傳回 start_line；否則僅在區塊與 added_lines 有交集時傳回命中行。"""
    if added_lines is None:
        return start_line
    if start_line in added_lines:
        return start_line
    hits = [ln for ln in range(start_line, end_line + 1) if ln in added_lines]
    if not hits:
        return None
    return hits[0]


# ---------------------------------------------------------------------------
# 詞法掃描與遮罩 (JS/TS/JSX/Vue/Svelte/HTML)
# ---------------------------------------------------------------------------


def _has_closing_quote_on_line(content: str, start: int, quote: str) -> bool:
    """檢查單/雙引號在同一行（允許反斜線續行）內是否能正常閉合，以避開 JSX 文本撇號。"""
    n = len(content)
    i = start + 1
    while i < n:
        ch = content[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "\n":
            return False
        if ch == quote:
            return True
        i += 1
    return False


def _find_regex_end_on_line(content: str, start: int) -> int | None:
    """嘗試在同一行內解析 JS 正規表示式字面量 /.../flags 的結尾位移。"""
    n = len(content)
    i = start + 1
    in_class = False
    while i < n:
        ch = content[i]
        if ch == "\n":
            return None
        if ch == "\\":
            i += 2
            continue
        if ch == "[":
            in_class = True
        elif ch == "]":
            in_class = False
        elif ch == "/" and not in_class:
            j = i + 1
            while j < n and content[j].isalpha():
                j += 1
            return j
        i += 1
    return None


def _is_regex_start(content: str, pos: int) -> bool:
    """根據 `/` 前方最後一個非空白字元或關鍵字判斷是否可能為正規表示式起始。"""
    j = pos - 1
    while j >= 0 and content[j] in " \t\r\n":
        j -= 1
    if j < 0:
        return True
    ch = content[j]
    if ch in "([{,;:=!&|?~^+-*%":
        return True
    if ch == ">" and j > 0 and content[j - 1] == "=":
        return True
    if ch.isalnum() or ch in "_$":
        k = j
        while k >= 0 and (content[k].isalnum() or content[k] in "_$"):
            k -= 1
        word = content[k + 1 : j + 1]
        return word in REGEX_PRECEDING_WORDS
    return False


def _scan_js_like(
    content: str,
    *,
    allow_jsx: bool,
    allow_html_comments: bool,
    enable_slash_comments: bool = True,
) -> _JsScanResult:
    """掃描程式碼，同步產出：僅遮罩註解、僅遮罩字串、註解與字串皆遮罩、註解行清單。"""
    n = len(content)
    comment_masked = list(content)
    string_masked = list(content)
    code_only = list(content)
    comments: list[tuple[int, str]] = []

    def _blank(buf: list[str], start: int, end: int) -> None:
        for k in range(start, end):
            if buf[k] != "\n":
                buf[k] = " "

    i = 0
    line_no = 1
    # 追蹤 template literal `${ ... }` 的大括號巢狀深度，以及是否正處於 template 文字段
    template_brace_stack: list[int] = []
    in_template_text = False
    tpl_start = 0

    while i < n:
        ch = content[i]

        if in_template_text:
            if ch == "\\":
                if i + 1 < n and content[i + 1] == "\n":
                    line_no += 1
                i += 2
                continue
            if ch == "\n":
                line_no += 1
                i += 1
                continue
            if ch == "$" and i + 1 < n and content[i + 1] == "{":
                _blank(string_masked, tpl_start, i)
                _blank(code_only, tpl_start, i)
                template_brace_stack.append(1)
                in_template_text = False
                i += 2
                continue
            if ch == "`":
                _blank(string_masked, tpl_start, i)
                _blank(code_only, tpl_start, i)
                in_template_text = False
                i += 1
                continue
            i += 1
            continue

        # 若位於 template literal 內部的 `${...}` 表達式結束處，切回掃描 template 文字段
        if template_brace_stack:
            if ch == "{":
                template_brace_stack[-1] += 1
            elif ch == "}":
                template_brace_stack[-1] -= 1
                if template_brace_stack[-1] == 0:
                    template_brace_stack.pop()
                    i += 1
                    in_template_text = True
                    tpl_start = i
                    continue

        # HTML 註解 <!-- ... -->
        if allow_html_comments and content.startswith("<!--", i):
            end = content.find("-->", i + 4)
            end = n if end == -1 else end + 3
            raw_comment = content[i:end]
            for offset, c_line in enumerate(raw_comment.splitlines()):
                comments.append((line_no + offset, c_line))
            _blank(comment_masked, i, end)
            _blank(code_only, i, end)
            line_no += raw_comment.count("\n")
            i = end
            continue

        # 單行註解 // ...（排除 https:// 等協定斜線）
        if (
            enable_slash_comments
            and ch == "/"
            and i + 1 < n
            and content[i + 1] == "/"
            and not URL_SCHEME_BEFORE_SLASH_RE.search(content[max(0, i - 16) : i])
        ):
            nl = content.find("\n", i)
            end = n if nl == -1 else nl
            comments.append((line_no, content[i:end]))
            _blank(comment_masked, i, end)
            _blank(code_only, i, end)
            i = end
            continue

        # 多行註解 /* ... */
        if enable_slash_comments and ch == "/" and i + 1 < n and content[i + 1] == "*":
            end = content.find("*/", i + 2)
            end = n if end == -1 else end + 2
            raw_comment = content[i:end]
            for offset, c_line in enumerate(raw_comment.splitlines()):
                comments.append((line_no + offset, c_line))
            _blank(comment_masked, i, end)
            _blank(code_only, i, end)
            line_no += raw_comment.count("\n")
            i = end
            continue

        # 單引號或雙引號字串
        if ch in ("'", '"'):
            if allow_jsx and not _has_closing_quote_on_line(content, i, ch):
                i += 1
                continue
            j = i + 1
            closed = False
            while j < n:
                sch = content[j]
                if sch == "\\":
                    if j + 1 < n and content[j + 1] == "\n":
                        line_no += 1
                    j += 2
                    continue
                if sch == "\n":
                    break
                if sch == ch:
                    j += 1
                    closed = True
                    break
                j += 1
            if closed:
                _blank(string_masked, i + 1, j - 1)
                _blank(code_only, i + 1, j - 1)
                i = j
            else:
                i += 1
            continue

        # Template literal `...`
        if ch == "`":
            in_template_text = True
            tpl_start = i + 1
            i += 1
            continue

        # JS 正規表示式字面量 /.../flags
        if ch == "/" and _is_regex_start(content, i):
            regex_end = _find_regex_end_on_line(content, i)
            if regex_end is not None:
                _blank(string_masked, i, regex_end)
                _blank(code_only, i, regex_end)
                i = regex_end
                continue

        if ch == "\n":
            line_no += 1
        i += 1

    if in_template_text:
        _blank(string_masked, tpl_start, n)
        _blank(code_only, tpl_start, n)

    return _JsScanResult(
        comment_masked="".join(comment_masked),
        string_masked="".join(string_masked),
        code_only="".join(code_only),
        comments=comments,
    )


def _scan_html_only(content: str) -> _JsScanResult:
    """針對 .html 檔案：全域遮罩 <!-- -->，並額外遮罩 <script> 區塊內的 JS 註解。"""
    base = _scan_js_like(
        content,
        allow_jsx=True,
        allow_html_comments=True,
        enable_slash_comments=False,
    )
    script_re = re.compile(r"<script\b[^>]*>([\s\S]*?)</script>", re.IGNORECASE)
    cm_chars = list(base.comment_masked)
    sm_chars = list(base.string_masked)
    co_chars = list(base.code_only)
    for m in script_re.finditer(base.comment_masked):
        inner = m.group(1)
        sub = _scan_js_like(
            inner,
            allow_jsx=False,
            allow_html_comments=False,
            enable_slash_comments=True,
        )
        start = m.start(1)
        end = start + len(inner)
        cm_chars[start:end] = list(sub.comment_masked)
        sm_chars[start:end] = list(sub.string_masked)
        co_chars[start:end] = list(sub.code_only)
    return _JsScanResult(
        comment_masked="".join(cm_chars),
        string_masked="".join(sm_chars),
        code_only="".join(co_chars),
        comments=base.comments,
    )


# ---------------------------------------------------------------------------
# JSX / HTML 標籤結構解析
# ---------------------------------------------------------------------------


def _scan_open_tag_end(text: str, tag_name_end: int) -> tuple[int, bool] | None:
    """從標籤名稱結尾向後尋找開標籤結尾，回傳 (end_pos, is_self_closing)。"""
    n = len(text)
    i = tag_name_end
    quote: str | None = None
    brace_depth = 0
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            i += 1
            continue
        if ch == "{":
            brace_depth += 1
            i += 1
            continue
        if ch == "}":
            if brace_depth > 0:
                brace_depth -= 1
            i += 1
            continue
        if brace_depth == 0:
            if ch == "/" and i + 1 < n and text[i + 1] == ">":
                return i + 2, True
            if ch == ">":
                return i + 1, False
        i += 1
    return None


def _extract_jsx_elements(
    comment_masked: str,
    code_only: str,
    tag_names: tuple[str, ...],
    offsets: list[int],
    *,
    allow_self_closing: bool = False,
) -> list[_JsxElement]:
    """在 comment_masked 中抽出指定標籤（僅承認在 code_only 中亦存在 `<` 起點的真實標籤）。"""
    tag_alt = "|".join(re.escape(t) for t in tag_names)
    open_re = re.compile(rf"<({tag_alt})(?=[\s>/])")
    elements: list[_JsxElement] = []
    n = len(comment_masked)
    pos = 0

    while pos < n:
        m = open_re.search(code_only, pos)
        if not m:
            break
        start = m.start()
        tag_name = m.group(1)
        tag_end_info = _scan_open_tag_end(comment_masked, m.end())
        if tag_end_info is None:
            pos = m.end()
            continue
        open_end, is_self_closing = tag_end_info
        raw_end = open_end - (2 if is_self_closing else 1)
        attrs = comment_masked[m.end() : raw_end]

        if is_self_closing:
            if allow_self_closing:
                elements.append(
                    _JsxElement(
                        tag_name=tag_name,
                        attrs=attrs,
                        inner_raw="",
                        start_line=_offset_to_line(offsets, start),
                        end_line=_offset_to_line(offsets, open_end - 1),
                        is_self_closing=True,
                    )
                )
            pos = open_end
            continue

        if allow_self_closing:
            # 針對如 <input> 這類 HTML 單標籤（未寫 />），無需尋找配對閉標籤
            elements.append(
                _JsxElement(
                    tag_name=tag_name,
                    attrs=attrs,
                    inner_raw="",
                    start_line=_offset_to_line(offsets, start),
                    end_line=_offset_to_line(offsets, open_end - 1),
                    is_self_closing=False,
                )
            )
            pos = open_end
            continue

        # 尋找配對的 </tag_name>
        same_open_re = re.compile(rf"<{re.escape(tag_name)}(?=[\s>/])")
        same_close_re = re.compile(rf"</{re.escape(tag_name)}\s*>")
        depth = 1
        scan_pos = open_end
        close_start = -1
        close_end = -1
        while scan_pos < n and depth > 0:
            next_open = same_open_re.search(code_only, scan_pos)
            next_close = same_close_re.search(code_only, scan_pos)
            if next_close is None:
                break
            if next_open is not None and next_open.start() < next_close.start():
                sub_info = _scan_open_tag_end(comment_masked, next_open.end())
                if sub_info is None:
                    scan_pos = next_open.end()
                    continue
                sub_end, sub_self = sub_info
                if not sub_self:
                    depth += 1
                scan_pos = sub_end
            else:
                depth -= 1
                if depth == 0:
                    close_start = next_close.start()
                    close_end = next_close.end()
                    break
                scan_pos = next_close.end()

        if close_start == -1:
            pos = open_end
            continue

        elements.append(
            _JsxElement(
                tag_name=tag_name,
                attrs=attrs,
                inner_raw=comment_masked[open_end:close_start],
                start_line=_offset_to_line(offsets, start),
                end_line=_offset_to_line(offsets, close_end - 1),
                is_self_closing=False,
            )
        )
        pos = open_end

    return elements


def _skip_matching_svg(text: str, start: int) -> int:
    """從 `<svg` 標籤起點跳過整個 `<svg ...>...</svg>`（或自閉合 `<svg .../>`）。"""
    info = _scan_open_tag_end(text, start + 4)
    if info is None:
        return start + 4
    open_end, is_self = info
    if is_self:
        return open_end
    close_m = re.search(r"</svg\s*>", text[open_end:], re.IGNORECASE)
    if close_m:
        return open_end + close_m.end()
    return open_end


def _analyze_button_inner(inner_raw: str) -> tuple[bool, bool, str]:
    """解析按鈕內部，回傳 (是否含圖示元件或 svg, 是否含動態 JS 表達式, 純靜態文字)。"""
    has_icon = False
    has_js_expr = False
    static_chars: list[str] = []
    n = len(inner_raw)
    i = 0

    while i < n:
        ch = inner_raw[i]
        if ch == "{":
            # 跳過 JSX 表達式 { ... }
            expr_start = i + 1
            depth = 1
            j = i + 1
            quote: str | None = None
            while j < n and depth > 0:
                ech = inner_raw[j]
                if quote is not None:
                    if ech == "\\":
                        j += 2
                        continue
                    if ech == quote:
                        quote = None
                    j += 1
                    continue
                if ech in ("'", '"', "`"):
                    quote = ech
                elif ech == "{":
                    depth += 1
                elif ech == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            expr_body = inner_raw[expr_start:j].strip()
            if expr_body:
                if re.fullmatch(r"<(?:[A-Z][\w.]*[^>]*/>|svg[\s\S]*</svg>)", expr_body):
                    has_icon = True
                else:
                    has_js_expr = True
            i = j + 1 if j < n else n
            continue

        if ch == "<":
            if inner_raw.startswith("</", i):
                gt = inner_raw.find(">", i + 2)
                i = gt + 1 if gt != -1 else i + 2
                continue
            tag_m = re.match(r"<([A-Za-z_][\w.:-]*)(?=[\s>/])", inner_raw[i:])
            if tag_m:
                sub_tag = tag_m.group(1)
                if sub_tag.lower() == "svg":
                    has_icon = True
                    i = _skip_matching_svg(inner_raw, i)
                    continue
                if sub_tag[0].isupper():
                    has_icon = True
                info = _scan_open_tag_end(inner_raw, i + len(tag_m.group(0)))
                if info is not None:
                    i = info[0]
                    continue

        static_chars.append(ch)
        i += 1

    return has_icon, has_js_expr, "".join(static_chars)


# ---------------------------------------------------------------------------
# 六大規則實作
# ---------------------------------------------------------------------------


def _check_ui_no_emoji(
    rel_path: str,
    ext: str,
    is_test: bool,
    scan: _JsScanResult,
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    if ext not in UI_EMOJI_EXTS or is_test:
        return []
    violations: list[dict[str, Any]] = []
    for idx, line_text in enumerate(scan.comment_masked.splitlines(), start=1):
        if added_lines is not None and idx not in added_lines:
            continue
        if EMOJI_RE.search(line_text):
            violations.append(_make_violation("UI_NO_EMOJI", rel_path, idx, lines))
    return violations


def _check_ui_buttons(
    rel_path: str,
    ext: str,
    is_test: bool,
    scan: _JsScanResult,
    offsets: list[int],
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    if ext not in UI_JSX_EXTS or is_test:
        return []
    violations: list[dict[str, Any]] = []
    elements = _extract_jsx_elements(
        scan.comment_masked, scan.code_only, ("button", "Button"), offsets
    )
    for elem in elements:
        report_line = _pick_report_line(elem.start_line, elem.end_line, added_lines)
        if report_line is None:
            continue

        has_icon, has_js_expr, static_text = _analyze_button_inner(elem.inner_raw)
        stripped_text = static_text.strip()

        # 規則 2: 純圖示按鈕無可見文字與動態變數時，不可同時缺少 aria-label 與 title
        if has_icon and not has_js_expr and not stripped_text:
            if not A11Y_ATTR_RE.search(elem.attrs):
                violations.append(
                    _make_violation("UI_ICON_BTN_A11Y", rel_path, report_line, lines)
                )

        # 規則 3: 按鈕純靜態中文字元 > 6 且不含受保護風險關鍵詞
        cjk_count = len(CJK_CHAR_RE.findall(stripped_text))
        if cjk_count > 6 and not any(kw in stripped_text for kw in PROTECTED_RISK_KEYWORDS):
            violations.append(
                _make_violation("UI_COMPACT_BUTTON", rel_path, report_line, lines)
            )
    return violations


def _check_web_rules(
    rel_path: str,
    ext: str,
    is_test: bool,
    scan: _JsScanResult,
    offsets: list[int],
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    if ext not in WEB_EXTS or is_test:
        return []
    violations: list[dict[str, Any]] = []

    # WEB_DATE_INPUT_LANG
    inputs = _extract_jsx_elements(
        scan.comment_masked,
        scan.code_only,
        ("input",),
        offsets,
        allow_self_closing=True,
    )
    for inp in inputs:
        report_line = _pick_report_line(inp.start_line, inp.end_line, added_lines)
        if report_line is None:
            continue
        if DATE_TYPE_ATTR_RE.search(inp.attrs) and not LANG_EN_ATTR_RE.search(inp.attrs):
            violations.append(
                _make_violation("WEB_DATE_INPUT_LANG", rel_path, report_line, lines)
            )

    # WEB_NO_DANGEROUS_HTML
    for idx, line_text in enumerate(scan.comment_masked.splitlines(), start=1):
        if added_lines is not None and idx not in added_lines:
            continue
        if DANGEROUS_HTML_RE.search(line_text):
            violations.append(
                _make_violation("WEB_NO_DANGEROUS_HTML", rel_path, idx, lines)
            )

    return violations


def _check_ui_design_system(
    rel_path: str,
    ext: str,
    is_test: bool,
    scan: _JsScanResult,
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    if is_test:
        return []
    violations: list[dict[str, Any]] = []
    check_nt = ext in (JS_EXTS | UI_EMOJI_EXTS)
    check_jsx = ext in UI_JSX_EXTS
    if not (check_nt or check_jsx):
        return []
    for idx, line_text in enumerate(scan.comment_masked.splitlines(), start=1):
        if added_lines is not None and idx not in added_lines:
            continue
        if check_nt and NT_DOLLAR_RE.search(line_text):
            violations.append(_make_violation("UI_NO_NT_DOLLAR", rel_path, idx, lines))
        if check_jsx:
            if SIDE_STRIPE_RE.search(line_text) and not BLOCKQUOTE_TAG_RE.search(line_text):
                violations.append(_make_violation("UI_NO_SIDE_STRIPE", rel_path, idx, lines))
            if PLAIN_LOADING_JSX_RE.search(line_text) and not LOADING_COMPONENT_RE.search(line_text):
                violations.append(
                    _make_violation("UI_NO_PLAIN_TEXT_LOADING", rel_path, idx, lines)
                )
    return violations


def _tokenize_python_safe(content: str) -> list[tokenize.TokenInfo]:
    tokens: list[tokenize.TokenInfo] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(content).readline):
            tokens.append(tok)
    except (tokenize.TokenError, IndentationError):
        # 語法不完整或縮排錯誤的 Python 片段提前中止，保留已收集的 token
        pass
    return tokens


def _check_py_test_no_skip(
    rel_path: str,
    tokens: list[tokenize.TokenInfo],
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    ignored_types = {
        tokenize.COMMENT,
        tokenize.STRING,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
    for attr in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
        if hasattr(tokenize, attr):
            ignored_types.add(getattr(tokenize, attr))

    code_tokens = [t for t in tokens if t.type not in ignored_types]
    violations: list[dict[str, Any]] = []
    reported_lines: set[int] = set()
    total = len(code_tokens)

    def _match_seq(idx: int, expected: tuple[str, ...]) -> bool:
        if idx + len(expected) > total:
            return False
        return all(code_tokens[idx + k].string == exp for k, exp in enumerate(expected))

    for idx, tok in enumerate(code_tokens):
        matched = (
            _match_seq(idx, ("@", "pytest", ".", "mark", ".", "skip"))
            or _match_seq(idx, ("@", "unittest", ".", "skip"))
            or _match_seq(idx, ("pytest", ".", "skip", "("))
        )
        if not matched:
            continue
        line_no = tok.start[0]
        if added_lines is not None and line_no not in added_lines:
            continue
        if line_no not in reported_lines:
            reported_lines.add(line_no)
            violations.append(_make_violation("TEST_NO_SKIP", rel_path, line_no, lines))

    return violations


def _check_js_test_no_skip(
    rel_path: str,
    scan: _JsScanResult,
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for idx, line_text in enumerate(scan.code_only.splitlines(), start=1):
        if added_lines is not None and idx not in added_lines:
            continue
        if JS_SKIP_RE.search(line_text):
            violations.append(_make_violation("TEST_NO_SKIP", rel_path, idx, lines))
    return violations


def _is_pass_or_ellipsis(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Pass):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
        return stmt.value.value is ...
    return False


def _check_py_no_silent_catch(
    rel_path: str,
    content: str,
    tokens: list[tokenize.TokenInfo],
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    comment_lines: set[int] = set()
    for tok in tokens:
        if tok.type == tokenize.COMMENT and tok.string.lstrip("#").strip():
            comment_lines.add(tok.start[0])

    violations: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or not node.body:
            continue
        if not all(_is_pass_or_ellipsis(stmt) for stmt in node.body):
            continue
        end_line = getattr(node, "end_lineno", None) or node.body[-1].lineno
        has_comment = any(ln in comment_lines for ln in range(node.lineno, end_line + 1))
        if has_comment:
            continue
        report_line = _pick_report_line(node.lineno, end_line, added_lines)
        if report_line is None:
            continue
        violations.append(_make_violation("NO_SILENT_CATCH", rel_path, report_line, lines))
    return violations


def _check_js_no_silent_catch(
    rel_path: str,
    scan: _JsScanResult,
    offsets: list[int],
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for m in JS_EMPTY_CATCH_RE.finditer(scan.string_masked):
        # 確認 catch 關鍵字確實位於程式碼區，而非被遮罩掉的註解內
        if scan.code_only[m.start()] != "c":
            continue
        start_line = _offset_to_line(offsets, m.start())
        end_line = _offset_to_line(offsets, m.end() - 1)
        report_line = _pick_report_line(start_line, end_line, added_lines)
        if report_line is None:
            continue
        violations.append(_make_violation("NO_SILENT_CATCH", rel_path, report_line, lines))
    return violations


def _check_comment_text_list(
    rel_path: str,
    comments: list[tuple[int, str]],
    lines: list[str],
    added_lines: set[int] | None,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for line_no, text in comments:
        if added_lines is not None and line_no not in added_lines:
            continue
        if EXCUSE_COMMENT_RE.search(text):
            violations.append(_make_violation("NO_EXCUSE_COMMENT", rel_path, line_no, lines))
        elif SHORTCUT_PREFIX_RE.search(text):
            sc_m = SHORTCUT_VALID_RE.search(text)
            if not (sc_m and len(sc_m.group(1).strip()) >= 2):
                violations.append(
                    _make_violation(
                        "NO_EXCUSE_COMMENT",
                        rel_path,
                        line_no,
                        lines,
                        meta_key="NO_EXCUSE_COMMENT_SHORTCUT",
                    )
                )
    return violations


# ---------------------------------------------------------------------------
# 公開 API：lint_file_content & lint_git_diff
# ---------------------------------------------------------------------------


def lint_file_content(
    rel_path: str,
    content: str,
    added_lines: set[int] | None = None,
) -> list[dict[str, Any]]:
    """對單一檔案內容執行所有適用的確定性規則檢查。

    Args:
        rel_path: 檔案相對路徑（用以判斷副檔名與是否為測試檔，並填入違規結果的 file 欄位）。
        content: 檔案全文內容。
        added_lines: 若提供 1-based 行號集合，僅回報命中該集合的新增/修改行；若為 None 則全檔檢查。
    """
    if added_lines is not None and len(added_lines) == 0:
        return []

    ext = _normalize_rel_path(rel_path).suffix.lower()
    if ext not in RELEVANT_EXTS:
        return []

    is_test = _is_test_file(rel_path)
    lines = content.splitlines()
    violations: list[dict[str, Any]] = []

    if ext in PY_EXTS:
        tokens = _tokenize_python_safe(content)
        if is_test:
            violations.extend(_check_py_test_no_skip(rel_path, tokens, lines, added_lines))
        violations.extend(
            _check_py_no_silent_catch(rel_path, content, tokens, lines, added_lines)
        )
        py_comments = [
            (tok.start[0], tok.string) for tok in tokens if tok.type == tokenize.COMMENT
        ]
        violations.extend(_check_comment_text_list(rel_path, py_comments, lines, added_lines))
        violations.sort(key=lambda v: (v["line"], v["rule_id"]))
        return violations

    offsets = _line_offsets(content)
    if ext == ".html":
        scan = _scan_html_only(content)
    else:
        scan = _scan_js_like(
            content,
            allow_jsx=ext in UI_EMOJI_EXTS,
            allow_html_comments=ext in {".vue", ".svelte"},
            enable_slash_comments=True,
        )

    violations.extend(_check_ui_no_emoji(rel_path, ext, is_test, scan, lines, added_lines))
    violations.extend(_check_ui_buttons(rel_path, ext, is_test, scan, offsets, lines, added_lines))
    violations.extend(_check_web_rules(rel_path, ext, is_test, scan, offsets, lines, added_lines))
    violations.extend(_check_ui_design_system(rel_path, ext, is_test, scan, lines, added_lines))

    if ext in JS_EXTS:
        if is_test:
            violations.extend(_check_js_test_no_skip(rel_path, scan, lines, added_lines))
        violations.extend(_check_js_no_silent_catch(rel_path, scan, offsets, lines, added_lines))
        violations.extend(_check_comment_text_list(rel_path, scan.comments, lines, added_lines))

    violations.sort(key=lambda v: (v["line"], v["rule_id"]))
    return violations


HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _clean_diff_path(raw_path: str, strip_prefix: str) -> str:
    path = raw_path.strip()
    if path.startswith('"') and path.endswith('"') and len(path) >= 2:
        path = path[1:-1]
        # 還原基本跳脫字元
        path = path.replace('\\"', '"').replace("\\\\", "\\")
    # 處理 git diff 可能在檔名後方附帶 tab timestamp
    if "\t" in path:
        path = path.split("\t", 1)[0].strip()
    if path.startswith(strip_prefix):
        path = path[len(strip_prefix) :]
    return path


def _parse_unified_diff(diff_text: str) -> dict[str, set[int]]:
    """解析 unified diff，回傳 {rel_path: 新增/修改的 1-based 行號集合}，忽略 /dev/null 刪除檔。"""
    file_added_lines: dict[str, set[int]] = {}
    current_file: str | None = None
    in_hunk = False
    old_rem = 0
    new_rem = 0
    cur_new_line = 0

    for line in diff_text.splitlines():
        if in_hunk:
            if old_rem <= 0 and new_rem <= 0:
                in_hunk = False
            elif line.startswith("\\"):
                # "\ No newline at end of file" 不計入行數
                continue
            elif line.startswith("+"):
                if current_file is not None:
                    file_added_lines.setdefault(current_file, set()).add(cur_new_line)
                cur_new_line += 1
                new_rem -= 1
                continue
            elif line.startswith("-"):
                old_rem -= 1
                continue
            elif line.startswith(" "):
                cur_new_line += 1
                old_rem -= 1
                new_rem -= 1
                continue
            else:
                # 異常提早結束 hunk 的非內容行（如新 diff 標頭）
                in_hunk = False

        if line.startswith("diff --git "):
            current_file = None
            in_hunk = False
            continue

        if line.startswith("--- "):
            continue

        if line.startswith("+++ "):
            target = line[4:].strip()
            if target == "/dev/null":
                current_file = None
            else:
                current_file = _clean_diff_path(target, "b/")
                file_added_lines.setdefault(current_file, set())
            in_hunk = False
            continue

        hunk_m = HUNK_HEADER_RE.match(line)
        if hunk_m:
            old_count = int(hunk_m.group(2)) if hunk_m.group(2) is not None else 1
            new_start = int(hunk_m.group(3))
            new_count = int(hunk_m.group(4)) if hunk_m.group(4) is not None else 1
            old_rem = old_count
            new_rem = new_count
            cur_new_line = new_start
            in_hunk = (old_rem > 0) or (new_rem > 0)
            continue

    return file_added_lines


def _build_report(files_checked: int, violations: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_violations = sorted(
        violations, key=lambda v: (v["file"], v["line"], v["rule_id"])
    )
    error_count = sum(1 for v in sorted_violations if v["severity"] == "error")
    warning_count = sum(1 for v in sorted_violations if v["severity"] == "warning")
    return {
        "passed": error_count == 0,
        "files_checked": files_checked,
        "error_count": error_count,
        "warning_count": warning_count,
        "violations": sorted_violations,
    }


def lint_git_diff(
    diff_text: str, repo_root: Path | None = None, *, from_index: bool = False
) -> dict[str, Any]:
    """解析 unified diff，僅檢查新增/修改行（+ 行號），並回傳標準 JSON 報告結構。"""
    root = repo_root if repo_root is not None else Path.cwd()
    file_added_lines = _parse_unified_diff(diff_text)
    files_checked = 0
    all_violations: list[dict[str, Any]] = []

    for rel_path, added_lines in file_added_lines.items():
        if not added_lines or _is_ignored_mirror_path(rel_path):
            continue
        if from_index:
            git_rel = rel_path.replace("\\", "/")
            idx_res = _run_git(root, ["show", f":{git_rel}"])
            if idx_res.returncode != 0:
                continue
            content = idx_res.stdout
        else:
            target_path = root / _normalize_rel_path(rel_path)
            if not target_path.is_file():
                continue
            content = target_path.read_text(encoding="utf-8", errors="replace")
        files_checked += 1
        all_violations.extend(
            lint_file_content(rel_path, content, added_lines=added_lines)
        )

    return _build_report(files_checked, all_violations)


# ---------------------------------------------------------------------------
# CLI 入口與輸出格式化
# ---------------------------------------------------------------------------


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), "-c", "core.quotepath=false", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _collect_git_diff(
    repo_root: Path,
    commit: str | None,
    paths: list[str] | None,
    staged: bool = False,
) -> str:
    pathspecs = [str(p).strip() for p in (paths or []) if str(p).strip()]
    if commit:
        res = _run_git(repo_root, ["show", "--format=", commit, "--", *pathspecs])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or f"git show failed for {commit}")
        return res.stdout

    if staged:
        res = _run_git(repo_root, ["diff", "--cached", "--", *pathspecs])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or "git diff --cached failed")
        return res.stdout

    has_head = _run_git(repo_root, ["rev-parse", "--verify", "HEAD"]).returncode == 0
    if has_head:
        res = _run_git(repo_root, ["diff", "HEAD", "--", *pathspecs])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or "git diff HEAD failed")
        return res.stdout

    # 尚無任何 commit 的新倉庫，合併暫存區與工作區差異
    staged_res = _run_git(repo_root, ["diff", "--cached", "--", *pathspecs])
    unstaged_res = _run_git(repo_root, ["diff", "--", *pathspecs])
    if staged_res.returncode != 0 or unstaged_res.returncode != 0:
        err = staged_res.stderr.strip() or unstaged_res.stderr.strip() or "git diff failed"
        raise RuntimeError(err)
    return "\n".join(part for part in (staged_res.stdout, unstaged_res.stdout) if part)


def _collect_untracked_files(
    repo_root: Path,
    paths: list[str] | None,
    already_checked: set[str],
) -> list[str]:
    """列出尚未追蹤且屬於目標檢查副檔名的新增檔案（排除常見快取與依賴目錄）。"""
    pathspecs = [str(p).strip() for p in (paths or []) if str(p).strip()]
    res = _run_git(
        repo_root,
        ["ls-files", "-z", "--others", "--exclude-standard", "--", *pathspecs],
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "git ls-files failed")

    untracked: list[str] = []
    for raw in res.stdout.split("\0"):
        if not raw:
            continue
        rel_norm = raw.replace("\\", "/")
        if rel_norm in already_checked or _is_ignored_mirror_path(rel_norm):
            continue
        rel_path_obj = _normalize_rel_path(rel_norm)
        if any(part in IGNORED_UNTRACKED_DIRS for part in rel_path_obj.parts):
            continue
        if rel_path_obj.suffix.lower() not in RELEVANT_EXTS:
            continue
        if (repo_root / rel_path_obj).is_file():
            untracked.append(rel_norm)
    return untracked


def _format_text(report: dict[str, Any]) -> str:
    violations = report["violations"]
    if not violations:
        return (
            f"PASS: 0 errors, {report['warning_count']} warnings "
            f"({report['files_checked']} files checked)."
        )
    blocks: list[str] = []
    for v in violations:
        sev = str(v["severity"]).upper()
        blocks.append(
            f"[{sev}][{v['rule_id']}] {v['file']}:{v['line']} — {v['why']}\n"
            f"  ↳ Snippet: {v['snippet']}\n"
            f"  ↳ 修復指引: {v['fix_hint']}"
        )
    return "\n".join(blocks)


def _configure_stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                # 受限主控台或測試模擬串流不支援重新配置編碼，保留原有串流設定
                pass


def main(argv: list[str] | None = None) -> int:
    _configure_stdio_utf8()
    parser = argparse.ArgumentParser(
        description="全域確定性規則檢查腳本 (Rule Lint Gate)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--git-diff", action="store_true", help="檢查 Git Diff 新增/修改行")
    mode.add_argument("--files", nargs="+", help="檢查指定檔案清單")
    mode.add_argument("--stdin", action="store_true", help="從標準輸入讀取檔案內容檢查")

    parser.add_argument("--repo", default=".", help="--git-diff 模式使用的倉庫根目錄")
    parser.add_argument("--commit", default=None, help="--git-diff 模式指定檢查的 Commit Ref")
    parser.add_argument(
        "--staged",
        action="store_true",
        help="搭配 --git-diff 僅檢查暫存區 (staged) 修改，不納入未追蹤檔案",
    )
    parser.add_argument("--paths", nargs="*", default=None, help="--git-diff 模式路徑過濾")
    parser.add_argument(
        "--filename",
        default=None,
        help="--stdin 模式必填之虛擬相對路徑（例如 src/App.tsx）",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="輸出格式（text 或 json）",
    )

    args = parser.parse_args(argv)
    if args.staged and not args.git_diff:
        parser.error("--staged 必須搭配 --git-diff 使用")

    try:
        if args.git_diff:
            repo_root = Path(args.repo).resolve()
            diff_text = _collect_git_diff(repo_root, args.commit, args.paths, staged=args.staged)
            report = lint_git_diff(diff_text, repo_root=repo_root, from_index=bool(args.staged))
            if not args.commit and not args.staged:
                checked_set = {
                    p.replace("\\", "/")
                    for p, lines_set in _parse_unified_diff(diff_text).items()
                    if lines_set and (repo_root / _normalize_rel_path(p)).is_file()
                }
                extra_files = _collect_untracked_files(repo_root, args.paths, checked_set)
                if extra_files:
                    all_violations = list(report["violations"])
                    extra_checked = 0
                    for rel_path in extra_files:
                        target_path = repo_root / _normalize_rel_path(rel_path)
                        if not target_path.is_file():
                            continue
                        extra_checked += 1
                        content = target_path.read_text(encoding="utf-8", errors="replace")
                        all_violations.extend(
                            lint_file_content(rel_path, content, added_lines=None)
                        )
                    report = _build_report(
                        report["files_checked"] + extra_checked, all_violations
                    )
        elif args.files:
            all_violations: list[dict[str, Any]] = []
            files_checked = 0
            for raw_file in args.files:
                file_path = Path(raw_file)
                if not file_path.is_file():
                    raise FileNotFoundError(f"找不到檔案: {raw_file}")
                files_checked += 1
                content = file_path.read_text(encoding="utf-8", errors="replace")
                all_violations.extend(lint_file_content(raw_file, content, added_lines=None))
            report = _build_report(files_checked, all_violations)
        else:
            if not args.filename:
                parser.error("--stdin 模式必須同時提供 --filename <virtual_rel_path>")
            content = sys.stdin.read()
            violations = lint_file_content(args.filename, content, added_lines=None)
            report = _build_report(1, violations)
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"[ERROR] rule_lint 執行失敗: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_format_text(report))

    return 1 if report["error_count"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
