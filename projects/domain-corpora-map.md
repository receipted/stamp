# Domain Corpora Map
# Source corpora for uncovering the mother type system

## Legal
- US Supreme Court opinions (court-listener.com, free, structured)
- English common law (British and Irish Legal Information Institute, bailii.org)
- Roman law (Corpus Juris Civilis, public domain)
- Parse target: ratio decidendi, holdings, dissents, precedent citations
- Already typed by courts themselves
- Ben has law firm contact — beachhead

## Evolutionary Biology  
- NCBI Taxonomy Database (free, structured, 500k+ species)
- Paleobiology Database (fossilworks.org, open access)
- TRY Plant Trait Database (open access)
- Parse target: trait definitions, selection pressures, speciation events, extinction events
- Ground truth: fossil record, independently verifiable by geology

## Music Theory
- Bach Well-Tempered Clavier (complete typed harmonic system)
- iRb Jazz Chord Progressions Database (free)
- Musicology papers (JSTOR, some open access)
- Parse target: tension/resolution events, harmonic intervals, structural cadences
- Ground truth: what audiences have returned to for centuries

## Epidemiology
- WHO outbreak reports (who.int, free, structured)
- CDC surveillance data (cdc.gov, free)
- Historical epidemic records: Black Death, 1918 flu, cholera pandemics
- Parse target: R0 estimates, transmission chains, immunity events, outbreak trajectories
- Ground truth: mortality records, independently verified

## Mathematics
- arxiv.org math preprints (free, structured)
- Lean/Coq formal proof databases (machine-readable, already typed)
- Metamath proof database (complete, verifiable)
- Parse target: axioms, theorems, lemmas, conjectures, proof steps
- Ground truth: logical consistency (machine-verifiable)

## Ayurveda / Classical Medicine
- Charaka Samhita (English translations, public domain)
- Sushruta Samhita (English translations, public domain)
- Modern clinical Ayurveda papers (PubMed, some open access)
- Parse target: dosha classifications, treatment protocols, contraindications, constitution types
- Ground truth: clinical outcomes, centuries of practice

---

## The Run Order (by ease of access + Ben's beachhead)

1. **Mathematics first** — already machine-typed, no parsing required, Lean/Coq is ground truth
2. **Legal second** — most digitized, law firm contact
3. **Epidemiology third** — WHO/CDC structured data
4. **Biology fourth** — NCBI structured
5. **Music fifth** — requires more parsing
6. **Ayurveda sixth** — requires text processing of classical texts

---

## What We're Looking For

Run sieve over each corpus independently.
What promotes in ALL six = mother type candidate.
What promotes in only one = domain-specific type (not the mother).
What promotes in three or more = strong candidate worth investigating.

The intersection is the mother. The rest are derivatives.
