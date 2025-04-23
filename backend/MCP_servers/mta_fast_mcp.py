import zipfile
import io
import os
import requests
import logging
import datetime
import pytz
from datetime import timedelta
from typing import Dict
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import great_circle
from dotenv import load_dotenv
import os
load_dotenv()

import r5py
from fastmcp import FastMCP
import logging
import sys
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(
    "http://localhost:9200",
    headers={
        "Accept": "application/vnd.elasticsearch+json;compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json;compatible-with=8"
    }
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
mcp = FastMCP("mta-subway-tools")

GTFS_ZIP = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
OSM_PBF_URL = "https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf"

_stops = None
_transport_network = None

def stops() -> pd.DataFrame:
    global _stops
    if _stops is None:
        resp = requests.get(GTFS_ZIP)
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        logger.info("Reading stops.txt from GTFS zip (in-memory)")
        _stops = pd.read_csv(z.open("stops.txt"))
    return _stops

def get_nearest_poi(name: str):
    """
    Returns the (lat, lon) tuple of the nearest POI using Elasticsearch.
    """
    res = es.search(
        index="points_of_interest",
        body={
            "query": {
                "match": {
                    "name": name
                }
            }
        }
    )
    hits = res["hits"]["hits"]
    if hits:
        loc = hits[0]["_source"]["location"]
        return loc["lat"], loc["lon"]
    else:
        return None

def get_transport_network():
    global _transport_network
    if _transport_network is None:
        logger.info("Creating r5py.TransportNetwork")
        cache_dir = os.path.expanduser("~/.cache/r5py")
        logger.info(f"Using cache directory: {cache_dir}")
        os.makedirs(cache_dir, exist_ok=True)
        gtfs_path = os.path.join(cache_dir, "gtfs.zip")
        osm_path = os.path.join(cache_dir, "nyc.osm.pbf")
        logger.info(f"Checking for GTFS at {gtfs_path} and OSM at {osm_path}")
        if not os.path.exists(gtfs_path):
            logger.info(f"Downloading GTFS zip to {gtfs_path}")
            with open(gtfs_path, "wb") as f:
                f.write(requests.get(GTFS_ZIP).content)
        if not os.path.exists(osm_path):
            logger.info(f"Downloading OSM PBF to {osm_path}")
            with open(osm_path, "wb") as f:
                f.write(requests.get(OSM_PBF_URL).content)
        logger.info(f"Creating r5py.TransportNetwork with OSM: {osm_path}, GTFS: {gtfs_path}")
        logger.info(f"OSM path exists: {os.path.exists(osm_path)}, GTFS path exists: {os.path.exists(gtfs_path)}")
        logger.info(f"OSM path type: {type(osm_path)}, GTFS path type: {type(gtfs_path)}")
        
        _transport_network = r5py.TransportNetwork(osm_path, gtfs_path)
    return _transport_network

@mcp.tool()
def get_nearest_subway_station(lat: float, lon: float) -> Dict:
    """Return the closest station to a point (meters)."""
    logger.info(f"Finding nearest station to ({lat}, {lon})")
    stops_df = stops()
    logger.info(f"Found {len(stops_df)} stations")
    stops_df["dist"] = stops_df.apply(lambda r: great_circle((lat, lon), (r.stop_lat, r.stop_lon)).meters, axis=1)
    n = stops_df.nsmallest(1, "dist").iloc[0]
    return {"station_id": n.stop_id, "stop_name": n.stop_name, "distance_m": round(n.dist, 1)}

@mcp.tool()
def plan_subway_trip(origin: str, destination: str) -> Dict:
    """Find optimal transit route between two points using r5py."""
    origin_coords = get_nearest_poi(origin)
    destination_coords = get_nearest_poi(destination)
    if origin_coords is None or destination_coords is None:
        return {"error": "Origin or destination POI not found."}
    origin_lat, origin_lon = origin_coords
    destination_lat, destination_lon = destination_coords
    logger.info(f"Origin: ({origin_lat}, {origin_lon}), Destination: ({destination_lat}, {destination_lon})")

    origin = get_nearest_subway_station(origin_lat, origin_lon)
    destination = get_nearest_subway_station(destination_lat, destination_lon)

    try:
        transport_network = get_transport_network()

        # Build GeoDataFrames
        origins = gpd.GeoDataFrame({
            "id": ["origin"],
            "geometry": [Point(origin_lon, origin_lat)]
        }, geometry="geometry", crs="EPSG:4326")

        destinations = gpd.GeoDataFrame({
            "id": ["destination"],
            "geometry": [Point(destination_lon, destination_lat)]
        }, geometry="geometry", crs="EPSG:4326")

        # Timezone-aware departure at 8:00 AM NYC
        ny_tz = pytz.timezone("America/New_York")
        departure = datetime.datetime.now(ny_tz)

        # Compute travel time matrix using supported r5py API
        travel_time_matrix = r5py.TravelTimeMatrix(
            transport_network,
            origins=origins,
            destinations=destinations,
            departure=departure,
            transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
        )

        if not travel_time_matrix.empty:
            travel_time_minutes = travel_time_matrix.iloc[0]["travel_time"]
            import math
            rounded_minutes = math.ceil(travel_time_minutes)
            arrival_time = departure + timedelta(minutes=rounded_minutes)

            return {
                "origin": origin["stop_name"],
                "origin_lat": origin_lat,
                "origin_lon": origin_lon,
                "destination": destination["stop_name"],
                "destination_lat": destination_lat,
                "destination_lon": destination_lon,
                "travel_time_minutes": round(travel_time_minutes, 1),
                "departure_time": departure.strftime("%H:%M"),
                "arrival_time": arrival_time.strftime("%H:%M"),
            }
        else:
            return {
                "origin": origin["stop_name"],
                "origin_lat": origin_lat,
                "origin_lon": origin_lon,
                "destination": destination["stop_name"],
                "destination_lat": destination_lat,
                "destination_lon": destination_lon,
                "message": "No route found between these locations."
            }

    except Exception as e:
        return {
            "origin": origin["stop_name"],
            "destination": destination["stop_name"],
            "error": str(e),
            "message": "Error using r5py for routing."
        }

def test_subway_router():
    test_cases = [
        ("33rd street", "Battery Park"),
        ("33rd street", "Battery Park"),
        ("33rd street", "Battery Park"),
        ("33rd street", "Battery Park"),
    ]
    for i, (o_name, d_name) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {o_name} to {d_name}")
        result = plan_subway_trip(o_name, d_name)
        if 'error' in result:
            logger.error(f"Error: {result['error']}")
        elif 'message' in result:
            print(f"Message: {result['message']}")
        else:
            print(f"From {result['origin']} to {result['destination']}:")
            print(f" • Travel time: {result['travel_time_minutes']} min")
            print(f" • Departure time: {result['departure_time']}")
            print(f" • Arrival time: {result['arrival_time']}")

def test_get_nearest_subway_station():
    test_cases = [
        ("Grand Central"),
        ("Vessel"),
        ("Harlem"),
        ("MoMA"),
        ("Flatiron"),
        ("Holland Tunnel Vent Shaft"),
    ]
    for i, (o_name) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {o_name}")
        result = get_nearest_poi(o_name)
        o_lat, o_lon = result
        if 'error' in result:
            logger.error(f"Error: {result['error']}")
        elif 'message' in result:
            print(f"Message: {result['message']}")
        else:
            print(f"Geopoint: {o_name}:({o_lat}, {o_lon})")

if __name__ == "__main__":
    try:
        print("Starting server...", flush=True)
        mcp.run()
    except KeyboardInterrupt:
        # Do not log or print here; just exit silently
        sys.exit(0)
    except Exception as e:
        # Optionally log only if sys.stderr is open
        try:
            import sys
            if sys.stderr:
                print(f"Unhandled exception: {e}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
