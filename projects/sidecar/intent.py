#!/usr/bin/env python3
"""
intent.py — Code Intent Extractor
Feed a Python file in. Get a human-readable intent map out.

Usage:
  python3 intent.py <file.py>
  python3 intent.py <file.py> [function_name]

Output:
  Intent map to stdout + receipt to /Users/Shared/sidecar-ore/spines/

Pure function pipeline:
  parse_function_to_claims() [kernel.py] — pure, no IO
    → promote() [sieve.py] — pure, no IO  
      → receipt [harness] — hash-linked, verifiable

FUTURE: Uplift to Rust. Single binary. WASM-compilable.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

THINKING_LOG = "/Users/shadow/projects/thinking-log"
SPINES_DIR = "/Users/Shared/sidecar-ore/spines"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(source_path: str, fn_filter=None):
    # --- Validate input ---
    if not os.path.exists(source_path):
        print(f"ERROR: file not found: {source_path}")
        sys.exit(1)

    if not source_path.endswith(".py"):
        print(f"ERROR: only Python (.py) files are supported, got: {source_path}")
        sys.exit(1)

    if os.path.getsize(source_path) == 0:
        print(f"ERROR: empty file: {source_path}")
        sys.exit(1)

    # --- Read source ---
    try:
        raw = Path(source_path).read_bytes()
        source = raw.decode("utf-8", errors="replace")
    except (OSError, PermissionError) as e:
        print(f"ERROR: cannot read file: {e}")
        sys.exit(1)
    input_hash = h(raw)

    # --- Hash the pure functions we're using ---
    kernel_path = os.path.join(THINKING_LOG, "src/surface/kernel.py")
    sieve_path = os.path.join(THINKING_LOG, "src/surface/sieve.py")
    kernel_hash = h(Path(kernel_path).read_bytes())
    sieve_hash = h(Path(sieve_path).read_bytes())

    print(f"Intent map: {os.path.basename(source_path)}")
    print(f"  input_hash:  {input_hash[:16]}...")
    print(f"  kernel_hash: {kernel_hash[:16]}...")
    print(f"  sieve_hash:  {sieve_hash[:16]}...")

    # --- Load venv ---
    import glob
    for sp in glob.glob(os.path.join(THINKING_LOG, ".venv/lib/python3*/site-packages")):
        if sp not in sys.path:
            sys.path.insert(0, sp)
    sys.path.insert(0, THINKING_LOG)

    # --- Pure function pipeline ---
    from src.surface.kernel import parse_function_to_claims, parse_function_to_graph
    from src.surface.sieve import promote
    sys.path.insert(0, os.path.join(THINKING_LOG, "graph-lab"))
    from relevance import score_all

    # Load infer_edges_fn here (IO layer) and inject into pure kernel function
    infer_edges_fn = None
    type_lab_path = os.path.join(THINKING_LOG, "type-lab")
    if os.path.exists(os.path.join(type_lab_path, "infer.py")):
        if type_lab_path not in sys.path:
            sys.path.insert(0, type_lab_path)
        try:
            import importlib
            infer_mod = importlib.import_module("infer")
            infer_edges_fn = infer_mod.infer_edges
        except ImportError:
            pass

    claims, edges = parse_function_to_graph(source, infer_edges_fn=infer_edges_fn)

    # Score all claims by graph connectivity
    graph = {"nodes": [{"id": c["id"]} for c in claims], "edges": edges}
    seed_ids = {c["id"] for c in claims if c.get("claim_type") == "constraint"}
    if not seed_ids:
        seed_ids = {c["id"] for c in claims[:3]}  # fallback
    bfs_scores = score_all(graph, seed_ids, max_hops=3)

    # Inject scores — high-connectivity claims get evidence_refs boost
    for c in claims:
        score = bfs_scores.get(c["id"], 0.0)
        c["graph_relevance"] = score
        if score > 0.1:
            c["evidence_refs"] = ["ast", "graph"]
        # guarantee claims always get evidence_refs — purity is always relevant
        if c.get("claim_type") == "guarantee":
            c["evidence_refs"] = ["ast", "guarantee"]
            c["graph_relevance"] = max(score, 0.5)  # guaranteed to surface

    # Filter to specific function if requested
    if fn_filter:
        claims = [c for c in claims if c.get("fn_name") == fn_filter]
        print(f"  filtered to: {fn_filter} ({len(claims)} claims)")
    else:
        print(f"  claims extracted: {len(claims)} from {len(set(c.get('fn_name','') for c in claims))} functions")

    if not claims:
        print("ERROR: no claims extracted")
        sys.exit(1)

    topic_context = {
        "handle": "code-intent",
        "title": "Code intent extraction",
        "description": "Extract structural intent from Python source code",
        "keywords": [
            "pure", "function", "constraint", "contract", "intent",
            "return", "raises", "io", "deterministic", "pure function",
            "no io", "optional", "none", "assert", "invariant",
            "classify", "role", "text", "str", "appears", "contains",
            "operations", "exception", "conditions", "heuristic",
        ],
    }

    # Load epistemic classifier here (IO layer) and inject into pure promote()
    _epistemic_fn = None
    try:
        from src.surface.epistemic_tagger import classify_turn as _et
        _epistemic_fn = _et
    except ImportError:
        pass

    promoted, contested, deferred, loss = promote(claims, topic_context,
                                                   epistemic_classify_fn=_epistemic_fn)

    # --- Build output ---
    spine = {
        "schema": "sidecar.intent.v1",
        "source_file": source_path,
        "fn_filter": fn_filter,
        "promoted": promoted,
        "contested": contested,
        "deferred": deferred,
        "declared_loss": loss,
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }

    output_bytes = json.dumps(spine, sort_keys=True, default=str).encode()
    output_hash = h(output_bytes)

    receipt = {
        "schema": "sidecar.receipt.v1",
        "input_hash": input_hash,
        "kernel_hash": kernel_hash,
        "sieve_hash": sieve_hash,
        "harness_hash": h(Path(__file__).read_bytes()),
        "output_hash": output_hash,
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }

    # --- Print human-readable intent map ---
    print()
    print("=" * 60)
    print("INTENT MAP")
    print("=" * 60)

    # Group by function
    by_fn: dict[str, list[dict]] = {}
    for c in promoted:
        fn = c.get("fn_name", "unknown")
        by_fn.setdefault(fn, []).append(c)

    # Purity signals from ALL claims (bypass sieve — purity is metadata not a claim)
    purity_by_fn: dict[str, str] = {}
    for c in claims:
        fn = c.get("fn_name", "")
        text = c.get("text", "")
        if "IMPURE" in text:
            purity_by_fn[fn] = "\u26a0\ufe0f  impure — contains IO or side effects"
        elif "pure" in text.lower() and fn not in purity_by_fn:
            purity_by_fn[fn] = "\u2713  pure"

    for fn, fn_claims in by_fn.items():
        print(f"\n{fn}()")
        if fn in purity_by_fn:
            print(f"  purity:     {purity_by_fn[fn]}")
        for c in fn_claims:
            text = c["text"]
            if "IMPURE" in text or ("pure" in text.lower() and "impure" not in text.lower()):
                continue  # already shown as purity signal
            prefix = {
                "fact": "  contract:   ",
                "observation": "  note:       ",
                "constraint": "  constraint: ",
                "hypothesis": "  uncertain:  ",
                "guarantee": "  guarantee:  ",
            }.get(c["claim_type"], "  \u2192  ")
            text = text.replace(f"{fn}: ", "").replace(f"{fn}", "").strip()
            print(f"{prefix}{text}")

    print()
    print(f"promoted: {len(promoted)} | contested: {len(contested)} | loss: {len(loss)}")
    print(f"output_hash: {output_hash[:16]}...")

    # --- Write receipt ---
    os.makedirs(SPINES_DIR, exist_ok=True)
    base = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}_{output_hash[:12]}"
    receipt_path = os.path.join(SPINES_DIR, f"{base}.intent-receipt.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print(f"receipt:     {os.path.basename(receipt_path)}")
    print()
    print("VERIFY:")
    print(f"  shasum -a 256 {kernel_path}")
    print(f"  → should match kernel_hash in receipt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 intent.py <file.py> [function_name]")
        sys.exit(1)

    source_path = sys.argv[1]
    fn_filter = sys.argv[2] if len(sys.argv) > 2 else None
    run(source_path, fn_filter)
