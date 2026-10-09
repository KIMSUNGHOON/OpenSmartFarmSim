"""Process observation core for a separately deployed CLI supervisor.

This core owns a child and its bytes. It does not issue an execution signature,
hold a production key, or grant G1 by itself.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time

from .cli_contracts import SCHEMA_BYTES
from .cli_worker import CliWorker, MAX_FINAL, MAX_JSONL, MAX_STDERR


@dataclass(frozen=True)
class LaunchObservation:
    argv: tuple[str, ...]
    cli_version: str
    executable_sha256: str
    prompt_sha256: str
    schema_sha256: str
    process_id: int
    process_start_token: str
    started_at_utc: datetime


@dataclass(frozen=True)
class ProcessObservation:
    started_at_utc: datetime
    ended_at_utc: datetime
    exit_code: int | None
    termination_reason: str
    jsonl: bytes | None
    final_output: bytes | None
    jsonl_sha256: str | None
    final_output_sha256: str | None
    usage: dict[str, int] | None


class CliProcessSupervisor:
    """One-shot observer to run inside the separate supervisor service."""

    def __init__(self, cli_path: Path, codex_home: Path, *,
                 child_env: dict[str, str] | None = None, timeout_seconds: int = 600):
        cli_path, codex_home = Path(cli_path), Path(codex_home)
        if (not cli_path.is_absolute() or not cli_path.is_file() or
                cli_path.is_symlink() or not os.access(cli_path, os.X_OK) or
                not codex_home.is_absolute() or not codex_home.is_dir() or
                codex_home.stat().st_mode & 0o077):
            raise ValueError("pinned executable and private CODEX_HOME required")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 600:
            raise ValueError("invalid CLI timeout")
        if child_env is not None and (type(child_env) is not dict or any(
                key not in {"CODEX_API_KEY", "SSL_CERT_FILE", "HTTPS_PROXY", "HTTP_PROXY",
                            "NO_PROXY"} or type(value) is not str
                for key, value in child_env.items())):
            raise ValueError("child environment includes an unapproved key")
        self.cli_path = cli_path
        self.codex_home = codex_home
        self.child_env = dict(child_env or {})
        if "CODEX_API_KEY" in self.child_env and (codex_home / "auth.json").exists():
            raise ValueError("choose exactly one Codex credential source")
        self.timeout_seconds = timeout_seconds
        self._temporary = None
        self._process = None
        self._streams = ()
        self._launch = None
        self._result = None
        self._deadline = None
        self._paths = None

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()

    def _env(self, home, *, credentials=True):
        env = {"CODEX_HOME": str(home), "HOME": str(home),
               "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
        if credentials:
            env.update(self.child_env)
        return env

    def _attempt_home(self, root):
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
        with tempfile.TemporaryDirectory(prefix="ossf-observer-version-") as home:
            version = subprocess.run([str(self.cli_path), "--version"],
                capture_output=True, timeout=5, check=False,
                env=self._env(Path(home), credentials=False))
        if version.returncode != 0 or len(version.stdout) > 100:
            raise ValueError("CLI version unavailable")
        value = version.stdout.decode("ascii", "strict").strip()
        if not re.fullmatch(r"codex-cli [0-9]+\.[0-9]+\.[0-9]+", value):
            raise ValueError("unexpected CLI version")
        return value

    @staticmethod
    def _process_start_token(pid):
        # Linux /proc stat field 22, after the parenthesized command name.
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        fields = raw.rsplit(")", 1)[1].split()
        if len(fields) < 20 or not fields[19].isdecimal():
            raise ValueError("process start identity unavailable")
        return fields[19]

    def start(self, prompt: bytes) -> LaunchObservation:
        if self._process is not None or self._result is not None:
            raise ValueError("supervisor attempt already started")
        if type(prompt) is not bytes or not 1 <= len(prompt) <= 65536:
            raise ValueError("bounded prompt bytes required")
        self._temporary = tempfile.TemporaryDirectory(prefix="ossf-observed-cli-")
        root = Path(self._temporary.name)
        try:
            home = self._attempt_home(root)
            workdir, output = root / "input", root / "output"
            workdir.mkdir(mode=0o700)
            output.mkdir(mode=0o700)
            schema_path, prompt_path = workdir / "decision.schema.json", workdir / "stdin.txt"
            final_path, stdout_path = output / "decision.json", output / "events.jsonl"
            stderr_path = output / "stderr.txt"
            schema_path.write_bytes(SCHEMA_BYTES)
            prompt_path.write_bytes(prompt)
            schema_path.chmod(0o400)
            prompt_path.chmod(0o400)
            workdir.chmod(0o500)
            version = self._version()
            binary_sha = sha256(self.cli_path.read_bytes()).hexdigest()
            argv = CliWorker._argv(self.cli_path, workdir, schema_path, final_path)
            self._streams = (prompt_path.open("rb"), stdout_path.open("wb"),
                             stderr_path.open("wb"))
            started_at = datetime.now(timezone.utc)
            self._process = subprocess.Popen(argv, stdin=self._streams[0],
                stdout=self._streams[1], stderr=self._streams[2], cwd=workdir,
                env=self._env(home), start_new_session=True, close_fds=True)
            self._deadline = time.monotonic() + self.timeout_seconds
            self._paths = (stdout_path, final_path, stderr_path)
            self._launch = LaunchObservation(tuple(argv), version, binary_sha,
                sha256(prompt_path.read_bytes()).hexdigest(),
                sha256(schema_path.read_bytes()).hexdigest(), self._process.pid,
                self._process_start_token(self._process.pid), started_at)
            return self._launch
        except BaseException:
            self.close()
            raise

    def poll(self) -> ProcessObservation | None:
        if self._result is not None:
            return self._result
        if self._process is None or self._launch is None:
            raise ValueError("supervisor attempt has not started")
        stdout_path, final_path, stderr_path = self._paths
        running = self._process.poll() is None
        timed_out = running and time.monotonic() >= self._deadline
        overflow = any(path.exists() and path.stat().st_size > limit for path, limit in
                       ((stdout_path, MAX_JSONL), (final_path, MAX_FINAL),
                        (stderr_path, MAX_STDERR)))
        if running and not timed_out and not overflow:
            return None
        CliWorker._stop_group(self._process)
        ended_at = datetime.now(timezone.utc)
        for stream in self._streams:
            stream.close()
        self._streams = ()
        jsonl, jsonl_large = CliWorker._bounded_file(stdout_path, MAX_JSONL)
        final, final_large = CliWorker._bounded_file(final_path, MAX_FINAL)
        overflow = overflow or jsonl_large or final_large
        exit_code = self._process.returncode
        usage = None
        reason = ("cli_timeout" if timed_out else "capture_overflow" if overflow else
                  "cli_error" if exit_code != 0 else "final_missing" if final is None else
                  "completed")
        if reason == "completed":
            try:
                usage, terminal = CliWorker._allowed_jsonl(jsonl)
                if terminal != final or usage is None:
                    reason = "invalid_cli_output"
            except (ValueError, UnicodeError, TypeError):
                reason = "invalid_cli_output"
        self._result = ProcessObservation(self._launch.started_at_utc, ended_at,
            exit_code if type(exit_code) is int and 0 <= exit_code <= 255 else None,
            reason, jsonl, final, sha256(jsonl).hexdigest() if jsonl else None,
            sha256(final).hexdigest() if final else None, usage)
        return self._result

    def close(self):
        if self._process is not None and self._result is None:
            CliWorker._stop_group(self._process)
        for stream in self._streams:
            stream.close()
        self._streams = ()
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None
