-- Nettoyage NON destructif : on garde stop_name original, on ajoute une version propre
ALTER TABLE stops ADD COLUMN IF NOT EXISTS stop_name_clean TEXT;

-- Etape 1 : Title Case de base (chaque mot commence par une majuscule)
UPDATE stops SET stop_name_clean = INITCAP(stop_name);

-- Etape 2 : remettre en minuscule les petits mots de liaison francais
UPDATE stops SET stop_name_clean = REGEXP_REPLACE(stop_name_clean, '\\m(De|Du|La|Le|Les|Des|Et|Sur|Sous|A|Au|Aux|En|D|L)\\M', LOWER('\\1'), 'g');

-- Etape 3 : la premiere lettre du nom reste toujours en majuscule
UPDATE stops SET stop_name_clean = UPPER(LEFT(stop_name_clean,1)) || SUBSTRING(stop_name_clean FROM 2);
