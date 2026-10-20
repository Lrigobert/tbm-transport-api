SELECT
  rt.route_id AS ligne,
  r.route_long_name AS nom_ligne,
  rt.vehicle_label AS destination,
  s.stop_name_clean AS prochain_arret,
  rt.arrival_delay AS retard_sec,
  CASE
    WHEN rt.arrival_delay > 60 THEN 'EN RETARD (' || ROUND(rt.arrival_delay/60.0,1) || ' min)'
    WHEN rt.arrival_delay < -60 THEN 'EN AVANCE'
    ELSE 'A L HEURE'
  END AS statut
FROM realtime_updates rt
JOIN routes r ON r.route_id = rt.route_id
JOIN stops s ON s.stop_id = rt.stop_id
WHERE rt.arrival_delay IS NOT NULL
ORDER BY rt.arrival_delay DESC
LIMIT 10;
