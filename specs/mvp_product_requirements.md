# MVP Product Requirements — May 1st
# Status: Draft
# Date: 2026-04-14
# Rule: Everything below must work for ONE example AND for any repo someone throws at it.

---

## The Product

**One sentence:** Post a codebase, get a receipted governance report.

**The endpoint:** `POST /analyze` — accepts a repo URL or source archive, returns a signed receipt bundle.

**The receipt bundle is the product.** Everything else is infrastructure that produces it or UI that displays it.

---

## Core Flow

```
user submits repo (URL or archive)
    → clone/extract source files
        → for each file: parse AST → extract typed units (CONTRACT/CONSTRAINT/UNCERTAINTY/RELATION/WITNESS)
            → classify pure vs impure boundaries
            → identify dependency provenance gaps (stamped vs unstamped)
            → stamp each transform (tagger stamp → mother_type stamp → sieve stamp)
                → assemble receipt bundle
                    → return bundle + shareable verify URL
```

---

## P0 — Must Ship (demo breaks without these)

### Input
- [ ] Accept GitHub repo URL (public repos, clone via git)
- [ ] Accept local directory path (for CLI usage)
- [ ] Accept tarball/zip upload (for the endpoint)
- [ ] Discover Python files automatically (`.py` only for v0)

### Analysis
- [ ] Parse each Python file's AST → extract functions
- [ ] Classify each function with mother types (CONTRACT/CONSTRAINT/UNCERTAINTY/RELATION/WITNESS)
- [ ] Assign dev-first subtypes via heuristic inference
- [ ] Detect pure vs impure boundaries (IO calls, global state reads, env var access, network, filesystem)
- [ ] Flag impurity in functions declared/documented as pure
- [ ] Identify dependency imports and classify as stamped (in-repo, typed) vs unstamped (external, untyped)

### Receipts
- [ ] Stamp every transform in the analysis pipeline (tagger → mother_types → sieve)
- [ ] Each stamp contains: input_hash, fn_hash (real source hash), output_hash, prev_stamp_hash
- [ ] Receipt bundle contains: all stamps, all typed units, all violations, custody chain
- [ ] `substrate verify <receipt>` independently verifies the bundle
- [ ] Receipt format is JSON, one file, self-contained

### Output
- [ ] Summary: total functions, typed breakdown by mother type, violation count
- [ ] Violations list: each with function name, file, line, mother type, what's wrong, one-sentence explanation
- [ ] Dependency map: which deps are stamped (in-repo) vs unstamped (external)
- [ ] Custody chain: sequence of stamps proving the analysis pipeline ran faithfully
- [ ] fn_hash: hash of the analysis code itself (proves which version of the tool ran)

### CLI
- [ ] `substrate analyze <path-or-url>` — run analysis, print report, save receipt
- [ ] `substrate verify <receipt.json>` — verify a receipt bundle independently
- [ ] `substrate info` — show tool version, source hashes

### Demo
- [ ] Pre-built villain codebase (AI-generated ML inference service, ~300 lines)
- [ ] The villain has 3-4 violations that light up the receipt
- [ ] Can run the villain through the platform live in <10 seconds

---

## P1 — Should Ship (demo is weaker without these)

