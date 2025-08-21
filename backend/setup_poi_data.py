#!/usr/bin/env python3
"""
Setup script for MTA MCP Server POI data.
This script sets up Elasticsearch and loads POI data for the MTA routing server.
"""
import os
import sys
import subprocess
import time
from elasticsearch import Elasticsearch

def check_elasticsearch_running():
    """Check if Elasticsearch is running."""
    try:
        es = Elasticsearch("http://localhost:9200")
        es.info()
        return True
    except Exception:
        return False

def wait_for_elasticsearch(max_wait=60):
    """Wait for Elasticsearch to be ready."""
    print("Waiting for Elasticsearch to be ready...")
    for i in range(max_wait):
        if check_elasticsearch_running():
            print("✅ Elasticsearch is ready!")
            return True
        print(f"⏳ Waiting... ({i+1}/{max_wait})")
        time.sleep(1)
    return False

def setup_with_docker():
    """Setup using Docker Compose."""
    print("🐳 Starting Elasticsearch with Docker Compose...")
    try:
        # Start only Elasticsearch service
        subprocess.run(["docker-compose", "up", "-d", "elasticsearch"], 
                      cwd="..", check=True)
        
        if wait_for_elasticsearch():
            load_poi_data()
        else:
            print("❌ Failed to start Elasticsearch with Docker")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker Compose failed: {e}")
        return False
    return True

def load_poi_data():
    """Load POI data into Elasticsearch."""
    print("📍 Loading POI data...")
    try:
        # Import and run the POI loading script
        poi_script_path = os.path.join("POI_data", "geo_point.py")
        if os.path.exists(poi_script_path):
            subprocess.run([sys.executable, poi_script_path], check=True)
            print("✅ POI data loaded successfully!")
        else:
            print(f"❌ POI script not found at {poi_script_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to load POI data: {e}")
        return False
    return True

def main():
    """Main setup function."""
    print("🚇 MTA MCP Server Setup")
    print("=" * 40)
    
    # Check if Elasticsearch is already running
    if check_elasticsearch_running():
        print("✅ Elasticsearch is already running!")
        choice = input("🤔 Do you want to reload POI data? (y/N): ").strip().lower()
        if choice == 'y':
            load_poi_data()
        else:
            print("✅ Setup complete! Elasticsearch is ready.")
        return
    
    print("📋 Elasticsearch is not running. Choose setup method:")
    print("1. Use Docker Compose (recommended)")
    print("2. Manual setup (you handle Elasticsearch)")
    print("3. Skip (run MCP server without POI lookup)")
    
    choice = input("👉 Enter choice (1-3): ").strip()
    
    if choice == "1":
        if setup_with_docker():
            print("\n✅ Setup complete!")
            print("🎯 You can now run the MCP server:")
            print("   python MCP_servers/mta_fast_mcp.py")
        else:
            print("\n❌ Setup failed. Please check Docker and try again.")
    
    elif choice == "2":
        print("\n📋 Manual setup instructions:")
        print("1. Start Elasticsearch on localhost:9200")
        print("2. Run: python setup_poi_data.py")
        print("3. Run: python MCP_servers/mta_fast_mcp.py")
    
    elif choice == "3":
        print("\n⚠️  Running without POI lookup:")
        print("- Use coordinates in 'lat,lon' format for routing")
        print("- Example: plan_subway_trip('40.7589,-73.9851', '40.6892,-74.0445')")
        print("🎯 Run the MCP server: python MCP_servers/mta_fast_mcp.py")
    
    else:
        print("❌ Invalid choice")
        sys.exit(1)

if __name__ == "__main__":
    main()
