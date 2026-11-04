# gcp-dataflow — Detailed Reference & Extended Examples

    -   > **Strict parameter validation**: Any parameter in the metadata JSON
    -   > that does **NOT** explicitly have `"isOptional": true` is **strictly
    -   > required** by the Dataflow API.
    -   > This applies even if the description suggests it has a default value
    -   > (e.g., `csvFormat` or `badRecordsOutputTable` in some templates).
    -   > You must identify and supply all of them.
    -   Identify which parameters are provided by the user and which need to be
        resolved or created by you.
        *   **Action**: Present these parameters to the user using Markdown
            Key-Value (bullet points) for clarity and confirmation.
    -   **Schema Handling**: If a schema JSON parameter (like `schemaJSONPath`
        or `JSONPath`) is required:
        *   **Action**: Ask the user to provide the GCS path to an existing
            schema file or the JSON content.
        *   If the user does not have a schema file, ask them to provide the
            field names and their types. Construct the schema JSON locally and
            present it to the user for validation.
        *   Once confirmed by the user, write the schema JSON file locally and
            upload it to a GCS staging location, then supply this path to the
            parameter.
    -   **Pre-create Target Sink (Best Practice)**: To ensure stability and
        avoid runtime creation schema mismatches:
        *   **Action**: Clarify with the user whether the target sink (e.g.,
            BigQuery table, Spanner database/table) already exists. If the user
            confirms it exists, proceed to the remaining steps as-is.
        *   If it does not exist, ask for permission to create it. If permitted,
            create it yourself. Otherwise, provide the exact creation commands
            to the user.
        *   If the sink is BigQuery, refer to
            [Destination-specific prerequisites][dest-prereqs] for crucial table
            and error table setup.
    -   Include additional parameters such as service accounts, network details,
        and other pipeline options.
        *   **Specifying Options**: For Google-provided Flex Templates, refer to
            the [Specifying options for Flex Templates][flex-template-options]
            guide for how to pass parameters and additional experiments.

### Destination-specific prerequisites

Different templates might require specific resources to be prepared in the
target sink before execution. Follow the instructions for your target sink
below.

#### BigQuery

When running templates that write to BigQuery, you MUST ensure the following
resources are prepared to prevent job failures:

-   **Pre-create Target Table**: Create the target BigQuery table (e.g., using
    `bq mk`) before launching the job. Ensure the schema matches the template's
    expectations.
-   **Pre-create Error/Bad Records Table**: Many templates that write to
    BigQuery have a parameter for redirecting failed records (e.g.,
    `badRecordsOutputTable` or `outputDeadletterTable`). Some templates attempt
    to auto-create this table. However, pre-creating it is a best practice. This
    ensures correct schema and permissions.
    *   **How to Determine the Error Schema**: Trace the schema definition in
        the public [DataflowTemplates GitHub repository][df-templates-repo]:
        1.  Locate the source code or README for the template you are using
            (e.g., in `v1/` or `v2/` directories).
        2.  Identify the parameter name used for the error table (e.g.,
            `badRecordsOutputTable` or `outputDeadletterTable`).
        3.  Search the source code to see how the schema is defined or loaded
            for that parameter:
            *   **Example (Code Reference)**: In `PubSubToBigQuery.java`, the
                schema is set using
                `ResourceUtils.getDeadletterTableSchemaJson()`. Tracing
                `ResourceUtils.java` shows it loads the schema from
                [streaming_source_deadletter_table_schema.json on GitHub][deadletter-schema].
            *   **Example (Documentation Reference)**: For simpler templates,
                the schema might be listed in the official documentation, such
                as the `RawContent`/`ErrorMsg` schema shown in the
                [CSV to BigQuery DevSite Doc][csv-bq-doc].

## Configuring Custom Pipelines (Dataflow Runner)

Use this section when preparing to run a custom Apache Beam pipeline on
Dataflow.

-   When launching Python Pipelines without a Flex Template with
    `DataflowRunner`, you MUST scan the pipeline project directory for the
    following files:
    -   **`requirements.txt`**:
        -   If found, you MUST include `--requirements_file` pipeline option.
    -   **`setup.py`**:
        -   If found, you MUST include `--setup_file` pipeline option. This is
            critical if the pipeline uses local modules or packages.

