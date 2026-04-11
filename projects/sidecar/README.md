# Sidecar

A file watcher that captures ore blobs from your AI development surfaces.

## What it does

Watches `~/.claude/projects/`, `~/.codex/sessions/`, and `~/projects/thinking-log/` for file changes. When a file changes, it captures the content as an immutable ore blob with a SHA-256 hash.

## Usage

```bash
# Start watching
python watcher.py

# Verify any ore blob independently
python verify.py ore/2026-04-08T21-40-00Z_abc123def456.ore.json

# Verify the hash yourself (no trust required)
shasum -a 256 ore/2026-04-08T21-40-00Z_abc123def456.raw
```

## Ore format

Each capture produces two files:
- `*.ore.json` — metadata envelope (source, timestamp, hash, size)
- `*.raw` — the actual content, byte-for-byte

The hash in the ore blob is SHA-256 of the raw file. Verify it yourself with `shasum -a 256`.

## Trust model

- **watcher.py** — captures files. Read the source. It's ~160 lines.
- **verify.py** — checks hashes. Read the source. It's ~20 lines of logic.
- Pin both with `shasum -a 256 watcher.py verify.py` and check before each run.
- You run it. Not an AI. You see the output directly.

## Dependencies

Python 3.11+. Standard library only. No pip install. No network.

## Future

This is the Python proof-of-concept. The production path:
1. **Python** (now) — prove the pattern works
2. **Rust** — single static binary, FSEvents/inotify native, no interpreter trust
3. **WASM** — same binary runs on-chain as a smart contract for receipt anchoring

See `ROADMAP.md` in the parent project for the full progression.
