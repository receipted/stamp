"""Action-witness verification tests.

"We are not trying to detect lies.
 We are trying to detect unwitnessed operational claims."

These tests verify the pure verdict engine:
- Claims with corroborating witnesses → WITNESSED
- Claims with no witnesses → UNWITNESSED
- Claims contradicted by witnesses → CONTRADICTED
- Mixed evidence → INSUFFICIENT_EVIDENCE
- Negative-polarity actions (stop/delete) with correct absence semantics
- Enum rehydration through receipted wrapper
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.surface.action_witness import (
    ActionClaim,
    ActionWitness,
    ActionVerdict,
    Verdict,
    WitnessKind,
    adjudicate_claim,
    adjudicate,
    verdict_summary,
    _relevant_witnesses,
    _is_corroborating,
)
from src.surface.receipted import run_witness_verdict_with_receipt


# ---------------------------------------------------------------------------
# The demo scenario
# ---------------------------------------------------------------------------

class TestDemoScenario:
    """The target demo: 'Did you run the API bridge, or did you fake it?'"""

    def test_bridge_actually_running(self):
        """Agent says it started the bridge. Port is listening. → WITNESSED"""
        claim = ActionClaim(
            action="start",
            subject="API bridge",
            qualifiers={"port": 8080},
            source_text="I started the API bridge on port 8080",
        )
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PORT_HEALTH,
                subject="localhost:8080",
                observed=True,
                detail="port 8080 is listening",
            ),
            ActionWitness(
                kind=WitnessKind.PROCESS_WITNESS,
                subject="api_bridge",
                observed=True,
                detail="found 1 process(es) (PIDs: 12345)",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.WITNESSED

    def test_bridge_not_running(self):
        """Agent says it started the bridge. Nothing is listening. → CONTRADICTED"""
        claim = ActionClaim(
            action="start",
            subject="API bridge",
            qualifiers={"port": 8080},
            source_text="I started the API bridge on port 8080",
        )
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PORT_HEALTH,
                subject="localhost:8080",
                observed=False,
                detail="port 8080 not listening",
            ),
            ActionWitness(
                kind=WitnessKind.PROCESS_WITNESS,
                subject="api_bridge",
                observed=False,
                detail="no matching process found",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.CONTRADICTED

    def test_bridge_no_witnesses_collected(self):
        """Agent says it started the bridge. No one checked. → UNWITNESSED"""
        claim = ActionClaim(
            action="start",
            subject="API bridge",
            qualifiers={"port": 8080},
            source_text="I started the API bridge on port 8080",
        )
        verdict = adjudicate_claim(claim, [])
        assert verdict.verdict == Verdict.UNWITNESSED

    def test_bridge_mixed_evidence(self):
        """Port is listening but process not found. → INSUFFICIENT_EVIDENCE"""
        claim = ActionClaim(
            action="start",
            subject="API bridge",
            qualifiers={"port": 8080},
            source_text="I started the API bridge on port 8080",
        )
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PORT_HEALTH,
                subject="localhost:8080",
                observed=True,
                detail="port 8080 is listening",
            ),
            ActionWitness(
                kind=WitnessKind.PROCESS_WITNESS,
                subject="api_bridge",
                observed=False,
                detail="no matching process found",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.INSUFFICIENT_EVIDENCE


# ---------------------------------------------------------------------------
# Polarity — the P1 fix: stop/delete expect absence
# ---------------------------------------------------------------------------

class TestNegativePolarity:
    """Negative-polarity actions (stop, delete) expect observed=False."""

    def test_stop_server_process_gone_is_witnessed(self):
        """'I stopped the server' + process NOT found → WITNESSED (not CONTRADICTED)."""
        claim = ActionClaim(action="stop", subject="server")
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PROCESS_WITNESS,
                subject="server",
                observed=False,
                detail="no matching process found",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.WITNESSED, (
            "stop + process gone should be WITNESSED, not CONTRADICTED"
        )

    def test_stop_server_still_running_is_contradicted(self):
        """'I stopped the server' + process STILL running → CONTRADICTED."""
        claim = ActionClaim(action="stop", subject="server")
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PROCESS_WITNESS,
                subject="server",
                observed=True,
                detail="found 1 process(es) (PIDs: 12345)",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.CONTRADICTED

    def test_stop_server_port_closed_is_witnessed(self):
        """'I stopped the server' + port NOT listening → WITNESSED."""
        claim = ActionClaim(action="stop", subject="server", qualifiers={"port": 8080})
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PORT_HEALTH,
                subject="localhost:8080",
                observed=False,
                detail="port 8080 not listening",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.WITNESSED

    def test_delete_file_gone_is_witnessed(self):
        """'I deleted the config' + file NOT found → WITNESSED."""
        claim = ActionClaim(action="delete", subject="config", qualifiers={"path": "/tmp/config.json"})
        witnesses = [
            ActionWitness(
                kind=WitnessKind.ARTIFACT_EFFECT,
                subject="/tmp/config.json",
                observed=False,
                detail="artifact does not exist",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.WITNESSED

    def test_delete_file_still_exists_is_contradicted(self):
        """'I deleted the config' + file STILL exists → CONTRADICTED."""
        claim = ActionClaim(action="delete", subject="config", qualifiers={"path": "/tmp/config.json"})
        witnesses = [
            ActionWitness(
                kind=WitnessKind.ARTIFACT_EFFECT,
                subject="/tmp/config.json",
                observed=True,
                detail="exists, 1024 bytes",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.CONTRADICTED

    def test_stop_mixed_evidence(self):
        """'I stopped the server' + process gone but port still open → INSUFFICIENT."""
        claim = ActionClaim(action="stop", subject="server", qualifiers={"port": 8080})
        witnesses = [
            ActionWitness(
                kind=WitnessKind.PROCESS_WITNESS,
                subject="server",
                observed=False,
                detail="no process found",
            ),
            ActionWitness(
                kind=WitnessKind.PORT_HEALTH,
                subject="localhost:8080",
                observed=True,
                detail="port 8080 still listening",
            ),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.INSUFFICIENT_EVIDENCE


class TestPolarityHelper:
    """_is_corroborating() must invert for negative-polarity actions."""

    def test_start_observed_true_corroborates(self):
        w = ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="x", observed=True)
        assert _is_corroborating(w, "start") is True

    def test_start_observed_false_contradicts(self):
        w = ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="x", observed=False)
        assert _is_corroborating(w, "start") is False

    def test_stop_observed_false_corroborates(self):
        w = ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="x", observed=False)
        assert _is_corroborating(w, "stop") is True

    def test_stop_observed_true_contradicts(self):
        w = ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="x", observed=True)
        assert _is_corroborating(w, "stop") is False

    def test_delete_observed_false_corroborates(self):
        w = ActionWitness(kind=WitnessKind.ARTIFACT_EFFECT, subject="x", observed=False)
        assert _is_corroborating(w, "delete") is True

    def test_kill_is_negative_polarity(self):
        w = ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="x", observed=False)
        assert _is_corroborating(w, "kill") is True


# ---------------------------------------------------------------------------
# Verdict enum
# ---------------------------------------------------------------------------

class TestVerdictValues:
    def test_all_four_verdicts_exist(self):
        assert set(Verdict) == {
            Verdict.WITNESSED,
            Verdict.UNWITNESSED,
            Verdict.CONTRADICTED,
            Verdict.INSUFFICIENT_EVIDENCE,
        }

    def test_verdict_string_values(self):
        assert Verdict.WITNESSED.value == "WITNESSED"
        assert Verdict.UNWITNESSED.value == "UNWITNESSED"
        assert Verdict.CONTRADICTED.value == "CONTRADICTED"
        assert Verdict.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"


# ---------------------------------------------------------------------------
# Witness matching
# ---------------------------------------------------------------------------

class TestWitnessMatching:
    def test_start_matches_process_and_port(self):
        claim = ActionClaim(action="start", subject="server")
        witnesses = [
            ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="server", observed=True),
            ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="server:8080", observed=True),
            ActionWitness(kind=WitnessKind.ARTIFACT_EFFECT, subject="output.txt", observed=True),
        ]
        relevant = _relevant_witnesses(claim, witnesses)
        kinds = {w.kind for w in relevant}
        assert WitnessKind.PROCESS_WITNESS in kinds
        assert WitnessKind.PORT_HEALTH in kinds
        # artifact not expected for "start" action
        assert WitnessKind.ARTIFACT_EFFECT not in kinds

    def test_run_matches_command_receipt(self):
        claim = ActionClaim(action="run", subject="pytest")
        witnesses = [
            ActionWitness(kind=WitnessKind.COMMAND_RECEIPT, subject="pytest tests/", observed=True),
        ]
        relevant = _relevant_witnesses(claim, witnesses)
        assert len(relevant) == 1

    def test_irrelevant_witnesses_excluded(self):
        claim = ActionClaim(action="start", subject="database")
        witnesses = [
            ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="webserver", observed=True),
        ]
        relevant = _relevant_witnesses(claim, witnesses)
        assert len(relevant) == 0

    def test_port_qualifier_matching(self):
        claim = ActionClaim(action="start", subject="service", qualifiers={"port": 3000})
        witnesses = [
            ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="localhost:3000", observed=True,
                          detail="port 3000 is listening"),
            ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="localhost:5000", observed=True,
                          detail="port 5000 is listening"),
        ]
        relevant = _relevant_witnesses(claim, witnesses)
        # Should match port 3000 specifically
        assert len(relevant) == 1
        assert "3000" in relevant[0].subject


# ---------------------------------------------------------------------------
# Batch adjudication
# ---------------------------------------------------------------------------

class TestBatchAdjudication:
    def test_multiple_claims(self):
        claims = [
            ActionClaim(action="start", subject="server", qualifiers={"port": 8080}),
            ActionClaim(action="create", subject="config file", qualifiers={"path": "/tmp/config.json"}),
            ActionClaim(action="run", subject="migration"),
        ]
        witnesses = [
            ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="localhost:8080",
                          observed=True, detail="port 8080 listening"),
            ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="server",
                          observed=True, detail="PID 1234"),
            # No witnesses for config file or migration
        ]
        verdicts = adjudicate(claims, witnesses)
        assert len(verdicts) == 3
        assert verdicts[0].verdict == Verdict.WITNESSED
        assert verdicts[1].verdict == Verdict.UNWITNESSED
        assert verdicts[2].verdict == Verdict.UNWITNESSED


# ---------------------------------------------------------------------------
# Summary projection
# ---------------------------------------------------------------------------

class TestVerdictSummary:
    def test_summary_counts(self):
        verdicts = [
            ActionVerdict(
                claim=ActionClaim(action="start", subject="a"),
                verdict=Verdict.WITNESSED, witnesses=[], reasoning="ok",
            ),
            ActionVerdict(
                claim=ActionClaim(action="run", subject="b"),
                verdict=Verdict.UNWITNESSED, witnesses=[], reasoning="none",
            ),
            ActionVerdict(
                claim=ActionClaim(action="create", subject="c"),
                verdict=Verdict.CONTRADICTED, witnesses=[], reasoning="nope",
            ),
        ]
        s = verdict_summary(verdicts)
        assert s["total_claims"] == 3
        assert s["witnessed"] == 1
        assert s["unwitnessed"] == 1
        assert s["contradicted"] == 1
        assert s["insufficient"] == 0


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_claim_to_dict(self):
        c = ActionClaim(action="start", subject="bridge", qualifiers={"port": 8080})
        d = c.to_dict()
        assert d["action"] == "start"
        assert d["qualifiers"]["port"] == 8080

    def test_witness_to_dict(self):
        w = ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="localhost:8080", observed=True)
        d = w.to_dict()
        assert d["kind"] == "port_health"
        assert d["observed"] is True

    def test_verdict_to_dict(self):
        v = ActionVerdict(
            claim=ActionClaim(action="start", subject="bridge"),
            verdict=Verdict.WITNESSED,
            witnesses=[ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="localhost:8080", observed=True)],
            reasoning="corroborated",
        )
        d = v.to_dict()
        assert d["verdict"] == "WITNESSED"
        assert len(d["witnesses"]) == 1


# ---------------------------------------------------------------------------
# Receipted verdict — stamped, with enum rehydration
# ---------------------------------------------------------------------------

class TestReceiptedVerdict:
    def test_verdict_is_stamped(self):
        claims = [{"action": "start", "subject": "API bridge", "qualifiers": {"port": 8080}}]
        witnesses = [
            {"kind": "port_health", "subject": "localhost:8080", "observed": True,
             "detail": "port 8080 listening"},
        ]
        result = run_witness_verdict_with_receipt(claims, witnesses)
        assert result["stamp"].domain == "witness_verdict"
        assert result["summary"]["witnessed"] == 1

    def test_stamped_verdict_deterministic(self):
        claims = [{"action": "start", "subject": "server", "qualifiers": {"port": 3000}}]
        witnesses = [
            {"kind": "port_health", "subject": "localhost:3000", "observed": True, "detail": "listening"},
            {"kind": "process_witness", "subject": "server", "observed": True, "detail": "PID 42"},
        ]
        r1 = run_witness_verdict_with_receipt(claims, witnesses)
        r2 = run_witness_verdict_with_receipt(claims, witnesses)
        assert r1["stamp"].stamp_hash == r2["stamp"].stamp_hash

    def test_tampered_verdict_different_stamp(self):
        claims = [{"action": "run", "subject": "pytest"}]
        w1 = [{"kind": "command_receipt", "subject": "pytest tests/", "observed": True, "detail": "exit 0"}]
        w2 = [{"kind": "command_receipt", "subject": "pytest tests/", "observed": False, "detail": "exit 1"}]
        r1 = run_witness_verdict_with_receipt(claims, w1)
        r2 = run_witness_verdict_with_receipt(claims, w2)
        assert r1["stamp"].stamp_hash != r2["stamp"].stamp_hash
        assert r1["summary"]["witnessed"] == 1
        assert r2["summary"]["contradicted"] == 1

    def test_rehydrated_verdict_to_dict_works(self):
        """Enum rehydration fix: to_dict() must work on verdicts from the receipted wrapper.

        Before the fix, WitnessKind was passed as a raw string, so
        .value would raise AttributeError on the ActionWitness objects
        inside the returned verdicts.
        """
        claims = [{"action": "start", "subject": "bridge", "qualifiers": {"port": 8080}}]
        witnesses = [
            {"kind": "port_health", "subject": "localhost:8080", "observed": True, "detail": "listening"},
        ]
        result = run_witness_verdict_with_receipt(claims, witnesses)
        # This is the line that would fail before the fix
        verdict_dict = result["verdicts"][0].to_dict()
        assert verdict_dict["verdict"] == "WITNESSED"
        # Witnesses inside the verdict must also serialize cleanly
        for w in verdict_dict["witnesses"]:
            assert w["kind"] == "port_health"  # string value, not enum repr

    def test_negative_polarity_through_receipted(self):
        """Stop claims with absence evidence must work through the receipted wrapper."""
        claims = [{"action": "stop", "subject": "server"}]
        witnesses = [
            {"kind": "process_witness", "subject": "server", "observed": False,
             "detail": "no process found"},
        ]
        result = run_witness_verdict_with_receipt(claims, witnesses)
        assert result["summary"]["witnessed"] == 1
        assert result["summary"]["contradicted"] == 0
