# Type System v0

**Status:** Draft  
**Date:** 2026-04-14  
**Purpose:** Define the minimum viable type system for the substrate so the root ontology is stable, the first subtype lattice is practical, and the runtime can mint typed, receipted semantic transforms without overfitting to one demo.

## Core Rule

Freeze the root ontology now. Earn the useful granularity through the first real workflow.

That means:

- the mother types are substrate-level and should remain stable
- the first subtype vocabulary should be forced by the MVP wedge
- the system must preserve unknowns, loss, and partial witness instead of forcing false precision

## Goals

- Give the substrate a stable ontological floor
- Define the canonical typed unit that can travel across transforms
- Make witness and authority first-class, not metadata afterthoughts
- Support deterministic inference over typed claims and relations
- Start with a dev-first subtype lattice that is useful immediately
- Preserve room for later domains without redesigning the root

## Non-Goals

- Build the final universal ontology
- Enumerate every future subtype up front
- Replace all existing `claim_role` and `type_key` usage immediately
- Collapse human judgment into automatic typing

## Layer Split

Two layers are intentionally different:

### Stable Now

- mother types
- canonical typed unit shape
- witness model
- relation algebra
- binding tiers
- authority surface
- unknown and loss handling

### Earned Through MVP

- first subtype lattice
- domain-specific witness classes
- relevance heuristics within a wedge
- relation weighting and promotion thresholds
- what counts as "enough witness" for a specific workflow

## 1. Root Ontology

The substrate root ontology is the five mother types:

| Mother Type | Meaning | Guiding question |
|---|---|---|
| `CONTRACT` | A falsifiable promise, interface, or behavioral commitment | What is being asserted as true or expected? |
| `CONSTRAINT` | A structural limit or incompatibility | What cannot be true or happen together? |
| `UNCERTAINTY` | A declared limit, open question, or unresolved gap | What is not yet known or not yet justified? |
| `RELATION` | A meaningful connection between typed units | How does this unit connect to another? |
| `WITNESS` | Provenance, observation, or attestation | Who or what observed this, when, and under what authority? |

These five should be treated as the substrate floor, not a per-domain taxonomy.

## 2. Canonical Typed Unit

The minimum portable unit is a typed claim-like object. The existing `Claim` model is close, but v0 needs a clearer transport shape.

### `TypedUnit v0`

```json
{
  "id": "clm_...",
  "text": "The stamped turn chain is deterministic across runs.",
  "mother_type": "CONTRACT",
  "subtype": "determinism_guarantee",
  "binding_tier": "observed",
  "confidence": 0.82,
  "authority": "system",
  "source_refs": ["snap_...", "turn_..."],
  "witness_refs": ["wit_..."],
  "relation_refs": ["rel_..."],
  "type_key": "dev.determinism.guarantee",
  "claim_role": "guarantee",
  "schema_version": "substrate.typed_unit.v0"
}
```

### Required fields

- `id`
- `text`
- `mother_type`
- `binding_tier`
- `schema_version`

### Strongly recommended fields

- `subtype`
- `confidence`
- `authority`
- `source_refs`
- `witness_refs`
- `relation_refs`

### Field semantics

- `mother_type` answers what kind of thing this is at the substrate layer
- `subtype` answers what kind of thing this is in the current working lattice
- `type_key` is a stable lookup and clustering key, not the ontology itself
- `claim_role` is a compatibility shim for existing Surface behavior and UI
- `authority` records who is entitled to stand behind the unit at its current tier

## 3. Witness Model

The type system is not valid without a witness model. A typed unit without witness discipline becomes narrative rather than substrate.

### `Witness v0`

```json
{
  "id": "wit_...",
  "witness_type": "ast",
  "source_kind": "code",
  "source_ref": "blob_or_snapshot_or_turn_id",
  "observed_at": "2026-04-14T12:00:00Z",
  "observed_by": "kernel.parse_function_to_claims",
  "authority": "system",
  "attested_by": null,
  "schema_version": "substrate.witness.v0"
}
```

### Initial witness classes

- `raw_turn`
- `ore_blob`
- `ast`
- `graph_derivation`
- `test_result`
- `runtime_trace`
- `lockfile`
- `human_review`
- `human_ratification`
- `external_document`

### Witness rules

- A unit may have multiple witnesses
- Witnesses may disagree
- A witness can support a unit without upgrading its binding tier
- A witness must not be silently synthesized from downstream projections

## 4. Relation Algebra

`RELATION` must be explicit enough to compute over. "Connected" is not enough.

### Minimum first-class relations

- `supports`
- `attacks`
- `depends_on`
- `derived_from`
- `specializes`
- `generalizes`
- `precedes`
- `supersedes`
- `ratifies`
- `questions`
- `instantiates`
- `conflicts_with`

### Relation requirements

- Every relation must name a source and target unit
- Every relation may carry confidence
- Every relation may carry witness
- Some relations are directional, some symmetric

### Directionality defaults

- directional: `supports`, `attacks`, `depends_on`, `derived_from`, `precedes`, `supersedes`, `ratifies`, `questions`, `instantiates`
- symmetric: `conflicts_with`

