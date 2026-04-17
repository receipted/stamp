"""Epistemic tagger — classifies each relay turn's epistemic delta.

Runs as a lightweight post-hook after every model response in the relay.
Pure heuristic for v0 (< 1ms overhead, no model call). Future: Haiku
as real-time tagger for semantic classification.

Epistemic event types (from the protocol spec):
- belief_formed: new assertion or claim
- belief_revised: modification of a prior belief
- tension_detected: contradiction or disagreement surfaced
- tension_resolved: prior tension explicitly resolved
- question_posed: new question or uncertainty raised
- evidence_cited: reference to sources, data, or prior evidence

Each turn can emit multiple epistemic events — a single response
might form a belief AND detect a tension.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .kernel import StoreProtocol
from .models import LedgerAction, LedgerEvent

logger = logging.getLogger("surface.epistemic_tagger")


# --- Epistemic event types ---

BELIEF_FORMED = "belief_formed"
BELIEF_REVISED = "belief_revised"
TENSION_DETECTED = "tension_detected"
TENSION_RESOLVED = "tension_resolved"
QUESTION_POSED = "question_posed"
EVIDENCE_CITED = "evidence_cited"

ALL_TYPES = frozenset({
    BELIEF_FORMED, BELIEF_REVISED, TENSION_DETECTED,
    TENSION_RESOLVED, QUESTION_POSED, EVIDENCE_CITED,
})


@dataclass
class EpistemicTag:
    """A single epistemic event detected in a turn."""
    event_type: str
    confidence: float  # 0-1 heuristic confidence
    span: str = ""     # the text fragment that triggered this tag
    detail: str = ""   # human-readable explanation


@dataclass
class TurnClassification:
    """Full epistemic classification of a single turn."""
    turn_id: str
    actor: str
    tags: list[EpistemicTag] = field(default_factory=list)
    claim_count: int = 0
    question_count: int = 0
    text_length: int = 0

    @property
    def event_types(self) -> list[str]:
        return [t.event_type for t in self.tags]

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "actor": self.actor,
            "event_types": self.event_types,
            "tags": [
                {
                    "event_type": t.event_type,
                    "confidence": round(t.confidence, 2),
                    "span": t.span[:200],
                    "detail": t.detail,
                }
                for t in self.tags
            ],
            "claim_count": self.claim_count,
            "question_count": self.question_count,
            "text_length": self.text_length,
        }


# --- Heuristic patterns ---

# Belief formation: assertive statements
_BELIEF_PATTERNS = [
    re.compile(r"\b(?:I (?:think|believe|conclude|suggest|recommend)|the (?:key|main|core|central) (?:point|issue|finding|insight))\b", re.I),
    re.compile(r"\b(?:this (?:means|suggests|indicates|implies|shows)|based on (?:this|the evidence|what we know))\b", re.I),
    re.compile(r"\b(?:in (?:fact|reality|practice)|the evidence (?:shows|suggests|indicates))\b", re.I),
    re.compile(r"\b(?:it(?:'s| is) (?:clear|evident|apparent|likely) that)\b", re.I),
]

# Belief revision: changing a prior stance
_REVISION_PATTERNS = [
    re.compile(r"\b(?:actually|on (?:second thought|reflection)|I (?:was wrong|stand corrected|need to revise))\b", re.I),
    re.compile(r"\b(?:however|but (?:now|upon)|re-?evaluat|reconsider|update (?:my|our|the))\b", re.I),
    re.compile(r"\b(?:contrary to (?:what|my)|this changes|revising (?:my|our))\b", re.I),
    re.compile(r"\b(?:not (?:quite|exactly) (?:right|correct|accurate)|more (?:nuanced|complex) than)\b", re.I),
]

# Tension detection: contradictions, disagreement
_TENSION_PATTERNS = [
    re.compile(r"\b(?:contradicts?|conflicts? with|tension between|at odds with|inconsistent with)\b", re.I),
    re.compile(r"\b(?:on (?:the )?one hand.*on (?:the )?other|two (?:competing|conflicting)|trade-?off)\b", re.I),
    re.compile(r"\b(?:disagree|push ?back|counter-?argument|counter-?point|problematic)\b", re.I),
    re.compile(r"\b(?:but this (?:conflicts|contradicts)|this (?:doesn't|does not) align)\b", re.I),
]

# Tension resolution
_RESOLUTION_PATTERNS = [
    re.compile(r"\b(?:resolv(?:es?|ed|ing)|reconcil(?:es?|ed|ing)|synthe(?:sis|size)|integrate[sd]?)\b", re.I),
    re.compile(r"\b(?:the (?:resolution|answer|solution) is|this (?:resolves|settles|clarifies))\b", re.I),
    re.compile(r"\b(?:both (?:are|can be) (?:true|right)|compatible (?:if|when)|false dichotomy)\b", re.I),
]

# Question posing
_QUESTION_PATTERNS = [
    re.compile(r"\?\s*$", re.M),  # sentences ending in ?
    re.compile(r"\b(?:what (?:if|about)|how (?:do|does|would|could)|why (?:is|does|would))\b", re.I),
    re.compile(r"\b(?:the (?:question|unknown|gap|uncertainty) (?:is|remains)|we (?:(?:still )?don['\u2019]t|do not) (?:know|understand))\b", re.I),
    re.compile(r"\b(?:unclear|uncertain|unresolved|unknown|open question|needs? (?:investigation|research|clarification))\b", re.I),
]

# Evidence citation
_EVIDENCE_PATTERNS = [
    re.compile(r"\b(?:according to|as (?:noted|mentioned|stated|shown) (?:in|by|earlier))\b", re.I),
    re.compile(r"\b(?:the (?:data|evidence|research|study|source) (?:shows?|suggests?|indicates?))\b", re.I),
    re.compile(r"\b(?:citing|referenced|per the|from the (?:document|source|snapshot|thread))\b", re.I),
    re.compile(r"\b(?:\d+%|\$[\d,.]+|(?:source|snapshot|thread|claim)[:_])\b", re.I),
]


def classify_turn(
    text: str,
    turn_id: str = "",
    actor: str = "",
    *,
    prior_turns: list[str] | None = None,
) -> TurnClassification:
    """Classify a turn's epistemic content using heuristics.

    Args:
        text: The turn's text content.
        turn_id: ID of the turn artifact.
        actor: The actor who produced this turn.
        prior_turns: Optional list of recent prior turn texts for
            revision/tension detection context.

    Returns:
        TurnClassification with all detected epistemic tags.
    """
    result = TurnClassification(
        turn_id=turn_id,
        actor=actor,
        text_length=len(text),
    )

    if not text.strip():
        return result

    # Count questions
    questions = re.findall(r"[^.!?]*\?", text)
    result.question_count = len(questions)

    # Count claim-like sentences (assertive, non-question, > 20 chars)
    sentences = re.split(r"[.!]\s+", text)
    claims = [s for s in sentences if len(s.strip()) > 20 and "?" not in s]
    result.claim_count = len(claims)

    # Run pattern matching
    _match_patterns(text, _BELIEF_PATTERNS, BELIEF_FORMED, result)
    _match_patterns(text, _REVISION_PATTERNS, BELIEF_REVISED, result)
    _match_patterns(text, _TENSION_PATTERNS, TENSION_DETECTED, result)
    _match_patterns(text, _RESOLUTION_PATTERNS, TENSION_RESOLVED, result)
    _match_patterns(text, _EVIDENCE_PATTERNS, EVIDENCE_CITED, result)

    # Questions: count-based + pattern-based
    _match_patterns(text, _QUESTION_PATTERNS, QUESTION_POSED, result)
    if result.question_count > 0 and QUESTION_POSED not in result.event_types:
        conf = min(0.9, 0.5 + result.question_count * 0.1)
        best_q = questions[0].strip() if questions else ""
        result.tags.append(EpistemicTag(
            event_type=QUESTION_POSED,
            confidence=conf,
            span=best_q[:200],
            detail=f"{result.question_count} question(s) detected",
        ))

    # Boost belief_formed if many assertive claims and no other tags
    if result.claim_count >= 3 and BELIEF_FORMED not in result.event_types:
        result.tags.append(EpistemicTag(
            event_type=BELIEF_FORMED,
            confidence=0.5,
            span=claims[0][:200] if claims else "",
            detail=f"{result.claim_count} assertive sentences detected",
        ))

    # Sort by confidence descending
    result.tags.sort(key=lambda t: t.confidence, reverse=True)

    return result


def emit_epistemic_events(
    store: StoreProtocol,
    turn_id: str,
    classification: TurnClassification,
    *,
    topic_handle: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
) -> list[LedgerEvent]:
    """Emit ledger events for each epistemic tag in a classification.

    Returns the list of emitted events.
    """
    if not classification.tags:
        return []

    events: list[LedgerEvent] = []

    for tag in classification.tags:
        # Only emit tags above threshold
        if tag.confidence < 0.4:
            continue

        event = LedgerEvent(
            action=LedgerAction.epistemic_event,
            subject_id=turn_id,
            subject_type="conversation_turn",
            details={
                "event_type": tag.event_type,
                "confidence": round(tag.confidence, 2),
                "span": tag.span[:200],
                "detail": tag.detail,
                "actor": classification.actor,
                "model_name": model_name,
                "provider": provider,
                "topic_handle": topic_handle,
                "claim_count": classification.claim_count,
                "question_count": classification.question_count,
                "text_length": classification.text_length,
            },
        )
        store.append_event(event)
        events.append(event)

    if events:
        logger.debug(
            "Emitted %d epistemic events for turn %s: %s",
            len(events),
            turn_id,
            [e.details["event_type"] for e in events],
        )

    return events


def tag_and_emit(
    store: StoreProtocol,
    text: str,
    turn_id: str,
    actor: str,
    *,
    topic_handle: str | None = None,
    model_name: str | None = None,
    provider: str | None = None,
) -> TurnClassification:
    """Convenience: classify a turn and emit events in one call.

    This is the primary entry point for the relay hook.
    """
    classification = classify_turn(text, turn_id=turn_id, actor=actor)
    emit_epistemic_events(
        store,
        turn_id,
        classification,
        topic_handle=topic_handle,
        model_name=model_name,
        provider=provider,
    )
    return classification


# --- Private helpers ---


def _match_patterns(
    text: str,
    patterns: list[re.Pattern],
    event_type: str,
    result: TurnClassification,
) -> None:
    """Match regex patterns and add tags to result."""
    matches = []
    for pat in patterns:
        for m in pat.finditer(text):
            matches.append(m)

    if matches:
        # Confidence based on match count and text coverage
        coverage = sum(m.end() - m.start() for m in matches) / max(len(text), 1)
        conf = min(0.95, 0.5 + len(matches) * 0.1 + coverage * 2)
        best_match = max(matches, key=lambda m: m.end() - m.start())
        result.tags.append(EpistemicTag(
            event_type=event_type,
            confidence=round(conf, 2),
            span=best_match.group()[:200],
            detail=f"{len(matches)} pattern match(es)",
        ))


# ---------------------------------------------------------------------------
# Backfill — batch-tag existing thread history
# ---------------------------------------------------------------------------

def backfill_epistemic_events(
    store: StoreProtocol,
    *,
    skip_human: bool = True,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Backfill epistemic events for all existing conversation turns.

    Iterates every conversation_turn artifact, classifies it, and emits
    epistemic events for any that don't already have them. Idempotent —
    skips turns that already have epistemic events.

    Args:
        store: Storage backend.
        skip_human: If True (default), skip human-authored turns.
        dry_run: If True, classify but don't emit events.

    Returns:
        Summary dict with counts and per-turn results.
    """
    from .models import ArtifactType

    # Collect turn IDs that already have epistemic events (idempotency)
    # Use read_all to avoid query_ledger's default limit
    if force:
        already_tagged: set[str] = set()  # force re-tags everything
    else:
        all_events = store.read_all_ledger_events()
        already_tagged = {
            e.subject_id for e in all_events
            if e.action.value == "epistemic.event"
        }

    # Iterate all conversation turns
    art_ids = store.list_artifact_ids_by_type("conversation_turn")
    total = 0
    tagged = 0
    skipped_human = 0
    skipped_existing = 0
    skipped_empty = 0
    events_emitted = 0
    per_type: dict[str, int] = {}
    per_actor: dict[str, int] = {}

    for aid in art_ids:
        art = store.get_artifact(aid)
        if art is None or art.type != ArtifactType.conversation_turn:
            continue

        total += 1
        turn_id = art.content.get("turn_id", "")
        actor = art.content.get("actor", "")
        text = art.content.get("text", "")

        # Skip human turns
        if skip_human and actor.startswith("human:"):
            skipped_human += 1
            continue

        # Skip already tagged turns
        if turn_id in already_tagged:
            skipped_existing += 1
            continue

        # Skip empty/trivial text
        if not text or len(text.strip()) < 20:
            skipped_empty += 1
            continue

        # Classify
        classification = classify_turn(text, turn_id=turn_id, actor=actor)

        # Check if there are any tags above threshold
        actionable = [t for t in classification.tags if t.confidence >= 0.4]
        if not actionable:
            continue

        # Extract model info from provenance, fall back to actor registry
        model_name = art.provenance.model_name
        provider = art.provenance.provider
        if not provider and actor.startswith("agent:"):
            try:
                from .actors import get_actor as _get_actor
                a = _get_actor(actor)
                if a and a.metadata:
                    provider = provider or a.metadata.get("provider")
                    model_name = model_name or a.metadata.get("model")
            except Exception:
                pass

        if not dry_run:
            events = emit_epistemic_events(
                store,
                turn_id,
                classification,
                model_name=model_name,
                provider=provider,
            )
            events_emitted += len(events)

        tagged += 1
        # Track per-type counts
        for t in actionable:
            per_type[t.event_type] = per_type.get(t.event_type, 0) + 1
        # Track per-actor counts
        per_actor[actor] = per_actor.get(actor, 0) + 1

    return {
        "total_turns": total,
        "tagged": tagged,
        "events_emitted": events_emitted,
        "skipped_human": skipped_human,
        "skipped_existing": skipped_existing,
        "skipped_empty": skipped_empty,
        "per_event_type": per_type,
        "per_actor": per_actor,
        "dry_run": dry_run,
    }
