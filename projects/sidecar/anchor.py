#!/usr/bin/env python3
"""
anchor.py — Anchor a turn chain to a public, verifiable record.

IO layer only. All computation is in turn_chain.compute_anchor() (pure).

Free tier: git commit anchor — timestamped by git, verifiable by anyone
           with a clone of the repo.

Usage:
  python3 anchor.py <chain.jsonl>              # anchor to git
  python3 anchor.py <chain.jsonl> --show       # show anchor without committing
  python3 anchor.py <chain.jsonl> --verify     # verify chain integrity first

The git commit message contains:
  turn-chain-anchor: {merkle_root} turns={count} chain={filename}

Anyone with the chain file can independently verify:
  1. Load the chain
  2. Call compute_anchor() — same chain -> same root
  3. Compare root to the git commit message
  4. If they match: the chain is authentic and unchanged

FUTURE: --onchain flag to submit root to L2 (Base/Polygon) for trustless verification.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SIDECAR_DIR = os.path.dirname(os.path.abspath(__file__))


def load_chain(chain_path: str) -> list[dict]:
    """IO: read chain from JSONL file."""
    chain = []
    with open(chain_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chain.append(json.loads(line))
    return chain


def git_anchor(root_hash: str, chain_path: str, turn_count: int) -> str:
    """IO: write Merkle root as a git commit. Returns commit hash."""
    chain_filename = os.path.basename(chain_path)
    message = f"turn-chain-anchor: {root_hash} turns={turn_count} chain={chain_filename}"

    result = subprocess.run(
        ["git", "commit", "--allow-empty", "-m", message],
        capture_output=True,
        text=True,
        cwd=SIDECAR_DIR,
    )

    if result.returncode != 0:
        # Try from workspace root
        result = subprocess.run(
            ["git", "commit", "--allow-empty", "-m", message],
            capture_output=True,
            text=True,
            cwd=os.path.expanduser("~/.openclaw/workspace"),
        )

    if result.returncode != 0:
        raise RuntimeError(f"git commit failed: {result.stderr}")

    # Get the commit hash
    ref = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=os.path.expanduser("~/.openclaw/workspace"),
    )
    return ref.stdout.strip()


def run_anchor(chain_path: str, show_only: bool = False, verify_first: bool = False):
    """Main entry point. IO layer."""
    # Load chain
    print(f"Loading chain: {os.path.basename(chain_path)}")
    chain = load_chain(chain_path)
    print(f"  Turns: {len(chain)}")

    if len(chain) == 0:
        print("ERROR: empty chain")
        sys.exit(1)

    # Optionally verify chain integrity first
    if verify_first:
        sys.path.insert(0, SIDECAR_DIR)
        from turn_chain import verify_chain
        valid, errors = verify_chain(chain)
        if not valid:
            print(f"CHAIN INVALID: {len(errors)} error(s)")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)
        print(f"  Chain verified: intact")

    # Compute anchor (pure)
    sys.path.insert(0, SIDECAR_DIR)
    from turn_chain import compute_anchor
    anchor = compute_anchor(chain)

    print()
    print("=== ANCHOR ===")
    print(f"  Merkle root:    {anchor['merkle_root']}")
    print(f"  Turn count:     {anchor['turn_count']}")
    print(f"  First turn:     {anchor['first_turn_hash'][:16]}...")
    print(f"  Last turn:      {anchor['last_turn_hash'][:16]}...")

    if show_only:
        print()
        print("(--show only, not committing)")
        print()
        print("To anchor: python3 anchor.py " + chain_path)
        return

    # Git anchor (IO)
    print()
    print("Anchoring to git...")
    try:
        commit_hash = git_anchor(anchor['merkle_root'], chain_path, anchor['turn_count'])
        print(f"  Commit: {commit_hash[:16]}...")
        print()
        print("ANCHOR COMPLETE")
        print(f"  Merkle root: {anchor['merkle_root']}")
        print(f"  Git commit:  {commit_hash}")
        print()
        print("VERIFY (anyone with the chain file):")
        print(f"  python3 anchor.py {chain_path} --show")
        print(f"  Compare root to git log: git log --oneline | grep turn-chain-anchor")
    except RuntimeError as e:
        print(f"  Git anchor failed: {e}")
        print(f"  Root computed: {anchor['merkle_root']}")
        print(f"  Save this manually if needed.")

    # Save anchor receipt
    anchor_path = chain_path.replace(".jsonl", ".anchor.json")
    with open(anchor_path, "w") as f:
        json.dump({
            **anchor,
            "chain_path": chain_path,
            "anchored_at": datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)
    print(f"  Anchor saved: {os.path.basename(anchor_path)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 anchor.py <chain.jsonl>           # anchor to git")
        print("  python3 anchor.py <chain.jsonl> --show    # show without committing")
        print("  python3 anchor.py <chain.jsonl> --verify  # verify chain first")
        sys.exit(1)

    chain_path = sys.argv[1]
    show_only = "--show" in sys.argv
    verify_first = "--verify" in sys.argv

    if not os.path.exists(chain_path):
        print(f"ERROR: chain file not found: {chain_path}")
        sys.exit(1)

    run_anchor(chain_path, show_only=show_only, verify_first=verify_first)
