# AtmosIQ Audit — Phase 2: Environment and Reproducibility Audit

**Audit Date**: 2026-10-12  
**Auditor**: Senior QA Automation Engineer / Production Readiness Auditor  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Environment Verification Summary

| Check | Specification | Observed Status | Verdict | Evidence / Notes |
|---|---|---|---|---|
| **Python Runtime** | Python 3.13.x | Python 3.13.11 (win32, 64-bit) | PASS | Verified via `.\.venv\Scripts\python.exe --version` |
| **Virtual Environment** | `.venv` | Root directory `.venv` | PASS | Interpreter at `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ\.venv\Scripts\python.exe` |
| **Package Management** | pip in `.venv` | pip 26.2.1 installed | PARTIAL | Pip warning: `Ignoring invalid distribution ~ip` in site-packages |
| **Backend Dependencies** | Declared in `backend/requirements.txt` | 10 packages declared; all installed | PASS | `fastapi`, `uvicorn`, `httpx`, `pydantic-settings`, `python-dotenv`, `pytest`, `pytest-asyncio`, `google-genai`, `langgraph`, `langchain-google-genai` |
| **Frontend Dependencies** | Declared in `frontend/requirements.txt` | 2 packages declared (`streamlit`, `httpx`); `pandas` **missing** | FAIL | `frontend/app.py` line 5 has `import pandas as pd`, but `pandas` is omitted from `frontend/requirements.txt` |
| **Backend Import** | `from app.main import app` | Clean import, status 0 | PASS | Evaluated: `App successfully imported: AtmosIQ Weather API 0.5.0` |
| **File Encoding / BOM** | Standard UTF-8 without BOM | 8 Python files have UTF-8 BOM (`\xef\xbb\xbf`) | PARTIAL | `frontend/app.py`, `weather_graph.py`, `supervisor.py`, etc., start with BOM, causing raw UTF-8 string parsers to fail |
| **Pytest Cache System** | Writeable `.pytest_cache` | Permission Denied on `.pytest_cache/v/cache/nodeids` | PARTIAL | Pytest generates cache warning unless `-p no:cacheprovider` is passed |

---

## 2. Dependency Discrepancy Analysis

### Backend Dependencies (`backend/requirements.txt`)
```text
fastapi
uvicorn[standard]
httpx
pydantic-settings
python-dotenv
pytest
pytest-asyncio
google-genai
langgraph
langchain-google-genai
```
- **Installed Status**: All 10 declared backend packages (and their transitive dependencies, such as `starlette`, `pydantic`, `langchain-core`, etc.) are installed and active in `.venv`.
- **Finding**: While installed in the local environment, no exact versions or pinned lockfile (`requirements.lock` or `Pipfile.lock` or `poetry.lock`) exist. Minor or major upstream changes may cause future non-reproducibility.

### Frontend Dependencies (`frontend/requirements.txt`)
```text
streamlit
httpx
```
- **Discrepancy**:
  `frontend/app.py` line 5 explicitly executes:
  ```python
  import pandas as pd
  ```
  And lines 463–494 build a Pandas DataFrame:
  ```python
  df = pd.DataFrame(chart_data)
  ```
  `pandas` is **omitted** from `frontend/requirements.txt`.
- **Impact**: Any fresh installation running `pip install -r frontend/requirements.txt` in a separate frontend environment will crash immediately upon startup with `ModuleNotFoundError: No module named 'pandas'`.

---

## 3. Environment Variables & Configuration Validation

| Variable | Target Module | Default Value | Required / Optional | Observed Behavior |
|---|---|---|---|---|
| `ATMOSIQ_USE_GEMINI` | `weather_graph_llm.py` | `"true"` | Optional | When set to `"false"`, disables Gemini calls and falls back to deterministic agents. |
| `GEMINI_API_KEY` | `weather_graph_llm.py`, `gemini_service.py` | `""` | Optional (if disabled) | If `ATMOSIQ_USE_GEMINI=true` and key is empty, raises `RuntimeError: GEMINI_API_KEY is missing.` |
| `ATMOSIQ_LOCAL_ROUTING`| `supervisor.py` | `""` | Optional | Set to `"1"` during synthetic evaluation to force local keyword routing. |
| `ATMOSIQ_API_URL` | `frontend/app.py` | `"http://127.0.0.1:8000"` | Optional | Allows pointing Streamlit to a remote or non-standard backend URL. |

---

## 4. Execution & Setup Path Audit

The `README.md` documents:
```powershell
cd "C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ\backend"
python -m pytest -v
```
When running this command in a fresh terminal without activating the root `.venv`, `python` defaults to the global system Python instead of the virtual environment unless activated.
Furthermore, if `.venv` is created inside `backend/` as some developers might assume, the path diverges from the project root where `.venv` actually lives.

**Resolution Recommendation**:
1. Add `pandas` to `frontend/requirements.txt`.
2. Add a `pytest.ini` with `addopts = -p no:cacheprovider` to silence the Windows `.pytest_cache` ACL permission warning.
3. Remove the broken `~ip` folder in `.venv/Lib/site-packages`.
