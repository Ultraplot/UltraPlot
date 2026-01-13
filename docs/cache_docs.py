#!/usr/bin/env python3
"""
Documentation caching utility for UltraPlot.

This script provides functions to manage caching of documentation builds,
including notebook execution results and Sphinx doctrees.
"""

import hashlib
import json
import os
import pickle
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set


class DocCacheManager:
    """Manage caching for documentation builds."""

    def __init__(self, cache_dir: str = ".doc_cache"):
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            print(f"Warning: Could not create cache directory: {e}")
            # Fallback to current directory if cache_dir is not writable
            self.cache_dir = Path(".")

        self.notebook_cache_file = self.cache_dir / "notebook_cache.json"
        self.doctree_cache_file = self.cache_dir / "doctree_cache.json"
        self.file_hashes_file = self.cache_dir / "file_hashes.json"

        # Initialize cache files if they don't exist
        self._initialize_cache_files()

    def _initialize_cache_files(self):
        """Initialize cache files if they don't exist."""
        for cache_file in [
            self.notebook_cache_file,
            self.doctree_cache_file,
            self.file_hashes_file,
        ]:
            if not cache_file.exists():
                try:
                    with open(cache_file, "w") as f:
                        json.dump({}, f)
                except Exception as e:
                    print(f"Warning: Could not initialize cache file {cache_file}: {e}")

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file."""
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _get_directory_hash(self, directory: Path, patterns: List[str] = None) -> str:
        """Calculate hash of all files in a directory."""
        if patterns is None:
            patterns = ["*.py", "*.rst", "*.md", "*.ipynb"]

        hash_obj = hashlib.sha256()

        for pattern in patterns:
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    file_hash = self._get_file_hash(file_path)
                    hash_obj.update(file_hash.encode("utf-8"))

        return hash_obj.hexdigest()

    def check_source_changes(self, source_dir: str = ".") -> bool:
        """Check if source files have changed since last build."""
        source_path = Path(source_dir)
        current_hash = self._get_directory_hash(source_path)

        # Load previous hash
        try:
            with open(self.file_hashes_file, "r") as f:
                file_hashes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            file_hashes = {}

        previous_hash = file_hashes.get("source_hash", "")

        # Update hash file
        file_hashes["source_hash"] = current_hash
        with open(self.file_hashes_file, "w") as f:
            json.dump(file_hashes, f, indent=2)

        return current_hash != previous_hash

    def cache_notebook_results(self, notebook_paths: List[str]):
        """Cache notebook execution results."""
        notebook_cache = {}

        # Load existing cache
        try:
            with open(self.notebook_cache_file, "r") as f:
                notebook_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            notebook_cache = {}

        # Update cache with current notebooks
        for notebook_path in notebook_paths:
            notebook_file = Path(notebook_path)
            if notebook_file.exists():
                file_hash = self._get_file_hash(notebook_file)
                notebook_cache[notebook_path] = {
                    "hash": file_hash,
                    "timestamp": str(Path(notebook_path).stat().st_mtime),
                }

        # Save updated cache
        with open(self.notebook_cache_file, "w") as f:
            json.dump(notebook_cache, f, indent=2)

    def should_rebuild_notebook(self, notebook_path: str) -> bool:
        """Check if a notebook needs to be re-executed."""
        notebook_file = Path(notebook_path)
        if not notebook_file.exists():
            return True

        # Load notebook cache
        try:
            with open(self.notebook_cache_file, "r") as f:
                notebook_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True

        cached_info = notebook_cache.get(notebook_path)
        if not cached_info:
            return True

        current_hash = self._get_file_hash(notebook_file)
        current_mtime = str(notebook_file.stat().st_mtime)

        return current_hash != cached_info.get(
            "hash"
        ) or current_mtime != cached_info.get("timestamp")

    def cache_doctrees(self, doctree_dir: str):
        """Cache Sphinx doctrees."""
        doctree_path = Path(doctree_dir)
        if not doctree_path.exists():
            return

        # Calculate hash of all doctree files
        doctree_hash = self._get_directory_hash(doctree_path, ["*.doctree", "*.pickle"])

        # Save doctree cache info
        doctree_cache = {}
        try:
            with open(self.doctree_cache_file, "r") as f:
                doctree_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            doctree_cache = {}

        doctree_cache["doctree_hash"] = doctree_hash
        doctree_cache["timestamp"] = str(Path().cwd().stat().st_mtime)

        with open(self.doctree_cache_file, "w") as f:
            json.dump(doctree_cache, f, indent=2)

    def should_rebuild_doctrees(self) -> bool:
        """Check if doctrees need to be rebuilt."""
        # Check if source files have changed
        if self.check_source_changes():
            return True

        # Load doctree cache
        try:
            with open(self.doctree_cache_file, "r") as f:
                doctree_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True

        # Check if any cached notebooks need rebuilding
        try:
            with open(self.notebook_cache_file, "r") as f:
                notebook_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return True

        for notebook_path, cached_info in notebook_cache.items():
            if self.should_rebuild_notebook(notebook_path):
                return True

        return False

    def clear_cache(self):
        """Clear all cached data."""
        # Remove cache files
        for cache_file in [
            self.notebook_cache_file,
            self.doctree_cache_file,
            self.file_hashes_file,
        ]:
            if cache_file.exists():
                cache_file.unlink()

        # Remove cached doctrees
        doctree_dir = Path("_build/doctrees")
        if doctree_dir.exists():
            shutil.rmtree(doctree_dir)

        print("Cache cleared successfully.")

    def get_cache_info(self) -> Dict:
        """Get information about current cache status."""
        cache_info = {"notebook_cache": {}, "doctree_cache": {}, "file_hashes": {}}

        # Load notebook cache info
        try:
            with open(self.notebook_cache_file, "r") as f:
                cache_info["notebook_cache"] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Load doctree cache info
        try:
            with open(self.doctree_cache_file, "r") as f:
                cache_info["doctree_cache"] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Load file hashes
        try:
            with open(self.file_hashes_file, "r") as f:
                cache_info["file_hashes"] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return cache_info


def main():
    """Main function for command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="UltraPlot Documentation Cache Manager"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if rebuild is needed")
    check_parser.add_argument(
        "--source-dir", default=".", help="Source directory to check"
    )

    # Clear command
    subparsers.add_parser("clear", help="Clear all cached data")

    # Info command
    subparsers.add_parser("info", help="Show cache information")

    # Cache doctrees command
    cache_parser = subparsers.add_parser("cache_doctrees", help="Cache doctree files")
    cache_parser.add_argument("doctree_dir", help="Directory containing doctree files")

    args = parser.parse_args()

    cache_manager = DocCacheManager()

    if args.command == "check":
        if cache_manager.should_rebuild_doctrees():
            print("Rebuild needed: Source files or dependencies have changed.")
            return 1
        else:
            print("No rebuild needed: All source files are up to date.")
            return 0

    elif args.command == "clear":
        cache_manager.clear_cache()
        return 0

    elif args.command == "info":
        cache_info = cache_manager.get_cache_info()
        print(json.dumps(cache_info, indent=2))
        return 0

    elif args.command == "cache_doctrees":
        cache_manager.cache_doctrees(args.doctree_dir)
        print("Doctrees cached successfully.")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