-   When launching Python Pipelines with a Flex Template, if the Flex Template
    image is also the SDK Container image (Single Docker Image Configuration),
    then you MUST supply the image in the `sdk_container_image` parameter.

### Lookup environment resources instead of using placeholder values

-   Avoid using generic placeholders (e.g., `your-gcp-project-id`) for GCP
    resources when drafting run scripts or configs. **Action**: If values are
    unknown, proactively run commands like `gcloud config get-value project` to
    find active resources to pre-fill scripts for the user. Confirm the values
    with the user before proceeding.

## Job Execution

Use this section when configuration is complete and you are ready to launch any
Dataflow job (Google-provided template, Custom Flex template, or standalone
pipeline).

### Universal Execution Workflow

1.  **Construct Launch Command**: Draft the full launch command based on the
    pipeline type (e.g., `gcloud dataflow flex-template run` or `python main.py
    --runner=DataflowRunner`). Ensure workers default to private IP
    configuration unless specified otherwise, and verify target project
    permissions.
2.  **Mandatory Pre-Launch Confirmation**: Present the *entire* drafted command
    to the user at once. Explain the purpose of all parameters (including
    experimental flags) and allow the user to review and correct the command as
    a batch instead of confirming piecemeal. **Do NOT proceed** with execution
    until explicitly approved.
3.  **Trigger Job**: Once approved, execute the command and note the resulting
    Job ID (displaying it to the user).
4.  **Display Console URL**: Construct and present the direct Cloud Console
    monitoring URL:
    https://console.cloud.google.com/dataflow/jobs/<region>/<job_id>?project=<project_id>

## Job Monitoring

Use this section to monitor the progress of a running Dataflow job.

-   Check the status of the triggered Dataflow job using the job ID.
-   Run the check every 30 seconds for the first 2 minutes, then check every 3
    minutes, unless specified otherwise by the user.
-   **Note**: Do NOT perform data check queries on the sink until the job has
    reached a stable `RUNNING` or `DONE` state.

## Diagnostics & Troubleshooting

> [!IMPORTANT] YOU MUST use this section when the user asks about performance of
> their Dataflow pipelines. This can be used to debug issues like pipeline
> slowness, pipeline failures, etc.

### Task Execution Workflow

1.  **Understand User Request**: Extract Job ID, Project ID, Transform Name
    (optional), and Time Window.
2.  **Transform Name Mapping**: If the user requires transform-based debugging,
    map user-provided Transform Names to actual Dataflow `stage` or `ptransform`
    and apply to filters while querying:

    This mapping can be extracted from `gcloud dataflow jobs describe JOB_ID
    --full --format="json(pipelineDescription.executionPipelineStage)"`.

    1.  **Extract the targets**:
        *   Get stage_id: **`name`** property at the parent stage level. This
            matches `"F[digit]"` (e.g. `"F6"`).
        *   Get ptransform: inside the `componentTransform` array, read
            precisely from **`userName`** or **`originalTransform`** (e.g.
            `"RateLimitAndLog/ParMultiDo(RateLimitAndLog)"`). and use it as
            **`ptransform`**.
    2.  **Apply the filters strictly following mapping mechanics**:
        *   **For Cloud Logging queries**: Apply extracted ptransform name to
            filter `resource.labels.step_id="[Extracted ptransform name]"`.
        *   **For Monitoring queries**: Use the stage_id/ptransform filters
            based on filters supported by metric:
            `metric.labels.ptransform="[Extracted ptransform name]"` or
            `metric.labels.stage="[Extracted stage_id]"`.

3.  **Query Telemetry**:

    *   Use Dataflow REST API to get High level Job Messages/Events that
        happened in the job.
    *   Refer to [dataflow_diagnostics_reference.md][diag-ref] for
        key metrics and logging query patterns based on Job Type.
    *   Use Monitoring REST API to fetch metrics.
    *   Use GCloud Logging command to fetch logs.
    *   Use Dataflow REST API to fetch current snapshot metrics when historical
        time-series are not needed.

