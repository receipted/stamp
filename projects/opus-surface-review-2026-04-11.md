# Opus Surface Review — 2026-04-11
# Model Crit v1 — First logged review, baseline for future diffs
# TAG ALL SECTIONS: [CRIT-TAG: surface-review-2026-04-11-v1]

---

## WHAT THIS IS

A dated, structured model review of the Surface/substrate codebase. This is the first entry in a **model crit log**. Future reviews will be diffed against this one using the sieve to find what changed, what we got right, what we missed.

Write for the record — not just for this conversation.

---

## THE CODEBASE

Root: `/Users/shadow/projects/thinking-log/`

**Core substrate:**
- `src/surface/kernel.py` (936+ lines) — pure functions, zero IO. Reducers, validators, hashing, AST intent extraction (recently added: `parse_function_to_claims()`, `parse_function_to_graph()`)
- `src/surface/sieve.py` (1027 lines) — `promote()`, `structure()`, `check_sieve()`, `synthesize()`. Recently added: `guarantee` claim type, `_CLAIM_DIMENSIONS` semantic dimension map, provenance-aware complementarity rule
- `src/surface/binding.py` (345 lines) — human gate (`promoted_by.startswith("human:")`)
- `src/surface/record.py` — thread blob upsert, diff tracking, ledger events
- `src/surface/claims.py` — heuristic claim extractor, two-phase model loop
- `src/surface/epistemic_tagger.py` (442 lines) — classifies relay turns: `belief_formed`, `belief_revised`, `tension_detected`, `tension_resolved`, `question_posed`, `evidence_cited`

**Labs:**
- `graph-lab/` — argument graph, BFS relevance (NOT yet wired into sieve.promote())
- `sieve-lab/` — corrections dataset, 41 false negatives identified
- `type-lab/` — semantic frame schema (kind × target × goal × polarity × source), inference rules
- `integrity-lab/` — 16 security test specs (core 8 + extended 8)
- `ore-lab/`, `lore-lab/`, `cast-lab/`, `check-lab/`, `store-lab/` — primitive labs

**Recently built (outside the repo, in workspace):**
- `intent.py` — CLI: any .py file → intent map with receipts
- File watcher → `/Users/Shared/sidecar-ore/` with hash-chained ledger
- 12 corpus sieve runs → 5 mother types identified: CONTRACT, CONSTRAINT, UNCERTAINTY, RELATION, WITNESS

**Browser extension:** `/extension/` — captures ChatGPT/Gemini DOM → posts to Surface `/record/ingest`

**Shape app:** `/shape/` — Next.js frontend that calls sieve via API, has `castToMarkdown()` and `castToHostJson()`

---

## PART 1: FULL LAY OF THE LAND REVIEW

[CRIT-TAG: surface-review-2026-04-11-v1]

Do a full architecture review of the thinking-log directory. Read the key files. Assess:

1. **What is actually working end-to-end vs what is designed but not connected?** Be specific about which functions/modules are truly wired vs which are orphaned rooms.

2. **What has changed since the original architecture?** The recent additions to kernel.py (AST parsing) and sieve.py (guarantee type, dimension map) — do they strengthen or complicate the architecture? Are they in the right place?

3. **The epistemic tagger:** Read `epistemic_tagger.py` fully. How does `belief_formed / tension_detected / question_posed / evidence_cited` relate to the mother types CONTRACT / CONSTRAINT / UNCERTAINTY / RELATION / WITNESS? Same thing in different vocabulary? Should the epistemic tagger be the type system seed rather than building from scratch?

4. **Strategic assessment:** Where is the project relative to where it should be? What's the critical path to a shippable product?

---

## PART 2: SURVEY OF src/surface/ — THE HIDDEN ROOMS

[CRIT-TAG: surface-review-2026-04-11-v1]

There are 141 files in `src/surface/`. Many have never been read by the current session. Survey these specifically and tell me what each does and whether it's a room that should be connected to the substrate:

- `epistemic_tagger.py` — already discussed above
- `coalescence.py` — sounds like claim merging
- `coagulation.py` — ?
- `parity.py` — cross-model comparison?
- `reflexivity.py` / `reflexes.py` — self-referential behavior?
- `actors.py` — agent primitives?
- `grounding.py` — ?
- `consensus.py` — multi-model agreement?
- `facilitation.py` — ?
- `epistemic_tagger.py` — type system seed?
- `outcomes.py` — ?
- `verbs.py` — ?
- `enrich.py` — ?

For each: one sentence on what it does, one sentence on whether it's load-bearing for the substrate or scaffolding that can be dropped.

---

## PART 3: THE SECURITY GAP

[CRIT-TAG: surface-review-2026-04-11-v1]

The integrity-lab tests showed 4 of 8 attack scenarios slip through the current sieve. Root cause: `source: 'untrusted:document'` and `source: 'human:engineer'` look the same to `promote()`. 

The fix: type the provenance at construction time. `HumanClaim` vs `UntrustedClaim` — the sieve only accepts `HumanClaim`. The type mismatch is caught before the sieve runs.

What's the cleanest Python implementation of this before the Rust port? And what does binding.py's existing human gate mechanism need to be extended with?

---

## PART 4: FASTEST PATH TO LAW FIRM REVENUE

[CRIT-TAG: surface-review-2026-04-11-v1]

Given the full codebase: what is the minimum viable product that a law firm would pay for?

Constraints:
- Must solve one problem they have today
- Must produce receipts they can verify independently
- Must be buildable within 4-6 weeks
- Must not require the full substrate to be complete

Be specific. Not "a provenance layer" — what exact output, what exact workflow, what exact price point.

---

## FORMAT

Clear section headers matching the 4 parts. Each section:
- What you found (specific, with file names and line numbers where relevant)
- What's wrong or missing
- What would change your assessment
- Confidence (0-1)

Tag every section `[CRIT-TAG: surface-review-2026-04-11-v1]` — this response will be sieved and diffed against future reviews.
