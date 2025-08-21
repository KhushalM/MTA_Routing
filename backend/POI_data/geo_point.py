from elasticsearch import Elasticsearch, helpers
import csv
import json

es = Elasticsearch(
    "http://localhost:9200",
    headers={
        "Accept": "application/vnd.elasticsearch+json;compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json;compatible-with=8"
    }
)

mapping = {
    "mappings": {
        "properties": {
            "name": {"type": "text"},
            "location": {"type": "geo_point"},
            # Add other fields as needed
        }
    }
}

es.indices.create(index="points_of_interest", body=mapping, ignore=400)

def parse_geom(geom_str):
    # Example: 'POINT (-74.00701717096757 40.724634757833414)'
    parts = geom_str.strip().replace("POINT (", "").replace(")", "").split()
    lon, lat = map(float, parts)
    return {"lon": lon, "lat": lat}

actions = []
# Get the directory of this script and find the CSV file relative to it
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "Points_of_Interest_20250422.csv")
with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        doc = {
            "name": row["NAME"],
            "location": parse_geom(row["the_geom"]),
            # Add other fields as needed
        }
        actions.append({
            "_index": "points_of_interest",
            "_source": doc
        })

if actions:
    helpers.bulk(es, actions)
    print(f"Indexed {len(actions)} POIs.")
else:
    print("No POIs found in CSV.")