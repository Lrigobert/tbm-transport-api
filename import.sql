\copy routes FROM '/tmp/routes.txt' WITH (FORMAT csv, HEADER true);
\copy stops FROM '/tmp/stops.txt' WITH (FORMAT csv, HEADER true);
\copy trips FROM '/tmp/trips.txt' WITH (FORMAT csv, HEADER true);
\copy stop_times FROM '/tmp/stop_times.txt' WITH (FORMAT csv, HEADER true);
