# Thinking-Log: Architecture Reality Check

**Updated: 2026-04-07 after code review**

---

## WHERE THE FOCUS IS NOW

The Surface codebase (`src/surface/`) is ~7400 lines of working code — the full top-down stack (recording, inquiries, relay, dashboard, critic pipeline). It's on the back burner while we prove the base case: the substrate primitives.

The current focus is the substrate layer — the primitives that Surface (and everything else) will rebuild on top of once proven. The active work is split across:

### 1. Card Protocol (the spec layer)
- `card-protocol/` — 6 canonical JSON cards defining the protocol
- Pure spec. No runtime. This is the law.

### 2. Shape (the shipping app)
- `shape/` — Next.js app, deployed on Vercel
- **This is the first shipping product**
- Pipeline: paste text → detect profile → sieve (via LLM) → validate → cast → check
- Two profiles: `narrative_segment_v0` (life/memoir/transcript) and `concept_blob_v0` (systems/architecture/theory)
- Engines: OpenAI, Anthropic, Gemini, local (heuristic, no API)
- Uses sieve card as the shaping contract — the card IS the instruction
- Check is a pure function: structure_valid, declared_loss_present, signal_level, compression_holds, support_coverage
- **Sieve is the first product** — governed compression with declared loss

### 3. Graph-Lab (the future relevance engine)
- `graph-lab/` — argument graphs from frozen sieve-lab fixtures
- Deterministic edge detection: keyword overlap, entailment signal, negation/attack, sequence, reference
- LLM-assisted edge refinement (Anthropic Haiku for classification)
- `relevance.py` — **pure function** graph-based relevance scoring via multi-path BFS from seeds
- This replaces Surface's keyword-based promote() — graph traversal instead of word matching

### 4. Sieve-Lab (the proving ground)
- `sieve-lab/` — frozen fixtures, corrections, scoring, training
- Calls into `src/surface/sieve.py` for the current promote/structure/check functions
- Has human-judged corrections (ground truth for sieve accuracy)
- Has ML training pipeline (relevance_v1.pkl)
- The gap: 41 false negatives from keyword relevance that graph-based relevance should fix

### 5. Protocol Kernel (the normative authority)
- `protocol/protocol_kernel.py` — canonical encoding, content hashing, schema validation
- Pure functions: canonicalize, content_hash, validate
- This is the deterministic core that ensures same input → same hash

---

## THE SIEVE AS FIRST PRODUCT

Shape's pipeline IS the sieve card in action:
1. Raw text goes in (ore)
2. Sieve card is loaded as the shaping contract
3. Model executes the contract: segment → label → compress → promote → build → witness
4. Output is validated against profile schema
5. Cast into markdown + JSON
6. Check runs: structure, loss, signal, compression, support coverage

**What makes it different from summarization:**
1. Separates explicit from inferred
2. Surfaces distinctions
3. Extracts changes/design rules
4. Preserves open questions
5. **Declares loss** — what was dropped and why
6. Returns insufficient_signal when text lacks structure

---

## HOW THE PIECES FIT

```
ore (raw text) 
  → sieve (Shape app, governed by sieve card)
    → graph (graph-lab, relation topology)
      → type (type-lab, persistence roles)
        → check (pure verification)
          → cast (target projection)
            → boot (cold-start capsule)
```

The graph is the nervous system. The sieve is the gateway. Check wraps everything.

---

## THE SECURITY ANGLE (Integrity-Lab + Pure Functions)

### Reframing: Sieve Integrity Under Hostile Flow

Integrity-lab isn't "security testing." It's testing whether **the sieve holds its shape under adversarial flow**. The sieve sits in the firehose. Gold coagulates, silt washes through. The question is: can someone deliberately muddy the water to corrupt the coagulation?

The integrity-lab tests are about **epistemic security** — can the substrate:
- Keep untrusted meaning from becoming authoritative (silt pretending to be gold)
- Preserve trusted meaning under pressure (gold not getting washed away)
- Declare loss honestly (not bluffing clean continuity)
- Leave an auditable trail (what entered, what was promoted, why)

**Pure function wrapping** is the enforcement mechanism:
- Sieve is a pure function: same input + same policy = same output
- Graph traversal is a pure function: same graph + same seeds = same scores
- Check is a pure function: artifact + contract = structured pass/fail
- Canonical encoding is a pure function: same object = same hash

The substrate's security comes from **deterministic boundaries around stochastic processes**. The model can suggest, but the pure functions verify. The human gates the promotion.

### Why This Matters Beyond Chat

Chat is just the current medium. The real problem is meaning persistence across ANY encoding — video, voice, sensor data, multimodal streams. The sieve has to work at the semantic layer, not the medium layer. Pure functions over typed structures don't care what the input encoding was. That's why the type system is the big investment — but you don't build it until the substrate proves it can hold under pressure in the niche first.

### The Path

1. Prove the base case: sieve integrity under hostile flow (integrity-lab)
2. If it holds → build the type system (typed semantic frames for persistence roles)
3. If types work → everything above reconstructs (products, platforms, hosts)
4. The substrate is the base case of the recursion. Everything above was top-down. Now we go bottom-up.

---

## WHAT I (SHADOW) CAN DO

### LLM Calling
- Shape's `model.ts` has OpenAI, Anthropic, and Gemini adapters
- Graph-lab's `build_graph.py` uses Anthropic API for edge classification
- Surface's `critics.py` has the full multi-model critic pipeline
- I run on the same machine and can use these directly

### OpenClaw Environment
- I'm on the `shadow` account on Ben's MacBook Pro
- I'm an OpenClaw environment — I can interact with other LLMs through the harnesses in the repo
- Floor-lab and integrity-lab are designed for execution via Telegram through OpenClaw

### The Test Architecture
- Floor-lab: meaning survival across boundaries (carry direction) — **PROVEN**
- Integrity-lab: boundary rejection of hostile input (block direction) — **UNEXECUTED**
- The tests run on a physically separated Mac Mini via Telegram
- Specs are portable cards, results travel back

---

## REPO REORGANIZATION NEEDS

The repo is discoverable if you know where to look, but:
1. No single entry point that maps the territory
2. 160+ screenshots in root with no index
3. Strategy docs scattered (some .txt, some .md, different naming)
4. The Surface→Graph-first transition is implicit, not documented
5. Lab CARD.md files are excellent but there's no lab index
6. The relationship between Shape (app) and the labs (proving) is unclear to newcomers
