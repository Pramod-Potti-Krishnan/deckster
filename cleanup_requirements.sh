#!/bin/bash
# Clean up temporary requirements files

echo "🧹 Cleaning up temporary requirements files..."
echo "============================================"

# List of temporary files to remove
temp_files=(
    "requirements-all.txt"
    "requirements-base.txt"
    "requirements-complete-frozen.txt"
    "requirements-minimal.txt"
    "requirements-phase1.txt"
    "requirements-py313-latest.txt"
    "requirements-py313-safe.txt"
    "requirements-py313.txt"
    "requirements-ultra-minimal.txt"
    "install_all.sh"
    "install_and_freeze.sh"
    "install_fallback.py"
    "install_minimal.sh"
    "install_phase1_windows.sh"
    "install_py313.sh"
    "cleanup_requirements.sh"  # Remove this script itself
)

# Count files
count=0

# Remove each file
for file in "${temp_files[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "✅ Removed: $file"
        ((count++))
    fi
done

echo ""
echo "✅ Cleaned up $count files"
echo ""
echo "Remaining files:"
ls -la requirements*.txt install*.* 2>/dev/null || echo "No temporary files remaining"

echo ""
echo "✅ Main requirements.txt is now the frozen version with all packages"
echo "   Total packages: $(wc -l < requirements.txt)"
echo ""
echo "Key packages installed:"
echo "  - FastAPI: $(grep "^fastapi==" requirements.txt)"
echo "  - Pydantic: $(grep "^pydantic==" requirements.txt)"
echo "  - LangChain: $(grep "^langchain==" requirements.txt)"
echo "  - Redis: $(grep "^redis==" requirements.txt)"
echo "  - Supabase: $(grep "^supabase==" requirements.txt)"