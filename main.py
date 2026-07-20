from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from api.database import engine, get_db
from api import models, schemas

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Weather API", version="1.0")

# ---------- API Endpoints ----------
@app.get("/")
async def root():
    return {"status": "Weather API is running", "version": "1.0"}

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

