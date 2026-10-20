DROP TABLE IF EXISTS calendar, calendar_dates, shapes, fare_products CASCADE;

CREATE TABLE calendar (service_id TEXT, monday INT, tuesday INT, wednesday INT, thursday INT, friday INT, saturday INT, sunday INT, start_date TEXT, end_date TEXT, service_name TEXT);

CREATE TABLE calendar_dates (service_id TEXT, date TEXT, exception_type INT);

CREATE TABLE shapes (shape_id TEXT, shape_pt_lat DOUBLE PRECISION, shape_pt_lon DOUBLE PRECISION, shape_pt_sequence INT, shape_dist_traveled DOUBLE PRECISION);

CREATE TABLE fare_products (fare_product_id TEXT, fare_product_name TEXT, amount NUMERIC, currency TEXT, fare_media_id TEXT, rider_category_id TEXT);
