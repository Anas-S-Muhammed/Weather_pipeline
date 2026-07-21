# Weather Pipeline

A small, local-first weather data pipeline. It collects current conditions from OpenWeatherMap, stores each reading in PostgreSQL, and exposes the stored data through a FastAPI service.

The project is designed as a practical foundation for data engineering work: ingestion is separate from serving, the database is the source of truth, and the API provides a simple interface for applications, dashboards, or analysis notebooks.

## What it does

- Tracks a configurable list of cities and their coordinates.
- Fetches current weather conditions from OpenWeatherMap.
- Appends each result to PostgreSQL as a timestamped weather reading.
- Provides endpoints to inspect tracked cities, the latest reading for a city, recent reading history, and database totals.
- Exposes a health check that verifies API-to-database connectivity.

## Architecture

```text
OpenWeatherMap API
        |
        v
fetch_weather.py  --->  PostgreSQL (cities, weather_readings)
                                  |
                                  v
                    FastAPI (main.py + index.html)
                                  |
                                  v
                  browser dashboard, /docs, clients
```

`fetch_weather.py` is the ingestion job. `main.py` is the read API. Keeping them separate makes it safe to run ingestion on a schedule without coupling it to web traffic.

## Repository layout

```text
.
├── api/
│   ├── database.py       # SQLAlchemy engine and session dependency
│   ├── models.py         # ORM table models
│   └── schemas.py        # API request and response models
├── main.py               # FastAPI routes and dashboard delivery
├── index.html            # Weather Station browser dashboard
├── fetch_weather.py      # OpenWeatherMap ingestion job
├── schema.sql            # PostgreSQL schema bootstrap
├── seed.sql              # Initial tracked cities
├── requirements.txt      # Python dependencies
└── .env.example          # Environment-variable template
```

## Prerequisites

- Python 3.11 or later
- PostgreSQL 18 (or a compatible PostgreSQL version)
- An [OpenWeatherMap API key](https://openweathermap.org/api)

## Quick start

The commands below use PowerShell on Windows.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Create the database

Create `weather_db` once. If `createdb` is not on your PATH, use the PostgreSQL installation directory instead.

```powershell
createdb -U postgres weather_db
```

### 3. Configure local environment variables

Copy the template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with real local values:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=weather_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
OPENWEATHER_API_KEY=your_openweathermap_api_key
```

Never commit `.env`. It is ignored by Git because it contains credentials. The older `OWN_API` variable is accepted for compatibility, but `OPENWEATHER_API_KEY` is the supported name.

### 4. Create tables and seed cities

```powershell
psql -U postgres -d weather_db -f schema.sql
psql -U postgres -d weather_db -f seed.sql
```

The seed file adds 30 cities across Asia-Pacific, Europe, Africa, the Americas, and the Middle East. It is safe to run again because duplicate city/country pairs are ignored.

### 5. Start the API

```powershell
python -m uvicorn main:app --reload
```

Open the Weather Station dashboard at <http://127.0.0.1:8000/>. The dashboard is served by FastAPI and calls the API through the same origin. Open the interactive API documentation at <http://127.0.0.1:8000/docs>.

Verify the database connection:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected result:

```json
{"status":"ok","database":"connected"}
```

### 6. Ingest weather data

In a second PowerShell window with the virtual environment active:

```powershell
python fetch_weather.py
```

The job reads all tracked cities, fetches their current conditions, and inserts one reading per successful city. Run it repeatedly to build a historical dataset.

## API reference

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Weather Station dashboard |
| `GET` | `/api` | API status and version |
| `GET` | `/health` | Database connectivity check; returns `503` when unavailable |
| `GET` | `/cities` | List tracked cities |
| `POST` | `/cities` | Add a city to track |
| `GET` | `/weather/{city}` | Latest reading and recent reading history for a city |
| `GET` | `/stats` | City and reading totals |

### Get weather for a city

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/weather/London?forecast_hours=24"
```

`forecast_hours` accepts values from `1` to `168`. Despite the field name, the API currently returns **stored readings from the preceding time window**, not a provider-generated future forecast.

### Add a city

```powershell
Invoke-RestMethod http://127.0.0.1:8000/cities `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"name":"Kuala Lumpur","country":"MY","lat":3.139,"lon":101.6869}'
```

## Data model

### `cities`

One row per tracked location. A city is unique by `(name, country)` and includes its latitude and longitude.

### `weather_readings`

One row per ingestion event, linked to `cities` through `city_id`. It stores temperature, perceived temperature, humidity, text condition, wind speed, and the time the reading was recorded.

This append-only design preserves history and makes later analytics—daily averages, trend analysis, anomaly detection, or dashboarding—straightforward.

## Operations

### Run the final local version

Once the database, `.env`, and dependencies are configured, use two PowerShell windows from the project directory.

**Window 1 — populate weather data**

```powershell
.\.venv\Scripts\Activate.ps1
python fetch_weather.py
```

**Window 2 — run the application**

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

Then open <http://127.0.0.1:8000/>. The dashboard shows every tracked city and its most recent stored reading; select a city to see its stored history. Use `/docs` for the raw API and `/health` to diagnose database connectivity.

If you want fresh readings while the dashboard is open, run `python fetch_weather.py` again. The dashboard refreshes its city cards every 60 seconds.

### Schedule ingestion

For local development, run `python fetch_weather.py` manually. For regular collection, schedule the same command with Windows Task Scheduler, cron, or a workflow orchestrator. A sensible first cadence is every 30–60 minutes; choose a rate that fits your OpenWeatherMap plan.

### Check service health

Use `/health` for a lightweight readiness check. A `200` means the API and database can communicate. A `503` usually indicates that PostgreSQL is stopped, credentials in `.env` are wrong, or the configured database does not exist.

### Change PostgreSQL credentials

If the PostgreSQL password changes, update `DB_PASSWORD` in `.env` and restart Uvicorn. Do not put passwords into source files or commit them to Git.

## Troubleshooting

### `Database is unavailable` or `/health` returns `503`

1. Confirm the PostgreSQL Windows service is running.
2. Verify `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` in `.env`.
3. Test the same credentials directly:

   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -d weather_db
   ```

4. Restart the API after changing `.env`.

### `City '...' not found`

Add it through `POST /cities`, or insert it into `cities` with valid latitude and longitude.

### `No weather data for '...'`

The city exists but has no readings yet. Run:

```powershell
python fetch_weather.py
```

### OpenWeatherMap request fails

Confirm `OPENWEATHER_API_KEY` is set and active. The ingestion job prints a per-city failure and continues with the remaining cities.

## Development roadmap

The current project is intentionally compact. Strong next steps are:

1. Add automated tests for routes, validation, and ingestion failures.
2. Add Alembic migrations instead of applying `schema.sql` manually.
3. Schedule ingestion with retry/backoff and structured logs.
4. Store all timestamps as timezone-aware UTC values.
5. Add pagination and date-range filters for large reading histories.
6. Add a true forecast table/endpoint using OpenWeatherMap forecast data.
7. Containerize the API and PostgreSQL with Docker Compose.
8. Add CI checks for formatting, tests, and dependency security.

## Current implementation status

- PostgreSQL connectivity is configured and verified through `/health`.
- The FastAPI service can be started with Uvicorn.
- The schema and seed data provide the initial database state.
- The ingestion script is ready to populate historical weather readings once a valid OpenWeatherMap API key is configured.
