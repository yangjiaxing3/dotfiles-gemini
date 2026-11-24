#!/usr/bin/env python3
"""
Excel Multi-Engine Formula Recalculation, OOXML _xlfn Fixer & Audit Inspector (V2.5)
整合引擎降級鏈：
  1. Windows Excel COM (pywin32)         -> CalculateFullRebuild() (Windows 本機首選)
  2. PSU3D0/formualizer (Rust + Arrow)   -> 無頭高相容重算 (支援 Excel 365 現代函數)
  3. vinci1it2000/formulas (v1.3.4)      -> 純 Python AST/DAG 重算備援
  4. LibreOffice Headless (soffice)      -> Linux / macOS 無頭環境備援
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


def _bootstrap_global_xlsx_venv() -> None:
    """若當前環境缺少 openpyxl，自動掛載全域 /xlsx .venv site-packages 避免跨目錄斷路。"""
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


_bootstrap_global_xlsx_venv()
from openpyxl import load_workbook  # noqa: E402

# OOXML Future Function mapping (Excel 2010 - Excel 365)
# 使用 openpyxl 直接寫入這些函數若未加前綴，在 Excel 開啟會變 #NAME?
XLFN_MAP = {
    "XLOOKUP": "_xlfn.XLOOKUP",
    "XMATCH": "_xlfn.XMATCH",
    "LET": "_xlfn.LET",
    "LAMBDA": "_xlfn.LAMBDA",
    "FILTER": "_xlfn._xlws.FILTER",
    "SORT": "_xlfn._xlws.SORT",
    "SORTBY": "_xlfn.SORTBY",
    "UNIQUE": "_xlfn.UNIQUE",
    "SEQUENCE": "_xlfn.SEQUENCE",
    "RANDARRAY": "_xlfn.RANDARRAY",
    "TEXTJOIN": "_xlfn.TEXTJOIN",
    "TEXTSPLIT": "_xlfn.TEXTSPLIT",
    "TEXTBEFORE": "_xlfn.TEXTBEFORE",
    "TEXTAFTER": "_xlfn.TEXTAFTER",
    "VSTACK": "_xlfn.VSTACK",
    "HSTACK": "_xlfn.HSTACK",
    "TOCOL": "_xlfn.TOCOL",
    "TOROW": "_xlfn.TOROW",
    "WRAPROWS": "_xlfn.WRAPROWS",
    "WRAPCOLS": "_xlfn.WRAPCOLS",
    "TAKE": "_xlfn.TAKE",
    "DROP": "_xlfn.DROP",
    "CHOOSEROWS": "_xlfn.CHOOSEROWS",
    "CHOOSECOLS": "_xlfn.CHOOSECOLS",
    "EXPAND": "_xlfn.EXPAND",
    "IFS": "_xlfn.IFS",
    "SWITCH": "_xlfn.SWITCH",
    "MAXIFS": "_xlfn.MAXIFS",
    "MINIFS": "_xlfn.MINIFS",
    "CONCAT": "_xlfn.CONCAT",
    "IFNA": "_xlfn.IFNA",
    "XOR": "_xlfn.XOR",
}

CELL_REF_RE = re.compile(
    r"(?:(?:'([^']+)'|([A-Za-z0-9_\u4e00-\u9fa5]+))!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?"
)


def inspect_and_fix_ooxml_formulas(filename: str, auto_fix: bool = False) -> dict:
    """掃描公式之 _xlfn. 缺漏、盲目 IFERROR、SUMIFS 型別轉型風險與跨分頁依賴邊。"""
    is_xlsm = Path(filename).suffix.lower() == ".xlsm"
    wb = (
        load_workbook(filename, data_only=False, keep_vba=is_xlsm)
        if auto_fix
        else load_workbook(filename, data_only=False, read_only=True)
    )
    unprefixed_hits = []
    iferror_warnings = []
    coercion_warnings = []
    dag_edges = set()
    fixed_count = 0

    pattern_names = "|".join(sorted(XLFN_MAP.keys(), key=len, reverse=True))
    modern_fn_re = re.compile(rf"(?<![._A-Za-z0-9])({pattern_names})\s*\(", re.IGNORECASE)

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for row in ws.iter_rows():
            for cell in row:
                val = cell.value
                if not (isinstance(val, str) and val.startswith("=")):
                    continue

                coord = f"{sheet_name}!{cell.coordinate}"
                matches = modern_fn_re.findall(val)
                if matches:
                    unprefixed_hits.append({
                        "location": coord,
                        "functions": sorted({m.upper() for m in matches}),
                        "formula": val[:120],
                    })
                    if auto_fix:
                        def _repl(m):
                            fn_upper = m.group(1).upper()
                            return f"{XLFN_MAP[fn_upper]}("
                        new_val = modern_fn_re.sub(_repl, val)
                        if new_val != val:
                            cell.value = new_val
                            fixed_count += 1

                val_u = val.upper()
                if "IFERROR(" in val_u:
                    iferror_warnings.append(coord)
                if ("SUMIFS(" in val_u or "COUNTIFS(" in val_u) and '"<>"&' in val.replace(" ", ""):
                    coercion_warnings.append(coord)

                for m in CELL_REF_RE.finditer(val):
                    target_sheet = m.group(1) or m.group(2)
                    if target_sheet and target_sheet in wb.sheetnames and target_sheet != sheet_name:
                        dag_edges.add(f"{target_sheet} -> {sheet_name}")

    if auto_fix and fixed_count > 0:
        wb.save(filename)
    wb.close()

    return {
        "unprefixed_modern_functions": unprefixed_hits[:20],
        "unprefixed_count": len(unprefixed_hits),
        "auto_fixed_xlfn_count": fixed_count,
        "blind_iferror_warning_locations": iferror_warnings[:15],
        "sumifs_inequality_coercion_check": coercion_warnings[:15],
        "cross_sheet_dag_edges": sorted(dag_edges)[:30],
    }


def recalc_via_windows_com(abs_path: str) -> tuple[bool, str]:
    """Windows 首選引擎：透過本機 Excel COM 執行全量重建重算並儲存快取值。"""
    if platform.system() != "Windows":
        return False, "win32com only available on Windows"
    try:
        import win32com.client
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        wb_com = None
        try:
            wb_com = excel.Workbooks.Open(abs_path)
            excel.CalculateFullRebuild()
            wb_com.Save()
            return True, "win32com (Excel.Application CalculateFullRebuild)"
        finally:
            if wb_com is not None:
                wb_com.Close(SaveChanges=False)
            excel.Quit()
    except Exception as exc:
        return False, f"win32com failed: {exc}"


def recalc_via_formualizer(abs_path: str) -> tuple[bool, str]:
    """無頭 Rust + Arrow 引擎備援（PSU3D0/formualizer）。"""
    try:
        import formualizer  # type: ignore
        if hasattr(formualizer, "recalc_file"):
            formualizer.recalc_file(abs_path)
            return True, "PSU3D0/formualizer (recalc_file)"
        return False, "formualizer installed without recalc_file entrypoint"
    except ImportError:
        return False, "formualizer not installed"
    except Exception as exc:
        return False, f"formualizer failed: {exc}"


def recalc_via_formulas_engine(abs_path: str) -> tuple[bool, str]:
    """純 Python AST/DAG 公式重算引擎（vinci1it2000/formulas）。"""
    try:
        import formulas
        xl_model = formulas.ExcelModel().loads(abs_path).finish()
        xl_model.calculate()
        xl_model.write(dirpath=str(Path(abs_path).parent))
        return True, f"vinci1it2000/formulas (v{formulas.__version__}, nodes={len(xl_model.dsp.nodes)})"
    except Exception as exc:
        return False, f"formulas engine failed: {exc}"


def setup_libreoffice_macro() -> bool:
    """為 Linux / macOS 設定 LibreOffice 重算巨集。"""
    if platform.system() == "Darwin":
        macro_dir = os.path.expanduser("~/Library/Application Support/LibreOffice/4/user/basic/Standard")
    else:
        macro_dir = os.path.expanduser("~/.config/libreoffice/4/user/basic/Standard")

    macro_file = os.path.join(macro_dir, "Module1.xba")
    if os.path.exists(macro_file):
        with open(macro_file, "r", encoding="utf-8", errors="ignore") as f:
            if "RecalculateAndSave" in f.read():
                return True

    if not os.path.exists(macro_dir):
        try:
            subprocess.run(["soffice", "--headless", "--terminate_after_init"], capture_output=True, timeout=10)
            os.makedirs(macro_dir, exist_ok=True)
        except Exception:
            return False

    macro_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>"""
    try:
        with open(macro_file, "w", encoding="utf-8") as f:
            f.write(macro_content)
        return True
    except Exception:
        return False


