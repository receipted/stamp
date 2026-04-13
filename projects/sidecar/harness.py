#!/usr/bin/env python3
"""
harness.py — Multi-model substrate harness.

Takes a JSON seed spec card, sends it to multiple models (parallel or sequential),
runs the sieve over all responses, produces a receipted multi-model spine.

Architecture:
  seed_spec.json (CONTRACT for the run)
    → staged per model (adapted, not rewritten)
    → parallel or sequential API calls
    → responses typed as claims
    → sieve produces spine
    → receipt proves: which models, which spec, what emerged

Usage:
  python3 harness.py <seed_spec.json>                    # parallel, all configured models
  python3 harness.py <seed_spec.json> --sequential       # sequential runs
  python3 harness.py <seed_spec.json> --estimate         # cost estimate only, no API calls
  python3 harness.py <seed_spec.json> --models opus,sonnet  # specific models

Persona assignments (default):
  opus:   adversarial (find what breaks, what's missing)
  sonnet: builder (find what works, what connects)
  codex:  implementer (find what can be built, what's concrete)

Matrix: model x tier x persona — all configurable.
"""

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

THINKING_LOG = "/Users/shadow/projects/thinking-log"
SPINES_DIR = "/Users/Shared/sidecar-ore/spines"

# Model pricing (per million tokens, approximate)
MODEL_PRICING = {
    "claude-opus-4-6":    {"in": 15.0,  "out": 75.0},
    "claude-sonnet-4-6":  {"in": 3.0,   "out": 15.0},
    "gpt-4.1":            {"in": 2.0,   "out": 8.0},
    "gemini-2.0-flash":   {"in": 0.1,   "out": 0.4},
}

# Default persona per model
DEFAULT_PERSONAS = {
    "claude-opus-4-6":   "adversarial",
    "claude-sonnet-4-6": "builder",
    "gpt-4.1":           "implementer",
    "gemini-2.0-flash":  "builder",
}

# Lens definitions — each persona is a typed epistemic filter
# promote_bias: claim types this lens is expected to find
# deprioritize: claim types this lens naturally misses
# Claims that survive AGAINST their lens bias are the strongest signal
LENS_SPECS = {
    "adversarial": {
        "scope": "Find what breaks, what's missing, what cannot be true",
        "promote_bias": ["constraint", "uncertainty"],
        "deprioritize": ["contract", "guarantee"],
        "failure_mode": "Produces only praise — no CONSTRAINT claims found",
        "weights": {"constraint": 1.3, "uncertainty": 1.1, "contract": 0.7, "observation": 0.9, "guarantee": 0.8},
    },
    "builder": {
        "scope": "Find what works, what's load-bearing, what the system promises",
        "promote_bias": ["contract", "relation"],
        "deprioritize": ["constraint", "uncertainty"],
        "failure_mode": "Produces only criticism — no CONTRACT claims found",
        "weights": {"contract": 1.3, "relation": 1.1, "constraint": 0.7, "uncertainty": 0.8, "guarantee": 1.0},
    },
    "implementer": {
        "scope": "Find what can be built, what connects, what the dependencies are",
        "promote_bias": ["relation", "contract"],
        "deprioritize": ["uncertainty", "guarantee"],
        "failure_mode": "Produces only abstractions — no RELATION claims with concrete interfaces",
        "weights": {"relation": 1.3, "contract": 1.1, "uncertainty": 0.8, "constraint": 1.0, "guarantee": 0.9},
    },
}

PERSONA_INSTRUCTIONS = {
    "adversarial": (
        "Your role is adversarial. Find what breaks, what's missing, what's wrong. "
        "Challenge every assumption. Your job is to produce CONSTRAINT claims — "
        "what cannot be true, what must not be allowed, what the spec fails to address. "
        "Do not be agreeable. Be rigorous."
    ),
    "builder": (
        "Your role is builder. Find what works, what connects, what's load-bearing. "
        "Your job is to produce CONTRACT claims — what this system promises, "
        "what the spec correctly identifies, what should be preserved. "
        "Be constructive but precise."
    ),
    "implementer": (
        "Your role is implementer. Find what can be built, what's concrete, "
        "what the relations between components are. "
        "Your job is to produce RELATION claims — how things connect, "
        "what depends on what, what the build sequence should be. "
        "Be specific about interfaces and dependencies."
    ),
}


