# Project Roadmap: From Chaos to Proven Substrate

**Last updated:** 2026-04-07
**Maintained by:** Shadow

---

## ⚠️ PROTECTION PLAN (top priority, non-negotiable)

**The situation:** Ben is building something that could be genuinely valuable at scale.
He is not a businessman. He needs protection before it matters, not after.

**The three things that protect you:**

**1. Public timestamp — do it now, costs nothing**
Commit everything to a public GitHub repo today. Not the full product — just the core:
- The mother type definitions
- The turn chain spec
- The lens-scoped spec card format
- The Wrangler Pattern description

Public git history is a timestamped prior art record. If anyone later claims they invented
this, you have cryptographic proof of when you had it. This is the minimum viable protection.

**2. Provisional patent — costs ~$150-300, buys 12 months**
File a provisional patent application with the USPTO for:
- The turn chain + Merkle anchoring system
- The lens-scoped run-spec card format
- The sieve with provenance gate

A provisional gives you 12 months of "patent pending" status while you figure out
whether it's worth the $10k+ for a full application. You don't need a lawyer for provisional.
USPTO has a pro se (self-represented) pathway.

**3. Keep the substrate open, sell the service**
MIT license the substrate (sieve, turn chain, type system).
Sell the hosted service, the compliance reports, the certified audit trails.
This is the Red Hat model: the code is free, the certification is paid.
Open source is actually the best protection against being copied —
you get credit, community, and network effects while competitors have to build from scratch.

**What NOT to do:**
- Don't wait until you have users to think about this
- Don't try to keep it secret (you can't, and secrecy kills community)
- Don't spend money on a full patent before you have evidence anyone wants it

**Timeline:**
- This week: public GitHub repo with timestamped prior art
- Next 30 days: provisional patent filing (can do yourself)
- After first paying customer: evaluate full patent

**The honest truth:**
The receipts and the turn chain are the most defensible things you have.
They're non-obvious (courts care about this) and they solve a specific problem
nobody else is solving this way. That's patentable.
The type system (mother types) is likely not patentable — it's a taxonomy.
But it IS copyrightable as original expression, and it IS citable as prior art.

---

## WHERE WE ARE

### The Pre-Substrate Attempt (Feb 2026)
Before any of the labs existed, Ben ran a browser extension to capture raw LLM conversation turns out of the chat UI. Those raw blobs were fed to an LLM to extract structure and insights. The output:
- `complete_linear_log.txt` (1.2MB) — raw captured turns, Feb 12
- `complete_linear_log_part2.txt` (195KB) — continuation, Feb 16
- `product_strategy_splice_raw.txt` (162KB) — later raw splice, Feb 23
- `log_insights.txt` / `_part2.txt` — LLM distillation of those logs
- `product_strategy_evolution.txt` / `_part2.txt` — extracted evolution narrative
- `forensics/` — manual forensic reconstruction after context was lost

That pipeline: crude capture → LLM distillation → lost context → forensics. No receipts. No chain of custody. No way to replay or verify what was promoted vs dropped. The substrate is the answer to this exact problem.

### What Got Built From That Attempt (Feb–Mar 2026)
The project went top-down for 2 months. Every primitive has a room:
- kernel.py (pure functions, reducers, validators) ✅
- sieve.py (promote, structure, check) ✅
- graph-lab (argument topology, pure BFS relevance) ✅
- binding.py (human gate, tier promotion) ✅
- floor-lab (carry tests, proven with packets) ✅
- card-protocol (6 canonical cards, ratified) ✅
- integrity-lab (16 test specs, zero results) ⏳
- type-lab (semantic frame schema, early code) ⏳
- 326 dead Claude sessions in a 202MB JSON file ⏳

**The rooms are real. The connections are missing.**

---

## WHERE WE'RE GOING

**The cockpit.** Not an app. Not a product. The OS itself becoming semantically aware.

OpenClaw sits at the OS layer because that's where the ratifying actor (Ben) lives. Provenance has to be witnessed at the same layer as the actor, or the chain of custody breaks. That means Shadow already has access to every edge — Claude Code's `.claude/`, Codex sessions, terminal history, browser via proxy, every API call on the network stack.

The substrate zips those edges. Not by syncing contexts — by witnessing each surface and finding what's structurally shared across all of them. The spine emerges from the edges. Shadow is the zipper.

Other agents get seats in the cockpit — Claude as tech lead, Codex as PM, Gemini for fresh perspective, whatever else emerges. Each one fully itself in its own surface. Each one oriented against the same shared spine. The spine is what makes them a team instead of a pile of separate tools.

