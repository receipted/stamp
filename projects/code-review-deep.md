# Deep Code Review: thinking-log/src/surface/

**Date:** 2026-04-07
**Reviewer:** Shadow
**Total codebase:** 104,972 lines across 120 Python files

---

## SIZE BREAKDOWN

| Category | Lines | % | Files |
|----------|-------|---|-------|
| **UI/App pages** | ~43,856 | 42% | 46 app_*.py files |
| **HTTP Server** | 7,617 | 7% | 1 god-file |
| **Dashboard** | 7,008 | 7% | 1 embedded SPA |
| **Substrate Core** (kernel, sieve, binding, graph, reflexes, challenge) | ~3,078 | 3% | 7 files |
| **Semantic Spine** (evidence, dissent, commitments, claims, steering, mutations, inquiries) | ~4,439 | 4% | 7 files |
| **Orchestration** (orchestrator, capsule, stateframe, compiler, coagulation, synthesizer, adversary, lineage, healing) | ~8,488 | 8% | 9 files |
| **Data Layer** (storage, models, hashing, ids) | ~1,032 | 1% | 4 files |
| **Relay** (relay, bridge, tools, studio, actors, inbox, parity) | ~3,500 | 3% | 7 files |
| **Other** (workers, providers, sessions, narrative, etc.) | ~25,954 | 25% | ~38 files |

**The substrate — the actual IP — is ~3,078 lines (3% of the codebase).** Everything else is product surface, orchestration, or infrastructure.

---

## SUBSTRATE CORE: What's Actually Pure

### kernel.py (936 lines) — THE HEART

Six layers, all pure:

**Layer 0: StoreProtocol** — Abstract IO boundary. Runtime-checkable Protocol class. Every domain function programs against this, never against concrete storage. Methods: write_file, write_json, read_file, store_blob, read_blob, snapshot ops, artifact ops, ledger ops, policy config.

**Layer 1: Types** — 9 frozen dataclasses:
- `ClaimRecord` — the substrate primitive (claim_id, text, confidence, claim_role, type_key, binding_tier, parent_claim_id, source, inquiry_id)
- `EventRecord` — ledger event for reducer consumption
- `InquiryStatus` — computed from event reduction
- `MutationStatus` — computed from event reduction
- `PromotionEligibility` — result of promotion evaluation
- `ConflictReport` — detected conflict between claims
- `DiffResult` — pure diff computation
- `ValidationResult` — schema check result
- `ReplaySnapshot` — deterministic state at a ledger position

**Layer 2: Reducers** — 6 pure functions, all take event lists and return computed state:
- `reduce_inquiry_status(events, inquiry_id)` → InquiryStatus
- `reduce_mutation_status(events, mutation_id)` → MutationStatus
- `reduce_options(events, inquiry_id)` → list[dict]
- `reduce_evidence_refs(events, inquiry_id)` → list[str]
- `reduce_supersession(events, inquiry_id)` → dict
- `reduce_claim_tiers(events)` → {claim_id: tier}

**Layer 3: Operators** — pure transforms:
- `classify_claim_role(text)` → str (heuristic, no model)
- `compute_text_diff(old, new)` → DiffResult
- `normalize_text(raw)` → str
- `extract_type_key(text, domain)` → str|None (heuristic keyword matching)
- `build_claim_tree(claims)` → nested tree
- `flatten_claim_tree(roots)` → flat list
- `compute_claim_confidence(base, source_count, corroboration, challenges)` → float

**Layer 4: Validators** — pure schema checks:
- `validate_claim(claim)` → ValidationResult
- `validate_event(event)` → ValidationResult
- `validate_inquiry(inquiry)` → ValidationResult
- `validate_ledger_chain(events)` → ValidationResult

**Layer 5: Conflict Detection** — pure:
- `detect_contradictions(claims)` → list[ConflictReport] (heuristic: same type_key, negation patterns)
- `detect_coverage_gaps(claims, required_dimensions)` → list[ConflictReport]
- `detect_stale_evidence(claims, max_age, reference_date)` → list[ConflictReport]
- `detect_all_conflicts(claims)` → combined
- `_texts_contradict(text1, text2)` → bool (negation word proximity)

