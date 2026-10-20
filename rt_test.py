import requests
from google.transit import gtfs_realtime_pb2

# Flux GTFS-RT VehiclePositions de TBM (Mecatran)
URL = "https://bdx.mecatran.com/utw/ws/gtfsfeed/realtime/bordeaux?apiKey=opendata-bordeaux-metropole-flux-gtfs-rt"

print("Recuperation du flux temps reel...")
r = requests.get(URL, timeout=15)
print("Code HTTP:", r.status_code)
print("Taille recue:", len(r.content), "octets")

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(r.content)
print("Nombre d entites dans le flux:", len(feed.entity))

# Afficher les 3 premieres entites
for e in feed.entity[:3]:
    print("---")
    print(e)
