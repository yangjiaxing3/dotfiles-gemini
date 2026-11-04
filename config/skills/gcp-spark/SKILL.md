---
name: gcp-spark
description: "Use when authoring or optimizing PySpark/Spark SQL workloads on Dataproc Serverless or Managed Spark clusters. GCP PySpark/Dataproc巨量資料處理"
license: Apache-2.0
version: v31
---

# Managed Spark on Google Cloud

> [!IMPORTANT]
>
> You MUST follow the Task Execution Workflow when writing spark code.

## Notebook Generation Environment Rules

> [!CAUTION]
>
> When the task is to **generate** a Spark notebook (as opposed to executing
> one), you **MUST NOT** modify your own local execution environment (i.e. do
> not run these commands with your shell or other tools). Specifically:
>
> -   **NEVER create a virtual environment** (`python -m venv`, `virtualenv`,
>     `conda create`, `uv venv`, `poetry init/install`, etc.).
> -   **NEVER install packages** (`pip install`, `%pip install`, `uv pip
>     install`, `conda install`, `poetry add`).
> -   **NEVER run environment discovery loops** such as activating a venv,
>     `pip list`, or probing for `ipykernel` / `google-cloud-spark-connect` as a
>     precondition for writing the notebook.
>
> Assume the user will select the appropriate
> kernel and dependencies after the notebook is generated.

## Task Execution Workflow

1.  **Understand user request**:

    -   When asked to generate a new spark notebook you **MUST** clarify with
        the user which kernel type will be used: "Local Python" (Spark Connect)
        or "Remote Spark" where the Spark session (`spark` variable) is
        automatically initialized. If the user selects "Local Python", you MUST
        additionally clarify which dataprocSessionConfig should be used (scan
        for existing serverless session templates), and **MUST** initialize the
        session with `ManagedSparkSession` by adding the following cells to the
        notebook:
        ```python
        from google.cloud.dataproc_v1 import Session
        # requires google-cloud-spark-connect pypi package for execution
        from google.cloud.managed_spark_connect import ManagedSparkSession

        session_config = Session()
        session_config.session_template = (
            "projects/<PROJECT_ID>/locations/<REGION>/sessionTemplates/<TEMPLATE_ID>"
        )
        spark = (
            ManagedSparkSession.builder.projectId("<PROJECT_ID>")
            .location("<REGION>")
            .dataprocSessionConfig(session_config)
            .getOrCreate()
        )
        ```
2.  **Understand schemas**: **ALWAYS** use `@skill:discovering-gcp-data-assets`
    skill or `references/schema_direct_inspection.md` to understand input and
    output schemas. Include the schema in your thought process BEFORE generating
    any code. Do NOT guess column names. Cap GCP data asset discovery attempts
    at **3 retries max**. Unless explicitly specified, assume
    that the assets are located in the same project. Avoid scanning for assets
    across other projects as it can take a long time. If an expected dataset or
    table does not exist, use `@skill:discovering-gcp-data-assets` to discover
    all similar tables in the namespace or project.

    *MISSING SOURCE RULE*: If the request does not name a table, GCS path or
    catalog, you MUST run at most ONE `@skill:discovering-gcp-data-assets`
    search. If it does not return a single clear match, you MUST list the
    candidates, ask the user which source to use, and STOP. You MUST NOT infer
    the source by listing buckets, reading existing notebooks or scripts, or
    running `SHOW NAMESPACES` / `SHOW TABLES`.

    *MINOR TYPO RULE*: If there is a minor typo (e.g. `employees` vs
    `employee`), you can fix the error and proceed.

    *STRICT HALT RULE*: If the discovered table names differ from the requested
    table by more than a minor typo (e.g. completely different words, prefixes,
    or suffixes), you must IMMEDIATELY report the missing table and a neutral
    list of all available alternatives in the same namespace to the user without
    making any recommendations. You MUST ask the user which alternative to use
    and then STOP EXECUTING your turn. Do NOT write any Spark code or notebooks.
    Do NOT proceed with code generation, do NOT add fallback logic to code, and
    do NOT automatically substitute any alternative table (even if its schema
    seems to match) without explicit user permission.
3.  **Verify source accessibility**: For Google Cloud Storage (`gs://`) paths,
    verify access/existence using `gcloud storage ls gs://<path-to-dataset>`
    (skip `gcloud storage ls` for external cloud URIs such as `s3a://`,
    `abfss://`, `wasbs://`, or `wasb://`, which are accessed directly by Spark's
    Hadoop FileSystem connectors). If accessing or reading a GCS path fails
    with a storage error e.g., permission errors like `403
    Forbidden`/`Forbidden`/`PermissionDenied`, or location errors like `404 Not
    Found`/`NotFound`/`FileNotFoundException` you should report the error
    immediately. Either (1) ask the user what to do next, or (2) if asked to
    execute a notebook, save the notebook with the error output and recommend
    next steps to resolve the issue. Do NOT scan all buckets for alternative
    fallback datasets when encountering GCS errors.
4.  **Generate spark code**:

    *   **Output Format**: **ALWAYS** generate code in **Python Notebooks
        (.ipynb)** format. Generate scripts (.py) only if explicitly requested.
    *   **Spark Session Initialization**:

        > [!IMPORTANT] Initializing a Spark session on Google Cloud can take 2-3
        > minutes. You MUST inform the user about the potential delay.

        > [!CAUTION] You **MUST NOT** create a local Spark session. The
        > following are **BANNED**: - `SparkSession.builder.master("local")` -
        > `pyspark.sql.SparkSession.builder.getOrCreate()` in notebooks or local
        > Spark Connect scripts - Any `try/except` fallbacks that revert to a
        > local `SparkSession`.
        >
        > - **Remote Kernel Notebooks (`.ipynb`)**: `spark` is pre-initialized;
        >   use it directly without calling `ManagedSparkSession` or
        >   `SparkSession.builder.getOrCreate()`.
        > - **Local Python Notebooks (`.ipynb`) & Spark Connect scripts**: You
        >   **MUST** use `ManagedSparkSession` from `google-cloud-spark-connect`
        >   to connect to **Managed Spark Serverless**.
        > - **Dataproc Batch & Cluster jobs (`.py` submitted via `gcloud dataproc batches submit pyspark` or `gcloud dataproc jobs submit pyspark`)**:
        >   Use standard `SparkSession.builder.appName("<APP_NAME>").getOrCreate()`
        >   (never `.master("local")`).

        Refer to `references/gcloud_dataproc.md` for detailed configuration.
        Minimal initialization for **Local Python** notebooks / Spark Connect:

        ```python
        from google.cloud.managed_spark_connect import ManagedSparkSession

        spark = (
            ManagedSparkSession.builder.projectId("<PROJECT_ID>")
            .location("<REGION>")
            .getOrCreate()
        )
        ```
    *   **Production Logging**: In standalone
        production PySpark batch jobs and scripts (`.py`), you MUST use the
        standard Python `logging` module instead of `print()` statements for job
        lifecycle, progress, and record counts. Do **NOT** use the `logging`
        module in notebooks (`.ipynb`); use `print()`, `.show()`, and standard
        cell outputs instead. Configure `logging` for `.py` scripts with
        timestamps:


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
