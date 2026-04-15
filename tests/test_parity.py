"""Cross-language parity tests — Python stamps must be byte-identical to Rust stamps.

Runs the same inputs through both languages and compares outputs.
This is the most important invariant in the system: if Python and Rust
disagree on a stamp hash, the entire custody chain is broken.

Usage:
    /Users/Shared/substrate/.venv/bin/python3 -m pytest tests/test_parity.py -v
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure substrate is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.surface.stamp import stamp, verify_stamp, verify_stamp_chain, stamp_chain_anchor, GENESIS, h, _canonical_json

RUST_BINARY = Path(__file__).parent.parent / "rust" / "target" / "release" / "substrate"


def rust_available() -> bool:
    return RUST_BINARY.exists()


# ---------------------------------------------------------------------------
# Core hash parity
# ---------------------------------------------------------------------------

class TestHashParity:
    """SHA-256 and canonical JSON must produce identical results."""

    def test_genesis_hash(self):
        """h(b"genesis") must be the same everywhere."""
        py = h(b"genesis")
        assert py == "aeebad4a796fcc2e15dc4c6061b45ed9b373f26adfc798ca7d2d8cc58182718e"
        assert py == GENESIS

    def test_empty_hash(self):
        py = h(b"")
        assert py == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_canonical_json_sorted_keys(self):
        obj = {"b": 2, "a": 1}
        result = _canonical_json(obj)
        assert result == '{"a":1,"b":2}'

    def test_canonical_json_nested(self):
        obj = {"z": {"b": 2, "a": 1}, "a": [3, 1]}
        result = _canonical_json(obj)
        assert result == '{"a":[3,1],"z":{"a":1,"b":2}}'

    def test_canonical_json_string_escaping(self):
        obj = {"text": 'hello "world"\nnewline'}
        result = _canonical_json(obj)
        assert result == '{"text":"hello \\"world\\"\\nnewline"}'

    def test_canonical_json_hash_deterministic(self):
        """Same object, multiple calls, same hash."""
        obj = {"domain": "turn", "fn_hash": "bbb", "input_hash": "aaa"}
        h1 = h(_canonical_json(obj).encode())
        h2 = h(_canonical_json(obj).encode())
        assert h1 == h2


# ---------------------------------------------------------------------------
# Stamp parity
# ---------------------------------------------------------------------------

class TestStampParity:
    """stamp() must produce identical hashes in Python and Rust."""

    def test_stamp_known_values(self):
        """stamp("turn", "aaa", "bbb", "ccc", genesis) → known hash."""
        s = stamp("turn", "aaa", "bbb", "ccc", GENESIS)
        # This is the canonical value. If this changes, Rust must change too.
        assert s.stamp_hash == "45f3a2ccce4525eee8217324f8d367e2df227e9c53ede0e89dbab1b3d6a66f0c"

    def test_stamp_canonical_json_matches_rust(self):
        """The partial JSON that gets hashed must be byte-identical to Rust."""
        partial = _canonical_json({
            "schema": "substrate.stamp.v1",
            "domain": "turn",
            "input_hash": "aaa",
            "fn_hash": "bbb",
            "output_hash": "ccc",
            "prev_stamp_hash": GENESIS,
        })
        expected = (
            '{"domain":"turn","fn_hash":"bbb","input_hash":"aaa",'
            '"output_hash":"ccc","prev_stamp_hash":"'
            + GENESIS
            + '","schema":"substrate.stamp.v1"}'
        )
        assert partial == expected

    def test_stamp_different_domains(self):
        """Same inputs, different domains → different hashes."""
        s1 = stamp("turn", "a", "b", "c", GENESIS)
        s2 = stamp("sieve", "a", "b", "c", GENESIS)
        s3 = stamp("intent", "a", "b", "c", GENESIS)
        assert s1.stamp_hash != s2.stamp_hash
        assert s2.stamp_hash != s3.stamp_hash

    def test_stamp_deterministic(self):
        s1 = stamp("turn", "x", "y", "z", GENESIS)
        s2 = stamp("turn", "x", "y", "z", GENESIS)
        assert s1.stamp_hash == s2.stamp_hash

    def test_stamp_schema_version(self):
        s = stamp("turn", "a", "b", "c", GENESIS)
        assert s.schema == "substrate.stamp.v1"


# ---------------------------------------------------------------------------
# Chain parity
# ---------------------------------------------------------------------------

class TestChainParity:
    """Chains built in Python must verify correctly."""

    def test_chain_of_three(self):
        s1 = stamp("sieve", "in1", "fn1", "out1", GENESIS)
        s2 = stamp("sieve", "in2", "fn1", "out2", s1.stamp_hash)
        s3 = stamp("sieve", "in3", "fn1", "out3", s2.stamp_hash)
        chain = [s1, s2, s3]
        valid, errors = verify_stamp_chain(chain)
        assert valid, f"errors: {errors}"

    def test_chain_broken_link(self):
        s1 = stamp("sieve", "in1", "fn1", "out1", GENESIS)
        s2 = stamp("sieve", "in2", "fn1", "out2", "wrong_prev")
        valid, _ = verify_stamp_chain([s1, s2])
        assert not valid

    def test_chain_tampered_stamp(self):
        s1 = stamp("turn", "a", "b", "c", GENESIS)
        # Tamper with a field
        from dataclasses import replace
        s1_bad = replace(s1, input_hash="tampered")
        assert not verify_stamp(s1_bad)

    def test_anchor_deterministic(self):
        s1 = stamp("turn", "a", "b", "c", GENESIS)
        s2 = stamp("turn", "d", "b", "e", s1.stamp_hash)
        root1 = stamp_chain_anchor([s1, s2])
        root2 = stamp_chain_anchor([s1, s2])
        assert root1 == root2
        assert len(root1) == 64  # hex SHA-256


# ---------------------------------------------------------------------------
# Merkle root parity
# ---------------------------------------------------------------------------

class TestMerkleParity:
    """Merkle roots must be identical to Rust."""

    def test_merkle_single(self):
        root = stamp_chain_anchor([stamp("t", "a", "b", "c", GENESIS)])
        # Single element → root = that element's hash
        s = stamp("t", "a", "b", "c", GENESIS)
        assert root == s.stamp_hash

    def test_merkle_empty(self):
        from src.surface.stamp import _merkle_root
        root = _merkle_root([])
        assert root == h(b"empty")

    def test_merkle_two(self):
        from src.surface.stamp import _merkle_root
        h1 = h(b"one")
        h2 = h(b"two")
        root = _merkle_root([h1, h2])
        # Manual: SHA256(decode(h1) || decode(h2))
        manual = hashlib.sha256(bytes.fromhex(h1) + bytes.fromhex(h2)).hexdigest()
        assert root == manual


# ---------------------------------------------------------------------------
# Cross-language parity (requires Rust binary)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not rust_available(), reason="Rust binary not built")
class TestCrossLanguageParity:
    """Run the same operations in Rust and Python, compare outputs."""

    def test_ore_verify_parity(self):
        """Both languages verify the same ore blob identically."""
        import glob
        ore_files = sorted(glob.glob("/Users/Shared/sidecar-ore/*.ore.json"))
        if not ore_files:
            pytest.skip("No ore files available")
        ore_path = ore_files[0]

        # Python verify
        with open(ore_path) as f:
            blob = json.load(f)
        raw_path = ore_path.replace(".ore.json", ".raw")
        with open(raw_path, "rb") as f:
            content = f.read()
        py_hash = h(content)
        py_pass = py_hash == blob["content_hash"]

        # Rust verify
        result = subprocess.run(
            [str(RUST_BINARY), "verify", ore_path],
            capture_output=True, text=True,
        )
        rust_pass = result.returncode == 0

        assert py_pass == rust_pass, f"Python={py_pass}, Rust={rust_pass}"

    def test_ledger_verify_parity(self):
        """Both languages verify the ledger chain identically."""
        # Rust
        result = subprocess.run(
            [str(RUST_BINARY), "ledger", "verify"],
            capture_output=True, text=True,
        )
        rust_pass = "PASS" in result.stdout

        # Python: read ledger, verify chain
        ledger_path = "/Users/Shared/sidecar-ore/ledger.jsonl"
        if not Path(ledger_path).exists():
            pytest.skip("No ledger file")
        entries = []
        with open(ledger_path) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        prev_hash = h(b"genesis")
        py_pass = True
        for entry in entries:
            claimed = entry.get("prev_entry_hash", "")
            if claimed != prev_hash:
                py_pass = False
                break
            prev_hash = h(_canonical_json(entry).encode())

        assert py_pass == rust_pass, f"Python={py_pass}, Rust={rust_pass}"

    def test_turn_chain_verify_parity(self):
        """Both languages verify the same turn chain identically."""
        import glob
        chains = glob.glob("/Users/Shared/sidecar-ore/turn-chains/*.turn-chain.jsonl")
        if not chains:
            pytest.skip("No turn chains available")
        chain_path = chains[0]

        # Rust
        result = subprocess.run(
            [str(RUST_BINARY), "turn-chain", "verify", chain_path],
            capture_output=True, text=True,
        )
        rust_pass = "PASS" in result.stdout

        # Extract Rust Merkle root
        rust_root = ""
        for line in result.stdout.split("\n"):
            if "Merkle root:" in line:
                rust_root = line.split("Merkle root:")[1].strip()

        # Python: verify + compute root
        from src.surface.stamp import _merkle_root
        receipts = []
        with open(chain_path) as f:
            for line in f:
                if line.strip():
                    receipts.append(json.loads(line))

        # Verify chain integrity
        prev_hash = h(b"genesis")
        py_pass = True
        for i, r in enumerate(receipts):
            if r.get("prev_receipt_hash") != prev_hash:
                py_pass = False
                break
            check = dict(r)
            claimed = check.pop("receipt_hash", "")
            computed = h(_canonical_json(check).encode())
            if computed != claimed:
                py_pass = False
                break
            prev_hash = r["receipt_hash"]

        # Compute Merkle root
        py_root = _merkle_root([r["receipt_hash"] for r in receipts])

        assert py_pass == rust_pass, f"Python chain={py_pass}, Rust chain={rust_pass}"
        if rust_root:
            assert py_root == rust_root, f"Python root={py_root[:16]}..., Rust root={rust_root[:16]}..."
