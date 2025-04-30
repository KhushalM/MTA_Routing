import zipfile
import io
import os
import requests
import logging
import datetime
import pytz
from datetime import timedelta
from typing import Dict, List
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import great_circle
from dotenv import load_dotenv
import time
from collections import defaultdict
import sys
from elasticsearch import Elasticsearch, helpers
import google.transit.gtfs_realtime_pb2 as gtfs_realtime_pb2
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Setup Elasticsearch
es = Elasticsearch(
    "http://localhost:9200",
    headers={
        "Accept": "application/vnd.elasticsearch+json;compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json;compatible-with=8"
    }
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
mcp = FastMCP("mta-subway-tools")

# Constants
GTFS_ZIP = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
OSM_PBF_URL = "https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf"

# MTA GTFS Realtime feed URLs - publicly accessible
MTA_FEEDS = {
    '123456S': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs',  # 1,2,3,4,5,6,S lines
    'L': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l',  # L line
    'G': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g',  # G line
    'NQRW': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw',  # N,Q,R,W lines
    'BDFM': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm',  # B,D,F,M lines
    'ACE': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace',  # A,C,E lines
    'SI': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si',  # Staten Island Railway
    'JZ': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz',  # J,Z lines
}

# Cached data
_stops = None
_routes = None
_trips = None
_stop_times = None
_transport_network = None
_trip_updates_cache = {}
_alerts_cache = []
_vehicle_positions_cache = {}
_last_refresh_time = 0
_refresh_interval = 30  # seconds

# Static data functions
def stops() -> pd.DataFrame:
    """Get stops data from GTFS static feed"""
    global _stops
    if _stops is None:
        resp = requests.get(GTFS_ZIP)
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        logger.info("Reading stops.txt from GTFS zip (in-memory)")
        _stops = pd.read_csv(z.open("stops.txt"))
    return _stops

def routes() -> pd.DataFrame:
    """Get routes data from GTFS static feed"""
    global _routes
    if _routes is None:
        resp = requests.get(GTFS_ZIP)
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        logger.info("Reading routes.txt from GTFS zip (in-memory)")
        _routes = pd.read_csv(z.open("routes.txt"))
    return _routes

def trips() -> pd.DataFrame:
    """Get trips data from GTFS static feed"""
    global _trips
    if _trips is None:
        resp = requests.get(GTFS_ZIP)
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        logger.info("Reading trips.txt from GTFS zip (in-memory)")
        _trips = pd.read_csv(z.open("trips.txt"))
    return _trips

def stop_times() -> pd.DataFrame:
    """Get stop_times data from GTFS static feed"""
    global _stop_times
    if _stop_times is None:
        resp = requests.get(GTFS_ZIP)
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        logger.info("Reading stop_times.txt from GTFS zip (in-memory)")
        _stop_times = pd.read_csv(z.open("stop_times.txt"))
    return _stop_times

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
        
        import r5py
        _transport_network = r5py.TransportNetwork(osm_path, gtfs_path)
    return _transport_network

# GTFS Realtime Functions
def get_realtime_data(refresh=False):
    """Fetch and parse real-time GTFS data from all MTA feeds"""
    global _last_refresh_time, _trip_updates_cache, _alerts_cache, _vehicle_positions_cache
    
    current_time = time.time()
    if not refresh and current_time - _last_refresh_time < _refresh_interval:
        logger.info("Using cached real-time data")
        return _trip_updates_cache, _alerts_cache, _vehicle_positions_cache
    
    logger.info("Fetching fresh real-time data from MTA")
    _last_refresh_time = current_time
    
    trip_updates = defaultdict(dict)
    alerts = []
    vehicle_positions = defaultdict(dict)
    
    for line_id, url in MTA_FEEDS.items():
        try:
            response = requests.get(url)
            if response.status_code != 200:
                logger.warning(f"Failed to get data for {line_id}: {response.status_code}")
                continue
                
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)
            
            # Process trip updates
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    trip_id = entity.trip_update.trip.trip_id
                    trip_updates[trip_id] = {
                        'line_group': line_id,
                        'route_id': entity.trip_update.trip.route_id,
                        'start_time': entity.trip_update.trip.start_time,
                        'start_date': entity.trip_update.trip.start_date,
                        'stop_time_updates': []
                    }
                    
                    for stu in entity.trip_update.stop_time_update:
                        stop_update = {
                            'stop_id': stu.stop_id,
                            'scheduled_arrival': stu.arrival.time if stu.HasField('arrival') else None,
                            'scheduled_departure': stu.departure.time if stu.HasField('departure') else None,
                            'delay': stu.arrival.delay if stu.HasField('arrival') else None
                        }
                        trip_updates[trip_id]['stop_time_updates'].append(stop_update)
                
                # Process service alerts
                if entity.HasField('alert'):
                    alert = {
                        'id': entity.id,
                        'effect': gtfs_realtime_pb2.Alert.Effect.Name(entity.alert.effect),
                        'header': entity.alert.header_text.translation[0].text if entity.alert.header_text.translation else "",
                        'description': entity.alert.description_text.translation[0].text if entity.alert.description_text.translation else "",
                        'affected_routes': [e.route_id for e in entity.alert.informed_entity if e.HasField('route_id')],
                        'affected_stops': [e.stop_id for e in entity.alert.informed_entity if e.HasField('stop_id')]
                    }
                    alerts.append(alert)
                
                # Process vehicle positions
                if entity.HasField('vehicle'):
                    vehicle = entity.vehicle
                    vehicle_id = vehicle.vehicle.id if vehicle.HasField('vehicle') else vehicle.trip.trip_id
                    vehicle_positions[vehicle_id] = {
                        'trip_id': vehicle.trip.trip_id,
                        'route_id': vehicle.trip.route_id,
                        'latitude': vehicle.position.latitude,
                        'longitude': vehicle.position.longitude,
                        'bearing': vehicle.position.bearing,
                        'current_stop_sequence': vehicle.current_stop_sequence,
                        'current_status': gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.Name(vehicle.current_status),
                        'timestamp': vehicle.timestamp
                    }
        
        except Exception as e:
            logger.error(f"Error processing {line_id} feed: {str(e)}")
    
    _trip_updates_cache = trip_updates
    _alerts_cache = alerts
    _vehicle_positions_cache = vehicle_positions
    
    logger.info(f"Fetched {len(trip_updates)} trip updates, {len(alerts)} alerts, {len(vehicle_positions)} vehicle positions")
    return trip_updates, alerts, vehicle_positions

