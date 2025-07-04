#!/usr/bin/env python3
"""Test script to verify authentication flow after Round 10 fixes."""

import asyncio
import aiohttp
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Base URLs - change these for different environments
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
WS_URL = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")

async def test_endpoint(session, endpoint, method="GET", json_data=None):
    """Test an endpoint and return the result."""
    print(f"\n{'='*50}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*50}")
    
    try:
        async with session.request(method, f"{BASE_URL}{endpoint}", json=json_data) as response:
            print(f"Status: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return True, data
            else:
                text = await response.text()
                print(f"Error Response: {text}")
                return False, None
                
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        return False, None

async def test_websocket(token):
    """Test WebSocket connection with token."""
    print(f"\n{'='*50}")
    print(f"Testing WebSocket Connection")
    print(f"{'='*50}")
    
    ws_endpoint = f"{WS_URL}/ws?token={token}"
    print(f"Connecting to: {ws_endpoint}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_endpoint) as ws:
                print("✅ WebSocket connected successfully!")
                
                # Wait for connection message
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    print(f"Received connection message: {json.dumps(data, indent=2)}")
                    
                    # Send a test message
                    test_message = {
                        "message_id": f"test_{int(asyncio.get_event_loop().time())}",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "session_id": data.get("session_id"),
                        "type": "user_input",
                        "data": {
                            "text": "Test message from auth flow test",
                            "response_to": None,
                            "attachments": [],
                            "ui_references": [],
                            "frontend_actions": []
                        }
                    }
                    
                    await ws.send_json(test_message)
                    print(f"Sent test message: {test_message['message_id']}")
                    
                    # Wait for response
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            print(f"Received response: {json.dumps(data, indent=2)}")
                    except asyncio.TimeoutError:
                        print("No response received within 5 seconds (this might be normal)")
                    
                await ws.close()
                return True
                
    except Exception as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")
        return False

async def main():
    """Run authentication flow tests."""
    print(f"Testing authentication flow against: {BASE_URL}")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        success, _ = await test_endpoint(session, "/health")
        if not success:
            print("\n❌ Health check failed - is the server running?")
            return
        
        # Test 2: CORS health check
        await test_endpoint(session, "/api/health/cors")
        
        # Test 3: Dev token endpoint (might fail in production)
        success, data = await test_endpoint(
            session, 
            "/api/dev/token", 
            method="POST",
            json_data={"user_id": "test_user_dev"}
        )
        
        if success:
            print("\n✅ Dev token endpoint is available")
            token = data.get("access_token")
            if token:
                await test_websocket(token)
        else:
            print("\n⚠️  Dev token endpoint not available (expected in production)")
        
        # Test 4: Demo token endpoint (should work in all environments)
        success, data = await test_endpoint(
            session,
            "/api/auth/demo",
            method="POST", 
            json_data={"user_id": "test_user_demo"}
        )
        
        if success:
            print("\n✅ Demo token endpoint is working!")
            token = data.get("access_token")
            if token:
                await test_websocket(token)
        else:
            print("\n❌ Demo token endpoint failed - this should work in all environments")
        
        # Test 5: Try accessing a protected endpoint without token
        print(f"\n{'='*50}")
        print("Testing protected endpoint without authentication")
        print(f"{'='*50}")
        
        async with session.get(f"{BASE_URL}/api/v1/user/profile") as response:
            print(f"Status: {response.status} (should be 401)")
            if response.status == 401:
                print("✅ Authentication middleware is working correctly")
            else:
                print("❌ Expected 401 but got different status")
    
    print("\n" + "="*50)
    print("Authentication flow test completed!")
    print("="*50)

if __name__ == "__main__":
    # Test different environments by setting TEST_BASE_URL
    # Examples:
    # export TEST_BASE_URL=http://localhost:8000
    # export TEST_BASE_URL=https://deckster-production.up.railway.app
    
    asyncio.run(main())