**Layer 6: Replay** — deterministic:
- `compute_content_hash(data)` → sha256 string (sorted JSON, deterministic)
- `replay_to_snapshot(events, claims)` → ReplaySnapshot (same events → same hash, always)
- `verify_replay_determinism(events, n_replays)` → bool

**Verdict: kernel.py is genuinely pure.** No imports of I/O libraries. No `open()`, no `os.path`, no network. The StoreProtocol is the only IO boundary and it's an abstract interface. This is the real substrate.

### sieve.py (1,027 lines) — THE GATEWAY

Two pure stages + one orchestrator:

**`promote(claims, topic_context, all_handles)`** — PURE. Takes claim list + topic context, returns (promoted, contested, deferred, loss). Pipeline:
1. Type accuracy check (reclassify mistyped claims heuristically)
2. Relevance filter (source match → provenance match → keyword overlap with inferred terms)
3. Cross-contamination filter (claims mentioning other topic handles)
4. Deduplication (>80% Jaccard word overlap = duplicate)
5. Deferred bucket (claims that pass relevance but lack confidence signals)
6. Contested detection (attack signal between promoted pairs)

**`structure(promoted, topic_context, loss, deferred)`** — PURE. Groups claims by type, builds summary from strongest, computes compression ratio.

**`check_sieve(card, input_stats)`** — PURE. 5 structural checks: compression_holds, no_empty_sections, loss_declared, all_drops_have_reasons, deferred_bounded.

**`synthesize(promoted, cluster_threshold, max_lines)`** — PURE. Greedy clustering by Jaccard overlap, pick representative per cluster, rank by size.

**`synthesize_with_embeddings(promoted, embeddings, ...)`** — PURE. Same as synthesize but uses numpy cosine similarity instead of Jaccard.

**`sieve_topic(store, handle)`** — IMPURE. This is the orchestrator. Loads data from store, calls pure stages, persists artifacts + ledger events. This is the IO boundary.

**Key weakness:** Relevance is still keyword-based with inferred corpus terms. `_extract_keywords()` is the bottleneck — it's bag-of-words plus bigrams. No graph awareness. The 41 false negatives from sieve-lab corrections are caused by this. graph-lab/relevance.py has the pure function replacement (BFS from seeds) but it's NOT integrated into sieve.py yet.

### binding.py (345 lines) — THE PROMOTION ENGINE

**`evaluate_promotion(store, claim_id)`** — Reads from store (not pure in the strict sense, but zero writes). Checks 5 criteria:
1. Cross-turn recurrence (claim text in 2+ snapshots, 60% word overlap)
2. Cross-model agreement (2+ different models affirm similar claim)
3. No active dissent (no unresolved challenges)
4. Human ratification (promoted_by starts with "human:")
5. Replay stability (guaranteed by deterministic replay)

**`promote_claim(store, claim_id, new_tier, promoted_by)`** — The write path. Enforces:
- Tier can only go UP (observed → proposed → ratified)
- **Ratified requires `promoted_by` starting with `human:`** — the human gate is enforced in code
- Emits `claim.promoted` ledger event

**`compute_semantic_health(store)`** — Read-only projection: counts by tier, active dissent, contradiction rate, rollbacks.

**Verdict: The human gate IS enforced.** Line ~130: `if not promoted_by.startswith("human:"):` return error. This is the code that implements "the system may prepare indefinitely, it may never decide without a remembered human action." It's real, not aspirational.

### graph.py (445 lines) — EDGE STORAGE (not the graph-lab graph)

This is the **Surface** graph layer — stores typed edges as artifacts in the ledger. NOT the pure function graph traversal from graph-lab.

Functions: create_edge, get_edges, get_neighbors, get_subgraph, walk_back (provenance reconstruction), generate_edges_from_topology, cross-topic edges, suggest_cross_topic_links.

**All functions use store** — this is the persistence layer for edges, not the compute layer. The pure compute lives in graph-lab/relevance.py.

### challenge.py (236 lines) — DEMOTION ENGINE

