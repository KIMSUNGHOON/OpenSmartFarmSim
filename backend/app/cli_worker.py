"""Supervise one real Codex CLI attempt and close its durable job lease.

The supervisor observes a local process. Its own observations are not an
independent G1 execution attestation or G4 container/egress proof.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time

from app.cli_contracts import (DecisionContract, ProposalHold, SCHEMA_BYTES,
                               STAGES, _canonical)


MAX_JSONL = 10 * 1024 * 1024
MAX_FINAL = 1024 * 1024
MAX_STDERR = 64 * 1024
MODEL = "gpt-6-sol"
EFFORT = "xhigh"
PROMPT_VERSION = "cli-worker-prompt-v1"
SCHEMA_VERSION = "decision-v1"


@dataclass(frozen=True)
class WorkResult:
    job_id: object
    attempt: int
    state: str
    reason_code: str
    capture_id: object | None = None
    decision_id: object | None = None


class CliWorker:
    def __init__(self, store, contract: DecisionContract, *, cli_path: Path | None = None,
                 codex_home: Path | None = None, child_env: dict[str, str] | None = None,
                 timeout_seconds: int = 600, lease_seconds: int = 660,
                 synthetic_smoke: bool = False, supervisor_client=None,
                 attestation_store=None):
        if synthetic_smoke is not True:
            raise ValueError("production CLI isolation is not yet attested")
        if (not isinstance(contract, DecisionContract) or
                store.decision_validator is not contract or store.evidence_policy is None):
            raise ValueError("trusted contract and evidence policy must be installed on JobStore")
        if (type(timeout_seconds) is not int or type(lease_seconds) is not int or
                not 1 <= timeout_seconds <= 600 or lease_seconds <= timeout_seconds + 5 or
                lease_seconds > 86400):
            raise ValueError("invalid process and lease bounds")
        self.store, self.contract = store, contract
        self.timeout_seconds, self.lease_seconds = timeout_seconds, lease_seconds
        self.supervisor_client, self.attestation_store = supervisor_client, attestation_store
        if supervisor_client is not None:
            from .cli_supervisor_client import SupervisorClient
            from .execution_attestation import ExecutionAttestationStore
            if (not isinstance(supervisor_client, SupervisorClient) or
                    not isinstance(attestation_store, ExecutionAttestationStore) or
                    attestation_store.job_store is not store or
                    cli_path is not None or codex_home is not None or child_env is not None):
                raise ValueError("supervised worker needs a public-key store and no CLI credentials")
            self.cli_path, self.codex_home, self.child_env = None, None, {}
            return
        if cli_path is None or codex_home is None or attestation_store is not None:
            raise ValueError("local worker executable and credential home required")
        cli_path = Path(cli_path)
        codex_home = Path(codex_home)
        if (not cli_path.is_absolute() or not cli_path.is_file() or
                not codex_home.is_absolute() or not codex_home.is_dir()):
            raise ValueError("absolute CLI executable and existing private CODEX_HOME required")
        if codex_home.stat().st_mode & 0o077:
            raise ValueError("CODEX_HOME must not be accessible to other users")
        if child_env is not None and (type(child_env) is not dict or any(
                key not in {"CODEX_API_KEY", "SSL_CERT_FILE", "HTTPS_PROXY", "HTTP_PROXY",
                            "NO_PROXY"} or type(value) is not str
                for key, value in child_env.items())):
            raise ValueError("child environment includes an unapproved key")
        self.store = store
        self.contract = contract
        self.cli_path = cli_path
        self.codex_home = codex_home
        self.child_env = dict(child_env or {})
        if "CODEX_API_KEY" in self.child_env and (codex_home / "auth.json").exists():
            raise ValueError("choose exactly one Codex credential source")
        self.timeout_seconds = timeout_seconds
        self.lease_seconds = lease_seconds

    def _env(self, home=None, *, credentials=True):
        # Never inherit the caller's broad environment or shell startup files.
        child_home = home or self.codex_home
        env = {"CODEX_HOME": str(child_home), "HOME": str(child_home),
               "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
        if credentials:
            env.update(self.child_env)
        return env

    def _attempt_home(self, root: Path):
        """Create a per-attempt home with only the configured credential, no MCP config."""
        home = root / "codex-home"
        home.mkdir(mode=0o700)
        if "CODEX_API_KEY" not in self.child_env:
            source = self.codex_home / "auth.json"
            fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                info = os.fstat(fd)
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                        info.st_mode & 0o077 or info.st_size > 1048576):
                    raise ValueError("Codex credential source is not private")
                target = home / "auth.json"
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    with os.fdopen(fd, "rb", closefd=False) as reader, \
                            os.fdopen(target_fd, "wb", closefd=False) as writer:
                        shutil.copyfileobj(reader, writer)
                    if target.stat().st_size != info.st_size:
                        raise ValueError("Codex credential changed while copying")
                finally:
                    os.close(target_fd)
            finally:
                os.close(fd)
        return home

    def _version(self):
        with tempfile.TemporaryDirectory(prefix="ossf-cli-version-") as home:
            result = subprocess.run([str(self.cli_path), "--version"],
                                    capture_output=True, timeout=5,
                                    env=self._env(Path(home), credentials=False),
                                    check=False)
        if result.returncode != 0 or len(result.stdout) > 100:
            raise ValueError("CLI version unavailable")
        version = result.stdout.decode("ascii", "strict").strip()
        if not re.fullmatch(r"codex-cli [0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("unexpected CLI version")
        return version

    @staticmethod
    def _prompt(job, value, authority):
        # The fixed instruction and bounded canonical input are the exact stdin evidence.
        context = {"job_id": str(job["job_id"]), "tenant_id": job["tenant_id"],
                   "stage": job["stage"], "input_sha256": job["input_sha256"],
                   "input": value, "server_missing_evidence": list(authority.missing_evidence),
                   "server_allows_proceed": authority.allow_proceed}
        instruction = (
            "OpenSmartFarmSim decision proposal v1. Read only the supplied, server-scoped "
            "identifiers. Do not call tools, browse, run commands, or infer farm measurements. "
            "Return one JSON object matching the provided output schema. Echo stage, input "
            "hash and decision context exactly. If server_allows_proceed is false, set "
            "proposed_status to hold, selected_ids to [], claims to [], and missing_evidence "
            "exactly to server_missing_evidence. Do not invent evidence IDs, coefficients, "
            "crop yields, energy purchases, margins, or rankings.\n")
        prompt = instruction.encode("utf-8") + _canonical(context) + b"\n"
        if len(prompt) > 65536:
            raise ProposalHold("prompt_too_large")
        return prompt

    @staticmethod
    def _argv(cli_path, workdir, schema_path, final_path):
        return [str(cli_path), "--ask-for-approval", "never", "exec",
                "-m", MODEL, "-c", 'model_reasoning_effort="xhigh"',
                "--sandbox", "read-only", "--skip-git-repo-check",
                "--ephemeral", "--ignore-user-config", "--json",
                "--output-schema", str(schema_path),
                "--output-last-message", str(final_path),
                "-C", str(workdir), "-"]

    @staticmethod
    def _stop_group(process):
        # The leader may already have exited while descendants keep credentials.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                break
            if sig == signal.SIGTERM:
                time.sleep(0.2)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    @staticmethod
    def _bounded_file(path, limit):
        if not path.exists():
            return None, False
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
        return data[:limit], len(data) > limit

    @staticmethod
    def _allowed_jsonl(data):
        # JobStore verifies lifecycle/final equality. This additionally denies tool use.
        if not data or len(data) > MAX_JSONL:
            raise ProposalHold("jsonl_missing_or_large")
        from app.job_store import JobStore
        usage, final = JobStore._parse_cli_jsonl(data)
        for line in data.splitlines():
            event = json.loads(line)
            if event["type"].startswith("item.") and event["item"]["type"] not in {
                    "agent_message", "reasoning"}:
                raise ProposalHold("unapproved_tool_event")
        return usage, final

    def _close_failure(self, lease, code, *, kind="hold", jsonl_id=None):
        tenant, job_id, attempt, token = (lease["tenant_id"], lease["job_id"],
                                          lease["attempt"], lease["lease_token"])
        if self.store.ack_cancel(tenant, job_id, attempt, token,
                                 jsonl_evidence_id=jsonl_id):
            return WorkResult(job_id, attempt, "canceled", "canceled_by_request")
        closed = self.store.fail(tenant, job_id, attempt, token, kind, code,
                                 jsonl_evidence_id=jsonl_id)
        state = ("unclosed" if not closed else "hold" if kind == "hold" else
                 "queued" if kind == "transient" and attempt < lease["max_attempts"]
                 else "failed")
        return WorkResult(job_id, attempt, state,
                          code if closed else "lease_lost")

    def run_once(self) -> WorkResult | None:
        lease = self.store.claim(self.lease_seconds, allowed_stages=STAGES,
            tenant_id=self.supervisor_client.tenant_id if self.supervisor_client else None)
        if lease is None:
            return None
        try:
            if self.supervisor_client:
                with self.supervisor_client.session() as execution:
                    return self._run_claimed(lease, execution)
            return self._run_claimed(lease)
        except Exception:
            try:
                return self._close_failure(lease, "worker_runtime_error", kind="fatal")
            except Exception:
                return WorkResult(lease["job_id"], lease["attempt"], "unclosed",
                                  "store_unavailable")

    def _run_claimed(self, lease, execution=None) -> WorkResult:
        tenant, job_id, attempt, token = (lease["tenant_id"], lease["job_id"],
                                          lease["attempt"], lease["lease_token"])
        try:
            raw = self.store.read_input(tenant, job_id, attempt, token)
            if raw is None:
                return self._close_failure(lease, "input_unavailable")
            job = dict(lease, input_bytes=raw)
            value, authority = self.contract.input_context(job)
            prompt = self._prompt(job, value, authority)
            version = execution.version() if execution is not None else self._version()
        except ProposalHold as exc:
            return self._close_failure(lease, exc.code)
        except Exception:
            return self._close_failure(lease, "worker_setup_error", kind="fatal")

        prompt_row = self.store.append_evidence(
            tenant, job_id, attempt, token, kind="prompt", payload=prompt,
            rights_ref="server_cli_prompt")
        schema_row = self.store.append_evidence(
            tenant, job_id, attempt, token, kind="output_schema", payload=SCHEMA_BYTES,
            rights_ref="server_cli_schema")
        if (not prompt_row or not schema_row or
                prompt_row["receipt_state"] != "retained" or
                schema_row["receipt_state"] != "retained"):
            return self._close_failure(lease, "invocation_evidence_withheld")
        invocation = self.store.register_invocation(
            tenant, job_id, attempt, token,
            prompt_evidence_id=prompt_row["evidence_id"],
            schema_evidence_id=schema_row["evidence_id"],
            prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION,
            execution_kind="codex_cli", cli_version=version,
            model=MODEL, reasoning_effort=EFFORT)
        if invocation is None:
            return self._close_failure(lease, "invocation_fenced")
        if execution is not None:
            return self._run_supervised(lease, job, execution)

        with tempfile.TemporaryDirectory(prefix="ossf-cli-") as tmp:
            root = Path(tmp)
            try:
                attempt_home = self._attempt_home(root)
            except (OSError, ValueError):
                return self._close_failure(lease, "credential_unavailable", kind="fatal")
            workdir = root / "input"
            output_dir = root / "output"
            workdir.mkdir(mode=0o700)
            output_dir.mkdir(mode=0o700)
            schema_path = workdir / "decision.schema.json"
            prompt_path = workdir / "stdin.txt"
            final_path = output_dir / "decision.json"
            stdout_path = output_dir / "events.jsonl"
            stderr_path = output_dir / "stderr.txt"
            schema_path.write_bytes(SCHEMA_BYTES)
            prompt_path.write_bytes(prompt)
            schema_path.chmod(0o400)
            prompt_path.chmod(0o400)
            workdir.chmod(0o500)
            argv = self._argv(self.cli_path, workdir, schema_path, final_path)
            launch = None
            timed_out = False
            overflow = False
            fenced = False
            with prompt_path.open("rb") as stdin, stdout_path.open("wb") as stdout, \
                    stderr_path.open("wb") as stderr:
                try:
                    process = subprocess.Popen(
                        argv, stdin=stdin, stdout=stdout, stderr=stderr,
                        cwd=workdir, env=self._env(attempt_home), start_new_session=True,
                        close_fds=True)
                except OSError:
                    return self._close_failure(lease, "cli_spawn_error", kind="fatal")
                deadline_reached = threading.Event()
                watchdog_done = threading.Event()

                def watchdog():
                    if not watchdog_done.wait(self.timeout_seconds):
                        deadline_reached.set()
                        for sig in (signal.SIGTERM, signal.SIGKILL):
                            try:
                                os.killpg(process.pid, sig)
                            except ProcessLookupError:
                                break
                            if sig == signal.SIGTERM:
                                watchdog_done.wait(0.2)

                guard = threading.Thread(target=watchdog, daemon=True)
                guard.start()
                try:
                    launch = self.store.record_cli_launch(
                        tenant, job_id, attempt, token, argv=argv,
                        process_id=process.pid)
                    if launch is None:
                        fenced = True
                        self._stop_group(process)
                    else:
                        deadline = time.monotonic() + self.timeout_seconds
                        next_renew = time.monotonic() + 5
                        while process.poll() is None:
                            now = time.monotonic()
                            if now >= deadline or deadline_reached.is_set():
                                timed_out = True
                                self._stop_group(process)
                                break
                            if (stdout_path.stat().st_size > MAX_JSONL or
                                    stderr_path.stat().st_size > MAX_STDERR):
                                overflow = True
                                self._stop_group(process)
                                break
                            if now >= next_renew:
                                if not self.store.renew(tenant, job_id, attempt, token,
                                                        self.lease_seconds):
                                    fenced = True
                                    self._stop_group(process)
                                    break
                                next_renew = now + 5
                            time.sleep(0.05)
                except BaseException:
                    self._stop_group(process)
                    raise
                finally:
                    self._stop_group(process)
                    watchdog_done.set()
                    guard.join(timeout=1)
            timed_out = timed_out or deadline_reached.is_set()
            jsonl, too_large = self._bounded_file(stdout_path, MAX_JSONL)
            final, final_large = self._bounded_file(final_path, MAX_FINAL)
            overflow = overflow or too_large or final_large
            if jsonl is None or jsonl == b"":
                jsonl_row = self.store.append_evidence(
                    tenant, job_id, attempt, token, kind="jsonl", payload=None,
                    withhold_reason="not_received", rights_ref="server_cli_jsonl")
            else:
                jsonl_row = self.store.append_evidence(
                    tenant, job_id, attempt, token, kind="jsonl", payload=jsonl,
                    rights_ref="server_cli_jsonl")
            jsonl_id = jsonl_row["evidence_id"] if jsonl_row else None
            exit_code = process.returncode if type(process.returncode) is int and 0 <= process.returncode <= 255 else None
            reason = ("cli_timeout" if timed_out else "capture_overflow" if overflow else
                      "lease_lost" if fenced else "cli_error" if exit_code != 0 else
                      "final_missing" if final is None else "completed")
            capture = None
            if launch is not None and final is not None:
                capture = self.store.seal_cli_capture(
                    tenant, job_id, attempt, token, launch_id=launch["launch_id"],
                    jsonl_evidence_id=jsonl_id, final_output=final,
                    exit_code=exit_code, termination_reason=reason,
                    completed=(reason == "completed"))
            if reason != "completed":
                return self._close_failure(lease, reason,
                                           kind="transient" if timed_out else "fatal",
                                           jsonl_id=jsonl_id)
            return self._finish_capture(lease, job, capture, jsonl_row, jsonl, final)

    def _run_supervised(self, lease, job, execution):
        tenant, job_id, attempt, token = (lease["tenant_id"], lease["job_id"],
                                         lease["attempt"], lease["lease_token"])
        observed_launch = execution.start(job_id, attempt)
        launch = self.store.record_cli_launch(tenant, job_id, attempt, token,
            argv=list(observed_launch.argv), process_id=observed_launch.process_id)
        if launch is None:
            return self._close_failure(lease, "invocation_fenced")
        deadline, next_renew = time.monotonic() + self.timeout_seconds + 5, time.monotonic() + 5
        while True:
            observed = execution.poll()
            if observed is not None:
                break
            now = time.monotonic()
            if now >= deadline:
                return self._close_failure(lease, "cli_timeout", kind="transient")
            if now >= next_renew:
                if not self.store.renew(tenant, job_id, attempt, token, self.lease_seconds):
                    return self._close_failure(lease, "lease_lost")
                next_renew = now + 5
            time.sleep(0.05)
        jsonl_row = self.store.append_evidence(tenant, job_id, attempt, token, kind="jsonl",
            payload=observed.jsonl if observed.jsonl else None,
            withhold_reason=None if observed.jsonl else "not_received", rights_ref="server_cli_jsonl")
        jsonl_id = jsonl_row["evidence_id"] if jsonl_row else None
        capture = None
        if observed.final_output is not None:
            capture = self.store.seal_cli_capture(tenant, job_id, attempt, token,
                launch_id=launch["launch_id"], jsonl_evidence_id=jsonl_id,
                final_output=observed.final_output, exit_code=observed.exit_code,
                termination_reason=observed.termination_reason,
                completed=observed.termination_reason == "completed")
        if observed.termination_reason != "completed":
            return self._close_failure(lease, observed.termination_reason,
                kind="transient" if observed.termination_reason == "cli_timeout" else "fatal",
                jsonl_id=jsonl_id)
        return self._finish_capture(lease, job, capture, jsonl_row, observed.jsonl,
                                    observed.final_output, execution)

    def _finish_capture(self, lease, job, capture, jsonl_row, jsonl, final, execution=None):
        tenant, job_id, attempt, token = (lease["tenant_id"], lease["job_id"],
                                         lease["attempt"], lease["lease_token"])
        jsonl_id = jsonl_row["evidence_id"] if jsonl_row else None
        if (capture is None or jsonl_row is None or
                jsonl_row["receipt_state"] != "retained" or final is None):
            return self._close_failure(lease, "capture_unverified", jsonl_id=jsonl_id)
        try:
            _, terminal_final = self._allowed_jsonl(jsonl)
            if terminal_final != final:
                raise ProposalHold("final_jsonl_mismatch")
            plan = self.contract.plan(job, final)
        except (ProposalHold, ValueError, UnicodeError) as exc:
            code = exc.code if isinstance(exc, ProposalHold) else "invalid_cli_output"
            return self._close_failure(lease, code, jsonl_id=jsonl_id)
        decision = self.store.record_decision(
            tenant, job_id, attempt, token, final, plan.artifact)
        if decision is None:
            return self._close_failure(lease, "decision_unverified", jsonl_id=jsonl_id)
        if execution is not None:
            from .execution_verifier import ExecutionVerifier
            try:
                raw, signature = execution.issue(capture["capture_id"], decision)
                self.attestation_store.put(raw, signature)
                verifier = ExecutionVerifier(self.attestation_store,
                    executable_sha256=self.supervisor_client.executable_sha256,
                    environment_sha256=self.supervisor_client.environment_sha256)
                if not verifier.verify_pending(tenant, job_id, attempt,
                                               capture["capture_id"], decision):
                    raise ValueError("signed execution differs from durable attempt")
            except Exception:
                return self._close_failure(lease, "execution_attestation_unverified", jsonl_id=jsonl_id)
        if plan.disposition == "hold":
            held = self.store.finish_validated_hold(
                tenant, job_id, attempt, token, decision, plan.artifact)
            return WorkResult(job_id, attempt, "hold" if held else "unclosed",
                              "validated_hold" if held else "closure_fenced",
                              capture["capture_id"], decision)
        published = self.store.publish(
            tenant, job_id, attempt, token, decision, plan.artifact,
            sha256(plan.artifact).hexdigest(), {"schema_version": "1"})
        return WorkResult(job_id, attempt, "succeeded" if published else "unclosed",
                          "validated_proposal" if published else "closure_fenced",
                          capture["capture_id"], decision)
