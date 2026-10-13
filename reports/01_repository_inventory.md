# AtmosIQ Audit — Phase 1: Repository Inventory

**Audit Date**: 2026-10-12  
**Auditor**: Senior Software Engineer / Production Readiness Auditor  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Executive Summary

A comprehensive, ground-truth inspection of the AtmosIQ repository was executed. Rather than trusting documentation or directory names, every directory, file, import path, schema, router, and agent module was analyzed directly from the filesystem.

Key structural findings:
1. **Entry Points**:
   - Frontend entry point: `frontend/app.py` (Streamlit dashboard, 665 lines).
   - Backend entry point: `backend/app/main.py` (FastAPI app, version 0.5.0).
2. **Disconnected / Orphaned Components**:
   - `backend/app/api/air_quality.py` implements `GET /api/v1/air-quality` via `get_current_air_quality` but is **never included in `main.py`**.
   - `backend/app/agents/air_quality_agent.py` contains a stub function `air_quality_source_status()` which is **never imported or called** in any agent or workflow.
   - `backend/app/services/india_aqi.py` implements CPCB AQI calculations and is tested in unit tests, but is **not integrated into any API router or agent graph**.
   - `backend/app/services/gemini_service.py` provides `generate_ai_response()` which is **completely dead code** (the agents use `weather_graph_llm.py` instead).
   - `backend/app/tools/weather_api.py` provides `get_weather_by_city()`, which is **never called anywhere in the active codebase**.
3. **Empty Architecture Stubs**:
   - `backend/app/core/` (empty directory)
   - `backend/app/rag/` (empty directory)
   - `backend/app/schemas/` (empty directory; request/response models are defined ad-hoc in `backend/app/api/chat.py`)
4. **Backup Files in Source Tree**:
   - Eleven `.backup` files reside directly in source directories:
     - `frontend/app.py.before_dashboard_fixes.backup`
     - `frontend/app.py.before_polish.backup`
     - `backend/app/agents/knowledge_agent.py.before_local_fallback.backup`
     - `backend/app/agents/supervisor.py.backup`
     - `backend/app/agents/supervisor.py.before_priority_fix.backup`
     - `backend/app/agents/weather_advice_agent.py.before_local_fallback.backup`
     - `backend/app/agents/weather_graph.py.before_advice_diagnostics.backup`
     - `backend/app/agents/weather_graph.py.before_error_handling.backup`
     - `backend/app/agents/weather_graph.py.before_forecast_format_fix.backup`
     - `backend/app/agents/weather_graph.py.before_forecast_routing.backup`
     - `backend/app/agents/weather_graph.py.before_weather_summary_fallback.backup`
5. **Git Status**:
   - The workspace root is **not a Git repository** (`fatal: not a git repository: .git`).
6. **Hardcoded Credentials**:
   - No hardcoded API keys or secrets were detected in tracked files or source code.
   - `.env` in `backend/` stores `GEMINI_API_KEY` and `ATMOSIQ_USE_GEMINI`.

---

## 2. Complete Inventory Matrix

