"""Fetch current conditions from OpenWeatherMap and store them in PostgreSQL."""

import os
from datetime import datetime

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "weather_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}
API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OWN_API")


def get_cities():
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, lat, lon FROM cities ORDER BY name")
        return cur.fetchall()


def fetch_weather(city_id, name, lat, lon):
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "city_id": city_id,
        "temperature": data["main"]["temp"],
        "feels_like": data["main"].get("feels_like"),
        "humidity": data["main"].get("humidity"),
        "condition": data["weather"][0]["description"],
        "wind_speed": data.get("wind", {}).get("speed"),
        "recorded_at": datetime.utcnow(),
    }


def insert_reading(reading):
    with psycopg2.connect(**DB_CONFIG) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO weather_readings
                (city_id, temperature, feels_like, humidity, condition, wind_speed, recorded_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reading["city_id"], reading["temperature"], reading["feels_like"],
                reading["humidity"], reading["condition"], reading["wind_speed"],
                reading["recorded_at"],
            ),
        )


def main():
    if not DB_CONFIG["password"]:
        raise RuntimeError("Set DB_PASSWORD in .env before fetching weather")
    if not API_KEY:
        raise RuntimeError("Set OPENWEATHER_API_KEY in .env before fetching weather")

    print("Fetching weather...")
    for city_id, name, lat, lon in get_cities():
        print(f"  -> {name}...", end=" ")
        try:
            reading = fetch_weather(city_id, name, lat, lon)
            insert_reading(reading)
            print(f"OK: {reading['temperature']} C, {reading['condition']}")
        except (requests.RequestException, KeyError, psycopg2.Error) as exc:
            print(f"failed: {exc}")
    print("Done!")


if __name__ == "__main__":
    main()
