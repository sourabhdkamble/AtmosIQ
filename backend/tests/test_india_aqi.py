
import math

import pytest

from app.services.india_aqi import (
    calculate_india_aqi,
    calculate_sub_index,
    get_aqi_category,
)


@pytest.mark.parametrize(
    ("aqi", "expected"),
    [
        (0, "Good"),
        (50, "Good"),
        (51, "Satisfactory"),
        (100, "Satisfactory"),
        (101, "Moderate"),
        (200, "Moderate"),
        (201, "Poor"),
        (300, "Poor"),
        (301, "Very Poor"),
        (400, "Very Poor"),
        (401, "Severe"),
        (500, "Severe"),
    ],
)
def test_indian_aqi_categories(aqi, expected):
    assert get_aqi_category(aqi) == expected


@pytest.mark.parametrize("aqi", [-1, 501, 12.5, True])
def test_rejects_invalid_aqi(aqi):
    with pytest.raises(ValueError):
        get_aqi_category(aqi)


def test_pm25_interpolation():
    assert calculate_sub_index("pm2_5", 30) == 50
    assert calculate_sub_index("pm2_5", 45) == 75
    assert calculate_sub_index("pm2_5", 60) == 100


def test_pm10_interpolation():
    assert calculate_sub_index("pm10", 25) == 25
    assert calculate_sub_index("pm10", 75) == 75


@pytest.mark.parametrize(
    "concentration",
    [-1, math.nan, math.inf, -math.inf, True, "invalid"],
)
def test_rejects_invalid_concentrations(concentration):
    with pytest.raises(ValueError):
        calculate_sub_index("pm2_5", concentration)


def test_unknown_pollutant_is_rejected():
    with pytest.raises(ValueError):
        calculate_sub_index("unknown", 10)


def test_insufficient_data_does_not_create_overall_aqi():
    result = calculate_india_aqi({
        "pm2_5": 20,
        "pm10": None,
        "nitrogen_dioxide": 10,
    })

    assert result["aqi"] is None
    assert result["status"] == "insufficient_pollutant_data"


def test_missing_pollutants_are_ignored():
    result = calculate_india_aqi({
        "pm2_5": 20,
        "pm10": 25,
        "nitrogen_dioxide": 10,
        "ozone_8h": None,
    })

    assert result["aqi"] is not None
    assert result["category"] == "Good"
    assert result["status"] == "provisional_estimate"


def test_overall_aqi_uses_highest_sub_index():
    result = calculate_india_aqi({
        "pm2_5": 20,
        "pm10": 150,
        "nitrogen_dioxide": 10,
    })

    assert result["aqi"] == max(result["sub_indices"].values())


@pytest.mark.parametrize(
    ("pollutant", "concentration", "expected_sub_index"),
    [
        ("pm2_5", 30.5, 51),
        ("pm10", 50.5, 51),
        ("carbon_monoxide_8h", 1.05, 51),
        ("nitrogen_dioxide", 40.5, 51),
        ("sulphur_dioxide", 40.5, 51),
        ("ozone_8h", 50.5, 51),
    ],
)
def test_decimal_breakpoint_interpolation(pollutant, concentration, expected_sub_index):
    """Regression test: decimal measurements between breakpoint bands must interpolate smoothly without ValueError."""
    assert calculate_sub_index(pollutant, concentration) == expected_sub_index

