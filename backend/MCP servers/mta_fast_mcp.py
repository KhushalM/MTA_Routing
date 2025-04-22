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
def plan_subway_trip(o_lat: float, o_lon: float, d_lat: float, d_lon: float) -> Dict:
    """Find optimal transit route between two points using r5py."""
    origin = get_nearest_subway_station(o_lat, o_lon)
    dest = get_nearest_subway_station(d_lat, d_lon)

    try:
        transport_network = get_transport_network()

        # Build GeoDataFrames
        origins = gpd.GeoDataFrame({
            "id": ["origin"],
            "geometry": [Point(o_lon, o_lat)]
        }, geometry="geometry", crs="EPSG:4326")

        destinations = gpd.GeoDataFrame({
            "id": ["destination"],
            "geometry": [Point(d_lon, d_lat)]
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
                "destination": dest["stop_name"],
                "travel_time_minutes": round(travel_time_minutes, 1),
                "departure_time": departure.strftime("%H:%M"),
                "arrival_time": arrival_time.strftime("%H:%M"),
            }
        else:
            return {
                "origin": origin["stop_name"],
                "destination": dest["stop_name"],
                "message": "No route found between these locations."
            }

    except Exception as e:
        return {
            "origin": origin["stop_name"],
            "destination": dest["stop_name"],
            "error": str(e),
            "message": "Error using r5py for routing."
        }

def test_subway_router():
    test_cases = [
        (40.7128, -74.0060, 40.7580, -73.9855, "Downtown to Midtown"),
        (40.6782, -73.9442, 40.7831, -73.9712, "Brooklyn to Upper East Side"),
        (40.7505, -73.8854, 40.7831, -73.9712, "Queens to Upper East Side"),
        (40.7527, -73.9772, 40.7589, -73.9851, "Short Manhattan trip")
    ]
    for i, (o_lat, o_lon, d_lat, d_lon, desc) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {desc}")
        result = plan_subway_trip(o_lat, o_lon, d_lat, d_lon)
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
        (40.7128, -74.0060, "Downtown"),
        (40.6782, -73.9442, "Brooklyn"),
        (40.7505, -73.8854, "Queens"),
        (40.7527, -73.9772, "Manhattan")
    ]
    for i, (lat, lon, desc) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {desc}")
        result = get_nearest_subway_station(lat, lon)
        if 'error' in result:
            logger.error(f"Error: {result['error']}")
        elif 'message' in result:
            print(f"Message: {result['message']}")
        else:
            print(f"Closest station: {result['stop_name']} ({result['distance_m']}m)")

if __name__ == "__main__":
    test_subway_router()
    test_get_nearest_subway_station()
    mcp.run()
