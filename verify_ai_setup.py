#!/usr/bin/env python3
"""
Quick verification script for AI setup
Run this to check if pydantic_ai and langgraph are properly installed
"""

import sys
import os

def check_imports():
    """Check if required packages can be imported"""
    print("🔍 Checking Core Package Imports...\n")
    
    results = []
    
    # Check Pydantic (CRITICAL)
    try:
        import pydantic
        from pydantic import BaseModel, Field, field_validator
        print(f"✅ pydantic: INSTALLED (v{pydantic.VERSION})")
        print("   ✓ Core components importable")
        
        # Test creating a model
        class TestModel(BaseModel):
            test: str = Field(default="test")
            
        TestModel()
        print("   ✓ Model creation working")
        results.append(("pydantic", True))
    except Exception as e:
        print(f"❌ pydantic: ERROR - {e}")
        print("   This is CRITICAL - the application cannot function!")
        results.append(("pydantic", False))
    
    print()
    
    # Check pydantic_ai
    try:
        import pydantic_ai
        print("✅ pydantic_ai: INSTALLED")
        try:
            from pydantic_ai import Agent, RunContext, FallbackModel
            print("   ✓ Core components importable")
            results.append(("pydantic_ai", True))
        except Exception as e:
            print(f"   ✗ Error importing components: {e}")
            results.append(("pydantic_ai", False))
    except ImportError:
        print("❌ pydantic_ai: NOT INSTALLED")
        print("   Run: pip install pydantic-ai==0.3.5")
        results.append(("pydantic_ai", False))
    
    print()
    
    # Check langgraph
    try:
        import langgraph
        print("✅ langgraph: INSTALLED")
        try:
            from langgraph import StateGraph, END
            from langgraph.graph import Graph
            print("   ✓ Core components importable")
            results.append(("langgraph", True))
        except Exception as e:
            print(f"   ✗ Error importing components: {e}")
            results.append(("langgraph", False))
    except ImportError:
        print("❌ langgraph: NOT INSTALLED")
        print("   Run: pip install langgraph==0.5.1")
        results.append(("langgraph", False))
    
    print()
    
    # Check Logfire (OPTIONAL)
    try:
        import logfire
        print("✅ logfire: INSTALLED")
        print("   ✓ Enhanced observability available")
        results.append(("logfire", True))
    except ImportError:
        print("ℹ️  logfire: NOT INSTALLED (optional)")
        print("   Run: pip install logfire==3.22.0 for enhanced logging")
        results.append(("logfire", True))  # Mark as true since it's optional
    
    print()
    
    # Check environment variables
    print("🔍 Checking Environment Configuration...\n")
    
    env_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "APP_ENV": os.getenv("APP_ENV", "development")
    }
    
    for var, value in env_vars.items():
        if value:
            if "API_KEY" in var:
                # Mask API keys
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print("\n" + "="*50)
    
    # Summary
    all_packages_ok = all(result[1] for result in results)
    has_llm_key = env_vars["OPENAI_API_KEY"] or env_vars["ANTHROPIC_API_KEY"]
    
    if all_packages_ok and has_llm_key:
        print("✅ AI SETUP COMPLETE - Ready for production!")
    elif all_packages_ok:
        print("⚠️  PACKAGES OK but NO LLM API KEYS configured")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
    else:
        print("❌ AI SETUP INCOMPLETE - Install missing packages")
    
    print("="*50)
    
    return 0 if all_packages_ok else 1


if __name__ == "__main__":
    sys.exit(check_imports())