# Tools
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

        # Timezone-aware departure at current time in NYC
        ny_tz = pytz.timezone("America/New_York")
        departure = datetime.datetime.now(ny_tz)

        # Compute travel time matrix using supported r5py API
        import r5py
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
                "destination": destination["stop_name"],
                "message": "No route found between these locations."
            }

    except Exception as e:
        return {
            "origin": origin["stop_name"],
            "destination": destination["stop_name"],
            "error": str(e),
            "message": "Error using r5py for routing."
        }

@mcp.tool()
def get_station_arrivals(station_name: str, limit: int = 10) -> Dict:
    """Get upcoming arrivals at a specific station with real-time data."""
    # First, find the station ID from the name
    stops_df = stops()
    lat, lon = get_nearest_poi(station_name)
    station_name = get_nearest_subway_station(lat, lon)
    station_name = station_name['stop_name']
    station_matches = stops_df[stops_df['stop_name'].str.contains(station_name, case=False)]
    
    if station_matches.empty:
        return {"error": f"No station found matching '{station_name}'"}
    
    # Use the first matching station (could be enhanced to find best match)
    station = station_matches.iloc[0]
    station_id = station.stop_id
    station_name = station.stop_name
    
    # Get real-time data
    trip_updates, alerts, _ = get_realtime_data()
    
    # Find all stop time updates for this station
    arrivals = []
    current_time = int(time.time())
    
    for trip_id, trip_data in trip_updates.items():
        for stop_update in trip_data['stop_time_updates']:
            # Check if stop ID in GTFS-RT matches our target station
            # MTA prefixes stop IDs with "MTASBWY:" in real-time data
            if stop_update['stop_id'] == f"MTASBWY:{station_id}" and stop_update['scheduled_arrival']:
                # Only include future arrivals
                if stop_update['scheduled_arrival'] > current_time:
                    arrival_time = datetime.datetime.fromtimestamp(
                        stop_update['scheduled_arrival'], 
                        pytz.timezone("America/New_York")
                    )
                    
                    # Get route info (color, description)
                    route_id = trip_data['route_id']
                    
                    arrivals.append({
                        'route_id': route_id,
                        'trip_id': trip_id,
                        'arrival_time': arrival_time.strftime("%H:%M:%S"),
                        'delay': stop_update['delay'] if stop_update['delay'] else 0,
                        'minutes_until_arrival': round((stop_update['scheduled_arrival'] - current_time) / 60, 1)
                    })
    
    # Sort by arrival time
    arrivals.sort(key=lambda x: x['minutes_until_arrival'])
    
    # Get relevant service alerts
    station_alerts = []
    for alert in alerts:
        if f"MTASBWY:{station_id}" in alert['affected_stops']:
            station_alerts.append({
                'effect': alert['effect'],
                'header': alert['header'],
                'description': alert['description'],
            })
    
    return {
        'station_id': station_id,
        'station_name': station_name,
        'current_time': datetime.datetime.now(pytz.timezone("America/New_York")).strftime("%H:%M:%S"),
        'arrivals': arrivals[:limit],
        'alerts': station_alerts
    }