## 5. Binding and Authority

Types alone do not tell us what the system is allowed to rely on.

### Binding tiers

- `observed`
  first capture, extraction, or low-commitment inference
- `proposed`
  corroborated or structured enough to survive local governance
- `ratified`
  explicitly accepted by a remembered authority act

### Authority values

Initial authority values:

- `system`
- `model`
- `human`
- `external_authority`
- `mixed`

### Binding rules

- `observed` does not imply truth, only capture
- `proposed` implies the unit survived at least one meaningful gate
- `ratified` requires an explicit human or designated authority action
- a unit's mother type does not determine its tier
- a unit may be high-confidence but still only `observed`

## 6. Inference Contract

The type system is not just labels. It needs explicit transform rules.

### v0 inference principles

- `WITNESS` can increase support for a unit but does not automatically ratify it
- two `CONTRACT` units in incompatibility may produce a `CONSTRAINT` or an `UNCERTAINTY`, depending on witness quality
- `UNCERTAINTY` must be preserved as first-class output, not treated as failure
- `RELATION` can be inferred only when the transform that inferred it is itself witnessable
- typed output must preserve declared loss where classification or relation is ambiguous

### v0 transform families

- tagger transform: text to epistemic events
- mother-type bridge: epistemic events to typed units
- sieve transform: typed units to promoted, contested, deferred, and loss sets
- compiler and field transforms: typed units to projections

## 7. Unknown and Loss Discipline

False precision is worse than incompleteness.

### Required fallback states

- `unknown_subtype`
- `unclassifiable`
- `insufficient_witness`
- `declared_loss`

### Rules

- if mother type is known but subtype is unclear, keep the mother type and mark subtype unknown
- if witness is weak, preserve the unit at low binding rather than invent stronger certainty
- if no honest mapping exists, declare loss instead of coercing a fit

## 8. Dev-First Subtype Lattice

The first subtype lattice should come from the dev wedge because dev already has strong demand for execution receipts, compatibility proofs, and explainable transforms.

### `CONTRACT` subtypes

- `behavioral_guarantee`
- `interface_promise`
- `determinism_guarantee`
- `compatibility_claim`
- `execution_contract`

### `CONSTRAINT` subtypes

- `version_incompatibility`
- `impurity_boundary`
- `runtime_requirement`
- `ordering_constraint`
- `resource_constraint`

### `UNCERTAINTY` subtypes

- `unverified_path`
- `dynamic_behavior_gap`
- `heuristic_inference`
- `coverage_gap`
- `open_edge_case`

### `RELATION` subtypes

- `calls`
- `wraps`
- `depends_on`
- `derives_from`
- `conflicts_with`
- `narrows`
- `stamps`

### `WITNESS` subtypes

- `ast_evidence`
- `test_evidence`
- `lockfile_evidence`
- `ci_evidence`
- `runtime_trace_evidence`
- `human_review_evidence`

## 9. Mapping to Current Code

This spec is intentionally close to the current code so it can be adopted incrementally.

### Existing modules that already align

- [mother_types.py](/Users/Shared/substrate/src/surface/mother_types.py)
- [epistemic_tagger.py](/Users/Shared/substrate/src/surface/epistemic_tagger.py)
- [sieve.py](/Users/Shared/substrate/src/surface/sieve.py)
- [receipted.py](/Users/Shared/substrate/src/surface/receipted.py)
- [models.py](/Users/Shared/substrate/src/surface/models.py)

### Adoption path

1. Keep existing `claim_type`, `claim_role`, and `type_key` behavior working
2. Add explicit `mother_type` and `subtype` to the generated units
3. Treat `type_key` as the durable clustering key, not the full ontology
4. Add witness objects and refs to every typed output path
5. Only then tighten relation and binding logic

## 10. Implementation Order

### Freeze now

- mother types
- binding tiers
- initial authority values
- minimum relation algebra
- witness object shape

### Build next

- typed unit constructor
- witness constructor
- tagger to mother-type bridge with subtype assignment
- sieve rules that operate on mother types plus dev-first subtypes
- receipts for every typed transform boundary

### Defer

- cross-domain subtype explosion
- healthcare and legal subtype lattices
- deep ontological graph semantics
- final naming of every relation family

## 11. Design Tests

The type system is only good if it passes a few simple tests.

### Closure test

Can every important unit produced in the dev wedge be assigned:

- one mother type
- zero or one subtype
- one binding tier
- at least one witness or declared lack of witness

### Honesty test

When classification is weak, does the system preserve uncertainty instead of overclaiming?

### Portability test

Can another runtime consume the typed unit without needing the original transcript?

### Upgrade test

Can later domains add subtypes without altering the mother types?

## 12. Open Questions

- Should `WITNESS` be modeled as a typed unit, a separate entity, or both?
- Should relation objects themselves carry binding tiers?
- Is `authority` best modeled as a scalar, a set, or a structured contract?
- When a unit has multiple witnesses with different strengths, where should aggregation live?

## 13. Working Rule for v0

The root ontology is discovered once.  
The first useful granularity is earned by the first real workflow.

