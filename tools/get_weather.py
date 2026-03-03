import json
import urllib.request
import urllib.parse
from datetime import datetime

# Hardcoded locations for the briefing
LOCATIONS = {
    "cupertino": {
        "name": "Apple Park, Cupertino",
        "latitude": 37.3348,
        "longitude": -122.0090,
        "timezone": "America/Los_Angeles",
    },
    "home": {
        "name": "Nob Hill, San Francisco",
        "latitude": 37.7946,
        "longitude": -122.4205,
        "timezone": "America/Los_Angeles",
    },
    "tahoe": {
        "name": "Lake Tahoe",
        "latitude": 39.1906,
        "longitude": -120.2484,
        "timezone": "America/Los_Angeles",
    },
}

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ slight hail",
    99: "Thunderstorm w/ heavy hail",
}

schema = {
    "name": "get_weather",
    "description": (
        "Get current weather conditions and 7-day forecasts for key locations using Open-Meteo. "
        "Locations: 'home' (Nob Hill, SF), 'cupertino' (Apple Park), 'tahoe' (Lake Tahoe), or 'all'. "
        "Returns current temp, feels-like, humidity, wind, and daily highs/lows with conditions. "
        "For Tahoe, includes a snow alert showing total inches and snow days in the next 7 days. "
        "Always prefer this over web search for weather — it's faster and more precise."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "enum": ["home", "cupertino", "tahoe", "all"],
                "description": (
                    "Which location(s) to fetch. "
                    "'home' = Nob Hill, SF. "
                    "'cupertino' = Apple Park. "
                    "'tahoe' = Lake Tahoe (includes snow alert). "
                    "'all' = all three (default)."
                ),
            }
        },
        "required": [],
    },
}


def _fetch(lat: float, lon: float, timezone: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 7,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
            "precipitation",
            "snowfall",
        ]),
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "weather_code",
            "precipitation_sum",
            "snowfall_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
        ]),
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def _wmo(code: int) -> str:
    return WMO_CODES.get(int(code), f"Code {code}")


def _format_location(loc_key: str, data: dict) -> str:
    name = LOCATIONS[loc_key]["name"]
    c = data["current"]
    d = data["daily"]

    lines = [f"### {name}"]

    # Current conditions
    lines.append(
        f"Now: {c['temperature_2m']:.0f}°F (feels {c['apparent_temperature']:.0f}°F)  "
        f"{_wmo(c['weather_code'])}"
    )
    lines.append(
        f"Humidity: {c['relative_humidity_2m']}%  "
        f"Wind: {c['wind_speed_10m']:.0f} mph (gusts {c['wind_gusts_10m']:.0f} mph)"
    )

    # 7-day daily forecast
    lines.append("Forecast:")
    for i, date in enumerate(d["time"]):
        hi = d["temperature_2m_max"][i]
        lo = d["temperature_2m_min"][i]
        cond = _wmo(d["weather_code"][i])
        pop = d["precipitation_probability_max"][i] or 0
        precip = d["precipitation_sum"][i] or 0
        snow = d["snowfall_sum"][i] or 0
        label = datetime.strptime(date, "%Y-%m-%d").strftime("%a %m/%d")
        row = f"  {label}: {hi:.0f}/{lo:.0f}°F  {cond}  {pop}% precip"
        if precip > 0:
            row += f'  {precip:.2f}"'
        if snow > 0:
            row += f"  {snow:.1f}\" snow"
        lines.append(row)

    # Tahoe-specific snow alert
    if loc_key == "tahoe":
        total_snow = sum(d["snowfall_sum"][i] or 0 for i in range(len(d["time"])))
        snow_days = [
            datetime.strptime(d["time"][i], "%Y-%m-%d").strftime("%a %m/%d")
            for i in range(len(d["time"]))
            if (d["snowfall_sum"][i] or 0) > 0
        ]
        lines.append("")
        if total_snow >= 0.1:
            lines.append(
                f"SNOW ALERT: {total_snow:.1f}\" forecast over 7 days  |  Days: {', '.join(snow_days)}"
            )
        else:
            lines.append("No snow in the 7-day forecast.")

    return "\n".join(lines)


def execute(location: str = "all") -> str:
    keys = list(LOCATIONS.keys()) if location == "all" else [location]
    parts = []
    errors = []
    for key in keys:
        loc = LOCATIONS[key]
        try:
            data = _fetch(loc["latitude"], loc["longitude"], loc["timezone"])
            parts.append(_format_location(key, data))
        except Exception as e:
            errors.append(f"{loc['name']}: {e}")

    result = "\n\n".join(parts)
    if errors:
        result += "\n\nErrors: " + "; ".join(errors)
    return result or "No data."
