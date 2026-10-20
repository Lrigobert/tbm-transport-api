-- Corriger les espaces multiples
UPDATE trips SET headsign_clean = REGEXP_REPLACE(headsign_clean, ' +', ' ', 'g');

-- Normaliser St / Ste vers Saint / Sainte (avec espaces autour pour cibler le mot entier)
UPDATE trips SET headsign_clean = REPLACE(' ' || headsign_clean, ' St ', ' Saint ');
UPDATE trips SET headsign_clean = REPLACE(headsign_clean, ' Ste ', ' Sainte ');
UPDATE trips SET headsign_clean = TRIM(headsign_clean);
