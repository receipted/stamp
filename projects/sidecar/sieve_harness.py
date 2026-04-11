#!/usr/bin/env python3
"""
Sieve Harness — Phase 1.1
Runs sieve.promote() against a real ore blob and produces a receipted spine.

Usage:
  python3 sieve_harness.py <ore_blob.raw> [topic]

Output:
  spine.v1 JSON with receipt to /Users/Shared/sidecar-ore/spines/

FUTURE: Uplift to Rust kernel.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

THINKING_LOG = "/Users/shadow/projects/thinking-log"
VENV_SITE = os.path.join(THINKING_LOG, ".venv/lib")
SPINES_DIR = "/Users/Shared/sidecar-ore/spines"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_claims_from_claude_session(raw_bytes: bytes) -> list[dict]:
    """
    Extract user/assistant message turns from a Claude Code JSONL session.
    Returns a list of claim-like dicts that promote() can work with.
    """
    claims = []
    lines = raw_bytes.decode("utf-8", errors="replace").split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = obj.get("type")

        # Extract user and assistant message turns
        if msg_type in ("user", "assistant"):
            msg = obj.get("message", {})
            role = msg.get("role", msg_type)
            content = msg.get("content", "")

            # Content can be string or list of blocks
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                content = " ".join(text_parts)

            if content and isinstance(content, str) and len(content.strip()) > 20:
                claims.append({
                    "id": obj.get("uuid", f"claim_{len(claims)}"),
                    "text": content.strip()[:2000],  # sieve expects 'text' field
                    "claim_type": "observation" if role == "assistant" else "claim",
                    "role": role,
                    "timestamp": obj.get("timestamp", ""),
                    "source": "claude-code-session",
                })

    return claims


def run(ore_raw_path: str, topic: str = "substrate-development"):
    # --- Read and hash the input ---
    raw = Path(ore_raw_path).read_bytes()
    input_hash = h(raw)

    # --- Hash the sieve source (contract signature) ---
    sieve_path = os.path.join(THINKING_LOG, "src/surface/sieve.py")
    sieve_source = Path(sieve_path).read_bytes()
    sieve_hash = h(sieve_source)

    # --- Hash this harness (our contract) ---
    harness_hash = h(Path(__file__).read_bytes())

    print(f"Input:   {os.path.basename(ore_raw_path)}")
    print(f"  input_hash:   {input_hash[:16]}...")
    print(f"  sieve_hash:   {sieve_hash[:16]}...")
    print(f"  harness_hash: {harness_hash[:16]}...")

    # --- Extract claims ---
    claims = extract_claims_from_claude_session(raw)
    print(f"  claims extracted: {len(claims)}")

    if not claims:
        print("ERROR: no claims extracted from ore blob")
        sys.exit(1)

    # --- Activate venv and run promote() ---
    # Add venv site-packages to path
    import glob
    site_pkgs = glob.glob(os.path.join(VENV_SITE, "python3*/site-packages"))
    for sp in site_pkgs:
        if sp not in sys.path:
            sys.path.insert(0, sp)
    sys.path.insert(0, THINKING_LOG)

    from src.surface.sieve import promote
    sys.path.insert(0, os.path.join(THINKING_LOG, "graph-lab"))
    from build_graph import detect_deterministic_edges
    from relevance import score_all

    # --- Build argument graph from claims ---
    nodes = [
        {"id": i, "text": c["text"], "claim_type": c.get("claim_type", "")}
        for i, c in enumerate(claims)
    ]
    edges = detect_deterministic_edges(nodes)
    graph = {"nodes": nodes, "edges": edges}
    print(f"  graph edges: {len(edges)}")

    # --- Score all nodes by BFS relevance from seed claims ---
    # Seeds: claims that contain substrate-domain keywords
    domain_terms = {"substrate", "sieve", "promote", "spine", "kernel",
                    "receipt", "hash", "claim", "ore", "lore", "provenance",
                    "ledger", "pure", "function", "deterministic", "graph",
                    "surface", "binding", "ratification", "type", "watcher"}
    seed_ids = set()
    for node in nodes:
        words = set(node["text"].lower().split())
        if words & domain_terms:
            seed_ids.add(node["id"])
    print(f"  seed nodes: {len(seed_ids)}")

    bfs_scores = score_all(graph, seed_ids, max_hops=3)

    # --- Inject BFS scores into claims before promote() ---
    # Minimum threshold: claims below 0.1 graph relevance are filtered out
    # before the sieve even sees them. This replaces keyword matching as
    # the primary relevance gate.
    RELEVANCE_THRESHOLD = 0.1
    filtered_claims = []
    for i, claim in enumerate(claims):
        score = bfs_scores.get(i, 0.0)
        claim["graph_relevance"] = score
        if score >= RELEVANCE_THRESHOLD:
            claim["evidence_refs"] = ["graph-relevance"]
            filtered_claims.append(claim)
    
    pre_filter = len(claims)
    claims = filtered_claims
    print(f"  after graph filter ({RELEVANCE_THRESHOLD} threshold): {len(claims)} of {pre_filter} claims pass")

    # --- Load seed spec as topic context ---
    seed_spec_path = os.path.join(os.path.dirname(__file__), "seed_spec.json")
    with open(seed_spec_path) as f:
        seed_spec = json.load(f)

    # Extract keywords from spec definitions + constraints + sieve_rule
    spec_keywords = set()
    for term in seed_spec.get("definitions", {}).keys():
        spec_keywords.add(term)
    for term in seed_spec.get("definitions", {}).values():
        for word in term.lower().split():
            if len(word) > 4:
                spec_keywords.add(word)
    # Core substrate vocabulary
    spec_keywords.update([
        "substrate", "sieve", "promote", "spine", "kernel", "receipt",
        "hash", "claim", "ore", "lore", "provenance", "ledger",
        "pure", "function", "deterministic", "graph", "surface",
        "binding", "ratification", "loss", "gate", "primitive",
        "type", "check", "spec", "boot", "watcher", "merkle",
    ])

    topic_context = {
        "handle": seed_spec["card_id"],
        "title": seed_spec["title"],
        "description": seed_spec["context"]["mission"],
        "keywords": list(spec_keywords),
        "sieve_rule": seed_spec["transform"]["sieve_rule"],
        "invalidation_conditions": seed_spec["governance"]["invalidation_conditions"],
    }

    promoted, contested, deferred, loss = promote(claims, topic_context)

    print(f"  promoted:  {len(promoted)}")
    print(f"  contested: {len(contested)}")
    print(f"  deferred:  {len(deferred)}")
    print(f"  loss:      {len(loss)}")

    # --- Build spine output ---
    spine = {
        "schema": "sidecar.spine.v1",
        "topic": topic,
        "promoted": promoted,
        "contested": contested,
        "deferred": deferred,
        "declared_loss": loss,
        "claim_count": len(claims),
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }

    output_bytes = json.dumps(spine, sort_keys=True, default=str).encode()
    output_hash = h(output_bytes)

    # --- Build receipt ---
    receipt = {
        "schema": "sidecar.receipt.v1",
        "input_hash": input_hash,
        "sieve_hash": sieve_hash,
        "harness_hash": harness_hash,
        "output_hash": output_hash,
        "claim_count": len(claims),
        "promoted_count": len(promoted),
        "loss_count": len(loss),
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }

    # --- Write outputs ---
    os.makedirs(SPINES_DIR, exist_ok=True)
    os.chmod(SPINES_DIR, 0o777)

    base = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}_{output_hash[:12]}"
    spine_path = os.path.join(SPINES_DIR, f"{base}.spine.json")
    receipt_path = os.path.join(SPINES_DIR, f"{base}.receipt.json")

    with open(spine_path, "w") as f:
        json.dump(spine, f, indent=2, default=str)

    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"\nOUTPUT:")
    print(f"  spine:   {os.path.basename(spine_path)}")
    print(f"  receipt: {os.path.basename(receipt_path)}")
    print(f"  output_hash: {output_hash[:16]}...")
    print(f"\nVERIFY:")
    print(f"  shasum -a 256 {sieve_path}")
    print(f"  → should match sieve_hash in receipt")

    return receipt


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sieve_harness.py <ore_blob.raw> [topic]")
        sys.exit(1)

    ore_path = sys.argv[1]
    topic = sys.argv[2] if len(sys.argv) > 2 else "substrate-development"

    run(ore_path, topic)
