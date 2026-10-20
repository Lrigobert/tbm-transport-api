import os
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import base64
import psycopg2
import psycopg2.extras
import requests as _req

DB = dict(host=os.environ.get("DB_HOST", "localhost"), port=int(os.environ.get("DB_PORT", "5433")), dbname=os.environ.get("DB_NAME", "tbm_db"), user=os.environ.get("DB_USER", "tbm"), password=os.environ["DB_PASSWORD"])

app = FastAPI(title="API Mobilite TBM", version="0.4")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class DemandeVerificationQuai(BaseModel):
    image_base64: str
    nom_arret: str
    ligne: str | None = None
    destination: str | None = None

def q(sql, args=()):
    conn = psycopg2.connect(**DB)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def cote(cap_vers, cap_user):
    d = (cap_vers - cap_user + 540) % 360 - 180
    if abs(d) <= 20:
        return "TOUT DROIT"
    return "a DROITE" if d > 0 else "a GAUCHE"

@app.get("/")
def accueil():
    return {"message": "API Mobilite TBM - operationnelle",
            "routes": ["/proches", "/arret/{stop_id}", "/prochains", "/zone", "/recherche", "/itineraire", "/acces_quai", "/alertes", "/verifier-quai"]}

@app.post("/verifier-quai")
def verifier_quai(demande: DemandeVerificationQuai):
    """Compare le panneau photographié avec les informations du trajet."""
    image = demande.image_base64
    if image.startswith("data:") and "," in image:
        image = image.split(",", 1)[1]
    if len(image) > 12_000_000:
        raise HTTPException(status_code=413, detail="Image trop volumineuse (12 Mo maximum).")
    try:
        image_bytes = base64.b64decode(image, validate=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Image illisible.") from exc
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        mime_type = "image/webp"
    else:
        mime_type = "image/jpeg"
    prompt = (
        "Tu aides un voyageur à vérifier un panneau de transport à Bordeaux. "
        "Lis uniquement le texte visible sur la photo. Compare-le aux attentes fournies. "
        "Réponds en français et ne devine jamais un texte illisible. Si le panneau est "
        "absent, flou ou si la comparaison n'est pas sûre, choisis 'incertain'. "
        "Retourne strictement un objet JSON avec les clés verdict (correct, incorrect ou incertain), "
        "ligne_lue, destination_lue et explication (une phrase courte).\n"
        f"Arrêt attendu : {demande.nom_arret}. "
        f"Ligne attendue : {demande.ligne or 'non précisée'}. "
        f"Destination attendue : {demande.destination or 'non précisée'}."
    )
    try:
        response = _req.post(
            "http://localhost:12434/engines/llama.cpp/v1/chat/completions",
            json={
                "model": "ai/gemma3:4b-q4_K_M",
                "temperature": 0,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image}"}},
                ]}],
            },
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content)
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            result = json.loads(content)
        except (ValueError, TypeError):
            result = {"verdict": "incertain", "ligne_lue": None,
                      "destination_lue": None, "explication": content[:500]}
        if not isinstance(result, dict):
            result = {"verdict": "incertain", "ligne_lue": None,
                      "destination_lue": None, "explication": "Réponse de lecture non reconnue."}
        if result.get("verdict") not in {"correct", "incorrect", "incertain"}:
            result["verdict"] = "incertain"
        return result
    except _req.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="L’assistant photo local n’est pas prêt. Vérifiez Docker Model Runner et le modèle Gemma 3.",
        ) from exc

@app.get("/proches")
def proches(lat: float = Query(...), lon: float = Query(...), cap: float | None = None):
    sql = """
    SELECT
      s.stop_id AS quai,
      s.stop_name_clean AS arret,
      ROUND(ST_Distance(s.geom::geography, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography)::numeric, 0) AS metres,
      ROUND(DEGREES(ST_Azimuth(ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, s.geom::geography))::numeric, 0) AS cap,
      string_agg(DISTINCT r.route_short_name || ' vers ' || t.headsign_clean, ' | ') AS destinations
    FROM stops s
    LEFT JOIN stop_times st ON st.stop_id = s.stop_id
    LEFT JOIN trips t ON t.trip_id = st.trip_id
    LEFT JOIN routes r ON r.route_id = t.route_id
    WHERE s.location_type = 0
    GROUP BY s.stop_id, s.stop_name_clean, s.geom
    ORDER BY s.geom <-> ST_SetSRID(ST_MakePoint(%s,%s),4326)
    LIMIT 5;
    """
    res = q(sql, (lon, lat, lon, lat, lon, lat))
    if cap is not None:
        for r in res:
            r["cote"] = cote(float(r["cap"] or 0), cap)
    return {"position": {"lat": lat, "lon": lon, "cap": cap}, "quais": res}

