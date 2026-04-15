# Stamp

**Receipted governance for code.**

Post a codebase, get a signed governance report.
Every function typed. Pure/impure boundaries classified.
Dependency provenance gaps identified. Every finding receipted and independently verifiable.

## Try it

```bash
# Analyze a GitHub repo
curl -X POST https://substrate-api.fly.dev/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/your/repo"}'

# Analyze a single file
curl -X POST https://substrate-api.fly.dev/analyze \
  -H "Content-Type: application/json" \
  -d '{"source": "import pickle\ndef load(p):\n    return pickle.loads(open(p,\"rb\").read())", "filename": "app.py"}'
```

## What you get

A receipted governance report containing:

- **Function typing** — every function classified as CONTRACT, CONSTRAINT, UNCERTAINTY, RELATION, or WITNESS
- **Purity analysis** — pure vs impure boundaries, with specific impurity signals (I/O, env vars, dangerous deserialization, network calls)
- **Dangerous pattern detection** — `pickle.loads`, `eval`, `allow_dangerous_code=True`, and other semantic red flags
- **Dependency provenance** — which dependencies are in-repo (stamped) vs external (unstamped)
- **Smoking gun** — the single worst violation, highlighted
- **Cryptographic receipt** — stamp proving what input was analyzed, which version of the analyzer ran, and what output was produced

## Why it matters

Standard tools check syntax. Stamp checks governance.

A function can pass linting, pass tests, pass code review — and still have the wrong trust boundary. Stamp finds the semantic failures that look correct but aren't:

- A "CSV helper" that secretly enables code execution ([CVE-2026-27966](https://nvd.nist.gov/vuln/detail/CVE-2026-27966))
- A JWT verifier that lets the token choose its own verification algorithm ([CVE-2026-22817](https://nvd.nist.gov/vuln/detail/CVE-2026-22817))
- A "safe" extractor that doesn't validate where writes actually land ([GHSA-m6w7-qv66-g3mf](https://github.com/bentoml/BentoML/security/advisories/GHSA-m6w7-qv66-g3mf))
- A login validator that checks claims but never verifies the signature ([CVE-2026-31946](https://nvd.nist.gov/vuln/detail/CVE-2026-31946))

Every finding is receipted. Every receipt is independently verifiable.

## How it works

```
source code
    → AST extraction (functions, imports, call graph)
        → mother type classification (CONTRACT/CONSTRAINT/UNCERTAINTY/RELATION/WITNESS)
            → purity analysis (I/O signals, dangerous patterns, env var reads)
                → dependency provenance (stamped vs unstamped)
                    → stamp(input_hash, fn_hash, output_hash, prev_stamp_hash)
                        → receipt
```

Every step in the pipeline is a deterministic transform. The receipt proves the entire chain ran faithfully.

## Run locally

```bash
# Clone
git clone https://github.com/receipted/stamp.git
cd stamp

# Install
python3 -m venv .venv && .venv/bin/pip install pydantic

# Analyze
.venv/bin/python3 stamp_cli.py analyze /path/to/your/code

# Verify a receipt
.venv/bin/python3 stamp_cli.py verify substrate-receipt-*.json
```

## The stamp primitive

```
stamp(input_hash, fn_hash, output_hash, prev_stamp_hash) → receipt
```

- **input_hash** — what went in
- **fn_hash** — which function ran (hash of the actual source)
- **output_hash** — what came out
- **prev_stamp_hash** — what it chained from

Same inputs → same receipt, always. Rust and Python implementations produce byte-identical output. 29 Rust tests + 21 Python parity tests enforce this.

## Concepts

| Term | What it means |
|---|---|
| **stamp** | mint a receipt for one transform |
| **receipt** | the portable proof artifact |
| **turn** | an attributed, sequenced, receipted coordination move |
| **chain** | ordered history of receipts |
| **verify** | check receipt integrity and lineage |
| **mother type** | one of five governance facets: CONTRACT, CONSTRAINT, UNCERTAINTY, RELATION, WITNESS |

## Five governance types

| Type | What it catches |
|---|---|
| **CONTRACT** | what a function promises to do |
| **CONSTRAINT** | what must not happen (violated trust boundaries) |
| **UNCERTAINTY** | what is unknown or unverified |
| **RELATION** | how components depend on each other |
| **WITNESS** | provenance — who observed what, when, with what authority |

## Rust binary

```bash
cd rust
cargo build --release

# Stamp, verify, chain
./target/release/substrate stamp mint turn <input> <fn> <output>
./target/release/substrate verify <ore_blob.json>
./target/release/substrate turn-chain verify <chain.jsonl>
./target/release/substrate ledger verify
./target/release/substrate info
```

573KB binary. No runtime dependencies.

## Project structure

```
rust/src/
  stamp.rs     — the generic stamp primitive (pure, ZK-circuit-ready)
  core.rs      — hash functions, chain building, Merkle trees
  io.rs        — file I/O, session parsing
  main.rs      — CLI

src/surface/
  stamp.py     — Python stamp (byte-identical to Rust)
  analyzer.py  — AST-based code analysis engine
  mother_types.py — five governance types + TypedUnit v0
  report.py    — HTML report generator

examples/
  langflow-csv-agent/   — CVE-2026-27966 (AI code execution)
  hono-jwt/             — CVE-2026-22817 (JWT algorithm confusion)
  openolat-oidc/        — CVE-2026-31946 (missing signature verification)
  bentoml-tarfile/      — GHSA-m6w7-qv66-g3mf (path traversal)
  ml-service/           — reconstructed AI-generated inference service
```

## Status

**Live.** API deployed at `substrate-api.fly.dev`. CLI and Rust binary working. Five real CVEs analyzed and receipted.

Current focus: demo — one canonical example (Langflow CSV Agent), one receipt, one verify.

## What this repo is not

This repo is the engine and verification tools. It is not:
- A dashboard or UI
- A policy engine (the governance sieve is not in this repo)
- An on-chain verifier (planned, not built)
- A replacement for SAST/linting (it finds what those tools miss)

## License

TBD

---

*We review AI's code with a hashchained ratification engine.*

**[receipted](https://github.com/receipted)** · [turnchain](https://github.com/turnchain)
