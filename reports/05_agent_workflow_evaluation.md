# AtmosIQ Audit — Phase 5: LangGraph and Agent Workflow Evaluation

**Audit Date**: 2026-10-12  
**Auditor**: AI/ML Engineer / QA Automation Engineer  
**Workspace Root**: `C:\Users\Lenovo\Desktop\my personal Projects\AtmosIQ`  
**Status**: COMPLETE (Evidence-Verified)

---

## 1. Executive Summary & Graph Architecture

The AtmosIQ conversational core is implemented as a compiled LangGraph `StateGraph` in `backend/app/agents/weather_graph.py`.

```text
               +---------------+
               |    [START]    |
               +-------+-------+
                       |
                       v
               +---------------+
               |  supervisor   | (Intent Classification)
               +-------+-------+
                       |
       +---------------+---------------+---------------+
       | (forecast)    | (current/adv) | (knowledge)   | (air_quality)
       v               v               v               v
+--------------+ +--------------+ +-------------+ +--------------------+
|retrieve_     | |retrieve_     | |answer_      | |answer_air_quality_ |
|forecast      | |weather       | |knowledge    | |unavailable         |
+------+-------+ +------+-------+ +-----+-------+ +---------+----------+
       |                |               |                   |
       |         +------+------+        |                   |
       |         | (advice)    | (cur)  |                   |
       |         v             v        |                   |
       |  +-------------+ +----------+  |                   |
       |  |answer_      | |answer_   |  |                   |
       |  |weather_adv  | |with_weath|  |                   |
       |  +------+------+ +----+-----+  |                   |
       |         |             |        |                   |
       v         v             v        v                   v
     +--------------------------------------------------------+
     |                         [END]                          |
     +--------------------------------------------------------+
```

### Architectural Audit Findings
1. **Routing Asymmetry**:
   - `choose_route()` routes `forecast` to `retrieve_forecast`, but `retrieve_forecast` has a fixed edge to `answer_with_weather`. It **cannot** route to `answer_weather_advice`. If a user asks for advice about tomorrow's weather (*"What should I wear tomorrow?"*), either:
     - Supervisor routes to `weather_advice`, which triggers `retrieve_weather` (current weather only), or
     - Supervisor routes to `forecast`, which triggers `answer_with_weather` (forecast list without specific clothing advice).
2. **India-First Geocoding Trap**:
   - Geocoding `"Goa"` via `tools/weather_api.py` resolved to `"Genoa"` (Italy) because `count=1` and no country code filter (`country_code="IN"`) was applied.
3. **Keyword Fallback Blind Spot**:
   - In local mode, requests that fail exact substring matching fall through to `knowledge`. Misspelled queries (e.g. `"temprature"`) or reordered phrases fall through to science knowledge explanations instead of reporting location or weather status.

---

## 2. Held-Out Evaluation Dataset Methodology

The previous synthetic 90/90 score reported in `data/training/supervisor_evaluation_report.json` was an overfitted evaluation on synthetic phrases matching exact substrings in `supervisor.py`.

To measure true performance, a new held-out evaluation dataset of 50 diverse queries was constructed and tested across both the routing supervisor and full end-to-end graph execution (`weather_graph.ainvoke`):
- Direct requests (20 queries)
- Conversational / natural phrasing (18 queries)
- Real-world typos (2 queries)
- Out-of-domain requests (2 queries)
- Science knowledge requests (8 queries)

---

## 3. Evaluation Metrics

| Metric | Measured Value | Standard Target | Assessment |
|---|---|---|---|
| **Intent-Routing Accuracy** | **94.00%** (47/50) | ≥ 90.0% | PASS |
| **Workflow Completion Rate** | **100.00%** (50/50) | 100.0% | PASS (0 uncaught graph crashes) |
| **Unsupported Claim Rate** | **0.00%** (0/50) | 0.0% | PASS (All answers grounded in retrieved state) |
| **Tool/API Success Rate** | **100.00%** (50/50) | ≥ 98.0% | PASS |

### Per-Class Performance Matrix

| Intent Class | Samples | True Positives | Predicted | Precision | Recall | F1-Score |
|---|---|---|---|---|---|---|
| **forecast** | 10 | 10 | 10 | **1.0000** | **1.0000** | **1.0000** |
| **current_weather** | 10 | 9 | 9 | **1.0000** | **0.9000** | **0.9474** |
| **weather_advice** | 10 | 9 | 9 | **1.0000** | **0.9000** | **0.9474** |
| **air_quality** | 10 | 9 | 9 | **1.0000** | **0.9000** | **0.9474** |
| **knowledge** | 10 | 10 | 13 | **0.7692** | **1.0000** | **0.8696** |
| **Overall (Macro)** | **50** | **47** | **50** | **0.9538** | **0.9400** | **0.9429** |

---

## 4. Confusion Matrix

| Actual \ Predicted | `current_weather` | `forecast` | `weather_advice` | `air_quality` | `knowledge` (Fallback) |
|---|---|---|---|---|---|
| **`current_weather`** | **9** | 0 | 0 | 0 | 1 |
| **`forecast`** | 0 | **10** | 0 | 0 | 0 |
| **`weather_advice`** | 0 | 0 | **9** | 0 | 1 |
| **`air_quality`** | 0 | 0 | 0 | **9** | 1 |
| **`knowledge`** | 0 | 0 | 0 | 0 | **10** |

---

## 5. Detailed Failure Case Analysis

Three queries were misclassified, each falling into the default `knowledge` route:

1. **Failure Case 1 (Typo in query)**:
   - *Text*: `"current temprature in Mumbai"`
   - *Expected*: `current_weather` | *Predicted*: `knowledge`
   - *Cause*: Typo `"temprature"` bypassed substring check `"temperature in"`. Keyword matching lacks levenshtein distance or fuzzy tokenization.
2. **Failure Case 2 (Phrasing permutation in advice)**:
   - *Text*: `"Should I wear a jacket if I go out in Manali?"`
   - *Expected*: `weather_advice` | *Predicted*: `knowledge`
   - *Cause*: `supervisor.py` includes `"take a jacket"` and `"carry a jacket"`, but omitted `"wear a jacket"` and `"should i wear"`.
3. **Failure Case 3 (Word order variation in AQI)**:
   - *Text*: `"Can I breathe outdoor air safely in Kanpur today?"`
   - *Expected*: `air_quality` | *Predicted*: `knowledge`
   - *Cause*: `supervisor.py` matches `"air safe to breathe"` and `"breathing outdoor air"`, but not `"breathe outdoor air safely"`.
