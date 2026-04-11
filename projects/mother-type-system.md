# The Mother Type System

**Status:** Theoretical. To be uncovered, not designed.
**Method:** Run the sieve across independent knowledge domains. What survives all passes is the mother.

---

## The Hypothesis

There exists a minimal set of irreducible claim types that appear in every human knowledge system that has survived long enough to be considered rigorous. These types are not invented by any domain — they are discovered independently by each one because they reflect something structural about how meaning persists across time and observers.

The sieve is the instrument for uncovering them. The verticals are the ore.

---

## The Domains (ore for the mother)

Each domain has three properties that make it useful:
1. **Typed state machine** — explicit input/output structure
2. **Long-running ratification** — human consensus over time
3. **Independent ground truth** — verifiable without trusting any single actor

| Domain | Type system | Ratification mechanism | Ground truth |
|---|---|---|---|
| Legal precedent | Facts, holdings, dicta, dissents | Stare decisis, appeals courts | Published decisions |
| Evolutionary biology | Traits, selection pressure, fitness, speciation | Peer review, fossil record | Geological stratigraphy |
| Music theory | Tension, resolution, consonance, dissonance | Centuries of performance | What audiences return to |
| Epidemiology | Pathogen, host, transmission, immunity | Outbreak outcomes | Historical mortality data |
| Astrology | Planets, aspects, houses, transits | Centuries of practice | Ephemerides (astronomical) |
| Mathematics | Axioms, theorems, proofs, conjectures | Peer proof verification | Logical consistency |
| Common law | Precedent, statute, ratio decidendi, obiter | Judicial hierarchy | Case outcomes |
| Medicine (Ayurveda) | Doshas, constitution, balance, treatment | Clinical outcomes | Patient records |

---

## What Survives All Passes (candidate mother types)

These are what every domain above independently arrives at:

### 1. CONTRACT
**What it is:** The input/output agreement. What this thing accepts, what it promises to return, under what conditions.

- Legal: the ratio decidendi — what the court actually decided and why
- Biology: the fitness function — what traits survive under what pressures
- Music: the harmonic contract — what tensions must resolve and how
- Code: the function signature + guarantees
- Ayurveda: the treatment protocol — given this constitution, this intervention

**Irreducibility test:** Can you have a knowledge claim without a contract? No. Every claim that persists makes an implicit contract about when it holds.

### 2. CONSTRAINT
**What it is:** What cannot be true simultaneously. The boundary condition. The invariant that must hold.

- Legal: the holding that overrules — what is now excluded from valid argument
- Biology: the viability limit — what trait combinations cannot survive
- Music: the forbidden parallel fifths — what is structurally dissonant
- Code: the precondition, the guard, the assertion
- Ayurveda: the contraindication — what aggravates the imbalance

**Irreducibility test:** Can you have a system without constraints? No. A system with no constraints has no structure.

### 3. UNCERTAINTY
**What it is:** Where the system explicitly hedges. The declared confidence limit. What remains open.

- Legal: the obiter dictum — what the court said but didn't decide
- Biology: the missing link — the gap in the fossil record, acknowledged
- Music: the blue note — the deliberately ambiguous tone
- Code: the Optional return, the hypothesis claim
- Ayurveda: the prakruti variation — individual constitution modifies universal rules

**Irreducibility test:** Can you have a complete knowledge system with no uncertainty? No. Any system that claims zero uncertainty is lying.

### 4. RELATION
**What it is:** How this claim connects to other claims. The edge in the graph. Supports/attacks/elaborates.

- Legal: distinguishes, follows, overrules — explicit relation to prior decisions
- Biology: phylogenetic distance — how far two species are in the tree
- Music: harmonic interval — the relationship between two notes
- Code: calls, imports, depends-on
- Ayurveda: the six tastes and their dosha effects — typed relations between substances

**Irreducibility test:** Can a claim be load-bearing in isolation? No. Load-bearing means something depends on it. Dependency is a relation.

### 5. WITNESS
**What it is:** The provenance. Who observed this, when, under what conditions. The receipt.

- Legal: the court, the date, the jurisdiction — who ratified this
- Biology: the specimen, the location, the date — who found this
- Music: the composer, the first performance — who made this
- Code: the function hash, the commit — what version ran
- Ayurveda: the lineage of teachers — who transmitted this

**Irreducibility test:** Can a claim be trustworthy without a witness? No. A claim with no provenance is just noise.

---

## The Five Mother Types

```
CONTRACT    — what this thing promises
CONSTRAINT  — what cannot be true simultaneously  
UNCERTAINTY — where the system declares its limits
RELATION    — how this connects to other claims
WITNESS     — who observed this and when
```

These map to the current substrate primitives:

| Mother type | Substrate primitive | Claim type |
|---|---|---|
| CONTRACT | kernel.py signature | fact |
| CONSTRAINT | sieve declared loss | constraint |
| UNCERTAINTY | deferred bucket | hypothesis |
| RELATION | graph edges | (structural, not a claim) |
| WITNESS | receipt chain | guarantee |

---

## What This Changes

The current claim types (`fact`, `observation`, `constraint`, `hypothesis`, `guarantee`) are domain-specific approximations of the mother types. They emerged from code analysis. The mother types would replace them with irreducible primitives that work across all domains.

The sieve's topic_context would no longer need keywords — it would need a **mother type spec**: which combination of CONTRACT/CONSTRAINT/UNCERTAINTY/RELATION/WITNESS is load-bearing for this topic?

---

## The Path to Uncovering the Mother

1. Run the sieve over each domain corpus independently
2. Look at what promotes across all five domains without contamination
3. Find the structural invariant — what's in every promoted set
4. That's the mother

The mother isn't in any single domain. It's in the intersection.

---

## What We Can't Know Yet

- Whether five types is the right number (could be three, could be seven)
- Whether the types are truly orthogonal or whether some collapse into others under scrutiny
- Whether "witness" is a type or a meta-property of all types

These are open questions. The sieve will answer them. Not us.
