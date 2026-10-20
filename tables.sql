CREATE TABLE routes (
  route_id TEXT PRIMARY KEY,
  agency_id TEXT,
  route_short_name TEXT,
  route_long_name TEXT,
  route_type INT,
  route_color TEXT,
  route_text_color TEXT
);

CREATE TABLE stops (
  stop_id TEXT PRIMARY KEY,
  stop_code TEXT,
  stop_name TEXT,
  stop_lat DOUBLE PRECISION,
  stop_lon DOUBLE PRECISION,
  location_type INT,
  parent_station TEXT,
  wheelchair_boarding INT
);

CREATE TABLE trips (
  route_id TEXT,
  service_id TEXT,
  trip_id TEXT PRIMARY KEY,
  trip_headsign TEXT,
  direction_id INT,
  shape_id TEXT,
  wheelchair_accessible INT,
  bikes_allowed INT
);

CREATE TABLE stop_times (
  trip_id TEXT,
  arrival_time TEXT,
  departure_time TEXT,
  stop_id TEXT,
  stop_sequence INT,
  stop_headsign TEXT,
  pickup_type INT,
  drop_off_type INT,
  shape_dist_traveled DOUBLE PRECISION,
  timepoint INT
);
