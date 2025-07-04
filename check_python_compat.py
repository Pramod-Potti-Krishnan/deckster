#!/usr/bin/env python
"""
Check for Python 3.11 vs 3.13 compatibility issues.
"""

import sys

print(f"Current Python: {sys.version}")
print("\nChecking for potential compatibility issues...\n")

# Check for Python 3.13 specific features
issues = []

# 1. Check for match statements (3.10+)
try:
    exec("""
match 1:
    case 1:
        pass
""")
    print("✓ Match statements supported")
except SyntaxError:
    print("✗ Match statements not supported (needs Python 3.10+)")
    issues.append("match statements")

# 2. Check for ExceptionGroup (3.11+)
try:
    from builtins import ExceptionGroup
    print("✓ ExceptionGroup available")
except ImportError:
    print("✗ ExceptionGroup not available (needs Python 3.11+)")
    issues.append("ExceptionGroup")

# 3. Check for typing features
try:
    from typing import Self, Never
    print("✓ Self and Never types available")
except ImportError:
    print("⚠️  Self/Never types not available (3.11+ feature)")
    # Not critical

# 4. Check installed packages for version conflicts
import subprocess
result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
if result.returncode == 0:
    lines = result.stdout.strip().split('\n')[2:]  # Skip header
    print("\nPackages that might have version issues:")
    for line in lines:
        if any(pkg in line for pkg in ['pydantic', 'fastapi', 'typing-extensions']):
            print(f"  {line}")

if issues:
    print(f"\n⚠️  Found {len(issues)} potential compatibility issues")
else:
    print("\n✓ No major compatibility issues detected")