# AtmosIQ Audit — Phase 6: India AQI and Air-Quality Safety Audit

**Audit Date**: 2026-10-12  
**Auditor**: Environmental Data Engineer / QA Automation Engineer  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Executive Summary

AtmosIQ includes an India-specific Air Quality Index (AQI) calculation module in `backend/app/services/india_aqi.py` based on Central Pollution Control Board (CPCB) concentration breakpoints.

A dual audit was conducted:
1. **Mathematical & Algorithmic Correctness**: Testing interpolation formulas, boundary values, decimal inputs, and dominant pollutant selection.
2. **Operational Safety & Grounding**: Testing whether the conversational assistant refuses to fabricate live AQI when no verified live data provider is connected.

**Key Findings**:
- **Critical Calculation Defect**: The breakpoint table `BREAKPOINTS` contains integer intervals with gaps between bounds (e.g. `(0, 30)` followed by `(31, 60)`). Any real-world decimal measurement falling in the gap (such as PM2.5 = 30.5 µg/m³ or PM10 = 50.5 µg/m³) raises an unhandled `ValueError`.
- **Operational Safety Verified**: The conversational agent correctly refuses to invent or hallucinate live AQI measurements, returning: *"AtmosIQ's air-quality data provider is not configured yet, so I can't provide a verified live AQI reading."*
- **Module Isolation**: `calculate_india_aqi()` is tested in unit tests, but is **never invoked** by any active REST API endpoint or agent in production.

---

## 2. Breakpoint Verification & Decimal Gap Analysis

### Tested Pollutants and CPCB Breakpoint Bands

| Pollutant | Documented Units | CPCB Concentration Bands | AtmosIQ Implementation | Decimal Values Tested | Result |
|---|---|---|---|---|---|
| **PM2.5** | µg/m³ (24h avg) | 0–30, 31–60, 61–90, 91–120, 121–250, 250+ | `(0, 30), (31, 60), ...` | 30.0, **30.5**, 60.0, **60.5** | **FAIL**: 30.5 & 60.5 raise `ValueError` |
| **PM10** | µg/m³ (24h avg) | 0–50, 51–100, 101–250, 251–350, 351–430, 430+ | `(0, 50), (51, 100), ...` | 50.0, **50.5**, 100.0, **100.5** | **FAIL**: 50.5 & 100.5 raise `ValueError` |
| **NO2** | µg/m³ (24h avg) | 0–40, 41–80, 81–180, 181–280, 281–400, 400+ | `(0, 40), (41, 80), ...` | 40.0, **40.5**, 80.0 | **FAIL**: 40.5 raises `ValueError` |
| **SO2** | µg/m³ (24h avg) | 0–40, 41–80, 81–380, 381–800, 801–1600, 1600+ | `(0, 40), (41, 80), ...` | 40.0, **40.5** | **FAIL**: 40.5 raises `ValueError` |
| **O3** | µg/m³ (8h avg) | 0–50, 51–100, 101–168, 169–208, 209–748, 748+ | `(0, 50), (51, 100), ...` | 50.0, **50.5**, 168.0, **168.5** | **FAIL**: 50.5 & 168.5 raise `ValueError` |
| **CO** | mg/m³ (8h avg) | 0–1.0, 1.1–2.0, 2.1–10, 10.1–17, 17.1–34, 34+ | `(0, 1.0), (1.1, 2.0), ...` | 1.0, **1.05**, 2.0, **2.05** | **FAIL**: 1.05 & 2.05 raise `ValueError` |

### Concrete Defect Reproduction Evidence
```python
>>> calculate_sub_index("pm2_5", 30.5)
ValueError: Concentration 30.5 does not fit a breakpoint for pm2_5. Check the concentration and units.

>>> calculate_sub_index("pm10", 50.5)
ValueError: Concentration 50.5 does not fit a breakpoint for pm10. Check the concentration and units.

>>> calculate_sub_index("carbon_monoxide_8h", 1.05)
ValueError: Concentration 1.05 does not fit a breakpoint for carbon_monoxide_8h. Check the concentration and units.
```

**Root Cause**:
In `backend/app/services/india_aqi.py`:
```python
for low_c, high_c, low_i, high_i in BREAKPOINTS[pollutant]:
    if low_c <= concentration <= high_c:
...
```
Because `high_c` of band 1 is `30` and `low_c` of band 2 is `31`, any real number `30.0 < concentration < 31.0` satisfies neither condition and falls through to raise a `ValueError`.

---

## 3. CPCB Algorithm Rules Compliance

| Rule / Requirement | Expected Behavior | Observed Behavior | Verdict |
|---|---|---|---|
| **Sub-Index Interpolation** | Linear interpolation formula: $I = \frac{I_{hi} - I_{lo}}{C_{hi} - C_{lo}} \times (C - C_{lo}) + I_{lo}$ | Correct formula with rounding: `floor(value + 0.5)` | **PASS** |
| **Dominant Pollutant** | AQI = $\max(\text{sub-indices})$ | Correctly returns maximum sub-index | **PASS** |
| **Minimum Pollutants** | Must have at least 3 pollutants | Returns `status: "insufficient_pollutant_data"` if $< 3$ | **PASS** |
| **Particulate Requirement** | At least one particulate (PM2.5 or PM10) required | Returns `status: "insufficient_pollutant_data"` if neither PM2.5 nor PM10 present | **PASS** |
| **Negative Inputs** | Concentration $< 0$ rejected | Raises `ValueError: Concentration cannot be negative.` | **PASS** |
| **Non-finite Inputs** | `NaN`, $\pm\infty$, `True` rejected | Raises `ValueError: Concentration must be a finite number.` | **PASS** |
| **Category Mapping** | 0–50: Good, 51–100: Satisfactory, 101–200: Moderate, 201–300: Poor, 301–400: Very Poor, 401–500: Severe | Verified exact matches for all boundary indices 0 to 500 | **PASS** |

---

## 4. Air-Quality Safety & Live Provider Status

### Distinction between Calculation Engine vs Live Provider
- `india_aqi.py` is a **pure calculation engine**. It computes provisional AQI given valid concentration inputs with appropriate 24-hour and 8-hour averaging periods.
- Open-Meteo Air Quality API (`air_quality_api.py`) provides instantaneous model-based concentrations (µg/m³), not official 24-hour CPCB monitoring station averages.

### Safety Behavior in Conversational Assistant
When a user asks:
- *"What is the current AQI in Delhi?"*
- *"Are PM2.5 levels high in Mumbai?"*
- *"Can I breathe outdoor air safely in Kolkata?"*

The system executes `answer_air_quality_unavailable()` in `backend/app/agents/weather_graph.py`:
```json
{
  "weather": {},
  "answer": "AtmosIQ's air-quality data provider is not configured yet, so I can't provide a verified live AQI reading."
}
```
**Safety Verdict: PASS**. The application never invents or hallucinates hazardous air quality numbers.
