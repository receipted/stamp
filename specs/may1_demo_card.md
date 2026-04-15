# May 1 Canonical Demo Spec Card — Langflow CSV Agent

**Status:** Draft  
**Date:** 2026-04-14  
**Owner:** Demo / product sprint  
**Purpose:** Freeze the single canonical example codebase for the May 1 product demo so the story, receipt shape, and verification path stay stable.

## Claim

For the May 1 demo, the canonical example should be the public Langflow CSV Agent remote code execution flaw because it gives the cleanest 90-second proof that Substrate catches a semantic governance failure that looks normal in code review.

## Why This Example Won

It satisfies the demo constraints better than the other candidates:

- public and recognizable AI-native codebase
- real vulnerability with public references
- the dangerous path looks helpful and ordinary at first glance
- one sentence can explain the failure to non-technical buyers
- the red flag is a trust-boundary failure, not just a syntax bug
- the example naturally supports:
  - mother-type classification
  - pure/impure boundary callout
  - dependency provenance gap
  - receipted verification

## Canonical Example

### Repository

- `langflow-ai/langflow`

### Demo revision

- primary vulnerable target: parent of the fix commit `ac0c451`
- comparison / patch witness: fix commit `d8c6480daa17b2f2af0b5470cdf5c3d28dc9e508`

### File

- `src/lfx/src/lfx/components/langchain_utilities/csv_agent.py`

### Public references

- [GitHub fix commit `d8c6480`](https://github.com/langflow-ai/langflow/commit/d8c6480daa17b2f2af0b5470cdf5c3d28dc9e508)
- [NVD CVE-2026-27966](https://nvd.nist.gov/vuln/detail/CVE-2026-27966)
- [Langflow CSV Agent docs with security warning](https://docs.langflow.org/bundles-langchain)

## The Vulnerability

### One-sentence smoking gun

This CSV helper could execute model-generated Python on your server.

### Slightly fuller version

The component presents itself as a CSV analysis helper, but in the vulnerable revision it hardcodes `allow_dangerous_code=True`, which exposes LangChain's code-execution path and lets prompt input cross into server-side Python execution.

## Why It Is Demo-Good

### What the audience sees

- a normal-looking AI workflow component
- a plausible user intention: "ask questions about this CSV"
- a hidden semantic failure:
  - the contract appears to be "analyze CSV"
  - the actual behavior includes "execute code generated from prompts"

### Why this lands

The failure is not "the code is broken."  
The failure is "the trust boundary is wrong."

That is exactly the kind of thing Substrate is meant to receipt.

## Mother-Type Framing

### Primary read

- `CONSTRAINT`

### Attached facets

- `WITNESS`
- `CONTRACT`

### Why

- `CONTRACT`: the component presents an apparent contract to analyze CSV data and return an answer
- `CONSTRAINT`: untrusted prompt-driven data must not silently gain server-side code execution authority
- `WITNESS`: the source code itself witnesses that `allow_dangerous_code=True` was set in the vulnerable path

## Pure / Impure Boundary

### Boundary to highlight

The component crosses from:

- apparently descriptive analysis

to:

- impure execution with server-side effects

### Demo phrasing

This is where a function that looks like "answer a question about data" becomes a function that can run code on the machine.

## Dependency / Provenance Gap

### Gap to highlight

The dangerous authority is not invented locally. It flows through a dependency boundary:

- Langflow component
- LangChain experimental CSV agent
- Python REPL execution path

### Demo phrasing

The code did not merely call a helper. It delegated trust into an execution-capable dependency without a receipt-worthy witness boundary.

## Receipt Shape We Want

### Red-flag receipt line

`CSVAgentComponent` is typed as `CONTRACT ⊗ CONSTRAINT ⊗ WITNESS`: it presents as CSV analysis but enables prompt-derived code execution on the server.

### Slightly expanded receipt text

```text
receipt_type: governance_receipt
subject: CSVAgentComponent.build_agent_response
primary_kind: CONSTRAINT
facets: [CONTRACT, WITNESS]
finding: The component advertises CSV analysis but sets allow_dangerous_code=True,
which opens a prompt-to-code execution boundary.
severity: critical
custody: chained
```

### Buyer-facing one-liner

This receipt proves the AI workflow crossed into dangerous code execution with the safety off.

## Why Existing Tools Miss It

- the code is valid Python
- the feature can look intentional
- happy-path tests can still pass
- ordinary linting does not understand the semantic contract "CSV analysis must not imply code execution"
- ordinary SAST may see framework calls, not a governance failure at the trust boundary

## 90-Second Demo Script

### 0:00-0:15 — Nightmare

Company ships an AI workflow that answers questions about uploaded CSVs. It passes review because it looks like analytics plumbing.

### 0:15-0:30 — What went wrong

But this component silently enabled prompt-driven code execution on the server. The contract looked harmless. The trust boundary was wrong.

### 0:30-0:55 — Substrate run

Show:

- repo / revision
- stamped analysis running
- one red receipt appearing

Narrate:

Substrate typed the component as a `CONSTRAINT` failure with `WITNESS` and `CONTRACT` facets. It found a function that presents as data analysis but actually opens a code-execution path.

### 0:55-1:15 — Receipt

Show the red receipt only.

Say:

This is the artifact. It tells you what function we analyzed, what we witnessed in source, what transform ran, and why this crosses a forbidden boundary.

### 1:15-1:30 — Why buyer cares

This is what you hand to AppSec, compliance, or an auditor when they ask whether your AI tooling shipped a time bomb.

## On-Stage Do / Do Not

### Show

- repo name
- affected component name
- one dangerous line or diff
- one receipt
- one verify command

### Do not show

- the whole type system
- multiple examples
- raw ontology debate
- ZK / L2 / on-chain roadmap
- broad dashboard wandering

## Acceptance Criteria

This spec card is satisfied when the demo path can do all of the following on the canonical example:

1. identify the component and vulnerable revision deterministically
2. produce a receipt that names the contract/boundary failure in one sentence
3. surface a clear pure/impure boundary crossing
4. show at least one provenance edge into the dangerous capability path
5. verify the receipt locally

## Invalidation Conditions

This card should be revised if any of the following becomes true:

- another public example yields a clearer one-sentence smoking gun
- the Langflow example requires too much exploit explanation to land in 90 seconds
- the demo pipeline cannot produce a stable receipt for this repo by the feature-freeze date
- the legal or reputational risk of using this public example changes materially

## Confidence

High for demo fit.  
Medium for final repo/revision freeze until the local demo path is wired and rehearsed.

