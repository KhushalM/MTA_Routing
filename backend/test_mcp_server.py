#!/usr/bin/env python3
"""
Test script to validate MCP server functionality.
This tests the core functionality without requiring a full environment setup.
"""

def test_imports():
    """Test if all required imports work."""
    try:
        import requests
        import zipfile
        import io
        import os
        import logging
        import datetime
        import pytz
        from datetime import timedelta
        from typing import Dict
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_heavy_imports():
    """Test heavy scientific computing imports."""
    try:
        import pandas as pd
        import geopandas as gpd
        from shapely.geometry import Point
        from geopy.distance import great_circle
        print("✅ Scientific computing imports successful")
        return True
    except ImportError as e:
        print(f"⚠️  Scientific computing import error: {e}")
        print("   This may be due to environment issues but the server may still work")
        return False

def test_mcp_imports():
    """Test MCP-specific imports."""
    try:
        from fastmcp import FastMCP
        print("✅ FastMCP import successful")
        return True
    except ImportError as e:
        print(f"❌ FastMCP import error: {e}")
        print("   Install with: pip install fastmcp")
        return False

def test_r5py_import():
    """Test r5py import."""
    try:
        import r5py
        print("✅ r5py import successful")
        return True
    except ImportError as e:
        print(f"❌ r5py import error: {e}")
        print("   Install with: pip install r5py==1.0.3")
        return False

def test_elasticsearch_optional():
    """Test Elasticsearch import (optional)."""
    try:
        from elasticsearch import Elasticsearch
        print("✅ Elasticsearch import successful")
        return True
    except ImportError as e:
        print(f"⚠️  Elasticsearch import error: {e}")
        print("   This is optional - server will work with coordinates")
        return False

def test_gtfs_download():
    """Test GTFS data download."""
    try:
        import requests
        url = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print("✅ GTFS data source accessible")
            return True
        else:
            print(f"⚠️  GTFS data source returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  GTFS data source test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚇 MTA MCP Server Validation")
    print("=" * 40)
    
    tests = [
        ("Basic imports", test_imports),
        ("Scientific computing", test_heavy_imports),
        ("FastMCP", test_mcp_imports),
        ("r5py routing engine", test_r5py_import),
        ("Elasticsearch (optional)", test_elasticsearch_optional),
        ("GTFS data access", test_gtfs_download),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        result = test_func()
        results.append((name, result))
    
    print("\n📊 Test Results:")
    print("=" * 40)
    critical_passed = 0
    total_critical = 0
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
        
        # Critical tests
        if name in ["Basic imports", "FastMCP", "r5py routing engine"]:
            total_critical += 1
            if passed:
                critical_passed += 1
    
    print(f"\n🎯 Critical tests: {critical_passed}/{total_critical}")
    
    if critical_passed == total_critical:
        print("✅ MCP server should work! You can run:")
        print("   python MCP_servers/mta_fast_mcp.py")
    else:
        print("❌ Missing critical dependencies. Install requirements:")
        print("   pip install -r requirements.txt")
    
    return critical_passed == total_critical

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
