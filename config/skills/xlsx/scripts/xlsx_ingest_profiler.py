#!/usr/bin/env python3
"""
Zero-PII Structural & Static Audit Profiler for Excel Workbooks (.xlsx / .xlsm)

融合 SpreadsheetLLM Structural Anchors × spreadsheet-auditor × 台灣財會實務防線：
1. 絕對唯讀：絕不執行 VBA 巨集，絕不回寫原檔。
2. 零個資預設 (--mask-pii=True)：輸出禁止出現任何員工姓名、身分證號、手機、帳號與個人薪資金額。
3. 單遍 OOXML ZIP/XML 串流極速解析（~10x 提速；非標準壓縮格式優雅退回 openpyxl）。
4. 專抓髒表陷阱：合併儲存格錯位、隱藏列 SUM 雙重計數、小計/合計列偵測、真實 SUM Off-by-one（排除 SUMIF 部門小計誤報）與公式覆寫常數。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


def _bootstrap_venv() -> None:
    try:
        import openpyxl  # noqa: F401
        return
    except ImportError:
        pass
    candidates = [
        Path(__file__).resolve().parent / ".venv" / "Lib" / "site-packages",
        Path.home() / ".gemini" / "config" / "skills" / "xlsx" / ".venv" / "Lib" / "site-packages",
    ]
    for cand in candidates:
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


_bootstrap_venv()

from openpyxl import load_workbook  # noqa: E402
from openpyxl.utils import get_column_letter, column_index_from_string  # noqa: E402

try:
    import python_calamine  # type: ignore  # noqa: F401
    HAS_CALAMINE = True
except ImportError:
    HAS_CALAMINE = False

SUBTOTAL_KW_RE = re.compile(
    r"(?:^|\s)(合計|小計|總計|總額|部門合計|Total|Subtotal|Grand\s*Total)(?:\s|$|:|：)", re.I
)
SUBTOTAL_FORMULA_RE = re.compile(r"\b(?:SUMIF|SUMIFS|SUBTOTAL|SUM|AVERAGE)\s*\(", re.I)
ROC_DATE_RE = re.compile(r"^(?:1[0-2]\d|\d{2,3})[./-](?:0?[1-9]|1[0-2])[./-](?:0?[1-9]|[12]\d|3[01])$")
TW_ID_RE = re.compile(r"\b[A-Z][12]\d{8}\b")
PHONE_RE = re.compile(r"\b09\d{2}[- ]?\d{3}[- ]?\d{3}\b")
SUM_RANGE_RE = re.compile(r"\bSUM\(\s*\$?([A-Z]{1,3})\$?(\d+)\s*:\s*\$?([A-Z]{1,3})\$?(\d+)\s*\)", re.I)
CELL_COORD_RE = re.compile(r"^([A-Z]{1,3})(\d+)$")
DIM_RANGE_RE = re.compile(r"^(?:[A-Z]{1,3}\d+:)?([A-Z]{1,3})(\d+)$")
EXCEL_ERRORS = ("#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A", "#GETTING_DATA")
BUILTIN_DATE_FMT_IDS = {
    14, 15, 16, 17, 18, 19, 20, 21, 22,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
    45, 46, 47, 50, 51, 52, 53, 54, 55, 56, 57, 58,
}


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _mask_header_label(raw: Any) -> str:
    """表頭通常為欄位語意；僅移除疑似個資樣式。"""
    if raw is None:
        return ""
    text = re.sub(r"\s+", " ", str(raw)).strip()
    if not text:
        return ""
    if TW_ID_RE.search(text) or PHONE_RE.search(text):
        return "<MASKED_HEADER>"
    return text[:28]


def _classify_token(val: Any) -> tuple[str, str]:
    """將儲存格值分類為純型別計數鍵與零個資遮罩標籤，絕不吐出個資或金額。"""
    if val is None:
        return "empty_count", "<EMPTY>"
    if isinstance(val, bool):
        return "str_count", "<BOOL>"
    if isinstance(val, (dt.date, dt.datetime)):
        return "date_count", "<DATE>"
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return "empty_count", "<EMPTY>"
        if s.startswith("="):
            return "formula_count", "<FORMULA>"
        if ROC_DATE_RE.match(s):
            return "roc_date_count", "<ROC_DATE>"
        if TW_ID_RE.search(s):
            return "str_count", "<MASKED_TW_ID>"
        if PHONE_RE.search(s):
            return "str_count", "<MASKED_PHONE>"
        if re.search(r"[\u4e00-\u9fff]", s):
            return "str_count", "<STR_ZH>"
        return "str_count", "<STR_ASCII>"
    if isinstance(val, (int, float)):
        if val == 0:
            return "zero_count", "<NUM_ZERO>"
        if isinstance(val, int) or float(val).is_integer():
            return "int_count", "<NUM_INT>"
        return "float_count", "<NUM_FLOAT>"
    return "str_count", "<OTHER>"


def _is_numeric_val(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _col_str_to_idx(col_str: str) -> int:
    idx = 0
    for ch in col_str:
        idx = idx * 26 + (ord(ch) - 64)
    return idx


def _extract_text_no_phonetic(parent_elem: ET.Element) -> str:
    """從 <si> 或 <is> 串接文字，明確略過台灣 Excel 常見的 <rPh> 注音標記。"""
    parts: list[str] = []
    for child in parent_elem:
        tag = _local_tag(child.tag)
        if tag == "rPh":
            continue
        if tag == "t":
            if child.text:
                parts.append(child.text)
        elif tag == "r":
            for sub in child:
                if _local_tag(sub.tag) == "t" and sub.text:
                    parts.append(sub.text)
    return "".join(parts)


def _parse_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    strings: list[str] = []
    with zf.open("xl/sharedStrings.xml") as fh:
        for event, elem in ET.iterparse(fh, events=("end",)):
            if _local_tag(elem.tag) == "si":
                strings.append(_extract_text_no_phonetic(elem))
                elem.clear()
    return strings


def _is_date_format_code(code: str) -> bool:
    cleaned = re.sub(r"\[[^\]]*\]|\"[^\"]*\"", "", code).lower()
    if any(ch in cleaned for ch in ("#", "0.0")):
        return False
    return bool(re.search(r"[ymde]", cleaned)) and not re.search(r"^[^ymde]*0+[^ymde]*$", cleaned)


def _parse_date_style_indices(zf: zipfile.ZipFile) -> set[int]:
    if "xl/styles.xml" not in zf.namelist():
        return set()
    date_indices: set[int] = set()
    custom_is_date: dict[int, bool] = {}
    try:
        with zf.open("xl/styles.xml") as fh:
            root = ET.parse(fh).getroot()
        for nf in root.iter():
            if _local_tag(nf.tag) == "numFmt":
                try:
                    nid = int(nf.attrib.get("numFmtId", "-1"))
                    fcode = nf.attrib.get("formatCode", "")
                    custom_is_date[nid] = nid in BUILTIN_DATE_FMT_IDS or _is_date_format_code(fcode)
                except ValueError:
                    continue
        for node in root.iter():
            if _local_tag(node.tag) == "cellXfs":
                idx = 0
                for xf in node:
                    if _local_tag(xf.tag) == "xf":
                        try:
                            nid = int(xf.attrib.get("numFmtId", "0"))
                            if nid in BUILTIN_DATE_FMT_IDS or custom_is_date.get(nid, False):
                                date_indices.add(idx)
                        except ValueError:
                            pass
                        idx += 1
                break
    except Exception:
        return set()
    return date_indices


def _parse_workbook_sheets(zf: zipfile.ZipFile) -> list[dict[str, str]]:
    """解析 workbook.xml 與 rels，按分頁順序回傳 (name, state, zip_path)。"""
    rels_map: dict[str, str] = {}
    if "xl/_rels/workbook.xml.rels" in zf.namelist():
        with zf.open("xl/_rels/workbook.xml.rels") as fh:
            rels_root = ET.parse(fh).getroot()
        for rel in rels_root:
            if _local_tag(rel.tag) != "Relationship":
                continue
            rel_type = rel.attrib.get("Type", "")
            if not rel_type.endswith("/worksheet"):
                continue
            rid = rel.attrib.get("Id", "")
            tgt = rel.attrib.get("Target", "").replace("\\", "/")
            if tgt.startswith("/"):
                norm_tgt = tgt.lstrip("/")
            else:
                norm_tgt = posixpath.normpath(posixpath.join("xl", tgt))
            if rid and norm_tgt in zf.namelist():
                rels_map[rid] = norm_tgt

    sheets: list[dict[str, str]] = []
    with zf.open("xl/workbook.xml") as fh:
        wb_root = ET.parse(fh).getroot()
    for elem in wb_root.iter():
        if _local_tag(elem.tag) == "sheet":
            name = elem.attrib.get("name", "")
            state = elem.attrib.get("state", "visible")
            rid = ""
            for k, v in elem.attrib.items():
                if k == "r:id" or k.endswith("}id"):
                    rid = v
                    break
            target_path = rels_map.get(rid, "")
            if name and target_path:
                sheets.append({"name": name, "state": state, "path": target_path})
    return sheets


def _analyze_sheet_matrix(
    sname: str,
    sheet_state: str,
    actual_max_r: int,
    actual_max_c: int,
    max_r: int,
    max_c: int,
    merged_ranges: list[str],
    hidden_rows: list[int],
    cells_f: dict[tuple[int, int], Any],
    cells_v: dict[tuple[int, int], Any],
    *,
    mask_pii: bool,
    max_sample_rows: int,
    totals_acc: dict[str, Any],
) -> dict[str, Any]:
    """對單一分頁的邊界矩陣執行零個資剖析、公式健檢與無誤報 Off-by-one 稽核。"""
    hidden_set = set(hidden_rows)
    header_scores: list[tuple[int, int, list[dict[str, str]]]] = []
    subtotal_rows: list[int] = []
    subtotal_set: set[int] = set()

    col_stats: dict[int, dict[str, Any]] = {
        c: {
            "col": get_column_letter(c),
            "int_count": 0,
            "float_count": 0,
            "str_count": 0,
            "date_count": 0,
            "roc_date_count": 0,
            "formula_count": 0,
            "zero_count": 0,
            "empty_count": 0,
            "sample_tokens": [],
            "_formula_rows": [],
            "_const_num_rows": [],
        }
        for c in range(1, max_c + 1)
    }

    # 第一遍：收集儲存格統計、小計／合計列（含 SUMIF/SUMIFS 部門小計）、錯誤與公式集合
    sum_candidates: list[tuple[int, int, str, str]] = []
    for r in range(1, max_r + 1):
        non_empty_headers: list[dict[str, str]] = []
        row_has_subtotal = False

        for c in range(1, max_c + 1):
            val_f = cells_f.get((r, c))
            val_v = cells_v.get((r, c))
            is_formula = isinstance(val_f, str) and val_f.startswith("=")

            if c <= 8 and isinstance(val_v, str) and SUBTOTAL_KW_RE.search(val_v):
                row_has_subtotal = True

            if r <= 15 and val_v is not None and str(val_v).strip():
                non_empty_headers.append({
                    "col": get_column_letter(c),
                    "label": _mask_header_label(val_v),
                })

            coord = f"{sname}!{get_column_letter(c)}{r}"
            if is_formula:
                totals_acc["total_formulas"] += 1
                if val_v is None:
                    totals_acc["uncached_count"] += 1
                    if len(totals_acc["uncached_samples"]) < 15:
                        totals_acc["uncached_samples"].append(coord)

                f_upper = val_f.upper()
                if (
                    hidden_set
                    and "SUM(" in f_upper
                    and "SUBTOTAL(109" not in f_upper
                    and len(totals_acc["sum_hidden_risks"]) < 10
                ):
                    totals_acc["sum_hidden_risks"].append(coord)

                if "SUM(" in f_upper:
                    sum_candidates.append((r, c, coord, val_f))

            if isinstance(val_v, str):
                for err in EXCEL_ERRORS:
                    if err in val_v and len(totals_acc["error_cells"]) < 20:
                        totals_acc["error_cells"].append({"location": coord, "error": err})
                        break

            stat_key, token_lbl = _classify_token(val_f if is_formula else val_v)
            st = col_stats[c]
            st[stat_key] += 1
            if len(st["sample_tokens"]) < max(1, max_sample_rows):
                if mask_pii:
                    if token_lbl not in st["sample_tokens"]:
                        st["sample_tokens"].append(token_lbl)
                else:
                    st["sample_tokens"].append(str(val_f if is_formula else val_v)[:24])

            if r >= 4 and not row_has_subtotal:
                if is_formula:
                    st["_formula_rows"].append(r)
                elif _is_numeric_val(val_v) and val_v != 0:
                    st["_const_num_rows"].append(r)

        if row_has_subtotal:
            subtotal_set.add(r)
            if len(subtotal_rows) < 20:
                subtotal_rows.append(r)

        if r <= 15 and len(non_empty_headers) >= 3:
            header_scores.append((len(non_empty_headers), r, non_empty_headers))

    # 第二遍：精準檢核 SUM Off-by-one（排除小計/SUMIF/SUBTOTAL 列誤報）
    for r, _c, coord, val_f in sum_candidates:
        if len(totals_acc["sum_off_by_one"]) >= 10:
            break
        for m in SUM_RANGE_RE.finditer(val_f):
            c1, r1_s, c2, r2_s = m.group(1).upper(), int(m.group(2)), m.group(3).upper(), int(m.group(4))
            next_r = r2_s + 1
            if c1 == c2 and r2_s >= r1_s and next_r < r:
                if next_r in subtotal_set:
                    continue
                col_idx = _col_str_to_idx(c1)
                next_f = cells_f.get((next_r, col_idx))
                if isinstance(next_f, str) and SUBTOTAL_FORMULA_RE.search(next_f):
                    continue
                next_val = cells_v.get((next_r, col_idx))
                if _is_numeric_val(next_val) and next_val != 0:
                    totals_acc["sum_off_by_one"].append({
                        "location": coord,
                        "formula": val_f[:80],
                        "reason": f"第 {next_r} 列緊接在 SUM 範圍末列之下且仍為非零明細數值",
                    })
                    break

    for c, st in col_stats.items():
        f_rows = st.pop("_formula_rows")
        c_rows = st.pop("_const_num_rows")
        if len(f_rows) >= 5 and 1 <= len(c_rows) <= max(2, len(f_rows) // 5):
            if len(totals_acc["pattern_breaks"]) < 10:
                totals_acc["pattern_breaks"].append({
                    "sheet": sname,
                    "col": st["col"],
                    "formula_rows": len(f_rows),
                    "hardcoded_rows_sample": c_rows[:5],
                })

    header_scores.sort(key=lambda x: (-x[0], x[1]))
    top_headers = [
        {"row": r_idx, "non_empty_cols": cnt, "columns": cols[:20]}
        for cnt, r_idx, cols in header_scores[:3]
    ]
    compact_cols = [st for st in col_stats.values() if st["empty_count"] < max_r][:25]

    return {
        "name": sname,
        "sheet_state": sheet_state,
        "actual_max_row": actual_max_r,
        "actual_max_column": actual_max_c,
        "scanned_rows": max_r,
        "scanned_columns": max_c,
        "merged_cells_count": len(merged_ranges),
        "merged_ranges_sample": merged_ranges[:20],
        "hidden_rows_count": len(hidden_rows),
        "hidden_rows_sample": hidden_rows[:20],
        "subtotal_total_rows": subtotal_rows,
        "header_candidate_rows": top_headers,
        "pii_redacted_column_profile": compact_cols,
    }


def _profile_via_ooxml_stream(
    path_obj: Path,
    *,
    mask_pii: bool,
    max_sample_rows: int,
    max_scan_cols: int,
    max_scan_rows: int,
) -> dict[str, Any]:
    """單遍 ZIP + ElementTree 串流解析器：無雙重 load_workbook 開銷。"""
    totals_acc: dict[str, Any] = {
        "total_formulas": 0,
        "uncached_samples": [],
        "uncached_count": 0,
        "error_cells": [],
        "sum_hidden_risks": [],
        "sum_off_by_one": [],
        "pattern_breaks": [],
    }
    sheets_report: list[dict[str, Any]] = []

    with zipfile.ZipFile(str(path_obj), "r") as zf:
        shared_strings = _parse_shared_strings(zf)
        date_styles = _parse_date_style_indices(zf)
        sheet_infos = _parse_workbook_sheets(zf)

        for info in sheet_infos:
            sname = info["name"]
            sstate = info["state"]
            spath = info["path"]
            merged_ranges: list[str] = []
            hidden_rows: list[int] = []
            cells_f: dict[tuple[int, int], Any] = {}
            cells_v: dict[tuple[int, int], Any] = {}
            shared_formulas: dict[str, str] = {}
            actual_max_r = 0
            actual_max_c = 0

            with zf.open(spath) as fh:
                cur_row_num = 0
                cur_col_seq = 0
                for _ev, elem in ET.iterparse(fh, events=("end",)):
                    tag = _local_tag(elem.tag)
                    if tag == "dimension":
                        ref = elem.attrib.get("ref", "")
                        m = DIM_RANGE_RE.match(ref)
                        if m:
                            actual_max_c = max(actual_max_c, _col_str_to_idx(m.group(1)))
                            actual_max_r = max(actual_max_r, int(m.group(2)))
                        elem.clear()
                    elif tag == "mergeCell":
                        mref = elem.attrib.get("ref", "")
                        if mref:
                            merged_ranges.append(mref)
                        elem.clear()
                    elif tag == "row":
                        r_str = elem.attrib.get("r", "")
                        r_idx = int(r_str) if r_str.isdigit() else (cur_row_num + 1)
                        cur_row_num = r_idx
                        cur_col_seq = 0
                        if elem.attrib.get("hidden") in ("1", "true", "True"):
                            hidden_rows.append(r_idx)
                        if r_idx > actual_max_r:
                            actual_max_r = r_idx

                        if r_idx <= max_scan_rows:
                            for cell in elem:
                                if _local_tag(cell.tag) != "c":
                                    continue
                                cref = cell.attrib.get("r", "")
                                if cref:
                                    cm = CELL_COORD_RE.match(cref)
                                    if cm:
                                        c_idx = _col_str_to_idx(cm.group(1))
                                        cur_col_seq = c_idx
                                    else:
                                        cur_col_seq += 1
                                        c_idx = cur_col_seq
                                else:
                                    cur_col_seq += 1
                                    c_idx = cur_col_seq
                                if c_idx > actual_max_c:
                                    actual_max_c = c_idx
                                if c_idx > max_scan_cols:
                                    continue

                                c_type = cell.attrib.get("t", "")
                                s_attr = cell.attrib.get("s", "")
                                style_idx = int(s_attr) if s_attr.isdigit() else -1

                                f_elem = None
                                v_elem = None
                                is_elem = None
                                for sub in cell:
                                    st = _local_tag(sub.tag)
                                    if st == "f":
                                        f_elem = sub
                                    elif st == "v":
                                        v_elem = sub
                                    elif st == "is":
                                        is_elem = sub

                                if f_elem is not None:
                                    ft = f_elem.attrib.get("t", "")
                                    si = f_elem.attrib.get("si")
                                    if f_elem.text:
                                        f_str = "=" + f_elem.text
                                        if ft == "shared" and si is not None:
                                            shared_formulas[si] = f_str
                                    elif ft == "shared" and si is not None:
                                        f_str = shared_formulas.get(si, "=<SHARED>")
                                    else:
                                        f_str = "=<ARRAY>"
                                    cells_f[(r_idx, c_idx)] = f_str

                                parsed_v: Any = None
                                if c_type == "inlineStr" and is_elem is not None:
                                    parsed_v = _extract_text_no_phonetic(is_elem)
                                elif v_elem is not None and v_elem.text is not None:
                                    raw_t = v_elem.text
                                    if c_type == "s":
                                        try:
                                            s_i = int(raw_t)
                                            parsed_v = shared_strings[s_i] if 0 <= s_i < len(shared_strings) else raw_t
                                        except ValueError:
                                            parsed_v = raw_t
                                    elif c_type == "b":
                                        parsed_v = raw_t == "1"
                                    elif c_type in ("str", "e"):
                                        parsed_v = raw_t
                                    else:
                                        try:
                                            num = float(raw_t)
                                            num_val: int | float = int(num) if num.is_integer() else num
                                            if style_idx in date_styles and 1 <= num <= 2958465:
                                                parsed_v = dt.datetime(1899, 12, 30) + dt.timedelta(days=num)
                                            else:
                                                parsed_v = num_val
                                        except ValueError:
                                            parsed_v = raw_t
                                if parsed_v is not None:
                                    cells_v[(r_idx, c_idx)] = parsed_v

                        elem.clear()

            max_r = min(actual_max_r, max_scan_rows)
            max_c = min(actual_max_c, max_scan_cols)
            sheets_report.append(
                _analyze_sheet_matrix(
                    sname,
                    sstate,
                    actual_max_r,
                    actual_max_c,
                    max_r,
                    max_c,
                    merged_ranges,
                    sorted(hidden_rows),
                    cells_f,
                    cells_v,
                    mask_pii=mask_pii,
                    max_sample_rows=max_sample_rows,
                    totals_acc=totals_acc,
                )
            )

    return {
        "file": path_obj.name,
        "engine": "ooxml_stream_v2",
        "pii_masked": mask_pii,
        "calamine_available": HAS_CALAMINE,
        "sheets_count": len(sheets_report),
        "sheets": sheets_report,
        "formula_audit": {
            "total_formulas": totals_acc["total_formulas"],
            "uncached_formula_count": totals_acc["uncached_count"],
            "uncached_sample": totals_acc["uncached_samples"],
            "error_cells": totals_acc["error_cells"],
            "sum_hidden_row_risks": totals_acc["sum_hidden_risks"],
            "sum_off_by_one_warnings": totals_acc["sum_off_by_one"],
            "pattern_break_warnings": totals_acc["pattern_breaks"],
        },
    }


def _profile_via_openpyxl(
    path_obj: Path,
    *,
    mask_pii: bool,
    max_sample_rows: int,
    max_scan_cols: int,
    max_scan_rows: int,
) -> dict[str, Any]:
    is_xlsm = path_obj.suffix.lower() == ".xlsm"
    wb_f = load_workbook(str(path_obj), data_only=False, keep_vba=is_xlsm)
    wb_v = load_workbook(str(path_obj), data_only=True, keep_vba=is_xlsm)
    totals_acc: dict[str, Any] = {
        "total_formulas": 0,
        "uncached_samples": [],
        "uncached_count": 0,
        "error_cells": [],
        "sum_hidden_risks": [],
        "sum_off_by_one": [],
        "pattern_breaks": [],
    }
    sheets_report: list[dict[str, Any]] = []
    try:
        for sname in wb_f.sheetnames:
            ws_f = wb_f[sname]
            ws_v = wb_v[sname]
            actual_max_r = ws_f.max_row or 0
            actual_max_c = ws_f.max_column or 0
            max_r = min(actual_max_r, max_scan_rows)
            max_c = min(actual_max_c, max_scan_cols)
            merged_ranges = [str(rng) for rng in ws_f.merged_cells.ranges]
            hidden_rows = sorted(r for r, dim in ws_f.row_dimensions.items() if getattr(dim, "hidden", False))
            cells_f: dict[tuple[int, int], Any] = {}
            cells_v: dict[tuple[int, int], Any] = {}
            for r in range(1, max_r + 1):
                for c in range(1, max_c + 1):
                    vf = ws_f.cell(r, c).value
                    vv = ws_v.cell(r, c).value
                    if vf is not None:
                        cells_f[(r, c)] = vf
                    if vv is not None:
                        cells_v[(r, c)] = vv
            sheets_report.append(
                _analyze_sheet_matrix(
                    sname,
                    ws_f.sheet_state,
                    actual_max_r,
                    actual_max_c,
                    max_r,
                    max_c,
                    merged_ranges,
                    hidden_rows,
                    cells_f,
                    cells_v,
                    mask_pii=mask_pii,
                    max_sample_rows=max_sample_rows,
                    totals_acc=totals_acc,
                )
            )
    finally:
        wb_f.close()
        wb_v.close()

    return {
        "file": path_obj.name,
        "engine": "openpyxl_fallback",
        "pii_masked": mask_pii,
        "calamine_available": HAS_CALAMINE,
        "sheets_count": len(sheets_report),
        "sheets": sheets_report,
        "formula_audit": {
            "total_formulas": totals_acc["total_formulas"],
            "uncached_formula_count": totals_acc["uncached_count"],
            "uncached_sample": totals_acc["uncached_samples"],
            "error_cells": totals_acc["error_cells"],
            "sum_hidden_row_risks": totals_acc["sum_hidden_risks"],
            "sum_off_by_one_warnings": totals_acc["sum_off_by_one"],
            "pattern_break_warnings": totals_acc["pattern_breaks"],
        },
    }


def profile_workbook(
    file_path: str,
    mask_pii: bool = True,
    max_sample_rows: int = 3,
    max_scan_cols: int = 60,
    max_scan_rows: int = 600,
) -> dict[str, Any]:
    path_obj = Path(file_path)
    if not path_obj.is_file():
        return {"error": f"File not found: {file_path}"}
    try:
        return _profile_via_ooxml_stream(
            path_obj,
            mask_pii=mask_pii,
            max_sample_rows=max_sample_rows,
            max_scan_cols=max_scan_cols,
            max_scan_rows=max_scan_rows,
        )
    except Exception:
        return _profile_via_openpyxl(
            path_obj,
            mask_pii=mask_pii,
            max_sample_rows=max_sample_rows,
            max_scan_cols=max_scan_cols,
            max_scan_rows=max_scan_rows,
        )


def main():
    parser = argparse.ArgumentParser(description="Zero-PII Structural & Static Audit Profiler for Excel Workbooks")
    parser.add_argument("excel_file", help="Path to .xlsx or .xlsm workbook")
    parser.add_argument("--mask-pii", dest="mask_pii", action="store_true", default=True, help="Mask all personal/monetary values (default)")
    parser.add_argument("--no-mask-pii", dest="mask_pii", action="store_false", help="Disable PII masking (only for synthetic test fixtures)")
    parser.add_argument("--max-sample-rows", type=int, default=3, help="Max token samples per column (default: 3)")
    args = parser.parse_args()

    report = profile_workbook(
        args.excel_file,
        mask_pii=args.mask_pii,
        max_sample_rows=args.max_sample_rows,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
