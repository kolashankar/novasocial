#!/usr/bin/env python3
"""
Simple test script to check reels endpoints
"""

import requests
import json

BACKEND_URL = "http://localhost:8001/api"

def test_filter_presets():
    """Test the filter presets endpoint"""
    print("Testing GET /api/reels/filters/presets...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/reels/filters/presets")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Filters: {len(data.get('filters', []))}")
            print(f"AR Effects: {len(data.get('arEffects', []))}")
            return True
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_auth_endpoint():
    """Test a known working endpoint"""
    print("Testing GET /api/auth/me (should return 401)...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=== Simple Reels Endpoint Test ===")
    
    # Test auth endpoint first to verify API is working
    print("\n1. Testing known working endpoint:")
    auth_works = test_auth_endpoint()
    
    print("\n2. Testing reels filter presets:")
    reels_works = test_filter_presets()
    
    print(f"\nResults:")
    print(f"Auth endpoint working: {auth_works}")
    print(f"Reels endpoint working: {reels_works}")

if __name__ == "__main__":
    main()