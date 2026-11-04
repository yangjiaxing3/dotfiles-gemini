---
name: gcp-dataflow
description: "Use when building, packaging, or debugging Apache Beam pipelines and Flex Templates on Dataflow. GCP Dataflow資料管線"
license: Apache-2.0
version: v5
---

# Apache Beam Pipelines on Cloud Dataflow

## Pipeline authoring

Use this section when implementing Dataflow pipeline logic using Apache Beam.

### Check if existing Google Dataflow Template exists

Google provides a variety of pre-built, open source Dataflow templates that can
be used for common scenarios. Before implementing a pipeline from scratch, you
MUST follow the steps below to check whether a Dataflow template for the
pipeline logic you need to implement already exists.

-   **Step 1: Check for a matching Google Dataflow Template**

    -   Identify the **source** and **sink** (e.g., GCS to BigQuery) from the
        user's request. *Note*: You *MUST NOT* proceed until the source and sink
        are clearly identified.
    -   **Action**: List templates in the public `dataflow-templates` bucket:
        *   For Classic templates, check `gs://dataflow-templates/latest`.
        *   For Flex templates, check `gs://dataflow-templates/latest/flex`. Use
            `gcloud storage ls` to list the contents.
    -   Match templates by name or description to the source and sink.
    -   If no matching template is found, go to **Create a new pipeline from
        scratch**.

-   **Step 2: Confirm template selection**

    -   Present the matched template(s) to the user with a brief explanation of
        why they match, and make a note of whether it is a Classic or Flex
        template.
    -   **Action**: Ask the user for explicit confirmation to proceed with this
        template.
    -   If the user rejects or prefers a custom solution, proceed to **Create a
        new pipeline from scratch**.

### Create a new pipeline from scratch

Use this section when creating a new project for a Dataflow pipeline from
scratch.

-   If the user doesn't say explicitly which language (Java, Python, Go) shall
    be used to write the pipeline, you MUST confirm the language.
-   Determine which version of Beam SDK should be used by searching for the most
    recently released version of Apache Beam, unless the user already uses a
    particular version.
    -   **Action**: Run a web search for the latest Apache Beam SDK release.
-   YOU MUST use same version of Apache Beam consistently throughout the project
    in Dockerfiles, `requirements.txt`, and other similar files where versions
    are specified.

### Java projects using Gradle

Use this section when configuring a Dataflow Java pipeline project using gradle.

-   **Shadow Jars (Fat Jars)**: Do NOT propose to use the Shadow plugin
    (`com.github.johnrengelman.shadow`) unless the user explicitly requests a
    Fat Jar.
-   **Passing command-line parameters**: Use the `application` plugin for
    passing command-line parameters.
-   **SLF4J Logging Dependency Alignment**:
    -   Verify the `slf4j-api` version pulled transitively by Apache Beam.
    -   You MUST configure the application logging backend (`slf4j-simple`,
        `logback-classic`, etc.) to exactly match the major/minor version of the
        resolved `slf4j-api`.

### Packaging a pipeline as a Flex Template

Use this section to package pipeline code as a Flex template.

Flex Templates offer a hermetic and reproducible launch environment for a
pipeline. They are easy to launch with `gcloud` or with orchestrators like Cloud
Composer. You **MUST** package the pipeline as a Flex Template when creating new
Dataflow pipeline projects.

Follow the steps below:

-   **Provide Instructions**: Provide instructions on rebuilding and running
    Flex Templates to the user in walkthrough.
-   **Use Single Docker Image for Python pipelines**: For Python Flex Templates,
    it is better to use a single image for the template launcher image and for
    the worker runtime environment (`--sdk_container_image`). Does the Python
    pipeline require extra dependencies (e.g., using `--requirements_file`,
    `--setup_file`, or `--extra_package`)? If so, **YOU MUST recommend the**
    **Single Docker Image Configuration** for the Flex Template. See
    [python_flex_template_reference.md][py-flex-ref] for details.
-   **Prefer Cloud Build over Local Docker**:
    -   Do NOT assume local Docker availability on the workspace machine.
    -   **Action**: Suggest and provide `cloudbuild.yaml` out-of-the-box for
        building and pushing images unless local setup is explicitly requested.
    -   When building images with Cloud Build in the background you MUST provide
        the link where the user can monitor the long-running operation.
-   **Providing SSL certificates and Secrets to Workers**:
    -   If certificates or keys are stored in Secret Manager, **NEVER** bake
        them into the Docker image layers. Instead, retrieve them dynamically at
        runtime inside the Apache Beam `DoFn.setup()` lifecycle using the Secret
        Manager client library (writing them to ephemeral worker disk like
        `/tmp` only if physical file paths are strictly required). Ensure the
        Dataflow Worker Service Account has the
        `roles/secretmanager.secretAccessor` role.

## Configuring Google-provided templates

Use this section when the user has selected a Google-provided template (Classic
or Flex) and you need to configure it.

-   **Step 1: Get template metadata**

    -   Identify template type:
        *   **Classic**: Metadata files are in `gs://dataflow-templates` and end
            with `_metadata` (e.g.,
            `gs://dataflow-templates/latest/Word_Count_metadata`).
        *   **Flex**: Metadata are embedded in the template spec file under
            `gs://dataflow-templates/latest/flex` (e.g.
            `gs://dataflow-templates/latest/flex/Cloud_Datastream_to_BigQuery`).
    -   Read the corresponding template metadata file to identify required
        parameters.
    -   **Note**:
        *   Make sure to run a recursive search over the bucket if needed to
            locate the metadata.
        *   If the template parameters include UDF-related fields (e.g.,
            `javascriptTextTransformGcsPath`,
            `javascriptTextTransformFunctionName`), refer to the
            [UDF guide][udf-guide] to write and configure the UDF.
        *   **Parameter-Based SSL / Secret Staging**: If the Google-provided
            template requires local SSL certificates or Secret Manager secrets,
            pass comma-separated GCS paths via the `extraFilesToStage`
            parameter. The runner will drop them into `/extra_files` on worker
            VMs. Refer to the [SSL certificates guide][ssl-cert-guide] for local
            referencing syntax (`/extra_files/...`).

-   **Step 2: Get network configuration**

    -   **Action**: Run `gcloud` commands to list networks and subnetworks.
    -   Confirm the network and subnetwork to use with the user.

-   **Step 3: Identify required parameters and prepare resources**

    -   Extract required parameters from the template metadata.
    -   > [!IMPORTANT]

## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
