#!/bin/bash
# Simple authentication flow test script

echo "=================================="
echo "Authentication Flow Test Script"
echo "=================================="

# Set the base URL (default to production)
BASE_URL="${TEST_BASE_URL:-https://deckster-production.up.railway.app}"
echo "Testing against: $BASE_URL"
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
echo "------------------------------"
curl -s "$BASE_URL/health" | python3 -m json.tool || echo "Failed to parse JSON"
echo ""

# Test 2: Demo token endpoint
echo "2. Testing /api/auth/demo endpoint..."
echo "------------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/demo" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user_demo"}')

echo "$RESPONSE" | python3 -m json.tool || echo "Failed to parse JSON"

# Extract token if successful
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo ""
    echo "✅ Successfully obtained token!"
    echo "Token (first 20 chars): ${TOKEN:0:20}..."
else
    echo ""
    echo "❌ Failed to obtain token"
fi

# Test 3: Dev token endpoint (might fail in production)
echo ""
echo "3. Testing /api/dev/token endpoint..."
echo "------------------------------"
curl -s -X POST "$BASE_URL/api/dev/token" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user_dev"}' | python3 -m json.tool || echo "Failed - this is expected in production"

echo ""
echo "=================================="
echo "Test completed!"
echo "=================================="

# Instructions for WebSocket testing
if [ -n "$TOKEN" ]; then
    echo ""
    echo "To test WebSocket connection, run this in your browser console:"
    echo ""
    echo "const ws = new WebSocket('${BASE_URL/https/wss}/ws?token=$TOKEN');"
    echo "ws.onopen = () => console.log('Connected!');"
    echo "ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));"
    echo "ws.onerror = (e) => console.error('Error:', e);"
fi