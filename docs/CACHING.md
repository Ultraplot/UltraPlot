# Documentation Caching System

This document describes the caching system for UltraPlot documentation builds.

## Overview

The caching system is designed to significantly reduce documentation build times by:

1. **Detecting changes**: Only rebuild documentation when source files have actually changed
2. **Caching notebook execution**: Avoid re-executing notebooks that haven't changed
3. **Caching Sphinx doctrees**: Reuse parsed documentation structure when possible

## Components

### 1. Cache Manager (`cache_docs.py`)

The main caching utility that provides:

- **Change detection**: Hash-based comparison of source files
- **Notebook caching**: Track notebook execution results
- **Doctree caching**: Cache Sphinx's parsed documentation structure
- **Cache invalidation**: Automatic detection of when rebuilds are needed

### 2. Cached Build Script (`build_docs_cached.sh`)

A drop-in replacement for the standard build script that:

1. Checks if a rebuild is needed
2. Only executes changed notebooks
3. Builds Sphinx documentation with parallel processing
4. Caches the results for future builds

### 3. Cache Files

All cache data is stored in the `.doc_cache` directory:

- `notebook_cache.json`: Hashes and timestamps of executed notebooks
- `doctree_cache.json`: Hashes of Sphinx doctree files
- `file_hashes.json`: Hashes of source files for change detection

## Usage

### Basic Usage

```bash
# Check if rebuild is needed
python cache_docs.py check

# Build documentation (only if needed)
./build_docs_cached.sh

# Clear all cached data
python cache_docs.py clear

# Show cache information
python cache_docs.py info
```

### Manual Cache Management

```bash
# Cache doctrees manually
python cache_docs.py cache_doctrees _build/doctrees

# Check if a specific notebook needs rebuilding
python cache_docs.py check --source-dir path/to/notebooks
```

## How It Works

### Change Detection

1. **File hashing**: Each source file is hashed using SHA-256
2. **Directory hashing**: All relevant files in a directory are combined into a single hash
3. **Comparison**: Current hashes are compared against cached hashes

### Build Process

1. **Check for changes**: Compare current source file hashes with cached versions
2. **Selective execution**: Only execute notebooks that have changed
3. **Parallel building**: Use Sphinx's parallel build capability
4. **Cache results**: Store hashes of successful builds

### Cache Invalidation

The cache is automatically invalidated when:

- Source files (.py, .rst, .md, .ipynb) are modified
- Notebook execution results change
- Sphinx configuration changes
- Manual cache clearing

## Performance Benefits

### Before Caching

- Full rebuild on every run
- All notebooks executed every time
- Sphinx parses all source files every time
- Build times: 5-15 minutes (depending on system)

### After Caching

- Only changed files are processed
- Only changed notebooks are executed
- Sphinx reuses cached doctrees
- Build times: 30 seconds - 2 minutes (when no changes)

## Integration with CI/CD

The caching system is designed to work with GitHub Actions and ReadTheDocs:

### GitHub Actions

Add caching steps to your workflow:

```yaml
- name: Cache documentation
  uses: actions/cache@v4
  with:
    path: docs/.doc_cache
    key: docs-cache-${{ hashFiles('docs/**') }}
    restore-keys: docs-cache-
```

### ReadTheDocs

The system automatically works with ReadTheDocs by:

1. Using the existing `jcache` notebook caching
2. Adding Sphinx doctree caching
3. Providing fast incremental builds

## Troubleshooting

### Cache not working

1. **Clear cache**: `python cache_docs.py clear`
2. **Check permissions**: Ensure `.doc_cache` directory is writable
3. **Verify hashes**: Run `python cache_docs.py info` to see cached data

### False positives (rebuilding when not needed)

1. **Check file timestamps**: Some systems may have timestamp issues
2. **Verify hash stability**: Ensure hash calculation is consistent
3. **Debug with info**: Use `python cache_docs.py info` to diagnose

### False negatives (not rebuilding when needed)

1. **Clear cache manually**: Force a full rebuild
2. **Check file patterns**: Ensure all relevant files are being hashed
3. **Verify cache files**: Check that cache files are being updated

## Advanced Configuration

### Custom Cache Directory

```python
cache_manager = DocCacheManager(cache_dir=".my_custom_cache")
```

### Custom File Patterns

Modify the `_get_directory_hash` method to include additional file types:

```python
def _get_directory_hash(self, directory: Path, patterns: List[str] = None) -> str:
    if patterns is None:
        patterns = ["*.py", "*.rst", "*.md", "*.ipynb", "*.txt", "*.json"]
    # ... rest of method
```

## Future Enhancements

Potential improvements to the caching system:

1. **Distributed caching**: Share cache between CI runners
2. **Partial doctree caching**: Cache individual pages rather than entire doctree
3. **Dependency tracking**: Track dependencies between documentation pages
4. **Incremental notebook execution**: Execute only changed cells in notebooks
5. **Cache compression**: Reduce cache size for large documentation sets

## Contributing

Contributions to improve the caching system are welcome! Please:

1. Open an issue to discuss proposed changes
2. Ensure changes maintain backward compatibility
3. Add tests for new functionality
4. Update this documentation as needed