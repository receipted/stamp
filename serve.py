#!/usr/bin/env python3
"""substrate serve — the product endpoint.

POST /analyze with source files, get a receipted governance report back.
GET /health for status.

Usage:
    python serve.py                    # port 7799
    python serve.py --port 8080
"""

import json
import os
import sys
import tempfile
import time
import zipfile
import io
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent))

from src.surface.analyzer import analyze_repo
from src.surface.stamp import stamp, h, GENESIS, hash_analysis_payload

PORT = int(os.environ.get("SUBSTRATE_PORT", "7799"))

# --- Clone URL validation (SSRF guard) ---

_ALLOWED_CLONE_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def _validate_clone_url(url: str) -> str | None:
    """Validate a git clone URL. Returns error string or None if ok."""
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        return f"only HTTPS URLs allowed (got {parsed.scheme!r})"
    if parsed.hostname not in _ALLOWED_CLONE_HOSTS:
        return f"host {parsed.hostname!r} not in allowlist: {sorted(_ALLOWED_CLONE_HOSTS)}"
    if parsed.port is not None:
        return "custom ports not allowed"
    if ".." in parsed.path:
        return "path traversal not allowed"
    return None
MAX_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES = 1000
ANALYSIS_TIMEOUT = 60

# Rate limiting
_request_times: dict[str, list[float]] = {}
RATE_LIMIT = 10  # per minute per IP


def _rate_ok(ip: str) -> bool:
    now = time.time()
    times = _request_times.get(ip, [])
    times = [t for t in times if now - t < 60]
    _request_times[ip] = times
    if len(times) >= RATE_LIMIT:
        return False
    times.append(now)
    return True


def _build_receipt(files: dict[str, str], result: dict) -> dict:
    """Build a receipt bundle from analysis results."""
    t0 = time.time()

    source_concat = "".join(f"{name}:{content}" for name, content in sorted(files.items()))
    input_hash = h(source_concat.encode())

    analyzer_path = Path(__file__).parent / "src" / "surface" / "analyzer.py"
    fn_hash = h(analyzer_path.read_bytes()) if analyzer_path.exists() else h(b"unknown")

    output_hash = hash_analysis_payload(result)

    analysis_stamp = stamp("analyze", input_hash, fn_hash, output_hash, GENESIS)

    return {
        "schema": "substrate.receipt.v1",
        "analysis": result,
        "stamp": {
            "schema": analysis_stamp.schema,
            "domain": analysis_stamp.domain,
            "input_hash": analysis_stamp.input_hash,
            "fn_hash": analysis_stamp.fn_hash,
            "output_hash": analysis_stamp.output_hash,
            "prev_stamp_hash": analysis_stamp.prev_stamp_hash,
            "stamp_hash": analysis_stamp.stamp_hash,
        },
        "metadata": {
            "tool": "substrate",
            "version": "0.1.0",
            "analyzer_hash": fn_hash,
        },
    }


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path == "/analyze" or self.path.startswith("/analyze?"):
            self._handle_analyze()
        else:
            self._json_response(404, {"error": "not found"})

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok", "version": "0.1.0"})
        elif self.path == "/" or self.path == "/analyze":
            self._json_response(200, {
                "service": "substrate",
                "version": "0.1.0",
                "usage": "POST /analyze with JSON body: {\"files\": {\"filename.py\": \"source code...\"}}",
            })
        else:
            self._json_response(404, {"error": "not found"})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _handle_analyze(self):
        # Rate limit
        ip = self.client_address[0]
        if not _rate_ok(ip):
            self._json_response(429, {"error": "rate limited, try again in a minute"})
            return

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._json_response(400, {"error": "empty body"})
            return
        if content_length > MAX_SIZE:
            self._json_response(413, {"error": f"payload too large (max {MAX_SIZE // 1024 // 1024}MB)"})
            return

        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid JSON"})
            return

        # Extract files
        files = {}
        if "url" in payload:
            # GitHub URL: {"url": "https://github.com/org/repo"}
            import subprocess, tempfile
            url = payload["url"].rstrip("/")
            # SSRF guard: validate before clone
            err = _validate_clone_url(url)
            if err:
                self._json_response(400, {"error": f"invalid URL: {err}"})
                return
            if not url.endswith(".git"):
                url += ".git"
            tmp = tempfile.mkdtemp(prefix="substrate-")
            try:
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", "--single-branch", url, tmp + "/repo"],
                    capture_output=True, text=True, timeout=60,
                )
                if result.returncode != 0:
                    self._json_response(400, {"error": f"clone failed: {result.stderr.strip()[:200]}"})
                    return
                repo_path = Path(tmp) / "repo"
                for p in sorted(repo_path.rglob("*.py")):
                    parts = p.parts
                    if any(part.startswith(".") or part in ("__pycache__", ".venv", "venv", "node_modules", "test", "tests") for part in parts):
                        continue
                    try:
                        files[str(p.relative_to(repo_path))] = p.read_text()
                    except (UnicodeDecodeError, PermissionError):
                        continue
            except subprocess.TimeoutExpired:
                self._json_response(504, {"error": "clone timed out"})
                return
        elif "files" in payload:
            # Direct file submission: {"files": {"app.py": "source..."}}
            files = payload["files"]
        elif "source" in payload:
            # Single file: {"source": "code...", "filename": "app.py"}
            filename = payload.get("filename", "source.py")
            files = {filename: payload["source"]}
        else:
            self._json_response(400, {"error": "must provide 'url', 'files' dict, or 'source' string"})
            return

        if len(files) > MAX_FILES:
            self._json_response(413, {"error": f"too many files (max {MAX_FILES})"})
            return

        # Filter to Python files
        py_files = {k: v for k, v in files.items() if k.endswith(".py")}
        if not py_files:
            self._json_response(400, {"error": "no Python files found"})
            return

        # Analyze
        try:
            result = analyze_repo(py_files)
        except Exception as e:
            self._json_response(500, {"error": f"analysis failed: {str(e)}"})
            return

        # Build receipt
        receipt = _build_receipt(py_files, result)

        self._json_response(200, receipt)

        # Log
        s = result["summary"]
        print(f"  POST /analyze: {s['total_files']} files, {s['total_functions']} functions, {s['violation_count']} violations")

    def _json_response(self, status: int, data: dict):
        body = json.dumps(data, indent=2, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        pass  # Quiet logging


def main():
    port = PORT
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    print(f"Substrate serving on http://localhost:{port}")
    print(f"  POST /analyze  — analyze a codebase")
    print(f"  GET  /health   — health check")
    print(f"  Rate limit: {RATE_LIMIT}/min per IP")
    print(f"  Max payload: {MAX_SIZE // 1024 // 1024}MB")
    print()

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
