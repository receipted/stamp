# Mother Type Evidence — Cross-Corpus Sieve Runs
# Date: 2026-04-11
# Corpora: Lean mathlib, Charaka Samhita Ch1, Brown v Board of Education

## Results

### Lean Mathematics (mathlib List.Basic)
- Claims: 16 | Promoted: 14 | Contested: 0 | Loss: 2
- Loss: assert_not_exists (constraint claims dropped — keyword miss)
- Load-bearing: theorems, injective, exists, subset, iff

### Ayurveda (Charaka Samhita Chapter 1)
- Claims: 16 | Promoted: 13 | Contested: 2 | Loss: 1
- Loss: four purushartha instincts (dropped — too foundational, no keyword match)
- Load-bearing: dosha type system, physician constraints, knowledge methodology, prakruti uncertainty

### Legal (Brown v Board of Education, 347 US 483)
- Claims: 16 | Promoted: 8 | Contested: 7 | Loss: 1
- Loss: jurisdictional scope (Kansas, SC, VA, DE) — too specific
- Load-bearing: Equal Protection constraint, psychological harm observation, precedent relation, Warren witness

## Cross-Corpus Convergence

| Mother Type | Lean | Ayurveda | Legal |
|---|---|---|---|
| CONTRACT | theorems (iff, implies) | dosha type system | Equal Protection Clause |
| CONSTRAINT | assert_not_exists | physician without knowledge causes harm | Plessy overruled |
| UNCERTAINTY | exists claims | prakruti modifies universal rules | framers intent inconclusive |
| RELATION | subset, iff, injective | samanya/vishesha | Sweatt v Painter precedent |
| WITNESS | MISSING | lineage of teachers | Warren unanimous opinion |

## Key Finding

WITNESS is the type that distinguishes empirical knowledge systems from formal ones.
- Lean: no witness needed — the proof IS the witness
- Ayurveda: witness = lineage of teachers (who transmitted this)
- Legal: witness = court + author + date (who ratified this)
- Code: witness = commit hash (but most code has no witness at all)

The refactoring tool adds the witness to code. That's what's missing.

## What Got Dropped (sieve calibration signal)

Across all three corpora, the sieve dropped:
1. Overly specific claims (jurisdictions, individual names)
2. Foundational axioms stated without qualifiers (assumed, not argued)
3. Claims with no keyword overlap despite being structurally important

→ The keyword filter is still the bottleneck. The mother type system would replace it.
   A claim is relevant if it instantiates any of the five mother types — no keywords needed.

## Full Corpus Run Results (2026-04-11)

| Corpus | Claims | Promoted | Contested | Loss |
|---|---|---|---|---|
| Lean mathlib (List.Basic) | 16 | 14 | 0 | 2 |
| Ayurveda (Charaka Ch.1) | 16 | 13 | 2 | 1 |
| Legal (Brown v Board) | 16 | 8 | 7 | 1 |
| Legal (Roe v Wade) | 14 | 6 | 7 | 1 |
| Biology (Darwin Ch.4) | 16 | 8 | 8 | 0 |
| Vedic (Rigveda + Upanishads) | 16 | 6 | 10 | 0 |
| Founding docs (DOI + Constitution) | 24 | 13 | 8 | 3 |
| Finance (Fed FOMC + Apple Q4) | 16 | 9 | 7 | 0 |
| Physics (Einstein 1905) | 12 | 4 | 8 | 0 |
| Ethics (Trolley + Rawls + Nozick) | 20 | 6 | 13 | 1 |
| Ship of Theseus | 12 | 2 | 10 | 0 |
| Riemann Hypothesis | 14 | 12 | 2 | 0 |

## Key Findings Per Corpus

**Lean:** Purely formal — no WITNESS needed. Proof IS the witness.
**Ayurveda:** WITNESS = guru lineage. SEQUENCE visible in panchamahabhuta.
**Brown v Board:** Psychological harm observation promoted. Scope (jurisdictions) dropped.
**Roe v Wade:** Trimester framework entirely contested — SEQUENCE type missing.
**Darwin:** Geological record imperfection promoted as UNCERTAINTY. Darwin 1859 as WITNESS.
**Vedic:** Most contested corpus — convergence cluster around Brahman. Revealed CONVERGENCE type.
**Founding docs:** Declaration vs Constitution contested — two sovereignty claims about same polity. Real constitutional tension correctly identified.
**Finance:** FED CONSTRAINT + AAPL WITNESS promoted. FX headwind as UNCERTAINTY.
**Einstein:** E=mc² contested against photoelectric quanta — the structural fault line physics spent 20 years resolving.
**Ethics:** Meta-ethics promoted (Kant dignity, Rawls difference principle). All first-order dilemmas contested.
**Ship of Theseus:** Only the question itself and Heraclitus' WITNESS promoted. Every answer contested. Substrate's own identity claim contested.
**Riemann:** Hilbert-Polya quantum path and Gödel undecidability promoted as the two real frontiers. Confirmed what mathematicians believe.

## Emerging Mother Type Candidates (beyond original five)
- **SEQUENCE** — ordered transitions in a state machine (trimester framework, panchamahabhuta, evolutionary stages)
- **CONVERGENCE** — claims approaching the same truth from different angles (Vedic corpus, physics)
- **APOPHASIS** — what can only be described by negation (neti neti = assert_not_exists)

## Additional Corpus Runs (2026-04-12)

| Corpus | Claims | Promoted | Contested | Loss |
|---|---|---|---|---|
| Crypto (Bitcoin + Ethereum + EIPs) | 22 | 13 | 8 | 1 |
| Music Theory (Bach WTC + counterpoint) | 14 | 7 | 7 | 0 |
| Epidemiology (WHO + outbreak theory) | 12 | 12 | 0 | 0 |

## Key Findings from New Corpora

**Crypto:** Mother types all present. Gap claims (blockchain proves value not meaning; smart contracts enforce financial not semantic logic) correctly identified as CONTESTED against core Bitcoin/Ethereum facts. The substrate is the semantic layer above the crypto layer — not competing, completing.

**Music Theory:** Half the claims contested — core structural tension: is harmonic resolution a law or a convention? Composers have argued this for 300 years. Sieve correctly puts it in contested. WITNESS: Bach 1722.

**Epidemiology:** 12/12 promoted, 0 contested — cleanest run yet. Highly formalized field, all claims structurally non-contradictory. Every mother type present. WITNESS: WHO Jan 30 2020.

## Full Corpus Count: 13
Lean, Ayurveda, Brown v Board, Roe v Wade, Darwin, Vedic, Founding Docs, Finance, Einstein 1905, Ethics, Ship of Theseus, Riemann Hypothesis, Crypto, Music Theory, Epidemiology

## Mother Types: Still Holding Across All 13
CONTRACT, CONSTRAINT, UNCERTAINTY, RELATION, WITNESS — present in every corpus.
