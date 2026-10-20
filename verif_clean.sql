SELECT DISTINCT stop_name AS original, stop_name_clean AS nettoye
FROM stops
WHERE LOWER(stop_name) IN ('cantinolle','base sous-marine','de lattre de tassigny','croix de seguey','cité administrative')
ORDER BY 1;
