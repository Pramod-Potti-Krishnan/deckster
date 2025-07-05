#!/usr/bin/env python3
"""
Test WebSocket connection directly.
Usage: python test_websocket_chat.py [--prod]

By default connects to local development server.
Use --prod flag to connect to production.
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime
from uuid import uuid4
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test WebSocket connection')
parser.add_argument('--prod', action='store_true', help='Connect to production server')
parser.add_argument('--url', type=str, help='Custom WebSocket URL')
args = parser.parse_args()

# Configuration
if args.url:
    WS_URL = args.url
elif args.prod:
    WS_URL = "wss://deckster-production.up.railway.app/ws"
else:
    WS_URL = "ws://localhost:8000/ws"

# You'll need to get a valid token - for testing you might need to add this
AUTH_TOKEN = None  # Set this if authentication is required

async def test_websocket():
    """Test WebSocket connection and messaging."""
    print(f"🔌 WebSocket Test Client")
    print(f"📍 Connecting to: {WS_URL}")
    print("=" * 50)
    
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    try:
        async with websockets.connect(WS_URL, extra_headers=headers) as websocket:
            print("✅ Connected to WebSocket")
            
            # Task to receive messages
            async def receive_messages():
                try:
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)
                        print(f"\n📥 Received ({data.get('type', 'unknown')}):")
                        print(json.dumps(data, indent=2))
                        print("-" * 50)
                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ Connection closed")
                except Exception as e:
                    print(f"\n❌ Receive error: {e}")
            
            # Start receiving task
            receive_task = asyncio.create_task(receive_messages())
            
            # Wait a bit for initial messages
            await asyncio.sleep(1)
            
            # Test sequence
            test_messages = [
                {
                    "text": "hi",
                    "description": "Testing greeting"
                },
                {
                    "text": "Can you help me create a presentation?",
                    "description": "Testing general request"
                },
                {
                    "text": "I need a presentation about AI",
                    "description": "Testing specific request"
                }
            ]
            
            for test in test_messages:
                print(f"\n📤 Sending: {test['description']}")
                print(f"   Text: \"{test['text']}\"")
                
                message = {
                    "type": "user_input",
                    "data": {"text": test["text"]},
                    "id": f"msg_{uuid4().hex[:8]}",  # Using 'id' not 'message_id'
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": "test_session"  # This might be set by server
                }
                
                await websocket.send(json.dumps(message))
                print("   ✅ Sent")
                
                # Wait for responses
                await asyncio.sleep(3)
                
                # Ask user if they want to continue
                try:
                    continue_test = input("\nPress Enter to continue or 'q' to quit: ")
                    if continue_test.lower() == 'q':
                        break
                except EOFError:
                    break
            
            # Cancel receive task
            receive_task.cancel()
            
    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket Error: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def test_simple():
    """Simple test that just sends one message."""
    print("\n🧪 Simple WebSocket Test")
    print("=" * 30)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected")
            
            # Send hi
            message = {
                "type": "user_input",
                "data": {"text": "hi"},
                "id": f"msg_{uuid4().hex[:8]}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n📤 Sending: {json.dumps(message, indent=2)}")
            await websocket.send(json.dumps(message))
            
            # Wait for responses
            print("\n⏳ Waiting for responses (5 seconds)...")
            
            try:
                for i in range(5):
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    print(f"\n📥 Response {i+1}:")
                    print(json.dumps(data, indent=2))
            except asyncio.TimeoutError:
                print("\n⏰ No more messages")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print(f"WebSocket Test Tool")
    print(f"Target: {WS_URL}")
    print("-" * 50)
    
    if not AUTH_TOKEN and "production" in WS_URL:
        print("⚠️  WARNING: No auth token set for production server")
        print("   You may need to set AUTH_TOKEN in the script")
    
    choice = input("\nChoose test mode:\n1. Interactive test\n2. Simple test\n> ")
    
    if choice == "2":
        asyncio.run(test_simple())
    else:
        asyncio.run(test_websocket())