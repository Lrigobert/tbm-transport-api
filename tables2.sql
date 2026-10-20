DROP TABLE IF EXISTS routes, stops, trips, stop_times CASCADE;

CREATE TABLE routes (route_id TEXT, agency_id TEXT, route_short_name TEXT, route_long_name TEXT, route_type INT, route_color TEXT, route_text_color TEXT, ext_type TEXT, ineo_id TEXT, ineo_nomc TEXT);

CREATE TABLE stops (stop_id TEXT, stop_code TEXT, stop_name TEXT, stop_lat DOUBLE PRECISION, stop_lon DOUBLE PRECISION, zone_id TEXT, stop_url TEXT, location_type INT, parent_station TEXT, wheelchair_boarding INT, ineo_id TEXT, ineo_mnemoc TEXT, ineo_mnemol TEXT, ineo_noc TEXT, ineo_nol TEXT, ineo_nomc TEXT);

CREATE TABLE trips (route_id TEXT, service_id TEXT, trip_id TEXT, trip_headsign TEXT, direction_id INT, block_id TEXT, shape_id TEXT, wheelchair_accessible INT, bikes_allowed INT, ext_id TEXT, ineo_id_chainage TEXT, ineo_id_course TEXT, ineo_id_jour TEXT);

CREATE TABLE stop_times (trip_id TEXT, arrival_time TEXT, departure_time TEXT, stop_id TEXT, stop_sequence INT, stop_headsign TEXT, pickup_type INT, drop_off_type INT, shape_dist_traveled DOUBLE PRECISION, timepoint INT);
