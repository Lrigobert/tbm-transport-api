-- Recorriger : petits mots en minuscule, methode robuste avec espaces
UPDATE stops SET stop_name_clean = INITCAP(stop_name);

UPDATE stops SET stop_name_clean =
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
  ' ' || stop_name_clean || ' ',
  ' De ',' de '),' Du ',' du '),' La ',' la '),' Le ',' le '),
  ' Les ',' les '),' Des ',' des '),' Et ',' et '),' Sur ',' sur ');

UPDATE stops SET stop_name_clean = TRIM(stop_name_clean);

-- Premiere lettre toujours en majuscule
UPDATE stops SET stop_name_clean = UPPER(LEFT(stop_name_clean,1)) || SUBSTRING(stop_name_clean FROM 2);
