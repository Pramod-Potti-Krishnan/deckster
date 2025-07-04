#!/usr/bin/env python
"""
Test script to identify missing imports and find correct package versions.
Run this in your virtual environment to test different magic packages.
"""

import sys
import subprocess

def test_import(module_name, package_info):
    """Test if a module can be imported."""
    try:
        if module_name == "magic":
            import magic
            print(f"✓ {module_name} imported successfully")
            print(f"  Magic version info: {magic}")
            # Test basic functionality
            try:
                mime = magic.Magic(mime=True)
                test_data = b"Hello World"
                result = mime.from_buffer(test_data)
                print(f"  MIME detection test: {result}")
            except Exception as e:
                print(f"  Warning: Magic functionality test failed: {e}")
        elif module_name == "PIL":
            from PIL import Image
            print(f"✓ PIL imported successfully")
            print(f"  PIL version: {Image.__version__ if hasattr(Image, '__version__') else 'Unknown'}")
        else:
            exec(f"import {module_name}")
            print(f"✓ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ {module_name} import failed: {e}")
        print(f"  Try installing: {package_info}")
        return False

def main():
    """Test all required imports."""
    print("Testing missing imports for Railway deployment...\n")
    
    # Test core imports that should work
    print("1. Testing core imports (should already work):")
    test_import("fastapi", "Already in requirements")
    test_import("pydantic", "Already in requirements")
    print()
    
    # Test missing imports
    print("2. Testing potentially missing imports:")
    magic_ok = test_import("magic", "pip install python-magic python-magic-bin")
    pil_ok = test_import("PIL", "pip install Pillow")
    print()
    
    # Installation suggestions
    if not magic_ok or not pil_ok:
        print("3. Installation commands to try:")
        print("\nFor magic (try these in order):")
        print("  a) pip install python-magic")
        print("  b) pip install python-magic-bin  # Includes Windows support")
        print("  c) pip install python-magic==0.4.27 python-magic-bin==0.4.14")
        print("\nFor PIL:")
        print("  pip install Pillow")
        print("\nOn Linux/Railway, you may also need:")
        print("  apt-get install libmagic1")
    else:
        print("3. All imports successful! Get the versions:")
        print("\nRun this to see installed versions:")
        print("  pip freeze | grep -E 'magic|Pillow'")
    
    print("\n4. After installing, run this script again to verify.")
    
    # Check current pip freeze for reference
    print("\n5. Current related packages:")
    try:
        result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            relevant = [line for line in lines if any(pkg in line.lower() for pkg in ['magic', 'pillow', 'pil'])]
            if relevant:
                print("Found:")
                for line in relevant:
                    print(f"  {line}")
            else:
                print("  No magic or Pillow packages currently installed")
    except Exception as e:
        print(f"  Could not check pip freeze: {e}")

if __name__ == "__main__":
    main()