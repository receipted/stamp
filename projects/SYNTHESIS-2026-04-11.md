# Synthesis — 2026-04-11
# What we learned, what it changes, what's next

---

## WHAT HAPPENED THIS WEEK (Apr 7-11)

Three days of deep work across two major sessions:

**Session 1 (Apr 7-8):** Architecture audit, roadmap creation, watcher built and tested, receipt harness proven, sieve running on real ore, graph-lab wired into promote(), seed spec written, first sieve runs on Claude Code sessions.

**Session 2 (Apr 9-11):** AST-based intent extraction built (parse_function_to_claims, parse_function_to_graph), guarantee type created, dimension map for complementarity, intent.py CLI proven on stranger's code (httpx), 12 corpus runs across knowledge domains establishing mother types, Opus architecture crit run.

---

## THE CORPUS RUNS — WHAT THEY PROVED (Apr 10-11, Shadow + Opus)

Ran the sieve over 12 independent knowledge systems:
- Lean mathematics, Ayurveda, Darwin, Vedic/Upanishads
- Brown v Board, Roe v Wade, Declaration + Constitution
- Finance (Fed + Apple), Einstein 1905, Ethics (Trolley + Rawls + Nozick)
- Ship of Theseus, Riemann Hypothesis

**What converged across all 12 — the mother types:**

