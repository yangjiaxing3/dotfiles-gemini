#!/usr/bin/env python3
"""
Storeasy 6-Repo Nexus Brain Synchronizer (C:\\Users\\Jiaxing\\.gemini\\scripts\\update_storeasy_nexus.py)

注意：只在本機跑，不碰任何 Turso 正式庫，不讀或印出任何 env / token 值。
以 C:\\Users\\Jiaxing\\.graphify\\nexus-cross-links.json 為跨專案契約單一真相來源 (SoT)，
將 B 重新注入 C (C:\\Users\\Jiaxing\\.graphify\\global-graph.json)。
"""
import json
import pathlib

NEXUS_CL_PATH = pathlib.Path(r"C:\Users\Jiaxing\.graphify\nexus-cross-links.json")
GLOBAL_GRAPH_PATH = pathlib.Path(r"C:\Users\Jiaxing\.graphify\global-graph.json")


def sync_from_cross_links() -> None:
    if not NEXUS_CL_PATH.exists():
        raise FileNotFoundError(f"Missing SoT file: {NEXUS_CL_PATH}")
    if not GLOBAL_GRAPH_PATH.exists():
        raise FileNotFoundError(f"Missing global graph: {GLOBAL_GRAPH_PATH}")

    cross_links = json.loads(NEXUS_CL_PATH.read_text(encoding="utf-8"))
    g = json.loads(GLOBAL_GRAPH_PATH.read_text(encoding="utf-8"))

    # 1. 移除先前注入的舊版 XREF / turso / policy 節點與邊，以及違反 POLICY_FINHR_NO_PAYROLL_OUTBOUND
    #    未經三審核准的 FinHRPayrollMirror 節點，確保 global-graph.json 與 B 完全一致
    def _is_stale_or_blocked_node(n: dict) -> bool:
        ntype = str(n.get("type") or "")
        nid = str(n.get("id") or "")
        lbl = str(n.get("label") or "")
        if ntype in ("xref_endpoint", "turso_database", "governance_policy"):
            return True
        if nid.startswith(("turso:", "POLICY_")):
            return True
        if "FinHRPayrollMirror" in nid or "FinHRPayrollMirror" in lbl:
            return True
        return False

    nodes = [n for n in g.get("nodes", []) if not _is_stale_or_blocked_node(n)]
    valid_node_ids = {n.get("id") for n in nodes}

    links = [
        e
        for e in g.get("links", [])
        if not str(e.get("relation") or e.get("type") or "").startswith("XREF_")
        and e.get("source") in valid_node_ids
        and e.get("target") in valid_node_ids
    ]

    existing_ids = {n.get("id") for n in nodes}
    added_nodes = 0
    added_edges = 0

    # 2. 注入 B 定義的顯式節點（如 turso:storeasy-finhr、turso:storeasy-db、POLICY_FINHR_NO_PAYROLL_OUTBOUND）
    for cnode in cross_links.get("nodes", []):
        cid = cnode["id"]
        if cid not in existing_ids:
            nodes.append(
                {
                    "id": cid,
                    "label": cnode.get("label", cid),
                    "type": cnode.get("type", "xref_node"),
                    "source_file": cnode.get("source_file", cid),
                    "repo": cnode.get("repo", ""),
                    "decided_at": cnode.get("decided_at", ""),
                    "attributes": cnode.get("attributes", {}),
                }
            )
            existing_ids.add(cid)
            added_nodes += 1

    # 3. 注入 B 定義的所有跨專案 XREF_ 與 POLICY 邊（若端點節點不存在則自動補齊）
    existing_edges = {(e.get("source"), e.get("target"), e.get("relation")) for e in links}
    for item in cross_links.get("links", []):
        for endpoint_id in (item["source"], item["target"]):
            if endpoint_id not in existing_ids:
                nodes.append(
                    {
                        "id": endpoint_id,
                        "label": endpoint_id.split("::")[-1],
                        "type": "xref_endpoint",
                        "source_file": endpoint_id,
                        "repo": endpoint_id.split("::")[0] if "::" in endpoint_id else "",
                    }
                )
                existing_ids.add(endpoint_id)
                added_nodes += 1

        edge_key = (item["source"], item["target"], item["relation"])
        if edge_key not in existing_edges:
            attrs = item.get("attributes", {})
            links.append(
                {
                    "id": item.get("id", ""),
                    "source": item["source"],
                    "target": item["target"],
                    "relation": item["relation"],
                    "type": item["relation"],
                    "endpoint": item.get("endpoint", ""),
                    "shared_table": item.get("shared_table", ""),
                    "revalidate_tag": item.get("revalidate_tag", ""),
                    "description": item.get("description", ""),
                    "write_risk": attrs.get("write_risk", False),
                    "governance": attrs.get("governance", "normal"),
                    "decided_at": attrs.get("decided_at", ""),
                    "attributes": attrs,
                    "confidence": 1.0,
                }
            )
            existing_edges.add(edge_key)
            added_edges += 1

    # 4. 為讓 `graphify query "FinHR turso"` 能直接從 AST 節點連通到 `turso:storeasy-finhr`，
    #    將 StoreasyFinHR 的 database.py 節點連向 `turso:storeasy-finhr`
    for n in nodes:
        if n.get("label") == "database.py" and "StoreasyFinHR" in str(n.get("id", "")):
            ek = (n["id"], "turso:storeasy-finhr", "XREF_FINHR_INDEPENDENT_TURSO")
            if ek not in existing_edges:
                links.append(
                    {
                        "id": "xref_finhr_ast_db_to_turso",
                        "source": n["id"],
                        "target": "turso:storeasy-finhr",
                        "relation": "XREF_FINHR_INDEPENDENT_TURSO",
                        "type": "XREF_FINHR_INDEPENDENT_TURSO",
                        "description": "FinHR database.py connects exclusively to independent Turso DB storeasy-finhr",
                        "write_risk": False,
                        "governance": "sensitive",
                        "decided_at": "2026-10-22",
                        "attributes": {
                            "write_risk": False,
                            "governance": "sensitive",
                            "decided_at": "2026-10-22",
                        },
                        "confidence": 1.0,
                    }
                )
                existing_edges.add(ek)
                added_edges += 1

    g["version"] = cross_links.get("version", "2026-10-31b")
    g["nodes"] = nodes
    g["links"] = links
    GLOBAL_GRAPH_PATH.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    print(
        f"[OK] Re-injected {NEXUS_CL_PATH.name} (v={g['version']}) -> {GLOBAL_GRAPH_PATH.name}: "
        f"+{added_nodes} nodes, +{added_edges} edges | Total: {len(nodes)} nodes, {len(links)} edges"
    )


if __name__ == "__main__":
    sync_from_cross_links()
