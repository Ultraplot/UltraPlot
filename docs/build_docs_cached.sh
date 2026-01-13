#!/bin/bash
# Cached documentation build script for UltraPlot
# This script checks if a rebuild is needed and only rebuilds what has changed

set -e  # Exit on error

# Check if cache manager is available
if [ ! -f "cache_docs.py" ]; then
    echo "Error: cache_docs.py not found. Please run this script from the docs directory."
    exit 1
fi

# Check if rebuild is needed
if python cache_docs.py check; then
    echo "No rebuild needed. Documentation is up to date."
    exit 0
fi

# If we get here, a rebuild is needed
echo "Rebuilding documentation..."

# 1. Convert all .py scripts to .ipynb (ignoring hidden dirs like _build)
echo "Converting Python scripts to notebooks..."
jupytext --to notebook *.py

# 2. Add these notebooks to the cache database
echo "Adding notebooks to cache..."
jcache notebook add *.ipynb

# 3. Execute only what has changed
echo "Executing changed notebooks..."
jcache notebook execute

# 4. Run Sphinx with parallel builds
echo "Building Sphinx documentation..."
sphinx-build -b html -j auto . _build/html -d _build/doctrees

# 5. Cache the results
echo "Caching build results..."
python cache_docs.py cache_doctrees _build/doctrees

echo "Documentation build complete."