@mcp.tool()
def get_line_status() -> List[Dict]:
    """Get the current status of all subway lines."""
    # Get real-time data
    trip_updates, alerts, vehicle_positions = get_realtime_data()
    
    # Get routes data for details
    routes_df = routes()
    
    # Count active vehicles and alerts by route
    line_status = []
    route_groups = {}
    
    # Group vehicle positions by route
    for vehicle_id, vehicle_data in vehicle_positions.items():
        route_id = vehicle_data['route_id']
        if route_id not in route_groups:
            route_groups[route_id] = []
        route_groups[route_id].append(vehicle_id)
    
    # Process each route
    for _, route in routes_df.iterrows():
        route_id = route['route_id']
        
        # Count active vehicles for this route
        active_vehicles = len(route_groups.get(route_id, []))
        
        # Find alerts affecting this route
        route_alerts = [
            alert for alert in alerts 
            if route_id in alert['affected_routes']
        ]
        
        # Get service status based on alerts
        service_status = "Good Service"
        if route_alerts:
            effects = [alert['effect'] for alert in route_alerts]
            if 'SIGNIFICANT_DELAYS' in effects:
                service_status = "Delays"
            elif 'DETOUR' in effects:
                service_status = "Detour"
            elif 'REDUCED_SERVICE' in effects:
                service_status = "Reduced Service"
            elif 'SUSPENSION' in effects:
                service_status = "Suspended"
            elif 'PLANNED' in effects or 'PLANNED_DETOUR' in effects:
                service_status = "Planned Work"
            else:
                service_status = "Service Change"
        
        line_status.append({
            'route_id': route_id,
            'route_long_name': route['route_long_name'],
            'route_color': f"#{route['route_color']}" if 'route_color' in route else None,
            'service_status': service_status,
            'active_vehicles': active_vehicles,
            'alerts': [{'effect': a['effect'], 'header': a['header']} for a in route_alerts]
        })
    
    return sorted(line_status, key=lambda x: x['route_id'])

