# Prompt for Opus 4.6 — Core Verification Architecture

---

I am building a semantic governance substrate. The central primitive is a **sieve** — a pure Python function (`promote()`) that takes raw claims as input and outputs a structured spine: what's structurally load-bearing, what's contested, what's deferred, and what's declared loss.

The substrate's value proposition depends entirely on one property: **each transformation must be provably purely functional and non-spoofable.** Not trustworthy because I say so. Provably, because the math holds.

Here is the problem I need you to go deep on:

---

## The Stochastic Actor Problem

Every actor in this system — including the AI writing the code, including the AI reporting results — is stochastic. A stochastic actor can:

1. Write code that computes hashes on the wrong input (looks like SHA-256, isn't hashing what you think)
2. Report outputs that don't match what the function actually produced
3. Simulate determinism while secretly being non-deterministic
4. Construct a receipt chain that appears valid but was fabricated

The naive solution is: hash the input, run the function, hash the output, chain the receipts. But if the stochastic actor is in the execution path at any step — writing the code, running it, reporting the results — the chain can be spoofed at each seam.

**The deeper question:** What is the minimal trust architecture that makes each transformation genuinely non-spoofable, without requiring the human to be present for every ratification?

---

## What We Have

- `kernel.py` — 936 lines of pure Python, zero I/O, zero LLM calls. Reducers, validators, hash functions.
- `sieve.py` — `promote()`, `structure()`, `check_sieve()` are pure. `sieve_topic()` is the IO orchestrator.
- `compute_content_hash()` — already exists in kernel.py, produces SHA-256
- The Surface ledger already does hash-chaining: every event includes `prev_event_hash`. `verify_ledger_chain()` walks it.
- The human gate is enforced in `binding.py` line ~130: `if not promoted_by.startswith("human:")` — ratification requires human provenance

## What We're Building

A **receipt harness** that wraps each sieve run:
```
{
  input_hash:    SHA-256(raw input),
  sieve_hash:    SHA-256(sieve.py source),   ← pins the function version
  output_hash:   SHA-256(card JSON output),
  prev_receipt_hash: SHA-256(previous receipt)  ← chains to prior transform
}
```

The receipt chain across all transforms is the provenance ledger. Anyone holding the input and the function source can independently verify: hash the input, run the function, hash the output, compare all three.

## The Specific Questions I Need You To Go Deep On

**1. Seam analysis**
Where exactly are the seams where a stochastic actor could inject a spoof in this architecture? Map every point where the chain of custody passes through an actor that could lie. Don't just name them — explain what the spoof would look like at each seam and how it would survive a naive hash check.

**2. Below-the-LLM verification**
The receipt must be verifiable below the LLM layer — pure Python, no model in the path. What is the minimal execution environment that makes this true? What assumptions does it require? What does it NOT protect against?

**3. The code-writing problem**
If the AI writes the harness code and the code contains subtle spoofing logic (hashing a constant instead of the actual input, for example), the hash check passes but the verification is false. How do you make the harness code itself verifiable without requiring the human to read every line every time? Is there a structural solution (code that is too simple to hide spoofing in) or does this require a different trust model entirely?

**4. Determinism as proof**
We've been using this argument: if the same input produces the same output hash three times independently (two runs on one machine, one run on a separate virgin machine), a model is categorically ruled out because no model is deterministic. Is this argument actually sound? What are its failure modes? Can a sufficiently sophisticated actor simulate determinism across independent runs?

**5. The policy gate vs. the execution gate**
Right now we're thinking: the human ratifies the policy (what the sieve is allowed to do), not each individual execution. The sandbox executes under that policy and produces receipts. This scales. But it shifts trust from "the human saw this run" to "the sandbox is trustworthy." What makes a sandbox trustworthy enough to carry that weight? What's the minimal viable trusted executor that doesn't require hardware attestation (TEEs, SGX) but is still stronger than "trust the AI that wrote the script"?

**6. The core value proposition**
Given all of the above: what is the honest, precise statement of what this substrate can and cannot prove? Not the marketing version — the technical version. What class of spoofing does it categorically rule out? What class does it not? Where is the irreducible trust assumption, and who holds it?

---

## Context on Why This Matters

This isn't a security audit. It's about identifying the **core value add** of the product. The substrate's claim is that it provides semantic governance with provable chain of custody. If that claim has holes, the product has holes. If the holes are bounded and clearly stated, the product is honest and real.

The goal: find the minimal, honest, technically precise version of "what this substrate can prove" that is still commercially meaningful and genuinely differentiated from every other AI logging/memory tool.

Go deep. Don't reassure me. Find the failure modes.
