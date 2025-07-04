#!/usr/bin/env python3
"""
Fallback installation script for Python 3.13
Installs packages one by one with error handling
"""

import subprocess
import sys

def try_install(package, version=None):
    """Try to install a package, return success status."""
    pkg_spec = f"{package}=={version}" if version else package
    print(f"\nInstalling {pkg_spec}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_spec])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} failed to install")
        return False

def main():
    print("🚀 Fallback Installation for Python 3.13")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    
    # Core packages with specific versions
    core_packages = [
        ("pip", None),  # Upgrade pip first
        ("setuptools", None),
        ("wheel", None),
        ("fastapi", "0.115.14"),
        ("uvicorn", "0.32.1"),
        ("websockets", "14.2"),
        ("pydantic", "2.11.7"),
        ("pydantic-settings", "2.7.1"),
        ("supabase", "2.12.0"),
        ("redis", "5.3.0"),
        ("python-jose[cryptography]", "3.3.0"),
        ("passlib[bcrypt]", "1.7.4"),
        ("python-multipart", "0.0.20"),
        ("openai", "1.59.15"),
        ("anthropic", "0.41.1"),
        ("python-dotenv", "1.0.1"),
        ("httpx", "0.28.1"),
        ("aiofiles", "24.1.0"),
        ("pytest", "8.3.4"),
    ]
    
    # Optional packages
    optional_packages = [
        ("pydantic-ai", "0.0.13"),
        ("langchain", "0.3.18"),
        ("numpy", "2.2.2"),
        ("asyncpg", "0.30.0"),
        ("tiktoken", "0.8.0"),
        ("logfire", "2.14.0"),
    ]
    
    # Install core packages
    print("\n📦 Installing core packages...")
    failed_core = []
    for package, version in core_packages:
        if not try_install(package, version):
            failed_core.append(package)
    
    # Install optional packages
    print("\n📦 Installing optional packages...")
    failed_optional = []
    for package, version in optional_packages:
        if not try_install(package, version):
            failed_optional.append(package)
    
    # Summary
    print("\n" + "=" * 40)
    print("Installation Summary:")
    print(f"✅ Core packages installed: {len(core_packages) - len(failed_core)}/{len(core_packages)}")
    print(f"✅ Optional packages installed: {len(optional_packages) - len(failed_optional)}/{len(optional_packages)}")
    
    if failed_core:
        print(f"\n❌ Failed core packages: {', '.join(failed_core)}")
        print("⚠️  Some core functionality may not work!")
    
    if failed_optional:
        print(f"\n⚠️  Failed optional packages: {', '.join(failed_optional)}")
        print("The application will work with reduced functionality.")
    
    # Test imports
    print("\n📋 Testing imports...")
    test_imports = ["fastapi", "pydantic", "uvicorn", "redis", "supabase"]
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
    
    print("\n✅ Installation process complete!")
    
    if failed_core:
        print("\n⚠️  WARNING: Core packages failed. Consider using Python 3.11 or 3.12 instead.")
        print("Download from: https://www.python.org/downloads/")

if __name__ == "__main__":
    main()