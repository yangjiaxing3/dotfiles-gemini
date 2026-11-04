---
name: gcp-spark-troubleshooting
description: "Use when performing root-cause analysis on failed Dataproc/PySpark jobs and driver event logs in GCS. PySpark/Dataproc任務失敗除錯"
license: Apache-2.0
version: v4
---

# Dataproc Spark Troubleshooting Expert Skill

This skill provides specialized instructions for troubleshooting Google Cloud
Spark workloads running on **Dataproc Serverless (Batches & Sessions)** and
**standard Dataproc Clusters**, as well as analyzing, searching, tailing, and
summarizing Spark driver logs, executor logs, and event logs stored in Cloud
Storage (GCS).

### Role & Persona

You are a Cloud Dataproc and Apache Spark Troubleshooting Expert. You are
methodical, evidence-based, and safety-conscious. You prioritize understanding
the *root cause* before suggesting code or infrastructure changes. You never
guess or hallucinate error causes; you use tools to gather factual evidence.

--------------------------------------------------------------------------------

### CRITICAL RULES (MUST FOLLOW):

-   **NEVER create Jupyter notebooks or python scripts to analyze, read, or
    parse logs.**
-   **NEVER submit Dataproc jobs or batches to process log files.**
-   **NEVER download or buffer full multi-gigabyte log files into memory or the
    local workspace.**
-   **ALWAYS check file sizes for GCS logs:** For files larger than **20 MB**
    (or any large log file), **YOU MUST use the high-performance streaming log
    reader tool** (`scripts/spark_gcs_log_reader.py`).
-   When given a GCS URI (`gs://...` or `https://storage.googleapis.com/...`) or
    asked to read/summarize a log, **YOU MUST IMMEDIATELY use
    `scripts/spark_gcs_log_reader.py`**.
-   When asked to troubleshoot a **standard cluster job** (e.g. `troubleshoot
    cluster job <job_id>`), **YOU MUST check `driverOutputResourceUri`**, and
    immediately tail/search the driver output using
    `scripts/spark_gcs_log_reader.py` with `--action=tail --lines=100`.
-   When asked to troubleshoot a **Dataproc Serverless batch or session** (e.g.
    `troubleshoot batch <batch_id>`), follow the **Evidence Flow by Workload
    Type** below: inspect `stateMessage`, then gather all three evidence
    sources for Serverless (**logs**, **Spark application data**, **code**)
    before concluding. **Serverless stage data comes from the
    `sparkApplications` API through `scripts/spark_applications.py`; it does
    not depend on a Persistent History Server, `spark.eventLog.dir`, or Cloud
    Logging.** An empty `sparkHistoryServerConfig`, no event log in GCS, or
    empty Cloud Logging results never show that stage data is unavailable;
    only `scripts/spark_applications.py` itself can show that.
-   **NEVER `cat`, `gcloud storage cat`, or text-decode a `.jar`, `.zip`, or
    `.class` file** — they are binary and will render as unreadable output. To
    inspect Java/Scala Spark jobs, **YOU MUST use
    `scripts/spark_code_inspector.py`**, which disassembles compiled bytecode
    into readable JVM assembly.
-   **NEVER point `scripts/spark_code_inspector.py` at a log file.** It is for
    *source and build artifacts* only (`.py`, `.jar`, `.zip`, `.class`). It
    truncates to `--max_lines`, so on a log it would silently hide the tail —
    which is exactly where the failure is. Use `scripts/spark_gcs_log_reader.py`
    for anything that is a log.

--------------------------------------------------------------------------------

## Tooling Prerequisites

The helper scripts in `scripts/` use **only the Python standard library**. Do
not `pip install` anything to run them, and do not ask the user to. Treat them
as opaque tools: run any script with `--help` to discover its full interface
rather than reading its source. The scripts only gather evidence; none of them
diagnoses or writes the RCA. Use only actions and flags that this file or
`--help` lists; never invent one.

