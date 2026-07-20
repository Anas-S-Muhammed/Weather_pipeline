INSERT INTO cities (name, country, lat, lon) VALUES 
('London', 'UK', 51.5074, -0.1278),
('New York', 'US', 40.7128, -74.0060),
('Tokyo', 'JP', 35.6762, 139.6503),
('Paris', 'FR', 48.8566, 2.3522),
('Sydney', 'AU', -33.8688, 151.2093)
ON CONFLICT (name, country) DO NOTHING;