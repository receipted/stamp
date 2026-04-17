"""Pydantic data models for Surface Server."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .ids import generate_id


class SnapshotOrigin(str, Enum):
    url = "url"
    file = "file"
    text = "text"


class ArtifactType(str, Enum):
    claim_set = "claim_set"
    brief = "brief"
    decision = "decision"            # kept for backward compat + healthcare
    inquiry = "inquiry"              # new: general inquiries
    note = "note"
    outline = "outline"
    thread_diff = "thread_diff"
    delta_report = "delta_report"
    working_set = "working_set"
    change_set = "change_set"
    capsule_report = "capsule_report"
    review = "review"
    critic_review = "critic_review"
    decision_packet = "decision_packet"  # kept for backward compat + healthcare
    inquiry_packet = "inquiry_packet"    # new
    policy_result = "policy_result"
    commit_event = "commit_event"
    thread_index = "thread_index"
    steering_packet = "steering_packet"
    feature_event = "feature_event"
    authored_mutation = "authored_mutation"
    conversation_turn = "conversation_turn"
    evidence = "evidence"
    dissent = "dissent"
    commitment = "commitment"
    edge = "edge"
    research_plan = "research_plan"
    coverage_assessment = "coverage_assessment"
    option_synthesis = "option_synthesis"
    adversary_report = "adversary_report"
    reflex_result = "reflex_result"
    decision_brief = "decision_brief"
    decision_capsule = "decision_capsule"
    investigation_state = "investigation_state"
    coalescence = "coalescence"
    outcome = "outcome"
    topic_reduction = "topic_reduction"
    topic_sieve = "topic_sieve"


class LedgerAction(str, Enum):
    snapshot_created = "snapshot.created"
    artifact_committed = "artifact.committed"
    claims_extracted = "claims.extracted"
    healthcare_decision_packet = "healthcare.decision_packet"
    outline_generated = "outline.generated"
    thread_blob_upserted = "thread.blob_upserted"
    topic_created = "topic.created"
    thread_attached = "thread.attached"
    thread_detached = "thread.detached"
    delta_computed = "delta.computed"
    working_set_updated = "working_set.updated"
    run_started = "run.started"
    run_completed = "run.completed"
    run_gated = "run.gated"
    run_committed = "run.committed"
    head_advanced = "head.advanced"
    git_commit_recorded = "git.commit_recorded"
    thread_index_generated = "thread_index.generated"
    decision_created = "decision.created"              # kept for backward compat
    decision_review_submitted = "decision.review_submitted"  # kept for backward compat
    decision_adjudicated = "decision.adjudicated"        # kept for backward compat
    decision_superseded = "decision.superseded"          # kept for backward compat
    decision_evidence_added = "decision.evidence_added"  # kept for backward compat
    inquiry_created = "inquiry.created"
    inquiry_review_submitted = "inquiry.review_submitted"
    inquiry_adjudicated = "inquiry.adjudicated"
    inquiry_superseded = "inquiry.superseded"
    inquiry_evidence_added = "inquiry.evidence_added"
    inquiry_options_set = "inquiry.options_set"
    inquiry_status_transition = "inquiry.status_transition"
    inquiry_archived = "inquiry.archived"
    steering_packet_created = "steering.packet_created"
    steering_packet_expired = "steering.packet_expired"
    steering_packet_acted_event = "steering.packet_acted_event"
    mutation_ratified = "mutation.ratified"
    mutation_rejected = "mutation.rejected"
    steering_packet_acted = "steering.packet_acted"
    feature_shipped = "feature.shipped"
    mutation_logged = "mutation.logged"
    projection_materialized = "projection.materialized"
    turn_posted = "turn.posted"
    turn_forked = "turn.forked"
    inquiry_idempotence_key_set = "inquiry.idempotence_key_set"
    # Expanded inquiry lifecycle (exploring → clustering → candidate → active → resolved)
    inquiry_exploring = "inquiry.exploring"
    inquiry_clustering = "inquiry.clustering"
    inquiry_candidate_proposed = "inquiry.candidate_proposed"
    inquiry_active_promoted = "inquiry.active_promoted"
    # Research thread engine
    research_plan_created = "research.plan_created"
    research_thread_started = "research.thread_started"
    research_thread_completed = "research.thread_completed"
    coagulation_evaluated = "coagulation.evaluated"
    coagulation_fired = "coagulation.fired"
    evidence_submitted = "evidence.submitted"
    dissent_recorded = "dissent.recorded"
    dissent_resolved = "dissent.resolved"
    challenge_filed = "challenge.filed"
    challenge_resolved = "challenge.resolved"
    commitment_proposed = "commitment.proposed"
    commitment_activated = "commitment.activated"
    commitment_fulfilled = "commitment.fulfilled"
    commitment_broken = "commitment.broken"
    claim_promoted = "claim.promoted"
    mutation_proposed = "mutation.proposed"
    inquiry_deferred = "inquiry.deferred"
    inquiry_forked = "inquiry.forked"
    healing_check_run = "healing.check_run"
    healing_anomaly_detected = "healing.anomaly_detected"
    healing_repair_applied = "healing.repair_applied"
    healing_quarantined = "healing.quarantined"
    # Session & parity trust events
    session_started = "session.started"
    session_context_seen = "session.context_seen"
    session_compacted = "session.compacted"
    parity_hydrated = "parity.hydrated"
    parity_linked = "parity.linked"
    # Self-healing policy matrix gaps
    healing_escalated = "healing.escalated"
    actor_health_changed = "actor.health_changed"
    # Tier 1/2 self-healing gaps
    inquiry_transition_blocked = "inquiry.transition_blocked"
    relay_dedup_skipped = "relay.dedup_skipped"
    ingest_phase_completed = "ingest.phase_completed"
    # Tier 0 self-healing gaps (Round 3)
    adjudication_frozen = "adjudication.frozen"
    dissent_recomputed = "dissent.recomputed"
    commitment_recomputed = "commitment.recomputed"
    stream_resynced = "stream.resynced"
    # Synthesizer + Adversary
    synthesis_produced = "synthesis.produced"
    adversary_attack_completed = "adversary.attack_completed"
    # Reflex engine
    reflex_evaluated = "reflex.evaluated"
    reflex_fired = "reflex.fired"
    reflex_healed = "reflex.healed"
    reflex_disabled = "reflex.disabled"
    reflex_enabled = "reflex.enabled"
    # Decision brief/capsule lifecycle
    brief_generated = "brief.generated"
    brief_amended = "brief.amended"
    capsule_created = "capsule.created"
    capsule_outcome_recorded = "capsule.outcome_recorded"
    topic_archived = "topic.archived"
    investigation_computed = "investigation.computed"
    edge_created = "edge.created"
    notebook_created = "notebook.created"
    notebook_updated = "notebook.updated"
    notebook_archived = "notebook.archived"
    # Coalescence lifecycle
    coalescence_provisional = "coalescence.provisional"
    coalescence_ratified = "coalescence.ratified"
    coalescence_superseded = "coalescence.superseded"
    # Epistemic events (real-time tagging)
    epistemic_event = "epistemic.event"
    # Action tracking (commitment specialization)
    action_created = "action.created"
    action_completed = "action.completed"
    action_overdue = "action.overdue"
    # Outcome recording (decision feedback loop)
    outcome_recorded = "outcome.recorded"
    # Epistemic safety net — grounded dissent detection
    inflection_detected = "inflection.detected"
    # Active epistemic facilitation
    facilitation_stance_transition = "facilitation.stance_transition"
    facilitation_action_applied = "facilitation.action_applied"
    # Evidence event system
    evidence_ingested = "evidence.ingested"
    topic_reduced = "topic.reduced"
    sieve_applied = "sieve.applied"


class BindingTier(str, Enum):
    observed = "observed"    # Raw extraction — hypothesis, not binding
    proposed = "proposed"    # Cross-turn or cross-model corroboration
    ratified = "ratified"   # Human-approved — replay-stable, binding


class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: generate_id("clm"))
    text: str
    source_span: str | None = None
    confidence: float | None = None
    # Structured knowledge (optional — text is always primary)
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    binding_tier: BindingTier = BindingTier.observed
    # Fractal tree structure (optional — flat claims work without these)
    parent_claim_id: str | None = None      # enables tree nesting (zoom in/out)
    claim_role: str | None = None           # "foundational_type" | "constraint" |
                                            # "preference" | "observation" | "hypothesis"
    type_key: str | None = None             # normalized taxonomy key for cross-inquiry
                                            # matching (e.g. "temporal_constraint",
                                            # "financial_constraint.premium_cap")


class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: generate_id("evi"))
    snapshot_id: str
    submitted_by: str | None = None
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context: str | None = None
    claim_refs: list[str] = Field(default_factory=list)
    inquiry_id: str | None = None


class Dissent(BaseModel):
    dissent_id: str = Field(default_factory=lambda: generate_id("dis"))
    inquiry_id: str
    claim_a: str              # one position (claim_id or text)
    claim_b: str              # competing position
    source_critics: list[str] = Field(default_factory=list)
    dissent_type: str = "finding_conflict"  # finding_conflict | option_conflict | assessment_split
    resolution: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None


class Commitment(BaseModel):
    commitment_id: str = Field(default_factory=lambda: generate_id("cmt"))
    text: str
    committed_by: str
    committed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_refs: list[str] = Field(default_factory=list)
    inquiry_id: str | None = None


class Provenance(BaseModel):
    derived_from: list[str] = Field(default_factory=list)
    model_name: str | None = None
    prompt_hash: str | None = None
    raw_output_blob: str | None = None
    created_by: str | None = None
    extraction_method: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    temperature: float | None = None
    # Reasoning reproducibility fields
    provider: str | None = None           # "anthropic", "openai", "google"
    max_tokens: int | None = None         # max output tokens for this call
    tools_enabled: bool | None = None     # whether tools were available
    context_turns: int | None = None      # how many prior turns were in context
    tool_iterations: int | None = None    # how many tool-use rounds occurred
    # Server-attested provenance (2026-03-14) — proves content origin
    # attested_by: who actually made the API call (server-side, not self-reported)
    # attestation_hash: SHA-256 of (api_endpoint + response_body + timestamp)
    # attestation_ts: ISO timestamp when attestation was created
    attested_by: str | None = None        # e.g. "surface-server:critic-pipeline"
    attestation_hash: str | None = None   # receipt proving actual API response
    attestation_ts: str | None = None     # when the attestation was stamped


class Snapshot(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("snap"))
    content_hash: str
    content_type: str = "text/plain"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    origin: SnapshotOrigin = SnapshotOrigin.text
    origin_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("art"))
    type: ArtifactType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: Provenance = Field(default_factory=Provenance)
    content: dict[str, Any] = Field(default_factory=dict)


class LedgerEvent(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("evt"))
    action: LedgerAction
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    subject_id: str
    subject_type: str
    details: dict[str, Any] = Field(default_factory=dict)
    prev_event_hash: str | None = None
    caused_by: str | None = None
    writer_id: str | None = None


class Projection(BaseModel):
    """Ephemeral in-memory projection — never persisted or logged."""

    id: str = Field(default_factory=lambda: generate_id("view"))
    query: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: list[dict[str, Any]] = Field(default_factory=list)
    derivation_chain: list[dict[str, Any]] = Field(default_factory=list)


class RunKind(str, Enum):
    record = "record"      # Extension captures, bookkeeping
    build = "build"        # Model-invoked, produces change_set + raw_output
    review = "review"      # Critic pass
    publish = "publish"    # Export/publish pass


class RunStatus(str, Enum):
    started = "started"
    completed = "completed"
    gated = "gated"
    committed = "committed"


class SemanticRole(str, Enum):
    builder = "Builder"
    critic = "Critic"
    gate = "Gate"
    publisher = "Publisher"


class GateVerdict(str, Enum):
    allow = "ALLOW"
    deny = "DENY"
    request_revision = "REQUEST_REVISION"


class Run(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("run"))
    kind: RunKind = RunKind.record
    user_id: str | None = None
    thread_id: str | None = None
    base_head_event_id: str | None = None
    status: RunStatus = RunStatus.started
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class Binding(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("bnd"))
    role: SemanticRole
    provider: str = ""
    model: str = ""
    capabilities: list[str] = Field(default_factory=list)
    enabled: bool = True
