"""The stamp primitive — generic receipted pure transform.

input → pure function → stamped output

A stamp proves:
  - what went in (input_hash)
  - which function ran (fn_hash)
  - what came out (output_hash)
  - what it chained from (prev_stamp_hash)

Pure. No I/O. No timestamps. No randomness.
Same inputs → same stamp, always.

Must produce byte-identical output to rust/src/stamp.rs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


def h(data: bytes) -> str:
    """SHA-256 of raw bytes, returned as hex string."""
    return hashlib.sha256(data).hexdigest()


def _canonical_json(obj: dict) -> str:
    """Canonical JSON: sorted keys, compact separators.
    Matches Rust's canonical_json() exactly."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _hash_json(obj: dict) -> str:
    """Hash canonical JSON representation."""
    return h(_canonical_json(obj).encode())


GENESIS = h(b"genesis")


@dataclass(frozen=True)
class Stamp:
    schema: str
    domain: str
    input_hash: str
    fn_hash: str
    output_hash: str
    prev_stamp_hash: str
    stamp_hash: str


def stamp(
    domain: str,
    input_hash: str,
    fn_hash: str,
    output_hash: str,
    prev_stamp_hash: str,
) -> Stamp:
    """Mint a stamp. Pure function. The primitive.

    Must produce identical stamp_hash to the Rust implementation.
    """
    partial = {
        "schema": "substrate.stamp.v1",
        "domain": domain,
        "input_hash": input_hash,
        "fn_hash": fn_hash,
        "output_hash": output_hash,
        "prev_stamp_hash": prev_stamp_hash,
    }
    stamp_hash = _hash_json(partial)

    return Stamp(
        schema="substrate.stamp.v1",
        domain=domain,
        input_hash=input_hash,
        fn_hash=fn_hash,
        output_hash=output_hash,
        prev_stamp_hash=prev_stamp_hash,
        stamp_hash=stamp_hash,
    )


def verify_stamp(s: Stamp) -> bool:
    """Verify a stamp's self-hash. Pure."""
    partial = {
        "schema": s.schema,
        "domain": s.domain,
        "input_hash": s.input_hash,
        "fn_hash": s.fn_hash,
        "output_hash": s.output_hash,
        "prev_stamp_hash": s.prev_stamp_hash,
    }
    return _hash_json(partial) == s.stamp_hash


def verify_stamp_chain(chain: list[Stamp]) -> tuple[bool, list[str]]:
    """Verify a chain of stamps. Pure."""
    errors = []
    prev_hash = GENESIS

    for i, s in enumerate(chain):
        if s.prev_stamp_hash != prev_hash:
            errors.append(f"Stamp {i}: prev_stamp_hash mismatch")
        if not verify_stamp(s):
            errors.append(f"Stamp {i}: stamp_hash invalid")
        prev_hash = s.stamp_hash

    return len(errors) == 0, errors


def stamp_chain_anchor(chain: list[Stamp]) -> str:
    """Merkle root over stamp_hash values. Pure."""
    hashes = [s.stamp_hash for s in chain]
    return _merkle_root(hashes)


def _merkle_root(hashes: list[str]) -> str:
    """Compute Merkle root. Pure. Matches Rust implementation."""
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


# --- Domain wrappers ---

def stamp_turn(input_hash: str, fn_hash: str, output_hash: str, prev: str) -> Stamp:
    return stamp("turn", input_hash, fn_hash, output_hash, prev)

def stamp_sieve(input_hash: str, fn_hash: str, output_hash: str, prev: str) -> Stamp:
    return stamp("sieve", input_hash, fn_hash, output_hash, prev)

def stamp_intent(input_hash: str, fn_hash: str, output_hash: str, prev: str) -> Stamp:
    return stamp("intent", input_hash, fn_hash, output_hash, prev)
