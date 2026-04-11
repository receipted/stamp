#!/usr/bin/env python3
"""
Sidecar Watcher — Phase 0.0
Watches configured directories for file changes and captures ore blobs.

Pure Python. No LLM. No network. No dependencies beyond stdlib.

FUTURE: Uplift to Rust for single-binary distribution and WASM compilation.
See ROADMAP.md Phase progression: Python (prove) → Rust (ship) → WASM (chain)
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# --- Configuration ---

WATCH_PATHS = [
    # Claude Code sessions
    os.path.expanduser("~/.claude/projects"),
    # Codex desktop app (OpenAI) session index and state
    os.path.expanduser("~/.codex"),
    # Shadow's thinking-log (lowercase)
    os.path.expanduser("~/projects/thinking-log"),
    # Genesis layer thinking-log (capital T — benjaminfenton account)
    "/Users/benjaminfenton/Thinking-Log",
    # Surface inbox from Codex app
    "/Users/benjaminfenton/.surface/inbox",
    # Shadow (OpenClaw) session transcripts — this conversation
    "/Users/shadow/.openclaw/agents/main/sessions",
]

# Shared ore directory — readable/writable by all accounts on this machine.
# This is the inter-agent bus. Unix does it well.
ORE_DIR = "/Users/Shared/sidecar-ore"

# File types to capture
WATCH_EXTENSIONS = {".jsonl", ".json", ".md", ".txt", ".py"}

# Minimum seconds between captures of the same file
DEBOUNCE_SECONDS = 1

# --- Core functions (pure, no I/O) ---

def compute_hash(data: bytes) -> str:
    """SHA-256 hash of raw bytes. That's it."""
    return hashlib.sha256(data).hexdigest()


def make_ore_blob(
    source: str,
    file_path: str,
    content: bytes,
    captured_at: str,
) -> dict:
    """
    Construct an ore blob. Pure function — takes values, returns dict.
    No I/O, no side effects.
    """
    return {
        "schema": "sidecar.ore.v1",
        "source": source,
        "file_path": file_path,
        "captured_at": captured_at,
        "content_hash": compute_hash(content),
        "content_size": len(content),
        # Content stored separately as .raw file, not embedded in JSON
        # This keeps the ore blob small and the raw content inspectable
    }


# --- I/O layer (thin, inspectable) ---

def detect_source(file_path: str) -> str:
    """Determine which surface produced this file."""
    if "/.claude/" in file_path:
        return "claude-code"
    if "/.codex/" in file_path:
        return "codex"
    if "/.openclaw/agents" in file_path:
        return "shadow-session"
    if "/thinking-log/" in file_path or "/Thinking-Log/" in file_path:
        return "thinking-log"
    if "/.surface/" in file_path:
        return "surface"
    return "unknown"


def write_ore(ore_blob: dict, content: bytes) -> str:
    """
    Write ore blob + raw content to ore directory.
    Returns path to the ore blob JSON.
    """
    os.makedirs(ORE_DIR, exist_ok=True)

    # Filename: timestamp + content hash prefix
    ts = ore_blob["captured_at"].replace(":", "-").replace(".", "-")
    hash_prefix = ore_blob["content_hash"][:12]
    base = f"{ts}_{hash_prefix}"

    blob_path = os.path.join(ORE_DIR, f"{base}.ore.json")
    raw_path = os.path.join(ORE_DIR, f"{base}.raw")

    # Write raw content first (the source of truth)
    with open(raw_path, "wb") as f:
        f.write(content)

    # Write ore blob (metadata envelope)
    with open(blob_path, "w") as f:
        json.dump(ore_blob, f, indent=2, sort_keys=True)

    return blob_path


