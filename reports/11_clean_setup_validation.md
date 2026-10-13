# AtmosIQ Audit — Phase 11: Documentation and Clean-Environment Audit

**Audit Date**: 2026-10-12  
**Auditor**: QA Automation Engineer / DevOps Auditor  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Executive Summary

The repository's setup instructions, prerequisites, startup commands, testing commands, and endpoint documentation in `README.md` were evaluated against the real codebase and execution environment.

**Key Findings**:
- **High Setup Accuracy**: The documented Python version (3.13.11), backend test baseline (50 passing tests), and local startup commands work as documented when the virtual environment is activated.
- **Dependency Split Discrepancy**: While README provides a monolithic `pip install` command including `pandas`, developers installing via `frontend/requirements.txt` will suffer a `ModuleNotFoundError: No module named 'pandas'`.
- **Undocumented Artifacts**: `data/training/` containing 8 dataset and evaluation files is not described in the README project tree.
- **Undocumented / Omitted Endpoint**: `GET /api/v1/air-quality` is neither documented in the README API table nor registered in `backend/app/main.py`.

---

## 2. README vs Codebase Comparison Matrix

| Section / Topic | README Claim | Actual Codebase Reality | Verdict | Discrepancy / Action |
|---|---|---|---|---|
| **Python Version** | Python 3.13.x | Python 3.13.11 installed | **PASS** | Exact match |
| **Project Structure** | Omits `data/`, requirements files | Contains `data/training/`, `requirements.txt` in frontend & backend | **PARTIAL** | README tree is simplified; should document `data/training/` |
| **Virtual Environment** | Root `.venv` | Root `.venv` exists | **PASS** | Match |
| **Backend Dependencies** | Declared in monolithic install command | Split across `backend/requirements.txt` | **PASS** | All backend packages install cleanly |
| **Frontend Dependencies** | Claims `streamlit pandas httpx` | `frontend/requirements.txt` missing `pandas` | **FAIL** | Add `pandas` to `frontend/requirements.txt` |
| **Backend Startup** | `uvicorn app.main:app` from `backend/` | Working from `backend/` | **PASS** | FastAPI initializes cleanly on port 8000 |
| **Frontend Startup** | `streamlit run .\frontend\app.py` from root | Working from root | **PASS** | Streamlit loads dashboard on port 8501 |
| **Pytest Execution** | `python -m pytest -v` from `backend/` | 50 tests pass; outputs `.pytest_cache` warning | **PARTIAL** | Add `pytest.ini` with `-p no:cacheprovider` |
| **Py-Compile Check** | `python -m py_compile .\frontend\app.py` | Compiles with exit code 0 | **PASS** | Match |
| **API Endpoints Table** | 6 endpoints documented | 6 active endpoints; `air-quality` omitted | **PARTIAL** | Mount and document `/api/v1/air-quality` |
| **Documented Limitations** | Mentions AQI provider not configured | Code enforces `answer_air_quality_unavailable` | **PASS** | Accurate documentation of known limitations |

---

## 3. Clean-Install Verification Walkthrough

If a developer clones this repository in a fresh clean environment, the following step-by-step procedure must be followed:

```powershell
# 1. Clone & enter repository
cd AtmosIQ

# 2. Create and activate Python 3.13 virtual environment
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip install -r frontend/requirements.txt
# (Requires pandas added to frontend/requirements.txt)

# 4. Configure environment
Copy-Item backend/.env.example backend/.env

# 5. Run test suite
cd backend
python -m pytest -v -p no:cacheprovider
cd ..

# 6. Launch Backend & Frontend
# Terminal 1: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 (from backend/)
# Terminal 2: streamlit run .\frontend\app.py (from root)
```
