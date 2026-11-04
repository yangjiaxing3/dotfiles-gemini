---
name: managing-python-dependencies
description: "Use when running pip install or adding Python packages to enforce project virtualenvs (.venv) over global installs. Python虛擬環境與套件依賴管理"
license: Apache-2.0
version: v3
---

# Python Dependency Management Rule

> [!CAUTION]
>
> **BEFORE any `pip install`**: You MUST first detect the project's existing
> dependency manager and use it correctly. Do NOT override the project's
> established tooling.

> [!NOTE]
>
> **Reactive Environment Check Bundling (Only When Installing)**: Do NOT run
> environment or package availability checks (`importlib.util.find_spec`,
> `pip list`, `ls uv.lock...`) proactively before writing code or creating a
> notebook. Only probe the environment when a package actually needs to be
> installed (for example, on `ModuleNotFoundError` / `ImportError` or an
> explicit user request to install dependencies).
>
> - **In Notebooks**: When a notebook cell execution tool (`execute_cell` /
>   `notebook_execute_cell`) is available, check package availability (`import
>   <pkg>` or `%pip list`) and install missing packages (`%pip install`)
>   **inside notebook cells**, never via `python3 -c` or `pip` in the shell.
> - **In the Shell (Only When Installing)**: When a shell check is required
>   before installing a missing package for a local script or project, you MUST
>   NOT run multiple sequential 1-line shell check commands. Combine all
>   environment and package availability probes into a single composite python
>   one-liner or shell check step:
>
> ```bash
> python3 -c "import sys, importlib.util; print(f'Python {sys.version.split()[0]}'); [(print(f'{pkg}: {__import__(pkg).__version__}') if importlib.util.find_spec(pkg) else print(f'{pkg}: not found')) for pkg in ['pyspark', 'google.cloud.bigquery']]"
> ```
>
> This bundling also applies to dependency manager detection; when an install is
> needed, use a single `ls` or `find` command to check for all potential
> dependency manager configuration and lock files at once (e.g. `ls uv.lock
> poetry.lock Pipfile.lock requirements.txt pyproject.toml`).

## Dependency Manager Detection (Only When Installing)

Only run dependency manager detection when a package actually needs to be
installed (e.g., on `ModuleNotFoundError` / `ImportError` or when setting up a
missing local project environment)—never as an upfront pre-flight check before
creating or running a notebook. Before installing ANY Python package, check the
workspace for these files **in priority order**:

1.  **Signal:** `uv.lock` or `pyproject.toml` with `[tool.uv]`
    *   **Tool:** **uv**
    *   **Install:** `uv add <package>`
    *   **Setup:** `uv sync`
2.  **Signal:** `pyproject.toml` with `[tool.poetry]`
    *   **Tool:** **Poetry**
    *   **Install:** `poetry add <package>`
    *   **Setup:** `poetry install`
3.  **Signal:** `Pipfile`
    *   **Tool:** **Pipenv**
    *   **Install:** `pipenv install <package>`
    *   **Setup:** `pipenv install`
4.  **Signal:** `environment.yml`
    *   **Tool:** **Conda**
    *   **Install:** `conda install <package>`
    *   **Setup:** `conda env create -f environment.yml`
5.  **Signal:** `requirements.txt` only
    *   **Tool:** **venv + pip**
    *   **Install:** `.venv/bin/pip install <package>`
    *   **Setup:** `.venv/bin/pip install -r requirements.txt`
6.  **Signal:** None of the above
    *   **Tool:** **venv + pip** (default)
    *   **Install:** `.venv/bin/pip install <package>`
    *   **Setup:** `.venv/bin/pip install -r requirements.txt`

## Default: venv + pip

If no dependency manager is detected, use **venv + pip + requirements.txt** as
the default:

```bash
# Initialize environment
python3 -m venv .venv

# Add dependencies
.venv/bin/pip install <package>

# Preserve state
.venv/bin/pip freeze > requirements.txt
```

**Rules for venv + pip workflow:**

-   Always use `.venv/bin/pip` or `.venv/bin/python` (explicit path).
-   After installing, run: `.venv/bin/pip freeze > requirements.txt`.
-   When setting up: `.venv/bin/pip install -r requirements.txt`.

## Prohibited

-   **NEVER** run `pip install` globally
-   **NEVER** override an existing dependency manager with a different one

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
