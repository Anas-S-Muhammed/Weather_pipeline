import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ========== READ FROM .env ==========
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "weather_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")
}

API_KEY = os.getenv("OWN_API")

# ========== REST OF YOUR CODE ==========
def get_cities():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, name, lat, lon FROM cities")
    cities = cur.fetchall()
    cur.close()
    conn.close()
    return cities

def fetch_weather(city_id, name, lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Failed for {name}: {response.status_code}")
        return None
    
    data = response.json()
    return {
        "city_id": city_id,
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"],
        "wind_speed": data["wind"].get("speed"),
        "recorded_at": datetime.now()
    }

def insert_reading(reading):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO weather_readings 
        (city_id, temperature, feels_like, humidity, condition, wind_speed, recorded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        reading["city_id"],
        reading["temperature"],
        reading["feels_like"],
        reading["humidity"],
        reading["condition"],
        reading["wind_speed"],
        reading["recorded_at"]
    ))
    conn.commit()
    cur.close()
    conn.close()

# ========== RUN IT ==========
print("🌤️ Fetching weather...")
cities = get_cities()

for city_id, name, lat, lon in cities:
    print(f"  → {name}...", end=" ")
    reading = fetch_weather(city_id, name, lat, lon)
    if reading:
        insert_reading(reading)
        print(f"✅ {reading['temperature']}°C, {reading['condition']}")
    else:
        print("❌ Failed")

print("✅ Done!")