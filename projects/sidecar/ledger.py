#!/usr/bin/env python3
"""
Sidecar Ledger — hash chain + Merkle tree over ore blobs.

Every ore blob that gets captured gets appended to the ledger.
The ledger is a hash chain: each entry includes the hash of the previous entry.
Periodically, a Merkle root is computed over all entries and written as an anchor.

This proves:
  - Ordering: entry N provably came after entry N-1
  - Completeness: the Merkle root covers all entries, nothing was silently dropped
  - Tamper evidence: any modification breaks the chain

FUTURE: Uplift to Rust. Anchor the daily Merkle root to a public git commit.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = "/Users/Shared/sidecar-ore/ledger.jsonl"
ORE_DIR = "/Users/Shared/sidecar-ore"


# --- Pure functions (no I/O) ---

def h(data: bytes) -> str:
    """SHA-256. That's it."""
    return hashlib.sha256(data).hexdigest()


def hash_entry(entry: dict) -> str:
    """Canonical hash of a ledger entry. sort_keys for determinism."""
    return h(json.dumps(entry, sort_keys=True, separators=(',', ':')).encode())


def function_hash() -> str:
    """
    Hash of this file's own source — the 'contract signature'.
    Proves which version of the ledger function ran.
    Anyone can verify: sha256sum ledger.py and compare.
    """
    return h(Path(__file__).read_bytes())


def make_entry(ore_blob_path: str, ore_content_hash: str, prev_entry_hash: str) -> dict:
    """
    Pure function. Build a ledger entry.
    contract_hash pins the exact version of this function that ran.
    The entry hash is computed AFTER construction, by the caller.
    """
    return {
        "schema": "sidecar.ledger.v1",
        "ore_blob_path": ore_blob_path,
        "ore_content_hash": ore_content_hash,
        "prev_entry_hash": prev_entry_hash,
        "contract_hash": function_hash(),  # SHA-256 of ledger.py itself
        "appended_at": datetime.now(timezone.utc).isoformat(),
    }


def merkle_root(hashes: list[str]) -> str:
    """
    Compute Merkle root over a list of hex hashes.
    Standard binary tree: pair up, hash each pair, repeat until one root.
    Empty list returns hash of empty string.
    """
    if not hashes:
        return h(b"")

    layer = [bytes.fromhex(x) for x in hashes]

    while len(layer) > 1:
        # Pad to even length by duplicating last element
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256(layer[i] + layer[i + 1]).digest()
            for i in range(0, len(layer), 2)
        ]

    return layer[0].hex()


# --- I/O layer ---

def read_ledger() -> list[dict]:
    """Read all ledger entries. Returns empty list if ledger doesn't exist."""
    if not os.path.exists(LEDGER_PATH):
        return []
    entries = []
    with open(LEDGER_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def last_entry_hash(entries: list[dict]) -> str:
    """Hash of the last entry, or genesis hash if ledger is empty."""
    if not entries:
        return h(b"genesis")
    return hash_entry(entries[-1])


def append_entry(entry: dict):
    """Append one entry to the ledger (append-only, never overwrite)."""
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(entry, sort_keys=True, separators=(',', ':')) + "\n")


def compute_anchor(entries: list[dict]) -> dict:
    """
    Compute the current Merkle root over all ledger entries.
    Returns an anchor object — suitable for publishing to a public git commit.
    """
    entry_hashes = [hash_entry(e) for e in entries]
    root = merkle_root(entry_hashes)
    return {
        "schema": "sidecar.anchor.v1",
        "entry_count": len(entries),
        "merkle_root": root,
        "anchored_at": datetime.now(timezone.utc).isoformat(),
    }


# --- Commands ---

def cmd_append(ore_blob_path: str):
    """Append an ore blob to the ledger."""
    # Read the ore blob
    with open(ore_blob_path) as f:
        blob = json.load(f)

    entries = read_ledger()
    prev_hash = last_entry_hash(entries)

    entry = make_entry(
        ore_blob_path=ore_blob_path,
        ore_content_hash=blob["content_hash"],
        prev_entry_hash=prev_hash,
    )

    append_entry(entry)
    entry_hash = hash_entry(entry)

    print(f"APPENDED: {os.path.basename(ore_blob_path)}")
    print(f"  entry_hash:  {entry_hash}")
    print(f"  prev_hash:   {prev_hash}")
    print(f"  ore_hash:    {blob['content_hash'][:16]}...")
    print(f"  total entries: {len(entries) + 1}")


def cmd_verify():
    """Walk the entire chain and verify every link."""
    entries = read_ledger()
    if not entries:
        print("Ledger is empty.")
        return

    print(f"Verifying {len(entries)} entries...")
    prev_hash = h(b"genesis")
    failures = 0

    for i, entry in enumerate(entries):
        claimed_prev = entry.get("prev_entry_hash")
        if claimed_prev != prev_hash:
            print(f"  FAIL [{i}]: prev_hash mismatch")
            print(f"    expected: {prev_hash}")
            print(f"    claimed:  {claimed_prev}")
            failures += 1
        prev_hash = hash_entry(entry)

    # Verify contract hash on every entry
    current_contract = function_hash()
    contract_mismatches = set()
    for i, entry in enumerate(entries):
        ec = entry.get("contract_hash")
        if ec and ec != current_contract:
            contract_mismatches.add(ec[:16])

    if failures == 0:
        print(f"PASS: chain intact ({len(entries)} entries)")
    else:
        print(f"FAIL: {failures} broken link(s)")

    if contract_mismatches:
        print(f"  WARN: {len(contract_mismatches)} different contract version(s) in chain")
        print(f"  Current contract: {current_contract[:16]}...")
        print(f"  To verify a version: sha256sum ledger.py")
    else:
        print(f"  Contract: {current_contract[:16]}... (all entries match this version)")

    anchor = compute_anchor(entries)
    print(f"  Merkle root: {anchor['merkle_root']}")
    print(f"  Anchor this root to prove state at: {anchor['anchored_at']}")


def cmd_anchor():
    """Print the current Merkle root — ready to publish."""
    entries = read_ledger()
    anchor = compute_anchor(entries)
    print(json.dumps(anchor, indent=2))


def cmd_status():
    """Show ledger status."""
    entries = read_ledger()
    print(f"Ledger: {LEDGER_PATH}")
    print(f"Entries: {len(entries)}")
    if entries:
        first = entries[0]
        last = entries[-1]
        print(f"First:  {first.get('appended_at', '?')}")
        print(f"Last:   {last.get('appended_at', '?')}")
        anchor = compute_anchor(entries)
        print(f"Merkle root: {anchor['merkle_root']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ledger.py append <ore_blob.ore.json>")
        print("  python ledger.py verify")
        print("  python ledger.py anchor")
        print("  python ledger.py status")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "append" and len(sys.argv) == 3:
        cmd_append(sys.argv[2])
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "anchor":
        cmd_anchor()
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
