# gcp-pipeline-orchestration — Detailed Reference & Extended Examples

    >
    > Running the command without `--format=yaml` provides a clear, tabular
    > output that is easier to read.

-   Then use the returned dataproc list with details to create the orchestration
    pipeline definition file based on the user's requirements for the pipeline's
    logic and schedule. **IMPORTANT:** Every schedule **must** include an
    `endTime`. Every schedule **must** use the current date as `startTime` if
    the user hasn't specified.

    > [!IMPORTANT]
    >
    > A Composer environment is not a Dataproc cluster. If no Dataproc clusters
    > are available, do not use a Composer environment for the
    > `sparkHistoryServerConfig`. It is better to omit this configuration if a
    > dedicated Spark History Server is not available.

-   **Python Actions (`python`)**:
    -   Check the content of the Python script to determine if it is a Spark
        job. If it is, use `pyspark` action instead of `python`.
    -   **Environment & Dependencies**: The `environment` field on a `python`
        action is **optional**.
        -   When `environment` or `requirements` is **omitted**, the action runs
            as a standard `PythonOperator` directly in the Airflow worker's host
            environment (using pre-installed Composer packages). Do **not**
            add `environment.requirements` unnecessarily when standard
            libraries or existing Composer packages are sufficient.
        -   Only specify `environment.requirements` (via `path: requirements.txt`
            or `inline: { list: [...] }`) when custom, isolated third-party
            packages not available in Composer are needed. This compiles to
            `PythonVirtualenvOperator` to create an isolated virtual
            environment.

-   **SQL Actions (`sql`)**:
    -   **BigQuery Dataset Location**: When creating a `sql` action with the `bigquery` engine, you **must inspect the location of any referenced BigQuery
        datasets** (e.g., whether it is multi-region `US`/`EU` or a specific region
        like `us-central1`).
        Run:

        ```
        # Replace <PROJECT_ID> and <DATASET_ID> with the actual project and dataset ID
        bq show --format=prettyjson <PROJECT_ID>:<DATASET_ID>
        ```

        Extract the `location` field (e.g., `US`, `EU`, `us-central1`) and set
        `actions[].sql.engine.bigquery.location: <LOCATION>` (or
        `actions[].dataIngestion.bigqueryDts.location: <LOCATION>`). Do NOT omit the
        location or assume `defaults.location` matches the BigQuery dataset
        location.
    -   **BigQuery vs Dataproc Query Syntax**:
        -   **For BigQuery (`engine.bigquery`)**: Specify the output table via
            `destinationTable: project.dataset.table_name`. The query
            (`query.inline` or `query.path`) must be a standard **`SELECT`**
            query without DDL/DML statements (do **not** use `CREATE TABLE`,
            `CREATE OR REPLACE TABLE`, or `INSERT INTO` as BigQuery will fail).
        -   **For Dataproc (`engine.dataprocServerless` / `engine.dataprocOnGce`)**:
            Dataproc engines do not support `destinationTable`; include DDL/DML
            statements (`CREATE TABLE ... AS SELECT ...` or `INSERT OVERWRITE`)
            directly in the SQL query text to materialize output tables.