def recalc_via_libreoffice(abs_path: str, timeout: int = 30) -> tuple[bool, str]:
    """Linux / macOS 備援：LibreOffice 無頭計算。"""
    if not setup_libreoffice_macro():
        return False, "LibreOffice not installed or macro setup failed"
    cmd = [
        "soffice", "--headless", "--norestore",
        "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
        abs_path,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0:
            return True, "LibreOffice Headless (soffice)"
        return False, res.stderr or f"soffice exited with {res.returncode}"
    except Exception as exc:
        return False, f"LibreOffice failed: {exc}"


def _scan_workbook_errors(abs_path: str) -> dict:
    """唯讀掃描所有儲存格之 Excel 錯誤字串與未快取公式座標（不印個人敏感明文）。"""
    wb_val = load_workbook(abs_path, data_only=True, read_only=True)
    wb_frm = load_workbook(abs_path, data_only=False, read_only=True)

    excel_errors = ["#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A", "#GETTING_DATA"]
    error_details: dict[str, list[str]] = {err: [] for err in excel_errors}
    total_errors = 0
    formula_count = 0
    uncached_formulas: list[str] = []

    try:
        for sheet_name in wb_frm.sheetnames:
            ws_f = wb_frm[sheet_name]
            ws_v = wb_val[sheet_name]
            for f_row, v_row in zip(ws_f.iter_rows(values_only=False), ws_v.iter_rows(values_only=False)):
                for cell_f, cell_v in zip(f_row, v_row):
                    f_val = cell_f.value
                    v_val = cell_v.value
                    if isinstance(f_val, str) and f_val.startswith("="):
                        formula_count += 1
                        if v_val is None and len(uncached_formulas) < 30:
                            uncached_formulas.append(f"{sheet_name}!{cell_f.coordinate}")
                    if isinstance(v_val, str):
                        for err in excel_errors:
                            if err in v_val:
                                error_details[err].append(f"{sheet_name}!{cell_v.coordinate}")
                                total_errors += 1
                                break
    finally:
        wb_val.close()
        wb_frm.close()

    error_summary = {
        err_type: {"count": len(locs), "locations": locs[:20]}
        for err_type, locs in error_details.items()
        if locs
    }
    return {
        "total_formulas": formula_count,
        "uncached_formula_count": len(uncached_formulas),
        "uncached_formula_sample": uncached_formulas[:15],
        "total_errors": total_errors,
        "error_summary": error_summary,
    }


def recalc(
    filename: str,
    timeout: int = 30,
    fix_xlfn: bool = True,
    engine_pref: str = "auto",
    audit_only: bool = False,
) -> dict:
    """執行公式靜態稽核，並依 --audit-only 決定是否寫回重算快取。"""
    path_obj = Path(filename)
    if not path_obj.exists():
        return {"error": f"File {filename} does not exist"}

    abs_path = str(path_obj.resolve())
    lint_report = inspect_and_fix_ooxml_formulas(abs_path, auto_fix=(fix_xlfn and not audit_only))

    engine_used = "audit_only (immutable)"
    engine_errors: list[str] = []

    if not audit_only:
        is_win = platform.system() == "Windows"
        if engine_pref == "com":
            chain = [("com", recalc_via_windows_com)]
        elif engine_pref == "formualizer":
            chain = [("formualizer", recalc_via_formualizer)]
        elif engine_pref == "formulas":
            chain = [("formulas", recalc_via_formulas_engine)]
        elif engine_pref == "libreoffice":
            chain = [("libreoffice", lambda p: recalc_via_libreoffice(p, timeout))]
        elif is_win:
            chain = [
                ("com", recalc_via_windows_com),
                ("formualizer", recalc_via_formualizer),
                ("formulas", recalc_via_formulas_engine),
            ]
        else:
            chain = [
                ("formualizer", recalc_via_formualizer),
                ("libreoffice", lambda p: recalc_via_libreoffice(p, timeout)),
                ("formulas", recalc_via_formulas_engine),
            ]

        recalc_ok = False
        for _name, fn in chain:
            recalc_ok, msg = fn(abs_path)
            if recalc_ok:
                engine_used = msg
                break
            engine_errors.append(msg)

        if not recalc_ok:
            return {
                "error": "All recalculation engines failed",
                "attempted_engines": engine_errors,
                "static_analysis": lint_report,
            }

    scan = _scan_workbook_errors(abs_path)
    return {
        "status": "success" if scan["total_errors"] == 0 else "errors_found",
        "audit_only": audit_only,
        "engine_used": engine_used,
        "engine_warnings": engine_errors if engine_errors else [],
        "total_formulas": scan["total_formulas"],
        "uncached_formula_count": scan["uncached_formula_count"],
        "uncached_formula_sample": scan["uncached_formula_sample"],
        "total_errors": scan["total_errors"],
        "error_summary": scan["error_summary"],
        "static_analysis": lint_report,
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-Engine Excel Formula Recalculator & Static Audit Inspector")
    parser.add_argument("excel_file", help="Path to the .xlsx or .xlsm file")
    parser.add_argument("timeout", nargs="?", type=int, default=30, help="Timeout in seconds (default: 30)")
    parser.add_argument("--audit-only", action="store_true", help="Immutable static & error scan without modifying workbook")
    parser.add_argument("--no-fix-xlfn", action="store_true", help="Do not auto-prefix modern Excel functions with _xlfn.")
    parser.add_argument(
        "--engine",
        choices=["auto", "com", "formualizer", "formulas", "libreoffice"],
        default="auto",
        help="Preferred recalculation engine",
    )
    args = parser.parse_args()

    res = recalc(
        args.excel_file,
        timeout=args.timeout,
        fix_xlfn=not args.no_fix_xlfn,
        engine_pref=args.engine,
        audit_only=args.audit_only,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
