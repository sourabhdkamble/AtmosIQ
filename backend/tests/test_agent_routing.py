
import pytest

import app.agents.supervisor as supervisor
from app.agents.supervisor import route_user_request, route_with_keywords


@pytest.mark.parametrize(
    ("message", "expected_route"),
    [
        # Current weather
        ("What is the current weather in Mumbai?", "current_weather"),
        ("Is it raining right now?", "current_weather"),

        # Forecasts
        ("What is the weather forecast for tomorrow?", "forecast"),
        ("Show me the next 24 hours", "forecast"),

        # Weather advice
        ("What should I wear in this weather?", "weather_advice"),
        ("Should I carry an umbrella?", "weather_advice"),

        # General weather knowledge
        ("What causes humidity?", "knowledge"),
        ("How do clouds form?", "knowledge"),

        # Air quality
        ("What is the current AQI?", "air_quality"),
        ("Are PM2.5 levels high?", "air_quality"),
    ],
)
def test_weather_request_routes(message, expected_route):
    assert route_with_keywords(message) == expected_route


def test_gemini_exception_falls_back_to_keywords(monkeypatch):
    class BrokenLLM:
        def invoke(self, prompt):
            raise RuntimeError("Simulated Gemini failure")

    monkeypatch.delenv("ATMOSIQ_LOCAL_ROUTING", raising=False)
    monkeypatch.setattr(
        supervisor, "get_weather_llm", lambda: BrokenLLM()
    )

    assert (
        route_user_request("What is the forecast for tomorrow?")
        == "forecast"
    )


def test_malformed_gemini_json_falls_back_to_keywords(monkeypatch):
    class FakeLLM:
        def invoke(self, prompt):
            return type(
                "Response", (), {"content": "{not valid JSON"}
            )()

    monkeypatch.delenv("ATMOSIQ_LOCAL_ROUTING", raising=False)
    monkeypatch.setattr(
        supervisor, "get_weather_llm", lambda: FakeLLM()
    )

    assert (
        route_user_request("What is the forecast for tomorrow?")
        == "forecast"
    )


def test_invalid_gemini_route_falls_back_to_keywords(monkeypatch):
    class FakeLLM:
        def invoke(self, prompt):
            return type(
                "Response",
                (),
                {"content": '{"route": "unknown_agent"}'},
            )()

    monkeypatch.delenv("ATMOSIQ_LOCAL_ROUTING", raising=False)
    monkeypatch.setattr(
        supervisor, "get_weather_llm", lambda: FakeLLM()
    )

    assert (
        route_user_request("What is the forecast for tomorrow?")
        == "forecast"
    )


def test_markdown_wrapped_gemini_json_is_accepted(monkeypatch):
    class FakeLLM:
        def invoke(self, prompt):
            return type(
                "Response",
                (),
                {
                    "content": '```json\n{"route": "forecast"}\n```'
                },
            )()

    monkeypatch.delenv("ATMOSIQ_LOCAL_ROUTING", raising=False)
    monkeypatch.setattr(
        supervisor, "get_weather_llm", lambda: FakeLLM()
    )

    assert (
        route_user_request("What is the forecast for tomorrow?")
        == "forecast"
    )


def test_local_routing_bypasses_gemini(monkeypatch):
    def should_not_be_called():
        raise AssertionError(
            "Gemini should not be called when local routing is enabled"
        )

    monkeypatch.setenv("ATMOSIQ_LOCAL_ROUTING", "1")
    monkeypatch.setattr(
        supervisor, "get_weather_llm", should_not_be_called
    )

    assert (
        route_user_request("What is the forecast for tomorrow?")
        == "forecast"
    )
