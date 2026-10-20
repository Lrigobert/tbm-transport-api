SELECT
  s.stop_name AS arret,
  s.stop_id AS quai,
  ROUND(ST_Distance(s.geom::geography, ST_SetSRID(ST_MakePoint(-0.50116, 44.89488),4326)::geography)::numeric, 0) AS metres,
  ROUND(DEGREES(ST_Azimuth(ST_SetSRID(ST_MakePoint(-0.50116, 44.89488),4326)::geography, s.geom::geography))::numeric, 0) AS cap,
  string_agg(DISTINCT r.route_short_name || ' vers ' || t.trip_headsign, ' | ') AS destinations
FROM stops s
LEFT JOIN stop_times st ON st.stop_id = s.stop_id
LEFT JOIN trips t ON t.trip_id = st.trip_id
LEFT JOIN routes r ON r.route_id = t.route_id
WHERE s.location_type = 0
GROUP BY s.stop_id, s.stop_name, s.geom
ORDER BY s.geom <-> ST_SetSRID(ST_MakePoint(-0.50116, 44.89488),4326)
LIMIT 5;
