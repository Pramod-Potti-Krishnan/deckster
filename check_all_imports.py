#!/usr/bin/env python
"""
Check all Python files for imports and verify they're in requirements.txt
"""

import os
import re
from pathlib import Path

# Read requirements.txt
requirements_path = Path("requirements.txt")
requirements = set()

if requirements_path.exists():
    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith("#"):
                # Extract package name (before ==, >=, etc.)
                package = re.split(r'[<>=\[]', line)[0].strip()
                requirements.add(package.lower())

print(f"Found {len(requirements)} packages in requirements.txt\n")

# Standard library modules (don't need to be in requirements.txt)
stdlib_modules = {
    'os', 'sys', 'json', 're', 'datetime', 'time', 'pathlib', 'typing',
    'asyncio', 'functools', 'itertools', 'collections', 'contextlib',
    'logging', 'uuid', 'hashlib', 'base64', 'secrets', 'random',
    'traceback', 'warnings', 'enum', 'dataclasses', 'abc', 'io',
    'importlib', 'inspect', 'types', 'copy', 'weakref', 'gc',
    'threading', 'multiprocessing', 'subprocess', 'signal', 'socket',
    'urllib', 'http', 'email', 'csv', 'xml', 'html', 'math',
    'statistics', 'decimal', 'fractions', 'numbers', 'string',
    'textwrap', 'unicodedata', 'codecs', 'locale', 'gettext',
    'tempfile', 'glob', 'fnmatch', 'shutil', 'zipfile', 'tarfile',
    'gzip', 'bz2', 'lzma', 'sqlite3', 'pickle', 'shelve', 'dbm',
    'queue', 'heapq', 'bisect', 'array', 'struct', 'operator',
    'pprint', 'reprlib', 'contextvars', '__future__'
}

# Package name mappings (import name -> package name)
package_mappings = {
    'PIL': 'pillow',
    'jose': 'python-jose',
    'dotenv': 'python-dotenv',
    'slowapi': 'slowapi',
    'magic': 'python-magic',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'yaml': 'pyyaml',
    'bs4': 'beautifulsoup4',
    'dateutil': 'python-dateutil',
    'multipart': 'python-multipart',
    'cryptography': 'cryptography',
    'jwt': 'pyjwt',
    'openai': 'openai',
    'anthropic': 'anthropic',
    'redis': 'redis',
    'supabase': 'supabase',
    'passlib': 'passlib',
    'pydantic': 'pydantic',
    'pydantic_ai': 'pydantic-ai',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'starlette': 'starlette',
    'httpx': 'httpx',
    'logfire': 'logfire',
    'pgvector': 'pgvector',
    'asyncpg': 'asyncpg',
    'websockets': 'websockets',
    'aiofiles': 'aiofiles'
}

# Find all Python files
python_files = []
for root, dirs, files in os.walk("src"):
    # Skip __pycache__ directories
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

print(f"Checking {len(python_files)} Python files...\n")

# Track all imports
all_imports = set()
missing_imports = set()
file_imports = {}

# Regex patterns for imports
import_patterns = [
    re.compile(r'^import\s+(\S+)', re.MULTILINE),
    re.compile(r'^from\s+(\S+)\s+import', re.MULTILINE)
]

for file_path in python_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    file_imports[file_path] = set()
    
    for pattern in import_patterns:
        matches = pattern.findall(content)
        for match in matches:
            # Get the base module name
            module = match.split('.')[0]
            
            # Skip relative imports and standard library
            if module and not module.startswith('.') and module not in stdlib_modules:
                all_imports.add(module)
                file_imports[file_path].add(module)
                
                # Check if it's in requirements
                package_name = package_mappings.get(module, module).lower()
                if package_name not in requirements:
                    # Also check if it's a sub-module of something in requirements
                    found = False
                    for req in requirements:
                        if module.startswith(req.replace('-', '_')):
                            found = True
                            break
                    if not found:
                        missing_imports.add((module, file_path))

# Report results
print("=== MISSING IMPORTS ===")
if missing_imports:
    print(f"\nFound {len(missing_imports)} imports not in requirements.txt:\n")
    
    # Group by module
    by_module = {}
    for module, file_path in sorted(missing_imports):
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(file_path)
    
    for module, files in sorted(by_module.items()):
        print(f"\n'{module}' used in:")
        for file_path in files[:3]:  # Show first 3 files
            print(f"  - {file_path}")
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more files")
else:
    print("\n✓ All imports are in requirements.txt!")

print("\n=== ALL UNIQUE IMPORTS ===")
print(f"\nTotal unique third-party imports: {len(all_imports)}")
print("\nAll imports found:")
for imp in sorted(all_imports):
    package_name = package_mappings.get(imp, imp).lower()
    status = "✓" if package_name in requirements or any(imp.startswith(req.replace('-', '_')) for req in requirements) else "✗"
    print(f"  {status} {imp} -> {package_name}")

print("\n=== UNUSED PACKAGES? ===")
print("\nPackages in requirements.txt but not directly imported:")
used_packages = set()
for imp in all_imports:
    package_name = package_mappings.get(imp, imp).lower()
    used_packages.add(package_name)
    # Also add parent packages
    if '_' in imp:
        used_packages.add(imp.split('_')[0])

unused = []
for req in sorted(requirements):
    # Skip sub-dependencies and tools
    if req not in used_packages and not any(req.startswith(used) for used in used_packages):
        # Also check underscore version
        if req.replace('-', '_') not in used_packages:
            unused.append(req)

if unused:
    print(f"\nPossibly unused ({len(unused)}):")
    for pkg in unused[:20]:  # Show first 20
        print(f"  - {pkg}")
    if len(unused) > 20:
        print(f"  ... and {len(unused) - 20} more")
else:
    print("\n✓ All packages appear to be used!")