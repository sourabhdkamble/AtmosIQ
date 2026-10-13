import os
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AtmosIQ | Weather Intelligence",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --cyan: #43dcff;
        --blue: #4388ff;
        --violet: #9c82ff;
        --text: #f4f7ff;
        --muted: #9cafd0;
        --border: rgba(105, 158, 255, .23);
    }

    .stApp {
        background:
            radial-gradient(ellipse at 82% 0%, rgba(62, 77, 190, .22), transparent 38%),
            radial-gradient(ellipse at 0% 50%, rgba(0, 192, 255, .07), transparent 35%),
            linear-gradient(145deg, #050918 0%, #0b1730 55%, #071126 100%);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(5, 9, 24, .88);
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1600px;
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #071329, #0b1b39 65%, #061027);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] h2 {
        color: white;
        letter-spacing: -.5px;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--muted);
    }

    h1, h2, h3 {
        color: #f6f8ff;
        letter-spacing: -.5px;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 30px 32px;
        border-radius: 24px;
        background:
            radial-gradient(ellipse at 90% 0%, rgba(113, 106, 255, .28), transparent 42%),
            linear-gradient(120deg, #111e50 0%, #124271 54%, #07596f 100%);
        border: 1px solid rgba(100, 177, 255, .38);
        box-shadow: 0 18px 55px rgba(0, 0, 0, .24);
        margin-bottom: 26px;
    }

    .hero h1 {
        color: #fff;
        margin: 0 0 8px;
        font-size: clamp(2rem, 3.5vw, 3rem);
        font-weight: 800;
        letter-spacing: -1.5px;
    }

    .hero p {
        color: #d1e7ff;
        margin: 4px 0;
        font-size: 1rem;
    }

    .eyebrow {
        color: var(--cyan);
        font-size: .76rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .section-title {
        color: #f5f8ff;
        font-size: 1.4rem;
        font-weight: 750;
        margin: 16px 0 10px;
    }

    .weather-summary {
        background: linear-gradient(125deg, rgba(22, 43, 83, .92), rgba(10, 26, 52, .95));
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 24px 26px;
        margin: 12px 0 18px;
        box-shadow: 0 12px 35px rgba(0, 0, 0, .15);
    }

    .weather-location {
        color: #b8ccef;
        font-size: 1rem;
        font-weight: 600;
    }

    .weather-temp {
        color: #fff;
        font-size: clamp(3rem, 6vw, 5rem);
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -3px;
        margin: 10px 0;
    }

    .weather-condition {
        color: var(--cyan);
        font-size: 1.12rem;
        font-weight: 650;
    }

    .weather-detail {
        color: #aebfdd;
        font-size: .92rem;
        margin-top: 8px;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(24, 43, 78, .95), rgba(10, 24, 48, .97));
        border: 1px solid var(--border);
        border-radius: 17px;
        padding: 18px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, .14);
        transition: border-color .18s ease, transform .18s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(67, 220, 255, .58);
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] {
        color: #a9c0e8 !important;
        font-size: .9rem;
    }

    [data-testid="stMetricValue"] {
        color: #fff !important;
        font-size: clamp(1.35rem, 2vw, 2rem);
        font-weight: 750;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, rgba(19, 37, 70, .88), rgba(9, 21, 43, .96));
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, .12);
    }

    .forecast-time {
        color: #a8c0ed;
        font-size: .86rem;
        font-weight: 650;
    }

    .forecast-temperature {
        color: #fff;
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -.5px;
    }

    .forecast-description {
        color: #a9bbd8;
        font-size: .9rem;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid var(--border);
    }

    [data-testid="stTabs"] button[data-baseweb="tab"] {
        color: #a9bbd8;
        border-radius: 10px 10px 0 0;
        padding: 12px 16px;
        font-weight: 650;
    }

    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--cyan);
        border-bottom: 2px solid var(--cyan);
    }

    div.stButton > button {
        background: rgba(23, 43, 80, .92);
        border: 1px solid rgba(100, 153, 255, .35);
        border-radius: 11px;
        color: #eef6ff;
        font-weight: 650;
        transition: all .18s ease;
    }

    div.stButton > button:hover {
        border-color: var(--cyan);
        background: rgba(24, 72, 122, .96);
        color: white;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(105deg, #078fc7, #315fe8);
        border: 1px solid rgba(107, 211, 255, .65);
        color: white;
        box-shadow: 0 7px 22px rgba(28, 118, 232, .22);
    }

    [data-testid="stTextInput"] input,
    [data-testid="stChatInput"] textarea {
        background: rgba(7, 17, 37, .95) !important;
        color: #f4f7ff !important;
        border: 1px solid rgba(91, 150, 255, .32) !important;
        border-radius: 12px !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--cyan) !important;
        box-shadow: 0 0 0 1px rgba(67, 217, 255, .24) !important;
    }

    [data-testid="stChatMessage"] {
        background: rgba(15, 30, 58, .76);
        border: 1px solid rgba(91, 150, 255, .18);
        border-radius: 16px;
        padding: 14px;
        margin-bottom: 10px;
    }

    [data-testid="stAlert"] {
        background: linear-gradient(110deg, rgba(16, 65, 115, .78), rgba(18, 42, 83, .88));
        border: 1px solid rgba(67, 217, 255, .27);
        border-radius: 14px;
        color: #dff7ff;
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: 13px;
        background: rgba(12, 25, 49, .72);
    }

    hr {
        border-color: rgba(111, 145, 202, .22) !important;
    }

    ::-webkit-scrollbar { width: 9px; height: 9px; }
    ::-webkit-scrollbar-track { background: #071126; }
    ::-webkit-scrollbar-thumb { background: #284a7b; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #3879b8; }

    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem .8rem 2rem;
        }
        .hero { padding: 22px 20px; border-radius: 18px; }
        .hero h1 { font-size: 2rem; }
        .weather-summary { padding: 20px; }
        [data-testid="stMetric"] { padding: 12px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_value(data, *keys, default=None):
    if not isinstance(data, dict):
        return default
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return default


def display_value(value, suffix=""):
    if value is None:
        return "—"
    if isinstance(value, (float, int)):
        value = round(value, 1)
    return f"{value}{suffix}"


def format_timestamp(value, include_date=False):
    if not value:
        return "Time unavailable"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if include_date:
            return parsed.strftime("%a, %d %b")
        return parsed.strftime("%I:%M %p").lstrip("0")
    except (ValueError, TypeError):
        return str(value)


def api_get(base_url, path, params=None):
    response = httpx.get(
        f"{base_url.rstrip('/')}{path}",
        params=params,
        timeout=25.0,
    )
    response.raise_for_status()
    return response.json()


def api_post(base_url, path, payload):
    response = httpx.post(
        f"{base_url.rstrip('/')}{path}",
        json=payload,
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()


def show_api_error(error):
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        try:
            detail = error.response.json().get("detail", "")
        except Exception:
            detail = ""
        st.error(f"Backend error ({status}): {detail}" if detail else f"The backend returned HTTP {status}.")
    elif isinstance(error, httpx.TimeoutException):
        st.error("The request timed out. Please try again.")
    elif isinstance(error, httpx.RequestError):
        st.error("Cannot reach the backend. Start FastAPI and check the backend URL in the sidebar.")
    else:
        st.error("Something went wrong while processing this request.")


def weather_emoji(description):
    text = str(description or "").lower()
    if "thunder" in text or "storm" in text:
        return "⛈️"
    if "snow" in text:
        return "❄️"
    if "rain" in text or "drizzle" in text:
        return "🌧️"
    if "fog" in text or "mist" in text:
        return "🌫️"
    if "overcast" in text or "cloud" in text:
        return "☁️"
    if "clear" in text or "sun" in text:
        return "☀️"
    return "🌤️"


# Sidebar
with st.sidebar:
    st.markdown("## 🌌 AtmosIQ")
    st.caption("WEATHER INTELLIGENCE")
    st.divider()

    city = st.text_input(
        "Your city",
        value=st.session_state.get("city", "Mumbai"),
        max_chars=100,
        help="Enter a city, for example Mumbai or Panvel.",
    ).strip()

    api_url = st.text_input(
        "Backend URL",
        value=os.getenv("ATMOSIQ_API_URL", DEFAULT_API_URL),
        help="Address of your running FastAPI backend.",
    ).strip().rstrip("/")

    refresh = st.button("↻ Refresh weather", type="primary", use_container_width=True)

    st.divider()
    st.caption("◉ WEATHER SOURCE")
    st.markdown("**Open-Meteo**")
    st.caption("◉ ASSISTANT")
    st.markdown("**AtmosIQ agents**")
    st.divider()
    st.caption("MIDNIGHT EDITION · LOCAL")

if "city" not in st.session_state:
    st.session_state.city = city

city_changed = st.session_state.get("loaded_city") != city
api_changed = st.session_state.get("loaded_api_url") != api_url

if refresh or city_changed or api_changed:
    st.session_state.city = city
    for key in ("current_weather_data", "hourly_data", "daily_data"):
        st.session_state.pop(key, None)

if not city:
    st.warning("Enter a city in the sidebar to continue.")
    st.stop()

if not api_url.startswith(("http://", "https://")):
    st.error("The backend URL must begin with http:// or https://.")
    st.stop()

# Header
st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">WEATHER · INSIGHTS · EVERY DAY</div>
        <h1>🌌 AtmosIQ</h1>
        <p>Your weather, your plans, your intelligent assistant.</p>
        <p>📍 {city} &nbsp; · &nbsp; Live weather intelligence</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Retrieve current conditions
if "current_weather_data" not in st.session_state:
    try:
        with st.spinner(f"Getting current weather for {city}..."):
            st.session_state.current_weather_data = api_get(
                api_url, "/api/v1/weather", {"city": city}
            )
            st.session_state.loaded_city = city
            st.session_state.loaded_api_url = api_url
    except Exception as error:
        show_api_error(error)
        st.session_state.current_weather_data = {}

current_payload = st.session_state.current_weather_data
current = current_payload.get("current_weather", {})
location = current_payload.get("location", {})
location_name = get_value(location, "name", default=city)
description = get_value(current, "description", default="Current conditions")
temperature = get_value(current, "temperature_c", "temperature")
feels_like = get_value(current, "feels_like_c", "apparent_temperature_c", "apparent_temperature")
humidity = get_value(current, "humidity_percent", "relative_humidity", "humidity")
wind = get_value(current, "wind_speed_kmh", "wind_speed")
rain = get_value(current, "precipitation_mm", "rain_mm")
advice = get_value(current, "advice")

# Current weather hero card
st.markdown(
    f"""
    <div class="weather-summary">
        <div class="weather-location">📍 {location_name}</div>
        <div class="weather-temp">{display_value(temperature, "°C")}</div>
        <div class="weather-condition">{weather_emoji(description)} &nbsp; {description}</div>
        <div class="weather-detail">
            Feels like {display_value(feels_like, "°C")}
            &nbsp; · &nbsp; Precipitation {display_value(rain, " mm")}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">At a glance</div>', unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)
m1.metric("💧 Humidity", display_value(humidity, "%"))
m2.metric("💨 Wind speed", display_value(wind, " km/h"))
m3.metric("🌧️ Precipitation", display_value(rain, " mm"))

if advice:
    if isinstance(advice, list):
        advice = " ".join(str(item) for item in advice)
    st.info(f"💡 Weather advice: {advice}")

# Forecast
st.divider()
st.markdown('<div class="section-title">Forecast</div>', unsafe_allow_html=True)
st.caption("Explore temperature trends and the week ahead.")

hourly_tab, daily_tab = st.tabs(["🕒  NEXT 24 HOURS", "📅  NEXT 7 DAYS"])

with hourly_tab:
    if st.button("Load hourly forecast", key="load_hourly"):
        try:
            with st.spinner("Loading hourly forecast..."):
                st.session_state.hourly_data = api_get(
                    api_url,
                    "/api/v1/weather/hourly",
                    {"city": city, "hours": 24},
                )
        except Exception as error:
            show_api_error(error)

    hourly_payload = st.session_state.get("hourly_data", {})
    hourly_records = hourly_payload.get("hourly_forecast", [])

    if hourly_records:
        chart_rows = []
        for record in hourly_records:
            timestamp = get_value(record, "time", "timestamp")
            temp = get_value(record, "temperature_c", "temperature")
            if timestamp and temp is not None:
                chart_rows.append({
                    "Time": format_timestamp(timestamp),
                    "Temperature (°C)": float(temp),
                })

        if chart_rows:
            st.markdown("#### 🌡️ Temperature trend")
            chart_data = pd.DataFrame(chart_rows).set_index("Time")
            st.line_chart(
                chart_data,
                y="Temperature (°C)",
                height=280,
                color="#43dcff",
            )
            st.caption("Hourly temperatures for the selected city, provided by Open-Meteo.")

        for start in range(0, len(hourly_records), 4):
            group = hourly_records[start:start + 4]
            columns = st.columns(len(group))
            for column, record in zip(columns, group):
                timestamp = get_value(record, "time", "timestamp")
                temp = get_value(record, "temperature_c", "temperature")
                desc = get_value(record, "description", default="—")
                rain_chance = get_value(
                    record,
                    "precipitation_probability_percent",
                    "precipitation_probability_pct",
                    "precipitation_probability",
                )
                with column:
                    with st.container(border=True):
                        st.markdown(
                            f'<div class="forecast-time">{format_timestamp(timestamp)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="forecast-temperature">{weather_emoji(desc)} '
                            f'{display_value(temp, "°C")}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption(desc)
                        if rain_chance is not None:
                            st.caption(f"🌧️ Rain chance: {rain_chance}%")
    else:
        st.caption("Load the hourly forecast to see the next 24 hours.")

with daily_tab:
    if st.button("Load 7-day forecast", key="load_daily"):
        try:
            with st.spinner("Loading daily forecast..."):
                st.session_state.daily_data = api_get(
                    api_url,
                    "/api/v1/weather/daily",
                    {"city": city, "days": 7},
                )
        except Exception as error:
            show_api_error(error)

    daily_payload = st.session_state.get("daily_data", {})
    daily_records = daily_payload.get("daily_forecast", [])

    if daily_records:
        for record in daily_records:
            date_value = get_value(record, "date", "time")
            low = get_value(record, "temperature_min_c", "temperature_2m_min")
            high = get_value(record, "temperature_max_c", "temperature_2m_max")
            desc = get_value(record, "description", default="—")
            rain_probability = get_value(
                record,
                "precipitation_probability_max_percent",
                "precipitation_probability_max_pct",
                "precipitation_probability_max",
            )

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.5, 0.6, 1, 1.8])
                c1.markdown(f"**{format_timestamp(date_value, True)}**")
                c2.markdown(weather_emoji(desc))
                c3.markdown(
                    f"**{display_value(low, '°')} — {display_value(high, '°')}C**"
                )
                c4.markdown(str(desc))
                if rain_probability is not None:
                    st.caption(f"Maximum rain probability: {rain_probability}%")
    else:
        st.caption("Load the seven-day forecast to see the coming week.")

# Chat
st.divider()
st.markdown('<div class="section-title">💬 Ask AtmosIQ</div>', unsafe_allow_html=True)
st.caption("Ask about current weather, forecasts, what to wear, outdoor plans, or weather concepts.")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if not st.session_state.chat_messages:
    st.markdown("**Try asking:**")
    suggestions = st.columns(3)
    suggested_questions = [
        "Will it rain tomorrow?",
        "What should I wear today?",
        "How humid will it feel?",
    ]
    for col, question in zip(suggestions, suggested_questions):
        with col:
            if st.button(question, key=f"suggest_{question}", use_container_width=True):
                st.session_state.pending_prompt = question
                st.rerun()

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input(f"Ask about the weather in {city}...", max_chars=1000)
if not prompt:
    prompt = st.session_state.pop("pending_prompt", None)

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AtmosIQ is thinking..."):
            try:
                result = api_post(
                    api_url,
                    "/api/v1/chat",
                    {"message": prompt, "city": city},
                )
                answer = result.get("answer", "Sorry, I couldn't generate a response.")
                st.markdown(answer)
                weather_data = result.get("weather") or {}
                if weather_data:
                    with st.expander("Weather data used"):
                        st.json(weather_data)
            except Exception as error:
                show_api_error(error)
                answer = "I couldn't complete that request. Please check the backend connection and try again."
                st.markdown(answer)

    st.session_state.chat_messages.append({"role": "assistant", "content": answer})

st.divider()
st.caption(
    "AtmosIQ · Weather Intelligence · Updated "
    f"{datetime.now().strftime('%d %b %Y, %H:%M')}"
)