@app.get("/arret/{stop_id}")
def arret(stop_id: str, cap: float = 90.0):
    info = q("SELECT stop_id, stop_name_clean AS nom, stop_lat, stop_lon FROM stops WHERE stop_id = %s", (stop_id,))
    rt = q("""SELECT r.route_short_name AS ligne, rt.vehicle_label AS destination, rt.arrival_delay AS retard_sec
              FROM realtime_updates rt JOIN routes r ON r.route_id = rt.route_id
              WHERE rt.stop_id = %s AND rt.arrival_delay IS NOT NULL
              ORDER BY rt.arrival_time LIMIT 10""", (stop_id,))
    return {"arret": info[0] if info else None, "temps_reel": rt}

@app.get("/acces_quai")
def acces_quai(stop_id: str = Query(...), lat: float = Query(...), lon: float = Query(...),
               fauteuil: bool = False):
    info = q("SELECT stop_lat, stop_lon FROM stops WHERE stop_id = %s", (stop_id,))
    if not info:
        return {"erreur": "Quai introuvable", "distance_m": None, "duree_min": None, "points": None}
    wheelchair = ", wheelchair: true" if fauteuil else ""
    query = """{ plan(from: {lat: %s, lon: %s}, to: {lat: %s, lon: %s},
      transportModes: [{mode: WALK}]%s) {
      itineraries { duration walkDistance legs {
        legGeometry { points }
        steps { relativeDirection streetName distance lat lon }
      } } } }""" % (
        lat, lon, info[0]["stop_lat"], info[0]["stop_lon"], wheelchair)
    try:
        response = _req.post("http://localhost:8080/otp/routers/default/index/graphql",
                             json={"query": query}, timeout=20)
        data = response.json()
        itineraries = data.get("data", {}).get("plan", {}).get("itineraries", [])
        if not itineraries:
            return {"erreur": "Aucun chemin piéton trouvé", "distance_m": None,
                    "duree_min": None, "points": None}
        route = itineraries[0]
        points = [leg.get("legGeometry", {}).get("points") for leg in route.get("legs", [])
                  if leg.get("legGeometry", {}).get("points")]
        directions = {
            "LEFT": "Tournez à gauche", "SLIGHTLY_LEFT": "Obliquez à gauche",
            "HARD_LEFT": "Tournez franchement à gauche", "RIGHT": "Tournez à droite",
            "SLIGHTLY_RIGHT": "Obliquez à droite", "HARD_RIGHT": "Tournez franchement à droite",
            "CIRCLE_CLOCKWISE": "Prenez le rond-point", "CIRCLE_COUNTERCLOCKWISE": "Prenez le rond-point",
            "UTURN_LEFT": "Faites demi-tour à gauche", "UTURN_RIGHT": "Faites demi-tour à droite",
            "CONTINUE": "Continuez tout droit", "DEPART": "Commencez à marcher",
            "ELEVATOR": "Prenez l’ascenseur", "STAIRS": "Prenez les escaliers",
        }
        consignes = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                nom_rue = step.get("streetName")
                if nom_rue and nom_rue.strip().lower() in {"path", "footway", "walkway", "pedestrian"}:
                    nom_rue = None
                base = directions.get(step.get("relativeDirection"), "Continuez")
                consignes.append({
                    "texte": f"{base}{' sur ' + nom_rue if nom_rue else ''}",
                    "distance_m": round(step.get("distance", 0)),
                    "lat": step.get("lat"), "lon": step.get("lon"),
                })
        return {"distance_m": round(route.get("walkDistance", 0)),
                "duree_min": round(route.get("duration", 0) / 60),
                "points": points[0] if points else None, "consignes": consignes}
    except Exception as e:
        return {"erreur": str(e), "distance_m": None, "duree_min": None, "points": None}

@app.get("/prochains")
def prochains(stop_id: str = Query(...)):
    sql = """
    SELECT
      r.route_short_name AS ligne,
      r.route_long_name AS nom_ligne,
      COALESCE(
        NULLIF(t.headsign_clean, ''),
        NULLIF(rt.vehicle_label, ''),
        r.route_long_name
      ) AS destination,
      rt.arrival_delay AS retard_sec,
      TO_CHAR(TO_TIMESTAMP(rt.arrival_time) AT TIME ZONE 'Europe/Paris', 'HH24:MI') AS heure_passage,
      TO_CHAR(rt.maj_le AT TIME ZONE 'Europe/Paris', 'HH24:MI') AS maj_heure
    FROM realtime_updates rt
    JOIN routes r ON r.route_id = rt.route_id
    LEFT JOIN trips t ON t.trip_id = rt.trip_id
    WHERE rt.stop_id = %s
      AND rt.arrival_time IS NOT NULL
      AND rt.arrival_time >= EXTRACT(EPOCH FROM NOW()) - 60
    ORDER BY rt.arrival_time
    LIMIT 10;
    """
    status = q("""SELECT last_success, entity_count, update_count,
                        (last_success >= NOW() - INTERVAL '3 minutes') AS a_jour
                 FROM realtime_sync_status WHERE sync_name = 'gtfs_rt'""")
    return {"stop_id": stop_id, "prochains_passages": q(sql, (stop_id,)),
            "synchronisation": status[0] if status else None}