-   **AI / Vertex AI Actions (`ai`)**:
    -   **Scope & Capabilities**: `agentPlatform` (`Vertex AI`) supports
        `modelUpload` (register a trained model), `batchInference` (batch
        predictions) and `createAndRunCustomJob` (run a Vertex AI `CustomJob`,
        e.g. containerized training). Spark-based training is executed in a
        `pyspark` action.
    -   **Custom Job (`agentPlatform.createAndRunCustomJob`)**: follow the
        `run_vertex_custom_job` example and reminder 7 in
        `references/orchestration-pipelines-schema.md`.

        > [!IMPORTANT]
        > Custom Jobs (`agentPlatform.createAndRunCustomJob`) REQUIRE a Composer environment with Airflow 2.11+ or 3.x.
    -   **Model Export Signature for Batch Prediction**: When creating a custom
        training pipeline in PySpark followed by a Agent Platform
        batch inference action (`agentPlatform.batchInference`) reading from
        BigQuery:
        -  Agent Platform Batch Prediction passes input instances wrapped in a key
            named `"instances"` (e.g., `{"instances": [...]}`).
        -   Standard TensorFlow / Keras models exported with default
            `model.save()` name their input signature after layer names (e.g.,
            `dense_input`), which causes Agent Platform batch prediction jobs to
            fail with input signature mismatch errors.
        -   You **must export the model with an explicit serving signature**
            expecting `instances` as the input name and returning a dictionary
            with `"prediction"`:

            ```python
            class ExportModel(tf.Module):

              def __init__(self, model):
                super().__init__()
                self.model = model

              @tf.function(
                  input_signature=[
                      tf.TensorSpec(
                          shape=[None, num_features],
                          dtype=tf.float32,
                          name="instances",
                      )
                  ]
              )
              def __call__(self, instances):
                predictions = self.model(instances)
                return {"prediction": predictions}


            tf.saved_model.save(
                ExportModel(model),
                export_path,
                signatures={"serving_default": ExportModel(model).__call__},
            )
            ```

    -   **Consuming Batch Prediction Outputs in Downstream Actions (dbt / SQL)**:
        -   When Vertex AI writes batch predictions to BigQuery, regression or
            single-value scalar predictions are serialized as scalar columns
            (e.g., `STRING` or `FLOAT64`), **not** arrays (`REPEATED`).
        -   Do **not** use array offset syntax (such as
            `prediction[OFFSET(0)]`) when querying scalar prediction results in
            downstream dbt models or BigQuery SQL actions, as this causes type
            mismatch errors.
        -   Instead, access the scalar column directly using
            `SAFE_CAST(prediction AS FLOAT64)`:

            ```sql
            SELECT
              id,
              SAFE_CAST(prediction AS FLOAT64) AS predicted_value,
              actual_value
            FROM {{ source('vertex_ai_predictions', 'batch_predictions') }}
            ```

-   **Pipeline Notifications (`notifications`)**: This block is **optional**.
    Configure top-level email notifications under
    `notifications.onPipelineSuccess.email` and
    `notifications.onPipelineFailure.email` (each a list of email strings).

-   Before creating or updating the `deployment.yaml` file, you **must** first
    run the following command to get the list of available Composer environments
    for the user's project.

    ```
    # Replace <PROJECT_ID> with the actual project_id
    # Replace <REGION> with the actual region
    gcloud composer environments list \
    --project <PROJECT_ID> \
    --locations <REGION> \
    ```

    After listing available Composer environments, you **must** check each
    environment to ensure the composer is using the right image version or has
    installed right PyPI packages. Run the following command for each
    environment:

    ```
    # Replace <ENVIRONMENT_NAME> with the Composer environment name
    # Replace <REGION> with the region
    gcloud composer environments describe <ENVIRONMENT_NAME> \
    --location <REGION> \
    --format="json(config.softwareConfig.imageVersion, config.softwareConfig.pypiPackages)"
    ```

    From the output, select an environment where the `imageVersion` value is one
    of `composer-3-airflow-3.1.7-build.x`, `composer-3-airflow-2.11.1-build.x`,
    `composer-3-airflow-2.10.5-build.x`, `composer-3-airflow-2.9.3-build.x`,
    `composer-2.16.11-airflow-2.11.1`, `composer-2.16.11-airflow-2.10.5`, or
    `composer-2.16.11-airflow-2.9.3`, or select an environment
    where `orchestration-pipelines` package is listed in the PyPI
    packages. This ensures the selected environment is compatible with
    orchestration pipelines. Pipelines with an
    `agentPlatform.createAndRunCustomJob` action MUST use an Airflow 2.11+ or
    3.x image (e.g. `composer-3-airflow-3.1.7-build.x`,
    `composer-3-airflow-2.11.1-build.x`).

-   Third, before generating the `deployment.yaml` file, you **must ask the
    user** to provide the `artifact_storage` bucket name. Note that the
    `artifact_storage` bucket is typically initialized as a placeholder (e.g.,
    `YOUR_BUCKET`) by the `init` command in Step 1. You must identify any such
    placeholders, ask the user for the actual bucket name, and then update the
    `deployment.yaml` file with the provided value.

    Use the returned composer list with details, along with the project ID,
    region, and the bucket name provided by the user, to generate or update the
    `deployment.yaml` file. When generating or updating the `deployment.yaml`
    file, you **must** replace placeholders (e.g., "<YOUR_PROJECT_ID>",
    "<YOUR_REGION>", "<YOUR_COMPOSER>", "<YOUR_BUCKET>") with the actual
    retrieved and provided values. Additionally, you **must** remove any
    associated `# TODO:` comments once the placeholders are replaced.

