from typing import Dict, List
import zipfile, io, os, pandas as pd, requests
from geopy.distance import great_circle
from fastmcp import FastMCP

mcp = FastMCP("mta-subway-tools")

GTFS_ZIP = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
_stops: pd.DataFrame | None = None

def stops() -> pd.DataFrame:
    global _stops
    if _stops is None:
        z = zipfile.ZipFile(io.BytesIO(requests.get(GTFS_ZIP).content))
        _stops = pd.read_csv(z.open("stops.txt"))
    return _stops

@mcp.tool()
def get_nearest_subway_station(lat: float, lon: float) -> Dict:
    """Return the closest station to a point (meters)."""
    s = stops()
    s["dist"] = s.apply(lambda r: great_circle((lat, lon),
                                               (r.stop_lat, r.stop_lon)).meters, axis=1)
    n = s.nsmallest(1, "dist").iloc[0]
    return {"station_id": n.stop_id, "stop_name": n.stop_name, "distance_m": round(n.dist, 1)}

@mcp.tool()
def plan_subway_trip(o_lat: float, o_lon: float, d_lat: float, d_lon: float) -> Dict:
    """High‑level snap‑to‑station planner (placeholder)."""
    return {
        "origin": get_nearest_subway_station(o_lat, o_lon)["stop_name"],
        "dest":   get_nearest_subway_station(d_lat, d_lon)["stop_name"],
        "note":   "Plug a RAPTOR engine here for full routing."
    }

if __name__ == "__main__":
    mcp.run()
