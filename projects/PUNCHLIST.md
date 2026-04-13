# Punchlist — Rolling
# Last updated: 2026-04-13

**North star:** Feed code in. Intent map out. No LLM. Ship it.

---

## ⚠️ PROTECTION FIRST (before anything else)
- [ ] **Public GitHub repo** — timestamp prior art. This week. Free. Non-negotiable.
- [ ] **Provisional patent** — $150-300, do it yourself, 30 days. Covers turn chain + lens-scoped run-spec + provenance gate.

---

## DONE (this week)
- [x] AST parser `parse_function_to_claims()` + `parse_function_to_graph()` in kernel.py
- [x] `intent.py` CLI — runs on any .py file, produces receipts
- [x] Purity signals (✓ pure / ⚠️ IMPURE / ⚠️ UNVERIFIED)
- [x] Tested on httpx/_urls.py — gate open
- [x] Epistemic tagger wired into sieve as pre-pass (inlined patterns, no injection vector)
- [x] Provenance gate in promote() — untrusted sources blocked
- [x] `guarantee` type — first new type from evidence
- [x] `_CLAIM_DIMENSIONS` semantic dimension map
- [x] Complementarity rule — different dimensions, same fn = not contested
- [x] 23 substrate tests — all green
- [x] `turn_chain.py` — hash-chain individual conversation turns with model attribution
- [x] `anchor.py` — Merkle anchoring to git (free tier)
- [x] Session anchored: 1,547 turns, Merkle root `4c690b5e...`, git commit `cf2f76e8...`
- [x] `harness.py` — multi-model harness with lens-scoped spec cards, cost estimator
- [x] `bridge.py` — SSE server feeding real sieve output into cockpit
- [x] `cockpit.html` — two-tab UI (Nuggets/Sediment), drill-down navigation
- [x] `audio_claim.py` — typed claims from audio signal (librosa)
- [x] 15 corpus runs — mother types confirmed across all domains
- [x] Formal type definitions with reasoning (mother-type-definitions.md)
- [x] Codebase cleanup — screenshots/txt/UI apps moved to _legacy/
- [x] `harness-design.md` — parallel vs sequential, defensibility layer

---

## NOW (immediate)

- [ ] **Run bridge.py** — test with live session data, see cockpit update in real time
- [ ] **UX design session** — cockpit redesign (you drive, I implement)
  - Round-robin prompt patterns as a new creative form
  - Conversational UX extension, not a scary matrix
  - Thinking environment, not dashboard
- [ ] **Requirements vs implementation test** — run sieve on spec claims vs code AST claims, compare spines
- [ ] **Git hook** — pre-commit runs intent.py on changed files, appends receipts

---

## NEXT

- [ ] **README + GitHub** — after protection plan. Rust first repo or Python. TBD.
- [ ] **critics.py → substrate wire** — multi-model spine with receipts
- [ ] **Turn configs + persona variables** — Liberating Structures as JSON configs
- [ ] **Rhetorical sieve** — detect when delivery diverges from content (epistemic hacking defense)
  - Positive sentiment wrapping a CONSTRAINT = flag
  - Consolation after LOSS = flag  
  - High confidence on UNCERTAINTY = flag
  - Sycophancy: human's framing adopted without evidence = flag
  - Output: `rhetorical_mismatch: true` on the claim, visible in the cockpit nugget
  - The declared loss of rhetorical sieve = what the delivery was trying to make you feel
- [ ] **Reverse-cast algorithm inference** — type Instagram meme feed → infer algorithm shape
- [ ] **Audio corpus runs** — voice/ambient as typed sediment

---

## AFTER TRACTION

- [ ] Rust port → WASM → ZK circuit → on-chain verifier
- [ ] Repo crawler (enterprise tier)
- [ ] Mac Mini / MBP virgin account career ops platform
- [ ] Tablets (HD-Rosetta nickel + 5D quartz editions)