-   Ensure both files adhere to the code structures and syntax specified in this
    document.

-   **Renaming Pipelines**: If requested to change the orchestration pipeline
    name, you must rename the orchestration YAML file accordingly (e.g., from
    `dbt_clean_pipeline.yaml` to `new_name.yaml`) and update the `source` field
    within the `pipelines` list in `deployment.yaml` to match the new filename.

> [!IMPORTANT]
>
> **Time Format**: Do NOT include the `Z` suffix in `startTime` and `endTime`.
> Use the format `"YYYY-MM-DDTHH:MM:SS"` (e.g., `"2025-10-01T00:00:00"`).

### Step 4: Validate the content (REQUIRED)

After creating or editing pipeline files, you **MUST** validate them using the
`gcloud beta orchestration-pipelines validate` command. you must: a. Read the
`deployment.yaml` file to identify all defined environments. b. Run the
`validate` command below for **each** environment found in `deployment.yaml`.

```
# Replace <ENV_NAME> with the identified environment name
gcloud beta orchestration-pipelines validate --environment=<ENV_NAME>
```

### Step 5: Handle Validation Errors

1.  Check the output of the validation command.

2.  If the command returns an error or failure message:

    -   Read the error message carefully.
    -   Edit the orchestration and deployment files to fix the specific issue
        mentioned.
    -   If the error is `has no field named "<field>"` for a field documented in
        `references/orchestration-pipelines-schema.md`, you MUST verify the
        Google Cloud CLI version (check the CLI's internal `model_version` with
        `gcloud beta orchestration-pipelines info`;
        `createAndRunCustomJob` and `onPipelineSuccess` require `model_version` `1.2.X` or higher).
        Ask the user to run `gcloud components update` and re-validate. Do NOT
        rewrite the action into a different type.

3.  Re-run the validation command to confirm the fix. Do not mark the task as
    complete until the validation passes (exit code 0), and do not fall back to
    create airflow dag in python if validation fails.

## Declarative Pipeline Templates

When asked to generate or verify declarative pipeline files, ensure they follow
these compliant structures. **Do not use the exact values below; adapt them to
the user's specific project, region, and environment details.**

### `deployment.yaml` Template - IMPORTANT FORMAT MUST MATCH-

```yaml
environments:
  <environment_name>: # e.g., dev, prod
    project: <PROJECT_ID>
    region: <REGION>
    composer_environment: <COMPOSER_ENVIRONMENT_NAME>
    gcs_bucket: "" # Optional
    artifact_storage:
      bucket: <ARTIFACT_BUCKET_NAME>
      path_prefix: "<prefix>-" # e.g., namespace or username prefix
    pipelines:
      - source: '<orchestration-pipeline.yaml>' # e.g., list of pipeline yaml names
```

### Step 6: Deploy the Orchestration Pipeline (Optional)

If requested to **deploy** the orchestration pipeline:

1.  You MUST ask the user which environment to deploy to. If no environment name
    is provided, list the available environments from `deployment.yaml` and ask
    the user to choose one, defaulting to `dev` if it exists.

2.  Read the orchestration YAML to extract the `pipelineId`.

3.  Deploy with `--local`. This uploads the DAG without running it:

    ```
    # Replace <ENV_NAME> with the target environment
    # Replace <PIPELINE_SOURCE> with the orchestration YAML filename
    gcloud beta orchestration-pipelines deploy \
      --environment=<ENV_NAME> --local
    ```

4.  Parse the deploy output to extract the **bundle ID** (version). The output
    includes a line like: `Pipeline deployment successful for version
    local-b32d15e307b5` The version string (e.g., `local-b32d15e307b5`) is the
    bundle ID.

