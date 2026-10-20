import csv, math
from collections import defaultdict

def distance_metres(la1,lo1,la2,lo2):
    R=6371000
    p1,p2=math.radians(la1),math.radians(la2)
    dphi=math.radians(la2-la1); dl=math.radians(lo2-lo1)
    a=math.sin(dphi/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def cap_vers(la1,lo1,la2,lo2):
    p1,p2=math.radians(la1),math.radians(la2)
    dl=math.radians(lo2-lo1)
    x=math.sin(dl)*math.cos(p2)
    y=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(x,y))+360)%360

def cote(capu,capc):
    d=(capc-capu+540)%360-180
    return ("TOUT DROIT" if abs(d)<=20 else "a DROITE" if d>0 else "a GAUCHE")

quais={}
for r in csv.DictReader(open("stops.txt",encoding="utf-8-sig")):
    if r["location_type"]=="0":
        quais[r["stop_id"]]={"nom":r["stop_name"],"lat":float(r["stop_lat"]),"lon":float(r["stop_lon"])}
print(len(quais),"quais charges")

LAT,LON,CAP=44.89488,-0.50116,90
L=sorted(((distance_metres(LAT,LON,q["lat"],q["lon"]),i,q) for i,q in quais.items()))[:5]
print("\nQuais les plus proches de ta position:\n")
for d,i,q in L:
    c=cap_vers(LAT,LON,q["lat"],q["lon"])
    print("  "+q["nom"]+" (quai "+i+") - "+str(round(d))+"m - "+cote(CAP,c))
