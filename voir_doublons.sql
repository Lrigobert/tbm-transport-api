SELECT string_agg(DISTINCT stop_name, '  ||  ') AS variantes
FROM stops
GROUP BY LOWER(stop_name)
HAVING COUNT(DISTINCT stop_name) > 1
LIMIT 15;
