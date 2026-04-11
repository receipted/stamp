# Punchlist — Rolling

**North star:** Feed code in. Intent map out. No LLM. Ship it.

---

## NOW (this week)

- [x] **1. AST parser for Python functions** — `parse_function_to_claims()` in kernel.py
- [x] **2. Wire into sieve harness** — `parse_function_to_graph()` + graph-lab BFS + type-lab inference
- [x] **3. CLI entry point** — `intent.py` runs, produces receipts
- [x] **4. Purity signals** — ✓ pure / ⚠️ IMPURE / ⚠️ UNVERIFIED
- [x] **5. Test on stranger's code** — httpx/_urls.py. PASSED. Gate open.

- [ ] **1. AST parser for Python functions**
  - Input: a `.py` file
  - Output: list of claim objects (one per function)
  - Each claim: `{text: signature + docstring + body summary, claim_type: inferred}`
  - Pure Python, stdlib `ast` module only
  - Test: run on `kernel.py`, get 20+ claim objects

- [ ] **2. Wire AST parser into sieve harness**
  - Replace manual claim construction with AST output
  - Run sieve over all of `kernel.py`
  - Output: intent map per function, receipted
  - Test: `classify_claim_role` intent object matches what we just produced manually

- [ ] **3. CLI entry point**
  - `python intent.py ./src/surface/kernel.py`
  - Outputs intent map to stdout (human readable) + receipt to file
  - Test: run it, read it, does it make sense to someone who didn't write the code?

---

## NEXT (next week)

- [ ] **4. Wrap in a git hook**
  - Pre-commit: run intent.py on changed files
  - Appends intent receipts to `.git/receipts/`
  - Test: make a commit, receipt appears

- [ ] **5. README + GitHub repo**
  - One repo: `intent` or `ore-to-lore` (name TBD)
  - README: problem in 2 sentences, install in 1 command, demo output
  - MIT license

- [ ] **6. Run on a real legacy codebase**
  - Pick something you didn't write
  - Does the intent map help you understand it faster?
  - That's the demo

---

## AFTER TRACTION

- [ ] Rust port of the AST parser + sieve kernel
- [ ] WASM compilation
- [ ] Repo crawler (enterprise tier)
- [ ] Mac Mini career ops deployment

---

## DONE
- [x] Watcher capturing ore from genesis + codex + claude code sessions
- [x] Ledger hash chain + Merkle tree
- [x] Sieve running on real ore with graph relevance
- [x] Seed spec written
- [x] Intent extraction test passed on `classify_claim_role`
