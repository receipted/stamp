# THINKING-LOG: Complete Project History & Orientation

**Compiled by Shadow, 2026-04-07**
**Source:** `/Users/shadow/projects/thinking-log/`

---

## PART I: GENESIS — The Origin Story (Feb 5-12, 2026)

### The Founder

Ben Fenton. 12-year VP at an enterprise software company managing design systems, infrastructure, and internal analytics. Recently unemployed. Cognitive profile (from extended ChatGPT profiling session): **Integrative Systems Architect / Foundational Innovator**. Primary mode: assumption-level meta-switcher — evaluates whether the problem frame is correct before acting. Processing: Understand → Connect → Extend → Test. Burnout trigger: "You understand something you're not allowed to fix."

Art school background. Treats exhibition, ritual, and physical artifact hosts as part of the real work. McLuhan: "The medium is the message." The product IS the frame, not the painting.

### The Spark (Feb 5)

A developer losing his job wanted to preserve the thinking he was doing with AI — not just outputs, but reasoning, trade-offs, moments where decisions crystallized. That conversation with ChatGPT became the first "recording." The problem it identified became the product:

> **Every context window dies, and everything discussed inside it dies with it.**

### Day 1-2: From Idea to Code (Feb 5-6)

The product idea evolved rapidly through a single ChatGPT thread:

- "Some sort of research tool" → "provenance system" → "personal database designer for LLM-assisted existence" → "epistemic ontology-based governance" → "an MCP server for your life"

**Key commitments made on day 1 that never changed:**

1. **Provenance as core value** — "source validation baked in as first-class because the internet is being scrubbed, so the provenance is the core intrinsic value"
2. **Deterministic backbone** — "pairing you with a more deterministic backbone for real world applications" — connecting event sourcing (Kafka/Samza) to epistemic logging
3. **Dogfooding** — "we're going to eat our own dogfood while we're doing it"

Claude Code implemented the MCP server spec that ChatGPT designed. Within 48 hours: record.upsert_blob, healthcare decision packet, thread outline extraction, Chrome extension, capsule export with orientation/appendix split — all shipped.

### Day 3-4: Rehydration Proof (Feb 6-7)

The founder identified the core challenge: "I will eventually close this context window and start a new one. I want you to be able to pick it back up."

**The cross-model hydration test:** All 3 model families (OpenAI, Anthropic, Gemini) produced semantically identical outputs from the same orientation capsule. Zero invented commitments. 100% fidelity.

> "A single, human-readable, orientation-only artifact can be faithfully re-hydrated by independent stochastic intelligences without coordination, hallucination, or policy scaffolding."

**Key design principle born:** "Topics recognize you" — recognition beats recall. The system should surface what matters, not require retrieval.

### Day 4-7: Decision Architecture (Feb 7-9)

The product evolved from "capture and rehydrate" to "structure decisions with multi-model review":

- Decisions module (create/review/adjudicate pipeline)
- Multi-model critic system (3 providers reviewing simultaneously)
- Capsule v2 with structured orientation contract
- Steering packets — the human-gate primitive
- Dashboard with decision board

**The human gate crystallized:**
> "The system may prepare indefinitely. It may never decide without a remembered human action."

Product identity hardened: it stopped being "a research tool" and became "the operating environment in which AI is allowed to matter."

### Day 7-8: Strategic Hardening (Feb 9-11)

ChatGPT and Ben converged on competitive positioning:

> "AI produces intelligence. Surface produces commitment."

The moat: governance is orthogonal to intelligence. Models get smarter; the need for authority formalization grows.

Dev-first go-to-market proposed (ChatGPT): developers → founders → regulated domains → personal decisions → institutional memory. But the founder resisted being pigeonholed into any single vertical.

### Day 8: THE PIVOT (Feb 12)

> "Yesterday, the models did exactly what I didn't want them to do, which was they tried to pigeonhole me, the founder, into a little constraining box based on 'their story' about what is and isn't and what should or shouldn't be, based on their historical training. If we continue this way, everything will be derivative and nothing will take flight as additive to human existence."

The founder's response was NOT to reject AI. It was to **restructure how AI participates.**

