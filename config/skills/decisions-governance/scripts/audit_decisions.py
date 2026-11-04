#!/usr/bin/env python3
"""
Deterministic Auditor for DECISIONS.md & docs/decisions/ across Storeasy & US3C repositories.
檢查項目：
1. DECISIONS.md 有效條目數量是否超過警戒門檻 (預設 25 條)
2. docs/decisions/NNNN-*.md 每份小檔是否維持在精簡範圍 (<= 25 行)
3. 目錄連結與實際檔案是否雙向對齊 (無斷鏈、無孤兒檔)
4. 目錄表狀態 (有效/被取代) 與小檔內部 `- **狀態**` 是否雙向一致
5. 檢查是否有到期的複查提醒 (due_date <= today 時列入 overdue_reviews 並發出告警)
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_REPOS = [
    Path(r"C:\Users\Jiaxing\Documents\GitHub\us3c-next"),
    Path(r"C:\Users\Jiaxing\Documents\GitHub\StoreasyFMnew"),
    Path(r"C:\Users\Jiaxing\Documents\GitHub\STOREASY_IT"),
    Path(r"C:\Users\Jiaxing\Documents\GitHub\storeasynewwebsite"),
    Path(r"C:\Users\Jiaxing\Documents\GitHub\Storeasyworkdivnew"),
]

MAX_ACTIVE_DECISIONS = 25
MAX_ADR_LINES = 25


def resolve_repos() -> list[Path]:
    existing = [r for r in DEFAULT_REPOS if r.exists()]
    # Fallback for Linux / Cloud Agent VM where local Windows paths do not exist
    script_repo = Path(__file__).resolve().parents[3]
    if (script_repo / "DECISIONS.md").exists() and script_repo not in existing:
        existing.insert(0, script_repo)
    return existing


def audit_repo(repo_path: Path, today: str) -> dict:
    decisions_md = repo_path / "DECISIONS.md"
    decisions_dir = repo_path / "docs" / "decisions"

    result = {
        "repo": repo_path.name,
        "has_decisions_md": decisions_md.exists(),
        "has_decisions_dir": decisions_dir.exists(),
        "active_count": 0,
        "superseded_count": 0,
        "linked_files": [],
        "missing_files": [],
        "orphan_files": [],
        "bloated_files": [],
        "status_mismatches": [],
        "due_reviews": [],
        "overdue_reviews": [],
        "warnings": [],
    }

    if not decisions_md.exists():
        result["warnings"].append("Missing root DECISIONS.md")
        return result

    text = decisions_md.read_text(encoding="utf-8", errors="ignore")
    row_pattern = re.compile(
        r"^\|\s*`?(\d{4})`?\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*([^|]+)\|",
        re.M,
    )

    linked_set = set()
    for match in row_pattern.finditer(text):
        num, title, rel_link, status, date_str = [m.strip() for m in match.groups()]
        linked_set.add(Path(rel_link).name)
        result["linked_files"].append(rel_link)
        is_active_in_index = "有效" in status and "取代" not in status
        is_superseded_in_index = "取代" in status

        if is_active_in_index:
            result["active_count"] += 1
        elif is_superseded_in_index:
            result["superseded_count"] += 1

        target_file = repo_path / rel_link
        if not target_file.exists():
            result["missing_files"].append(rel_link)
        else:
            lines = target_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(lines) > MAX_ADR_LINES:
                result["bloated_files"].append({"file": rel_link, "lines": len(lines)})
            body_text = "\n".join(lines)

            status_m = re.search(r"^-\s*\*\*狀態\*\*[：:]\s*(.+)$", body_text, re.M)
            if status_m:
                file_status = status_m.group(1).strip()
                file_active = "有效" in file_status and "取代" not in file_status
                if is_active_in_index != file_active:
                    result["status_mismatches"].append(
                        {"file": rel_link, "index_status": status, "file_status": file_status}
                    )

            for due_m in re.finditer(r"(20\d{2}-\d{2}-\d{2}).*?(複查|檢查|#\d+)", body_text):
                due_date = due_m.group(1)
                entry = {"file": rel_link, "due_date": due_date, "note": due_m.group(0)}
                result["due_reviews"].append(entry)
                if is_active_in_index and due_date <= today:
                    result["overdue_reviews"].append(entry)
                    result["warnings"].append(f"Overdue review in {rel_link}: {due_date}")

    if result["active_count"] > MAX_ACTIVE_DECISIONS:
        result["warnings"].append(
            f"Active decisions ({result['active_count']}) exceed threshold ({MAX_ACTIVE_DECISIONS}); review for consolidation."
        )

    if decisions_dir.exists():
        for f in sorted(decisions_dir.glob("*.md")):
            if f.name == "0000-template.md":
                continue
            if f.name not in linked_set:
                result["orphan_files"].append(f.name)

    return result


def main() -> None:
    today = datetime.date.today().isoformat()
    repos = resolve_repos()
    reports = [audit_repo(r, today) for r in repos]
    summary = {
        "audit_date": today,
        "total_repos_audited": len(reports),
        "all_healthy": len(reports) > 0
        and all(
            r["has_decisions_md"]
            and not r["missing_files"]
            and not r["orphan_files"]
            and not r["bloated_files"]
            and not r["status_mismatches"]
            and not r["overdue_reviews"]
            and not r["warnings"]
            for r in reports
        ),
        "repos": reports,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
