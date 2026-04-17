#!/usr/bin/env python3
"""substrate analyze — the product.

Post a codebase, get a receipted governance report.

Usage:
    python substrate_cli.py analyze <path>
    python substrate_cli.py analyze <path> --json
    python substrate_cli.py verify <receipt.json>
    python substrate_cli.py info
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.surface.analyzer import analyze_repo
from src.surface.stamp import stamp, verify_stamp, verify_stamp_chain, stamp_chain_anchor, h, GENESIS, _canonical_json, hash_analysis_payload, verify_receipt_payload
from src.surface.receipted import run_pipeline_with_receipts


_ALLOWED_CLONE_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def _validate_clone_url(url: str) -> str | None:
    """Validate a git clone URL. Returns error string or None if ok."""
    from urllib.parse import urlparse
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


def _clone_repo(url: str) -> Path | None:
    """Clone a GitHub repo to a temp directory. Returns the path or None."""
    import subprocess
    import tempfile

    # Normalize URL
    if url.startswith("github.com"):
        url = "https://" + url
    # Strip trailing slashes and .git
    url = url.rstrip("/")

    # SSRF guard
    err = _validate_clone_url(url)
    if err:
        print(f"  ERROR: {err}", file=sys.stderr)
        return None

    if not url.endswith(".git"):
        url = url + ".git"

    tmp = Path(tempfile.mkdtemp(prefix="substrate-"))
    print(f"  Cloning {url}...")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, str(tmp / "repo")],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"  Clone failed: {result.stderr.strip()}", file=sys.stderr)
            return None
        print(f"  Cloned to {tmp / 'repo'}")
        return tmp / "repo"
    except subprocess.TimeoutExpired:
        print("  Clone timed out (60s)", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("  git not found", file=sys.stderr)
        return None


def cmd_analyze(path: str, output_json: bool = False):
    """Analyze a Python codebase and produce a receipted governance report."""

    # Handle GitHub URLs first
    if path.startswith("http://") or path.startswith("https://") or path.startswith("github.com"):
        target = _clone_repo(path)
        if target is None:
            print(f"ERROR: could not clone {path}", file=sys.stderr)
            sys.exit(1)
    else:
        target = Path(path)
        if not target.exists():
            print(f"ERROR: {path} does not exist", file=sys.stderr)
            sys.exit(1)

    # Discover Python files
    if target.is_file():
        files = {str(target): target.read_text()}
    else:
        files = {}
        for p in sorted(target.rglob("*.py")):
            # Skip hidden dirs, __pycache__, .venv, node_modules
            parts = p.parts
            if any(part.startswith(".") or part in ("__pycache__", ".venv", "node_modules", "venv", "test", "tests", "docs") for part in parts):
                continue
            try:
                files[str(p.relative_to(target))] = p.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

    if not files:
        print(f"ERROR: no Python files found in {path}", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    t0 = time.time()
    result = analyze_repo(files)
    elapsed = time.time() - t0

    # Build receipt chain
    # Input hash: hash of all source files concatenated
    source_concat = "".join(f"{name}:{content}" for name, content in sorted(files.items()))
    input_hash = h(source_concat.encode())

    # Function hash: hash of the analyzer source
    analyzer_path = Path(__file__).parent / "src" / "surface" / "analyzer.py"
    fn_hash = h(analyzer_path.read_bytes())

    # Output hash: hash of the FULL analysis result (not just summary)
    output_hash = hash_analysis_payload(result)

    # Stamp
    analysis_stamp = stamp("analyze", input_hash, fn_hash, output_hash, GENESIS)

    # Find smoking gun for the governance receipt
    violations = result.get("violations", [])
    dangerous = [v for v in violations if v.get("type") in ("dangerous_deserialization", "code_execution", "dangerous_code_enabled", "constraint_violation")]
    smoking_gun = (dangerous or violations[:1] or [None])[0]

    # Build governance receipt (matches may1_demo_receipt_mock shape)
    gov_receipt = None
    if smoking_gun:
        # Determine primary kind and facets
        primary_kind = smoking_gun.get("mother_type", "CONSTRAINT")
        facet_types = set()
        for v in violations:
            mt = v.get("mother_type", "")
            if mt and mt != primary_kind:
                facet_types.add(mt)

        # Find the function data for boundary and dep path
        sg_func_name = smoking_gun.get("function")
        sg_func = None
        if sg_func_name:
            for fname, fdata in result.get("files", {}).items():
                for f in fdata.get("functions", []):
                    if f["name"] == sg_func_name:
                        sg_func = f
                        break

        gov_receipt = {
            "receipt_type": "governance_receipt",
            "status": "red_flag",
            "severity": "critical" if dangerous else "warning",
            "subject": f"{smoking_gun.get('function', 'module')}",
            "file": smoking_gun.get("file", ""),
            "line": smoking_gun.get("line", 0),
            "primary_kind": primary_kind,
            "facets": sorted(facet_types),
            "finding": smoking_gun.get("message", ""),
            "boundary": {
                "apparent_contract": sg_func.get("apparent_contract", "") if sg_func else "",
                "actual_capabilities": sg_func.get("actual_capabilities", []) if sg_func else [],
            },
            "dependency_path": sg_func.get("dependency_path", []) if sg_func else [],
            "source_witness": {
                "type": "source_code",
                "observed_fact": smoking_gun.get("message", ""),
            },
        }

    # Build receipt bundle
    receipt = {
        "schema": "substrate.receipt.v1",
        "governance_receipt": gov_receipt,
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
            "elapsed_s": round(elapsed, 3),
            "files_analyzed": len(files),
            "analyzer_hash": fn_hash,
        },
    }

    if output_json:
        print(json.dumps(receipt, indent=2, default=str))
    else:
        _print_report(result, analysis_stamp, elapsed, path)

    # Save receipt
    receipt_path = f"substrate-receipt-{analysis_stamp.stamp_hash[:12]}.json"
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2, default=str)
    print(f"\nReceipt saved: {receipt_path}")
    print(f"Verify: python substrate_cli.py verify {receipt_path}")

    # Generate HTML report
    from src.surface.report import render_html_report
    html = render_html_report(
        result,
        receipt["stamp"],
        target=path,
        metadata=receipt["metadata"],
    )
    html_path = f"substrate-report-{analysis_stamp.stamp_hash[:12]}.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"Report saved: {html_path}")


def _print_report(result: dict, stmp, elapsed: float, path: str):
    """Print a human-readable governance report."""
    s = result["summary"]

    print()
    print(f"  SUBSTRATE GOVERNANCE REPORT")
    print(f"  {'='*50}")
    print(f"  Target:     {path}")
    print(f"  Files:      {s['total_files']}")
    print(f"  Functions:  {s['total_functions']}")
    print(f"  Pure:       {s['pure_count']}  |  Impure: {s['impure_count']}")
    print(f"  Types:      {s['type_counts']}")
    print(f"  Elapsed:    {elapsed:.2f}s")
    print()

    violations = result["violations"]
    if violations:
        # Find the worst violation (smoking gun)
        dangerous = [v for v in violations if v.get("type") in ("dangerous_deserialization", "code_execution")]
        constraint_violations = [v for v in violations if v.get("type") == "constraint_violation"]
        smoking_gun = (dangerous or constraint_violations or violations)[0]

        print(f"  VIOLATIONS ({len(violations)})")
        print(f"  {'-'*50}")

        # Smoking gun first
        print(f"  🔴 SMOKING GUN")
        print(f"     {smoking_gun.get('function', smoking_gun.get('file', '?'))}:{smoking_gun.get('line', '?')}")
        print(f"     {smoking_gun['message']}")
        print()

        # Rest
        for v in violations:
            if v is smoking_gun:
                continue
            fn = v.get("function") or "module"
            marker = "🔴" if v.get("type") in ("dangerous_deserialization", "code_execution", "constraint_violation") else "🟡"
            print(f"  {marker} [{v['mother_type']}] {fn}:{v.get('line', '?')}")
            print(f"     {v['message']}")
            print()
    else:
        print("  ✅ No violations found.")
        print()

    # Dependencies
    external = s.get("external_deps", [])
    if external:
        print(f"  UNSTAMPED DEPENDENCIES ({len(external)})")
        print(f"  {'-'*50}")
        for dep in external:
            print(f"  ⚠️  {dep} — no provenance receipt")
        print()

    # Stamp
    print(f"  RECEIPT")
    print(f"  {'-'*50}")
    print(f"  stamp_hash:  {stmp.stamp_hash}")
    print(f"  input_hash:  {stmp.input_hash}")
    print(f"  fn_hash:     {stmp.fn_hash}")
    print(f"  output_hash: {stmp.output_hash}")

    # Governance receipt (folded stage version)
    smoking_gun = None
    if violations:
        dangerous_v = [v for v in violations if v.get("type") in ("dangerous_deserialization", "code_execution", "dangerous_code_enabled")]
        constraint_v = [v for v in violations if v.get("type") == "constraint_violation"]
        smoking_gun = (dangerous_v or constraint_v or violations)[0]
    if smoking_gun:
        gov = result.get("_gov_receipt")
        if not gov:
            # Build it inline
            primary = smoking_gun.get("mother_type", "CONSTRAINT")
            facets = set()
            for v in violations:
                mt = v.get("mother_type", "")
                if mt and mt != primary:
                    facets.add(mt)
            facet_str = " ⊗ ".join([primary] + sorted(facets))
            print()
            print(f"  GOVERNANCE RECEIPT")
            print(f"  {'-'*50}")
            print(f"  Status:  CRITICAL RED FLAG")
            print(f"  Subject: {smoking_gun.get('function', 'module')}")
            print(f"  Kind:    {facet_str}")
            print(f"  Finding: {smoking_gun['message']}")


def cmd_verify(receipt_path: str):
    """Verify a receipt bundle.

    Two checks:
    1. Stamp self-hash: is the stamp internally consistent?
    2. Payload binding: does the stamp's output_hash match the analysis?

    Both must pass. Without #2, a tampered receipt (e.g. violations=[])
    would verify as long as the stamp fields weren't touched.
    """
    with open(receipt_path) as f:
        receipt = json.load(f)

    stmp_data = receipt.get("stamp", {})
    from src.surface.stamp import Stamp
    stmp = Stamp(**stmp_data)

    # Check 1: stamp self-hash
    if not verify_stamp(stmp):
        print(f"FAIL: receipt stamp invalid (self-hash mismatch)")
        sys.exit(1)

    # Check 2: payload binding — does output_hash cover the analysis?
    schema = receipt.get("schema", "")
    if schema == "substrate.receipt.v0":
        print(f"WARNING: v0 receipt — output_hash covers summary only (upgrade to v1)")
    else:
        ok, msg = verify_receipt_payload(receipt)
        if not ok:
            print(f"FAIL: {msg}")
            sys.exit(1)

    print(f"PASS: receipt verified")
    print(f"  stamp_hash:  {stmp.stamp_hash}")
    print(f"  domain:      {stmp.domain}")
    print(f"  fn_hash:     {stmp.fn_hash[:32]}...")
    violations = receipt.get("analysis", {}).get("violations", [])
    print(f"  violations:  {len(violations)}")


def cmd_info():
    """Show tool info."""
    analyzer_path = Path(__file__).parent / "src" / "surface" / "analyzer.py"
    fn_hash = h(analyzer_path.read_bytes()) if analyzer_path.exists() else "?"
    print(f"substrate v0.1.0")
    print(f"  analyzer hash: {fn_hash[:32]}...")
    print(f"  stamp schema:  substrate.stamp.v1")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  substrate_cli.py analyze <path>        Analyze a codebase")
        print("  substrate_cli.py analyze <path> --json  Output as JSON")
        print("  substrate_cli.py verify <receipt.json>  Verify a receipt")
        print("  substrate_cli.py info                   Show tool info")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "analyze" and len(sys.argv) >= 3:
        output_json = "--json" in sys.argv
        cmd_analyze(sys.argv[2], output_json)
    elif cmd == "verify" and len(sys.argv) >= 3:
        cmd_verify(sys.argv[2])
    elif cmd == "info":
        cmd_info()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
