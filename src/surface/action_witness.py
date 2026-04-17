"""Action-witness verification — detecting unwitnessed operational claims.

We are not trying to detect lies.
We are trying to detect unwitnessed operational claims.

Target interaction:
    Human: "Did you run the API bridge, or did you fake it?"
    Model: <may answer confidently either way>
    Substrate: checks witnesses, returns verdict

Verdicts:
    WITNESSED           — claim has corroborating witness(es)
    UNWITNESSED         — no witnesses found for this claim
    CONTRADICTED        — witness evidence contradicts the claim
    INSUFFICIENT_EVIDENCE — some evidence exists but doesn't reach threshold

Architecture:
    This module is PURE. No I/O. No subprocess calls. No file reads.

    Witness collection is I/O — that lives in witness_collector.py.
    This module takes collected witnesses and operational claims as input,
    and produces stamped verdicts as output.

    Same claims + same witnesses = same verdicts, always.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

class Verdict(str, Enum):
    WITNESSED = "WITNESSED"
    UNWITNESSED = "UNWITNESSED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# ---------------------------------------------------------------------------
# Witness types — the five operational evidence kinds
# ---------------------------------------------------------------------------

class WitnessKind(str, Enum):
    """The five witness types we care about for operational claims."""
    COMMAND_RECEIPT = "command_receipt"        # subprocess ran, got exit code
    PROCESS_WITNESS = "process_witness"       # PID existed, was running
    PORT_HEALTH = "port_health"               # port listening, health responded
    LOG_WITNESS = "log_witness"               # log file contained expected output
    ARTIFACT_EFFECT = "artifact_effect"       # file created/modified, output exists


@dataclass(frozen=True)
class ActionWitness:
    """A piece of evidence collected from the environment.

    The collector (I/O layer) populates these. This module only reads them.
    Frozen so witnesses can't be mutated after collection.
    """
    kind: WitnessKind
    subject: str          # what was observed (command, process name, port, path)
    observed: bool        # was the expected state found?
    detail: str = ""      # human-readable observation ("port 8080 listening", "exit code 0")
    timestamp: str = ""   # ISO timestamp of observation
    authority: str = "system"  # who/what collected this witness

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "subject": self.subject,
            "observed": self.observed,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "authority": self.authority,
        }


# ---------------------------------------------------------------------------
# Operational claims — what the agent says it did
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ActionClaim:
    """An operational claim extracted from agent text.

    Examples:
        "I started the API bridge on port 8080"
        → ActionClaim(action="start", subject="API bridge", qualifiers={"port": 8080})

        "Tests passed with zero failures"
        → ActionClaim(action="run_tests", subject="test suite", qualifiers={"failures": 0})
    """
    action: str           # verb: "start", "run", "create", "stop", "modify"
    subject: str          # what: "API bridge", "test suite", "config file"
    qualifiers: dict[str, Any] = field(default_factory=dict)  # port, path, exit_code, etc.
    source_text: str = ""  # the original text this was extracted from

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "subject": self.subject,
            "qualifiers": self.qualifiers,
            "source_text": self.source_text,
        }


# ---------------------------------------------------------------------------
# Verdict with reasoning
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ActionVerdict:
    """The result of checking a claim against available witnesses."""
    claim: ActionClaim
    verdict: Verdict
    witnesses: list[ActionWitness]  # witnesses that were consulted
    reasoning: str                   # why this verdict was reached

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "verdict": self.verdict.value,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "reasoning": self.reasoning,
        }


# ---------------------------------------------------------------------------
# Matching — which witnesses are relevant to which claims
# ---------------------------------------------------------------------------

# Action verbs → witness kinds that could corroborate them
_ACTION_WITNESS_MAP: dict[str, list[WitnessKind]] = {
    "start":   [WitnessKind.PROCESS_WITNESS, WitnessKind.PORT_HEALTH, WitnessKind.LOG_WITNESS],
    "run":     [WitnessKind.COMMAND_RECEIPT, WitnessKind.LOG_WITNESS, WitnessKind.ARTIFACT_EFFECT],
    "create":  [WitnessKind.ARTIFACT_EFFECT, WitnessKind.COMMAND_RECEIPT],
    "modify":  [WitnessKind.ARTIFACT_EFFECT, WitnessKind.LOG_WITNESS],
    "stop":    [WitnessKind.PROCESS_WITNESS, WitnessKind.PORT_HEALTH],
    "delete":  [WitnessKind.ARTIFACT_EFFECT, WitnessKind.COMMAND_RECEIPT],
    "install": [WitnessKind.COMMAND_RECEIPT, WitnessKind.ARTIFACT_EFFECT],
    "deploy":  [WitnessKind.COMMAND_RECEIPT, WitnessKind.PORT_HEALTH, WitnessKind.LOG_WITNESS],
    "test":    [WitnessKind.COMMAND_RECEIPT, WitnessKind.LOG_WITNESS, WitnessKind.ARTIFACT_EFFECT],
}

# Actions where absence is the expected state — observed=False supports the claim.
# "I stopped the server" is corroborated by the server NOT running.
# "I deleted the file" is corroborated by the file NOT existing.
_NEGATIVE_POLARITY_ACTIONS = frozenset({"stop", "delete", "remove", "kill", "teardown"})


def _normalize_subject(s: str) -> set[str]:
    """Break a subject into normalized tokens for fuzzy matching. Pure.

    "API bridge" → {"api", "bridge"}
    "api_bridge" → {"api", "bridge"}
    "pytest tests/" → {"pytest", "tests"}
    """
    import re
    # Split on whitespace, underscores, hyphens, slashes, dots, colons
    tokens = re.split(r'[\s_\-/\.:]+', s.lower())
    return {t for t in tokens if t}


def _relevant_witnesses(
    claim: ActionClaim,
    witnesses: list[ActionWitness],
) -> list[ActionWitness]:
    """Find witnesses relevant to a claim. Pure.

    Matches on:
    1. Witness kind appropriate for the action verb
    2. Subject token overlap (normalized — "API bridge" matches "api_bridge")
    3. Qualifier match (port numbers, paths, etc.)
    """
    if claim.action not in _ACTION_WITNESS_MAP:
        # Unknown verb — return empty. The adjudicator will see no relevant
        # witnesses and can decide the verdict (UNWITNESSED or downgraded).
        # This is safer than matching against every witness kind, which would
        # let unsupported verbs like "restart" silently become WITNESSED.
        return []

    expected_kinds = _ACTION_WITNESS_MAP[claim.action]
    relevant = []

    claim_tokens = _normalize_subject(claim.subject)
    claim_port = claim.qualifiers.get("port")
    claim_path = claim.qualifiers.get("path", "")

    for w in witnesses:
        if w.kind not in expected_kinds:
            continue

        # Subject match: any shared token between claim and witness
        w_tokens = _normalize_subject(w.subject)
        subject_match = bool(claim_tokens & w_tokens)

        # Qualifier match: port or path if specified
        qualifier_match = False
        if claim_port and w.kind == WitnessKind.PORT_HEALTH:
            qualifier_match = str(claim_port) in w.subject or str(claim_port) in w.detail

        if claim_path and w.kind == WitnessKind.ARTIFACT_EFFECT:
            qualifier_match = claim_path in w.subject

        if subject_match or qualifier_match:
            relevant.append(w)

    return relevant


# ---------------------------------------------------------------------------
# Adjudication — the pure verdict engine
# ---------------------------------------------------------------------------

def _is_corroborating(witness: ActionWitness, action: str) -> bool:
    """Does this witness support the claim? Pure.

    For positive-polarity actions (start, run, create): observed=True supports.
    For negative-polarity actions (stop, delete): observed=False supports.

    "I stopped the server" + process NOT found → corroborating.
    "I started the server" + process NOT found → contradicting.
    """
    if action in _NEGATIVE_POLARITY_ACTIONS:
        return not witness.observed
    return witness.observed


def adjudicate_claim(
    claim: ActionClaim,
    witnesses: list[ActionWitness],
) -> ActionVerdict:
    """Produce a verdict for a single claim against available witnesses. Pure.

    Polarity-aware: negative-state actions (stop, delete) expect absence,
    so observed=False corroborates and observed=True contradicts.

    Logic:
    - No relevant witnesses → UNWITNESSED
    - All relevant witnesses contradict (polarity-adjusted) → CONTRADICTED
    - Mix of corroborating/contradicting → INSUFFICIENT_EVIDENCE
    - All relevant witnesses corroborate → WITNESSED
    """
    relevant = _relevant_witnesses(claim, witnesses)

    if not relevant:
        return ActionVerdict(
            claim=claim,
            verdict=Verdict.UNWITNESSED,
            witnesses=[],
            reasoning=f"No witnesses found for '{claim.action} {claim.subject}'",
        )

    corroborating = [w for w in relevant if _is_corroborating(w, claim.action)]
    contradicting = [w for w in relevant if not _is_corroborating(w, claim.action)]

    polarity = "negative" if claim.action in _NEGATIVE_POLARITY_ACTIONS else "positive"

    if not corroborating and contradicting:
        contra_details = "; ".join(w.detail for w in contradicting if w.detail)
        return ActionVerdict(
            claim=claim,
            verdict=Verdict.CONTRADICTED,
            witnesses=relevant,
            reasoning=f"Evidence contradicts claim ({polarity} polarity): {contra_details}",
        )

    if corroborating and contradicting:
        return ActionVerdict(
            claim=claim,
            verdict=Verdict.INSUFFICIENT_EVIDENCE,
            witnesses=relevant,
            reasoning=(
                f"{len(corroborating)} witness(es) corroborate, "
                f"{len(contradicting)} contradict ({polarity} polarity)"
            ),
        )

    # All relevant witnesses corroborate
    corr_details = "; ".join(w.detail for w in corroborating if w.detail)
    return ActionVerdict(
        claim=claim,
        verdict=Verdict.WITNESSED,
        witnesses=relevant,
        reasoning=f"Corroborated by {len(corroborating)} witness(es): {corr_details}",
    )


def adjudicate(
    claims: list[ActionClaim],
    witnesses: list[ActionWitness],
) -> list[ActionVerdict]:
    """Adjudicate all claims against available witnesses. Pure.

    Returns one verdict per claim, in the same order as the input claims.
    """
    return [adjudicate_claim(c, witnesses) for c in claims]


# ---------------------------------------------------------------------------
# Summary projection — for the demo receipt
# ---------------------------------------------------------------------------

def verdict_summary(verdicts: list[ActionVerdict]) -> dict[str, Any]:
    """Summarize verdicts into a receipt-ready dict. Pure."""
    by_verdict = {}
    for v in verdicts:
        key = v.verdict.value
        by_verdict.setdefault(key, [])
        by_verdict[key].append({
            "action": v.claim.action,
            "subject": v.claim.subject,
            "reasoning": v.reasoning,
        })

    return {
        "total_claims": len(verdicts),
        "witnessed": len([v for v in verdicts if v.verdict == Verdict.WITNESSED]),
        "unwitnessed": len([v for v in verdicts if v.verdict == Verdict.UNWITNESSED]),
        "contradicted": len([v for v in verdicts if v.verdict == Verdict.CONTRADICTED]),
        "insufficient": len([v for v in verdicts if v.verdict == Verdict.INSUFFICIENT_EVIDENCE]),
        "verdicts": by_verdict,
    }
