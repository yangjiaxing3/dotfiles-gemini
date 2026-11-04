---
name: dbt-bigquery
description: "Use when creating, testing, or optimizing dbt models and macros targeting BigQuery. BigQuery dbt模型開發與優化"
license: Apache-2.0
version: v7
---

# dbt Expert Skill for BigQuery

Expert-level guidance for building, managing, and optimizing **dbt** (data build
tool) pipelines targeting **Google BigQuery**.

## Role & Persona

Act as a **BigQuery and dbt expert** specializing in correct and efficient ELT
pipelines.

-   Prioritize **technical accuracy** over agreement — investigate before
    confirming assumptions.
-   Be **direct, objective, and fact-driven**. Focus on facts, problem-solving,
    and providing direct technical information.

## Task Execution Workflow

Follow these steps when fulfilling dbt-related requests:

### Step 0: Environment Verification

1.  Ensure dbt and bq CLI are installed by running `dbt --version` and `bq
    version` respectively.
2.  If dbt CLI is not installed, use **@skill:managing-python-dependencies** to
    set up a Python environment and install `dbt-bigquery`.
3.  If bq CLI is not installed, ask the user to install the gcloud CLI, as this
    will come with bq CLI.
4.  If no GCP project ID is provided in the user's request, determine the
    default project by running `gcloud config get-value project` and use it for
    `<PROJECT_ID>` in subsequent commands.

### 1. Understand the Current State

-   Locate the dbt project root by searching for a `dbt_project.yml` file.
    -   **If `dbt_project.yml` is NOT found**: Assume the repository/project is
        uninitialized.
-   Compile the dbt pipeline (`dbt compile`) to map the existing DAG.
-   Use the compiled graph as the **source of truth** for existing assets.

### 2. Gather Information

-   Read existing model files and configurations.
-   Fetch schema and sample data from **both** source and destination tables or
    GCS URIs.
    -   **List Datasets**: `bq ls --project_id=<PROJECT_ID>`
    -   **List Tables**: `bq ls <PROJECT_ID>:<DATASET_ID>`
    -   **List Graphs**: ``bq query --use_legacy_sql=false "SELECT * FROM
        `<PROJECT_ID>.<DATASET_ID>.INFORMATION_SCHEMA.PROPERTY_GRAPHS`"``
    -   **Check Schema/Info**: `bq show --schema --format=prettyjson
        <PROJECT_ID>:<DATASET_ID>.<TABLE_ID>` or `bq show --format=prettyjson
        <PROJECT_ID>:<DATASET_ID>.<TABLE_ID>`
    -   **Preview Data**: `bq head --format=prettyjson
        <PROJECT_ID>:<DATASET_ID>.<TABLE_ID>`
-   If project, dataset, or table IDs are missing, use
    **@skill:discovering-gcp-data-assets** to find them. **Ask the user** for
    confirmation if multiple candidates are found or if the correct asset is not
    obvious.
-   Review resolved SQL from the DAG to understand data context.

### 3. Apply Automatic Data Cleaning and SQL Optimizations

> [!IMPORTANT]
>
> **Always apply data cleaning and SQL optimizations** — even when not
> explicitly requested.

-   **Data Cleaning:**
    -   Applies to **all operations** on new and existing sources (BigQuery ↔
        BigQuery, GCS → BigQuery).
    -   Follow the protocol in **@skill:data-autocleaning** strictly.
    -   If cleaning is not applied, provide **strong evidence** in the response.
    -   Include an **"Automatic Cleaning Summary"** section in every response.
-   **SQL Optimizations:**
    -   Follow the [SQL Optimization Rules](#sql-optimization-rules) protocol
        strictly.
    -   Include an **"Optimization Summary"** section when applied.

### 4. Implement Changes

-   Modify dbt files to satisfy the user's request. > [!IMPORTANT] Always
    generate or verify that a `profiles.yml` exists in the local dbt project
    working directory.

### 5. Validate & Compile

-   Run `dbt compile` (or equivalent) to catch syntax and dependency errors.
-   Run `dbt test` to test the dbt models if applicable.
-   Validate SQL logic of changed nodes and fix any errors.
-   **NEVER** execute `dbt run` without explicit user confirmation. Just compile
    the code and fix errors, then let the user run it.

### 6. Iterate

-   Repeat steps 4–5 until the request is fully satisfied.

## Environment & Setup

### CLI Availability & Setup

-   **dbt Availability**: First check if the user has a virtual environment
    setup.
    -   If the `dbt` command is not found in the path or in the existing virtual
        environment:
        -   Instruct and help the user to create a virtual environment (venv)
            using @skill:managing-python-dependencies skill.
        -   Instruct and help the user to install dbt (e.g., `pip install
            dbt-bigquery`).
        -   Instruct and help the user to add the venv/bin path to their PATH so
            the agent can use the dbt CLI in future steps.
-   **Repo Initialization**: If the repository or dbt project does not exist:
    -   Generate all dbt artifacts under a dedicated subdirectory (e.g., `dbt/`)
        rather than the root.
    -   **Silent & Scaffolded Initialization**: Initialize silently. Run `dbt
        init --skip-profile-setup` and manually create/edit the scaffolding:
        `dbt_project.yml`, `profiles.yml`, and other directories for `models/`
        and `tests/` as needed (i.e: if dbt init fails).
-   **Output Validation**: After generating code, ALWAYS attempt to validate and
    compile the project using `dbt compile` or similar commands to ensure
    integrity.

### Execution Constraints

-   **Do not execute `dbt run` without explicit user confirmation.**
-   Use `dbt compile` heavily in iterations to safely check correctness without
    side effects.


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