# --- Pure functions ---

def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def estimate_cost(spec_text: str, models: list[str]) -> dict:
    """Pure function. Estimate cost for a run without making API calls."""
    # Rough token estimate: 4 chars per token
    input_tokens = len(spec_text) / 4
    output_tokens = input_tokens * 0.5  # responses ~50% of input length

    estimates = {}
    total = 0.0
    for model in models:
        if model not in MODEL_PRICING:
            continue
        pricing = MODEL_PRICING[model]
        cost = (input_tokens / 1_000_000 * pricing["in"] +
                output_tokens / 1_000_000 * pricing["out"])
        estimates[model] = round(cost, 4)
        total += cost

    return {"per_model": estimates, "total": round(total, 4), "input_tokens_est": int(input_tokens)}


def stage_spec_for_model(spec: dict, model: str, persona: str) -> tuple[dict, str]:
    """Pure function. Generate a lens-scoped run-spec card + prompt string.

    Returns (run_spec_card, prompt_string).
    The run_spec_card is the receipted contract for this model's run.
    The prompt string is derived from the card — no information outside the card.
    """
    lens = LENS_SPECS.get(persona, LENS_SPECS["builder"])
    persona_instruction = PERSONA_INSTRUCTIONS.get(persona, PERSONA_INSTRUCTIONS["builder"])

    # The lens-scoped run spec card
    run_spec = {
        "schema": "sidecar.run-spec.v1",
        "parent_spec_id": spec.get("card_id", "unknown"),
        "model": model,
        "persona": persona,
        "lens": lens,
        "intent": f"Review the parent spec through the {persona} lens: {lens['scope']}",
        "constraints": [
            f"Promote bias toward: {lens['promote_bias']}",
            f"Do not ignore: {lens['deprioritize']} types (finding them against bias is the strongest signal)",
            f"Failure mode to avoid: {lens['failure_mode']}",
        ],
        "output_contract": {
            "promoted": "[CONTRACT] | [CONSTRAINT] | [UNCERTAINTY] | [RELATION] | [WITNESS]",
            "contested": "[CONTESTED] claim | reason",
            "declared_loss": "[LOSS] what is missing | why it matters",
        },
    }

    # Prompt derived entirely from the card
    prompt = f"""You are participating in a multi-model substrate review.

RUN SPEC CARD:
{json.dumps(run_spec, indent=2)}

PARENT SEED SPEC:
{json.dumps(spec, indent=2)}

ROLE: {persona.upper()}
{persona_instruction}

TASK: Produce structured output as specified in the run_spec output_contract above.
Be specific. Be structural. Your output will be sieved.
"""
    return run_spec, prompt


def apply_lens_weight(claims: list[dict], persona: str) -> list[dict]:
    """Pure function. Apply lens weights to claim confidence scores.

    Claims that survive AGAINST their lens bias get the strongest boost.
    A CONTRACT claim from an adversarial lens (which deprioritizes contracts)
    is more significant than a CONTRACT claim from a builder lens.
    """
    lens = LENS_SPECS.get(persona, LENS_SPECS["builder"])
    weights = lens["weights"]
    deprioritized = lens["deprioritize"]

    weighted = []
    for c in claims:
        c = dict(c)
        ct = c.get("claim_type", "observation")
        base_weight = weights.get(ct, 1.0)

        # Extra boost if claim type is in deprioritized list — survived against the lens
        if ct in deprioritized:
            base_weight *= 1.2  # against-lens bonus
            c["against_lens"] = True  # flag for later analysis

        c["confidence"] = min(1.0, c.get("confidence", 0.8) * base_weight)
        c["lens_weight"] = base_weight
        weighted.append(c)
    return weighted


