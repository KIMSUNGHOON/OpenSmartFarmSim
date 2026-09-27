#!/usr/bin/env bash
set -euo pipefail
umask 077

ossf_repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
ossf_mode=${1:---check}
if [[ "$ossf_mode" != "--check" && "$ossf_mode" != "--run" &&
      "$ossf_mode" != "--thermal" ]]; then
    printf 'usage: %s [--check|--run|--thermal]\n' "$0" >&2
    exit 2
fi

if [[ -z "${OSSF_TEST_PG_DSN:-}" ]]; then
    printf 'OSSF_TEST_PG_DSN is required\n' >&2
    exit 2
fi

ossf_cli_bin=${OSSF_REAL_CLI_PATH:-$(command -v codex || true)}
if [[ -z "$ossf_cli_bin" || ! -f "$ossf_cli_bin" || ! -x "$ossf_cli_bin" ]]; then
    printf 'an executable Codex CLI path is required\n' >&2
    exit 2
fi
ossf_cli_version=$("$ossf_cli_bin" --version)
if [[ ! "$ossf_cli_version" =~ ^codex-cli\ [0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    printf 'an expected Codex CLI version is required\n' >&2
    exit 2
fi

ossf_source_home=${OSSF_SOURCE_CODEX_HOME:-${CODEX_HOME:-$HOME/.codex}}
ossf_auth_file="$ossf_source_home/auth.json"
if [[ ! -f "$ossf_auth_file" || -L "$ossf_auth_file" ]]; then
    printf 'a regular private Codex credential file is required\n' >&2
    exit 2
fi
ossf_auth_mode=$(stat -c '%a' -- "$ossf_auth_file")
ossf_auth_owner=$(stat -c '%u' -- "$ossf_auth_file")
if (( (8#$ossf_auth_mode & 077) != 0 )) || [[ "$ossf_auth_owner" != "$(id -u)" ]]; then
    printf 'Codex credential must belong to this user and deny group/other access\n' >&2
    exit 2
fi

cd -- "$ossf_repo_root/backend"
uv run --locked --group dev python - <<'PY'
import os
import psycopg

try:
    with psycopg.connect(os.environ["OSSF_TEST_PG_DSN"], connect_timeout=5) as connection:
        connection.execute("SELECT 1").fetchone()
except Exception:
    raise SystemExit("PostgreSQL smoke database is unavailable")
PY

if [[ "$ossf_mode" == "--check" ]]; then
    printf 'local prerequisites present; model account untested and no model call made\n'
    exit 0
fi

ossf_smoke_root=$(mktemp -d "${TMPDIR:-/tmp}/ossf-cli-smoke.XXXXXXXX")
trap 'rm -rf -- "$ossf_smoke_root"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -m 700 -- "$ossf_smoke_root/home"
install -m 600 -- "$ossf_auth_file" "$ossf_smoke_root/home/auth.json"

if [[ "$ossf_mode" == "--thermal" ]]; then
    ossf_smoke_flag=OSSF_REAL_THERMAL_CLI_SMOKE
    ossf_smoke_test=tests/test_thermal_cli_smoke.py::test_real_cli_synthetic_thermal_review
else
    ossf_smoke_flag=OSSF_REAL_CLI_SMOKE
    ossf_smoke_test=tests/test_cli_worker.py::test_real_cli_three_stage_synthetic_hold
fi

env "$ossf_smoke_flag=1" \
    OSSF_REAL_CLI_PATH="$ossf_cli_bin" \
    OSSF_REAL_CODEX_HOME="$ossf_smoke_root/home" \
    uv run --locked --group dev pytest -q -s "$ossf_smoke_test"