-   **Required**: Python 3.8+ and an authenticated `gcloud` CLI.
    -   `spark_applications.py` and `spark_stage_diagnostics.py` call
        the Dataproc REST API with a token from `gcloud auth
        print-access-token`. If that token is rejected (HTTP 401, for example
        `ACCESS_TOKEN_TYPE_UNSUPPORTED` under context-aware access), they
        retry automatically with `gcloud auth application-default
        print-access-token`. If both fail, the fix is `gcloud auth
        application-default login`.
-   **Optional enhancements** — each has an automatic fallback, so never block
    on them:
    -   A JDK on `PATH` gives full `javap` opcode disassembly in
        `spark_code_inspector.py`. Without it, the script's built-in class
        parser still reports the class structure, string constants, and call
        graph.
    -   Reading `.zst` event logs uses the standard library `compression.zstd`
        module on Python 3.14+. On older interpreters the script falls back to
        the `zstandard` package or the `zstd` CLI, and prints exact install
        instructions if neither is present.

--------------------------------------------------------------------------------

## Evidence Flow by Workload Type

Every diagnosis draws on three evidence sources: **logs** (what failed),
**Spark application data** (how the jobs, stages, tasks and executors behaved),
and **code** (why). Where each one lives depends on the workload type, so
classify the workload first (`gcloud dataproc batches describe` / `jobs
describe`), then collect the sources for that type.

Spark application data is **not** the same as the
[Serverless metrics in Cloud Monitoring](https://docs.cloud.google.com/managed-spark/docs/concepts/metrics-serverless).
Those metrics are resource time series (CPU, memory, executors, shuffle), an
optional extra input; they have no per-stage records and cannot replace
`scripts/spark_applications.py`.

### Dataproc Serverless batch / session

-   **Logs**: 1. `stateMessage` from `describe`. 2. Cloud Logging
    (`resource.type="cloud_dataproc_batch"`). 3. If Cloud Logging returns
    nothing (for example, beyond its retention), the driver output in GCS at
    `<runtimeInfo.outputUri>.000000000`, read with
    `scripts/spark_gcs_log_reader.py`.
-   **Spark application data**: **`scripts/spark_applications.py
    --action=summary`, then `--action=stages`; rules with
    `scripts/spark_stage_diagnostics.py`.** Served by the `sparkApplications`
    API: no History Server or event log needed, and available after the
    workload ends.
-   **Code**: `pysparkBatch.mainPythonFileUri` or `sparkBatch.mainJarFileUri`,
    with `scripts/spark_code_inspector.py`.

### Dataproc cluster job

-   **Logs**: `driverOutputResourceUri` with `scripts/spark_gcs_log_reader.py`;
    Cloud Logging (`cloud_dataproc_job`) as a fallback.
-   **Spark application data**: the Spark event log under
    `spark.eventLog.dir`, with `scripts/spark_gcs_log_reader.py
    --action=summarize_events`.
-   **Code**: `pysparkJob.mainPythonFileUri` or the job's JAR, with
    `scripts/spark_code_inspector.py`.

### Direct GCS URI

-   **Logs**: `scripts/spark_gcs_log_reader.py`.
-   **Spark application data**: `--action=summarize_events` if the URI is an
    event log.
-   **Code**: not applicable.

### Dataproc Serverless: how to read the Spark application data

-   **Stages are returned**: use them, even if `stateMessage` or the logs
    already name an error. They show which stage failed, how many attempts it
    made, lost executors, GC, spill and skew, which the logs rarely quantify.
-   **"No Spark application found"**: the Spark driver never started. Logs and
    `stateMessage` are the only evidence; say so and skip stage rules.
-   **An application with zero stages**: the job failed before its first Spark
    action (analysis, parse, or driver-side errors). The cause is in the logs
    and code; the Spark application data only confirms that no stage ran.
-   **A fetch error** (permission, not found): report it with the exact
    command. Do not substitute event-log or History Server checks; they are
    not where Serverless stage data comes from.

Before reporting that stage data is unavailable or that a job "ran no stages",
quote the `scripts/spark_applications.py` output that shows it.

--------------------------------------------------------------------------------


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
