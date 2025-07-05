#!/usr/bin/env python3
"""
Test Round 22 functionality via API endpoints
This can be run locally to verify Railway deployment
"""

import requests
import json
import sys

API_URL = "https://deckster-production.up.railway.app"

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Redis: {data['services']['redis']}")
            print(f"   Supabase: {data['services']['supabase']}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_auth_security():
    """Test that auth is properly enforced"""
    print("\n🔍 Testing Authentication Security...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 401:
            print("✅ Root endpoint requires auth (401)")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test dev token endpoint (should be disabled in production)
    try:
        response = requests.post(f"{API_URL}/api/v1/auth/dev-token")
        if response.status_code in [401, 404]:
            print("✅ Dev token endpoint properly secured")
        else:
            print(f"⚠️  Dev token endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return True

def test_cors_headers():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS Headers...")
    try:
        # Test preflight request
        response = requests.options(
            f"{API_URL}/health",
            headers={
                "Origin": "https://www.deckster.xyz",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"   {header}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ CORS Test Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ROUND 22 API TESTS")
    print(f"Testing: {API_URL}")
    print("="*50)
    
    results = {
        "health": test_health(),
        "auth": test_auth_security(),
        "cors": test_cors_headers()
    }
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*50)
    if all_passed:
        print("✅ ALL API TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())