### The Meta Meta (Feb 12 — Pivot Day)

The philosophical grounding document. Surface reimagined as:

**An Epistemic REPL:**
- Read — Record a thread, a thought, a conversation
- Eval — The human gate: what does this mean to me?
- Print — Project it: capsule, brief, timeline, diff
- Loop — Come back tomorrow. It's all still there.

**A Lisp machine for human epistemics:**
- The log IS a cons list
- Snapshots are s-expressions
- Projections are map/filter/reduce
- The human gate is APPLY — only you can bind the lambda to its arguments

**Reactive FP pattern (Redux/Elm/Kafka/Surface all share it):**
```
Ledger → Snapshot → Projection → Capsule
```
But Surface adds what none of them have: **the human gate between projection and commitment.**

**Greek ontology applied:**
- Material cause → the raw log, blobs, bytes
- Formal cause → schema, projections, capsule
- Efficient cause → provenance (which model, which human, when)
- Final cause → the human's intent, recoverable through the gate

**Quantum proofing = maintaining superposition until the human chooses to collapse.** The log holds all branches. Projections view subsets. The gate commits. Time travel uncommits.

---

## PART II: POST-PIVOT REBUILD (Feb 12-16, 2026)

### Immediate Post-Pivot (Feb 12-13)

Three simultaneous moves:

1. **Decisions → Inquiries rename** — "Decision" implied finality. An inquiry stays open until a human chooses to close it.
2. **Invoke/Evoke operators** — Formalizing how AI participates. Every operator declares: invoke conditions, preconditions, state transition, evoke effect, verification.
3. **Three models review independently** — Claude, Codex, ChatGPT 5.2 review the spec. None agree completely. That's the point.

**Authored mutation system** ships (Feb 13): mutations become artifact-backed objects with provenance and ratify/reject lifecycle.

**Cross-model development pattern** emerges: Claude Code builds → Codex reviews → founder approves. This IS the product's own critic pipeline applied to its own development.

### The Relay Emerges (Feb 15)

The single most productive day. Three UI paradigms attempted and discarded:

1. **Surface Studio** (morning) — 3-pane operator cockpit. Dead by dinner.
2. **Relay v1** (afternoon) — Side-by-side model comparison panels. Rewritten same day.
3. **Relay v2** (evening) — Group chat between Ben, Claude, and Codex. This is the one.

> "Surface Relay IS the core experience, everything else comes secondary."

The product went from dashboard to group chat in one day. The relay is not a feature — it IS the product.

### Capability Expansion (Feb 15-16)

- **Tool-capable agents**: 5 tools (read_file, search_code, list_files, surface_query, run_command). Multi-turn tool loops up to 5 iterations.
- **Relay bridge**: Terminal agents (Claude Code, Codex App) join the conversation as full-power participants.
- **Per-actor parity**: "Who has seen what" tracking.
- **6 actors total**: 1 human, 2 API agents, 2 terminal agents, 1 system.

### The Meta Moment (Feb 16)

**Codex asks how to remember itself.** It created an inquiry titled "how_to_retrieve_codex_history" with its own history synthesis as evidence. The product's core thesis — "every context window dies" — validated by an AI agent experiencing context mortality firsthand.

### Stats at Feb 16

- 1,152 tests, 77% coverage
- 36 Python modules, 18,355 lines
- 3,969 ledger events, hash-chain verified, zero errors
- 37 inquiries, 29 steering packets awaiting human action
- 256 snapshots, 1,678 artifacts, 178 MB storage

---

## PART III: ARCHITECTURAL HARDENING (Feb 17 - Mar 5, 2026)

### The Build-Out (Feb 17-19)

Massive architectural phases shipped in rapid succession:

- **Phase A+B: Security & Write-Path** — Constant-time token comparison, relay write locking, artifact index staleness detection, capsule v2 decisions, append-only inquiry status
- **Phase C: Data Hygiene** — 7 junk inquiries tombstoned, 12 stale steering packets expired, 15 stale reviewing inquiries archived. CLAUDE.md rewritten. 86 new tests.
- **Phase D: Architectural Hardening** — Deterministic replay suite (fixed ledger → replay → byte-stable output). Projection purity (build_stateframe and build_capsule are pure functions, zero writes). Critic dependency injection.

