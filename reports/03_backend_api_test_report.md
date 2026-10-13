# AtmosIQ Audit — Phase 3: Backend Unit and API Test Report

**Audit Date**: 2026-10-12  
**Auditor**: Senior QA Automation Engineer / Backend Engineer  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Baseline Pytest Verification

The existing unit test suite was executed in the project virtual environment:
```powershell
& ..\.venv\Scripts\python.exe -m pytest -v -p no:cacheprovider
```

**Results**:
- **Collected**: 50 items
- **Passed**: 50 items (100%)
- **Failed**: 0 items
- **Execution Time**: 1.00s – 1.25s
- **Breakdown**:
  - `tests/test_agent_routing.py`: 10 passed (keyword routes)
  - `tests/test_india_aqi.py`: 28 passed (CPCB categories, interpolation, invalid concentration handling)
  - `tests/test_weather_api.py`: 4 passed (geocoding, parameter bounds)
  - `tests/test_weather_interpreter.py`: 8 passed (WMO codes, advice generation)

---

## 2. Comprehensive FastAPI Endpoint Audit

The live ASGI application `app.main:app` was tested using `httpx.AsyncClient` with `ASGITransport`.

### Endpoint Results Summary

| Endpoint | Method | Scenario Tested | HTTP Status | Response Verdict | Evidence / Observed Output |
|---|---|---|---|---|---|
| `/` | `GET` | Root health ping | `200 OK` | PASS | `{"app": "AtmosIQ", "message": "Weather bot is running!", "status": "healthy"}` |
| `/health` | `GET` | Health monitoring | `200 OK` | PASS | `{"status": "ok", "service": "atmosiq-weather-backend"}` |
| `/api/v1/weather` | `GET` | Valid city (`Mumbai`) | `200 OK` | PASS | Complete payload with `location`, `current_weather`, units, advice |
| `/api/v1/weather` | `GET` | Missing `city` query param | `422 Unprocessable` | PASS | FastApi validation: `Field required` |
| `/api/v1/weather` | `GET` | Empty `city=""` | `422 Unprocessable` | PASS | Pydantic `min_length=1` violation |
| `/api/v1/weather` | `GET` | Whitespace `city="   "` | `400 Bad Request` | PASS | Handled in `weather_api.py`: `"City name cannot be empty."` |
| `/api/v1/weather` | `GET` | Non-existent location | `404 Not Found` | PASS | `"No location found for 'NonExistentCityXYZ123456'."` |
| `/api/v1/weather` | `GET` | Geocoding timeout | `504 Gateway Timeout` | PASS | Handled: `{"detail": "Geocoding timed out."}` |
| `/api/v1/weather` | `GET` | Weather provider 502 | `502 Bad Gateway` | PASS | Handled: `{"detail": "Weather provider error."}` |
| `/api/v1/weather/hourly` | `GET` | Boundary: `hours=0` | `422 Unprocessable` | PASS | Query validation `ge=1` |
| `/api/v1/weather/hourly` | `GET` | Boundary: `hours=49` | `422 Unprocessable` | PASS | Query validation `le=48` |
| `/api/v1/weather/hourly` | `GET` | Empty upstream response | `422 Unprocessable` | **FAIL (Defect)** | Maps upstream `ValueError` to `422` instead of `502 Bad Gateway` |
| `/api/v1/weather/daily` | `GET` | Boundary: `days=0` | `422 Unprocessable` | PASS | Query validation `ge=1` |
| `/api/v1/weather/daily` | `GET` | Boundary: `days=17` | `422 Unprocessable` | PASS | Query validation `le=16` |
| `/api/v1/weather/daily` | `GET` | Empty upstream response | `422 Unprocessable` | **FAIL (Defect)** | Maps upstream `ValueError` to `422` instead of `502 Bad Gateway` |
| `/api/v1/chat` | `POST` | Missing `message` body | `422 Unprocessable` | PASS | Body validation error |
| `/api/v1/chat` | `POST` | Empty `city=""` | `422 Unprocessable` | PASS | Pydantic `min_length=1` validation |
| `/api/v1/chat` | `POST` | Malformed JSON body | `422 Unprocessable` | PASS | JSON decode error handled |
| `/api/v1/chat` | `POST` | Invalid city in chat | `200 OK` | PASS (Conversational) | State machine catches geocoding failure and returns user-friendly answer |
| `/api/v1/chat` | `POST` | Weather concept query | `200 OK` | PASS | Correct local knowledge explanation returned |
| `/api/v1/air-quality` | `GET` | Air quality check | `404 Not Found` | **FAIL (Defect)** | Route exists in `app/api/air_quality.py` but is **not registered in `app/main.py`** |

---

## 3. Discovered Backend Defect Details

### Defect 1: Inconsistent Upstream Error Status Code in Forecast Endpoints
- **Location**: `backend/app/api/weather.py`, lines 113–114 (`hourly_weather`) and lines 150–151 (`daily_weather`).
- **Code**:
  ```python
  except ValueError as exc:
      raise HTTPException(status_code=422, detail=str(exc)) from exc
  ```
- **Analysis**:
  When `tools/weather_api.py` detects an empty or invalid payload from the upstream provider (`"The provider returned no hourly forecast."`), it raises `ValueError`.
  In `current_weather`, line 90–91 correctly maps this to HTTP 502:
  ```python
  except ValueError as exc:
      raise HTTPException(status_code=502, detail=str(exc)) from exc
  ```
  However, in `hourly_weather` and `daily_weather`, it is mapped to HTTP 422. HTTP 422 indicates an unprocessable client request, whereas this is an upstream service error (502).

### Defect 2: Missing Router Registration for Air Quality
- **Location**: `backend/app/main.py`, lines 13–14.
- **Code**:
  ```python
  app.include_router(weather_router)
  app.include_router(chat_router)
  ```
- **Analysis**:
  `backend/app/api/air_quality.py` is fully implemented with error handlers for geocoding and air-quality fetching, but was omitted from `main.py`. As a result, all requests to `/api/v1/air-quality` return a 404 Not Found.

### Defect 3: Non-existent City in Conversational Chat Swallows Intent
- **Location**: `backend/app/agents/supervisor.py` & `backend/app/agents/weather_graph.py`.
- **Analysis**:
  When a user submits `"What is the weather?"` with a city name, because the keyword `"weather"` alone is not in `supervisor.py:route_with_keywords`, it falls back to `knowledge`. The knowledge agent does not validate or check the city.
