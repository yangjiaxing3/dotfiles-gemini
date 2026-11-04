---
name: data-autocleaning
description: "Use when building automated data cleaning, deduplication, and schema normalization rules in BigQuery/Dataform. 自動化資料清洗與正規化"
license: Apache-2.0
version: v1
---

# Data Autocleaning Skill

Automated data profiling, quality assessment, and transformation for data
sourced from **BigQuery** or **Google Cloud Storage (GCS)**.

## When to Use

> [!IMPORTANT]
>
> You **MUST** use this skill for **ANY** task where the source is BigQuery or
> GCS — including seemingly simple operations like "move data" or "copy table".

-   Apply to **all operations** on new and existing sources: copying, moving,
    appending, ingesting, or extracting data.
-   Apply to the **source node** specifically, not to subsequent pipeline steps.
-   **Never skip** Dataplex profiling (Steps 1 and 3). Always use Dataplex —
    **not** ad-hoc BigQuery profiling.

## Task Execution Workflow

### Step 1: Preliminary Checks (Before Implementation Planning)

Perform these checks **before** generating the `implementation_plan.md`.

1.  **Check Eligibility** — You MUST confirm the source is a BigQuery table or
    GCS source.
2.  **Gather Data Profile via Dataplex**:

    -   **GCS sources**: For GCS sources, you MUST create an external table
        first before running the dataplex scan.
    -   **Wait for results**: You **MUST NOT** proceed until the Dataplex
        profile is available, unless user scan approval was denied.
    -   Use the profile as input for cleansing and schema mapping decisions. The
        transformations **MUST NOT** be finalized before profile information is
        available (unless scan was denied).
    -   **Commands**:

        1.  **Obtain user approval**: Present the `scripts/dataplex_scanner.py`
            scan command to the user and obtain explicit approval before
            executing it. Use the following template to present the command:
            -   **Command**: `python3 scripts/dataplex_scanner.py ...` (Fetch
                full arguments from step 6 below)
            -   **Summary**: The script automates Dataplex data profiling. It
                checks table sizes, applies dynamic sampling for large tables
                (>1M rows) to reduce costs, skips empty tables, executes
                concurrent scans for multiple tables, and polls for results
                automatically.
            -   **Value Add**: Enables deep data analysis (null rates, distinct
                values, distributions) allowing data-driven cleansing decisions.
                It helps identify hidden anomalies (garbage values, format
                variance) to guide accurate transformations and verifies that
                the cleaning logic resolves them without introducing
                regressions.
            -   **Scope**: The approval obtained here covers all executions of
                this scanner script for this task (including verification
                steps).
        2.  Run the `scripts/dataplex_scanner.py` script located in the same
            directory as this `SKILL.md` file. This script handles concurrent
            scan creation, dynamic sampling for large tables, and polling for
            results. Use --help to learn more.
        3.  The script will save the full results as JSON files in the specified
            output directory.
        4.  **[!IMPORTANT]** The location MUST be a specific Google Cloud region
            like `us-central1`; multi-regions like `us` are not supported in
            Dataplex scan.
        5.  If there are multiple tables to scan, provide them all in the
            `--tables` argument to run them concurrently.
        6.  Use the following command template:

            ```bash
            python3 scripts/dataplex_scanner.py \
              --tables <project.dataset.table> <project.catalog.namespace.table> \
              --location <location> \
              --output-dir <output_dir>
            ```

            Note: The script accepts table IDs in the format
            `project.dataset.table` for BigQuery tables and
            `project.catalog.namespace.table` for BigLake Iceberg tables.

3.  **Fetch Schema & Samples** — Use `bq` commands to fetch schema and sample
    data for **both** source and destination tables.

### Step 1.5: Implementation Plan Requirements

1.  Your `implementation_plan.md` **MUST** include a **Profiling Evidence**
    section. **Note**: If scan execution was denied by the user, document the
    denial reason here instead of Job IDs.

```markdown
## Profiling Evidence
- [ ] Dataplex Data Profile Job ID: <JOB_ID>
- [ ] Profile Result Summary: <Brief summary of key findings, e.g., % nulls, distinct values>
```

1.  Your `implementation_plan.md` **MUST** include a step to generate cleansing
    SQL transformations based on the profile output and instructions in Step 2:
    Generate Transformations.
2.  Your `implementation_plan.md` **MUST** also reference Step 3 (Quality
    Review) under its **Verification Plan** section.

> [!CAUTION]
>
> **Do not proceed to implementation** until both sections are completed. You
> MUST ensure that the verification phase only validates that your
> transformations successfully addressed the anomalies found in Step 1.

### Step 2: Generate Transformations

#### Schema Alignment

-   Match the destination table schema (types and names) if provided.
-   **Do not** perform column splits, merges, or other schema operations when no
    destination table is specified.

#### Data Cleaning Rules

-   **Garbage Values**: Drop or convert to `NULL` only for malformed data (e.g.,
    unparseable dates, zero-length strings for non-nullable integers).
-   **Unit Normalization**: Standardize measurable units (e.g., `'C'` → `'F'`)
    to the most common unit. If units are too varied (e.g., `mg`, `liter`),
    leave as-is.
-   **Type Conversion**: Use `COALESCE` with `SAFE.PARSE_*` functions for
    multiple date/time/datetime/timestamp formats. Fetch diverse samples when
    source data shows high variance.

#### JSON Data Handling

-   **Parsing**: Use `SAFE.PARSE_JSON` to cast JSON strings to `JSON` type.
    **Never** use deprecated `JSON_EXTRACT_*`.
-   **Extraction**: Flatten or extract fields **only** if a destination schema
    requires it.
-   **Accessors**: Use `JSON_VALUE`, `JSON_QUERY`, `JSON_QUERY_ARRAY`,
    `JSON_VALUE_ARRAY` without `SAFE.` prefix (they are safe by default).
-   **Schema mapping**: When a destination schema is provided, extract JSON
    fields to match target column names and types.
-   **NULL handling**: If `SAFE.PARSE_JSON` returns NULL, keep the original
    string and note the invalid JSON in the cleaning summary.

#### Array Data Handling

## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
