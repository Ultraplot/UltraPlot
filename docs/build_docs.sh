# 1. Convert all .py scripts to .ipynb (ignoring hidden dirs like _build)
# This creates matching .ipynb files for your gallery scripts
jupytext --to notebook *.py

# 2. Add these notebooks to the cache database
jcache notebook add *.ipynb

# 3. Execute only what has changed
jcache notebook execute

# 4. Run Sphinx, pointing to the current directory as source
# Use -d to keep doctrees separate from your HTML output
# Enable parallel builds for faster execution
sphinx-build -b html -j auto . _build/html -d _build/doctrees
