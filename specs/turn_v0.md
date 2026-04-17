# Turn v0

**Status:** Draft  
**Date:** 2026-04-14  
**Purpose:** Define `turn` as the minimum coordination primitive for the substrate so turns stop doing vague work and can cleanly relate to events, witnesses, receipts, rounds, and structures.

## Core Rule

A turn is not the deepest substrate primitive.

A turn is the deepest **coordination** primitive.

That means:

- not every event is a turn
- not every witness is a turn
- not every transform is a turn
- not every receipt is a turn
- a turn is the smallest bounded move that changes the next-step space in a shared context

## Working Definition

A turn is:

**a bounded, authored, directed move in a shared context that changes the space of valid next moves**

This is stricter than "message" and narrower than "event."

## Why Turn Matters

Without turns, the system can still have:

- source capture
- witness
- transforms
- receipts
- lineage

But it does not yet have:

- dialogue
- handoff
- delegation
- challenge
- ratification
- accountable reciprocity

Turns are where the substrate becomes social and coordinative instead of merely computational.

## What Turn Is Not

### `event`

An event is anything that happened.

A turn is only the subset of events that:

- are authored or attributable
- are directed into a shared context
- create, close, or modify coordination possibilities

### `witness`

A witness is evidence that something happened or was observed.

A turn may carry witness, but a witness is not automatically a turn.

### `transform`

A transform is computation over input.

A turn may invoke or cite transforms, but a transform is not automatically a turn.

### `receipt`

A receipt is portable proof that a transform or observed action occurred under stated conditions.

A turn may produce or cite receipts, but a receipt is not itself a turn.

### `transaction`

A transaction is a special case of turn where committed state changes under an authority surface.

All transactions are turns. Not all turns are transactions.

## Smell Test

Something is a turn if losing it would make you unable to reconstruct:

**who changed the next-step space for whom**

If that is not true, the thing is probably only:

- an event
- a witness
- a transform result
- or a passive record

## Turn Invariants

Every turn must have:

- an `actor`
- a `context_ref`
- a bounded payload or payload reference
- a coordination effect
- a timestamp

Every real turn should answer:

1. Who took the turn?
2. In what shared context?
3. What kind of move was it?
4. What did it carry?
5. What does it now make possible, required, or forbidden?

## Turn Effects

A turn changes coordination state by doing one or more of the following:

- `opens`
  creates new possible next moves
- `closes`
  resolves or removes possible next moves
- `binds`
  creates an obligation, commitment, or state change
- `routes`
  redirects work, attention, or authority
- `qualifies`
  adds uncertainty, witness, or contestation to an existing path

If none of those happened, the thing may not be a turn.

## Turn Acts

`turn_act` is not the same as mother type.

Mother types answer what kind of semantic object is being carried.
Turn acts answer what kind of coordination move is being made.

### Initial turn-act set

- `ask`
- `answer`
- `propose`
- `witness`
- `challenge`
- `commit`
- `delegate`
- `handoff`
- `ratify`
- `reject`
- `defer`
- `inform`

### Notes

- `witness` as a turn act means "I am placing observation or evidence into the shared coordination field"
- `commit`, `ratify`, and `reject` are the most transaction-like acts
- `ask`, `challenge`, and `defer` are clearly turns even though they may not be transactions

## Canonical Shape

### `Turn v0`

```json
{
  "turn_id": "trn_...",
  "actor": "human_or_model_or_system_id",
  "addressee": ["optional_target_ids"],
  "context_ref": "thread_or_round_or_session_id",
  "turn_act": "propose",
  "authority_mode": "human",
  "payload_refs": ["art_...", "snap_...", "txt_..."],
  "witness_refs": ["wit_..."],
  "receipt_refs": ["rct_..."],
  "parent_turn_refs": ["trn_..."],
  "relation_refs": ["rel_..."],
  "opens": ["review", "answer", "challenge"],
  "closes": [],
  "obligations_created": ["human_review_required"],
  "created_at": "2026-04-14T12:00:00Z",
  "schema_version": "substrate.turn.v0"
}
```

## Required Fields

- `turn_id`
- `actor`
- `context_ref`
- `turn_act`
- `created_at`
- `schema_version`

## Strongly Recommended Fields

