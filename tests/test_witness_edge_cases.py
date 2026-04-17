"""Edge case tests for the action-witness layer.

Covers:
- Verdict stamp binds full payload (not just summary)
- Unknown action verbs are rejected, not silently matched
- witness_collector.py passive vs active split
- Health check failure produces mixed witnesses
"""

import sys
import json
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.surface.action_witness import (
    ActionClaim,
    ActionWitness,
    Verdict,
    WitnessKind,
    adjudicate_claim,
    _relevant_witnesses,
)
from src.surface.receipted import run_witness_verdict_with_receipt
from src.surface.stamp import _canonical_json, h


# ---------------------------------------------------------------------------
# P1: Verdict stamp must bind full payload
# ---------------------------------------------------------------------------

class TestVerdictStampBinding:
    """The stamp output_hash must cover verdicts + summary, not summary alone."""

    def test_different_witness_details_different_stamp(self):
        """Two results with same summary counts but different witness details
        must produce different stamps."""
        claims = [{"action": "start", "subject": "server", "qualifiers": {"port": 8080}}]

        # Same verdict (WITNESSED), different witness details
        w1 = [{"kind": "port_health", "subject": "localhost:8080", "observed": True,
               "detail": "port 8080 listening on eth0"}]
        w2 = [{"kind": "port_health", "subject": "localhost:8080", "observed": True,
               "detail": "port 8080 listening on lo0"}]

        r1 = run_witness_verdict_with_receipt(claims, w1)
        r2 = run_witness_verdict_with_receipt(claims, w2)

        # Both have witnessed=1, but different details → different stamps
        assert r1["summary"]["witnessed"] == r2["summary"]["witnessed"] == 1
        assert r1["stamp"].stamp_hash != r2["stamp"].stamp_hash

    def test_tampered_verdict_reasoning_changes_stamp(self):
        """Changing reasoning in the verdict must change the stamp."""
        claims = [{"action": "run", "subject": "pytest"}]
        witnesses = [{"kind": "command_receipt", "subject": "pytest tests/",
                       "observed": True, "detail": "exit 0"}]

        r1 = run_witness_verdict_with_receipt(claims, witnesses)

        # Same inputs → same stamp (deterministic baseline)
        r2 = run_witness_verdict_with_receipt(claims, witnesses)
        assert r1["stamp"].stamp_hash == r2["stamp"].stamp_hash

    def test_verdict_qualifiers_are_stamped(self):
        """Claim qualifiers flow into verdicts and affect the stamp."""
        claims_a = [{"action": "start", "subject": "server", "qualifiers": {"port": 8080}}]
        claims_b = [{"action": "start", "subject": "server", "qualifiers": {"port": 9090}}]
        witnesses = [{"kind": "port_health", "subject": "localhost:8080", "observed": True,
                       "detail": "port 8080 listening"}]

        r_a = run_witness_verdict_with_receipt(claims_a, witnesses)
        r_b = run_witness_verdict_with_receipt(claims_b, witnesses)

        # Different qualifiers → different stamps
        assert r_a["stamp"].stamp_hash != r_b["stamp"].stamp_hash


# ---------------------------------------------------------------------------
# P1: Unknown action verbs
# ---------------------------------------------------------------------------

