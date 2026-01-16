#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path

# Test basic functionality
print("Testing basic hash functionality...")

# Test file hashing
test_file = Path("simple_test.py")
if test_file.exists():
    hash_obj = hashlib.sha256()
    with open(test_file, "rb") as f:
        hash_obj.update(f.read())
    file_hash = hash_obj.hexdigest()
    print(f"✓ File hash calculated: {file_hash[:16]}...")
else:
    print("✗ Test file not found")

# Test JSON operations
cache_data = {"test": "value", "hash": file_hash}
with open(".test_cache.json", "w") as f:
    json.dump(cache_data, f)
print("✓ JSON cache file created")

# Read it back
with open(".test_cache.json", "r") as f:
    loaded_data = json.load(f)
print(f"✓ JSON cache file read: {loaded_data['test']}")

# Clean up
Path(".test_cache.json").unlink()
print("✓ Test completed successfully!")
