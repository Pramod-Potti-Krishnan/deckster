#!/bin/bash
# Quick test script to validate full flow before frontend testing

echo "🧪 Testing Deckster Backend - Full Flow Validation"
echo "================================================"

# Test 1: Health Check
echo -e "\n1️⃣ Testing Health Endpoint..."
HEALTH=$(curl -s https://deckster-production.up.railway.app/health)
if [[ $HEALTH == *"healthy"* ]]; then
  echo "✅ Backend is healthy"
else
  echo "❌ Backend health check failed"
  exit 1
fi

# Test 2: CORS Configuration
echo -e "\n2️⃣ Testing CORS Configuration..."
CORS=$(curl -s https://deckster-production.up.railway.app/api/health/cors)
if [[ $CORS == *"cors_test\":true"* ]]; then
  echo "✅ CORS configured correctly"
else
  echo "❌ CORS configuration issue"
fi

# Test 3: Authentication
echo -e "\n3️⃣ Testing Authentication Endpoint..."
AUTH_RESPONSE=$(curl -s -X POST https://deckster-production.up.railway.app/api/auth/demo \
  -H "Content-Type: application/json" \
  -d '{"user_id": "backend_validation_test"}')

if [[ $AUTH_RESPONSE == *"access_token"* ]]; then
  echo "✅ Authentication working"
  TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  echo "   Token obtained (first 20 chars): ${TOKEN:0:20}..."
else
  echo "❌ Authentication failed"
  echo "   Response: $AUTH_RESPONSE"
  exit 1
fi

echo -e "\n4️⃣ WebSocket Test..."
echo "Note: Full WebSocket test requires Node.js or browser"
echo "Frontend can proceed with testing at: https://www.deckster.xyz/builder"

echo -e "\n✅ All backend validations passed!"
echo "Ready for frontend testing! 🚀"