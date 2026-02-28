#!/usr/bin/env python3
"""
Test script for IPO Scraper API
Run this to verify everything works before deploying
"""

import requests
import json

def test_api(base_url="http://localhost:5000"):
    """Test all API endpoints"""
    
    print("🧪 Testing IPO Scraper API")
    print("=" * 50)
    
    # Test 1: Home endpoint
    print("\n1. Testing home endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: All IPOs
    print("\n2. Testing /api/ipos...")
    try:
        response = requests.get(f"{base_url}/api/ipos")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {data.get('success')}")
        if data.get('success'):
            current = len(data['data']['current'])
            upcoming = len(data['data']['upcoming'])
            print(f"   Current IPOs: {current}")
            print(f"   Upcoming IPOs: {upcoming}")
            
            # Show first IPO
            if data['data']['current']:
                ipo = data['data']['current'][0]
                print(f"\n   Sample Current IPO:")
                print(f"      Company: {ipo['company']}")
                print(f"      Price: ₹{ipo['priceLow']}-₹{ipo['priceHigh']}")
                print(f"      Dates: {ipo['openDate']} to {ipo['closeDate']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Current IPOs only
    print("\n3. Testing /api/ipos/current...")
    try:
        response = requests.get(f"{base_url}/api/ipos/current")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Count: {data.get('count', 0)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Upcoming IPOs only
    print("\n4. Testing /api/ipos/upcoming...")
    try:
        response = requests.get(f"{base_url}/api/ipos/upcoming")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Count: {data.get('count', 0)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Tests complete!")
    print("\nNext steps:")
    print("1. If all tests passed, deploy to Railway/Render")
    print("2. Update your iOS app with the deployed URL")
    print("3. Test from your iPhone app!")

if __name__ == "__main__":
    import sys
    
    # Allow testing deployed URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Testing deployed API at: {url}")
        test_api(url)
    else:
        print("Testing local API at: http://localhost:5000")
        print("(Make sure you ran 'python app.py' first!)")
        print()
        test_api()