1. **CONTRACT** — what this thing promises (theorems, doshas, legal holdings, function signatures)
2. **CONSTRAINT** — what cannot be violated (assert_not_exists, physician harm, Due Process, no IO)
3. **UNCERTAINTY** — where the system declares its limits (exists clauses, prakruti, framers' intent, geological record)
4. **RELATION** — how claims connect (subset/iff, samanya/vishesha, Sweatt precedent, call edges)
5. **WITNESS** — who observed this and when (guru lineage, Darwin 1859, Warren unanimous, signed by 56 delegates)

**Emerging candidates from corpus evidence:**
- **SEQUENCE** — ordered transitions (trimester framework, panchamahabhuta, evolutionary stages)
- **CONVERGENCE** — claims approaching same truth from different angles (Vedic corpus, physics)
- **APOPHASIS** — what can only be described by negation (neti neti = assert_not_exists)

**Key finding:** WITNESS is the type that distinguishes empirical knowledge from formal. Lean doesn't need it — the proof IS the witness. Ayurveda and law do. Code is missing it almost entirely. This is what the substrate adds.

---

## THE OPUS CRIT — KEY FINDINGS (Apr 11, Crit v1, CRIT-TAG: surface-review-2026-04-11-v1)

Source: ran Opus against the full codebase (epistemic_tagger.py fully read, 12 hidden room files surveyed, kernel.py + sieve.py + binding.py + record.py reviewed)

### Finding 1: Epistemic tagger IS the type system seed (confidence: 0.9)

The epistemic_tagger.py (442 lines) already exists and classifies relay turns by:
- belief_formed → CONTRACT
- tension_detected → CONSTRAINT violation
- question_posed → UNCERTAINTY
- evidence_cited → WITNESS
- belief_revised, tension_resolved → SEQUENCE (transition events)

These are the mother types in different vocabulary. The tagger was built by a prior session that never knew about the mother type work. They independently arrived at the same structure.

**Implication:** Don't build a new type system from scratch. Wire epistemic_tagger.py into the sieve as a pre-pass classifier. Replace keyword matching with epistemic event classification.

### Finding 2: 5 hidden rooms are load-bearing (confidence: 0.85)

| File | What it is | Priority |
|---|---|---|
| epistemic_tagger.py | Type system seed | NOW |
| coalescence.py | Promoted knowledge commitment (the spec primitive) | Phase 1 |
| grounding.py | Evidence grounding scorer (confidence signal for promote()) | Phase 1 |
| consensus.py | Multi-model convergence detector (automates CONVERGENCE type) | Phase 2 |
| reflexes.py | Self-healing structural reflex engine (security layer) | Phase 2 |

**Implication:** Less to build than we thought. These rooms exist. Connect the doors.

### Finding 3: Architecture status (confidence: 0.85)

Working end-to-end (~30%):
- kernel.py → sieve.py → promote() / check_sieve()
- record.py → claims.py → ore intake
- browser extension → /record/ingest
- intent.py → AST-based code analysis

Orphaned rooms (~70%):
- graph-lab relevance NOT wired into production promote()
- type-lab inference rules NOT imported by anything
- coalescence, consensus, coagulation, reflexes, facilitation, parity, reflexivity — all designed, none connected

### Finding 4: Security fix is 8 lines (confidence: 0.9)

Add provenance gate at start of promote():
```python
TRUSTED_SOURCE_PREFIXES = ("human:", "system:", "agent:")
for c in claims:
    source = c.get("source", "")
    if not any(source.startswith(p) for p in TRUSTED_SOURCE_PREFIXES):
        loss.append({"claim_text": c.get("text",""), "reason": f"untrusted source: {source}", "rule_applied": "provenance_gate"})
        continue
    reclassified.append(c)
```

This closes 4 of 8 integrity-lab attack scenarios before the Rust port.

### Finding 5: Law firm MVP is real and near-term (confidence: 0.8)

**The product:** Browser extension captures AI-assisted legal research sessions → sieve classifies claims by type → receipted audit report → attached to matter file.

**The problem it solves:** Law firms using Claude/GPT for research have zero audit trail. When AI hallucinates a citation (Mata v. Avianca), the firm can't prove they caught it.

**The output:** Every AI claim typed (fact/observation/hypothesis/guarantee), confidence scored, hash-linked receipt chain, attorney sign-off recorded.

**Price:** $500/month per attorney. $5k/month for 10-attorney firm.

**Timeline:** 4-6 weeks. Week 1-2: add claude.ai to extension, wire to local sieve, produce typed report. Week 3-4: receipt chain. Week 5-6: test with one attorney.

**What it doesn't require:** Rust, blockchain, ZK, full type system, Shape, or any long-term architecture.

---

## HOW THIS CHANGES THE ROADMAP

### What accelerates:

**Type system:** Instead of building from scratch, wire epistemic_tagger.py as the sieve pre-pass. This is weeks of work, not months.

**Hidden rooms:** coalescence.py and grounding.py can be connected immediately. They're pure or near-pure functions that slot into the existing pipeline.

**Law firm path:** The browser extension already exists (95% built). Adding claude.ai and routing to local sieve is days, not weeks.

### What stays the same:

- Gate sequence (ore → sieve proven → spec → graph → type → check)
- The mother types as the grounding corpus
- Rust port as the long-term path to HFT, WASM, and ZK
- The semantic ticker tape as the finance vertical
- Mac Mini → MBP virgin account as the wild proof environment

### What was wrong or needs updating:

**Wrong:** We were planning to build a new type system from scratch. The epistemic tagger IS the type system. We extend it, we don't replace it.

**Updated:** The "no new rooms" rule still holds — but we now know there are connected rooms we missed (epistemic_tagger, coalescence, grounding). The rule becomes "connect existing rooms before building new ones."

**New constraint:** Context window is at 52% and growing. We should start a fresh session before hitting 80% to avoid compaction loss.

---

## UPDATED PRIORITY ORDER

### This week (highest leverage, lowest build cost):
1. **Wire epistemic_tagger into sieve** — pre-pass classifier replaces keyword matching. 1-2 days.
2. **8-line provenance gate** — closes 4 attack scenarios. 30 minutes.
3. **Add claude.ai to browser extension** — freemium capture layer complete. 1 hour.

### Next 2 weeks:
4. **Wire grounding.py into promote()** — confidence scores become evidence-grounded
5. **Law firm audit report format** — typed claims + receipt chain in a format attorneys recognize
6. **Test with law firm contact** — real feedback before building more

### Next month:
7. **Extend epistemic_tagger** with RELATION detection (currently missing)
8. **Wire consensus.py** — multi-model CONVERGENCE becomes automated
9. **GitHub repo** — intent.py + extension + README, freemium launch

### After traction:
10. **Rust port of kernel** — unlocks HFT, WASM, ZK, enterprise
11. **MBP virgin account** — wild proof environment, career ops platform
12. **Mac Mini return** — already decided

---

## OPEN QUESTIONS (need more thought, not tasks yet)

- Is the freemium model (open source + key for HumanClaim) the right structure, or is the extension itself the product?
- The provenance typing problem: session token as witness token is good enough for now, but what's the long-term answer that doesn't reduce the human to their credential?
- Music theory corpus still unrun — Bach WTC as final mother type evidence before publishing the taxonomy
- The model crit format — where do crits live and how do we diff them? (Opus proposed: workspace/projects/crits/YYYY-MM-DD.crit.json)

---

## SOURCES

- Shadow + Ben sessions, Apr 7-11 (this Telegram thread, full ore in /Users/Shared/sidecar-ore/)
- Opus crit v1, Apr 11 (CRIT-TAG: surface-review-2026-04-11-v1) — saved in session
- 12 corpus sieve runs (workspace/projects/corpus-runs/2026-04-11-mother-type-evidence.md)
- Mother type system doc (workspace/projects/mother-type-system.md)
- Domain corpora map (workspace/projects/domain-corpora-map.md)
- Knowledge system overlays (workspace/projects/knowledge-system-overlays.md)
- ROADMAP.md (workspace/projects/ROADMAP.md)
- PUNCHLIST.md (workspace/projects/PUNCHLIST.md)