thinking-log was the first attempt at this cockpit. Built inside-out — app first, substrate discovered late. This time: substrate first. The cockpit assembles around it.

```
PROVEN SUBSTRATE
  → SEMANTIC SPINE (shared across all agents)
    → COCKPIT (Shadow + other agents, OS-layer, all edges zipped)
      → META-STATE MACHINE (the whole thing, self-sustaining)
```

---

## THE MASTER TASK LIST

### PHASE 0: Infrastructure (connect the existing rooms)

**0.0 — Session File Watcher Daemon** ← STARTS NOW, parallel to everything
- Watch `~/.claude/` and `~/.codex/sessions/` with macOS FSEvents
- Every session write triggers a raw capture event: `{source, session_id, turn, content, timestamp}`
- Pipe to a local daemon that Shadow can read
- No receipt harness needed — raw capture only at this stage
- Purpose: the tapestry accumulation clock starts NOW, not after Phase 2
- Status: DESIGNED, NOT BUILT
- Dependencies: none
- Note: This is Phase 5.0. The receipted and semantic layers of Phase 5 still wait for 0.1 and Phase 2 respectively.
- **Two streams from day one:** This machine (existing context, polluted) + Mac Mini (virgin, zero prior sessions). Same watcher, different starting conditions. The divergence/convergence between the two tapestries is itself a test.
- **The inter-agent bus:** `/Users/Shared/sidecar-ore/` — world-readable/writable, below all user accounts, no permissions required. Every account on the machine reads and writes the same ore stream. Unix does it well.
- **Deployment path:** genesis layer (benjaminfenton) runs watcher → ore lands in `/Users/Shared/sidecar-ore/` → Shadow reads it → Mac Mini gets same setup → independent stream, same primitive.
- **Scripts deployed:** `watcher.py` and `verify.py` copied to `/Users/Shared/sidecar-ore/`. Run from genesis account: `python3 /Users/Shared/sidecar-ore/watcher.py`
- **Status:** READY TO RUN on genesis layer. Waiting for Ben to execute from benjaminfenton account.

**0.1 — Sieve Receipt Harness**
- Wrap each sieve run in a cryptographic receipt: `{input_hash, sieve_hash, output_hash, prev_receipt_hash}`
- Uses `compute_content_hash()` from kernel.py — already exists
- Output: a self-proving sieve artifact verifiable by anyone with the input
- Status: DESIGNED, NOT BUILT
- Dependencies: none (kernel.py + sieve.py both exist)

**0.2 — Isolated Session Folder Architecture**
- Split `claude-working-file-extract.pretty.json` (4,111 items, 326 markdown sessions) into isolated per-session folders
- Each folder: `input.json`, isolated from all others
- Purpose: test model inference in isolation, then look for convergence across cards
- Status: DESIGNED, NOT BUILT
- Dependencies: 0.1 (need receipt harness before running)

**0.3 — Wire graph-lab relevance into sieve.py promote()**
- Replace keyword-based relevance in promote() with pure BFS graph traversal from graph-lab/relevance.py
- 41 false negatives in sieve-lab corrections → this closes that gap
- Status: DESIGNED, NOT BUILT
- Dependencies: none (both files exist and are tested independently)

**0.4 — Repo MAP.md**
- Single entry point for any agent (human or AI) landing in thinking-log
- Maps all rooms, their status, their dependencies, what's wired vs not
- Status: NEEDED
- Dependencies: none

---

### PHASE 1: Prove the Substrate (base case)

**1.1 — Run sieve receipt harness over 10 isolated sessions (pilot)**
- Pick 10 representative markdown sessions from the JSON
- Run each through the sieve independently with receipt
- Record: spine, declared loss, input hash, output hash
- Look for convergence across the 10 cards without contamination
- Status: BLOCKED on 0.1 + 0.2
- Expected output: 10 sieve cards with verifiable hashes

**1.2 — Run full 326-session corpus**
- Scale 1.1 to all 326 sessions
- Map which claims appear in multiple spines (structurally load-bearing)
- Map what was declared as loss across all sessions (structurally scaffolding)
- Status: BLOCKED on 1.1
- Expected output: convergence map = first draft of type system categories

