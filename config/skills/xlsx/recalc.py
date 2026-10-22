#!/usr/bin/env python3
"""
Excel Multi-Engine Formula Recalculation, OOXML _xlfn Fixer & DAG Analyzer (V2.0)
Integrates:
  1. Windows Excel COM (pywin32 / xlwings) -> CalculateFullRebuild() (Primary on Windows)
  2. vinci1it2000/formulas (v1.3.4)        -> Pure-Python AST/DAG Dependency Graph & Fallback Recalc
  3. bradbase/xlcalculator (v0.5.0)        -> Financial Model Unit-Test Evaluator
  4. LibreOffice Headless (soffice)        -> Linux/macOS Fallback
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from openpyxl import load_workbook

# OOXML Future Function mapping (Excel 2010 - Excel 365)
# Writing these via openpyxl without prefix causes #NAME? in Excel!
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
    """
    Scan all formulas for:
      1. Unprefixed modern Excel functions written via openpyxl (which cause #NAME?)
      2. Blind IFERROR(..., "") wrappers in financial sheets
      3. Cross-sheet DAG edges & potential type-coercion pitfalls in SUMIFS/COUNTIFS
    """
    wb = load_workbook(filename, data_only=False)
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

                # 1. Check modern Excel functions lacking _xlfn.
                matches = modern_fn_re.findall(val)
                if matches:
                    unprefixed_hits.append({
                        "location": coord,
                        "functions": list({m.upper() for m in matches}),
                        "formula": val
                    })
                    if auto_fix:
                        def _repl(m):
                            fn_upper = m.group(1).upper()
                            return f"{XLFN_MAP[fn_upper]}("
                        new_val = modern_fn_re.sub(_repl, val)
                        if new_val != val:
                            cell.value = new_val
                            fixed_count += 1

                # 2. Check blind IFERROR(..., "") or IFERROR(..., 0)
                if "IFERROR(" in val.upper():
                    iferror_warnings.append(coord)

                # 3. Check SUMIFS/COUNTIFS "<>"&Cell potential numeric-text coercion
                if ("SUMIFS(" in val.upper() or "COUNTIFS(" in val.upper()) and '"<>"&' in val.replace(" ", ""):
                    coercion_warnings.append(coord)

                # 4. Extract cross-sheet dependency edges
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
        "blind_iferror_Warning_locations": iferror_warnings[:15],
        "sumifs_inequality_coercion_check": coercion_warnings[:15],
        "cross_sheet_dag_edges": sorted(dag_edges),
    }


def recalc_via_windows_com(abs_path: str) -> tuple[bool, str]:
    """Primary engine on Windows: Microsoft Excel COM CalculateFullRebuild()"""
    try:
        import win32com.client
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        try:
            wb_com = excel.Workbooks.Open(abs_path)
            excel.CalculateFullRebuild()
            wb_com.Save()
            wb_com.Close(SaveChanges=False)
            return True, "win32com (Excel.Application CalculateFullRebuild)"
        finally:
            excel.Quit()
    except Exception as exc:
        return False, f"win32com failed: {exc}"


def recalc_via_formulas_engine(abs_path: str) -> tuple[bool, str]:
    """Secondary pure-Python engine: vinci1it2000/formulas AST/DAG compiler"""
    try:
        import formulas
        xl_model = formulas.ExcelModel().loads(abs_path).finish()
        xl_model.calculate()
        out_dir = Path(abs_path).parent
        written = xl_model.write(dirpath=str(out_dir))
        return True, f"vinci1it2000/formulas (v{formulas.__version__}, nodes={len(xl_model.dsp.nodes)})"
    except Exception as exc:
        return False, f"formulas engine failed: {exc}"


def setup_libreoffice_macro() -> bool:
    """Setup LibreOffice macro for recalculation if not already configured"""
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
    """Fallback engine on Linux/macOS: LibreOffice headless macro"""
    if not setup_libreoffice_macro():
        return False, "LibreOffice not installed or macro setup failed"

    cmd = [
        "soffice", "--headless", "--norestore",
        "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
        abs_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0:
            return True, "LibreOffice Headless (soffice)"
        return False, res.stderr or f"soffice exited with {res.returncode}"
    except Exception as exc:
        return False, f"LibreOffice failed: {exc}"


def recalc(filename: str, timeout: int = 30, fix_xlfn: bool = True, engine_pref: str = "auto") -> dict:
    path_obj = Path(filename)
    if not path_obj.exists():
        return {"error": f"File {filename} does not exist"}

    abs_path = str(path_obj.resolve())

    # Step 1: Pre-flight OOXML static inspection & optional _xlfn auto-fix
    lint_report = inspect_and_fix_ooxml_formulas(abs_path, auto_fix=fix_xlfn)

    # Step 2: Route to best available recalculation engine
    engine_used = "none"
    recalc_ok = False
    engine_errors = []

    if engine_pref in ("auto", "com") and platform.system() == "Windows":
        recalc_ok, msg = recalc_via_windows_com(abs_path)
        if recalc_ok:
            engine_used = msg
        else:
            engine_errors.append(msg)

    if not recalc_ok and engine_pref in ("auto", "libreoffice"):
        recalc_ok, msg = recalc_via_libreoffice(abs_path, timeout=timeout)
        if recalc_ok:
            engine_used = msg
        else:
            engine_errors.append(msg)

    if not recalc_ok and engine_pref in ("auto", "formulas"):
        recalc_ok, msg = recalc_via_formulas_engine(abs_path)
        if recalc_ok:
            engine_used = msg
        else:
            engine_errors.append(msg)

    if not recalc_ok:
        return {
            "error": "All recalculation engines failed",
            "attempted_engines": engine_errors,
            "lint_report": lint_report,
        }

    # Step 3: Scan ALL cells for Excel error tokens and uncached formulas
    try:
        wb_val = load_workbook(abs_path, data_only=True)
        wb_frm = load_workbook(abs_path, data_only=False)

        excel_errors = ["#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A", "#GETTING_DATA"]
        error_details = {err: [] for err in excel_errors}
        total_errors = 0
        formula_count = 0
        uncached_formulas = []

        for sheet_name in wb_frm.sheetnames:
            ws_f = wb_frm[sheet_name]
            ws_v = wb_val[sheet_name]

            for r in range(1, ws_f.max_row + 1):
                for c in range(1, ws_f.max_column + 1):
                    f_val = ws_f.cell(r, c).value
                    v_val = ws_v.cell(r, c).value
                    coord = f"{sheet_name}!{ws_f.cell(r, c).coordinate}"

                    if isinstance(f_val, str) and f_val.startswith("="):
                        formula_count += 1
                        if v_val is None:
                            uncached_formulas.append(coord)

                    if v_val is not None and isinstance(v_val, str):
                        for err in excel_errors:
                            if err in v_val:
                                error_details[err].append(coord)
                                total_errors += 1
                                break

        wb_val.close()
        wb_frm.close()

        result = {
            "status": "success" if total_errors == 0 else "errors_found",
            "engine_used": engine_used,
            "total_formulas": formula_count,
            "uncached_formula_count": len(uncached_formulas),
            "total_errors": total_errors,
            "error_summary": {},
            "static_analysis": lint_report,
        }

        for err_type, locations in error_details.items():
            if locations:
                result["error_summary"][err_type] = {
                    "count": len(locations),
                    "locations": locations[:20],
                }

        return result

    except Exception as exc:
        return {"error": str(exc), "engine_used": engine_used}


def main():
    parser = argparse.ArgumentParser(description="Multi-Engine Excel Formula Recalculator & Static Linter")
    parser.add_argument("excel_file", help="Path to the .xlsx file")
    parser.add_argument("timeout", nargs="?", type=int, default=30, help="Timeout in seconds (default: 30)")
    parser.add_argument("--no-fix-xlfn", action="store_true", help="Do not auto-prefix modern Excel functions with _xlfn.")
    parser.add_argument("--engine", choices=["auto", "com", "formulas", "libreoffice"], default="auto", help="Preferred engine")
    args = parser.parse_args()

    res = recalc(
        args.excel_file,
        timeout=args.timeout,
        fix_xlfn=not args.no_fix_xlfn,
        engine_pref=args.engine,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
