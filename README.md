# Substrate

**Receipted execution for code, AI, and critical workflows.**

Internal: a forge for stamped semantic transforms.

A receipt is proof that a specific transform ran on specific material and yielded a specific output.

## The Primitive

```
input → pure function → stamped output
```

The stamp proves:
- what went in
- which function ran
- what came out
- what it chained from

The successful handoff to the next pure function is the proof of usable I/O.

## The Verb Stack

```
source → witness → transform → stamp → handoff → chain → project
```

## The Noun Stack

```
source event → witness → transform result → receipt → chain → projection
```

## Domain-Specific Chains Over One Primitive

| Domain | Coin | Chain |
|---|---|---|
| Conversation | turn coin | turn chain |
| Governance | sieve coin | sieve chain |
| Healthcare | care coin | care chain |
| Code intent | intent coin | intent chain |
| Legal | evidence coin | evidence chain |
| Finance | signal coin | signal chain |

These are all projections of the same lower primitive: a stamped pure function execution.

## The Distilled Center

Meaning-bearing state changes can be minted, chained, and re-executed through pure functions with portable proof.

## The Coin Has Two Sides

The same stamp, same pure function, same receipt. The difference is where the anchor lands.

| | Open Source (free) | Paid |
|---|---|---|
| Pure function | Same | Same |
| Receipt | Same | Same |
| Chain | Local + git anchor | Local + git + L2 on-chain anchor |
| Verification | Re-execute locally | ZK proof — verify without re-execution |
| Proof URL | None (you verify yourself) | Public, permanent, shareable |
| Trust model | "Run it yourself" | "Here's the proof, check the chain" |

The open source side is the full substrate. The coin is real. The chain is real. The stamp is real. You just verify by re-running the function yourself.

The paid side adds: ZK proof (don't need to re-run), on-chain anchor (don't need to trust the git host), and a proof URL (shareable verification without running anything). Same coin, more anchors.

The sieve, the types, the stamp primitive — all open. The ZK circuit compilation and the on-chain verifier are the paid tier. You don't pay for governance. You pay for portable proof.

## Design Law

**Loose at the edges, strict at the core.**

Loose at the edges: messy inputs, imperfect hosts, different devices, partial context, real-world mud.
Strict at the core: pure transforms, stamped receipts, explicit handoffs, verifiable chain.

Not a lab ornament. A field tool. A durable semantic mechanism that survives bad surfaces without lying about what happened.

## Types ARE Verticals

Each mother type is a customer segment's entry point:
- CONTRACT → legal, API governance
- CONSTRAINT → AppSec, compliance
- UNCERTAINTY → clinical, risk management
- RELATION → dependency analysis, supply chain
- WITNESS → audit, provenance, chain of custody

The type system is the go-to-market encoded as architecture. One axis, not two.

## What This Means

- `turn` is not the deepest primitive. `stamp` is deeper.
- The hash chain is a sequence of pure function executions, not a data format.
- The ZK proof verifies execution without re-running the function.
- The smart contract contains the proof, not the data.
- The apps are projections on top of the chain. The chain doesn't care about the domain.
- We distilled down through the apps to find the primitive. Now we build back up.