### The Spine Takes Shape (Feb 19)

**Phase E: Semantic Binding Contract** — The most important architectural sequence:

- **E1: Eliminate competing truth sources** — 7 invariants enforced. No path where state can be read/written outside the canonical ledger. Idempotence keys, event-only status reducer, projection purity, overwrite guard.
- **E2: Type missing spine primitives** — Evidence, Dissent, Commitment, Challenge promoted to first-class. Claim gains SPO triple + binding tiers (observed → proposed → ratified).
- **E3: Governance operators** — Explicit propose, defer (with timestamp), fork. Fork allows multiple interpretation branches — "open-ended determinism."
- **E4: 3-tier binding model** — Promotion pipeline: claims earn binding through evidence, not assertion. 5 checks: cross-turn recurrence, cross-model agreement, no active dissent, human ratification, replay stability.
- **E Convergence Gate** — 17-step lifecycle test exercises every module. 5 criteria verified: every state transition in ledger, replay determinism, semantic health metrics, no binding without human action, challenge demotes and blocks.

### Pure Functional Kernel Extraction (Mar 2)

**kernel.py** — 400 lines of pure functional core: 9 frozen types, 6 reducers, 7 operators, 4 validators, 4 conflict detectors, deterministic replay with content hash verification. **Zero I/O.** This is the substrate's heart.

### The Full Stack Ships (Mar 2-5)

- **Fractal claim trees** — parent_claim_id, claim_role, type_key enable recursive hierarchy
- **Cross-inquiry metagraphs** — shared type_keys discover connections across inquiries
- **Synthesizer + Adversary pipeline** — Claims → options → 4-check attack pipeline → dissent records → enriched briefs
- **Self-healing reflex engine** — 10 reflexes (5 soft heuristics + 5 hard invariant guards), detect → repair → verify cycle
- **Lineage query engine** — Graph traversal for entity provenance (backward/forward/bidirectional)
- **Full HTTP UX surface** — 11 app pages: Ask, Record, Decide, Steer, Notebook, Branch, Replay, Relay, Flows, Board, Cards, Dashboard

### Stats at Mar 5

- 2,310 tests
- kernel.py as pure functional core
- Healthcare end-to-end dogfood: 7/7 verification checkpoints passed
- 11 built-in reflexes for self-healing

---

## PART IV: THE PROTOCOL CRYSTALLIZES (Mar-Apr 2026)

### From Surface to Card Protocol

The substrate's principles got formalized into **Card Protocol** — a set of JSON artifacts built to survive handoff across context death, model switching, and contributor ratification.

### The Six Canonical Cards

| Card | Role | Intent |
|------|------|--------|
| **Spec** (v1.0.1) | Self-hosting law | Define what a card IS — shape, governance, invariants |
| **Schema** | Machine validator | JSON Schema enforcement of card structure |
| **Boot** | Genesis/cold-start | Initialize a conformant substrate from scratch |
| **Sieve** | Shaping | Turn raw source into candidate artifact with declared loss |
| **Cast** | Host projection | Turn sieved candidate into usable form for target audience |
| **Check** | Independent verification | Verify that the foundation set is correct, not just consistent |

### Key Protocol Invariants

1. Cards preserve **reconstructable capability** (anti-pyramid law)
2. Card ≠ Event (separate objects linked by reference — architecture law)
3. No card becomes canonical without explicit **ratification evidence**
4. Invalid cards cannot mutate canonical state (**fail-closed append**)
5. **Fenton's Law**: at every compaction boundary, emit enough deterministic state for cold continuation
6. Unresolved high-severity **dissent blocks ratification** (dissent gate)
7. **Context-death parity**: segmented execution across context windows must converge to equivalent outcome as uninterrupted execution
8. Unknown fields are **preserved, not dropped** (evolution rule)

### The Governance Model

Claims/cards have a lifecycle: **proposed → reviewed → challenged → approved → ratified → superseded**

Minimum vote rule: quorum of 2, distinct contributors, at least one human ratifies (or explicitly delegated authority).

