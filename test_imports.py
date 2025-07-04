#!/usr/bin/env python3
"""
Test script to verify all required imports work correctly.
Run this after installing requirements-phase1.txt
"""

import sys
print("Python version:", sys.version)
print("-" * 50)

# Test core imports
imports_to_test = [
    ("FastAPI", "fastapi"),
    ("Uvicorn", "uvicorn"),
    ("WebSockets", "websockets"),
    ("Pydantic", "pydantic"),
    ("Pydantic Settings", "pydantic_settings"),
    ("Pydantic AI", "pydantic_ai"),
    ("LangChain", "langchain"),
    ("LangGraph", "langgraph"),
    ("Supabase", "supabase"),
    ("Redis", "redis"),
    ("AsyncPG", "asyncpg"),
    ("PGVector", "pgvector"),
    ("Python-JOSE", "jose"),
    ("Passlib", "passlib"),
    ("OpenAI", "openai"),
    ("Anthropic", "anthropic"),
    ("NumPy", "numpy"),
    ("Python-dotenv", "dotenv"),
    ("HTTPX", "httpx"),
    ("Aiofiles", "aiofiles"),
    ("Pytest", "pytest"),
]

failed_imports = []
successful_imports = []

for name, module in imports_to_test:
    try:
        __import__(module)
        successful_imports.append((name, module))
        print(f"✅ {name} ({module})")
    except ImportError as e:
        failed_imports.append((name, module, str(e)))
        print(f"❌ {name} ({module}): {e}")

print("-" * 50)
print(f"✅ Successful imports: {len(successful_imports)}")
print(f"❌ Failed imports: {len(failed_imports)}")

if failed_imports:
    print("\nFailed imports details:")
    for name, module, error in failed_imports:
        print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print("\n🎉 All imports successful! Phase 1 dependencies are ready.")
    
# Test optional imports
print("\nOptional imports:")
try:
    import tiktoken
    print("✅ tiktoken (optional)")
except ImportError:
    print("⚠️  tiktoken not available (optional - for token counting)")

try:
    import logfire
    print("✅ logfire (optional)")
except ImportError:
    print("⚠️  logfire not available (optional - for observability)")

print("\nYou can now proceed with running the application!")