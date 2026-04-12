# Mother Type Definitions
# Formal definitions with reasoning for each type in the epistemic governance type system
# Date: 2026-04-12
# Evidence: 13 corpus runs (Lean, Ayurveda, Darwin, Vedic, Founding Docs, Finance, 
#           Einstein, Ethics, Ship of Theseus, Riemann, Crypto, Music Theory, Epidemiology)

---

## What a Type Is

A type in this system is not a label. It is a structural role — the function a claim plays
in maintaining the integrity of a knowledge system over time.

Every type answers a different question about a claim:
- What does this claim promise?
- What does it prohibit?
- What does it leave open?
- How does it connect to other claims?
- Who stands behind it?

A knowledge system that is missing any one of these five properties is structurally incomplete.
It may still be useful, but it will fail in predictable ways.

---

## The Primitive: Turn

Before defining the types, the atomic unit:

**A Turn is a receipted epistemic event produced by a specific actor at a specific time,
linked to what came before.**

```
Turn {
  actor:     who produced this (human | model_id | institution)
  content:   what was said, decided, or produced
  timestamp: when
  prev_hash: cryptographic link to previous turn
  receipt:   hash of all the above — proves this turn happened as recorded
}
```

Every claim in the type system is extracted from a Turn. The Turn is what gives a claim
its provenance — the moment it entered the world, attributed to someone, chained to
the sequence of events that preceded it.

"Take your turn" means: produce a receipted epistemic event.
"Wait for your turn" means: the chain determines sequence, not the actor.
"It's not your turn" means: the gate rejects the claim that lacks a valid receipt.

---

## Type 1: CONTRACT

**Definition:** A CONTRACT claim states what this system, function, or actor promises —
the conditions under which a specific output follows from a specific input.

**Formal statement:** If A then B. Given X, expect Y. Under conditions P, result Q holds.

**Why it's irreducible:** Without CONTRACT, a knowledge system makes no falsifiable
commitments. It can describe, observe, and opine — but nothing can be verified or refuted.
A system with no CONTRACT claims is a collection of assertions with no accountability.

