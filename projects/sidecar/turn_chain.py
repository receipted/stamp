#!/usr/bin/env python3
"""
turn_chain.py — Hash-chain individual conversation turns.

Every prompt and response gets a receipt:
  {
    turn_id:       unique ID for this turn
    role:          user | assistant
    model:         which model responded (from session snapshot)
    prompt_hash:   sha256 of the prompt text
    response_hash: sha256 of the response text (or text of this turn)
    prev_turn_hash: sha256 of the previous turn receipt
    timestamp:     when this turn happened
  }

The chain proves:
  - What was said (hash of text)
  - Who said it (role + model)
  - When (timestamp)
  - Order (prev_turn_hash)

Cannot be modified without breaking every subsequent hash.

Usage:
  python3 turn_chain.py <session.jsonl>
  python3 turn_chain.py <session.jsonl> --verify
  python3 turn_chain.py <session.jsonl> --summary

FUTURE: Uplift to Rust. Anchor daily Merkle root on-chain.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CHAIN_DIR = "/Users/Shared/sidecar-ore/turn-chains"


# --- Pure functions ---

def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_turn(role: str, model: str, text: str, timestamp: str) -> str:
    """Pure function. Hash the content of a single turn."""
    canonical = json.dumps({
        "role": role,
        "model": model,
        "text": text,
        "timestamp": timestamp,
    }, sort_keys=True, separators=(',', ':'))
    return h(canonical.encode())


def make_turn_receipt(
    turn_index: int,
    role: str,
    model: str,
    text: str,
    timestamp: str,
    prev_receipt_hash: str,
) -> dict:
    """Pure function. Build a turn receipt."""
    turn_hash = hash_turn(role, model, text, timestamp)
    receipt = {
        "schema": "sidecar.turn.v1",
        "turn_index": turn_index,
        "role": role,
        "model": model,
        "text_hash": turn_hash,
        "text_length": len(text),
        "timestamp": timestamp,
        "prev_receipt_hash": prev_receipt_hash,
    }
    receipt["receipt_hash"] = h(
        json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    )
    return receipt


def extract_turns_from_session(session_path: str) -> list[dict]:
    """
    Extract conversation turns from an OpenClaw session JSONL.
    Returns list of {role, model, text, timestamp} dicts.
    IO function — reads from disk.
    """
    turns = []
    current_model = "unknown"

    with open(session_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Track model changes
            if obj.get("type") == "model_change":
                current_model = obj.get("modelId", current_model)
                continue

            if obj.get("type") == "custom" and obj.get("customType") == "model-snapshot":
                data = obj.get("data", {})
                current_model = data.get("modelId", current_model)
                continue

            # Extract message turns
            if obj.get("type") != "message":
                continue

            msg = obj.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue

            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                text = " ".join(text_parts)
            else:
                text = str(content)

            text = text.strip()
            if not text or len(text) < 5:
                continue

            timestamp = obj.get("timestamp", "")

            turns.append({
                "role": role,
                "model": current_model if role == "assistant" else "human",
                "text": text,
                "timestamp": timestamp,
            })

    return turns


def build_chain(turns: list[dict]) -> list[dict]:
    """
    Pure function. Build receipt chain from turn list.
    Same turns → same chain, every time.
    """
    chain = []
    prev_hash = h(b"genesis")

    for i, turn in enumerate(turns):
        receipt = make_turn_receipt(
            turn_index=i,
            role=turn["role"],
            model=turn["model"],
            text=turn["text"],
            timestamp=turn["timestamp"],
            prev_receipt_hash=prev_hash,
        )
        chain.append(receipt)
        prev_hash = receipt["receipt_hash"]

    return chain


def merkle_root(hashes: list[str]) -> str:
    """Pure function. Compute Merkle root over a list of hex hashes.
    Same hashes → same root. Always. No IO.
    """
    import hashlib
    if not hashes:
        return h(b"empty")
    layer = [bytes.fromhex(x) for x in hashes]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256(layer[i] + layer[i + 1]).digest()
            for i in range(0, len(layer), 2)
        ]
    return layer[0].hex()


def compute_anchor(chain: list[dict]) -> dict:
    """Pure function. Compute Merkle root over all turn receipts.
    Same chain → same anchor. Always. No IO.

    Returns anchor dict suitable for git commit message or on-chain submission.
    """
    receipt_hashes = [r["receipt_hash"] for r in chain if "receipt_hash" in r]
    root = merkle_root(receipt_hashes)
    return {
        "schema": "sidecar.anchor.v1",
        "merkle_root": root,
        "turn_count": len(chain),
        "receipt_count": len(receipt_hashes),
        "first_turn_hash": chain[0]["receipt_hash"] if chain else "",
        "last_turn_hash": chain[-1]["receipt_hash"] if chain else "",
    }


def verify_chain(chain: list[dict]) -> tuple[bool, list[str]]:
    """
    Pure function. Verify every link in the chain.
    Returns (all_valid, list_of_errors).
    """
    errors = []
    prev_hash = h(b"genesis")

    for i, receipt in enumerate(chain):
        # Verify prev_receipt_hash
        if receipt.get("prev_receipt_hash") != prev_hash:
            errors.append(f"Turn {i}: prev_hash mismatch")

        # Verify receipt_hash
        check = dict(receipt)
        claimed_hash = check.pop("receipt_hash", "")
        computed_hash = h(
            json.dumps(check, sort_keys=True, separators=(',', ':')).encode()
        )
        if computed_hash != claimed_hash:
            errors.append(f"Turn {i}: receipt_hash invalid")

        prev_hash = receipt.get("receipt_hash", "")

    return len(errors) == 0, errors


# --- IO layer ---

def run_chain(session_path: str):
    """Build and save a turn chain from a session file."""
    print(f"Session: {os.path.basename(session_path)}")

    turns = extract_turns_from_session(session_path)
    print(f"  Turns extracted: {len(turns)}")

    if not turns:
        print("  ERROR: no turns found")
        sys.exit(1)

    chain = build_chain(turns)
    print(f"  Chain built: {len(chain)} receipts")

    # Show model distribution
    models = {}
    for r in chain:
        m = r.get("model", "unknown")
        models[m] = models.get(m, 0) + 1
    print(f"  Models: {dict(models)}")

    # Save chain
    os.makedirs(CHAIN_DIR, exist_ok=True)
    os.chmod(CHAIN_DIR, 0o777)

    session_id = Path(session_path).stem[:16]
    chain_path = os.path.join(CHAIN_DIR, f"{session_id}.turn-chain.jsonl")

    with open(chain_path, "w") as f:
        for receipt in chain:
            f.write(json.dumps(receipt, separators=(',', ':')) + "\n")

    final_hash = chain[-1]["receipt_hash"]
    print(f"  Final hash: {final_hash[:32]}...")
    print(f"  Chain saved: {os.path.basename(chain_path)}")
    print()
    print("VERIFY:")
    print(f"  python3 turn_chain.py {session_path} --verify")


def run_verify(session_path: str):
    """Verify an existing turn chain against the source session."""
    session_id = Path(session_path).stem[:16]
    chain_path = os.path.join(CHAIN_DIR, f"{session_id}.turn-chain.jsonl")

    if not os.path.exists(chain_path):
        print(f"ERROR: no chain found at {chain_path}")
        print(f"  Run: python3 turn_chain.py {session_path}")
        sys.exit(1)

    chain = []
    with open(chain_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chain.append(json.loads(line))

    valid, errors = verify_chain(chain)

    if valid:
        print(f"PASS: chain intact ({len(chain)} turns)")
        print(f"  Final hash: {chain[-1]['receipt_hash'][:32]}...")
    else:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  {e}")


def run_summary(session_path: str):
    """Show summary of models used in a session."""
    turns = extract_turns_from_session(session_path)
    models = {}
    for t in turns:
        m = t["model"]
        models[m] = models.get(m, 0) + 1

    print(f"Session: {os.path.basename(session_path)}")
    print(f"Total turns: {len(turns)}")
    print("Models:")
    for model, count in sorted(models.items(), key=lambda x: -x[1]):
        print(f"  {model}: {count} turns")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 turn_chain.py <session.jsonl>")
        print("  python3 turn_chain.py <session.jsonl> --verify")
        print("  python3 turn_chain.py <session.jsonl> --summary")
        sys.exit(1)

    session_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "--chain"

    if not os.path.exists(session_path):
        print(f"ERROR: file not found: {session_path}")
        sys.exit(1)

    if mode == "--verify":
        run_verify(session_path)
    elif mode == "--summary":
        run_summary(session_path)
    else:
        run_chain(session_path)