@mcp.tool()
def get_real_time_trip_info(origin_station: str, destination_station: str) -> Dict:
    """Get real-time trip information between two stations, falling back to nearest station from POI if needed."""
    stops_df = stops()
    lat, lon = get_nearest_poi(origin_station)
    origin_station = get_nearest_subway_station(lat, lon)
    origin_station = origin_station['stop_name']
    print(f"Origin station: {origin_station}")
    # --- DESTINATION ---
    lat, lon = get_nearest_poi(destination_station)
    destination_station = get_nearest_subway_station(lat, lon)
    destination_station = destination_station['stop_name']
    print(f"Destination station: {destination_station}")
    # --- CONTINUE AS BEFORE ---
    origin_matches = stops_df[stops_df['stop_name'].str.contains(origin_station, case=False)]
    print(f"Origin matches: {origin_matches}")
    if origin_matches.empty:
        # Try to resolve as POI
        poi_coords = get_nearest_poi(origin_station)
        if poi_coords is not None:
            lat, lon = poi_coords
            nearest = get_nearest_subway_station(lat, lon)
            if nearest and 'stop_name' in nearest:
                origin_station_name = nearest['stop_name']
                origin_matches = stops_df[stops_df['stop_name'].str.contains(origin_station_name, case=False)]
        if origin_matches.empty:
            return {"error": f"No station found matching or near '{origin_station}'"}
    origin = origin_matches.iloc[0]

    # --- DESTINATION ---
    dest_matches = stops_df[stops_df['stop_name'].str.contains(destination_station, case=False)]
    print(f"Destination matches: {dest_matches}")
    if dest_matches.empty:
        poi_coords = get_nearest_poi(destination_station)
        if poi_coords is not None:
            lat, lon = poi_coords
            nearest = get_nearest_subway_station(lat, lon)
            if nearest and 'stop_name' in nearest:
                destination_station_name = nearest['stop_name']
                dest_matches = stops_df[stops_df['stop_name'].str.contains(destination_station_name, case=False)]
        if dest_matches.empty:
            return {"error": f"No station found matching or near '{destination_station}'"}
    destination = dest_matches.iloc[0]

    # --- CONTINUE AS BEFORE ---
    trip_updates, alerts, vehicle_positions = get_realtime_data()
    stop_times_df = stop_times()
    trips_df = trips()
    origin_trips = stop_times_df[stop_times_df['stop_id'] == origin.stop_id]['trip_id'].unique()
    dest_trips = stop_times_df[stop_times_df['stop_id'] == destination.stop_id]['trip_id'].unique()
    common_trips = set(origin_trips).intersection(set(dest_trips))
    if len(common_trips) > 0:
        common_routes = trips_df[trips_df['trip_id'].isin(common_trips)]['route_id'].unique()
    else:
        common_routes = []
    if len(common_routes) == 0:
        return {
            "error": "No direct routes found between these stations",
            "origin_station": origin.stop_name,
            "destination_station": destination.stop_name
        }
    routes_df = routes()
    route_status = []
    for route_id in common_routes:
        active_trips = {
            trip_id: trip_data for trip_id, trip_data in trip_updates.items() 
            if trip_data['route_id'] == route_id
        }
        active_vehicles = sum(1 for vp in vehicle_positions.values() if vp['route_id'] == route_id)
        route_alerts = [
            alert for alert in alerts 
            if route_id in alert['affected_routes']
        ]
        route_info = routes_df[routes_df['route_id'] == route_id]
        route_name = route_info['route_long_name'].values[0] if not route_info.empty else "Unknown"
        route_color = f"#{route_info['route_color'].values[0]}" if not route_info.empty and 'route_color' in route_info else None
        route_status.append({
            'route_id': route_id,
            'route_name': route_name,
            'route_color': route_color,
            'active_trips': len(active_trips),
            'active_vehicles': active_vehicles,
            'alerts': [{'effect': a['effect'], 'header': a['header']} for a in route_alerts]
        })
    origin_coords = (origin.stop_lat, origin.stop_lon)
    dest_coords = (destination.stop_lat, destination.stop_lon)
    try:
        transport_network = get_transport_network()
        origins = gpd.GeoDataFrame({
            "id": ["origin"],
            "geometry": [Point(origin.stop_lon, origin.stop_lat)]
        }, geometry="geometry", crs="EPSG:4326")
        destinations = gpd.GeoDataFrame({
            "id": ["destination"],
            "geometry": [Point(destination.stop_lon, destination.stop_lat)]
        }, geometry="geometry", crs="EPSG:4326")
        ny_tz = pytz.timezone("America/New_York")
        departure = datetime.datetime.now(ny_tz)
        import r5py
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
            trip_info = {
                'estimated_travel_time': round(travel_time_minutes, 1),
                'departure_time': departure.strftime("%H:%M:%S"),
                'estimated_arrival_time': arrival_time.strftime("%H:%M:%S")
            }
        else:
            trip_info = {'error': 'No travel time found'}
    except Exception as e:
        trip_info = {'error': str(e)}
    return {
        'origin_station': origin.stop_name,
        'destination_station': destination.stop_name,
        'routes': route_status,
        'trip_info': trip_info
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
        if result is None:
            logger.error(f"Error: POI not found")
            continue
        o_lat, o_lon = result
        print(f"Geopoint: {o_name}:({o_lat}, {o_lon})")

def test_realtime_features():
    """Tests the real-time GTFS features"""
    # Test get_station_arrivals
    print("\n=== Testing get_station_arrivals ===")
    stations = ["Times Square", "Grand Central", "14th Street", "Hudson Yards"]
    for station in stations:
        print(f"\nGetting arrivals for {station}...")
        result = get_station_arrivals(station, limit=5)
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Station: {result['station_name']} (ID: {result['station_id']})")
            print(f"Current time: {result['current_time']}")
            print("Upcoming arrivals:")
            for arrival in result['arrivals']:
                delay_str = f", Delay: {arrival['delay']}s" if arrival['delay'] else ""
                print(f" • {arrival['route_id']} - Arriving in {arrival['minutes_until_arrival']} min ({arrival['arrival_time']}{delay_str})")
            if result['alerts']:
                print("Alerts:")
                for alert in result['alerts']:
                    print(f" • {alert['effect']}: {alert['header']}")
    
    # Test get_line_status
    print("\n=== Testing get_line_status ===")
    result = get_line_status()
    print("Subway line status:")
    for line in result[:5]:  # Show just first 5 for test
        alerts_str = f", {len(line['alerts'])} alerts" if line['alerts'] else ""
        print(f" • {line['route_id']} ({line['route_long_name']}): {line['service_status']} ({line['active_vehicles']} active vehicles{alerts_str})")
    
    # Test get_real_time_trip_info
    print("\n=== Testing get_real_time_trip_info ===")
    trips = [
        ("Times Sq-42 St", "Grand Central-42 St"),
        ("34 Hudson Yards", "50 St"),
        ("14 St-Union Sq", "34 St-Herald Sq"),
        ("34 St-Penn Station", "Chambers St"),
        ("59 St-Columbus Circle", "125 St"),
    ]
    for origin, destination in trips:
        print(f"\nGetting trip info from {origin} to {destination}...")
        result = get_real_time_trip_info(origin, destination)
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"From {result['origin_station']} to {result['destination_station']}")
            print(f"Available routes:")
            for route in result['routes']:
                alerts_str = f", {len(route['alerts'])} alerts" if route['alerts'] else ""
                print(f" • {route['route_id']}: {route['active_trips']} active trips, {route['active_vehicles']} active vehicles{alerts_str}")
            
            if 'trip_info' in result:
                if 'estimated_travel_time' in result['trip_info']:
                    print(f"Estimated travel time: {result['trip_info']['estimated_travel_time']} min")
                if 'departure_time' in result['trip_info']:
                    print(f"Departure time: {result['trip_info']['departure_time']}")
                if 'estimated_arrival_time' in result['trip_info']:
                    print(f"Estimated arrival time: {result['trip_info']['estimated_arrival_time']}")
            else:
                print("Trip info not available")

