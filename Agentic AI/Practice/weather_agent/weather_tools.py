
import requests
from typing import Optional
from weather_scheme import WeatherData, WeatherRequest

def get_coordinate(city: str, country_code: Optional[int]):
    query = city if not country_code else f"{city},{country_code}"
    response = requests.get('https://geocoding-api.open-meteo.com/v1/search',
                            params={"name": query, 
                                    "count":1,
                                    "language": "en",
                                    "format": "json"},
                            timeout=10,       
                            )
    response.raise_for_status()
    results = response.json().get("result")
    if not results:
        raise ValueError(f'City not found: {city}')
    
    result = results[0]
    return result["latitude"], result["longitude"], result.get("country", "")


def fetch_weather(lat: float, lon: float, units: str) -> dict:
    temperature_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
    wind_unit = "mph" if units == "fahrenheit" else "kmh"

    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "wind_speed_10m",
                "weather_code",
            ],
            "temperature_unit": temperature_unit,
            "wind_speed_unit": wind_unit,
            "forecast_days": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()

def decode_weather(code: int) -> str:
    mapping = {
        0 : "Clear Sky", 1: "Mainly clear", 2: "partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy fog",
        51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 99: "Thunderstorm with hail",
        }
    return mapping.get(code, f"The weather codee: {code}")
    

def get_data(request: WeatherRequest) -> WeatherData:
    lat, lon, country = get_coordinate(request.city, request.country_code)

    raw = fetch_weather(lat, lon, request.units)
    current = raw["current"]
    return WeatherData(
        city = request.city,
        country = country or request.country_code,
        temperature = current["temperature_2m"],
        feels_like = current["apparent_temperature"],
        humidy = current["relative_humidity_2m"],
        wind_speed = current["wind_speed_10m"],
        description = current["weather_code"],
        unit = request.unit,
        )
