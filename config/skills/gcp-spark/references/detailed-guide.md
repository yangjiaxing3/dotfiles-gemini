# gcp-spark — Detailed Reference & Extended Examples

        ```python
        import logging

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
        ```
    *   **Security & Dynamic Variables**: You MUST NOT hardcode plaintext
        credentials, passwords, or tokens (use Secret Manager — refer to
        `references/jdbc_cloudsql.md` when retrieving credentials from Secret
        Manager). You MUST NOT hardcode environment-specific variables;
        parameterize project IDs, dataset IDs, table names, and bucket paths via
        `os.environ.get(...)` or arguments.
    *   **Read and Write data**: **ALWAYS** load only the connector reference
        file(s) needed for the prompt:
        -   **BigQuery, GCS, or Pub/Sub**: `references/read_write_data.md`
        -   **BigLake Iceberg Catalog**: `references/biglake_iceberg.md`
        -   **Cloud Spanner**: `references/spanner.md`
        -   **JDBC, Cloud SQL (PostgreSQL / MySQL / SQL Server), AlloyDB & Secret Manager**:
            `references/jdbc_cloudsql.md`
        -   **Amazon S3 (`s3a://` / S3-compatible object storage)**:
            `references/aws_s3.md`
        -   **Azure Blob Storage & ADLS Gen2 (`abfss://`, `wasbs://`,
            `wasb://`)**: `references/azure_storage.md`
    *   **Machine Learning Tasks**: Refer to `@skill:ml-best-practices` skill and `references/ml_tasks.md` when generating Machine Learning code.
    *   **Spark Optimizations & Broadcast Joins**: **ALWAYS** refer to
        `references/spark_optimizations.md`. When joining a large DataFrame with
        a small lookup or dimension table, you MUST use `broadcast()` (`from
        pyspark.sql.functions import broadcast`) on the small table. Treat about
        10 MB (Spark's default `spark.sql.autoBroadcastJoinThreshold`) as a
        guide to what counts as small, not a hard limit.
5.  **Verify schema before write**: **ALWAYS** verify that the dataframe and
    destination schema match, use `df.printSchema()` for dataframe schema and
    refer to `@skill:discovering-gcp-data-assets` skill or
    `references/schema_direct_inspection.md` to verify destination schema.
6.  **Compile code before executing**: For notebooks convert them to python
    script using `jupyter nbconvert --to script your-notebook.ipynb` first. Then
    compile the resulting python script using `python3 -m py_compile
    your-script.py`. The same can be done for pyspark source code.
7.  **Execute script or notebook**: When requested to run a job, script,
    session, or execute notebook cells against Managed Spark, refer to
    `references/gcloud_dataproc.md` on how to execute code on Dataproc
    Serverless using Spark Connect or Dataproc jobs.
8.  **Follow up with the user**: If a brand new notebook was generated, instruct the user to select the appropriate kernel in the dropdown for cell execution.

--------------------------------------------------------------------------------

## Common Mistakes Checklist

> [!CAUTION]
>
> Ensure you verify this checklist to avoid mistakes

Before submitting a job, verify:

-   [ ] **All imports present** (`col`, `when`, `lit`, `broadcast`, etc. from
    `pyspark.sql.functions`)
-   [ ] **`vector_to_array` from correct module** use `from pyspark.ml.functions
    import vector_to_array` (NOT `pyspark.sql.functions`)
-   [ ] **DataFrame schema matches target Iceberg table** verify with
    `df.printSchema()` before writing
-   [ ] **CSV files read with `header` and `inferSchema`** without these, the
    header row becomes data and all columns are strings
-   [ ] **Driver memory safety (`toPandas()` / `collect()`)** NEVER call
    `.toPandas()` or `.collect()` on raw or un-aggregated DataFrames. ALWAYS
    perform transformations, aggregations (`groupBy().agg()`), or data reduction
    (`limit()`, `sample()`) in Spark before converting small summaries to Pandas
    for plotting or display.
-   [ ] **No inline pip install in Spark batch/script jobs**: NEVER run pip
    install or subprocess package installations inside PySpark batch scripts
    (the `%pip install` setup cell in generated notebooks is exempt). Pass
    dependencies using --properties=spark.jars.packages=...,
    --archives=gs://.../env.tar.gz#environment, --py-files, or a custom
    --container-image.
-   [ ] **Optimization & Pre-Submission Refactoring** Verify the job against
    `references/spark_optimizations.md` and follow the confirmation protocol in
    `references/spark_refactoring_guide.md`.
-   [ ] **No full file reads of executed notebooks**: You MUST NOT use `read_file` or
    generic full file reading tools on executed `.ipynb` notebooks; they often
    contain massive base64-encoded image outputs that cause excessive token
    consumption. You MUST inspect execution outputs with cell-scoped reading tools
    (such as `notebook__read_cell`, `jupyter__read_cell`, or specific line
    slices).

--------------------------------------------------------------------------------

## IAM Requirements

The Managed Spark (Dataproc) service account needs:

*   `roles/dataproc.worker`: Job execution
*   `roles/biglake.admin`: BigLake Iceberg table management
*   `roles/bigquery.jobUser`: BigQuery query materialization and load jobs
*   `roles/bigquery.dataEditor`: BigQuery table reads and writes (direct and indirect)
*   `roles/bigquery.readSessionUser`: BigQuery Storage Read API session creation
*   `roles/storage.objectUser`: Read/write GCS (data, Iceberg warehouse, and `--deps-bucket` / `temporaryGcsBucket`)
*   `roles/spanner.databaseUser`: Spanner reads and writes
*   `roles/secretmanager.secretAccessor`: Accessing database passwords and credentials stored in Secret Manager

--------------------------------------------------------------------------------

## Spark resource management & observability

Refer to `references/gcloud_dataproc.md` for detailed guidelines on managing
Spark clusters, jobs, batches, interactive sessions, and Spark Connect sessions.

For fleet-wide and multi-region observability — including active workload
inventory across Batches, Sessions, Clusters, and Jobs, failed batch discovery,
Serverless compute consumption (`DCU-Hours` and `Shuffle-GB-Months`), idle or
zombie cluster waste detection, scheduled pipeline cadence health, configuration
auditing, and Cloud Monitoring / Cloud Logging telemetry — use the
`@skill:gcp-spark-observability` skill.

--------------------------------------------------------------------------------

## Code Optimization & Pre-Submission Verification

Before submitting any Spark job or Dataproc batch, enforce the pre-submission
verification protocol in `references/spark_refactoring_guide.md`: inspect the
code for the anti-patterns catalogued in `references/spark_optimizations.md` and
obtain explicit user confirmation before applying refactoring.

--------------------------------------------------------------------------------

## Troubleshooting & Root Cause Analysis

For troubleshooting failed Spark jobs or Dataproc batches, inspecting/tailing
GCS driver output logs, analyzing Spark event logs, or performing Root Cause
Analysis (RCA), use the `@skill:gcp-spark-troubleshooting` skill.
