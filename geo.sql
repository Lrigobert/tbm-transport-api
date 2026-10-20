ALTER TABLE stops ADD COLUMN geom geometry(Point, 4326);
UPDATE stops SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326);
CREATE INDEX idx_stops_geom ON stops USING GIST (geom);
CREATE INDEX idx_stop_times_stop ON stop_times (stop_id);
CREATE INDEX idx_stop_times_trip ON stop_times (trip_id);
CREATE INDEX idx_trips_route ON trips (route_id);
