SELECT DISTINCT trip_headsign AS original, headsign_clean AS nettoye
FROM trips
WHERE UPPER(trip_headsign) LIKE '%AMBARES%' OR UPPER(trip_headsign) LIKE '%SAINT LOUIS%' OR UPPER(trip_headsign) LIKE '%ST LOUIS%'
ORDER BY 2;
