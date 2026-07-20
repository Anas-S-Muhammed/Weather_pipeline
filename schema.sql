-- Active: 1780000138164@@127.0.0.1@5432@weather_db
CREATE DATABASE weather_db;
 CREATE EXTENTION IF NOT EXISTS "pgcrypto";

 CREATE TABLE cities(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    lat FLOAT NOT NULL,
    LON FLOAT NOT NULL,
    UNIQUE(name , country)
 );

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE cities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    UNIQUE (name, country)
);

CREATE TABLE weather_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID REFERENCES cities(id),
    temperature FLOAT NOT NULL,
    feels_like FLOAT,
    humidity INTEGER,
    condition TEXT NOT NULL,
    wind_speed FLOAT,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

