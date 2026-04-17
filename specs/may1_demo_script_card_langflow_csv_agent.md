# May 1 Demo Script Card — Langflow CSV Agent

**Status:** Draft  
**Date:** 2026-04-14  
**Owner:** Demo / product sprint  
**Purpose:** Freeze the exact spoken demo path for the May 1 product demo so the narrative stays aligned to the receipt artifact.

## Source Artifacts

- [may1_canonical_demo_spec_card_langflow_csv_agent.md](/Users/benjaminfenton/Thinking-Log/specs/design/may1_canonical_demo_spec_card_langflow_csv_agent.md)
- [may1_demo_receipt_mock_langflow_csv_agent.md](/Users/benjaminfenton/Thinking-Log/specs/design/may1_demo_receipt_mock_langflow_csv_agent.md)

## Demo Rule

The demo is not about the full system.

The demo is about one thing:

**Substrate produces a receipt that proves an AI workflow crossed a dangerous trust boundary that looked harmless in ordinary review.**

## Runtime Target

90 seconds total.  
Do not exceed 100 seconds.

## Stage Assets

Prepare these in advance:

1. repo / revision screen
2. one code snippet or fix diff
3. stamped analysis screen
4. red receipt screen
5. local verify command output

If anything is flaky, prerecord steps 1-4 and keep step 5 live.

## Spoken Script

### Beat 1 — Problem setup

**Target:** 0:00-0:15

**Say:**

Company ships an AI workflow that answers questions about uploaded CSVs. It passes review because it looks like analytics plumbing.

**Show:**

- repo name: `langflow-ai/langflow`
- vulnerable revision
- component name: `CSVAgentComponent`

### Beat 2 — Trust boundary failure

**Target:** 0:15-0:30

**Say:**

But this component silently enabled prompt-driven code execution on the server. The contract looked harmless. The trust boundary was wrong.

**Show:**

- one dangerous line or a tiny diff
- ideally the `allow_dangerous_code=True` line or the patch turning it off by default

### Beat 3 — Substrate run

**Target:** 0:30-0:50

**Say:**

Substrate analyzes the repo, types the function, stamps the transform, and emits a receipt when it finds a boundary failure.

**Show:**

- minimal analysis flow
- receipts accumulating
- one red receipt appearing

### Beat 4 — Artifact

**Target:** 0:50-1:10

**Say:**

This is the artifact. It names the function, the source witness, the kind of failure, and the exact boundary it crossed.

Then say:

This CSV helper could execute model-generated Python on your server.

**Show:**

- the receipt only
- keep the focus on:
  - `CRITICAL RED FLAG`
  - subject
  - kind line
  - finding

### Beat 5 — Buyer meaning

**Target:** 1:10-1:20

**Say:**

This is what you hand to AppSec, compliance, or an auditor when they ask whether your AI tooling shipped a time bomb.

### Beat 6 — Verification

**Target:** 1:20-1:30

**Say:**

And because it is receipted, someone else can verify it independently.

**Show:**

- `substrate verify receipts/rct_demo_langflow_csv_agent_001.json`

## One-Line Version

If interrupted and forced to compress, say only this:

Substrate turned a hidden AI execution boundary in Langflow into a receipt an auditor can verify.

## What To Emphasize

- harmless appearance
- wrong trust boundary
- specific function
- witnessed source fact
- verify independently

## What Not To Explain Unless Asked

- all five mother types
- Rust vs Python
- Merkle details
- ZK or on-chain plans
- the full type algebra
- broader ontology naming

## Q&A Bridges

### If asked "How is this different from Semgrep or SAST?"

Say:

Those tools can catch patterns. We are producing a portable receipt that names the semantic boundary, the witness, and the custody of the analysis.

### If asked "Why receipts?"

Say:

Because the receipt is the artifact you can hand to another party. The analysis matters, but the receipt is what travels.

### If asked "Why this example?"

Say:

Because it looks normal to a reviewer and still crosses into dangerous execution authority. That is exactly the failure we want to make legible.

## Failure Handling

If the live run stalls:

1. switch to prerecorded analysis immediately
2. keep the receipt reveal live if possible
3. always keep verification live if possible

If verification also fails:

1. stop at the receipt
2. say the verify step is part of the shipping path and move to Q&A
3. do not debug on stage

## Rehearsal Checks

The demo is ready when all of these are true:

1. the full script lands in under 90 seconds without rushing
2. the finding sentence sounds natural when spoken aloud
3. the red receipt is readable in under 5 seconds
4. the verify step is muscle memory
5. no sentence requires ontology explanation to make sense

## Final Reminder

Do not demo the engine.

Demo the moment where a normal-looking AI helper turns into a verified red receipt.

