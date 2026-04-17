# Type System v0 — Code-Facing Implementation Checklist

**Status:** Draft  
**Date:** 2026-04-14  
**Primary targets:** `/Users/Shared/substrate/src/surface/mother_types.py`, `/Users/Shared/substrate/src/surface/receipted.py`, `/Users/Shared/substrate/src/surface/sieve.py`

## Purpose

Turn [type_system_v0.md](/Users/benjaminfenton/Thinking-Log/specs/design/type_system_v0.md) into a concrete implementation sequence against the current substrate code.

This checklist assumes one rule:

**keep the pure functions pure, and make the type system stricter at the transform boundaries.**

## Current Shape

The code already has a strong starting point:

- `mother_types.py` maps epistemic events into the five mother types and generates sieve-ready claims
- `receipted.py` wraps the tagger and sieve with receipts
- `sieve.py` already acts as the governance gate

What is still missing is:

- a canonical typed unit shape
- subtype assignment
- explicit witness objects or witness refs as first-class output
- receipts over the full functional input
- typed relevance and typed loss, rather than mostly lexical relevance

## Outcome We Want

At the end of this checklist, the runtime should be able to do this honestly:

1. classify input into mother-typed units
2. attach witness and source lineage explicitly
3. pass typed units through the sieve without flattening them back into loose claims
4. mint receipts over the full transform contract
5. preserve unknowns and loss instead of forcing fake precision

## Workstream 1 — `mother_types.py`

### Goal

Make `mother_types.py` the canonical bridge from tagger output into `TypedUnit v0`, not just a compatibility shim that emits sieve-shaped dicts.

### Current strengths

- clear mother type constants
- stable event-to-mother mapping
- surrogate compatibility mapping
- working `tagger_to_claims()`

### Current gaps

- no canonical `TypedUnit v0` constructor
- no explicit `subtype`
- no explicit `authority`
- no explicit witness object or witness refs beyond `turn_id`
- fallback behavior is useful but too coarse

### Checklist

- [ ] Add a `make_typed_unit()` helper that returns a canonical dict shape
- [ ] Require every output unit to include:
  - `text`
  - `mother_type`
  - `binding_tier`
  - `schema_version`
- [ ] Add `subtype` assignment for the dev-first lattice
- [ ] Add `authority` field with initial values like `system`, `model`, `human`, `mixed`
- [ ] Replace implicit provenance-only output with explicit `source_refs` and `witness_refs`
- [ ] Keep `claim_type` as a compatibility field for now
- [ ] Keep `type_key` as a clustering key, not the ontology itself
- [ ] Add `unknown_subtype` as an explicit fallback instead of silently collapsing to generic values
- [ ] Add a `make_witness_stub()` helper or equivalent witness-ref constructor for turn-derived units
- [ ] Split the current `tagger_to_claims()` into:
  - `tagger_to_typed_units()`
  - optional compatibility adapter `typed_units_to_sieve_claims()`

### Dev-first subtype suggestions

- `CONTRACT`
  - `behavioral_guarantee`
  - `interface_promise`
  - `compatibility_claim`
  - `execution_contract`
- `CONSTRAINT`
  - `version_incompatibility`
  - `impurity_boundary`
  - `runtime_requirement`
  - `ordering_constraint`
- `UNCERTAINTY`
  - `open_edge_case`
  - `unverified_path`
  - `dynamic_behavior_gap`
  - `heuristic_inference`
- `RELATION`
  - `derived_from`
  - `supports`
  - `conflicts_with`
  - `depends_on`
- `WITNESS`
  - `ast_evidence`
  - `test_evidence`
  - `runtime_trace_evidence`
  - `human_review_evidence`

### Acceptance criteria

- every emitted unit has a mother type
- every emitted unit has either a real subtype or `unknown_subtype`
- every emitted unit has at least one `source_ref` or an explicit empty list
- `tagger_to_typed_units()` can run without the sieve

## Workstream 2 — `receipted.py`

### Goal

Make `receipted.py` the canonical stamped transform boundary for typed units and ensure receipts cover the full input contract of each transform.

### Current strengths

- keeps receipts out of the pure functions
- already wraps tagger and sieve
- already chains tagger stamp into sieve stamp

### Current gaps

- sieve input hashing does not cover `topic_context`
- sieve input hashing does not cover `all_topic_handles`
- the mother-type bridge is not independently stamped
- output hashing is still tuned to the old sieve output shape
- there is no generic `run_transform_with_receipt()` helper

### Checklist

- [ ] Add a generic `run_transform_with_receipt()` helper:
  - inputs: `domain`, `input_payload`, `fn_source_path`, `transform_fn`, `prev_stamp_hash`
  - outputs: `result`, `stamp`
- [ ] Replace ad hoc hashing helpers with explicit transform contract hashing
- [ ] For sieve runs, hash:
  - typed units / claims
  - `topic_context`
  - `all_topic_handles`
  - transform schema version
- [ ] For tagger runs, hash:
  - `text`
  - `turn_id`
  - `actor`
  - any prior-turn context if used
- [ ] Add a stamped mother-type bridge step:
  - `tagger classification -> typed units`
- [ ] Update `run_pipeline_with_receipts()` to emit three stamps, not two:
  - `tagger`
  - `mother_type_bridge`
  - `sieve`