4.  **Analysis**:

    *   For Streaming Jobs
        *   Overall Job Health: YOU MUST refer to
            [streaming_job_health](references/streaming_job_health.md) to analyze
            overall streaming job health.
        *   Analyze Bottlenecks and Parallelism. YOU MUST refer to
            [bottlenecks_and_parallelism_context][bottlenecks-context] and
            interpret the bottlenecks and parallelism metrics in that context.
        *   Analyze Autoscaling Behavior. YOU MUST refer to
            [streaming_horizontal_autoscaling_analysis.md][autoscaling-analysis-link]
    *   For Batch Jobs
        *   Correlate metrics spikes/drops with log errors.
        *   Identify Issues.

5.  **Output**: Provide a synthesized diagnosis containing symptoms, root
    causes, and target code links (using `file:///...` format). Refer to
    [reporting_findings.md][reporting-findings] for report structure, evidence
    standards, and verification guidelines. Strictly follow the appropriate
    response structure for the job type:

    **For Streaming Jobs:**

    1.  **Overall Job State**: State categorization (Healthy, Mostly Healthy,
        Not Healthy) per
        [streaming_job_health](references/streaming_job_health.md).
    2.  **High-level Job Events**: Notable control plane events, errors, or
        stage failures parsed from job messages.
    3.  **Data Freshness**: Current data delay utilizing
        `job/data_watermark_age` / `job/per_stage_data_watermark_age` and system
        lag.
    4.  **Throughput**: Processing rate trends utilizing
        `job/elements_produced_count` / `job/estimated_bytes_produced_count`.
    5.  **Backlog**: Input backlog (if source stage) or inter-stage backlog
        using `job/estimated_backlog_processing_time` / `job/backlog_bytes`.
    6.  **Bottlenecks & Parallelism**: Queue delay diagnostics using
        `job/is_bottleneck` (interpreting `likely_cause` / `bottleneck_kind`)
        and key metrics `job/backlogged_keys` /
        `job/processing_parallelism_keys` interpreted in the context of
        [bottlenecks_and_parallelism_context][bottlenecks-context].
    7.  **Autoscaling Analysis**: Scaling trends using
        `job/horizontal_worker_scaling` (and label `rationale`), clamp limits
        (`job/max_worker_instances_limit` / `job/min_worker_instances_limit`),
        and utilization hints in the context of
        [streaming_horizontal_autoscaling_analysis][autoscaling-analysis-link].
    8.  **Recommendations**: Direct remediation plans (in-flight updates,
        client-side configurations, or code corrections linked via absolute
        `file:///` URIs).

    **For Batch Jobs:**

    1.  **High-level Job Events**: Notable control plane events, errors, or
        stage failures parsed from job messages.
    2.  **Throughput**: Processing rate trends utilizing
        `job/elements_produced_count` (primary performance indicator).
    3.  **Recommendations**: Direct remediation plans to future runs
        (client-side configurations, or code corrections linked via absolute
        `file:///` URIs).

[py-flex-ref]: references/python_flex_template_reference.md
[udf-guide]: https://docs.cloud.google.com/dataflow/docs/guides/templates/create-template-udf
[ssl-cert-guide]: https://docs.cloud.google.com/dataflow/docs/guides/templates/ssl-certificates
[dest-prereqs]: #destination-specific-prerequisites
[flex-template-options]: https://docs.cloud.google.com/dataflow/docs/guides/templates/run-flex-templates#specify-options
[df-templates-repo]: https://github.com/GoogleCloudPlatform/DataflowTemplates
[deadletter-schema]: https://github.com/GoogleCloudPlatform/DataflowTemplates/blob/main/v2/common/src/main/resources/schema/streaming_source_deadletter_table_schema.json
[csv-bq-doc]: https://cloud.google.com/dataflow/docs/guides/templates/provided/cloud-storage-csv-to-bigquery#GcsCSVToBigQueryBadRecordsSchema
[diag-ref]: references/dataflow_diagnostics_reference.md
[bottlenecks-context]: references/bottlenecks_and_parallelism_context.md
[autoscaling-analysis-link]: references/streaming_horizontal_autoscaling_analysis.md
[reporting-findings]: references/reporting_findings.md