**The failure mode:** A medical AI with no CONTRACT claims ("given these symptoms, this
diagnosis") cannot be held accountable for wrong outputs. It can always say "I only
suggested." CONTRACT is what makes suggestion into commitment.

**Structural property:** CONTRACT claims are the load-bearing nodes. Remove them and the
rest of the system collapses into opinion. They are what the sieve promotes first.

**Evidence across corpora:**
- Lean: theorems (`if A then B`, function signatures)
- Ayurveda: dosha type system (given this constitution, this treatment)
- Darwin: variation → preservation (profitable variation → individual survives)
- Crypto: electronic coin = chain of digital signatures
- Epidemiology: R0 definition (this input produces this output)
- Einstein: E = mc² (mass and energy are equivalent)

**Turn connection:** CONTRACT is a property of a single Turn — the commitment that Turn
makes about what will hold. It is internal to the Turn.

---

## Type 2: CONSTRAINT

**Definition:** A CONSTRAINT claim states what cannot be true simultaneously, what cannot
be done, or what must hold as an invariant regardless of other conditions.

**Formal statement:** NOT (A and B). X cannot exceed Y. Under any conditions, P must hold.

**Why it's irreducible:** Without CONSTRAINT, a knowledge system is unclosed — anything
is possible. CONTRACTs tell you what will happen; CONSTRAINTs tell you what cannot happen.
You need both to define the boundaries of a system.

**The failure mode:** The Linux mm/ kernel had implicit CONSTRAINTs (reference counts must
balance, locks must be held in order) that were never formally stated. The result: 30 years
of security bugs from people violating constraints nobody wrote down. Without explicit
CONSTRAINT, violations are invisible until they cause catastrophic failure.

**Structural property:** CONSTRAINT claims are the walls of the system. They define what
is structurally impossible rather than merely unlikely. The sieve puts them in loss when
they are violated — a CONSTRAINT failure is a critical finding, not a suggestion.

**Evidence across corpora:**
- Lean: `assert_not_exists` (this structure cannot exist in this module)
- Ayurveda: physician without knowledge causes harm (cannot be bypassed by intention)
- Darwin: natural selection cannot produce adaptation exclusively for another species
- Crypto: attacker must redo all proof-of-work (cannot shortcut the chain)
- Constitution: Congress shall make no law... (absolute prohibition)
- Music theory: parallel fifths are forbidden in classical counterpoint

**Turn connection:** CONSTRAINT is a property of the relationship between Turns —
specifically, what one Turn cannot do given what previous Turns have established.

---

## Type 3: UNCERTAINTY

**Definition:** An UNCERTAINTY claim formally declares the limits of what is known —
where the system acknowledges it cannot produce a determinate answer.

**Formal statement:** X remains unknown. The answer to Q is not yet determined.
Both A and B are possible under current evidence.

**Why it's irreducible:** Without UNCERTAINTY, a knowledge system is dishonest. It claims
more than it can prove. The declaration of uncertainty is not weakness — it is a structural
commitment to honesty about the epistemic state. A knowledge system that has no UNCERTAINTY
claims is lying.

**The failure mode:** The Riemann Hypothesis has never been proven. A mathematical system
that treated it as proven would cascade false theorems through everything that depends on
it. UNCERTAINTY claims protect downstream reasoning from building on unproven foundations.

**The Nasadiya Sukta test:** The Rigveda's creation hymn ends with "perhaps He does not
know." That is the most structurally honest UNCERTAINTY claim in human history. It is also
the claim the sieve promoted — because honesty about the limits of knowledge is load-bearing
in any system that claims to be rigorous.

**Structural property:** UNCERTAINTY claims are the declared gaps. They are not failures —
they are where honest systems mark the frontier. The sieve treats them as first-class
outputs, not as defects to be resolved.

**Evidence across corpora:**
- Lean: `exists` claims (there exists an X such that...)
- Ayurveda: prakruti modifies universal rules (individual variation creates uncertainty)
- Darwin: geological record is imperfect (uncertainty about the past)
- Riemann Hypothesis: the zeros may be undecidable within standard axioms
- Epidemiology: immunity wanes — duration unknown for novel pathogens

**Turn connection:** UNCERTAINTY is declared within a single Turn — the actor marks the
limit of what they can claim in this moment.

---

## Type 4: RELATION

**Definition:** A RELATION claim states how two or more claims, entities, or events are
structurally connected — supports, attacks, elaborates, precedes, depends-on.

**Formal statement:** A supports B. C attacks D. E must precede F. G depends on H.

**Why it's irreducible:** Without RELATION, claims are isolated — each one stands alone
with no structural connection to others. A knowledge system without RELATION is a bag of
facts, not a graph. You cannot reason about causation, dependency, or argument structure
without it.

**The failure mode:** Crypto proved value moved between addresses — but cannot prove the
RELATION between the parties' intent and the transaction. Was the transfer voluntary?
Was it informed? The blockchain records the event but not the epistemic relationship
between the actors. RELATION is what makes a sequence of events into a narrative.

**Structural property:** RELATION claims are the edges in the argument graph. They are
what the graph-lab BFS relevance scoring traverses. A claim that is highly connected via
RELATION edges is structurally load-bearing even if it is lexically unrelated to the topic.

**Evidence across corpora:**
- Lean: `subset`, `iff`, `implies` (typed logical relations)
- Ayurveda: samanya/vishesha (similarity increases, dissimilarity decreases)
- Legal: Sweatt v. Painter establishes intangible inequalities matter (precedent relation)
- Epidemiology: serial interval determines how fast interventions must be deployed
- Music theory: modulation connects keys through pivot chords

**Turn connection:** RELATION exists between Turns — it is the edge that connects what
one actor said to what another said, or what an earlier Turn established to what a later
Turn depends on.

---

## Type 5: WITNESS

**Definition:** A WITNESS claim establishes provenance — who produced this claim, when,
under what authority, and with what standing to make the assertion.

**Formal statement:** Produced by X at time T. Ratified by authority Y. Observed at
location L under conditions C.

**Why it's irreducible:** Without WITNESS, claims are anonymous — they cannot be
attributed, verified, or challenged. The WITNESS type is what transforms an observation
into evidence. A medical finding without a WITNESS is anecdote. A legal ruling without
a WITNESS is opinion. A scientific result without a WITNESS is not reproducible.

**The key insight:** WITNESS is the type that distinguishes empirical knowledge systems
from formal ones. Lean mathematics has no WITNESS type — the proof IS the witness, the
logic stands without attribution. But every empirical system (medicine, law, science,
journalism) requires explicit WITNESS because the authority of the claim depends on who
made it and under what conditions.

**The failure mode:** AI systems produce outputs without WITNESS — there is no record
of which model, which version, which inputs, which context produced the output. The result
is that AI outputs are structurally unverifiable: you cannot distinguish a hallucination
from a correct answer because neither has a WITNESS that can be independently checked.
The turn chain is the WITNESS primitive for AI outputs.

**Structural property:** WITNESS claims are the provenance anchors. They are what the
receipt chain preserves. The sieve always promotes WITNESS claims — they are load-bearing
regardless of content because they establish the epistemic status of everything else.

**Evidence across corpora:**
- Ayurveda: guru-shishya parampara (who transmitted this knowledge, through what lineage)
- Darwin: "Charles Darwin, 1859, On the Origin of Species"
- Legal: "Chief Justice Warren delivered the opinion for a unanimous Court"
- Vedic: "Vyasa compiled, Shankara commented" (lineage of transmission)
- Founding documents: "Signed by 56 delegates to the Continental Congress, July 4 1776"
- Crypto: "Satoshi Nakamoto, Bitcoin whitepaper, October 31 2008"
- Linux: "Linus Torvalds, LKML 2012" (the witness to the complexity)

**Turn connection:** WITNESS is a property of the Turn itself — the actor field IS the
witness. Every Turn is automatically a WITNESS claim about who took that turn.

---

## Why These Five and Not Others

Three candidate types emerged from the corpus runs but did not make it to the mother set:

**SEQUENCE** — ordered transitions in a state machine (trimester framework, panchamahabhuta).
Not a separate type: SEQUENCE is a property of the RELATION between Turns, not a new type.
A sequence is just a chain of RELATIONs with temporal ordering. The turn chain handles this.

**CONVERGENCE** — multiple independent claims approaching the same truth.
Not a separate type: CONVERGENCE is a property of the graph topology — when multiple
RELATION edges from different sources point to the same node, that is convergence.
It is discovered by the sieve, not declared by a type.

**APOPHASIS** — what can only be described by negation (neti neti, assert_not_exists).
Not a separate type: APOPHASIS is a special case of CONSTRAINT — specifically, a CONSTRAINT
that applies universally. "Cannot be described positively" is a constraint on the claim
space itself. The CONSTRAINT type handles this.

---

## The Completeness Argument

A knowledge system is epistemically complete if and only if it can:
1. Make falsifiable commitments (CONTRACT)
2. Define what is impossible (CONSTRAINT)
3. Declare what is unknown (UNCERTAINTY)
4. Map the connections between claims (RELATION)
5. Attribute claims to their sources (WITNESS)

Remove any one and something fails:
- No CONTRACT → unfalsifiable, unaccountable
- No CONSTRAINT → unclosed, anything is permitted
- No UNCERTAINTY → dishonest, overclaims
- No RELATION → unconnected, no argument structure
- No WITNESS → unattributable, unverifiable

The five types are necessary and sufficient for a knowledge system to be both rigorous
and honest. This is the claim. It is grounded in 13 independent corpus runs across domains
that have survived centuries of human use.

---

## The Code Mapping

```python
_CLAIM_DIMENSIONS = {
    "fact":        "contract",     # what it accepts/returns
    "observation": "purpose",      # what it's for (surrogate for contract in natural language)
    "guarantee":   "purity",       # what you can trust about execution (surrogate for witness)
    "hypothesis":  "uncertainty",  # where it hedges
    "constraint":  "constraint",   # what it refuses or guards
}
```

The current code mapping is a surrogate. The production type system should use the five
mother types directly. The surrogates were the path to discovering the mothers — they are
not the destination.
