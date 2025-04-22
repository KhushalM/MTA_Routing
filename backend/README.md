# MTA MCP Server: Subway Routing with RAPTOR

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
1. Clone this repository.
2. Install Python 3.11+ and [Java 21+](https://adoptium.net/).
3. Create a virtual environment:
   ```sh
   python3 -m venv XQ
   source XQ/bin/activate
   ```
4. Install requirements:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
To run the MTA MCP server directly:
```sh
python MCP\ servers/mta_fast_mcp.py
```

To use as part of a tool-using AI assistant, ensure the MCP server is launched and connected via stdio as per your system's architecture.

## How RAPTOR Works
- RAPTOR (Round-based Public Transit Optimized Router) is a fast, exact algorithm for computing optimal public transit routes.
- It efficiently finds the fastest path between origins and destinations using timetable data (GTFS).
- r5py provides a Python API to the R5 engine, which implements RAPTOR and supports multimodal routing (transit + walking).

## Data Sources
- **GTFS:** Official MTA subway feed ([gtfs_subway.zip](https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip))
- **OSM:** OpenStreetMap PBF for NYC

## Project Structure
- `MCP servers/mta_fast_mcp.py` — Main MCP server code for subway routing
- `requirements.txt` — Python dependencies

## License
GPL-3.0-or-later or MIT (per r5py)

---

*This project is intended for research and development purposes. For production, always check GTFS data freshness and R5/r5py updates.*
