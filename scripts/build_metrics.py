"""Compute road-per-resident metrics from data/hm71_2024_all_areas.csv.

Outputs:
    data/us-metro-road-per-resident-2024.csv  every US urbanized area over 1 million people
                                              (Puerto Rico excluded), sorted by road per resident
    data/regional-aggregates-2024.csv         greater Southern California and Bay Area totals,
                                              which recombine areas the Census splits apart
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M_PER_MI = 1609.344
MIN_POP = 1_000_000

# Short chart labels, keyed by the part of the FHWA name before the first comma.
LABELS = {
    "New York--Jersey City--Newark": "New York", "Los Angeles--Long Beach--Anaheim": "Los Angeles",
    "Dallas--Fort Worth--Arlington": "Dallas–Fort Worth", "Washington--Arlington": "Washington, DC",
    "Phoenix--Mesa--Scottsdale": "Phoenix", "San Francisco--Oakland": "San Francisco–Oakland",
    "Minneapolis--St. Paul": "Minneapolis–St. Paul", "Tampa--St. Petersburg": "Tampa",
    "Denver--Aurora": "Denver", "Riverside--San Bernardino": "Riverside–San Bernardino",
    "Las Vegas--Henderson--Paradise": "Las Vegas", "Miami--Fort Lauderdale": "Miami",
    "Seattle--Tacoma": "Seattle", "Virginia Beach--Norfolk": "Virginia Beach",
    "Nashville-Davidson": "Nashville",
}

REGIONS = {
    "Greater Southern California": [
        "Los Angeles--Long Beach--Anaheim", "Riverside--San Bernardino",
        "Mission Viejo--Lake Forest--Laguna Niguel", "Santa Clarita", "Thousand Oaks",
        "Simi Valley", "Oxnard--San Buenaventura (Ventura)", "Camarillo", "Palmdale--Lancaster",
        "Temecula--Murrieta--Menifee", "Victorville--Hesperia--Apple Valley"],
    "San Francisco Bay Area": [
        "San Francisco--Oakland", "San Jose", "Concord--Walnut Creek", "Antioch",
        "Livermore--Pleasanton--Dublin", "Vallejo",
        "Fairfield", "Vacaville", "Napa", "Santa Rosa", "Petaluma", "Gilroy--Morgan Hill"],
}


def key(name):
    return name.split(",")[0].strip()


def metrics(pop, miles, dvmt_k):
    return {
        "road_m_per_resident": round(miles * M_PER_MI / pop, 2),
        "residents_per_road_mile": round(pop / miles, 1),
        "daily_vmt_per_road_mile": round(dvmt_k * 1000 / miles),
        "daily_vmt_per_resident": round(dvmt_k * 1000 / pop, 1),
    }


rows = list(csv.DictReader(open(ROOT / "data" / "hm71_2024_all_areas.csv")))
for r in rows:
    for c in ("population_2020", "miles_total", "dvmt_k_total"):
        r[c] = int(r[c])

out = []
for r in rows:
    # FHWA sometimes truncates state suffixes (e.g. "Chicago, IL--I"); match on state list only for PR.
    if r["population_2020"] < MIN_POP or r["urbanized_area"].rstrip().endswith(", PR"):
        continue
    k = key(r["urbanized_area"])
    out.append({"urbanized_area": r["urbanized_area"], "label": LABELS.get(k, k),
                "population_2020": r["population_2020"], "public_road_miles": r["miles_total"],
                "daily_vmt_thousands": r["dvmt_k_total"],
                **metrics(r["population_2020"], r["miles_total"], r["dvmt_k_total"])})
out.sort(key=lambda d: -d["road_m_per_resident"])
p = ROOT / "data" / "us-metro-road-per-resident-2024.csv"
with open(p, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print(f"wrote {p} ({len(out)} urbanized areas over {MIN_POP:,})")

by_key = {key(r["urbanized_area"]): r for r in rows}
agg = []
for region, members in REGIONS.items():
    missing = [m for m in members if m not in by_key]
    if missing:
        print(f"skipping {region}: not in input: {missing}")
        continue
    pop = sum(by_key[m]["population_2020"] for m in members)
    miles = sum(by_key[m]["miles_total"] for m in members)
    dvmt = sum(by_key[m]["dvmt_k_total"] for m in members)
    agg.append({"region": region, "urbanized_areas": "; ".join(members), "population_2020": pop,
                "public_road_miles": miles, "daily_vmt_thousands": dvmt, **metrics(pop, miles, dvmt)})
if agg:
    p = ROOT / "data" / "regional-aggregates-2024.csv"
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(agg[0]))
        w.writeheader()
        w.writerows(agg)
    print(f"wrote {p}")

for d in out[:3] + out[-3:]:
    print(f'  {d["label"]:24s} {d["road_m_per_resident"]:5.2f} m/resident')
