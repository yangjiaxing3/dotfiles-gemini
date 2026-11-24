#!/usr/bin/env python3
"""
Formula Engine Hub for /xlsx Skill
Combines GitHub's open-source spreadsheet formula engines:
  1. vinci1it2000/formulas / networkx  -> AST/DAG Dependency Graph & Topological Depth
  2. bradbase/xlcalculator (v0.5.0)    -> What-If Scenario & Unit Test Evaluator
  3. OOXML _xlfn. Translator           -> Converts Excel 365 formulas for safe openpyxl writing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _bootstrap_paths() -> None:
    """確保可跨目錄匯入同門 recalc.py 及全域 /xlsx .venv 依賴。"""
    skill_dir = Path(__file__).resolve().parent.parent
    if str(skill_dir) not in sys.path:
        sys.path.insert(0, str(skill_dir))
    try:
        import networkx  # noqa: F401
        import openpyxl  # noqa: F401
        return
    except ImportError:
        pass
    venv_candidates = [
        skill_dir / ".venv" / "Lib" / "site-packages",
        Path.home() / ".gemini" / "config" / "skills" / "xlsx" / ".venv" / "Lib" / "site-packages",
    ]
    for cand in venv_candidates:
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


_bootstrap_paths()

import networkx as nx  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from recalc import XLFN_MAP, CELL_REF_RE  # noqa: E402


def translate_to_ooxml_xlfn(formula: str) -> str:
    """Translate modern Excel 365 functions (LET, LAMBDA, XLOOKUP, FILTER...) to OOXML _xlfn. format."""
    pattern_names = "|".join(sorted(XLFN_MAP.keys(), key=len, reverse=True))
    modern_fn_re = re.compile(rf"(?<![._A-Za-z0-9])({pattern_names})\s*\(", re.IGNORECASE)

    def _repl(m):
        fn_upper = m.group(1).upper()
        return f"{XLFN_MAP[fn_upper]}("

    return modern_fn_re.sub(_repl, formula)


def build_workbook_dag(excel_path: str) -> dict:
    """Build cell-level & sheet-level Dependency Graph (DAG), detecting circular references & hotspots."""
    wb = load_workbook(excel_path, data_only=False, read_only=True)
    cell_graph = nx.DiGraph()
    sheet_graph = nx.DiGraph()
    formula_cells = 0

    try:
        for sname in wb.sheetnames:
            sheet_graph.add_node(sname)
            ws = wb[sname]
            for row in ws.iter_rows():
                for cell in row:
                    val = cell.value
                    if not (isinstance(val, str) and val.startswith("=")):
                        continue
                    formula_cells += 1
                    target_node = f"{sname}!{cell.coordinate}"
                    cell_graph.add_node(target_node)

                    for m in CELL_REF_RE.finditer(val):
                        ref_sheet = m.group(1) or m.group(2) or sname
                        full_match = m.group(0)
                        ref_coord = full_match.split("!")[-1].replace("$", "")
                        src_node = f"{ref_sheet}!{ref_coord}"
                        cell_graph.add_edge(src_node, target_node)
                        if ref_sheet != sname and ref_sheet in wb.sheetnames:
                            sheet_graph.add_edge(ref_sheet, sname)
    finally:
        wb.close()

    # Large workbooks can have many SCCs; bound simple cycle inspection safely
    cycles = []
    try:
        if cell_graph.number_of_edges() <= 50000:
            for c in nx.simple_cycles(cell_graph):
                cycles.append(c)
                if len(cycles) >= 10:
                    break
        else:
            is_acyclic = nx.is_directed_acyclic_graph(cell_graph)
            if not is_acyclic:
                cycles = [["cycle_detected_in_large_graph"]]
    except Exception:
        cycles = []

    is_dag = len(cycles) == 0
    max_depth = 0
    if is_dag and cell_graph.number_of_nodes() > 0:
        try:
            max_depth = nx.dag_longest_path_length(cell_graph)
        except Exception:
            max_depth = 0

    hotspots = sorted(
        [(n, d) for n, d in cell_graph.out_degree() if d > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:10]

    return {
        "file": str(Path(excel_path).name),
        "total_formula_cells": formula_cells,
        "dag_nodes": cell_graph.number_of_nodes(),
        "dag_edges": cell_graph.number_of_edges(),
        "is_acyclic_dag": is_dag,
        "circular_references": cycles[:10],
        "max_topological_depth": max_depth,
        "sheet_dependencies": [f"{u} -> {v}" for u, v in sheet_graph.edges()][:30],
        "top_dependency_hotspots": [{"node": n, "dependents": d} for n, d in hotspots],
    }


def evaluate_what_if(excel_path: str, targets: list[str], overrides: list[str]) -> dict:
    """Evaluate target cells with optional input overrides using xlcalculator."""
    from xlcalculator import ModelCompiler, Evaluator

    compiler = ModelCompiler()
    model = compiler.read_and_parse_archive(excel_path)
    evaluator = Evaluator(model)

    applied_overrides = {}
    for item in overrides:
        if "=" not in item:
            continue
        addr, raw_val = item.split("=", 1)
        addr = addr.strip()
        try:
            parsed_val = float(raw_val) if "." in raw_val else int(raw_val)
        except ValueError:
            parsed_val = raw_val
        evaluator.set_cell_value(addr, parsed_val)
        applied_overrides[addr] = parsed_val

    results = {}
    for t in targets:
        t_addr = t.strip()
        results[t_addr] = evaluator.evaluate(t_addr)

    return {
        "engine": "bradbase/xlcalculator",
        "overrides_applied": applied_overrides,
        "evaluated_targets": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Formula Engine Hub for /xlsx Skill")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dag = sub.add_parser("dag", help="Analyze workbook formula DAG, topological depth, and circular refs")
    p_dag.add_argument("excel_file", help="Path to .xlsx or .xlsm file")

    p_xlfn = sub.add_parser("xlfn", help="Translate modern Excel 365 formula string to OOXML _xlfn. syntax")
    p_xlfn.add_argument("formula", help="Formula string starting with =")

    p_eval = sub.add_parser("eval", help="Run headless What-If unit test on Excel formulas via xlcalculator")
    p_eval.add_argument("excel_file", help="Path to .xlsx file")
    p_eval.add_argument("targets", nargs="+", help="Target cell addresses (e.g. Sheet1!B10)")
    p_eval.add_argument("--set", nargs="*", default=[], help="Override input cells (e.g. Sheet1!A2=100)")

    args = parser.parse_args()

    if args.cmd == "dag":
        out = build_workbook_dag(args.excel_file)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif args.cmd == "xlfn":
        out = {
            "original": args.formula,
            "ooxml_safe_formula": translate_to_ooxml_xlfn(args.formula),
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif args.cmd == "eval":
        out = evaluate_what_if(args.excel_file, args.targets, args.set)
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