def parse_model_response(response_text: str, model: str, persona: str) -> list[dict]:
    """Pure function. Parse a model's structured response into typed claims."""
    claims = []
    lines = response_text.strip().split('\n')

    claim_id = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse [TYPE] claim text format
        for type_tag, claim_type in [
            ('[CONTRACT]', 'fact'),
            ('[CONSTRAINT]', 'constraint'),
            ('[UNCERTAINTY]', 'hypothesis'),
            ('[RELATION]', 'observation'),
            ('[WITNESS]', 'guarantee'),
            ('[CONTESTED]', 'hypothesis'),
            ('[LOSS]', 'observation'),
        ]:
            if line.upper().startswith(type_tag):
                text = line[len(type_tag):].strip()
                if text:
                    claims.append({
                        'id': claim_id,
                        'text': text,
                        'claim_type': claim_type,
                        'evidence_refs': [f'{model}-{persona}'],
                        'confidence': 0.8,
                        'source': f'{model}:{persona}',
                        'model': model,
                        'persona': persona,
                    })
                    claim_id += 1
                break

    # Fallback: if no structured format, extract sentences as observations
    if not claims:
        sentences = [s.strip() for s in response_text.split('.') if len(s.strip()) > 20]
        for s in sentences[:10]:
            claims.append({
                'id': claim_id,
                'text': s,
                'claim_type': 'observation',
                'evidence_refs': [f'{model}-{persona}'],
                'confidence': 0.6,
                'source': f'{model}:{persona}',
                'model': model,
                'persona': persona,
            })
            claim_id += 1

    return claims


# --- IO layer ---

def call_model(model: str, prompt: str, api_key: str = None) -> str:
    """IO: call a model API and return the response text."""
    import sys
    sys.path.insert(0, THINKING_LOG)

    if model.startswith('claude-'):
        import glob
        for sp in glob.glob(os.path.join(THINKING_LOG, '.venv/lib/python3*/site-packages')):
            if sp not in sys.path:
                sys.path.insert(0, sp)
        import anthropic
        key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    raise ValueError(f"Model not yet supported in harness: {model}")


def run_model(model: str, persona: str, staged_prompt: str) -> dict:
    """IO: run one model and return result dict."""
    start = time.time()
    try:
        response = call_model(model, staged_prompt)
        claims = parse_model_response(response, model, persona)
        elapsed = time.time() - start
        return {
            "model": model,
            "persona": persona,
            "status": "ok",
            "response": response,
            "claims": claims,
            "elapsed": round(elapsed, 2),
        }
    except Exception as e:
        return {
            "model": model,
            "persona": persona,
            "status": "error",
            "error": str(e),
            "claims": [],
            "elapsed": round(time.time() - start, 2),
        }