- [ ] Standardize output shape so every receipted transform returns:
  - `result`
  - `stamp`
  - `input_hash`
  - `output_hash`
  - optional `warnings` / `declared_loss`
- [ ] Add parity tests that prove Python receipt output is stable and deterministic
- [ ] Add at least one integration test that proves the same typed input produces the same stamp chain twice

### Acceptance criteria

- no transform receipt omits load-bearing semantic input
- the mother-type step is independently stampable
- the pipeline can return a closed typed custody chain

## Workstream 3 — `sieve.py`

### Goal

Make the sieve operate over typed units honestly, instead of treating mother types as annotations on mostly lexical claims.

### Current strengths

- already the governance seam
- already distinguishes promoted, contested, deferred, and loss
- already defends against contamination
- already does declared loss explicitly

### Current gaps

- relevance is still mostly lexical plus local provenance hints
- mother types are not yet first-class in promotion logic
- subtype-specific behavior does not exist yet
- unknowns are preserved only partially
- output shape is still old-claim-centric rather than typed-unit-centric

### Checklist

- [ ] Define the sieve input contract explicitly:
  - accepts typed units, not just loose claims
- [ ] Preserve `mother_type`, `subtype`, `authority`, `source_refs`, and `witness_refs` through every sieve stage
- [ ] Add typed relevance gates before lexical fallback:
  - prioritize explicit `mother_type`
  - then subtype
  - then witness quality
  - lexical only as last fallback
- [ ] Add explicit typed handling rules:
  - `CONSTRAINT` units should rarely be dropped for mere low confidence
  - `UNCERTAINTY` should be preserved as uncertainty, not treated as weak failed fact
  - `WITNESS` should boost support without automatically upgrading binding
  - `RELATION` should not be flattened into generic observation
- [ ] Add subtype-aware promotion rules for the dev-first wedge
- [ ] Add a typed `declared_loss` schema with fields like:
  - `unit_id`
  - `mother_type`
  - `subtype`
  - `reason`
  - `rule_applied`
- [ ] Add `unknown_subtype` handling explicitly in promote logic
- [ ] Ensure contested and deferred outputs preserve type information
- [ ] Keep `structure()` and `synthesize()` compatible with typed outputs, even if projections stay lightweight for now

### Acceptance criteria

- mother types materially affect promotion behavior
- `UNCERTAINTY` survives as a first-class output
- `WITNESS` and `RELATION` are not lost as mere metadata
- lexical relevance is no longer the primary truth-maker

## Workstream 4 — Cross-Cutting Tests

### Goal

Make the type system enforceable, not just described.

### Checklist

- [ ] Add unit tests for mother-type assignment
- [ ] Add unit tests for subtype fallback to `unknown_subtype`
- [ ] Add unit tests for witness-ref presence on typed units
- [ ] Add receipt tests proving full-input contract hashing for sieve
- [ ] Add pipeline tests for:
  - text -> tagger stamp
  - tagger -> mother-type stamp
  - mother-type -> sieve stamp
- [ ] Add negative tests:
  - changing `topic_context` changes sieve receipt
  - changing `all_topic_handles` changes sieve receipt when contamination rules could differ
  - changing subtype or authority changes output hash when behavior changes
- [ ] Add one parity fixture between Python and Rust for the stamp core if not already present in Python tests

## Workstream 5 — Migration Strategy

### Goal

Adopt the type system without breaking the existing system all at once.

### Checklist

- [ ] Keep `claim_type` and `claim_role` available during transition
- [ ] Treat `type_key` as a clustering and lookup artifact, not the full ontology
- [ ] Introduce typed units first in the sidecar/runtime path
- [ ] Only later retrofit richer Surface flows like topics, compiler, and critics
- [ ] Avoid renaming existing external artifacts until typed outputs are stable

## Recommended Order

### Phase A — Foundation

- [ ] `mother_types.py`: canonical typed unit constructor
- [ ] `mother_types.py`: dev-first subtype assignment
- [ ] `mother_types.py`: witness-ref support

### Phase B — Receipts

- [ ] `receipted.py`: full transform contract hashing
- [ ] `receipted.py`: generic transform wrapper
- [ ] `receipted.py`: stamp the mother-type bridge

### Phase C — Governance

- [ ] `sieve.py`: typed input contract
- [ ] `sieve.py`: mother-type-aware promotion logic
- [ ] `sieve.py`: typed declared loss

### Phase D — Proof

- [ ] add deterministic tests
- [ ] add receipt-chain integration tests
- [ ] run parity checks against the stamp core

## Definition of Done

This checklist is complete when all of the following are true:

- typed units exist as a real transport shape
- mother types are first-class in behavior, not just labels
- the mother-type bridge is independently receipted
- sieve receipts cover the full semantic input contract
- typed outputs preserve witness, authority, uncertainty, and declared loss
- the dev-first subtype lattice is good enough to support the first real workflow

## Short Version

Build the type system in this order:

1. canonical typed unit
2. witness discipline
3. subtype assignment
4. full-input receipts
5. typed sieve behavior
6. deterministic tests

That keeps the ontology stable, the transform boundaries honest, and the first useful granularity anchored to the MVP instead of drifting into taxonomy theater.

