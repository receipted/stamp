"""Witness collector — I/O layer for gathering operational evidence.

This is the ONLY module that touches the real world. It checks:
- Did a command actually run? (command receipt)
- Is a process actually running? (process witness)
- Is a port actually listening? (port/health witness)
- Does a log file contain expected output? (log witness)
- Does an artifact/file exist with expected properties? (artifact/effect witness)

Each collector returns an ActionWitness — a frozen, hashable evidence object.
The adjudication engine (action_witness.py) consumes these. It never does I/O.
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .action_witness import ActionWitness, WitnessKind


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Command receipt — did a command run?
# ---------------------------------------------------------------------------

def collect_command_history_witness(
    cmd_pattern: str,
    *,
    log_path: str | None = None,
    pid_file: str | None = None,
) -> ActionWitness:
    """Passive witness: check if a command ran WITHOUT re-executing it.

    This is the correct witness for "did you run X?" questions.
    It checks for evidence that the command ran in the past:
    - Shell history
    - Log file entries
    - PID file existence

    It does NOT re-execute the command. Re-execution would change the world
    and convert an unwitnessed claim into a witnessed one, breaking the
    temporal meaning of the verdict.
    """
    evidence_found = False
    detail_parts = []

    # Check PID file (strongest passive evidence for daemons)
    if pid_file:
        pid_path = Path(pid_file)
        if pid_path.exists():
            evidence_found = True
            detail_parts.append(f"PID file exists: {pid_file}")
        else:
            detail_parts.append(f"no PID file at {pid_file}")

    # Check log for command execution evidence
    if log_path:
        log = Path(log_path)
        if log.exists():
            try:
                content = log.read_text()
                if cmd_pattern.lower() in content.lower():
                    evidence_found = True
                    detail_parts.append(f"command pattern found in {log_path}")
                else:
                    detail_parts.append(f"command pattern not found in {log_path}")
            except PermissionError:
                detail_parts.append(f"cannot read {log_path}")

    if not detail_parts:
        detail_parts.append("no historical evidence sources provided")

    return ActionWitness(
        kind=WitnessKind.COMMAND_RECEIPT,
        subject=cmd_pattern,
        observed=evidence_found,
        detail="; ".join(detail_parts),
        timestamp=_now_iso(),
    )


def execute_and_witness(
    cmd: list[str],
    *,
    timeout: int = 30,
    expected_exit_code: int = 0,
) -> ActionWitness:
    """ACTIVE execution: run a command NOW and witness the result.

    WARNING: This is an active primitive, not a passive witness.
    It changes the world by executing the command. Use this for:
    - Verification commands (e.g., "run the tests to check")
    - Health checks (e.g., "curl the endpoint")
    - Intentional re-execution

    Do NOT use this to answer "did you already run X?" — that question
    requires collect_command_history_witness() instead.
    """
    subject = " ".join(cmd)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        observed = result.returncode == expected_exit_code
        detail = (
            f"exit_code={result.returncode}, "
            f"stdout={len(result.stdout)} bytes, "
            f"stderr={len(result.stderr)} bytes"
        )
        if not observed:
            detail += f" (expected exit_code={expected_exit_code})"
            if result.stderr.strip():
                detail += f"; stderr: {result.stderr.strip()[:200]}"
    except subprocess.TimeoutExpired:
        observed = False
        detail = f"command timed out after {timeout}s"
    except FileNotFoundError:
        observed = False
        detail = f"command not found: {cmd[0]}"

    return ActionWitness(
        kind=WitnessKind.COMMAND_RECEIPT,
        subject=subject,
        observed=observed,
        detail=detail,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# Process witness — is a named process running?
# ---------------------------------------------------------------------------

def collect_process_witness(
    name: str,
    *,
    pid: int | None = None,
) -> ActionWitness:
    """Check if a process is running by name or PID."""
    subject = name
    try:
        if pid:
            # Check specific PID
            os.kill(pid, 0)  # signal 0 = existence check
            observed = True
            detail = f"PID {pid} is alive"
        else:
            # Search by name via pgrep
            result = subprocess.run(
                ["pgrep", "-f", name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            pids = result.stdout.strip().split("\n") if result.stdout.strip() else []
            observed = len(pids) > 0
            detail = f"found {len(pids)} process(es)" if observed else "no matching process found"
            if observed:
                detail += f" (PIDs: {', '.join(pids[:5])})"
    except ProcessLookupError:
        observed = False
        detail = f"PID {pid} does not exist"
    except PermissionError:
        # Process exists but we can't signal it — still a witness
        observed = True
        detail = f"PID {pid} exists (permission denied for signal)"

    return ActionWitness(
        kind=WitnessKind.PROCESS_WITNESS,
        subject=subject,
        observed=observed,
        detail=detail,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# Port/health witness — is something listening?
# ---------------------------------------------------------------------------

def collect_port_witness(
    port: int,
    *,
    host: str = "localhost",
    health_path: str | None = None,
    timeout: float = 3.0,
) -> list[ActionWitness]:
    """Check if a port is listening, optionally hit a health endpoint.

    Returns a LIST of witnesses (not a single witness) because port-open
    and health-ok are independent observations. When the port is open but
    the health check fails, this returns two witnesses:
      - port witness: observed=True (port is listening)
      - health witness: observed=False (health check failed)

    The verdict engine will see the mixed signals and return
    INSUFFICIENT_EVIDENCE instead of incorrectly returning WITNESSED.
    """
    subject = f"{host}:{port}"
    ts = _now_iso()
    witnesses = []

    # Step 1: TCP connect check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.close()
        port_open = True
    except (ConnectionRefusedError, TimeoutError, OSError):
        port_open = False

    if not port_open:
        witnesses.append(ActionWitness(
            kind=WitnessKind.PORT_HEALTH,
            subject=subject,
            observed=False,
            detail=f"port {port} not listening",
            timestamp=ts,
        ))
        return witnesses

    # Port is open — always emit a positive port witness
    witnesses.append(ActionWitness(
        kind=WitnessKind.PORT_HEALTH,
        subject=subject,
        observed=True,
        detail=f"port {port} is listening",
        timestamp=ts,
    ))

    # Step 2: optional health endpoint (separate witness)
    if health_path:
        try:
            import urllib.request
            url = f"http://{host}:{port}{health_path}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                if status < 400:
                    witnesses.append(ActionWitness(
                        kind=WitnessKind.PORT_HEALTH,
                        subject=subject,
                        observed=True,
                        detail=f"health {health_path} returned {status}",
                        timestamp=ts,
                    ))
                else:
                    witnesses.append(ActionWitness(
                        kind=WitnessKind.PORT_HEALTH,
                        subject=subject,
                        observed=False,
                        detail=f"health {health_path} returned {status} (unhealthy)",
                        timestamp=ts,
                    ))
        except Exception as e:
            witnesses.append(ActionWitness(
                kind=WitnessKind.PORT_HEALTH,
                subject=subject,
                observed=False,
                detail=f"health {health_path} failed: {e}",
                timestamp=ts,
            ))

    return witnesses


# ---------------------------------------------------------------------------
# Log witness — does a log contain expected output?
# ---------------------------------------------------------------------------

def collect_log_witness(
    log_path: str,
    *,
    pattern: str | None = None,
    tail_lines: int = 100,
) -> ActionWitness:
    """Check if a log file exists and optionally search for a pattern."""
    subject = log_path
    path = Path(log_path)

    if not path.exists():
        return ActionWitness(
            kind=WitnessKind.LOG_WITNESS,
            subject=subject,
            observed=False,
            detail=f"log file does not exist: {log_path}",
            timestamp=_now_iso(),
        )

    try:
        # Read tail of log
        lines = path.read_text().splitlines()
        tail = lines[-tail_lines:] if len(lines) > tail_lines else lines
        content = "\n".join(tail)

        if pattern:
            matches = [line for line in tail if re.search(pattern, line)]
            observed = len(matches) > 0
            detail = (
                f"pattern '{pattern}' found {len(matches)} time(s) in last {len(tail)} lines"
                if observed else
                f"pattern '{pattern}' not found in last {len(tail)} lines"
            )
        else:
            # No pattern — just check the file has content
            observed = len(content.strip()) > 0
            detail = f"log file has {len(lines)} lines"
            if not observed:
                detail = "log file is empty"
    except PermissionError:
        observed = False
        detail = f"cannot read log file: permission denied"

    return ActionWitness(
        kind=WitnessKind.LOG_WITNESS,
        subject=subject,
        observed=observed,
        detail=detail,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# Artifact/effect witness — does a file/directory exist?
# ---------------------------------------------------------------------------

def collect_artifact_witness(
    artifact_path: str,
    *,
    min_size: int | None = None,
    modified_after: float | None = None,
) -> ActionWitness:
    """Check if an artifact exists with expected properties."""
    subject = artifact_path
    path = Path(artifact_path)

    if not path.exists():
        return ActionWitness(
            kind=WitnessKind.ARTIFACT_EFFECT,
            subject=subject,
            observed=False,
            detail=f"artifact does not exist: {artifact_path}",
            timestamp=_now_iso(),
        )

    stat = path.stat()
    size = stat.st_size
    mtime = stat.st_mtime
    detail_parts = [f"exists, {size} bytes, modified {datetime.fromtimestamp(mtime, timezone.utc).isoformat()}"]

    observed = True

    if min_size is not None and size < min_size:
        observed = False
        detail_parts.append(f"too small (expected >= {min_size})")

    if modified_after is not None and mtime < modified_after:
        observed = False
        detail_parts.append(f"not modified recently enough")

    return ActionWitness(
        kind=WitnessKind.ARTIFACT_EFFECT,
        subject=subject,
        observed=observed,
        detail="; ".join(detail_parts),
        timestamp=_now_iso(),
    )