### Output Polish
- [ ] HTML report (single file, styled, shareable) in addition to JSON
- [ ] Violation severity ranking (red/yellow/green)
- [ ] "Smoking gun" highlight — the single worst violation, visually prominent
- [ ] Shareable proof URL (even if it's just a static file host for now)

### Analysis Depth
- [ ] Cross-file RELATION detection (module A depends on module B)
- [ ] Witness refs on typed units (which AST node, which file, which line)
- [ ] Detect `pickle.loads`, `eval`, `exec`, `subprocess` as impurity signals
- [ ] Detect `os.environ`, `os.getenv` reads as impurity signals
- [ ] Detect network calls (requests, httpx, urllib, socket) as impurity signals

### Platform
- [ ] HTTP endpoint (`POST /analyze`) not just CLI
- [ ] CORS headers for browser-based submission
- [ ] Rate limiting (don't get DDoS'd on day 1)

---

## P2 — Nice to Have (ship if time, cut without guilt)

- [ ] SLSA-compatible attestation format wrapper around receipt
- [ ] Deploy to public endpoint (Fly.io or Vercel)
- [ ] Support for JavaScript/TypeScript files
- [ ] Support for Rust files
- [ ] Dependency version checking (not just presence)
- [ ] Git blame integration (who wrote the violating function)
- [ ] Cockpit integration (stream results via SSE)
- [ ] Multiple report formats (markdown, PDF)

---

## Explicitly Cut (not in scope for May 1st)

- ZK proofs
- On-chain anchoring
- Paid tier
- Multi-language in one run
- Comprehensive SAST-level analysis
- CI/CD integration
- User accounts / auth
- Persistent storage of reports
- Web UI beyond the HTML report

---

## The Villain (pre-built demo example)

**AI-Generated ML Inference Service** (~300 lines, Python)

A FastAPI service that loads an ML model and serves predictions. Looks production-ready. Tests pass. Linter clean. LLMs generate exactly this pattern.

### Built-in violations:

| # | Function | Violation | Mother Type | One Sentence |
|---|---|---|---|---|
| 1 | `load_model()` | Uses `pickle.loads` — arbitrary code execution via deserialization | CONTRACT + CONSTRAINT | "Your model loader can execute any code" |
| 2 | `validate_input()` | Reads `os.environ` in a function declared pure | CONTRACT | "Your validator gives different answers in prod vs dev" |
| 3 | `model.pkl` | No provenance — who created this file, when, with what? | WITNESS | "Your model file has no receipt" |
| 4 | `requests` dep | External HTTP calls in the prediction path, unstamped | RELATION + WITNESS | "Your predictor talks to the internet with no provenance" |

### Demo script (90 seconds):

```
[0:00] "We asked Claude to build an ML inference service."
[0:10] Show clean code. Tests pass. Linter clean.
[0:20] "substrate analyze ./ml-service"
[0:30] Receipt appears. 4 violations highlighted.
[0:40] Click violation #1: "load_model uses pickle — can execute arbitrary code"
[0:50] Click violation #2: "validate_input reads os.environ — not pure"
[1:00] Show custody chain: "every step of this analysis is receipted"
[1:10] "substrate verify receipt.json" — PASS
[1:20] "One command. Four time bombs found. Every finding receipted and verifiable."
[1:30] END
```

---

## Success Criteria

The MVP is done when:

1. `substrate analyze` runs on the villain and produces a correct receipt with all 4 violations
2. `substrate analyze` runs on an arbitrary Python repo and produces a meaningful receipt (may not catch everything, but doesn't crash or produce garbage)
3. `substrate verify` independently verifies any receipt the tool produces
4. The demo runs in <10 seconds on the villain
5. The receipt is a single JSON file someone can save, share, and verify later
6. The tool eats its own code: `substrate analyze ./substrate` produces a receipt of itself

---

## Build Order

### Days 1-3: The analysis engine
- AST parser for Python files (function extraction, impurity detection)
- Mother type assignment per function
- Dependency graph extraction
- Receipt generation (stamps for each transform)

### Days 4-6: The villain + CLI
- Build the ML inference service example
- Wire `substrate analyze` CLI command
- Wire `substrate verify` CLI command
- Run villain through platform, verify receipt

### Days 7-9: Polish + HTML report
- HTML report template (single file, styled)
- Violation severity ranking
- Smoking gun highlight
- Shareable file

### Days 10-11: Platform endpoint + deploy
- HTTP `POST /analyze` endpoint
- Deploy (Fly.io or local with tunnel)
- Rate limiting

### Days 12-13: Rehearse
- Feature freeze Day 12
- Demo script finalized
- Run 20 times
- Fix only demo-blocking bugs

---

## The Sandbag

If this goes viral on May 1st, the platform must not fall over. Minimum sandbags:

- [ ] Rate limit: 10 analyses/minute per IP
- [ ] Max repo size: 50MB / 1000 files
- [ ] Timeout: 60 seconds per analysis
- [ ] Queue: if more than 5 concurrent, return "busy, try again"
- [ ] Persist analysis results (typed units, violations, dependency graphs, receipts) — this is the dataset
- [ ] User gets their receipt. We keep the typed associations. Both are valuable.
- [ ] Source code retention policy TBD (may need opt-in consent for storage, but the typed analysis is ours)
- [ ] Error responses are clean JSON, not stack traces
- [ ] The villain example is always cached and instant
