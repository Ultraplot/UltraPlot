# Documentation Cache Workflow

This workflow implements caching for UltraPlot documentation builds to significantly reduce build times in CI/CD environments.

## Overview

The `docs-cache.yml` workflow provides:

1. **Automatic cache detection**: Only rebuilds documentation when source files change
2. **GitHub Actions caching**: Uses GitHub's built-in caching for cache files
3. **Selective execution**: Only runs full builds when necessary
4. **Environment compatibility**: Works with micromamba and the UltraPlot development environment

## Workflow Structure

### Jobs

#### 1. `cache-documentation`
The main job that handles documentation caching and building:

- **Triggers**: Runs on pushes/pull requests to `main`/`devel` branches when documentation-related files change
- **Environment**: Uses micromamba with the UltraPlot development environment
- **Steps**:
  1. Checkout code
  2. Set up micromamba environment
  3. Install UltraPlot
  4. Test cache system
  5. Restore cached documentation
  6. Check if rebuild is needed
  7. Build documentation (if needed)
  8. Cache build results
  9. Upload documentation artifacts

#### 2. `verify-cache`
A verification job that ensures the caching system works correctly:

- **Triggers**: Runs after `cache-documentation` completes
- **Purpose**: Verifies cache files are created and accessible
- **Steps**:
  1. Checkout code
  2. Set up micromamba environment
  3. Download cached documentation
  4. Verify cache contents
  5. Test cache manager functionality

## Cache Strategy

### Cache Key

The cache uses a composite key based on:
- **Source files**: Hash of all files in `docs/` directory
- **Environment**: `environment.yml` file content
- **Configuration**: `.readthedocs.yml` file content

```yaml
key: docs-cache-${{ hashFiles('docs/**', 'environment.yml', '.readthedocs.yml') }}
```

### Cached Paths

The workflow caches two main directories:

1. **`.doc_cache/`**: Contains cache metadata and hashes
   - `notebook_cache.json` - Notebook execution cache
   - `doctree_cache.json` - Sphinx doctree cache
   - `file_hashes.json` - Source file hashes

2. **`_build/doctrees/`**: Contains Sphinx parsed documentation structure
   - `.doctree` files - Parsed documentation
   - `.pickle` files - Python objects from documentation

## Performance Benefits

### Before Caching

- **Full rebuild on every run**: 5-15 minutes
- **All notebooks executed every time**: Significant computational resources
- **Sphinx parses all files every time**: CPU-intensive

### After Caching

- **No changes detected**: 30 seconds - 2 minutes (just cache verification)
- **Minor changes**: 1-3 minutes (only changed files processed)
- **Major changes**: 2-5 minutes (full rebuild but with parallel processing)

## Usage

### Manual Trigger

You can manually trigger the workflow:

1. Go to GitHub Actions tab
2. Select "Documentation Cache" workflow
3. Click "Run workflow" button
4. Select branch and run

### Automatic Trigger

The workflow runs automatically when:
- Documentation files (`docs/**`) are modified
- Environment configuration (`environment.yml`) changes
- ReadTheDocs configuration (`.readthedocs.yml`) changes
- Workflow file (`.github/workflows/docs-cache.yml`) changes

## Cache Invalidation

The cache automatically invalidates when:

1. **Source files change**: Any modification to `.py`, `.rst`, `.md`, `.ipynb` files
2. **Environment changes**: Changes to `environment.yml`
3. **Configuration changes**: Changes to `.readthedocs.yml`
4. **Manual clearing**: Using `python cache_docs.py clear`

## Troubleshooting

### Cache Not Working

1. **Check cache hit/miss**: Look at GitHub Actions logs for cache restoration
2. **Verify cache files**: Check if `.doc_cache/` directory exists after build
3. **Debug with info**: Run `python cache_docs.py info` in workflow

### False Positives (Rebuilding when not needed)

1. **Check file timestamps**: Some systems may have timestamp issues
2. **Verify hash stability**: Ensure hash calculation is consistent
3. **Examine cache key**: Check if cache key components are stable

### False Negatives (Not rebuilding when needed)

1. **Clear cache manually**: Force a full rebuild with `python cache_docs.py clear`
2. **Check file patterns**: Ensure all relevant files are being hashed
3. **Verify cache files**: Check that cache files are being updated

## Integration with ReadTheDocs

This caching system is designed to work alongside ReadTheDocs:

1. **Local development**: Use cached builds for fast iteration
2. **CI/CD testing**: Verify documentation builds work before merging
3. **ReadTheDocs production**: Use official builds for published documentation

The workflow doesn't replace ReadTheDocs but provides:
- Faster local development
- Pre-merge verification
- Cache validation

## Environment Requirements

The workflow requires:

- **micromamba**: For environment management
- **Python 3.11**: Specified in workflow (can be adjusted)
- **UltraPlot dependencies**: From `environment.yml`
- **Cache system dependencies**: `json`, `hashlib`, `pathlib`, `tempfile` (all standard library)

## Customization

### Adjust Python Version

Change the Python version in the workflow:

```yaml
create-args: >-
  --verbose
  python=3.11  # Change this to desired version
```

### Add Additional Cache Paths

Add more paths to the cache:

```yaml
with:
  path: |
    docs/.doc_cache
    docs/_build/doctrees
    docs/_build/html  # Add HTML output if needed
```

### Adjust Cache Key

Modify the cache key for different granularity:

```yaml
key: docs-cache-${{ hashFiles('docs/**') }}-${{ hashFiles('environment.yml') }}
```

## Best Practices

1. **Commit cache files**: Consider committing `.doc_cache/` to repository for initial cache seeding
2. **Monitor cache size**: Large caches can slow down workflows
3. **Regular cache clearing**: Periodically clear cache to avoid stale data
4. **Test cache invalidation**: Verify cache invalidates when expected
5. **Use cache in development**: Run `python cache_docs.py check` before building locally

## Future Enhancements

Potential improvements:

1. **Distributed caching**: Share cache between different workflow runs
2. **Partial doctree caching**: Cache individual pages for finer granularity
3. **Dependency tracking**: Track dependencies between documentation pages
4. **Cache compression**: Reduce cache size for large documentation
5. **Cache statistics**: Collect and display cache hit/miss statistics

## Related Files

- `docs/cache_docs.py`: Main cache management utility
- `docs/build_docs_cached.sh`: Cached build script
- `docs/CACHING.md`: Comprehensive caching documentation
- `environment.yml`: Development environment configuration
- `.readthedocs.yml`: ReadTheDocs configuration