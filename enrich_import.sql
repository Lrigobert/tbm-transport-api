\copy calendar FROM '/tmp/calendar.txt' WITH (FORMAT csv, HEADER true);
\copy calendar_dates FROM '/tmp/calendar_dates.txt' WITH (FORMAT csv, HEADER true);
\copy shapes FROM '/tmp/shapes.txt' WITH (FORMAT csv, HEADER true);
\copy fare_products FROM '/tmp/fare_products.txt' WITH (FORMAT csv, HEADER true);