`challenge_claim()` — Creates dissent + files challenge. Auto-demotes ratified claims to proposed. `resolve_challenge()` — Optionally restores tier. Both emit ledger events.

**This is the inverse of binding.py.** Binding promotes (with human gate). Challenge demotes (creating first-class dissent). Together they implement the full lifecycle: observed → proposed → ratified → (challenged) → proposed.

### reflexes.py (1,089 lines) — SELF-HEALING

10 built-in reflexes (5 soft heuristics + 5 hard invariant guards). Detect → repair → verify cycle with ledger trail.

Soft: evidence coverage, decision crystallization, contradiction detection, missing key variable, summarize+map.
Hard: provenance guard, decision criteria guard, append-only guard, deterministic hydration guard, no-duplicate-claims guard, no-silent-duplication.

---

## WHAT'S WORKING VS. WHAT'S NOT

### Working and Proven:
1. **kernel.py** — Genuinely pure. 9 types, 6 reducers, 7 operators, 4 validators, 4 conflict detectors, deterministic replay. This is solid.
2. **The human gate** — Enforced in code (binding.py line ~130). Not just a design principle.
3. **Append-only ledger** — Hash-chained, verified. Status is computed from events, never stored.
4. **The sieve pipeline** — promote/structure/check are pure functions. They work. The 2,310 tests prove it.
5. **Deterministic replay** — Same events → same hash. Verified with multi-iteration stability tests.

### Working but Keyword-Limited:
6. **Sieve relevance** — Pure function but keyword-based. 41 false negatives on corrections. Graph-lab has the fix but it's not integrated.
7. **Conflict detection** — Heuristic negation-proximity matching. Catches obvious contradictions, misses subtle ones.
8. **Type key extraction** — Keyword pattern matching in `extract_type_key()`. Covers temporal, financial, risk, coverage, quality. No real type inference.

### Not Integrated:
9. **graph-lab/relevance.py** — Pure function graph-based relevance scoring (BFS from seeds). Exists but NOT wired into sieve.py's promote().
10. **graph-lab/build_graph.py** — Deterministic edge detection + LLM-assisted refinement. Exists but produces standalone .graph.json files, not connected to the Surface graph.py edge store.
11. **type-lab/** — Semantic frame schema defined in CARD.md. infer.py and mine.py exist but I haven't verified their state.

### Massively Over-Built:
12. **42% of the codebase is app_*.py files** — 46 UI pages that are HTML embedded in Python strings. These are product surfaces that were built top-down. They work but they're not the substrate.
13. **http_server.py** — 7,617 line god-file. A single if/elif dispatch chain with 87+ routes.
14. **dashboard.py** — 7,008 lines of embedded SPA.

---

## THE GAP

The substrate core (kernel + sieve + binding + challenge) is ~2,544 lines of genuinely principled code. The pure function boundary is real. The human gate is enforced. The deterministic replay works.

**What's missing is the bridge between:**
- graph-lab's pure relevance scoring → sieve.py's promote()
- type-lab's semantic frames → kernel.py's type system
- The card protocol's formal spec → the runtime's actual behavior

The labs have the right primitives. The kernel has the right architecture. They're just not connected yet. That's the integration work.

---

## WHAT'S REAL VS. ASPIRATIONAL

| Claim | Status |
|-------|--------|
| "Pure functions govern the substrate" | **REAL** — kernel.py, sieve promote/structure/check, graph-lab relevance.py |
| "Status is computed, never stored" | **REAL** — reducers in kernel.py derive status from event lists |
| "The human gate is enforced" | **REAL** — binding.py line ~130 rejects non-human promotion to ratified |
| "Same input → same output" | **REAL** — verify_replay_determinism() proves it |
| "Graph-based relevance" | **EXISTS BUT NOT INTEGRATED** — graph-lab has it, sieve doesn't use it |
| "Semantic type system" | **DESIGNED BUT NOT BUILT** — type-lab CARD.md has the schema, code is early |
| "Cards govern shaping" | **REAL IN SHAPE APP** — sieve_card_v1.json is loaded and sent as instruction |
| "The system is its own proof" | **PARTIALLY REAL** — ledger events ARE the audit trail, but check artifacts aren't yet self-proving objects |
