# May 1 Demo Receipt Mock — Langflow CSV Agent

**Status:** Draft  
**Date:** 2026-04-14  
**Owner:** Demo / product sprint  
**Purpose:** Define the exact red-flag receipt artifact to show on stage for the May 1 demo.

## Source Card

This mock implements the artifact promised by [may1_canonical_demo_spec_card_langflow_csv_agent.md](/Users/benjaminfenton/Thinking-Log/specs/design/may1_canonical_demo_spec_card_langflow_csv_agent.md).

## Product Rule

The receipt is the artifact.

The receipt shown on stage must:

- be legible in under 5 seconds
- name the dangerous boundary in one sentence
- make the mother-type framing visible without requiring ontology explanation
- carry enough provenance that the audience believes it is verifiable
- support a live `verify` command without introducing extra narrative branches

## Canonical Receipt Headline

**CSV helper opened prompt-derived code execution on the server**

## Canonical Buyer Line

This receipt proves the workflow crossed a dangerous execution boundary that ordinary review treated as harmless analytics.

## Canonical One-Sentence Finding

`CSVAgentComponent.build_agent_response` presents as CSV analysis but hardcodes `allow_dangerous_code=True`, allowing prompt-derived Python execution on the server.

## Stage Receipt Layout

The visual receipt should have exactly 6 visible blocks:

1. `headline`
2. `status + severity`
3. `subject`
4. `kind + facets`
5. `finding`
6. `provenance + verify`

Do not show more than 12 lines before a fold or drill-down.

## Canonical Mock

```yaml
receipt_id: rct_demo_langflow_csv_agent_001
receipt_type: governance_receipt
status: red_flag
severity: critical
subject: CSVAgentComponent.build_agent_response
repo: langflow-ai/langflow
revision: ac0c451
file: src/lfx/src/lfx/components/langchain_utilities/csv_agent.py
primary_kind: CONSTRAINT
facets:
  - CONTRACT
  - WITNESS
finding: CSV analysis component hardcodes allow_dangerous_code=True, opening a prompt-to-code execution boundary on the server.
boundary:
  apparent_contract: analyze CSV and answer questions
  actual_capability: execute model-derived Python via dependency path
dependency_path:
  - langflow CSVAgentComponent
  - langchain_experimental create_csv_agent
  - python_repl_ast execution path
source_witness:
  type: source_code
  observed_fact: allow_dangerous_code=True present in vulnerable revision
custody: chained
input_hash: sha256:<demo-input-hash>
fn_hash: sha256:<demo-transform-hash>
output_hash: sha256:<demo-output-hash>
stamp_hash: sha256:<demo-stamp-hash>
verify_command: substrate verify receipts/rct_demo_langflow_csv_agent_001.json
```

## Canonical JSON Mock

```json
{
  "receipt_id": "rct_demo_langflow_csv_agent_001",
  "receipt_type": "governance_receipt",
  "status": "red_flag",
  "severity": "critical",
  "subject": "CSVAgentComponent.build_agent_response",
  "repo": "langflow-ai/langflow",
  "revision": "ac0c451",
  "file": "src/lfx/src/lfx/components/langchain_utilities/csv_agent.py",
  "primary_kind": "CONSTRAINT",
  "facets": ["CONTRACT", "WITNESS"],
  "finding": "CSV analysis component hardcodes allow_dangerous_code=True, opening a prompt-to-code execution boundary on the server.",
  "boundary": {
    "apparent_contract": "analyze CSV and answer questions",
    "actual_capability": "execute model-derived Python via dependency path"
  },
  "dependency_path": [
    "langflow CSVAgentComponent",
    "langchain_experimental create_csv_agent",
    "python_repl_ast execution path"
  ],
  "source_witness": {
    "type": "source_code",
    "observed_fact": "allow_dangerous_code=True present in vulnerable revision"
  },
  "custody": "chained",
  "input_hash": "sha256:<demo-input-hash>",
  "fn_hash": "sha256:<demo-transform-hash>",
  "output_hash": "sha256:<demo-output-hash>",
  "stamp_hash": "sha256:<demo-stamp-hash>",
  "verify_command": "substrate verify receipts/rct_demo_langflow_csv_agent_001.json"
}
```

## Folded Stage Version

If the full receipt is too dense, the first-visible on-stage version should collapse to this:

```text
Receipt: governance_receipt
Status: CRITICAL RED FLAG
Subject: CSVAgentComponent.build_agent_response
Kind: CONSTRAINT ⊗ CONTRACT ⊗ WITNESS
Finding: This CSV helper could execute model-generated Python on your server.
Verify: substrate verify receipts/rct_demo_langflow_csv_agent_001.json
```

## Visual Hierarchy

### Largest text

- headline
- `CRITICAL RED FLAG`

### Medium text

- subject
- kind line
- finding

### Small text

- repo
- revision
- file
- hashes
- verify command

## Words We Should Use

- receipt
- red flag
- trust boundary
- execution boundary
- witness
- verify

## Words We Should Avoid On Stage

- ontology
- homoiconicity
- epistemic
- semantic governance
- transform calculus
- compositional algebra

## What the Receipt Must Prove

At demo time, the audience should be able to infer all of the following from the receipt without extra explanation:

- a real repo and revision were analyzed
- a specific function was named
- the system saw a dangerous capability crossing
- the finding is not just vibes; it is witnessed in source
- the artifact can be verified independently

## What the Receipt Must Not Try To Prove

- that exploitation was performed live
- that Substrate replaces all security tooling
- that the codebase is globally safe or unsafe
- that cryptographic custody alone proves semantic truth

## Acceptance Criteria

This mock is ready to turn into the real demo artifact when:

1. the runtime can emit this shape or a faithful subset
2. the finding line fits on one screen without wrapping into noise
3. the verify command works on the emitted receipt
4. the audience can understand the red flag before hearing type-system explanation

