
"""India-specific AQI calculations using CPCB concentration bands.

Concentrations must use the required CPCB averaging period.
CO is measured in mg/m³; other supported pollutants use µg/m³.

Results calculated from model estimates are not official CPCB readings.
"""

from math import floor, isfinite


# (concentration lower, concentration upper, AQI lower, AQI upper)
BREAKPOINTS = {
    "pm2_5": [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, float("inf"), 401, 500),
    ],
    "pm10": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 250, 101, 200),
        (251, 350, 201, 300),
        (351, 430, 301, 400),
        (431, float("inf"), 401, 500),
    ],
    "nitrogen_dioxide": [
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 180, 101, 200),
        (181, 280, 201, 300),
        (281, 400, 301, 400),
        (401, float("inf"), 401, 500),
    ],
    "sulphur_dioxide": [
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 380, 101, 200),
        (381, 800, 201, 300),
        (801, 1600, 301, 400),
        (1601, float("inf"), 401, 500),
    ],
    "ozone_8h": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 168, 101, 200),
        (169, 208, 201, 300),
        (209, 748, 301, 400),
        (749, float("inf"), 401, 500),
    ],
    "carbon_monoxide_8h": [
        (0, 1.0, 0, 50),
        (1.1, 2.0, 51, 100),
        (2.1, 10.0, 101, 200),
        (10.1, 17.0, 201, 300),
        (17.1, 34.0, 301, 400),
        (34.1, float("inf"), 401, 500),
    ],
}


AQI_CATEGORIES = [
    (50, "Good"),
    (100, "Satisfactory"),
    (200, "Moderate"),
    (300, "Poor"),
    (400, "Very Poor"),
    (500, "Severe"),
]


def get_aqi_category(aqi: int) -> str:
    """Return the Indian AQI category for an index from 0 to 500."""

    if isinstance(aqi, bool) or not isinstance(aqi, int):
        raise ValueError("AQI must be an integer.")

    if not 0 <= aqi <= 500:
        raise ValueError("AQI must be between 0 and 500.")

    for upper_bound, category in AQI_CATEGORIES:
        if aqi <= upper_bound:
            return category

    raise ValueError("AQI must be between 0 and 500.")


def calculate_sub_index(
    pollutant: str,
    concentration: float,
) -> int:
    """Calculate a pollutant sub-index by linear interpolation."""

    if pollutant not in BREAKPOINTS:
        raise ValueError(f"Unsupported pollutant: {pollutant}")

    if isinstance(concentration, bool):
        raise ValueError("Concentration must be a finite number.")

    try:
        concentration = float(concentration)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Concentration must be a finite number."
        ) from exc

    if not isfinite(concentration):
        raise ValueError("Concentration must be a finite number.")

    if concentration < 0:
        raise ValueError("Concentration cannot be negative.")

    bands = BREAKPOINTS[pollutant]

    for low_c, high_c, low_i, high_i in bands:
        if low_c <= concentration <= high_c:
            if high_c == float("inf"):
                return 500

            value = (
                (high_i - low_i)
                / (high_c - low_c)
                * (concentration - low_c)
                + low_i
            )

            return min(500, max(0, floor(value + 0.5)))

    # Handle continuous decimal readings falling into the gap between integer breakpoints
    for i in range(len(bands) - 1):
        prev_low_c, prev_high_c, prev_low_i, prev_high_i = bands[i]
        next_low_c, next_high_c, next_low_i, next_high_i = bands[i + 1]
        if prev_high_c < concentration < next_low_c:
            midpoint = (prev_high_c + next_low_c) / 2.0
            return prev_high_i if concentration < midpoint else next_low_i

    raise ValueError(
        f"Concentration {concentration} does not fit a breakpoint "
        f"for {pollutant}. Check the concentration and units."
    )


def calculate_india_aqi(
    concentrations: dict[str, float | None],
) -> dict:
    """Calculate a provisional Indian-style AQI.

    Only provide concentrations that have been computed using the
    required averaging period. This function cannot verify the period.
    """

    sub_indices = {}

    for pollutant, concentration in concentrations.items():
        if concentration is None or pollutant not in BREAKPOINTS:
            continue

        sub_indices[pollutant] = calculate_sub_index(
            pollutant,
            concentration,
        )

    has_particulate = (
        "pm2_5" in sub_indices or "pm10" in sub_indices
    )

    if len(sub_indices) < 3 or not has_particulate:
        return {
            "aqi": None,
            "category": None,
            "sub_indices": sub_indices,
            "status": "insufficient_pollutant_data",
        }

    aqi = max(sub_indices.values())

    return {
        "aqi": aqi,
        "category": get_aqi_category(aqi),
        "sub_indices": sub_indices,
        "status": "provisional_estimate",
    }
