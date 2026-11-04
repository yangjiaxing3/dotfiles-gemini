---
name: notebook-guidance
description: "Use when creating or executing Jupyter notebooks (.ipynb) for data exploration and %%bqsql BigQuery analysis. Jupyter Notebook資料分析與視覺化"
license: Apache-2.0
version: v7
---

# Notebook Guidance

## When to Use a Notebook

Before choosing to use a notebook, evaluate the task complexity using these
heuristics.

Use a notebook if you meet at least one of these criteria:

*   📈 **Data Insights & Storytelling**: Use a notebook for any request to "give
    insights", "find trends", "explore data", or "analyze data". These tasks
    benefit from using visualizations to present the data.
*   📊 **Visualizations are requested**: The user explicitly asks for charts or
    plots.
*   🔄 **Stateful / Iterative Exploration**: You need to run a query, inspect
    results, and decide the next query based on those results while keeping
    state in memory.

Do NOT use a notebook ONLY if:

*   📝 **Simple Fact/Status**: The request only requires a single number (e.g.,
    "how many rows") or a status check (e.g., "when was this table updated").
*   🏃‍♂️ **Schema Preview**: The request is only about the schema or field
    types.

**Golden Rule of Data Storytelling:** If any analytical insight, trend, or
comparison is involved, favor a notebook and a visualization. A notebook is the
"standard" environment for our developer workflow; do not avoid it because of
"overhead".

## Notebook Best Practices

> [!CAUTION]
>
> **ALL DISCOVERY HAPPENS IN-CELL**: Schema inspection, data preview, package
> availability, and model testing MUST be executed entirely inside notebook
> cells. Do not run shell commands, external SQL tools (`execute_sql`,
> `execute_sql_readonly`), or separate Python scripts/environments to test code
> before creating cells.

> [!IMPORTANT]
>
> **Agent execution rules**: Your behavior MUST depend on whether the
> `notebook_execute_cell` tool is available in your current context: * **If
> notebook `execute_cell` tool is available**: You MUST follow the incremental
> GENERATE CELL -> EXECUTE CELL -> VALIDATE flow. * **If notebook `execute_cell`
> tool is NOT available**: You MUST generate the complete notebook and request
> user execution.

1.  **CONDITIONAL EXECUTION FLOW**:
    *   **If notebook `execute_cell` tool is available**: Follow the **STEP BY
        STEP GENERATE CELL -> EXECUTE CELL -> VALIDATE OUTPUT** flow. Generate
        ONE cell, execute it, then verify the output. If the output is data
        (e.g. a dataframe), you MUST inspect it to confirm the logic is correct
        before generating the next step. Batch generation of an entire notebook
        is strictly prohibited because error propagation in notebooks is
        expensive to fix.
    *   **If notebook `execute_cell` tool is NOT available**:
        *   Create the whole notebook at once.
        *   Tell the user to run the notebook.
        *   Tell the user to let you know once the notebook run is completed so
            you can check the outputs to verify it's correct and fix any errors.
2.  **IDENTIFY DATA EARLY**: Use `@skill:discovering-gcp-data-assets` or
    BigQuery list tools to find the correct `project.dataset.table` before
    writing ANY code. If the table ID is missing, ask the user.
3.  **CLEAN FINAL STATE**: The final notebook MUST NOT have failed cells. It is
    normal for cells to encounter errors during in-notebook prototyping—fix
    failed cells in-place using `replace_cell` (or delete failed attempts)
    before presenting the notebook to the user, rather than pre-testing code
    outside the notebook.
4.  **LOGICAL CHUNK FIDELITY**: Keep cells small. One logical transformation or
    visualization per cell. Group related cells into logical units (e.g., a
    BigQuery `%%bqsql` magic cell followed immediately by a Python visualization
    cell for those results). Use descriptive **markdown cells** to separate and
    document different logical sections.
5.  **GENERATE VISUALIZATIONS**: Always accompany data insights with
    visualizations; charts are often more effective than raw numbers for
    communicating trends and comparisons.

## Kernel & Environment Management

Notebooks run in specific **Kernels** (execution backends). You MUST ensure the
kernel’s Python environment contains the necessary libraries (`bigframes`,
`ipykernel`, etc.).

### Kernel Types

1.  **Local Python**: Standard Python 3 kernel running on the notebook host
    (Managed instance, local machine).
2.  **Cloud Spark Remote (Dataproc Serverless)**: Transient Spark environment
    managed by GCP. Use for large-scale data processing.
3.  **Cloud Spark Remote (Dataproc Cluster)**: Persistent Spark clusters for
    shared or custom configurations.
4.  **Colab (Managed)**: Ephemeral Google-managed runtimes.

### No Active Kernel / Setup Check

1.  **Infer or Ask about Kernel Preferences**:
    -   **Infer from notebook purpose**:
        -   Only "Spark" notebooks may use a **Remote Spark** kernel.
            "BigFrames" and "BigQuery" notebooks MUST use **Local Python**.
    -   **Infer from notebook cells**:
        -   Presence of a Spark Connect session, for example
            `ManagedSparkSession` or `DataprocSparkSession`, indicates
            **Local Python**.
    -   **Infer from notebook metadata**:
        -   Read the `metadata.kernelspec` notebook field. A **Remote Spark**
            kernel name starts with a connection hash.
    -   **Infer from Context**:
        -   For a "Spark" notebook, evidence of a local Python setup (such as a
            Spark Connect session) means you should lean towards
            **Local Python**. Without such evidence, lean towards
            **Remote Spark**.
    -   **Ask when Ambiguous**: If multiple options fit, ask if they prefer a
        **Local Python** or a **Remote Kernel**.
2.  **For Local Setup**: Use `@skill:managing-python-dependencies` to verify if
    a virtual environment exists. If not, create one. Ensure `ipykernel` is
    installed in that environment. Install any other relevant libraries.
3.  **For Remote Setup**: Advise the user to use the UI to select the
    appropriate remote kernel.

> [!IMPORTANT]
>
> **HARD STOP on kernel failure**: If a cell execution returns "no active
> kernel" or any kernel-not-found error, you MUST **stop immediately**. Do NOT
> scaffold, generate, or insert any further cells. Inform the user which kernel
> is needed (e.g., PySpark / Dataproc Serverless) and wait for explicit
> confirmation that a kernel is active before proceeding with notebook
> execution.

### Proper Library Installation

#### 1. Local Kernels

Before installing any python libraries, you MUST use
`@skill:managing-python-dependencies` to detect how python dependencies are
managed in the project.

#### 2. Remote Kernels (Spark/Colab)

Since these are often ephemeral or managed by GCP:

*   **Check first (REQUIRED)**: Before writing any `%pip install` cell, run
    `%pip list` or `import <package>` to confirm the package is not already
    present. Managed runtimes (Dataproc Serverless, Colab) pre-install many
    common packages. Only install what is confirmed missing.
*   Use `%pip install <package>` in the first cell if a package is confirmed
    missing and it's the only way to modify the runtime.

When in doubt about the kernel type or preferred installation method, ask the
user for clarification.


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **禁止廉價 AI 模板感 (Anti-Slop)**：避免過度使用無意義的紫藍漸層、千篇一律的三欄卡片與脫離業務語境的假數字。
- **日期與表單無障礙**：所有 `<input type="date" lang="en" />` 強制加註 `lang="en"`；互動按鈕需具備明確 `title` 或 `aria-label` 與鍵盤焦點狀態。
