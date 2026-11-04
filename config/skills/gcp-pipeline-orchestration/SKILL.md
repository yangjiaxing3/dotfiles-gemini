---
name: gcp-pipeline-orchestration
description: "Use when generating or updating Cloud Composer (Airflow) DAG orchestration definitions for data pipelines. Cloud Composer資料管線排程編排"
license: Apache-2.0
version: v4
---

## Mandatory Reference Routing

If relevant, call the associated reference file(s) before you take actions.
Refer to the table below to determine which reference file to retrieve in
different scenarios involving specific functions. [!IMPORTANT]: DO NOT GUESS
filenames. You MUST only use the exact paths provided below.

Function/Use Case                  | Required Reference File                        | Capabilities & Intent Keywords
---------------------------------- | ---------------------------------------------- | ------------------------------
**orchestration-pipelines schema** | `references/orchestration-pipelines-schema.md` | orchestrate, generate, create, update

## How to use this skill

Orchestration pipelines require creating two files to ensure a complete and
deployable pipeline:

1.  `Orchestration File` (e.g., `orchestration-pipeline.yaml`,
    `test-pipeline.yaml`): Defines the pipeline's logic, tasks, and schedule.
    **IMPORTANT:** Check if a `deployment.yaml` file exists and references an
    existing orchestration file. If it does, you **must update the existing
    orchestration file** (e.g.,`test_pipeline.yaml`) instead of creating a new
    one. The filename can be customized but must be referenced in the
    `deployment.yaml` file.
2.  `deployment.yaml`: Defines the environment-specific configurations.(e.g.,
    `dev`, `prod`). `deployment.yaml`should only exists in the repository root
    and must be named `deployment.yaml`

-   All files should always be maintained together. And all files should be
    placed on the root of the workspace folder.

-   This skill is helpful to create or update configuration files to orchestrate
    data pipelines.

## How to use this skill

### Step 1: Assess Orchestration Pipeline Status and Initialize if Necessary

Examine the repository's root directory for a `deployment.yaml` file.

1.  **Check for existing setup**: The absence of `deployment.yaml` indicates
    that orchestration has not been set up.
2.  **Determine if initialization is required**: Initialization is required if
    `deployment.yaml` is missing. you **MUST** run the `init` command in Step 3
    to scaffold the project if `deployment.yaml` is missing. Do NOT create the
    files manually.
3.  **Pipeline Name**: If initialization is needed, ask the user for the
    pipeline name. If user hasn't provided the orchestration pipeline name, name
    should be "orchestration_pipeline"
4.  **Environment Name**: If initialization is needed, you MUST ask the user for
    the environment name. If the user does not provide it, use **dev** as the
    default.

5.  **Execute Initialization**: Once you have the pipeline name, run the
    following command:

```
# Replace <ORCHESTRATION_PIPELINE_NAME> with the actual name
# Replace <ENV_NAME> with the actual environment name
gcloud beta orchestration-pipelines init <ORCHESTRATION_PIPELINE_NAME> --environment=<ENV_NAME>
```

### Step 2: Review the orchestration pipeline code structure and syntax instruction

*** Pipeline Models (mapping to YAML)

> [!IMPORTANT]
>
> While the internal pipeline models are defined using protobuf (which typically
> uses `snake_case`), the **YAML configuration expects `camelCase`** for almost
> all field names.
>
> **Mapping Rule:** Always convert `snake_case` proto fields (e.g.,
> `pipeline_id`) to `camelCase` in YAML (e.g., `pipelineId`).

#### Orchestration-Pipelines yaml structure and syntax instruction

Reference to file `references/orchestration-pipelines-schema.md`.

**Required Tags (Top-Level)**: You **MUST** add a `tags` field to the top-level
of the orchestration pipeline YAML definition. The value of this field depends
on the IDE environment:

-   For Antigravity, use `["job:datacloud:antigravity"]`.
-   For VS Code, use `["job:datacloud:vscode"]`.
-   For Gemini CLI, use `["job:datacloud:gemini-cli"]`.
-   For Claude Code, use `["job:datacloud:claude"]`.
-   For Codex, use `["job:datacloud:codex"]`.
-   For any other environment, use `["job:datacloud:other"]`.

#### Deployment yaml structure and syntax instruction.

**Top-Level Structure:** The root of the YAML should be an object with the
following fields:

-   `environments` (dictionary): A map where keys are environment names (e.g.,
    'dev', 'prod', etc) and values are Environment objects.

**Environment:** Each environment object contains the following fields:

-   `project` (string): The Google Cloud Project ID.
-   `region` (string): The Google Cloud region (e.g., 'us-central1').
-   `composer_environment` (string): The Cloud Composer environment name.
-   `artifact_storage`
    -   `bucket` (string): GCS bucket
    -   `path_prefix`(string): prefix of path that we want to put in bucket
-   `pipelines`
    -   `- source` (string): orchestration pipeline yaml file names. It can be
        multiple
-   `variables` (dictionary, optional): Key-value pairs representing environment
    variables. Values can be strings, numbers, or booleans.

> [!TIP]
>
> If the user doesn't provide specific paths for scripts, dbt projects, or GCP
> details (Project ID, Region), use tools like `find_by_name` to search the
> repository and `gcloud` commands (e.g., `gcloud config get-value project`) to
> retrieve the necessary information.

### Step 3: Generate the pipeline files

-   Before generating, check if an orchestration pipeline definition file and
    `deployment.yaml` already exist in the current directory. If they do, inform
    the user and ask if they want to update the existing files or create new
    ones with different names. Do not overwrite without confirmation.

-   First, before creating the orchestration pipeline definition file, you
    **must** first run the following command to get the list of available
    dataproc environments for the user's project. This avoids using placeholder
    values to run the jobs.

    ```
    # Replace <PROJECT_ID> with the actual project_id
    # Replace <REGION> with the actual region
    gcloud dataproc clusters list \
    --project <PROJECT_ID> \
    --region <REGION> \
    ```

    > [!TIP]

## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
