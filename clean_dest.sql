ALTER TABLE trips ADD COLUMN IF NOT EXISTS headsign_clean TEXT;

UPDATE trips SET headsign_clean = INITCAP(trip_headsign);

UPDATE trips SET headsign_clean =
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
  ' ' || headsign_clean || ' ',
  ' De ',' de '),' Du ',' du '),' La ',' la '),' Le ',' le '),
  ' Les ',' les '),' Des ',' des '),' Et ',' et '),' Sur ',' sur ');

UPDATE trips SET headsign_clean = TRIM(headsign_clean);

UPDATE trips SET headsign_clean = UPPER(LEFT(headsign_clean,1)) || SUBSTRING(headsign_clean FROM 2);
