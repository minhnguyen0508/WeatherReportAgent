"""A read-only Open-Meteo weather service with strict input validation."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAYS = {"today": 0, "tomorrow": 1, "day_after_tomorrow": 2}
CONDITIONS = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog", 51: "light drizzle",
    53: "moderate drizzle", 55: "dense drizzle", 56: "light freezing drizzle",
    57: "dense freezing drizzle", 61: "slight rain", 63: "moderate rain",
    65: "heavy rain", 66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow",
    77: "snow grains", 80: "slight rain showers", 81: "moderate rain showers",
    82: "violent rain showers", 85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def _validate(city: str, day: str):
    if not isinstance(city, str) or not (2 <= len(city.strip()) <= 80):
        return "City must be a name between 2 and 80 characters."
    if not all(ch.isalnum() or ch.isspace() or ch in ",.'-" for ch in city):
        return "City contains unsupported characters."
    if not isinstance(day, str) or day not in DAYS:
        return "Day must be today, tomorrow, or day_after_tomorrow."
    return None


def _get_json(url: str, params: dict) -> dict:
    response = requests.get(url, params=params, timeout=(5, 12))
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("error"):
        raise ValueError("Weather provider returned an error")
    return payload


def get_weather_forecast_data(city: str = "Fullerton, CA", day: str = "today") -> dict:
    """Retrieve live US city forecast; never executes arbitrary URLs or commands."""
    error = _validate(city, day)
    if error:
        return {"error": error}

    try:
        requested_city = city.strip()
        city_name = requested_city.split(",", 1)[0].strip().casefold()

        locations = _get_json(
            GEOCODE_URL,{
                "name":requested_city,
                "count": 10,
                "language": "en",
                "countryCode": "US",
            }
        ).get("results") or []
        if not locations:
            return{
                "error": (
                    f"Could not fine '{requested_city}'."
                    "Check the spelling and state abbreviation."
                )
            }

        matches = [
            loc for loc in locations 
            if loc.get("name", "").strip().casefold() == city_name
        ]

        if not matches:
            return {
                "error":(
                    f"No exact city match found for '{requested_city}'."
                    "Please verify the city name."
                )
            }

        selected = matches[0]
        
        forecast = _get_json(FORECAST_URL, {
            "latitude": selected["latitude"],
            "longitude": selected["longitude"],
            "timezone": "auto",
            "forecast_days": 3,
            "temperature_unit": "fahrenheit",
            "precipitation_unit": "inch",
            "wind_speed_unit": "mph",
            "current": "temperature_2m,apparent_temperature,weather_code,cloud_cover,wind_speed_10m",
            "hourly": "temperature_2m,precipitation_probability,precipitation,cloud_cover,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,sunrise,sunset",
        })
        offset = DAYS[day]
        daily = forecast["daily"]
        date = daily["time"][offset]
        sunrise = daily["sunrise"][offset]
        sunset = daily["sunset"][offset]

        local_now = datetime.now(ZoneInfo(forecast["timezone"]))
        current_hour = local_now.strftime("%Y-%m-%dT%H:00")
        hourly = forecast["hourly"]
        rows = []
        for i, timestamp in enumerate(hourly["time"]):
            if not timestamp.startswith(date):
                continue
            if day == "today" and timestamp < current_hour:
                continue
            code = hourly["weather_code"][i]
            cloud = hourly["cloud_cover"][i]
            likely_sunny = (
                code in (0, 1) and cloud is not None and cloud <= 30
                and sunrise <= timestamp <= sunset
            )
            rows.append({
                "local_time": timestamp,
                "condition": CONDITIONS.get(code, "other/unknown"),
                "temperature_f": hourly["temperature_2m"][i],
                "precipitation_probability_percent": hourly["precipitation_probability"][i],
                "precipitation_in": hourly["precipitation"][i],
                "cloud_cover_percent": cloud,
                "likely_sunny": likely_sunny,
            })

        daily_code = daily["weather_code"][offset]
        return {
            "source": "Open-Meteo (model forecast, not a guarantee)",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "location": {"city": selected["name"], "state": selected.get("admin1"),
                         "country": selected.get("country"), "timezone": forecast["timezone"]},
            "day": day,
            "local_date": date,
            "daily": {
                "condition": CONDITIONS.get(daily_code, "other/unknown"),
                "high_f": daily["temperature_2m_max"][offset],
                "low_f": daily["temperature_2m_min"][offset],
                "maximum_precipitation_probability_percent": daily["precipitation_probability_max"][offset],
                "total_precipitation_in": daily["precipitation_sum"][offset],
                "sunrise_local": sunrise, "sunset_local": sunset,
            },
            "current": forecast.get("current") if day == "today" else None,
            "hourly": rows,
            "likely_sunny_hours_local": [r["local_time"] for r in rows if r["likely_sunny"]],
            "rain_risk_hours_local": [r["local_time"] for r in rows
                                      if (r["precipitation_probability_percent"] or 0) >= 50],
            "note": "Likely sunny means clear/mainly clear, <=30% cloud, during daylight. "
                    "Rain-risk hours use >=50% forecast precipitation probability. "
                    "These are heuristics, not certainty.",
        }
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, ZoneInfoNotFoundError):
        # Do not disclose provider payloads, credentials, or internals to an LLM/user.
        return {"error": "The weather provider is temporarily unavailable or returned incomplete data."}
