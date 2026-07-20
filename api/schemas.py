from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class CityBase(BaseModel):
    name: str
    country: str
    lat: float
    lon: float

class CityCreate(CityBase):
    pass

class City(CityBase):
    id: uuid.UUID
    
    class Config:
        from_attributes = True

class WeatherReadingBase(BaseModel):
    temperature: float
    feels_like: Optional[float] = None
    humidity: Optional[int] = None
    condition: str
    wind_speed: Optional[float] = None

class WeatherReadingCreate(WeatherReadingBase):
    city_id: uuid.UUID

class WeatherReading(WeatherReadingBase):
    id: uuid.UUID
    city_id: uuid.UUID
    recorded_at: datetime
    
    class Config:
        from_attributes = True

class WeatherResponse(BaseModel):
    city: str
    country: str
    current: WeatherReading
    forecast: Optional[list[WeatherReading]] = None