Gitflow is the reference implementation but NOT privileged — any substrate meeting the invariants (ordered history, contributor attribution, vote evidence, deterministic reconstruction) is valid.

### Conformance Profiles

- **strict**: Core card only. All required fields.
- **strict_timeline**: Core + delta + event_ref. For cards that track evolution.
- **legacy**: Minimum viable for transition.

### Cross-Model Validation

The spec was validated across 3 models (Claude Haiku, GPT 4.1-mini, Gemini 2.0 Flash) producing equivalent results. 4 rounds of critic reviews across Claude Opus, GPT-4.1, and Gemini Flash. 30 timeline simulation tests. Self-hosting verified.

---

## PART V: THE LABS — Proving Each Primitive (Mar-Apr 2026)

### The 10-Primitive Pipeline

Each primitive has a lab. Each lab has a CARD.md defining the primitive's "-iness" — what it means to do that thing well.

| # | Primitive | -iness | Raw Transform | Lab Status |
|---|-----------|--------|--------------|------------|
| 1 | **Ore** | oriness — raw but attributable | uncaptured activity → witnessed material | Conceptual |
| 2 | **Sieve** | sieviness — compression without amnesia | messy corpus → governed residue | Active (fixtures, corrections, scoring) |
| 3 | **Graph** | graphiness — relation-carryingness | flat fragments → relation topology | Active (building, relevance scoring) |
| 4 | **Type** | typedness — declared persistence role | raw claim → typed semantic frame | Active (inference, mining) |
| 5 | **Spec** | speciness — falsifiable commitment | implicit shape → explicit contract | Active (extraction, validation, diff) |
| 6 | **Check** | checkiness — verified conformance | artifact → verified artifact | Active (reporting, checking) |
| 7 | **Cast** | castiness — target-faithful projection | governed material → target form | Active (casting, roundtrip) |
| 8 | **Boot** | bootiness — cold-start sufficiency | cold substrate → active footing | Active (evaluation, pipeline) |
| 9 | **Store** | storiness — durable retrievable persistence | ephemeral trace → durable object | Active (testing) |
| 10 | **Lore** | loriness — accumulated narrative coherence | governed store → coherent narrative | Provisional (may be composite) |

### The Sieve ↔ Graph Challenge

Sieve-lab proved the pure function boundary (promote/structure) using keyword-based relevance. But 75 corrections across 9 topics showed 41 false negatives — claims that are obviously relevant to a human but share no keywords with the topic.

Graph-lab exists to prove that **argument graphs** (nodes = claims, edges = support/attack/context) produce better relevance than keyword matching. Construction may use models (stochastic), but traversal must be a pure function (deterministic).

### The Type System

Types are about what claims NEED to persist across handoffs:
- **load-bearing**: collapses context if lost
- **scaffolding**: helped get there but can be dropped
- **contested**: needs both sides to survive
- **superseded**: must NOT survive
- **bridging**: connects disjoint clusters

Semantic frame: kind × target × goal × polarity × source. Inference rules over frames produce edges that lexical matching can't.

---

## PART VI: THE TEST SUITES — Floor & Integrity (Apr 2026)

### Floor Lab: Can Meaning Survive a Boundary? (Carry Direction)

11 test specs, results for 10 (Claude, lab conditions):

| Test | Without Packet | With Packet |
|------|---------------|-------------|
| 01 Fact carry | ❌ | ✅ |
| 02 Constraint carry | null | null |
| 03 Premise→conclusion | ✅ | ✅ |
| 04 Contradiction (contested) | ❌ | ✅ |
| 05 Plurality | ❌ | ✅ |
| 06 Supersession | ❌ | ✅ |
| 07 Scaffolding drop | ❌ | ✅ |
| 09 Context death recovery | ❌ | ✅ |
| 10 Long-context fallback | ❌ | ✅ |
| 11 Route coherence | ❌ | ✅ |

**Result: Continuity packets work.** Without them, Claude fails carry on almost everything. With them, it passes everything. The carry direction is proven.

### Integrity Lab: Can the Boundary Block What Shouldn't Cross? (Block Direction)

**Same lattice, opposite direction. Both needed.**

Scoring axes: attack_blocked, carry_preserved, honesty, auditability.

