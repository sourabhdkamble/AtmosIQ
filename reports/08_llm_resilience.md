# AtmosIQ Audit — Phase 8: Gemini, Local Fallback, and LLM Resilience Audit

**Audit Date**: 2026-10-12  
**Auditor**: Senior AI/ML Engineer / Reliability Auditor  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Executive Summary

AtmosIQ is architected with a hybrid AI approach: it attempts to use Google Gemini LLMs for natural language routing, conversational synthesis, and advice, with a complete deterministic local fallback layer across all four operational agents.

**Key Findings**:
- **Local Fallback Resilience Verified**: When Gemini is disabled, times out, throws quota errors (429), or outputs malformed text, every single agent cleanly catches the failure and delegates to deterministic local logic without crashing.
- **Model Name Misconfiguration**: Both `weather_graph_llm.py` (line 31) and `gemini_service.py` (line 10) specify `MODEL_NAME = "gemini-3.8-flash"`. This model does not exist in Google's catalog; if Gemini were enabled, API calls would fail with a 404 Model Not Found error.
- **Quota Safety**: The application does not loop or retry unbounded on 429 quota exhaustion. When an LLM exception occurs, the failure is caught, logged once as a warning, and immediately handed off to local summarizers.

---

## 2. LLM Configuration & Lifecycle Audit

| Parameter / Feature | Code Location | Observed Setting | Risk Level | Evaluation Verdict |
|---|---|---|---|---|
| `ATMOSIQ_USE_GEMINI` | `weather_graph_llm.py:13` | `"false"` in `.env` | Low | PASS. Default is safely offline; no unexpected billing or quota hits. |
| `GEMINI_API_KEY` | `weather_graph_llm.py:23` | Read via `os.getenv` | Low | PASS. Key is not printed in logs or exposed in exceptions. |
| `MODEL_NAME` | `weather_graph_llm.py:31` | `"gemini-3.8-flash"` | **HIGH** | **FAIL (Defect)**: Non-existent model string. Must be `gemini-1.5-flash` or `gemini-2.0-flash`. |
| `temperature` | `weather_graph_llm.py:33` | `0` | Low | PASS. Low temperature ensures low variance and consistent JSON output. |
| `Dead SDK Service` | `services/gemini_service.py` | Standalone client | Low | DEAD CODE. Uses `google.genai` SDK directly but is never imported by any agent. |

---

## 3. Failure Mode & Resilience Test Matrix

The local fallback architecture was tested under simulated edge cases:

| Failure Mode | Injected Condition | Agent Tested | Expected Behavior | Actual Observed Outcome | Verdict |
|---|---|---|---|---|---|
| **Disabled Flag** | `ATMOSIQ_USE_GEMINI=false` | All agents | Raise `RuntimeError`, use local fallback | Caught; 100% of queries answered via local fallback | **PASS** |
| **Quota Exhaustion** | 429 `ResourceExhausted` | Supervisor | Fallback to keyword classification | Cleanly routed `"forecast"` with zero crash | **PASS** |
| **Malformed JSON** | Invalid markdown / non-JSON | Supervisor | Fallback to keyword classification | Regex/JSON decode caught; routed `"current_weather"` | **PASS** |
| **Empty LLM Body** | Response text is `""` / `None` | Weather Advice Agent | Fallback to rule-based advice | Generated practical clothing/hydration advice | **PASS** |
| **API Timeout** | `TimeoutError` (network hang) | Knowledge Agent | Fallback to scientific explanations | Returned local humidity explanation | **PASS** |
| **Hallucination Prevention** | Local mode generation | Weather Graph | Ground strictly in retrieved numbers | 0.0% unsupported claims; rain probabilities labeled estimates | **PASS** |

---

## 4. Remediation Recommendations

1. **Update Model Name**:
   Change `gemini-3.8-flash` in `backend/app/agents/weather_graph_llm.py` and `backend/app/services/gemini_service.py` to a valid model identifier such as `gemini-1.5-flash` or `gemini-2.0-flash` with a configurable environment variable `ATMOSIQ_GEMINI_MODEL`.
2. **Remove or Unify Dead Code**:
   Remove or integrate `backend/app/services/gemini_service.py` to avoid parallel SDK dependencies (`google-genai` vs `langchain-google-genai`).