- `addressee`
- `payload_refs`
- `witness_refs`
- `receipt_refs`
- `parent_turn_refs`
- `opens`
- `closes`
- `obligations_created`
- `authority_mode`

## Field Semantics

- `actor`
  who is responsible for the move
- `addressee`
  who or what the move is directed toward
- `context_ref`
  the shared space in which the move changes coordination state
- `turn_act`
  the coordination category of the move
- `payload_refs`
  the material the move carries
- `witness_refs`
  the evidence the move relies on or contributes
- `receipt_refs`
  the receipted transforms or artifacts the move cites or produces
- `parent_turn_refs`
  the turns this move responds to, extends, or supersedes
- `opens`
  what new next-step classes are now available
- `closes`
  what next-step classes are now resolved or blocked
- `obligations_created`
  what explicit burden or commitment this turn places into the shared field

## Relation to Receipts

Turns do not replace receipts.

The clean law is:

- receipts anchor lineage
- turns anchor coordination

In practice:

- a turn may cite one or more receipts
- a turn may create one or more receipts
- the turn chain is the social sequence of moves
- the receipt chain is the portable verification trail

Historical lineage should therefore be modeled as a graph, while turns are the ordered narrated path through that graph.

## Relation to Rounds

A round is a configured set of turns.

So:

- `turn`
  atomic coordination move
- `round`
  one completed pass through a coordination pattern
- `structure`
  the rule that defines how rounds happen

A round may require:

- one turn
- two turns
- or many turns

depending on the structure in force.

## Relation to Structures

A structure governs:

- who may take turns
- in what order
- with what authority
- under what handoff rules
- with what completion criteria

Turns are the moves.
Structures are the laws of moves.

## Relation to Transactions

Transaction is not the general primitive.

It is a subtype of turn where:

- committed state changes
- some authority surface applies
- the move can be adjudicated as completed, rejected, or pending

Examples of transaction-like turns:

- `commit`
- `ratify`
- `reject`
- some `handoff`

Examples of non-transaction turns:

- `ask`
- `challenge`
- `witness`
- `defer`

## Non-Examples

These are not turns by default:

- a raw file write with no authored or directed coordination effect
- an automatic background transform with no obligation or handoff implication
- a passive witness record not introduced into a shared context
- a receipt sitting in storage with no move that cites or routes it

These can become part of a turn if an actor:

- introduces them
- relies on them
- challenges them
- or uses them to bind the next-step space

## Minimal Examples

### Example 1 — Question

```text
actor: human
turn_act: ask
payload: "Did this function cross a trust boundary?"
opens: ["answer", "witness", "challenge"]
```

This is a turn because it opens a new valid next-step space.

### Example 2 — Receipted warning

```text
actor: substrate
turn_act: inform
receipt_refs: [rct_123]
opens: ["review", "ratify", "challenge"]
```

This is a turn because a receipted finding has been introduced into the shared coordination field.

### Example 3 — Ratification

```text
actor: human_reviewer
turn_act: ratify
parent_turn_refs: [trn_456]
closes: ["review"]
obligations_created: ["enforce_constraint"]
```

This is both a turn and a transaction-like move.

## Design Consequences

If `turn` is defined this way, then:

- `turnchain` is the ordered coordination spine, not the whole substrate
- turns can carry typed units and receipts without collapsing into them
- Agile and Liberating Structures can be re-read as structure systems over turns
- transaction-like business workflows can be modeled as one important family of turns without flattening everything into finance language

## Open Questions

These questions should stay open for v1:

- whether tool-only system moves can be first-class turns or only witnesses to a turn
- whether `addressee` should always be explicit
- whether `opens` / `closes` should be controlled vocabularies
- whether `authority_mode` belongs on the turn or only on attached typed units and receipts
- how much of turn construction should remain inferred versus explicitly authored

## Acceptance Criteria

This spec is useful when it becomes possible to:

1. distinguish a turn from a generic event without hand-waving
2. model `ask`, `challenge`, `ratify`, and `handoff` in one coherent shape
3. attach receipts and witnesses to turns without confusing the layers
4. explain why `turnchain` is one projection of the substrate rather than the whole substrate
5. model transaction-like business moves as a subtype of turn rather than the universal primitive