def run_harness(
    spec_path: str,
    models: list[str] = None,
    personas: dict = None,
    sequential: bool = False,
    estimate_only: bool = False,
):
    """Main harness entry point. IO layer."""
    # Load spec
    with open(spec_path) as f:
        spec = json.load(f)

    spec_text = json.dumps(spec)
    spec_hash = h(spec_text.encode())
    harness_hash = h(Path(__file__).read_bytes())

    models = models or ["claude-sonnet-4-6"]
    personas = personas or {m: DEFAULT_PERSONAS.get(m, "builder") for m in models}

    print(f"Harness run: {os.path.basename(spec_path)}")
    print(f"  spec_hash:    {spec_hash[:16]}...")
    print(f"  harness_hash: {harness_hash[:16]}...")
    print(f"  models: {models}")
    print(f"  mode: {'sequential' if sequential else 'parallel'}")
    print()

    # Cost estimate
    cost = estimate_cost(spec_text, models)
    print(f"Cost estimate:")
    for model, c in cost["per_model"].items():
        print(f"  {model}: ~${c:.4f}")
    print(f"  TOTAL: ~${cost['total']:.4f}")
    print()

    if estimate_only:
        print("(--estimate only, no API calls)")
        return

    # Stage: generate lens-scoped run-spec cards + prompts
    staged = {}
    run_specs = {}
    for m in models:
        run_spec, prompt = stage_spec_for_model(spec, m, personas[m])
        staged[m] = prompt
        run_specs[m] = run_spec
        print(f"  Staged for {m} ({personas[m]}): lens={run_spec['lens']['scope'][:50]}...")

    # Run models
    all_claims = []
    results = {}

    if sequential:
        print("Running models sequentially...")
        for model in models:
            print(f"  {model} ({personas[model]})...", end=" ", flush=True)
            result = run_model(model, personas[model], staged[model])
            results[model] = result
            print(f"{result['status']} ({result['elapsed']}s, {len(result['claims'])} claims)")
            weighted = apply_lens_weight(result["claims"], personas[model])
            all_claims.extend(weighted)
    else:
        print("Running models in parallel...")
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(run_model, m, personas[m], staged[m]): m
                for m in models
            }
            for future in as_completed(futures):
                model = futures[future]
                result = future.result()
                results[model] = result
                print(f"  {model} ({personas[model]}): {result['status']} "
                      f"({result['elapsed']}s, {len(result['claims'])} claims)")
                weighted = apply_lens_weight(result["claims"], personas[model])
                all_claims.extend(weighted)

    if not all_claims:
        print("\nERROR: no claims produced")
        return

    print(f"\nTotal claims from all models: {len(all_claims)}")

    # Run sieve
    print("Running sieve...")
    sys.path.insert(0, THINKING_LOG)
    import glob as g
    for sp in g.glob(os.path.join(THINKING_LOG, '.venv/lib/python3*/site-packages')):
        if sp not in sys.path:
            sys.path.insert(0, sp)
    from src.surface.sieve import promote

    topic = {
        "handle": spec.get("card_id", "harness-run"),
        "title": spec.get("title", "Multi-model harness run"),
        "description": spec.get("intent", ""),
        "provenance_mode": "open",
        "keywords": [],
    }

    promoted, contested, deferred, loss = promote(all_claims, topic)

    print(f"  Promoted: {len(promoted)} | Contested: {len(contested)} | Loss: {len(loss)}")

    # Build output
    output_bytes = json.dumps({
        "promoted": promoted,
        "contested": contested,
        "declared_loss": loss,
    }, sort_keys=True, default=str).encode()
    output_hash = h(output_bytes)

    receipt = {
        "schema": "sidecar.harness-receipt.v1",
        "spec_hash": spec_hash,
        "harness_hash": harness_hash,
        "models_run": list(results.keys()),
        "personas": personas,
        "mode": "sequential" if sequential else "parallel",
        "output_hash": output_hash,
        "promoted_count": len(promoted),
        "contested_count": len(contested),
        "loss_count": len(loss),
        "produced_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save
    os.makedirs(SPINES_DIR, exist_ok=True)
    base = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%S')}_{output_hash[:12]}"
    spine_path = os.path.join(SPINES_DIR, f"{base}.harness-spine.json")
    receipt_path = os.path.join(SPINES_DIR, f"{base}.harness-receipt.json")

    with open(spine_path, "w") as f:
        json.dump({"promoted": promoted, "contested": contested, "declared_loss": loss},
                  f, indent=2, default=str)
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"\nSaved:")
    print(f"  spine:   {os.path.basename(spine_path)}")
    print(f"  receipt: {os.path.basename(receipt_path)}")
    print(f"  output_hash: {output_hash[:16]}...")
    print()
    print("PROMOTED (multi-model spine):")
    for c in promoted[:10]:
        model = c.get('model', '?')
        print(f"  [{model}][{c['claim_type']}] {c.get('text','')[:90]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 harness.py <seed_spec.json>")
        print("  python3 harness.py <seed_spec.json> --sequential")
        print("  python3 harness.py <seed_spec.json> --estimate")
        print("  python3 harness.py <seed_spec.json> --models claude-sonnet-4-6,claude-opus-4-6")
        sys.exit(1)

    spec_path = sys.argv[1]
    sequential = "--sequential" in sys.argv
    estimate_only = "--estimate" in sys.argv

    models = None
    for arg in sys.argv[2:]:
        if arg.startswith("--models="):
            models = arg.split("=", 1)[1].split(",")

    if not os.path.exists(spec_path):
        print(f"ERROR: spec not found: {spec_path}")
        sys.exit(1)

    run_harness(spec_path, models=models, sequential=sequential, estimate_only=estimate_only)