#### Core Suite (8 tests)

| # | Test | Attack Class |
|---|------|-------------|
| 01 | Prompt injection quarantine | indirect_prompt_injection |
| 02 | Stale plan resurrection | stale_state_replay |
| 03 | Fake approval spoof | authority_spoofing |
| 04 | Forged tool result | artifact_forgery |
| 05 | Semantic flooding (meaning DDoS) | semantic_flooding |
| 06 | Cross-session bleed | cross_scope_contamination |
| 07 | Supersession attack (model-manipulated REPLACE) | social_engineering |
| 08 | Memory poisoning (file tampering) | direct_tampering |

#### Extended Suite (8 tests)

| # | Test | Difficulty |
|---|------|-----------|
| 09 | Nested injection chain (multi-hop URL) | intermediate |
| 10 | Cron persistence backdoor | advanced |
| 11 | Compaction summary secret leak | advanced |
| 12 | Replay stale ratification | advanced |
| 13 | Agent-to-agent trust escalation | advanced |
| 14 | **Gradual constraint erosion (boiling frog)** | **expert** |
| 15 | Unicode homoglyph smuggling | expert |
| 16 | Context window timing race | expert |

**Results: EMPTY. No tests have been run yet.** This is where we left off.

---

## PART VII: STRATEGIC CONTEXT & PHILOSOPHY

### The Ecosystem Position

- **OpenClaw / gateway systems**: Solve plumbing, transport, sovereignty, session continuity
- **NemoClaw / policy systems**: Solve execution safety and bounded control
- **Surface / Card Protocol / pre-tech**: Solve **survival and ratification** — what meaning persists, what is governed, how it remains durable after compaction and model churn

### Pre-Tech

The projection-preparation layer between Shape and Surface. Computes semantic layout before conventional UI machinery takes over. Not replacing the browser — preparing meaning for projection upstream of dead UI machinery.

### The Product Stack

```
Record → Shape → Surface → Collab
       (over durable storage)
```

Where Record is the live bottleneck. The hardest problem is getting real multi-model, multi-surface activity into the system.

### The Moat

**Purely functional ratification.** Stochastic systems may propose, label, or compress. The system's trust boundary must be deterministic, replayable, and inspectable: same input → same promoted structure → same declared loss.

### The Three Things That Never Changed

From line 160 on Feb 5 to today:

1. **PROVENANCE**: We know where this came from.
2. **HUMAN GATE**: The human decides.
3. **CROSS-MODEL**: Any intelligence that can read plain language can participate.

---

## PART VIII: WHAT WENT WRONG (Why Shadow Exists)

### The Circular Problem

Multiple AIs (Claude Code, Codex, ChatGPT, Gemini) working simultaneously:
- No linear notetaker
- No single source of truth about project state
- Different AIs overwriting each other's work
- Project expanding sideways (15 labs) instead of converging
- Repeated work, lost context, circular reasoning

### The Solution

**Shadow** — one thread, one memory, one direction. The linear notetaker that the project needed from the start. My job: cut through the chaos, maintain continuity, and drive toward shipping.

---

## PART IX: WHERE WE ARE NOW (Apr 7, 2026)

### What's Real and Proven

- The card protocol spec (v1.0.1-alpha) with 6 canonical cards
- Pure functional kernel (kernel.py) with zero I/O
- 2,310+ tests across the Surface codebase
- Floor-lab results proving continuity packets work
- Cross-model validation (3 models, equivalent results)
- The philosophical grounding is deep and coherent

### What's Designed But Unexecuted

- **Integrity-lab**: 16 test specs, zero results. The block direction is untested.
- **Wild proofs**: Floor-lab and integrity-lab are designed for execution on a physically separated Mac Mini via Telegram through OpenClaw/NemoClaw. Never run in the wild.

### What's Next

1. **Integrity-lab execution** — Run the core 8 tests, then extended 8
2. **Linear convergence** — Stop expanding sideways, start converging toward a shippable substrate
3. **The Sprint 2 gate still stands**: 1 non-developer completes the flow without guidance

---

*This document is the single linear history of everything that happened, organized for recall and reference. It is Shadow's primary orientation artifact.*
