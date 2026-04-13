# Multi-Model Harness Design
# Date: 2026-04-12

---

## Architecture

### Three Sediment Streams (ore sources)

```
Stream 1: Telegram session (this conversation)
  - Path: /Users/shadow/.openclaw/agents/main/sessions/*.jsonl
  - Watcher: shadow account watcher (running)
  - Format: OpenClaw JSONL, model snapshots included

Stream 2: Codex desktop app
  - Path: /Users/benjaminfenton/.codex/sessions/
  - Watcher: genesis account watcher (restart needed)
  - Format: Codex JSONL

Stream 3: Claude Code terminal
  - Path: /Users/benjaminfenton/.claude/projects/
  - Watcher: genesis account watcher (running)
  - Format: Claude Code JSONL
```

All three flow into `/Users/Shared/sidecar-ore/` via the watcher.
The turn chain runs over each stream independently.
The sieve can run over all three combined or each separately.

### Matrix-Backed API Bridge

```
Model × Tier matrix (checkboxes):

  [ ] claude-opus-4-6      $15/M in  $75/M out
  [x] claude-sonnet-4-6    $3/M in   $15/M out
  [ ] codex-mini           $1.5/M in $6/M out
  [ ] gpt-4.1              $2/M in   $8/M out
  [ ] gemini-2.0-flash     $0.1/M in $0.4/M out

Persona assignment per model:
  [ ] adversarial  (finds constraints, breaks things)
  [ ] builder      (finds contracts, makes things work)
  [ ] implementer  (finds relations, connects things)
  [ ] ratifier     (human gate — you)

Cost estimate: shown before run commits
```

### Staging Phase

Before each model run, a staging object is generated — a model-specific
prompt artifact optimized for that model's characteristics.

Not one prompt reused across models. N prompts, one per model.

(Full prompt engineering design is a separate hyperdimensional bumpdown — TBD)

---

## Parallel vs Sequential: Strategic Analysis

### Parallel Runs

**What it is:** All models receive the prompt simultaneously. Responses arrive
independently. No model sees another model's output before responding.

**Pros:**
- No contamination between models — true independent responses
- Fast wall-clock time
- Higher confidence that convergence is structural, not echo
- Best for: finding what's universally load-bearing across independent minds

**Cons:**
- Higher cost (all tokens consumed simultaneously)
- No iterative refinement based on other models' outputs
- Models can't challenge each other in real time

**Strategic scenarios where parallel wins:**
1. **Mother type validation** — you want to know if CONTRACT appears independently
   in all models without any one model influencing the others
2. **Convergence testing** — if 3 models in parallel produce the same spine,
   that's stronger evidence than 3 sequential models who each read the prior output
3. **Bias detection** — parallel runs expose each model's idiosyncratic biases
   because they can't defer to each other

---

### Sequential Runs

**What it is:** Models run in order. Each model sees the previous model's output
before responding. Output of model N becomes part of the input to model N+1.

**Pros:**
- Models can challenge, refine, and build on each other
- Lower cost if early models produce good output (later runs are shorter)
- More like a real collaborative process
- Best for: iterative refinement toward a ratified conclusion

**Cons:**
- Contamination — later models are influenced by earlier ones
- If model 1 is wrong, models 2 and 3 may compound the error
- Convergence could be false (model 3 agrees because model 2 agreed, not because
  the claim is structurally sound)

**Strategic scenarios where sequential wins:**
1. **Adversarial challenge** — run builder first, then adversarial. The adversarial
   model has something concrete to attack. More productive than adversarial into void.
2. **Incremental refinement** — you want the output to get better with each pass,
   not just get different
3. **Cost control** — if the first model produces a strong spine, you can skip
   subsequent models entirely

---

### The Hybrid: Parallel Then Sequential

**What it is:** Phase 1 — parallel runs produce independent spines.
Phase 2 — sequential refinement where each model sees the merged parallel output.

**Why this is the right default for the harness:**

Phase 1 (parallel) establishes independent ground truth. What each model
finds without contamination.

Phase 2 (sequential) refines — models challenge and integrate each other's
findings. But now the starting point is evidence, not void.

The sieve runs after Phase 1 to produce the merged spine. Phase 2 models
work from the spine, not the raw prompts. This is the Liberating Structures
pattern: 1-2-4-All applied to model runs.

```
Phase 1 (parallel):
  Opus → spine_A
  Sonnet → spine_B
  Codex → spine_C

Sieve(spine_A + spine_B + spine_C) → merged_spine

Phase 2 (sequential, working from merged_spine):
  Adversarial model → challenges merged_spine
  Builder model → defends + extends
  Human (you) → ratifies
```

**Cost:** Phase 2 tokens are much cheaper because models work from the compact
spine, not the full original corpus.

---

## Cost Estimator Logic (to be built)

```python
def estimate_run_cost(
    corpus_tokens: int,
    models: list[str],
    mode: str,  # "parallel" | "sequential" | "hybrid"
    phases: int,
) -> dict:
    # Phase 1: corpus_tokens × number of models (parallel) or × 1 (sequential)
    # Phase 2: spine_tokens (much smaller) × number of models
    # spine_tokens ≈ corpus_tokens × 0.1 (rough compression ratio)
    ...
```

---

## Open Questions (TBD)

- Staging object format: JSON seed spec vs free-form prompt adapted per model?
- Persona assignment: fixed per model or configurable per run?
- How does the turn chain interact with multi-model runs? Each model turn gets receipted?
- The full prompt engineering design (hyperdimensional bumpdown — separate doc)
