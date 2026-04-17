"""FP Kernel — pure functional core of the Surface substrate.

All functions in this module are PURE: no I/O, no side effects, no store access.
They take data in, return data out. Deterministic. Composable. Testable.

Architecture:
  Layer 0: StoreProtocol — abstract IO boundary (the ONLY place IO happens)
  Layer 1: Types         — canonical immutable data structures
  Layer 2: Reducers      — event list → computed state (no store)
  Layer 3: Operators     — pure transforms over claim graphs
  Layer 4: Validators    — schema invariant checks
  Layer 5: Conflict      — detect contradictions and tensions
  Layer 6: Replay        — deterministic snapshot reconstruction

Design principles:
  - Reducers take event lists, not store references
  - Status is computed, never stored
  - All functions return new data, never mutate inputs
  - Same inputs → same outputs always (no randomness, no timestamps)
  - Dependency injection for anything that needs I/O
  - StoreProtocol is the single IO boundary — all domain logic programs
    against it, never against a concrete backend
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from pathlib import Path

from .models import Artifact, LedgerEvent, Snapshot


# ===========================================================================
# Layer 0: Store Protocol — the IO boundary
# ===========================================================================


@runtime_checkable
class StoreProtocol(Protocol):
    """Abstract store interface for the Surface kernel.

    Any storage backend that implements these methods can drive the full
    domain logic layer. The interface is deliberately minimal — only methods
    that Layer 2+ modules actually call.

    Current implementation: SurfaceStore (filesystem, storage.py)
    Future: Postgres, S3, Letta agent memory, in-memory (fast tests)
    """

    writer_id: str
    base: Path

    # --- Generic file operations ---

    def write_file(self, path: Path, data: bytes) -> None:
        """Atomically write raw bytes to a path.

        Filesystem impl: temp file + fsync + rename.
        Postgres impl: upsert to a files table keyed by path.
        """
        ...

    def write_json(self, path: Path, obj: dict | list) -> None:
        """Atomically write a JSON-serializable object to a path."""
        ...

    def read_file(self, path: Path) -> bytes | None:
        """Read raw bytes from a path. None if not found."""
        ...

    # --- Blob operations (content-addressable) ---

    def store_blob(self, content: str | bytes) -> str:
        """Store content, return content hash (sha256:hex)."""
        ...

    def read_blob(self, content_hash: str) -> str | None:
        """Read blob by content hash. None if not found."""
        ...

    # --- Snapshot operations ---

    def save_snapshot(self, snapshot: Snapshot) -> Snapshot: ...
    def get_snapshot(self, snapshot_id: str) -> Snapshot | None: ...
    def list_snapshots(self) -> list[Snapshot]: ...
    def snapshot_exists(self, snapshot_id: str) -> bool: ...

    # --- Artifact operations ---

    def save_artifact(self, artifact: Artifact, *, allow_overwrite: bool = False) -> Artifact: ...
    def get_artifact(self, artifact_id: str) -> Artifact | None: ...
    def list_artifacts(self) -> list[Artifact]: ...
    def artifact_exists(self, artifact_id: str) -> bool: ...

    # --- Indexed artifact lookups ---

    def list_artifact_ids_by_type(self, art_type: str) -> list[str]: ...
    def list_artifact_ids_by_content_field(self, field: str, value: str) -> list[str]: ...
    def find_artifacts_by_type_and_content(
        self, art_type: str, field: str, value: str,
    ) -> list[Artifact]: ...

    # --- Ledger operations (append-only event log) ---

    def append_event(self, event: LedgerEvent) -> None:
        """Append an event to the ledger with hash chaining.

        This is the ONLY mutation path for the ledger. All domain modules
        call this instead of reaching into private storage internals.
        """
        ...

    def query_ledger(
        self,
        action: str | None = None,
        subject_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[LedgerEvent]: ...

    def read_all_ledger_events(self) -> list[LedgerEvent]: ...

    # --- Projection tracing ---

    def trace_projection(
        self,
        query: str,
        source_ids: list[str] | None = None,
        anchor_event_id: str | None = None,
        base_head_event_id: str | None = None,
    ) -> None: ...

    # --- Policy config ---

    def load_policy_config(self) -> dict: ...
    def save_policy_config(self, config: dict) -> None: ...

    # --- Chain verification ---

    def verify_ledger_chain(self) -> dict: ...


# ===========================================================================
# Layer 1: Canonical Types
# ===========================================================================


@dataclass(frozen=True)
class ClaimRecord:
    """Immutable claim — the substrate primitive."""
    claim_id: str
    text: str
    confidence: float = 0.5
    claim_role: str | None = None       # observation, goal, constraint, hypothesis
    type_key: str | None = None         # normalized taxonomy key
    binding_tier: str = "observed"      # observed → proposed → ratified
    parent_claim_id: str | None = None  # tree nesting
    source: str | None = None
    inquiry_id: str | None = None


@dataclass(frozen=True)
class EventRecord:
    """Immutable ledger event for reducer consumption."""
    id: str
    action: str
    subject_id: str | None = None
    subject_type: str | None = None
    details: dict = field(default_factory=dict)
    timestamp: str = ""
    writer_id: str | None = None


@dataclass(frozen=True)
class InquiryStatus:
    """Computed inquiry status from event reduction."""
    inquiry_id: str
    status: str  # open, reviewing, resolved, superseded, archived, exploring, clustering, candidate
    review_count: int = 0
    has_adjudication: bool = False
    is_superseded: bool = False
    is_archived: bool = False
    superseded_by: str | None = None


@dataclass(frozen=True)
class MutationStatus:
    """Computed mutation status from event reduction."""
    mutation_id: str
    status: str  # pending, ratified, rejected
    ratified_by: str | None = None
    rejected_by: str | None = None


@dataclass(frozen=True)
class PromotionEligibility:
    """Result of evaluating claim promotion eligibility."""
    claim_id: str
    eligible: bool
    target_tier: str | None = None
    checks: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)


@dataclass(frozen=True)
class ConflictReport:
    """Detected conflict between claims or options."""
    conflict_type: str  # contradiction, tension, coverage_gap, stale_evidence
    claim_ids: tuple = ()
    description: str = ""
    severity: float = 0.5  # 0=minor, 1=critical


@dataclass(frozen=True)
class DiffResult:
    """Pure diff computation result."""
    changed: bool
    added_lines: int = 0
    removed_lines: int = 0
    unified_diff: str = ""


@dataclass(frozen=True)
class ValidationResult:
    """Schema validation check result."""
    valid: bool
    errors: tuple = ()
    warnings: tuple = ()


@dataclass(frozen=True)
class ReplaySnapshot:
    """Deterministic state snapshot at a ledger position."""
    head_event_id: str
    event_count: int
    content_hash: str
    inquiry_statuses: dict = field(default_factory=dict)
    claim_count: int = 0
    artifact_count: int = 0


# ===========================================================================
# Layer 2: Reducers — event list → computed state
# ===========================================================================


def reduce_inquiry_status(events: list[dict], inquiry_id: str) -> InquiryStatus:
    """Reduce ledger events to compute inquiry status.

    Pure function: takes flat event list, returns computed status.
    Same events → same status, always.
    """
    review_count = 0
    has_adjudication = False
    is_superseded = False
    is_archived = False
    superseded_by = None
    latest_status = "open"

    # Status-relevant actions in priority order
    for evt in events:
        action = evt.get("action", "")
        sid = evt.get("subject_id", "")
        details = evt.get("details", {})

        if sid != inquiry_id:
            continue

        if action == "inquiry.created":
            latest_status = "open"
        elif action == "inquiry.review_submitted":
            review_count += 1
            if latest_status == "open":
                latest_status = "reviewing"
        elif action == "inquiry.adjudicated":
            has_adjudication = True
            latest_status = "resolved"
        elif action == "inquiry.superseded":
            is_superseded = True
            latest_status = "superseded"
            superseded_by = details.get("superseded_by")
        elif action == "inquiry.archived":
            is_archived = True
            latest_status = "archived"
        elif action == "inquiry.exploring":
            latest_status = "exploring"
        elif action == "inquiry.clustering":
            latest_status = "clustering"
        elif action == "inquiry.candidate_proposed":
            latest_status = "candidate"
        elif action == "inquiry.active_promoted":
            latest_status = "active"

    return InquiryStatus(
        inquiry_id=inquiry_id,
        status=latest_status,
        review_count=review_count,
        has_adjudication=has_adjudication,
        is_superseded=is_superseded,
        is_archived=is_archived,
        superseded_by=superseded_by,
    )


def reduce_mutation_status(events: list[dict], mutation_id: str) -> MutationStatus:
    """Reduce events to compute mutation status."""
    status = "pending"
    ratified_by = None
    rejected_by = None

    for evt in events:
        if evt.get("subject_id") != mutation_id:
            continue
        action = evt.get("action", "")
        details = evt.get("details", {})

        if action == "mutation.ratified":
            status = "ratified"
            ratified_by = details.get("ratified_by") or evt.get("writer_id")
        elif action == "mutation.rejected":
            status = "rejected"
            rejected_by = details.get("rejected_by") or evt.get("writer_id")

    return MutationStatus(
        mutation_id=mutation_id,
        status=status,
        ratified_by=ratified_by,
        rejected_by=rejected_by,
    )


def reduce_options(events: list[dict], inquiry_id: str) -> list[dict]:
    """Reduce events to compute current options for an inquiry."""
    options: list[dict] = []

    for evt in events:
        if evt.get("subject_id") != inquiry_id:
            continue
        if evt.get("action") != "inquiry.options_set":
            continue
        details = evt.get("details", {})
        new_options = details.get("options")
        if isinstance(new_options, list):
            options = new_options  # Last write wins

    return options


def reduce_evidence_refs(events: list[dict], inquiry_id: str) -> list[str]:
    """Reduce events to gather all evidence references for an inquiry."""
    refs: list[str] = []
    seen: set[str] = set()

    for evt in events:
        if evt.get("subject_id") != inquiry_id:
            continue
        if evt.get("action") != "inquiry.evidence_added":
            continue
        details = evt.get("details", {})
        ref = details.get("evidence_id") or details.get("snapshot_id")
        if ref and ref not in seen:
            refs.append(ref)
            seen.add(ref)

    return refs


def reduce_supersession(events: list[dict], inquiry_id: str) -> dict:
    """Reduce events to find supersession info."""
    for evt in events:
        if evt.get("subject_id") != inquiry_id:
            continue
        if evt.get("action") != "inquiry.superseded":
            continue
        details = evt.get("details", {})
        return {
            "superseded": True,
            "superseded_by": details.get("superseded_by"),
            "rationale": details.get("rationale"),
            "timestamp": evt.get("timestamp"),
        }

    return {"superseded": False}


def reduce_claim_tiers(events: list[dict]) -> dict[str, str]:
    """Reduce claim promotion events to current tier map.

    Returns: {claim_id: current_tier}
    """
    tiers: dict[str, str] = {}

    for evt in events:
        action = evt.get("action", "")
        details = evt.get("details", {})

        if action == "claims.extracted":
            # New claims default to observed
            for claim in details.get("claims", []):
                cid = claim.get("claim_id")
                if cid:
                    tiers[cid] = "observed"
        elif action == "claim.promoted":
            cid = evt.get("subject_id")
            new_tier = details.get("new_tier") or details.get("target_tier")
            if cid and new_tier:
                tiers[cid] = new_tier

    return tiers


# ===========================================================================
# Layer 3: Operators — pure transforms
# ===========================================================================


def classify_claim_role(text: str) -> str:
    """Classify a claim's role from its text content.

    Pure heuristic — no model calls, no I/O.
    """
    lower = text.lower()

    # Goal/desire patterns
    if any(p in lower for p in ["want", "need", "should", "prefer", "desire", "hope", "wish"]):
        return "goal"

    # Constraint patterns
    if any(p in lower for p in ["must", "cannot", "within", "deadline", "limit", "require",
                                 "no more than", "at least", "maximum", "minimum"]):
        return "constraint"

    # Hypothesis patterns
    if any(p in lower for p in ["might", "could", "perhaps", "possibly", "hypothe",
                                 "if we", "what if", "consider"]):
        return "hypothesis"

    # Default: observation
    return "observation"


def compute_text_diff(old_text: str, new_text: str) -> DiffResult:
    """Pure text diff computation."""
    if old_text == new_text:
        return DiffResult(changed=False)

    import difflib
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = list(difflib.unified_diff(old_lines, new_lines, n=3))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    return DiffResult(
        changed=True,
        added_lines=added,
        removed_lines=removed,
        unified_diff="".join(diff),
    )


def normalize_text(raw: str) -> str:
    """Normalize text for comparison — pure string transform."""
    text = raw.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text


def extract_type_key(text: str, domain: str | None = None) -> str | None:
    """Extract normalized type_key from claim text.

    Pure heuristic matching against common dimensional axes.
    """
    lower = text.lower()

    # Temporal
    if any(p in lower for p in ["deadline", "timeline", "window", "days", "months",
                                 "before", "after", "until", "duration", "schedule"]):
        return "temporal_constraint"

    # Financial
    if any(p in lower for p in ["cost", "price", "premium", "budget", "afford",
                                 "expense", "fee", "payment", "dollar", "$"]):
        return "financial_constraint"

    # Risk
    if any(p in lower for p in ["risk", "danger", "uncertain", "volatile", "exposure",
                                 "vulnerability", "downside"]):
        return "risk_factor"

    # Coverage/scope
    if any(p in lower for p in ["coverage", "scope", "include", "exclude", "cover",
                                 "eligible", "qualify"]):
        return "coverage_strategy"

    # Quality
    if any(p in lower for p in ["quality", "reliability", "performance", "speed",
                                 "accuracy", "precision"]):
        return "quality_dimension"

    return None


def build_claim_tree(claims: list[dict]) -> list[dict]:
    """Build tree structure from flat claim list with parent_claim_id pointers.

    Pure projection — no storage, no side effects.
    Returns list of root nodes with nested children.
    """
    by_id: dict[str, dict] = {}
    for c in claims:
        cid = c.get("claim_id", "")
        node = {**c, "children": []}
        by_id[cid] = node

    roots: list[dict] = []
    for c in claims:
        cid = c.get("claim_id", "")
        parent = c.get("parent_claim_id")
        node = by_id[cid]

        if parent and parent in by_id:
            by_id[parent]["children"].append(node)
        else:
            roots.append(node)

    return roots


def flatten_claim_tree(roots: list[dict]) -> list[dict]:
    """Flatten a nested claim tree back to a flat list.

    Inverse of build_claim_tree. Pure function.
    """
    result: list[dict] = []
    for node in roots:
        children = node.pop("children", [])
        result.append(node)
        result.extend(flatten_claim_tree(children))
    return result


def compute_claim_confidence(
    base_confidence: float,
    source_count: int = 1,
    corroboration_count: int = 0,
    challenge_count: int = 0,
) -> float:
    """Compute adjusted claim confidence.

    Pure formula: base * source_boost * corroboration_boost * challenge_penalty
    """
    source_boost = min(1.0 + (source_count - 1) * 0.05, 1.2)
    corr_boost = min(1.0 + corroboration_count * 0.1, 1.5)
    challenge_penalty = max(0.5, 1.0 - challenge_count * 0.15)

    adjusted = base_confidence * source_boost * corr_boost * challenge_penalty
    return round(min(1.0, max(0.0, adjusted)), 3)


# ===========================================================================
# Layer 4: Validators — schema invariant checks
# ===========================================================================


def validate_claim(claim: dict) -> ValidationResult:
    """Validate a claim record against schema invariants."""
    errors: list[str] = []
    warnings: list[str] = []

    # Required fields
    if not claim.get("text"):
        errors.append("Claim must have non-empty text")
    if not claim.get("claim_id"):
        errors.append("Claim must have claim_id")

    # Confidence range
    conf = claim.get("confidence", 0.5)
    if not isinstance(conf, (int, float)):
        errors.append(f"Confidence must be numeric, got {type(conf).__name__}")
    elif conf < 0.0 or conf > 1.0:
        errors.append(f"Confidence must be 0.0-1.0, got {conf}")

    # Binding tier validity
    tier = claim.get("binding_tier", "observed")
    valid_tiers = {"observed", "proposed", "ratified"}
    if tier not in valid_tiers:
        errors.append(f"Invalid binding_tier: {tier}")

    # Role validity
    role = claim.get("claim_role")
    valid_roles = {"observation", "goal", "constraint", "hypothesis", "foundational_type", None}
    if role not in valid_roles:
        warnings.append(f"Non-standard claim_role: {role}")

    # Parent reference loop detection (basic)
    if claim.get("parent_claim_id") == claim.get("claim_id"):
        errors.append("Claim cannot be its own parent")

    # Text length
    text = claim.get("text", "")
    if len(text) > 10000:
        warnings.append(f"Claim text unusually long: {len(text)} chars")
    elif len(text) < 5:
        warnings.append(f"Claim text very short: {len(text)} chars")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_event(event: dict) -> ValidationResult:
    """Validate a ledger event against schema invariants."""
    errors: list[str] = []
    warnings: list[str] = []

    if not event.get("id"):
        errors.append("Event must have id")
    if not event.get("action"):
        errors.append("Event must have action")

    # Action format: "namespace.verb"
    action = event.get("action", "")
    if action and "." not in action:
        warnings.append(f"Action should be namespaced (e.g. 'inquiry.created'), got: {action}")

    # Timestamp presence
    if not event.get("timestamp"):
        warnings.append("Event missing timestamp")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_inquiry(inquiry: dict) -> ValidationResult:
    """Validate an inquiry artifact."""
    errors: list[str] = []
    warnings: list[str] = []

    if not inquiry.get("inquiry_id"):
        errors.append("Inquiry must have inquiry_id")
    if not inquiry.get("question"):
        errors.append("Inquiry must have question")

    options = inquiry.get("options", [])
    if options:
        ids = [o.get("id") for o in options if isinstance(o, dict)]
        if len(ids) != len(set(ids)):
            errors.append("Duplicate option IDs")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_ledger_chain(events: list[dict], hash_fn=None) -> ValidationResult:
    """Validate hash chain integrity of a ledger event sequence.

    Pure function: takes event dicts, returns validation result.
    """
    if hash_fn is None:
        def hash_fn(data: bytes) -> str:
            return "sha256:" + hashlib.sha256(data).hexdigest()

    errors: list[str] = []
    warnings: list[str] = []

    for i, evt in enumerate(events):
        prev_hash = evt.get("prev_event_hash")
        if prev_hash is None:
            continue

        if i == 0:
            warnings.append(f"First event has prev_event_hash but no predecessor")
            continue

        prev_line = json.dumps(events[i - 1], default=str, sort_keys=True)
        expected = hash_fn(prev_line.encode("utf-8"))

        if prev_hash != expected:
            errors.append(
                f"Chain break at event {i}: expected {expected[:20]}... got {prev_hash[:20]}..."
            )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


# ===========================================================================
# Layer 5: Conflict Detection
# ===========================================================================


def detect_contradictions(claims: list[dict]) -> list[ConflictReport]:
    """Detect direct contradictions between claims.

    Heuristic: claims with same type_key but opposing sentiment/content.
    """
    conflicts: list[ConflictReport] = []

    # Group by type_key
    by_type: dict[str, list[dict]] = {}
    for c in claims:
        tk = c.get("type_key")
        if tk:
            by_type.setdefault(tk, []).append(c)

    # Check each group for contradictions
    for tk, group in by_type.items():
        if len(group) < 2:
            continue

        for i, c1 in enumerate(group):
            for c2 in group[i + 1:]:
                if _texts_contradict(c1.get("text", ""), c2.get("text", "")):
                    conflicts.append(ConflictReport(
                        conflict_type="contradiction",
                        claim_ids=(c1.get("claim_id", ""), c2.get("claim_id", "")),
                        description=f"Contradicting claims on {tk}",
                        severity=max(c1.get("confidence", 0.5), c2.get("confidence", 0.5)),
                    ))

    return conflicts


def detect_coverage_gaps(
    claims: list[dict],
    required_dimensions: list[str] | None = None,
) -> list[ConflictReport]:
    """Detect missing coverage in claim set.

    Checks that key dimensional axes have at least one claim.
    """
    if required_dimensions is None:
        required_dimensions = [
            "temporal_constraint",
            "financial_constraint",
            "risk_factor",
            "coverage_strategy",
        ]

    covered = {c.get("type_key") for c in claims if c.get("type_key")}
    gaps: list[ConflictReport] = []

    for dim in required_dimensions:
        if dim not in covered:
            gaps.append(ConflictReport(
                conflict_type="coverage_gap",
                claim_ids=(),
                description=f"No claims covering dimension: {dim}",
                severity=0.3,
            ))

    return gaps


def detect_stale_evidence(
    claims: list[dict],
    max_age_days: int = 90,
    reference_date: str | None = None,
) -> list[ConflictReport]:
    """Detect claims that may be based on stale evidence.

    Pure function — uses reference_date for comparison instead of datetime.now().
    """
    stale: list[ConflictReport] = []

    for c in claims:
        source_date = c.get("source_date") or c.get("created_at")
        if not source_date or not reference_date:
            continue

        try:
            # Simple ISO date comparison
            if source_date < reference_date:
                # Would need proper date arithmetic for real implementation
                stale.append(ConflictReport(
                    conflict_type="stale_evidence",
                    claim_ids=(c.get("claim_id", ""),),
                    description=f"Claim may be based on outdated evidence ({source_date})",
                    severity=0.2,
                ))
        except (TypeError, ValueError):
            pass

    return stale


def detect_all_conflicts(
    claims: list[dict],
    required_dimensions: list[str] | None = None,
) -> list[ConflictReport]:
    """Run all conflict detectors and return combined results."""
    conflicts: list[ConflictReport] = []
    conflicts.extend(detect_contradictions(claims))
    conflicts.extend(detect_coverage_gaps(claims, required_dimensions))
    return conflicts


def _texts_contradict(text1: str, text2: str) -> bool:
    """Heuristic contradiction detection between two texts.

    Looks for negation patterns and opposing qualifiers.
    """
    t1, t2 = text1.lower(), text2.lower()

    negation_pairs = [
        ("not ", ""), ("no ", ""),
        ("cannot ", "can "), ("won't ", "will "),
        ("don't ", "do "), ("isn't ", "is "),
        ("doesn't ", "does "), ("shouldn't ", "should "),
        ("never ", "always "),
        ("exclude", "include"),
        ("ineligible", "eligible"),
        ("unavailable", "available"),
    ]

    for neg, pos in negation_pairs:
        if (neg in t1 and pos in t2) or (neg in t2 and pos in t1):
            # Check if they share enough common words to be about the same thing
            words1 = set(t1.split())
            words2 = set(t2.split())
            common = words1 & words2 - {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and", "or", "in", "on", "for", "with"}
            if len(common) >= 2:
                return True

    return False


# ===========================================================================
# Layer 6: Deterministic Replay
# ===========================================================================


def compute_content_hash(data: dict) -> str:
    """Deterministic content hash — same data → same hash, always.

    Uses sorted JSON serialization for key-order independence.
    """
    canonical = json.dumps(data, sort_keys=True, default=str, ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def replay_to_snapshot(
    events: list[dict],
    claims: list[dict] | None = None,
) -> ReplaySnapshot:
    """Build a deterministic snapshot from events.

    Same events → same snapshot → same content_hash. Always.
    This is the core replay invariant.
    """
    if not events:
        return ReplaySnapshot(
            head_event_id="",
            event_count=0,
            content_hash=compute_content_hash({}),
        )

    # Compute aggregate state from events
    inquiry_ids: set[str] = set()
    artifact_count = 0
    claim_count = 0

    for evt in events:
        action = evt.get("action", "")
        sid = evt.get("subject_id", "")

        if action == "inquiry.created":
            inquiry_ids.add(sid)
        elif action == "artifact.committed":
            artifact_count += 1
        elif action == "claims.extracted":
            details = evt.get("details", {})
            claim_count += details.get("claim_count", 0)

    # Compute inquiry statuses
    statuses = {}
    for iid in sorted(inquiry_ids):
        status = reduce_inquiry_status(events, iid)
        statuses[iid] = status.status

    # Build deterministic snapshot data
    snapshot_data = {
        "event_count": len(events),
        "inquiry_statuses": statuses,
        "claim_count": claim_count,
        "artifact_count": artifact_count,
    }

    head_event_id = events[-1].get("id", "") if events else ""

    return ReplaySnapshot(
        head_event_id=head_event_id,
        event_count=len(events),
        content_hash=compute_content_hash(snapshot_data),
        inquiry_statuses=statuses,
        claim_count=claim_count,
        artifact_count=artifact_count,
    )


def verify_replay_determinism(
    events: list[dict],
    n_replays: int = 3,
) -> bool:
    """Verify that replaying the same events N times produces the same hash.

    This is the fundamental correctness property of event sourcing.
    """
    hashes = set()
    for _ in range(n_replays):
        snapshot = replay_to_snapshot(events)
        hashes.add(snapshot.content_hash)

    return len(hashes) == 1