> [!IMPORTANT]
>
> `--local` deployments now default to `--paused=true`. The deployed DAG will be
> visible in Airflow as a paused DAG without a schedule. It will **not**
> auto-run. Use Step 7 to trigger it.

### Step 7: Trigger the Orchestration Pipeline Run (Optional)

If requested to **trigger/run** the orchestration pipeline, you MUST follow the
Deploy → Poll → Trigger flow.

1.  **Ask for environment**: You MUST ask the user which environment to use.
    Default to `dev` if it exists in `deployment.yaml`.

2.  **Deploy first** (Step 6): Always deploy before triggering to ensure the run
    uses the latest code. Extract the `bundle ID` from deploy output and the
    `pipelineId` from the orchestration YAML.

3.  **Poll for DAG readiness**: Wait for the DAG to be registered in Composer.

    ```bash
    # Initial delay: wait 30 seconds after deploy
    sleep 30

    # Poll every 15 seconds, up to 2 minutes total
    # Replace <ENV_NAME>, <BUNDLE_ID> with actual values

    gcloud beta orchestration-pipelines list \
    --environment=<ENV_NAME> \
    --bundle=<BUNDLE_ID>
    ```

    The pipeline is ready when it appears in the list output. If it does not
    appear after 2 minutes, report failure and advise the user to check YAML
    validity.

4.  **Trigger the pipeline**:

    ```
    # Replace <ENV_NAME>, <BUNDLE_ID>, <PIPELINE_ID> with actual values
    gcloud beta orchestration-pipelines trigger \
    --environment=<ENV_NAME> \
    --bundle=<BUNDLE_ID> \
    --pipeline=<PIPELINE_ID>
    ```

5.  **Verify the run started**:

    ```
    gcloud beta orchestration-pipelines runs list \
    --environment=<ENV_NAME> \
    --bundle=<BUNDLE_ID> \
    --pipeline=<PIPELINE_ID>
    ```

> [!TIP]
>
> **Trigger-only (no deploy):** If the user wants to trigger an already-deployed
> pipeline, skip Step 6. Use `gcloud beta orchestration-pipelines list
> --environment=<ENV_NAME>` to find the bundle ID, then trigger directly with
> Step 7.4.

> [!IMPORTANT]
>
> **Fallback:** If `gcloud trigger` fails, use the bundled script: Run script
> with -- help to discover and learn the interface.
>
> ```
> python scripts/trigger/airflow_trigger.py \ --project <PROJECT_ID>
> --location <REGION> \ --environment <COMPOSER_ENV> --dag_id <PIPELINE_ID>
> ```
>
> Get `project`, `region`, and `composer_environment` from `deployment.yaml`.

## Definition of done

-   `deployment.yaml` file is created successfully.
-   The orchestration pipeline file (e.g., `orchestration_pipeline.yaml`) is
    created successfully, includes a mandatory `endTime` for every schedule, and
    passes the validation command: `gcloud beta orchestration-pipelines validate
    --environment=<ENV_NAME>`
-   If user requested to **deploy** the orchestration pipeline, the `gcloud beta
    orchestration-pipelines deploy --environment=<ENV_NAME> --local` command
    should return a success message with a version/bundle ID.
-   If user requested to **trigger/run** the orchestration pipeline:
    1.  Deploy succeeded (bundle ID extracted from output)
    2.  DAG appeared in `gcloud beta orchestration-pipelines list` within 2 min
    3.  `gcloud beta orchestration-pipelines trigger` returned success
    4.  Run is visible in `gcloud beta orchestration-pipelines runs list`

## Other actions

If requested to pause/stop the orchestration pipeline, use

```bash
    # Replace <ENV_NAME>, <BUNDLE_ID>, <PIPELINE_ID> with actual values
    gcloud beta orchestration-pipelines pause \
    --environment=<ENV_NAME> \
    --bundle=<BUNDLE_ID> \
    --pipeline=<PIPELINE_ID>
```

If requested to unpause/resume the orchestration pipeline, use

```bash
    # Replace <ENV_NAME>, <BUNDLE_ID>, <PIPELINE_ID> with actual values
    gcloud beta orchestration-pipelines unpause \
    --environment=<ENV_NAME> \
    --bundle=<BUNDLE_ID> \
    --pipeline=<PIPELINE_ID>
```
