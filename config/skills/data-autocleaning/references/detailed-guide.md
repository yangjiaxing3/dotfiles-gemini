# data-autocleaning — Detailed Reference & Extended Examples


-   **Unnesting**: Unnest array fields **only** if a destination schema
    explicitly requires it.
-   **Type Casting**: Attempt to cast elements to the most appropriate common
    type.
-   **CRITICAL**: Filter out `NULL` elements after `SAFE_CAST` (e.g., using
    `ARRAY`) as BigQuery arrays cannot contain `NULL`s.
-   **Normalization**: Only trim whitespace on string fields. Make sure to
    **PRESERVE CASE**. **DO NOT** perform case conversions (e.g., `LOWER()`,
    `UPPER()`) unless explicitly required.
-   **Filtering**: Filter out `NULL` values using `ARRAY_FILTER(array_column, e
    -> e IS NOT NULL)`.
-   **Deduplication**: Use `ARRAY(SELECT DISTINCT x FROM UNNEST(array_column))`
    for case-sensitive deduplication.
-   **Transformations**: Use `ARRAY_TRANSFORM` or `UNNEST`/`ARRAY_AGG` for
    element-wise changes (e.g., date parsing).
-   **Restructuring**: Use `UNNEST` to expand to rows, or `ARRAY_AGG` to group
    rows into an array, as required by the destination schema.

#### STRUCT/Record Data Handling

-   **Extraction**: Extract fields to top-level columns **only** if the
    destination schema requires it.
-   **Type Casting**: Cast each field using `SAFE_CAST` based on the destination
    schema or inferred profile.
-   **Normalization**: Only trim whitespace on string fields. Make sure to
    **PRESERVE CASE**. **DO NOT** perform case conversions (e.g., `LOWER()`,
    `UPPER()`) unless explicitly required.
-   **Field Mapping**: Map directly if structures align; use dot notation (e.g.,
    `struct.field`) to extract; or use `STRUCT()` constructor to group columns.
-   **Schema Alignment**: Populate missing fields with `NULL` and drop fields
    not present in the destination schema.

### Step 3: Quality Review & Profiling

> [!IMPORTANT]
>
> You **MUST** verify transformations strictly using the protocol below before
> completing the task. **Never** skip this step. Use **Dataplex profiling only**
> (unless scan was denied by the user) — not ad-hoc SQL queries.

**Quality review protocol:**

1.  Extract the `SELECT` query containing all generated transformations
    (autocleaning, schema mapping, JSON extractions).
2.  Create a **temporary sample output table** (max 1M rows, 1-hour TTL) by
    running the transformation query.
3.  Fix any runtime errors and re-run until the query succeeds.
4.  **Profile the temporary sample output table using Dataplex**:
    -   **Verify approval**: If scan execution was approved in Step 1, proceed.
        If approval was DENIED in Step 1, DO NOT run the scanner script and DO
        NOT ask the user for approval again. Proceed with manual verification
        using `bq` sample queries to ensure transformations were successful.
    -   Run the `scripts/dataplex_scanner.py` script on the temporary table.
    -   The script will automatically wait for the profile job to finish and
        save the results as JSON.
5.  **Compare profiles** (Skip if scans were denied) — Check the new profile
    against the Step 1 profile for **every transformed column**:

    ```markdown
    | Anomaly Type | Threshold |
    | --- | --- |
    | **NULL increase** | >1% increase compared to source (unless expected) |
    | **Value range shift** | Unexpected ranges or formats |
    ```

6.  **Iterate on anomalies** — For each anomaly:

    1.  **Identify**: Query samples where source is `NOT NULL` but transformed
        value `IS NULL`.
    2.  **Fix**: Update the transformation logic.
    3.  **Repeat**: Re-run Step 3 until the anomaly is resolved.

### Step 3.5: Quality Review Evidence Requirements

Your `walkthrough.md` **MUST** include a **Quality Review Profiling Evidence**
section. **Note**: If scan execution was denied by the user, document the denial
reason here instead of Job IDs.

```markdown
## Quality Review Profiling Evidence
- [ ] Post-Transformation Dataplex Profile Job ID: <JOB_ID>
- [ ] Profile Comparison Summary: <Detailed comparison between initial and final profiles per column>
```

> [!CAUTION]
>
> **Do not** conclude the task or ask for user review until this section is
> filled and the profile comparison is documented.

### Step 4: Documentation

Your `walkthrough.md` must contain a table for each transformation in the
following format:

```markdown
| Field | Description |
| --- | --- |
| **Destination schema considered** | The target column/type being matched |
| **Issue Detected** | What data quality problem was found |
| **Transformation Applied** | The SQL logic used to fix it |
| **Benefit** | Why this transformation improves the data |
```

Include a summary of all quality review steps and profiling evidence.

## Definition of Done

-   All source data quality issues are identified and addressed via SQL
    transformations.
-   Verification MUST be completed using the **Quality review protocol** and
    documented with evidence.
-   The verification step **MUST only** test the changes and should succeed when
    the sql is executed.
-   Transformations align with the target schema if provided.
-   Cleaning summary is provided with clear justification for each
    transformation.
-   If skipped, the reason is clearly stated (e.g., ineligible source).
