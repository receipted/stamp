#!/usr/bin/env python3
"""
Sidecar Verify — independently verify any ore blob.

Usage: python verify.py path/to/blob.ore.json

This script is 20 lines of logic. Read it. Understand it. Pin its hash.
Then you never need to read it again — just check the hash hasn't changed.

  sha256sum verify.py  # Record this. Check it before each use.

FUTURE: Uplift to Rust alongside watcher.
"""

import hashlib
import json
import sys
import os


def verify(ore_path: str) -> bool:
    # Load the ore blob
    with open(ore_path) as f:
        blob = json.load(f)

    # Find the raw content file (same name, .raw extension)
    raw_path = ore_path.replace(".ore.json", ".raw")
    if not os.path.exists(raw_path):
        print(f"FAIL: raw file not found: {raw_path}")
        return False

    # Read raw content
    with open(raw_path, "rb") as f:
        content = f.read()

    # Independently compute the hash
    actual_hash = hashlib.sha256(content).hexdigest()
    claimed_hash = blob["content_hash"]

    # Compare
    if actual_hash == claimed_hash:
        print(f"PASS: {os.path.basename(ore_path)}")
        print(f"  hash: {actual_hash}")
        print(f"  size: {len(content)} bytes (claimed: {blob['content_size']})")
        return True
    else:
        print(f"FAIL: hash mismatch!")
        print(f"  claimed: {claimed_hash}")
        print(f"  actual:  {actual_hash}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify.py path/to/blob.ore.json")
        sys.exit(1)

    ok = verify(sys.argv[1])
    sys.exit(0 if ok else 1)
