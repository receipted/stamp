#!/usr/bin/env python3
"""
bridge.py — SSE server that feeds real sieve output into the cockpit.

Watches /Users/Shared/sidecar-ore/ for new ore blobs and turn chain updates.
Runs the sieve on incoming turns. Pushes nuggets to the cockpit via SSE.

Serves:
  GET /stream  — SSE endpoint (cockpit connects here)
  GET /         — redirects to cockpit.html

Usage:
  python3 bridge.py                    # start on port 7788
  python3 bridge.py --port 8080        # custom port

Pure functions from the substrate do the work.
This file is IO only — the thinnest possible glue.
"""

import hashlib
import json
import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = 7788
ORE_DIR = "/Users/Shared/sidecar-ore"
COCKPIT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cockpit.html")
THINKING_LOG = "/Users/shadow/projects/thinking-log"

# SSE clients
clients = []
clients_lock = threading.Lock()

# Track what we've already processed
processed_ores = set()


def setup_sieve():
    """Load sieve and supporting modules. IO — runs once at startup."""
    import glob
    sys.path.insert(0, THINKING_LOG)
    for sp in glob.glob(os.path.join(THINKING_LOG, ".venv/lib/python3*/site-packages")):
        if sp not in sys.path:
            sys.path.insert(0, sp)
    from src.surface.sieve import promote
    return promote


def extract_turns_from_session(session_path):
    """Extract turns from an OpenClaw JSONL session file."""
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
            if obj.get("type") == "model_change":
                current_model = obj.get("modelId", current_model)
                continue
            if obj.get("type") == "custom" and obj.get("customType") == "model-snapshot":
                current_model = obj.get("data", {}).get("modelId", current_model)
                continue
            if obj.get("type") != "message":
                continue
            msg = obj.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue
            content = msg.get("content", "")
            if isinstance(content, list):
                parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                content = " ".join(parts)
            content = str(content).strip()
            if len(content) < 10:
                continue
            turns.append({
                "type": "turn",
                "id": obj.get("id", f"t-{len(turns)}"),
                "text": content[:2000],
                "actor": current_model if role == "assistant" else "human:ben",
                "stream": "shadow-session" if "shadow" in session_path else "claude-code",
                "timestamp": obj.get("timestamp", ""),
            })
    return turns


def sieve_turns(turns, promote_fn):
    """Run sieve over turns and produce claims + nuggets."""
    claims_input = []
    for t in turns[-20:]:  # Last 20 turns for performance
        text = t.get("text", "")
        if len(text) < 20:
            continue
        actor = t.get("actor", "")
        ctype = "observation" if "claude" in actor.lower() or "sonnet" in actor.lower() or "opus" in actor.lower() else "claim"
        claims_input.append({
            "id": t["id"],
            "text": text[:500],
            "claim_type": ctype,
            "evidence_refs": [t.get("stream", "")],
            "confidence": 0.8,
            "source": actor,
            "turn_id": t["id"],
            "stream": t.get("stream", ""),
        })

    if not claims_input:
        return []

    topic = {
        "handle": "cockpit-live",
        "title": "Live cockpit feed",
        "description": "Real-time sieve over incoming turns",
        "provenance_mode": "open",
        "keywords": ["substrate", "sieve", "pure", "function", "type", "claim",
                     "receipt", "hash", "chain", "turn", "promote", "contract",
                     "constraint", "kernel", "graph", "relevance"],
    }

    promoted, contested, deferred, loss = promote_fn(claims_input, topic)

    events = []
    for c in promoted:
        events.append({
            "type": "claim",
            "id": c.get("id", ""),
            "text": c.get("text", ""),
            "claim_type": c.get("claim_type", "observation"),
            "confidence": c.get("confidence", 0.8),
            "source": c.get("source", ""),
            "stream": c.get("stream", ""),
            "turn_id": c.get("turn_id", ""),
            "timestamp": c.get("timestamp", ""),
        })
    return events


def broadcast(event_data):
    """Push an event to all connected SSE clients."""
    msg = f"data: {json.dumps(event_data)}\n\n"
    with clients_lock:
        dead = []
        for wfile in clients:
            try:
                wfile.write(msg.encode())
                wfile.flush()
            except Exception:
                dead.append(wfile)
        for d in dead:
            clients.remove(d)


def watcher_loop(promote_fn):
    """Watch ore directory for new session files and process them."""
    known_mtimes = {}

    while True:
        try:
            # Scan for session JSONL files
            for root, dirs, files in os.walk(ORE_DIR):
                for fname in files:
                    if not fname.endswith(".jsonl"):
                        continue
                    fpath = os.path.join(root, fname)
                    mtime = os.path.getmtime(fpath)
                    if known_mtimes.get(fpath) == mtime:
                        continue
                    known_mtimes[fpath] = mtime

                    # Process new/updated session file
                    try:
                        turns = extract_turns_from_session(fpath)
                        if not turns:
                            continue

                        # Broadcast raw turns
                        for t in turns[-5:]:  # Last 5 new turns
                            broadcast(t)

                        # Sieve and broadcast claims
                        claim_events = sieve_turns(turns, promote_fn)
                        for ce in claim_events:
                            broadcast(ce)

                    except Exception as e:
                        print(f"  Error processing {fname}: {e}")

            # Also check shadow session files directly
            shadow_sessions = Path("/Users/shadow/.openclaw/agents/main/sessions")
            if shadow_sessions.exists():
                for f in shadow_sessions.glob("*.jsonl"):
                    fpath = str(f)
                    mtime = os.path.getmtime(fpath)
                    if known_mtimes.get(fpath) == mtime:
                        continue
                    known_mtimes[fpath] = mtime
                    try:
                        turns = extract_turns_from_session(fpath)
                        for t in turns[-3:]:
                            broadcast(t)
                        claims = sieve_turns(turns, promote_fn)
                        for c in claims:
                            broadcast(c)
                    except Exception as e:
                        print(f"  Error processing shadow session: {e}")

        except Exception as e:
            print(f"Watcher error: {e}")

        time.sleep(5)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with clients_lock:
                clients.append(self.wfile)

            # Keep connection open
            try:
                while True:
                    time.sleep(1)
            except Exception:
                pass
            finally:
                with clients_lock:
                    if self.wfile in clients:
                        clients.remove(self.wfile)

        elif self.path == "/" or self.path == "/cockpit":
            # Serve cockpit.html
            cockpit = Path(COCKPIT_PATH)
            if not cockpit.exists():
                # Try shared location
                cockpit = Path(os.path.join(ORE_DIR, "cockpit.html"))
            if cockpit.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(cockpit.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"cockpit.html not found")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Quiet logging
        pass


def main():
    port = PORT
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    print(f"Bridge starting on http://localhost:{port}")
    print(f"  Cockpit:  http://localhost:{port}/")
    print(f"  SSE:      http://localhost:{port}/stream")
    print(f"  Ore dir:  {ORE_DIR}")

    # Load sieve
    print("  Loading sieve...", end=" ", flush=True)
    promote_fn = setup_sieve()
    print("ok")

    # Start watcher in background
    watcher = threading.Thread(target=watcher_loop, args=(promote_fn,), daemon=True)
    watcher.start()
    print("  Watcher started")

    # Start HTTP server
    server = HTTPServer(("localhost", port), Handler)
    print(f"  Listening on port {port}")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBridge stopped.")


if __name__ == "__main__":
    main()