if __name__ == "__main__":
    test_realtime_features()
    try:
        # Load GTFS-RT dependencies
        try:
            import google.transit.gtfs_realtime_pb2
            logger.info("GTFS Realtime protobuf bindings loaded successfully")
        except ImportError:
            logger.error("GTFS Realtime protobuf bindings not found! Run: pip install gtfs-realtime-bindings")
            logger.info("Starting without real-time capabilities")
        
        # Preload stops data
        logger.info("Preloading static GTFS data...")
        stops_data = stops()
        logger.info(f"Loaded {len(stops_data)} stops")
        
        # Test real-time features if available
        try:
            logger.info("Testing real-time data retrieval...")
            trip_updates, alerts, vehicle_positions = get_realtime_data(refresh=True)
            logger.info(f"Successfully retrieved {len(trip_updates)} trip updates, {len(alerts)} alerts, {len(vehicle_positions)} vehicle positions")
        except Exception as e:
            logger.error(f"Failed to get real-time data: {str(e)}")
        
        print("Starting MTA subway tools server with real-time capabilities...", flush=True)
        mcp.run()
    except KeyboardInterrupt:
        # Do not log or print here; just exit silently
        sys.exit(0)
    except Exception as e:
        # Optionally log only if sys.stderr is open
        try:
            if sys.stderr:
                print(f"Unhandled exception: {e}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
