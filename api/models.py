from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid

class City(Base):
    __tablename__ = "cities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    
    weather_readings = relationship("WeatherReading", back_populates="city")

class WeatherReading(Base):
    __tablename__ = "weather_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=False)
    temperature = Column(Float, nullable=False)
    feels_like = Column(Float)
    humidity = Column(Integer)
    condition = Column(String, nullable=False)
    wind_speed = Column(Float)
    recorded_at = Column(DateTime, default=datetime.now)
    
    city = relationship("City", back_populates="weather_readings")