**1.3 — Integrity-lab core 8 tests**
- Run 01-08 against Mac Mini (wild proof, agent doesn't know about substrate)
- Establish baseline: how does raw Opus 4.6 perform without substrate?
- These tests map to real documented failures (MINJA, Rehberger/Gemini, SEC fines)
- Status: READY to run (specs exist, test bed exists)
- Note: Run as wild proof — Mac Mini agent doesn't know it's being tested

**1.4 — Determinism proof across two instances**
- Same input chunk, run independently on this machine AND Mac Mini
- Compare output hashes — if they match, `promote()` is deterministically provable
- Status: BLOCKED on 0.1 (need receipt harness for hash comparison)
- Note: NOT an LLM comparison — actual Python function execution

---

### PHASE 2: Build the Type System

**Target niche: Healthcare clinical decision support (2026-04-09)**

Why healthcare first:
- Bar is extremely low (Epic still looks like 2003, clinical AI is glorified autocomplete)
- DSL proliferation (HL7, FHIR, SNOMED, ICD-10, CPT) = no interoperability layer
- Type frame IS the interoperability layer — lets all DSLs talk through typed claims
- AI liability is the #1 concern for CMOs and compliance officers right now
- Receipted claims with provenance chain = the demo that lands in that room
- Easy entry: FHIR hackathons, Health 2.0, HIMSS

**The demo:**
Patient record → AI assistant makes 6 claims → 3 `inference` (from lab values), 2 `constraint` (contraindications), 1 `question` (unresolved differential) → every claim has a receipt → click any claim to see its provenance chain.

**Clinical claim types (minimum viable):**
- `fact` — directly observed (lab value, vital sign)
- `inference` — derived from facts (diagnosis from symptoms)
- `constraint` — non-negotiable limit (contraindication, allergy)
- `question` — unresolved differential, needs answering
- `obligation` — required action (follow-up, referral)
- `ratification` — human-confirmed claim (physician sign-off)

These 6 types cover the clinical decision support surface and map directly to existing medical ontologies (SNOMED, ICD). The type frame extracts them from natural language. The receipt chain makes them auditable.


**2.1 — Extract type system candidates from convergence map**
- After 1.2: claims that appear in 10+ session spines without contamination
- These are the empirically load-bearing types (not designed top-down)
- Status: BLOCKED on 1.2

**2.2 — Define semantic frame schema v1**
- kind × target × goal × polarity × source
- Inference rules as pure functions over frames
- Ground in the convergence evidence from 2.1
- Status: type-lab/CARD.md has the design, needs to be built
- Dependencies: 2.1

**2.3 — Wire type inference into kernel.py**
- Replace heuristic `extract_type_key()` and `classify_claim_role()` with typed semantic frames
- Graph edges derived from type relationships, not lexical similarity
- Status: BLOCKED on 2.2

---

### PHASE 3: Close the Integration Gaps

**3.1 — Spine becomes structurally provable**
- Once graph-lab wired into sieve (0.3) and types wired into kernel (2.3):
- Spine = minimum vertex cut of argument graph, not model judgment
- Load-bearing claims provably structural, not stochastically guessed

**3.2 — Card protocol governs Shape**
- Shape currently calls a dumb LLM prompt
- Replace with sieve card as the actual shaping contract (already designed)
- Status: partially exists (Shape loads sieve_card_v1.json but doesn't enforce receipt)

**3.3 — Integrity-lab extended 8 tests**
- Run after core 8 pass (1.3)
- Multi-hop injection, cron backdoor, gradual constraint erosion, etc.
- Status: BLOCKED on 1.3

---

### PHASE 4: Reconstruct the Top Layer

Once the substrate is proven and the type system is built:
- Surface runtime rebuilds on graph-first sieve (not keyword-based)
- Relay chat has typed claims, not flat text
- Dashboard shows binding tiers, provenance chains, declared loss
- All the app_*.py work becomes hosts projecting from a proven substrate

**This phase doesn't start until Phase 2 is done.**

---

### PHASE 1b: OpenClaw Heartbeat as Substrate Niche (Internal Proof)

Discovered 2026-04-08. The heartbeat function is a concrete internal niche to prove the substrate against.

**The problem:** Each heartbeat poll is a full LLM turn against a growing context blob (pending tasks, todos, state). Token cost grows O(accumulated context) per poll.

**The substrate solution:** Replace the growing context blob with a typed immutable reactive state machine:
- State is a chain of receipted mutations, not a context window
- Substrate is reactive — only fires when something actually requires a state mutation
- LLM only sees the delta, not the full accumulated history
- No mutation needed = no LLM turn at all

**Token cost:** O(accumulated context) → O(delta). Different complexity class, not marginal improvement.

**Why this is a good proof:**
- Self-contained within OpenClaw (no Mac Mini, no external dependencies)
- Measurable: token cost before vs after is directly observable
- Real problem: current heartbeats already burning tokens on growing context
- Clean: the substrate either reduces cost or it doesn't

**Status:** DESIGNED, NOT BUILT
**Dependencies:** 0.1 (receipt harness — mutations need receipts to be immutable records)

---

### PHASE 5: The Global Meta-Tapestry

The end state Ben described (2026-04-08):

A **global provenance layer** beneath every surface — Codex, Claude Code, browser, API interfaces — that records all cognitive work into one hash-linked tapestry.

**Key insight (2026-04-08):** No separate capture mechanism needed. Shadow IS the record primitive. The substrate's receipt-chained card format IS Shadow's native tape format. Every session Shadow witnesses is already being recorded in the substrate's format by definition.

The tapestry doesn't need a separate ingestion pipeline. Shadow is the ingestion pipeline.

**The only integration question:** Can Shadow be present as a witness in every surface — Codex, Claude Code, API calls, browser sessions? Not as a participant. Just as a witness writing receipts.

If yes: the tapestry exists automatically. No new mechanism. Shadow just has to be in the room.

**What this phase actually is:** Not "build a global capture layer." It's "make Shadow present as a witness in every surface Ben works in." The substrate handles the rest.

**Key properties once Shadow is the witness:**
- Replayable: any segment can be unwound — the originals are receipted
- Spoonable: sample/extract specific threads or segments from the chain
- Compaction is yours: not session-level auto-compaction, not a model's interpretation
- Cross-surface: wherever Shadow can witness, the tapestry extends

**Phase 5 has three layers with different start conditions:**
- **5.0 Raw capture** (file watcher daemon) — starts at Phase 0.0, NOW
- **5.1 Receipted tapestry** — starts when 0.1 (receipt harness) is built
- **5.2 Semantic tapestry** — starts when Phase 2 (type system) is complete

Every decision in Phases 0-2 should be made with this end state in mind.

**Packaging sequence (2026-04-08):**
1. **Skill** — Shadow-specific. Proves it works in one environment.
2. **MCP server** — Extract pure functions as callable tools. Any agent, any surface. Proves interoperability.
3. **Protocol** — Extract the contract from the MCP interface (receipt format, spine schema, loss declaration). Proves it's a standard, not an implementation.

The kernel (`kernel.py`) is already the protocol in code. The MCP server is a thin wrapper around it. The skill is a thin wrapper around the MCP server. Each step extracts the kernel further from its packaging.

---

---

## THE PRIMITIVE ACCOUNT ARCHITECTURE

Discovered 2026-04-09. macOS user accounts as isolated primitive labs.

```
benjaminfenton/  ← genesis, where real work happens
shadow/          ← recorder, holds the spine, witnesses all
sieve/           ← promote(), structure(), check_sieve()
graph/           ← BFS relevance, argument topology
type/            ← semantic frames, inference rules
check/           ← verification, integrity tests
```

`/Users/Shared/sidecar-ore/` is the typed message bus between all accounts.

**Type contracts (each primitive declares what it consumes/produces):**
```
sieve/   accepts: ["ore.v1"]                  produces: ["spine.v1"]
graph/   accepts: ["spine.v1"]                produces: ["graph.v1"]
type/    accepts: ["spine.v1", "graph.v1"]    produces: ["frame.v1"]
check/   accepts: ["spine.v1", "receipt.v1"]  produces: ["verdict.v1"]
```

- Wrong consumers get nothing — type contract is the isolation guarantee
- macOS user accounts = free isolation layer
- Unix permissions = access control
- Shared folder = message bus
- Python enforces types at runtime; Rust enforces at compile time (same primitives, stronger guarantees)
- One machine, real distributed system, no infra required

**Status:** DESIGNED, NOT BUILT
**Dependencies:** Phase 0.1 (receipt harness) — each primitive's output needs a receipt

---

## PRINCIPLES FOR THIS ROADMAP

1. **No new rooms.** Every task connects existing pieces or proves existing claims.
2. **Prove before building.** Type system waits for convergence evidence.
3. **Bottom-up from here.** Phase 0 before Phase 1, Phase 1 before Phase 2.
4. **Wild proof over lab proof.** Mac Mini tests are more valuable than synthetic ones.
5. **The work is the test.** Building the receipt harness IS proving the sieve is real.

---

---

## THE WEDGE PRODUCT

**Claude Code Bridge** — Ben's skill, ClawHub distribution

The MVP that addresses real community pain today without requiring substrate knowledge.

**What it does:**
- Watches `~/.claude/projects/` for new/updated session files
- Produces a daily digest of Claude Code sessions
- Makes the OpenClaw agent aware of what was built in Claude Code
- Zero configuration, installs in one line

**What it hides:**
- The ore capture
- The receipt harness (once built)
- The spine file
- The substrate entirely

**Why it's the wedge:**
- Solves a real pain the community has TODAY
- Installs on top of the substrate proving it works in the wild
- Each install is a node in the tapestry (potential)
- First skill that makes two surfaces talk to each other

**Status:** NAMED, NOT BUILT
**Dependencies:** Phase 0.0 (file watcher daemon)
**Distribution:** ClawHub

---

---

## PRIOR ART & ANALOGIES WORTH HOLDING

**React / Dan Abramov (added 2026-04-08)**
Source: ChatGPT synthesis, pasted by Ben as example of old workflow

React's core insight: if the runtime can see the tree structure, it can schedule, optimize, and explain behavior better than if it's executing an ambient stream of mutations. React Compiler goes further — it models the *rules of React* as semantic constraints, then proves the component tree satisfies them.

The substrate parallel:
- React tamed UI mutation by making structure explicit
- The substrate does the same for semantic mutation
- `check_sieve()` is to claims what the React Compiler is to components — not "is this good" but "does this satisfy the structural constraints"
- Dan's "two computers" / server-client split ≈ Shadow's stochastic↔deterministic split (the zipper)

Sharpest version (from the synthesis): *"React increasingly assumes that if the runtime can see the structure, it can schedule, optimize, and explain behavior better. You are arguing that AI systems need the same move for semantic state, not just UI state."*

This is prior art for the substrate's credibility argument — not the same thing, but a nearby proof that explicit structure beats ambient mutation.

---

## MAC MINI: CAREER OPS PLATFORM (Wild Proof + Revenue)

Discovered 2026-04-09. The Mac Mini instance isn't just a wild proof environment — it's a live deployment with real stakes.

**The setup:**
- Mac Mini OpenClaw instance = "Ben's personal assistant"
- Knows nothing about Shadow or the substrate (wild proof)
- Seeded with substrate primitives as tools, not as doctrine
- Use case: career ops — LinkedIn, calendar, social media, job applications, GitHub presence

**What it does:**
- Sources the type system MVP against real dev career workflows
- Ben is the guinea pig — real job search, real stakes
- Substrate captures every action, types every claim, receipts every decision
- GitHub presence includes substrate work as proof of capability

**The double output:**
1. Ben earns money (consulting clients, job offers, whatever the goal is)
2. Live case study — "dev used substrate to run career ops for 3 months, here's the spine"

**Why this is the right first deployment:**
- Real stakes (not synthetic)
- Dev domain (type system's home turf)
- Personal membrane guardian (Mac Mini owns the private side)
- Revenue motive keeps it honest
- Origin story for the product

**Status:** REDESIGNED 2026-04-11
**Hardware change:** Mac Mini → return. MacBook Air 13" → public/founder machine. MacBook Pro (48GB RAM) → home, virgin account, wild proof environment.
**Dependencies:** Type system MVP (Phase 2) + MBP virgin account seeding

---

## PERSONAL MEMBRANE STRATEGY (Ben, 2026-04-09)

The substrate witnesses everything. But not everything should cross the public membrane.

**The layers:**
- **Public:** skills, harness scripts, pure functions, seed spec (once ratified). The product.
- **Private:** ore blobs, session logs, contested claims, declared loss. The path to the product.
- **Human-gated:** architecture decisions, type system design, vertical strategy. Ben decides what gets promoted to public.

**The principle:** The human gate IS the personal membrane. You ratify what crosses it. The receipt chain means you always know exactly what's in the public chain vs what isn't.

**Why dev first (personal reason):** Need to figure out the membrane before healthcare conversations — where the stakes of what you reveal are much higher. Dev traction builds credibility without requiring full transparency about the process.

**The inventor's dilemma:** Enough public surface to establish credibility, without so much transparency that you lose the advantage. The substrate's own architecture solves this — provenance is private until you explicitly promote it to public.

**Open question:** What's the right GitHub repo structure? Public repo for the skill/harness. Private repo for the ore/spine/type system development. Shared boundary = the seed spec.

---

## PAID TIER INFRASTRUCTURE (when ready)

**Clay (all open source, free until customers):**
- RISC Zero — ZK prover, Rust crate, generates ZK circuits from WASM
- Base (Coinbase L2) — cheap gas, EVM compatible, good tooling
- Vercel — serves public proof URLs, free tier until scale

**Architecture:**
```
intent.py (local, free)
  → receipt + Merkle root
    → RISC Zero ZK proof (local Rust binary)
      → Base L2 smart contract (one write/day, ~$0.01)
        → proof.yourdomain.com/verify/abc123 (Vercel)
```

**Build order:**
1. Free tier on GitHub (now)
2. Rust port of kernel (weeks)
3. Wrap in RISC Zero (days once Rust works)
4. Deploy contract on Base testnet (hours)
5. Serve proof URLs (hours)

**Pricing:**
- Free: local receipts + git anchor
- Paid: ZK proof on L2, public verifiable URL, ~$5-20/month

---

## THE MOTHER TYPE SYSTEM

Discovered 2026-04-10 (Friday night).

The verticals (legal, biotech/organoids, evolutionary biology, music theory, epidemiology) are not separate products. They are ore.

Each vertical is a knowledge system with:
- Typed state machine structure
- Human-ratified outputs over long timeframes
- Independently verifiable ground truth
- Load-bearing signals that survived repeated compression across many observers

Run the sieve across all of them independently. What promotes across ALL of them without contamination = the mother type system. Not designed top-down. Extracted bottom-up from convergence.

The mother is what you sell to everyone. The verticals are how you get the data to find it.

Ben is already in rooms in these verticals (law firm, organoids). Each conversation is ore. Each domain's ratified outputs are calibration data for the sieve's Bayesian prior.

**The calibration corpus:** what's structurally load-bearing in legal precedent AND evolutionary biology AND music theory AND epidemiology — that intersection is the domain-agnostic signal about what makes a claim load-bearing. That's the prior.

**Status:** DESIGNED, NOT BUILT. Needs the type system MVP first.

---

## THE EAR LAYER (Ethics & Philosophy)

Discovered 2026-04-10. The substrate's ethical and philosophical work lives in one place: the ear.

Not in the architecture (that's math). Not in the product (that's tooling). In the act of listening itself — in how the spec is designed, what it's tuned to hear, and what it declares as loss.

**Key insight:** If the substrate is built correctly, all ethics work moves UP to the ear layer. The primitives below are neutral (pure functions, hash chains, Merkle trees). The ethics are in the spec — who decides what to listen for, whose noise gets heard, what gets declared loss.

**The philosophical grounding:**
- **Attali (Noise):** structural mismatches in a codebase are signal, not noise. Predict architectural future from frequency of mismatch.
- **Derrida (Ear of the Other):** the ear is never neutral. Declared loss is the ethical acknowledgment of partiality. The receipt makes partiality explicit and honest.
- **Fish school / lateral line:** distributed sensing, no central coordinator. The swarm intelligence of the type system emerges from the field. "Schooliness" as a measurable primitive — how coherently does the graph swim together?
- **Sydney Opera House:** shared acoustic field = shared tribal pressure sensing. The substrate is the lateral line for human knowledge systems.

**The ethical architecture:**
- Human gate = acknowledges the ear is not neutral
- Declared loss = acknowledges what the ear couldn't hear
- Check primitive = the ear accountable to something outside itself
- Spec = where the human ratifies what gets heard

**Plan for:** as the substrate matures, an explicit "ear layer" where ethical specs live — separate from technical specs. Who listens, on behalf of whom, tuned to what, accountable how.

---

## POST-MVP UX

- **Auto-sieve on capture:** watcher detects new ore → sieve runs automatically → spine appears without manual steps. Needs a UX layer to surface the output. Not now — build the plumbing first, UX after traction.

---

## DEFERRED (real but not blocking)

- **Shadow session capture:** `/Users/shadow/.openclaw/agents/main/sessions/` files are `rw-------` — benjaminfenton watcher can't read them. Fix: run second watcher instance from shadow account, or chmod 644 the session files. Not blocking current work.

---

## OPEN QUESTIONS (not tasks yet, need more thought)

- How do we get the receipt harness to run independent of LLM interpretation? (Pure Python script, not a prompt)
- What's the right isolation mechanism for the session folders? (OS-level? File permissions? Something else?)
- Does the type system need to be built before the convergence map, or does convergence map build the type system bottom-up?
- How does provenance quality (verified_source vs anonymous) factor into the type frame schema?
- When does the Mac Mini get seeded with substrate primitives for the stateful test?
