#!/usr/bin/env python
"""
Analyze dependency tree to understand which packages are direct vs indirect dependencies.
This helps identify why we have 135 packages when we only import 12.
"""

import subprocess
import json
from collections import defaultdict

def get_dependency_tree():
    """Get the full dependency tree using pip."""
    print("Analyzing dependency tree...\n")
    
    # Get list of all installed packages with their dependencies
    try:
        # Use pipdeptree if available, otherwise fall back to pip show
        result = subprocess.run(['pipdeptree', '--json'], capture_output=True, text=True)
        if result.returncode == 0:
            return analyze_pipdeptree(result.stdout)
        else:
            print("pipdeptree not found, using pip show method...")
            return analyze_pip_show()
    except:
        return analyze_pip_show()

def analyze_pipdeptree(json_output):
    """Analyze pipdeptree JSON output."""
    tree = json.loads(json_output)
    
    direct_deps = set()
    all_deps = set()
    dep_reasons = defaultdict(set)  # package -> set of packages that require it
    
    for package in tree:
        pkg_name = package['package']['package_name'].lower()
        direct_deps.add(pkg_name)
        all_deps.add(pkg_name)
        
        # Process dependencies
        for dep in package.get('dependencies', []):
            dep_name = dep['package_name'].lower()
            all_deps.add(dep_name)
            dep_reasons[dep_name].add(pkg_name)
    
    return direct_deps, all_deps, dep_reasons

def analyze_pip_show():
    """Fallback method using pip show."""
    # First get all packages
    result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running pip freeze")
        return set(), set(), {}
    
    all_packages = set()
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            pkg_name = line.split('==')[0].lower()
            all_packages.add(pkg_name)
    
    dep_reasons = defaultdict(set)
    
    # For each package, get what it requires
    for pkg in all_packages:
        result = subprocess.run(['pip', 'show', pkg], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Requires:'):
                    requires = line.replace('Requires:', '').strip()
                    if requires:
                        for req in requires.split(','):
                            req = req.strip().lower()
                            if req:
                                dep_reasons[req].add(pkg)
    
    # Direct deps are those in requirements.txt
    direct_deps = set()
    try:
        with open('requirements.txt') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    pkg = line.split('[')[0].split('==')[0].split('>=')[0].split('<=')[0].strip().lower()
                    direct_deps.add(pkg)
    except:
        pass
    
    return direct_deps, all_packages, dep_reasons

def main():
    # Get our direct imports from the previous analysis
    direct_imports = {
        'fastapi', 'python-jose', 'python-magic', 'numpy', 'passlib', 
        'pydantic', 'pydantic-ai', 'pydantic-settings', 'redis', 
        'slowapi', 'starlette', 'supabase'
    }
    
    # Get dependency tree
    direct_deps, all_deps, dep_reasons = get_dependency_tree()
    
    print(f"=== DEPENDENCY ANALYSIS ===\n")
    print(f"Total packages installed: {len(all_deps)}")
    print(f"Direct dependencies in requirements.txt: {len(direct_deps)}")
    print(f"Packages we directly import: {len(direct_imports)}")
    
    # Find indirect dependencies
    indirect_deps = all_deps - direct_deps
    print(f"Indirect dependencies (installed by other packages): {len(indirect_deps)}")
    
    print("\n=== PACKAGES WE IMPORT AND THEIR DEPENDENCIES ===\n")
    
    # For each package we import, show what it brings in
    for pkg in sorted(direct_imports):
        print(f"\n{pkg}:")
        # Find all packages that list this as a dependency
        brought_by_this = set()
        
        # Check what this package requires
        result = subprocess.run(['pip', 'show', pkg], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Requires:'):
                    requires = line.replace('Requires:', '').strip()
                    if requires:
                        deps = [r.strip() for r in requires.split(',')]
                        print(f"  Directly requires: {', '.join(deps[:5])}")
                        if len(deps) > 5:
                            print(f"                    ... and {len(deps)-5} more")
                        brought_by_this.update(deps)
    
    print("\n=== WHY EACH 'UNUSED' PACKAGE IS INSTALLED ===\n")
    
    # For some key "unused" packages, show why they're needed
    check_packages = [
        'aiofiles', 'anthropic', 'openai', 'httpx', 'cryptography', 
        'bcrypt', 'cffi', 'anyio', 'certifi', 'urllib3'
    ]
    
    for pkg in check_packages:
        if pkg in dep_reasons:
            required_by = sorted(list(dep_reasons[pkg]))[:3]
            print(f"{pkg}:")
            print(f"  Required by: {', '.join(required_by)}")
            if len(dep_reasons[pkg]) > 3:
                print(f"               ... and {len(dep_reasons[pkg])-3} more")
    
    print("\n=== RECOMMENDATIONS ===\n")
    
    # Find packages in requirements.txt that aren't imported or required
    truly_unused = []
    for pkg in direct_deps:
        if pkg not in direct_imports and pkg not in indirect_deps:
            # Check if anything depends on it
            has_dependents = False
            for dep_list in dep_reasons.values():
                if pkg in dep_list:
                    has_dependents = True
                    break
            if not has_dependents:
                truly_unused.append(pkg)
    
    if truly_unused:
        print(f"Packages that might be truly unused ({len(truly_unused)}):")
        for pkg in sorted(truly_unused)[:10]:
            print(f"  - {pkg}")
        if len(truly_unused) > 10:
            print(f"  ... and {len(truly_unused)-10} more")
    else:
        print("✓ All packages appear to be used either directly or as dependencies!")
    
    print("\n=== MISSING DIRECT IMPORTS ===\n")
    print("Packages in requirements.txt that should probably be imported:")
    should_import = ['anthropic', 'openai', 'httpx', 'aiofiles', 'websockets']
    for pkg in should_import:
        if pkg in direct_deps and pkg not in direct_imports:
            print(f"  - {pkg} (in requirements but not imported in code)")

if __name__ == "__main__":
    main()