def poll_watch_paths(
    watch_paths: list[str],
    known_state: dict[str, float],
    debounce: float,
) -> list[tuple[str, float]]:
    """
    Scan watch paths for files modified since last known state.
    Returns list of (file_path, mtime) for changed files.

    This is the polling approach. Simple, portable, no platform dependencies.
    FUTURE: Replace with FSEvents (macOS) / inotify (Linux) in Rust version.
    """
    changed = []
    now = time.time()

    for watch_path in watch_paths:
        try:
            os.listdir(watch_path)
        except (FileNotFoundError, PermissionError):
            continue

        for root, _dirs, files in os.walk(watch_path):
            # Skip hidden dirs (except .claude and .codex themselves)
            basename = os.path.basename(root)
            if basename.startswith(".") and basename not in (".claude", ".codex"):
                continue

            # Skip venv, node_modules, __pycache__, .git
            if basename in (".venv", "venv", "node_modules", "__pycache__", ".git", ".next"):
                continue

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in WATCH_EXTENSIONS:
                    continue

                fpath = os.path.join(root, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                except OSError:
                    continue

                last_seen = known_state.get(fpath, 0)
                if mtime > last_seen and (now - mtime) > debounce:
                    changed.append((fpath, mtime))

    return changed


def run_watcher(poll_interval: float = 5.0):
    """
    Main loop. Polls for changes, captures ore blobs.

    Press Ctrl+C to stop. That's the interface.
    """
    print(f"Sidecar Watcher v0.1.0", flush=True)
    print(f"Ore directory: {ORE_DIR}", flush=True)
    print(f"Watching {len(WATCH_PATHS)} paths:", flush=True)
    for p in WATCH_PATHS:
        try:
            os.listdir(p)
            exists = "✓"
        except (FileNotFoundError, PermissionError):
            exists = "✗ (will watch when created)"
        print(f"  {p} [{exists}]", flush=True)
    print(f"Poll interval: {poll_interval}s", flush=True)
    print(f"Press Ctrl+C to stop.\n", flush=True)

    # Initialize known state with current mtimes (don't capture everything on first run)
    # Exception: session files (large, frequently updated) — always capture on next change
    SESSION_PATHS = ["/Users/shadow/.openclaw/agents/main/sessions"]
    known_state: dict[str, float] = {}
    for fpath, mtime in poll_watch_paths(WATCH_PATHS, {}, 0):
        # Skip session files from initial index so first change gets captured
        if any(sp in fpath for sp in SESSION_PATHS):
            continue
        known_state[fpath] = mtime
    print(f"Indexed {len(known_state)} existing files. Watching for changes...\n", flush=True)

    capture_count = 0

    try:
        while True:
            changed = poll_watch_paths(WATCH_PATHS, known_state, DEBOUNCE_SECONDS)

            for fpath, mtime in changed:
                try:
                    content = Path(fpath).read_bytes()
                except (OSError, PermissionError) as e:
                    print(f"  ⚠ Cannot read {fpath}: {e}")
                    known_state[fpath] = mtime
                    continue

                source = detect_source(fpath)
                captured_at = datetime.now(timezone.utc).isoformat()

                ore_blob = make_ore_blob(
                    source=source,
                    file_path=fpath,
                    content=content,
                    captured_at=captured_at,
                )

                blob_path = write_ore(ore_blob, content)
                known_state[fpath] = mtime
                capture_count += 1

                print(f"  ✓ [{capture_count}] {source}: {os.path.basename(fpath)}", flush=True)
                print(f"    hash: {ore_blob['content_hash'][:16]}...", flush=True)
                print(f"    size: {ore_blob['content_size']} bytes", flush=True)
                print(f"    ore:  {os.path.basename(blob_path)}", flush=True)
                append_to_ledger(blob_path)

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print(f"\nStopped. Captured {capture_count} ore blobs in {ORE_DIR}", flush=True)


def append_to_ledger(ore_blob_path: str):
    """
    Append a newly captured ore blob to the hash chain ledger.
    Imports ledger.py from the same directory.
    """
    import importlib.util
    ledger_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.py")
    if not os.path.exists(ledger_path):
        # Ledger not present — skip silently (watcher works without it)
        return
    spec = importlib.util.spec_from_file_location("ledger", ledger_path)
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
    ledger.cmd_append(ore_blob_path)


if __name__ == "__main__":
    run_watcher()
