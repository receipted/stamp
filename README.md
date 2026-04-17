# stamp

Receipted deterministic transforms. 119 tests.

## What this is

A system where deterministic transforms emit execution receipts that bind:
- **what went in** (input hash)
- **which function ran** (transform identity hash)
- **what came out** (output hash)
- **what came before** (prior receipt reference)

Receipts chain. Chains prove custody. The same primitive works in Python and Rust, byte-identical.

## Core modules

| Module | Purpose |
|--------|---------|
| `src/surface/stamp.py` | Receipt primitive. Pure. No I/O. Must match `rust/src/stamp.rs`. |
| `src/surface/receipted.py` | Receipted transform orchestrators. Wraps pure transforms with stamps. |
| `src/surface/store.py` | SQLite store. Blobs, stamps, facts, edges, tx log, projections. |
| `src/surface/action_witness.py` | Witness verdict engine. Pure. Detects unwitnessed operational claims. |
| `src/surface/witness_collector.py` | I/O layer. Collects environmental evidence (process, port, log, artifact). |
| `rust/src/stamp.rs` | Rust receipt primitive. Byte-identical to Python. |

## Run tests

```bash
.venv/bin/python -m pytest -q
```

## Architecture

```
raw input → canonicalization → deterministic transform → canonical result
                                        ↓
                               execution receipt (stamp)
                                        ↓
                    blob write + fact inscription + tx log append
                                        ↓
                              derived projections
```

Receipts are authoritative. Projections are derived and non-authoritative.

The receipt binds the **complete** canonical result, not a summary. Tampering with any result field invalidates the receipt.

## Key invariants

- **Same inputs → same receipt hash.** Always. Across Python and Rust.
- **Receipts bind full payloads.** Not summaries.
- **Transport fields are excluded from hashing.** Nondeterministic IDs don't leak into stamps.
- **Projections are never authoritative.** If a projection disagrees with a receipt, the receipt wins.
- **Witness polarity is action-aware.** "I stopped the server" is corroborated by absence, not presence.