@app.get("/alertes")
def alertes(stop_id: str = Query(...), ligne: str | None = None):
    sql = """
    SELECT DISTINCT a.alert_id, a.header_text, a.description_text, a.effect,
      a.route_id, a.stop_id, a.start_time, a.end_time, a.updated_at
    FROM realtime_alerts a
    WHERE (a.start_time IS NULL OR a.start_time <= EXTRACT(EPOCH FROM NOW()))
      AND (a.end_time IS NULL OR a.end_time >= EXTRACT(EPOCH FROM NOW()))
      AND (
        (a.stop_id = %s AND (%s IS NULL OR a.route_id IS NULL OR a.route_id IN
          (SELECT route_id FROM routes WHERE route_short_name = %s)))
        OR (a.route_id IN (SELECT route_id FROM routes WHERE route_short_name = %s))
        OR (a.stop_id IS NULL AND a.route_id IS NULL)
      )
    ORDER BY a.updated_at DESC;
    """
    status = q("""SELECT last_success, entity_count, update_count, alert_count
                 FROM realtime_sync_status WHERE sync_name = 'gtfs_rt'""")
    return {"stop_id": stop_id, "alertes": q(sql, (stop_id, ligne, ligne, ligne)),
            "synchronisation": status[0] if status else None}

@app.get("/zone")
def zone(lat: float = Query(...), lon: float = Query(...), rayon: int = 1000):
    sql = """
    SELECT s.stop_id, s.stop_name_clean AS nom, s.stop_lat AS lat, s.stop_lon AS lon
    FROM stops s
    WHERE s.location_type = 0
      AND ST_DWithin(s.geom::geography, ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, %s)
    LIMIT 300;
    """
    return {"arrets": q(sql, (lon, lat, rayon))}

@app.get("/recherche")
def recherche(q_texte: str = Query(...)):
    sql = """
    SELECT DISTINCT ON (s.stop_name_clean)
      s.stop_id, s.stop_name_clean AS nom, s.stop_lat AS lat, s.stop_lon AS lon
    FROM stops s
    WHERE s.location_type = 0
      AND unaccent(lower(s.stop_name_clean)) LIKE unaccent(lower(%s))
    ORDER BY s.stop_name_clean
    LIMIT 30;
    """
    motif = f"%{q_texte}%"
    return {"resultats": q(sql, (motif,))}

@app.get("/itineraire")
def itineraire(lat_dep: float = Query(...), lon_dep: float = Query(...),
               lat_arr: float = Query(...), lon_arr: float = Query(...), fauteuil: bool = False):
    wheelchair = ", wheelchair: true" if fauteuil else ""
    query = """{ plan(from: {lat: %s, lon: %s}, to: {lat: %s, lon: %s},
      transportModes: [{mode: WALK}, {mode: TRANSIT}]%s) {
      itineraries { duration walkDistance
        legs { mode duration distance headsign startTime realTime
          route { shortName longName }
          from { name lat lon stop { gtfsId } }
          to { name } } } } }""" % (lat_dep, lon_dep, lat_arr, lon_arr, wheelchair)
    try:
        r = _req.post("http://localhost:8080/otp/routers/default/index/graphql",
                      json={"query": query}, timeout=15)
        data = r.json()
        itineraires = data.get("data", {}).get("plan", {}).get("itineraries", [])
        # OTP peut renvoyer une option entièrement à pied avant les trajets
        # en transport. Ne la garde que si aucun trajet bus/tram n'existe.
        avec_transport = [it for it in itineraires if any(
            leg.get("mode") in ("BUS", "TRAM", "RAIL", "SUBWAY", "FERRY")
            for leg in it.get("legs", []))]
        if avec_transport:
            itineraires = avec_transport
        itineraires.sort(key=lambda it: it.get("duration", float("inf")))
        resultats = []
        for it in itineraires:
            etapes = []
            for leg in it["legs"]:
                stop_id = None
                gtfs = (leg["from"].get("stop") or {}).get("gtfsId")
                if gtfs:
                    # gtfsId ressemble a "1:5513" -> on prend la partie apres ":"
                    stop_id = gtfs.split(":")[-1]
                start_ms = leg.get("startTime")
                depart_ts = round(start_ms / 1000) if start_ms else None
                depart_heure = datetime.fromtimestamp(depart_ts).strftime("%H:%M") if depart_ts else None
                etapes.append({
                    "mode": leg["mode"],
                    "ligne": leg["route"]["shortName"] if leg.get("route") else None,
                    "de": leg["from"]["name"],
                    # Le panneau du véhicule affiche le terminus (headsign),
                    # différent de l'arrêt suivant du trajet.
                    "vers": leg.get("headsign") or leg["to"]["name"],
                    "arrivee": leg["to"]["name"],
                    "duree_min": round(leg["duration"] / 60),
                    "stop_id": stop_id,
                    "depart_ts": depart_ts,
                    "depart_heure": depart_heure,
                    "temps_reel": leg.get("realTime"),
                })
            resultats.append({
                "duree_min": round(it["duration"] / 60),
                "marche_m": round(it["walkDistance"]),
                "etapes": etapes,
            })
        return {"itineraires": resultats}
    except Exception as e:
        return {"erreur": str(e), "itineraires": []}

