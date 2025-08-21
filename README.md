# MTA MCP Server: Subway Routing with RAPTOR 

## How This MCP Server Was Created
This MCP server demonstrates the process of building a custom Model Context Protocol server from scratch. The development involved:

1. **Identifying the Domain Problem:** NYC subway routing needed a programmatic solution for AI assistants
2. **Choosing the Right Libraries:** Selected r5py for RAPTOR algorithm implementation and GeoPandas for spatial data handling
3. **Implementing MCP Protocol:** Built proper tool definitions with JSON schemas following MCP specifications
4. **Data Integration:** Connected to MTA's official GTFS feed and OpenStreetMap data sources
5. **Optimization:** Added intelligent caching mechanisms to minimize data downloads and improve performance
6. **Tool Design:** Created intuitive routing tools that AI assistants can easily understand and use

The result is a production-ready MCP server that any AI assistant can integrate to provide accurate NYC subway routing capabilities.

## Overview
This project provides an MCP (Modular Command Protocol) server for New York City subway routing using the RAPTOR algorithm via the [r5py](https://github.com/r5py/r5py) library. It exposes routing tools for integration with tool-using AI assistants and other systems.

## Features
- **Subway routing:** Computes optimal routes between NYC subway stations using GTFS and OSM data.
- **RAPTOR algorithm:** Utilizes r5py's Python bindings for the R5 engine, which implements the RAPTOR algorithm for rapid public transit routing.
- **GeoDataFrame support:** Uses GeoPandas and Shapely for spatial data handling.

## How It Works
1. **GTFS/OSM Data:**
   - The server downloads and caches MTA's official GTFS feed and OSM street data for NYC.
   - GTFS zip URL: `https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip`
2. **Transport Network:**
   - r5py builds a multimodal transport network from these files.
   - Data is cached in `~/.cache/r5py` to avoid repeated downloads.
3. **Routing:**
   - The server exposes endpoints/tools (e.g., `plan_subway_trip`) that compute the fastest route between two points.
   - Uses the RAPTOR algorithm under the hood for efficient and accurate results.

## Installation

### Option 1: With pip (Recommended)
1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd MTA_Routing/backend
   ```

2. **Important**: Use a clean Python environment to avoid conflicts:
   ```sh
   # Using venv (recommended)
   python -m venv mcp_env
   source mcp_env/bin/activate  # On Windows: mcp_env\Scripts\activate
   
   # Or using conda
   conda create -n mcp_env python=3.10
   conda activate mcp_env
   ```

3. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Validate installation:
   ```sh
   python test_mcp_server.py
   ```

5. Set up POI data (optional but recommended):
   ```sh
   python setup_poi_data.py
   ```

### Option 2: With uv
1. Install [uv](https://github.com/astral-sh/uv):
   ```sh
   pip install uv
   # or
   brew install uv
   ```

2. Install dependencies:
   ```sh
   cd backend
   uv pip install -r requirements.txt
   ```

3. Set up POI data:
   ```sh
   python setup_poi_data.py
   ```

## Usage

### Running the MCP Server
```sh
cd backend
python MCP_servers/mta_fast_mcp.py
```

### Using with AI Assistants
To use as part of a tool-using AI assistant, ensure the MCP server is launched and connected via stdio as per your system's MCP client configuration.

### Available Tools
1. **`plan_subway_trip(origin, destination)`** - Route between named locations or coordinates
2. **`plan_subway_trip_coordinates(origin_lat, origin_lon, destination_lat, destination_lon)`** - Route between exact coordinates
3. **`get_nearest_subway_station(lat, lon)`** - Find closest subway station to coordinates

### Input Formats
- **Named locations**: "Times Square", "Central Park", etc. (requires POI data setup)
- **Coordinates**: "40.7589,-73.9851" (latitude,longitude format)
- **Direct coordinates**: Use the coordinates tool with separate lat/lon parameters

## How RAPTOR Works
- RAPTOR (Round-based Public Transit Optimized Router) is a fast, exact algorithm for computing optimal public transit routes.
- It efficiently finds the fastest path between origins and destinations using timetable data (GTFS).
- r5py provides a Python API to the R5 engine, which implements RAPTOR and supports multimodal routing (transit + walking).

## Data Sources
- **GTFS:** Official MTA subway feed ([gtfs_subway.zip](https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip))
- **OSM:** OpenStreetMap PBF for NYC

## Troubleshooting

### Common Issues
1. **"Elasticsearch not available"** - This is normal if you haven't set up POI data. The server will work with coordinate inputs.
2. **Import errors (numpy/pandas)** - Use a clean Python environment (venv/conda) to avoid library conflicts. 
3. **"No module named 'fastmcp'"** - Run `pip install fastmcp` in your active environment.
4. **r5py network building fails** - Check internet connection for GTFS/OSM downloads. Files are cached in `~/.cache/r5py`.
5. **No route found** - Ensure coordinates are within NYC area and transit operates at the requested time.
6. **Memory issues** - r5py network building requires significant RAM. Close other applications if needed.

### Running Without Elasticsearch
The MCP server works without Elasticsearch by using coordinates:
```python
# Instead of: plan_subway_trip("Times Square", "Central Park")
# Use coordinates: plan_subway_trip("40.7589,-73.9851", "40.7794,-73.9632")
# Or use the direct coordinate tool
```

## Project Structure
- `backend/MCP_servers/mta_fast_mcp.py` — Main MCP server code for subway routing
- `backend/requirements.txt` — Python dependencies
- `backend/test_mcp_server.py` — Validation script to test installation
- `backend/setup_poi_data.py` — Setup script for POI data and Elasticsearch
- `backend/POI_data/` — Points of Interest data and loading scripts
- `docker-compose.yml` — Docker setup including Elasticsearch

## License
GPL-3.0-or-later or MIT (per r5py)

---

*This project is intended for research and development purposes. For production, always check GTFS data freshness and R5/r5py updates.*
