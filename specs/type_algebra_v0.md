# Type Algebra v0 — Compositional Algebra of Governance Forms
# Source: GPT-5.2, 2026-04-14
# Context: Post-basecamp, pre-Week 2 sprint

---

## The Core Idea

Don't treat the five mother types as a flat enum. Treat them as **composable governance facets with a normal-form primary kind.**

## Three Orthogonal Axes

```
TypedReceipt = KindExpr × EvidenceGrade × Custody
```

- **KindExpr** — the semantic kind or combination of kinds
- **EvidenceGrade** — how well-supported it is
- **Custody** — how cleanly chained and verified it is

A thing can be a CONTRACT with weak evidence. A thing can be a RELATION with strong witness and full custody. A thing can be UNCERTAINTY without being a weak or broken object.

## 1. Composable Kind Expressions

Base kinds:
```
K ::= CONTRACT | CONSTRAINT | UNCERTAINTY | RELATION | WITNESS
```

Composition:
```
KindExpr ::= K
           | K ⊗ K       (simultaneous facets)
           | K ⊕ K       (unresolved alternative)
           | ref(K)      (reference to another typed object of kind K)
```

Examples:
```
CONTRACT ⊗ WITNESS                     — a witnessed contract
RELATION ⊗ UNCERTAINTY                 — an uncertain relation
CONSTRAINT ⊗ WITNESS ⊗ RELATION        — a witnessed constrained relation
CONTRACT ⊕ RELATION                    — unresolved: could be either
```

## 2. Typed Constructors with Payload

### CONTRACT
```
CONTRACT(antecedent, consequent, modality, scope)
```
Modalities: promise, rule, obligation, prediction

### CONSTRAINT
```
CONSTRAINT(subject, invariant, polarity, scope)
```
Polarity: require, forbid, bound

### UNCERTAINTY
```
UNCERTAINTY(target, mode, reason, scope)
```
Modes: missing, ambiguous, conflicted, deferred, unobservable, underspecified

### RELATION
```
RELATION(left, rel, right, direction, scope)
```
Relations: supports, attacks, depends_on, answers, etc.

### WITNESS
```
WITNESS(target, source, authority, observed_at, basis, custody_ref)
```
Basis: observed, quoted, computed, imported, attested

## 3. Evidence Grade (separate axis)

```
G ::= provisional | witnessed | corroborated | ratified
```

- provisional — typed but not yet strongly supported
- witnessed — at least one admissible witness exists
- corroborated — multiple independent supports align
- ratified — accepted by governance authority

## 4. Custody (separate axis)

```
C ::= local | chained | merklized | zk_proved | anchored
```

This answers not "is it true?" but "can I verify the lineage?"

## 5. Normal Form

Every stamped object normalizes to:
```
TypedReceipt = {
  subject,
  kind: Primary ⊗ Facets*,
  evidence_grade,
  custody,
  parents
}
```

Where Primary is one of the five, Facets* are zero or more attached kinds.

Example:
```
Primary: CONTRACT
Facets:  [WITNESS, CONSTRAINT]
Grade:   corroborated
Custody: anchored
Parents: [r12, r18]
```

## 6. Composition Laws

### Law 1: Witness does not change semantic kind
```
K ⊗ WITNESS ≠ WITNESS
```
A witnessed contract is still a contract.

### Law 2: Uncertainty does not erase kind
```
K ⊗ UNCERTAINTY ≠ UNCERTAINTY
```
An uncertain relation is still a relation. Stops uncertainty from becoming a trash can.

### Law 3: Constraints accumulate conjunctively
```
CONSTRAINT(p) ⊗ CONSTRAINT(q) → CONSTRAINT(p ∧ q)
```

### Law 4: Relations compose only when semantics allow
```
RELATION(a, depends_on, b) ⊗ RELATION(b, depends_on, c) → RELATION(a, depends_on+, c)
```
Only for relations declared transitive.

### Law 5: Conflicts remain visible
```
CONTRACT(A → B) ⊗ CONSTRAINT(not B) → CONTRACT ⊗ CONSTRAINT ⊗ UNCERTAINTY(conflicted)
```
Conflict does not collapse silently.

### Law 6: Witness raises grade, not rewrite meaning
```
grade(provisional) + admissible_witness → witnessed
grade(witnessed) + independent_witness → corroborated
```
Kind stays the same.

## 7. Canonical Operators

| Operator | Signature | Meaning |
|---|---|---|
| ⊗ | KindExpr × KindExpr → KindExpr | Both facets apply simultaneously |
| ⊕ | KindExpr × KindExpr → KindExpr | Unresolved alternative |
| ⇒ | TypedReceipt × Transform → TypedReceipt | Derivation through a transform |
| attach_witness | KindExpr × WitnessPayload → KindExpr | K ⊗ WITNESS(w) |
| mark_uncertain | KindExpr × UncertaintyPayload → KindExpr | K ⊗ UNCERTAINTY(u) |

## 8. Minimal Formal Shape

```
Receipt r ::= {
  in_hash,
  fn_hash,
  out_hash,
  parents,
  kind : P ⊗ F* | P ⊕ P,
  grade : G,
  custody : C
}

P ∈ {CONTRACT, CONSTRAINT, RELATION, UNCERTAINTY, WITNESS}
F ⊆ {CONTRACT, CONSTRAINT, RELATION, UNCERTAINTY, WITNESS}
G ∈ {provisional, witnessed, corroborated, ratified}
C ∈ {local, chained, merklized, zk_proved, anchored}
```

## 9. WITNESS Has a Dual Role

WITNESS is both:
- A base kind in its own right (when the object is literally a provenance claim)
- An attachable facet on other kinds (when witnessing a contract, relation, etc.)

That dual role is correct and useful.

## 10. Relationship to Current Implementation

The current TypedUnit v0 in `mother_types.py` uses `mother_type` as a flat enum with `subtype` for refinement. This algebra extends it:

| Current | Algebra |
|---|---|
| `mother_type: "CONTRACT"` | `kind: CONTRACT` (Primary) |
| `subtype: "determinism_guarantee"` | Constructor payload: `CONTRACT(pure_fn, same_output, guarantee, fn_scope)` |
| `witness_refs: [wit_id]` | `⊗ WITNESS(target, source, authority, ...)` |
| `binding_tier: "observed"` | `grade: provisional` |
| `confidence: 0.8` | Part of evidence_grade computation |
| — (not yet) | `custody: chained` |
| — (not yet) | `⊗` / `⊕` composition |

### Migration Path

1. Current v0 is sufficient for May 1st demo
2. The algebra becomes the v1 spec after the demo proves the primitive works
3. Composition (`⊗`, `⊕`) is the v2 move when cross-domain use cases demand it
4. Constructor payloads are v2-v3 — needed when the type system has to reason, not just label

---

## The Strongest Line

> A compositional algebra of governance forms.

Not "type system." Not "ontology." **An algebra of governance forms** — composable, witnessable, receipted.
