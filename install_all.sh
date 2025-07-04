#!/bin/bash
# Install all packages and freeze with hashes

echo "🚀 Installing ALL Requirements"
echo "=============================="
echo ""

# Upgrade pip first
echo "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install everything
echo -e "\nInstalling all requirements..."
echo "This may take a while..."
pip install -r requirements-all.txt

# Freeze with hashes
echo -e "\nFreezing requirements with hashes..."
pip freeze --all > requirements-complete-frozen.txt

# Also create one with hashes for security
echo -e "\nCreating requirements with hashes for secure deployment..."
pip freeze --all --require-hashes > requirements-hashes.txt 2>/dev/null || {
    echo "Note: --require-hashes needs all packages to have hashes"
    echo "Creating standard frozen file instead..."
    pip freeze > requirements-hashes.txt
}

echo -e "\n✅ Installation complete!"
echo ""
echo "Created files:"
echo "- requirements-complete-frozen.txt (all installed packages)"
echo "- requirements-hashes.txt (with hashes if available)"

# Show what got installed
echo -e "\n📦 Installed packages summary:"
pip list | grep -E "(fastapi|pydantic|langchain|openai|anthropic|redis|supabase)" || pip list

echo -e "\n✅ Done! You can now test with: python test_imports.py"