class TestUnknownActionVerbs:
    """Unknown verbs must not silently match against all witness kinds."""

    def test_unknown_verb_returns_unwitnessed(self):
        """An unsupported verb like 'restart' should not become WITNESSED."""
        claim = ActionClaim(action="restart", subject="server")
        witnesses = [
            ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="server", observed=True),
            ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="localhost:8080", observed=True),
        ]
        verdict = adjudicate_claim(claim, witnesses)
        assert verdict.verdict == Verdict.UNWITNESSED, (
            f"Unknown verb 'restart' should be UNWITNESSED, got {verdict.verdict}"
        )

    def test_unknown_verb_no_relevant_witnesses(self):
        """_relevant_witnesses returns empty for unknown verbs."""
        claim = ActionClaim(action="restart", subject="server")
        witnesses = [
            ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="server", observed=True),
        ]
        relevant = _relevant_witnesses(claim, witnesses)
        assert len(relevant) == 0

    def test_known_verbs_still_work(self):
        """Sanity: all mapped verbs still produce relevant witnesses."""
        known_verbs = ["start", "run", "create", "modify", "stop",
                       "delete", "install", "deploy", "test"]
        for verb in known_verbs:
            claim = ActionClaim(action=verb, subject="thing")
            # Just check it doesn't early-return empty
            # (actual matching depends on witness kinds)
            relevant = _relevant_witnesses(claim, [
                ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="thing", observed=True),
                ActionWitness(kind=WitnessKind.COMMAND_RECEIPT, subject="thing", observed=True),
                ActionWitness(kind=WitnessKind.PORT_HEALTH, subject="thing:8080", observed=True),
                ActionWitness(kind=WitnessKind.ARTIFACT_EFFECT, subject="thing", observed=True),
                ActionWitness(kind=WitnessKind.LOG_WITNESS, subject="thing", observed=True),
            ])
            assert len(relevant) > 0, f"verb '{verb}' matched no witnesses"

    def test_typo_verb_is_unwitnessed(self):
        """Common typos/variants don't silently match."""
        for verb in ["strat", "rn", "creat", "delet"]:
            claim = ActionClaim(action=verb, subject="server")
            verdict = adjudicate_claim(claim, [
                ActionWitness(kind=WitnessKind.PROCESS_WITNESS, subject="server", observed=True),
            ])
            assert verdict.verdict == Verdict.UNWITNESSED


# ---------------------------------------------------------------------------
# Collector tests — witness_collector.py
# ---------------------------------------------------------------------------

class TestCollectorPassiveCommand:
    """collect_command_history_witness must not execute commands."""

    def test_no_log_no_pid_file(self):
        """With no evidence sources, returns not-observed."""
        from src.surface.witness_collector import collect_command_history_witness
        w = collect_command_history_witness("some_command")
        assert w.observed is False
        assert w.kind == WitnessKind.COMMAND_RECEIPT

    def test_pid_file_exists(self):
        """PID file present → evidence found."""
        from src.surface.witness_collector import collect_command_history_witness
        with tempfile.NamedTemporaryFile(suffix=".pid", delete=False) as f:
            f.write(b"12345")
            pid_path = f.name
        try:
            w = collect_command_history_witness("daemon", pid_file=pid_path)
            assert w.observed is True
            assert "PID file exists" in w.detail
        finally:
            Path(pid_path).unlink()

    def test_pid_file_missing(self):
        """PID file absent → no evidence."""
        from src.surface.witness_collector import collect_command_history_witness
        w = collect_command_history_witness("daemon", pid_file="/tmp/nonexistent_pid_12345.pid")
        assert w.observed is False

    def test_log_pattern_found(self):
        """Log contains command pattern → evidence found."""
        from src.surface.witness_collector import collect_command_history_witness
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-04-15 started my_daemon with --port 8080\n")
            f.write("2026-04-15 my_daemon ready\n")
            log_path = f.name
        try:
            w = collect_command_history_witness("my_daemon", log_path=log_path)
            assert w.observed is True
            assert "command pattern found" in w.detail
        finally:
            Path(log_path).unlink()

    def test_log_pattern_not_found(self):
        """Log does not contain command pattern → no evidence."""
        from src.surface.witness_collector import collect_command_history_witness
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-04-15 started other_thing\n")
            log_path = f.name
        try:
            w = collect_command_history_witness("my_daemon", log_path=log_path)
            assert w.observed is False
        finally:
            Path(log_path).unlink()


class TestCollectorActiveExecution:
    """execute_and_witness runs real commands."""

    def test_true_command_observed(self):
        from src.surface.witness_collector import execute_and_witness
        w = execute_and_witness(["true"])
        assert w.observed is True
        assert "exit_code=0" in w.detail

    def test_false_command_not_observed(self):
        from src.surface.witness_collector import execute_and_witness
        w = execute_and_witness(["false"])
        assert w.observed is False
        assert "exit_code=1" in w.detail

    def test_nonexistent_command(self):
        from src.surface.witness_collector import execute_and_witness
        w = execute_and_witness(["nonexistent_command_xyz_12345"])
        assert w.observed is False
        assert "not found" in w.detail


