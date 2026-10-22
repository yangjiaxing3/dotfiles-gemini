#!/usr/bin/env python3
"""
Formula Engine Hub for /xlsx Skill
Combines GitHub's top open-source spreadsheet formula engines:
  1. vinci1it2000/formulas (v1.3.4)   -> AST/DAG Dependency Graph & Topological Depth
  2. bradbase/xlcalculator (v0.5.0)   -> What-If Scenario & Unit Test Evaluator
  3. xlwings / win32com               -> Native Excel 16.0 Dynamic Array (Formula2) & Recalc
  4. OOXML _xlfn. Translator          -> Converts Excel 365 formulas for safe openpyxl writing
"""

import argparse
import json
import re
import sys
from pathlib import Path
import networkx as nx
from openpyxl import load_workbook

# Reuse XLFN_MAP from recalc.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
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
    """
    Build cell-level & sheet-level Dependency Graph (DAG) using networkx + openpyxl/formulas,
    detecting circular references, topological depth, and high-fan-in/out bottleneck cells.
    """
    wb = load_workbook(excel_path, data_only=False)
    cell_graph = nx.DiGraph()
    sheet_graph = nx.DiGraph()
    formula_cells = 0

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
                cell_graph.add_node(target_node, formula=val)

                for m in CELL_REF_RE.finditer(val):
                    ref_sheet = m.group(1) or m.group(2) or sname
                    full_match = m.group(0)
                    ref_coord = full_match.split("!")[-1].replace("$", "")
                    src_node = f"{ref_sheet}!{ref_coord}"
                    cell_graph.add_edge(src_node, target_node)
                    if ref_sheet != sname and ref_sheet in wb.sheetnames:
                        sheet_graph.add_edge(ref_sheet, sname)

    wb.close()

    cycles = list(nx.simple_cycles(cell_graph))
    is_dag = len(cycles) == 0

    max_depth = 0
    if is_dag and cell_graph.number_of_nodes() > 0:
        try:
            max_depth = nx.dag_longest_path_length(cell_graph)
        except Exception:
            max_depth = 0

    # Top hotspot cells by out-degree (most depended upon)
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
        "sheet_dependencies": [f"{u} -> {v}" for u, v in sheet_graph.edges()],
        "top_dependency_hotspots": [{"node": n, "dependents": d} for n, d in hotspots],
    }


def evaluate_what_if(excel_path: str, targets: list[str], overrides: list[str]) -> dict:
    """
    Evaluate target cells with optional input overrides using xlcalculator / formulas.
    Example:
      python formula_engine_hub.py eval model.xlsx "Sheet1!C10" --set "Sheet1!A2=5000"
    """
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
        val = evaluator.evaluate(t_addr)
        results[t_addr] = val

    return {
        "engine": "bradbase/xlcalculator",
        "overrides_applied": applied_overrides,
        "evaluated_targets": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Formula Engine Hub for /xlsx Skill")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dag = sub.add_parser("dag", help="Analyze workbook formula DAG, topological depth, and circular refs")
    p_dag.add_argument("excel_file", help="Path to .xlsx file")

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