| Component | Path | Role / Intended Function | Status | Evidence / Notes |
|---|---|---|---|---|
| **Frontend** | `frontend/app.py` | Streamlit user interface | ACTIVE | 665 lines; renders dashboard, metrics, charts, chat |
| **Frontend Backups** | `frontend/*.backup` | Previous revisions | UNUSED / DEBT | 2 backup files polluting frontend folder |
| **Frontend Deps** | `frontend/requirements.txt` | Frontend dependency list | DEFECTIVE | Contains only `streamlit`, `httpx`; missing `pandas` |
| **Backend Main** | `backend/app/main.py` | FastAPI application root | ACTIVE | Mounts `weather_router` and `chat_router`; defines `/` and `/health` |
| **Weather Router** | `backend/app/api/weather.py` | REST API for weather data | ACTIVE | Endpoints: `GET /api/v1/weather`, `GET /api/v1/weather/hourly`, `GET /api/v1/weather/daily` |
| **Chat Router** | `backend/app/api/chat.py` | REST API for conversational agent | ACTIVE | Endpoint: `POST /api/v1/chat`; embeds `ChatRequest` & `ChatResponse` |
| **Air Quality Router** | `backend/app/api/air_quality.py` | REST API for air quality | ORPHANED | Not mounted in `main.py`; unreachable by clients |
| **Core Module** | `backend/app/core/` | Configuration / Settings | EMPTY | Directory exists, contains no files |
| **RAG Module** | `backend/app/rag/` | Retrieval-Augmented Generation | EMPTY | Directory exists, contains no files |
| **Schemas Module** | `backend/app/schemas/` | Pydantic data schemas | EMPTY | Directory exists, contains no files; schemas defined inline |
| **Weather Graph** | `backend/app/agents/weather_graph.py` | LangGraph compiled workflow | ACTIVE | StateGraph with 7 nodes, 2 conditional edges |
| **Supervisor Agent** | `backend/app/agents/supervisor.py` | Intent classification & routing | ACTIVE | LLM classification with keyword fallback |
| **Current Weather Agent** | `backend/app/agents/current_weather_agent.py` | Specialist for current weather | ACTIVE | Calls `resolve_city` & `get_current_weather` |
| **Forecast Agent** | `backend/app/agents/forecast_agent.py` | Specialist for hourly/daily forecasts | ACTIVE | Calls `get_daily_forecast` / `get_hourly_forecast` |
| **Weather Advice Agent** | `backend/app/agents/weather_advice_agent.py` | Specialist for clothing & activity advice | ACTIVE | LLM advice generation with deterministic fallback |
| **Knowledge Agent** | `backend/app/agents/knowledge_agent.py` | Specialist for weather concepts | ACTIVE | LLM science explanations with keyword fallback |
| **Air Quality Agent** | `backend/app/agents/air_quality_agent.py` | Specialist for AQI queries | DEAD CODE | Not hooked into graph; graph uses inline `answer_air_quality_unavailable` |
| **Weather Graph LLM** | `backend/app/agents/weather_graph_llm.py` | LangChain ChatGoogleGenerativeAI factory | ACTIVE / MISCONFIG | Uses non-existent model name `"gemini-3.8-flash"` |
| **Gemini Service** | `backend/app/services/gemini_service.py` | Google GenAI SDK wrapper | DEAD CODE | Never imported; also specifies `"gemini-3.8-flash"` |
| **India AQI Service** | `backend/app/services/india_aqi.py` | CPCB AQI breakpoint calculation | ISOLATED / DEFECT | Tested in unit tests, but breakpoint intervals have float gaps; not wired to API |
| **Air Quality Service** | `backend/app/services/air_quality_api.py` | Open-Meteo Air Quality HTTP client | UNUSED IN PROD | Only imported by unmounted `api/air_quality.py` |
| **Weather Interpreter** | `backend/app/services/weather_interpreter.py` | WMO codes & weather advice strings | ACTIVE | Maps WMO codes 0–99; generates rule-based advice |
| **Weather API Tool** | `backend/app/tools/weather_api.py` | Open-Meteo geocoding & forecast client | ACTIVE | `geocode_location`, `get_current_weather`, `get_hourly_forecast`, `get_daily_forecast` |
| **Unit Tests** | `backend/tests/` | Pytest test suite | ACTIVE | 4 test files, 50 passing test cases |
| **Training Data / Scripts** | `data/training/` | Intent routing dataset & eval | SEMI-ACTIVE | `evaluate_supervisor.py` tests keyword routing; 90 synthetic examples |

---

## 3. Discovered Anomalies, Dead Code, and Risks

1. **Dead / Unused Functions**:
   - `gemini_service.py:generate_ai_response()`: 0 references across the codebase.
   - `air_quality_agent.py:air_quality_source_status()`: 0 references across the codebase.
   - `weather_api.py:get_weather_by_city()`: 0 references across the codebase.
2. **Unmounted Router**:
   - `backend/app/api/air_quality.py` defines router `router = APIRouter(prefix="/api/v1/air-quality")`, but `backend/app/main.py` only mounts `weather_router` and `chat_router`.
3. **Invalid Model String**:
   - Both `backend/app/services/gemini_service.py` (line 10) and `backend/app/agents/weather_graph_llm.py` (line 31) specify:
     ```python
     MODEL_NAME = "gemini-3.8-flash"
     ```
     Google Gemini has no model named `gemini-3.8-flash`. If Gemini were enabled, initialization or inference would immediately fail with model not found.
4. **India AQI Discontinuity Defect**:
   - `india_aqi.py:BREAKPOINTS` defines integer-bounded tuples such as `(0, 30)` followed by `(31, 60)`. Any real-world decimal measurement between 30.0 and 31.0 (e.g. 30.5 µg/m³) throws an unhandled `ValueError` rather than interpolating.
5. **Swallowed Exceptions in Chat Flow**:
   - In `backend/app/api/chat.py`, any exception in `weather_graph.ainvoke()` triggers a generic HTTP 502 with message `"The AtmosIQ agent workflow failed."`. Location not found (`LookupError`) and validation errors (`ValueError`) are obscured from the client.
6. **Accumulation of Backup Files**:
   - Nine `.backup` files in `backend/app/agents/` and two in `frontend/` pose a risk of accidental inclusion, confusion during maintenance, and Git clutter.
