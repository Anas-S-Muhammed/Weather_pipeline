# Weather Pipeline

Fetches current weather from OpenWeatherMap into PostgreSQL and serves it through FastAPI.

## Setup

1. Copy `.env.example` to `.env` and set a valid PostgreSQL password and OpenWeatherMap API key. The legacy `OWN_API` key is still accepted, but `OPENWEATHER_API_KEY` is preferred.
2. Create the database once: `createdb -U postgres weather_db`.
3. Apply the schema and sample cities: `psql -U postgres -d weather_db -f schema.sql` then `psql -U postgres -d weather_db -f seed.sql`.
4. Install dependencies: `python -m pip install -r requirements.txt`.

## Run

Start the API with `python -m uvicorn main:app --reload` and use `/health` to confirm the database connection.

Fetch and store weather readings with `python fetch_weather.py`.
