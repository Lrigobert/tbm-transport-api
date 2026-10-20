-- Verification globale de la base
SELECT 'routes' AS table, COUNT(*) FROM routes
UNION ALL SELECT 'stops', COUNT(*) FROM stops
UNION ALL SELECT 'trips', COUNT(*) FROM trips
UNION ALL SELECT 'stop_times', COUNT(*) FROM stop_times
UNION ALL SELECT 'calendar', COUNT(*) FROM calendar
UNION ALL SELECT 'shapes', COUNT(*) FROM shapes;

-- Combien de noms d arrets ont des doublons de casse ?
SELECT COUNT(*) AS doublons_casse FROM (
  SELECT LOWER(stop_name) FROM stops GROUP BY LOWER(stop_name) HAVING COUNT(DISTINCT stop_name) > 1
) x;