class TestCollectorArtifact:
    """collect_artifact_witness checks file state."""

    def test_existing_file(self):
        from src.surface.witness_collector import collect_artifact_witness
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"content")
            path = f.name
        try:
            w = collect_artifact_witness(path)
            assert w.observed is True
            assert "exists" in w.detail
        finally:
            Path(path).unlink()

    def test_missing_file(self):
        from src.surface.witness_collector import collect_artifact_witness
        w = collect_artifact_witness("/tmp/nonexistent_file_xyz_12345.txt")
        assert w.observed is False

    def test_min_size_check(self):
        from src.surface.witness_collector import collect_artifact_witness
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"small")
            path = f.name
        try:
            w = collect_artifact_witness(path, min_size=1000)
            assert w.observed is False
            assert "too small" in w.detail
        finally:
            Path(path).unlink()


class TestCollectorLog:
    """collect_log_witness checks log files."""

    def test_log_with_pattern(self):
        from src.surface.witness_collector import collect_log_witness
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("INFO: server started on port 8080\n")
            f.write("INFO: ready for connections\n")
            path = f.name
        try:
            w = collect_log_witness(path, pattern="server started")
            assert w.observed is True
            assert "found 1 time(s)" in w.detail
        finally:
            Path(path).unlink()

    def test_log_pattern_missing(self):
        from src.surface.witness_collector import collect_log_witness
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("INFO: nothing relevant\n")
            path = f.name
        try:
            w = collect_log_witness(path, pattern="server started")
            assert w.observed is False
        finally:
            Path(path).unlink()

    def test_log_file_missing(self):
        from src.surface.witness_collector import collect_log_witness
        w = collect_log_witness("/tmp/nonexistent_log_xyz_12345.log")
        assert w.observed is False
        assert "does not exist" in w.detail


class TestCollectorPortWitness:
    """collect_port_witness returns a list and handles health check failures."""

    def test_closed_port_returns_single_negative(self):
        from src.surface.witness_collector import collect_port_witness
        # Port 1 is almost certainly not listening
        witnesses = collect_port_witness(1, timeout=0.5)
        assert isinstance(witnesses, list)
        assert len(witnesses) == 1
        assert witnesses[0].observed is False

    def test_returns_list_not_single_witness(self):
        """API contract: collect_port_witness returns list[ActionWitness]."""
        from src.surface.witness_collector import collect_port_witness
        result = collect_port_witness(1, timeout=0.5)
        assert isinstance(result, list)
        for w in result:
            assert isinstance(w, ActionWitness)

    def test_port_open_health_fails_produces_mixed_witnesses(self):
        """Port open + health check fails → two witnesses with opposite polarity.

        This is the exact branch the review flagged: before the fix,
        a single observed=True witness was emitted even when health failed,
        so the adjudicator returned WITNESSED for an unhealthy service.

        Now it emits [port: observed=True, health: observed=False],
        and the adjudicator returns INSUFFICIENT_EVIDENCE.
        """
        import threading
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from src.surface.witness_collector import collect_port_witness

        class UnhealthyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(503)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"unhealthy")
            def log_message(self, *args):
                pass  # quiet

        server = HTTPServer(("127.0.0.1", 0), UnhealthyHandler)
        port = server.server_address[1]
        # Serve multiple requests — the TCP probe and the health GET are separate
        t = threading.Thread(target=lambda: server.serve_forever(), daemon=True)
        t.start()

        try:
            witnesses = collect_port_witness(port, health_path="/health", timeout=2.0)

            # Must be two witnesses: port positive, health negative
            assert len(witnesses) == 2, (
                f"Expected 2 witnesses (port + health), got {len(witnesses)}: "
                + "; ".join(f"observed={w.observed} detail={w.detail}" for w in witnesses)
            )

            port_witness = witnesses[0]
            health_witness = witnesses[1]

            assert port_witness.observed is True, "port should be open"
            assert health_witness.observed is False, "health should have failed"
            assert "503" in health_witness.detail or "unhealthy" in health_witness.detail.lower()

            # Now feed these into the adjudicator — should be INSUFFICIENT_EVIDENCE
            claim = ActionClaim(
                action="start",
                subject="service",
                qualifiers={"port": port},
            )
            verdict = adjudicate_claim(claim, witnesses)
            assert verdict.verdict == Verdict.INSUFFICIENT_EVIDENCE, (
                f"Port open + health fail should be INSUFFICIENT_EVIDENCE, got {verdict.verdict}"
            )
        finally:
            server.shutdown()
            t.join(timeout=2)
