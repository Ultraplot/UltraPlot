#!/usr/bin/env python3
"""Serve the local docs preview and retain draggable alias-map positions."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


LAYOUT_KEYS = {"layout", "titles", "axes", "plot", "legend", "colorbar", "style"}


def _valid_layout(payload):
    if not isinstance(payload, dict) or payload.get("version") != 1:
        return False
    nodes = payload.get("nodes")
    if not isinstance(nodes, dict) or set(nodes) != LAYOUT_KEYS:
        return False
    for value in nodes.values():
        if not isinstance(value, list) or len(value) != 2:
            return False
        if not all(isinstance(item, (int, float)) for item in value):
            return False
        if not all(-250 <= item <= 1_000 for item in value):
            return False
    return True


def make_handler(directory, draft_path):
    class AliasDocsHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def do_GET(self):
            if urlsplit(self.path).path != "/__alias_layout":
                return super().do_GET()
            payload = draft_path.read_bytes() if draft_path.exists() else b'{"version":1,"nodes":{}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            if urlsplit(self.path).path != "/__alias_layout":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16_384:
                    raise ValueError("invalid payload size")
                payload = json.loads(self.rfile.read(length))
                if not _valid_layout(payload):
                    raise ValueError("invalid alias layout")
                temporary = draft_path.with_suffix(".tmp")
                temporary.write_text(json.dumps(payload, indent=2) + "\n")
                temporary.replace(draft_path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                self.send_error(400, str(error))
                return
            self.send_response(204)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

    return AliasDocsHandler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    handler = make_handler(args.directory.resolve(), args.draft.resolve())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Serving alias docs at http://127.0.0.1:{args.port}/aliases.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
