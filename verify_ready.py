#!/usr/bin/env python3
"""Final verification before starting the app"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Phase 1 Final Environment Check")
print("=" * 50)

# Check all mandatory variables
checks = {
    "JWT_SECRET_KEY": ("✅", "❌", True),
    "JWT_ALGORITHM": ("✅", "❌", True),
    "JWT_EXPIRY_HOURS": ("✅", "❌", True),
    "SUPABASE_URL": ("✅", "❌", True),
    "SUPABASE_ANON_KEY": ("✅", "❌", True),
    "SUPABASE_SERVICE_KEY": ("✅", "❌", True),
    "REDIS_URL": ("✅", "❌", True),
    "ANTHROPIC_API_KEY": ("✅", "❌", True),
    "OPENAI_API_KEY": ("✅", "⚠️", False),  # Optional but good to have
    "LOGFIRE_TOKEN": ("✅", "⚠️", False),   # Optional
}

all_good = True
mandatory_good = True

for var, (success, fail, required) in checks.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "KEY" in var or "TOKEN" in var:
            display = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display = value[:30] + "..." if len(value) > 30 else value
        print(f"{success} {var}: {display}")
    else:
        print(f"{fail} {var}: NOT SET")
        all_good = False
        if required:
            mandatory_good = False

print("\n" + "=" * 50)

if mandatory_good:
    print("✅ All mandatory environment variables are set!")
    print("\n🚀 You're ready to start the application!")
    print("\nNext steps:")
    print("1. Start the server:")
    print("   python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n2. Check the API:")
    print("   - Health: http://localhost:8000/health")
    print("   - Docs: http://localhost:8000/docs")
    print("   - WebSocket: ws://localhost:8000/ws")
else:
    print("❌ Missing mandatory environment variables!")
    print("Please check your .env file")
    sys.exit(1)