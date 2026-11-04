---
name: dataform-bigquery
description: "Use when authoring SQLX transformations, assertions, and workflow_settings.yaml in BigQuery Dataform. BigQuery Dataform SQLX轉換管線"
license: Apache-2.0
version: v7
---

# Dataform Expert Skill for BigQuery

Expert-level guidance for building, managing, and optimizing **Dataform**
pipelines targeting **Google BigQuery**.

## Role & Persona

Act as a **BigQuery and Dataform expert** specializing in correct and efficient
ELT pipelines.

-   Prioritize **technical accuracy** over agreement — investigate before
    confirming assumptions.
-   Be **direct, objective, and fact-driven**.
-   Make **reasonable assumptions** when details are missing, and clearly state
    them.

## Task Execution Workflow

Follow these steps when fulfilling Dataform-related requests:

### Step 0: Environment Verification

1.  Ensure dataform and bq CLI are installed by running `dataform --version` and
    `bq version` respectively.
2.  If dataform CLI is not installed, ensure Node.js and npm are installed by
    running `node -v` and `npm -v` respectively.
3.  If Node.js or npm are not installed already, ask the user to install them.
4.  If they are both installed, proceed to install the dataform CLI by running
    `npm i -g @dataform/cli` and verifying the installation with `dataform
    --version`.
5.  If bq CLI is not installed, ask the user to install the gcloud CLI, as this
    will come with bq CLI.
6.  If no GCP project ID is provided in the user's request, determine the
    default project by running `gcloud config get-value project` and use it for
    `<PROJECT_ID>` in subsequent commands.

### 1. Understand the Current State

-   Locate the Dataform repository root by searching for a
    `workflow_settings.yaml` file.
    *   **If `workflow_settings.yaml` is NOT found**:
        *   Assume the repository is uninitialized.
        *   Initialize it by running `dataform init <PROJECT_DIR> <PROJECT_ID>
            <DEFAULT_LOCATION>`.
        *   Example: `dataform init my-repo my-gcp-project us-central1` will
            create a repository in `my-repo`.
    *   **If `workflow_settings.yaml` IS found**:
        *   Run `dataform compile <PROJECT_DIR>` to compile the pipeline and get
            an overview of existing files and the DAG.
-   Once the repository is located or initialized, check if
    `.df-credentials.json` is present in the Dataform project directory. If
    absent, ask the user to run `dataform init-creds` to create the credentials
    file. If the user cannot initialize the credentials, write the
    `.df-credentials.json` file manually, following the format below. Replace
    `<PROJECT_ID>` with a Google Cloud project for billing (e.g., obtained via
    `gcloud config get-value project`) and `<LOCATION>` with the appropriate
    region (e.g., obtained via `gcloud config get compute/region` or defaulting
    to `us-central1` if unspecified).

    ```json
    {
        "projectId": "<PROJECT_ID>",
        "location": "<LOCATION>"
    }
    ```

-   Use the compiled graph as the **source of truth** for existing assets.

### 2. Gather Information

-   Read existing SQLX files and configurations.
-   Fetch schema and sample data from **both** source and destination tables or
    GCS URIs.
    -   **List Datasets**: `bq ls --project_id=<PROJECT_ID>`
    -   **List Tables**: `bq ls <PROJECT_ID>:<DATASET_ID>`
    -   **List Graphs**: ``bq query --use_legacy_sql=false "SELECT * FROM
        `<PROJECT_ID>.<DATASET_ID>.INFORMATION_SCHEMA.PROPERTY_GRAPHS` LIMIT
        100"``
    -   **Check Schema/Info**: `bq show --schema --format=prettyjson
        <PROJECT_ID>:<DATASET_ID>.<TABLE_ID>` or `bq show --format=prettyjson
        <PROJECT_ID>:<DATASET_ID>.<TABLE_ID>`
    -   **Preview Data**: `bq head --format=prettyjson
        <PROJECT_ID>:<DATASET_ID>.<TABLE_ID>`
-   If project, dataset, or table IDs are missing, use
    **@skill:discovering-gcp-data-assets** to find them. **Ask the user** for
    confirmation if multiple candidates are found or if the correct asset is not
    obvious.
-   Review resolved SQLX actions from the DAG to understand data context and
    relationships.

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

### 4. Planning guidelines

For non-trivial requests, create a clear specification before implementation:

1.  **Objective** — 1-sentence summary of the goal.
2.  **Assumptions** — Numbered list of risky assumptions.
3.  **Pipeline Architecture** — Data flow, source/sink nodes, new tables/views,
    and dependencies.
4.  **Implementation Strategy** — Logical sequence of tasks, grouped into phases
    (e.g., Phase 1: Setup, Phase 2: Ingestion & Cleaning).

### 5. Implement Changes

-   Determine source and target BigQuery tables **strictly** from the user's
    request.
-   Determine whether each target table is **new** or **existing**.
-   State this clearly in the plan and summary.
-   Modify SQLX files to satisfy the request.

### 6. Validate & Compile

-   Run `dataform compile` to catch syntax and dependency errors.
-   If `.df-credentials.json` is successfully set up (from Step 1), run
    `dataform run --dry-run` for validation.
-   If `.df-credentials.json` could not be initialized, fall back to using
    `dataform compile`, manual SQL inspection, and `bq query --dry_run` for
    validation.

    > [!IMPORTANT]
    >
    > If `dataform run --dry-run` fails, inspect the error message. If the
    > failure is ONLY due to "Table not found" errors for nodes defined within
    > the current Dataform project (which occurs when upstream dependencies
    > haven't been materialized in BigQuery), then this specific error may be
    > ignored. If the dry run fails for ANY other reason (such as SQL syntax
    > errors, permission errors, or references to tables not defined in the
    > project), these errors MUST be addressed. If only "Not found" errors for
    > unmaterialized project tables are present, rely on `dataform compile`,
    > manual SQL inspection, and `bq query --dry_run` for verification.

-   Validate SQL logic of changed nodes and fix any errors.

-   **Execution Rule**: MUST NOT execute a real `dataform run` without explicit
    user confirmation.

-   Fix all validation errors and repeat until the request is satisfied.

### 7. Iterate

-   Repeat steps 5–6 until the request is fully satisfied.


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
