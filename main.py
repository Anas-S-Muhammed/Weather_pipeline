from pathlib import Path


from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from api.database import get_db
from api import models, schemas


app = FastAPI(title="Weather API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_DIR = Path(__file__).resolve().parent

# ---------- API Endpoints ----------
@app.get("/")
def dashboard():
    """Serve the Weather Station dashboard."""
    return FileResponse(PROJECT_DIR / "index.html")


@app.get("/api")
def api_status():
    return {"status": "Weather API is running", "version": "1.0"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Report whether the API can reach its PostgreSQL database."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ok", "database": "connected"}

@app.get("/weather/{city}", response_model=schemas.WeatherResponse)
def get_weather(
    city: str, 
    forecast_hours: Optional[int] = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get current weather and forecast for a city"""

    # Get city
    city_obj = db.query(models.City).filter(models.City.name.ilike(city.strip())).first()
    if not city_obj:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    
    # Get current weather
    current = db.query(models.WeatherReading).filter(
        models.WeatherReading.city_id == city_obj.id
    ).order_by(models.WeatherReading.recorded_at.desc()).first()
    
    if not current:
        raise HTTPException(status_code=404, detail=f"No weather data for '{city}'")
    
    # Get forecast history
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=forecast_hours)
    forecast = db.query(models.WeatherReading).filter(
        models.WeatherReading.city_id == city_obj.id,
        models.WeatherReading.recorded_at >= cutoff,
        models.WeatherReading.id != current.id
    ).order_by(models.WeatherReading.recorded_at.desc()).limit(48).all()
    

    
    return schemas.WeatherResponse(
        city=city_obj.name,
        country=city_obj.country,
        current=current,
        forecast=forecast
    )

@app.get("/cities", response_model=list[schemas.City])
def list_cities(db: Session = Depends(get_db)):
    """List all tracked cities"""
    return db.query(models.City).order_by(models.City.name).all()

@app.post("/cities", response_model=schemas.City, status_code=status.HTTP_201_CREATED)
def add_city(city: schemas.CityCreate, db: Session = Depends(get_db)):
    """Add a new city to track"""
    existing = db.query(models.City).filter(
        models.City.name == city.name,
        models.City.country == city.country
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"City '{city.name}, {city.country}' already exists")
    
    db_city = models.City(**city.model_dump())
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    city_count = db.query(models.City).count()
    reading_count = db.query(models.WeatherReading).count()
    
    return {
        "total_cities": city_count,
        "total_readings": reading_count
    }

