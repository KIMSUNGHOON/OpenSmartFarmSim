"""Immutable PostgreSQL snapshots and atomic two-trace thermal G1 publication."""

from hashlib import sha256
import hmac
import json
import re

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_GATE_DOMAIN = b"thermal-g1-gate-v1\0"


class ThermalStoreHold(ValueError):
    """A snapshot or Run cannot pass the immutable storage boundary."""


def _need(condition, reason):
    if not condition:
        raise ThermalStoreHold(reason)


def _digest(raw):
    return sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ThermalStoreHold("FORMAT_HOLD: duplicate JSON key")
        value[key] = item
    return value


def _document(raw, *, max_size=16384):
    _need(type(raw) is bytes and 1 <= len(raw) <= max_size, "FORMAT_HOLD: invalid document bytes")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
        _need(type(value) is dict and _canonical(value) == raw,
              "FORMAT_HOLD: noncanonical document")
    except (UnicodeError, ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise ThermalStoreHold("FORMAT_HOLD: invalid canonical JSON") from exc
    return value


def snapshot_id_for(manifest_raw, weather_raw, thermal_raw):
    hashes = [_digest(raw) for raw in (manifest_raw, weather_raw, thermal_raw)]
    return "thermal-snapshot-v1:" + _digest(_canonical(hashes))


def install_thermal_run_schema(conn: psycopg.Connection, schema: str) -> None:
    """Install a fresh v1 schema beside the existing job tables."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.thermal_input_snapshots (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            snapshot_id text NOT NULL CHECK (length(snapshot_id) BETWEEN 1 AND 200),
            manifest_raw bytea NOT NULL CHECK (octet_length(manifest_raw) BETWEEN 1 AND 1048576),
            weather_raw bytea NOT NULL CHECK (octet_length(weather_raw) BETWEEN 1 AND 1048576),
            thermal_raw bytea NOT NULL CHECK (octet_length(thermal_raw) BETWEEN 1 AND 1048576),
            manifest_sha256 char(64) NOT NULL, weather_sha256 char(64) NOT NULL,
            thermal_sha256 char(64) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, snapshot_id),
            CHECK (manifest_sha256 = encode(sha256(manifest_raw), 'hex')),
            CHECK (weather_sha256 = encode(sha256(weather_raw), 'hex')),
            CHECK (thermal_sha256 = encode(sha256(thermal_raw), 'hex'))
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.thermal_g1_runs (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            run_id text NOT NULL CHECK (length(run_id) BETWEEN 1 AND 200),
            snapshot_id text NOT NULL,
            manifest_sha256 char(64) NOT NULL,
            trace0_raw bytea NOT NULL CHECK (octet_length(trace0_raw) BETWEEN 1 AND 1048576),
            trace0_sha256 char(64) NOT NULL,
            trace1_raw bytea NOT NULL CHECK (octet_length(trace1_raw) BETWEEN 1 AND 1048576),
            trace1_sha256 char(64) NOT NULL,
            release_raw bytea NOT NULL CHECK (octet_length(release_raw) BETWEEN 1 AND 16384),
            release_sha256 char(64) NOT NULL,
            release_signature text NOT NULL CHECK (length(release_signature) BETWEEN 1 AND 1024),
            report_raw bytea NOT NULL CHECK (octet_length(report_raw) BETWEEN 1 AND 16384),
            report_sha256 char(64) NOT NULL, gate_signature char(64) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, run_id),
            FOREIGN KEY (tenant_id, snapshot_id)
                REFERENCES {}.thermal_input_snapshots (tenant_id, snapshot_id),
            CHECK (trace0_sha256 = encode(sha256(trace0_raw), 'hex')),
            CHECK (trace1_sha256 = encode(sha256(trace1_raw), 'hex')),
            CHECK (release_sha256 = encode(sha256(release_raw), 'hex')),
            CHECK (report_sha256 = encode(sha256(report_raw), 'hex')),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'run_status') = 'accepted') IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'run_status') = 'accepted') IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'run_id') = run_id) IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'run_id') = run_id) IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'trace_sequence_index') = '0') IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'trace_sequence_index') = '1') IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb#>>
                '{{initial_state,temperature,previous_trace_sha256}}') = trace0_sha256) IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb#>>
                '{{initial_state,humidity_ratio,previous_trace_sha256}}') = trace0_sha256) IS TRUE)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_thermal_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'thermal snapshot and Run are immutable'; END
        $$
    """).format(namespace))
    for table in ("thermal_input_snapshots", "thermal_g1_runs"):
        conn.execute(sql.SQL("""
            CREATE TRIGGER thermal_immutable BEFORE UPDATE OR DELETE ON {}.{}
            FOR EACH ROW EXECUTE FUNCTION {}.reject_thermal_change()
        """).format(namespace, sql.Identifier(table), namespace))


class ThermalRunStore:
    """Server-only raw snapshot and accepted Run store with scoped reads."""

    def __init__(self, dsn, schema, *, gate_key, release_verifier, principal_provider):
        if (type(gate_key) is not bytes or len(gate_key) < 32 or
                not callable(principal_provider)):
            raise ValueError("thermal store needs a gate key and principal provider")
        self.dsn, self.schema = dsn, schema
        self._gate_key = gate_key
        self._release_verifier = release_verifier
        self._principal_provider = principal_provider

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _table(self, name):
        return sql.SQL("{}.{}").format(sql.Identifier(self.schema), sql.Identifier(name))

    def _scope(self, tenant, scope):
        try:
            principal = self._principal_provider()
            scopes = principal.get("scopes") if isinstance(principal, dict) else None
            return bool(type(tenant) is str and tenant and isinstance(principal, dict) and
                        principal.get("authenticated") is True and principal.get("tenant_id") == tenant and
                        isinstance(scopes, (tuple, list, set, frozenset)) and
                        all(type(item) is str for item in scopes) and scope in scopes)
        except Exception:
            return False

    def put_snapshot(self, tenant, manifest_raw, weather_raw, thermal_raw):
        _need(self._scope(tenant, "thermal_snapshot_write"), "ACCESS_HOLD: snapshot write denied")
        raws = (manifest_raw, weather_raw, thermal_raw)
        _need(all(type(raw) is bytes and 1 <= len(raw) <= 1048576 for raw in raws),
              "INPUT_HOLD: invalid snapshot bytes")
        snapshot_id = snapshot_id_for(*raws)
        hashes = tuple(map(_digest, raws))
        with self.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, snapshot_id, manifest_raw, weather_raw, thermal_raw,
                    manifest_sha256, weather_sha256, thermal_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """).format(self._table("thermal_input_snapshots")),
                (tenant, snapshot_id, *raws, *hashes))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND snapshot_id = %s
            """).format(self._table("thermal_input_snapshots")),
                (tenant, snapshot_id)).fetchone()
            _need(row is not None and tuple(row[key] for key in
                ("manifest_raw", "weather_raw", "thermal_raw")) == raws,
                "PIN_HOLD: snapshot ID collision or changed bytes")
        return snapshot_id

    def get_snapshot(self, tenant, snapshot_id):
        if not self._scope(tenant, "thermal_snapshot_read"):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND snapshot_id = %s
            """).format(self._table("thermal_input_snapshots")),
                (tenant, snapshot_id)).fetchone()
        if row is None:
            return None
        raws = tuple(row[key] for key in ("manifest_raw", "weather_raw", "thermal_raw"))
        _need(snapshot_id_for(*raws) == row["snapshot_id"] == snapshot_id and
              tuple(map(_digest, raws)) == tuple(row[key] for key in
                  ("manifest_sha256", "weather_sha256", "thermal_sha256")),
              "PIN_HOLD: stored snapshot integrity mismatch")
        return row

    def _check_packet(self, report_raw, gate_signature, release_raw, release_signature, trace_raws):
        _need(type(trace_raws) in (tuple, list) and len(trace_raws) == 2 and
              all(type(raw) is bytes and 1 <= len(raw) <= 1048576 for raw in trace_raws),
              "TRACE_HOLD: exactly two bounded raw traces required")
        _need(type(gate_signature) is str and _DIGEST.fullmatch(gate_signature) and
              type(release_signature) is str and 1 <= len(release_signature) <= 1024,
              "SIGNATURE_HOLD: missing gate/release signature")
        report = _document(report_raw)
        release = _document(release_raw)
        hashes = [_digest(raw) for raw in trace_raws]
        expected_gate = hmac.new(self._gate_key, _GATE_DOMAIN + report_raw + b"\0" +
                                 hashes[0].encode() + hashes[1].encode(), sha256).hexdigest()
        try:
            attestation = (self._release_verifier(release_raw, release_signature)
                           if callable(self._release_verifier) else None)
        except Exception as exc:
            raise ThermalStoreHold("SIGNATURE_HOLD: release verifier failed") from exc
        _need(type(attestation) is dict and
              set(attestation) == {"authority_id", "reviewer", "review_evidence_raw"} and
              type(attestation["authority_id"]) is str and attestation["authority_id"] and
              type(attestation["reviewer"]) is str and attestation["reviewer"] and
              type(attestation["review_evidence_raw"]) is bytes and
              1 <= len(attestation["review_evidence_raw"]) <= 1048576 and
              _digest(attestation["review_evidence_raw"]) == release.get("review_evidence_sha256") and
              attestation["authority_id"] == release.get("authority_id") and
              attestation["reviewer"] == release.get("reviewer") and
              hmac.compare_digest(gate_signature, expected_gate),
              "SIGNATURE_HOLD: untrusted gate/release evidence")
        required = {"gate_version", "status", "tenant_id", "run_id", "snapshot_id", "decision_id",
                    "review_job_id", "review_capture_id",
                    "decision_at_utc", "manifest_sha256", "code_sha256",
                    "environment_sha256", "release_sha256", "trace_sha256"}
        _need(set(report) == required and report["gate_version"] == "thermal-g1-publisher-v1" and
              report["status"] == "pass" and type(report["run_id"]) is str and
              type(report["tenant_id"]) is str and bool(report["tenant_id"]) and
              type(report["snapshot_id"]) is str and type(report["decision_id"]) is str and
              all(type(report[key]) is str and bool(report[key]) for key in
                  ("review_job_id", "review_capture_id")) and
              report["release_sha256"] == _digest(release_raw) and
              report["trace_sha256"] == hashes and
              all(type(report[key]) is str and _DIGEST.fullmatch(report[key]) for key in
                  ("manifest_sha256", "code_sha256", "environment_sha256")),
              "REPORT_HOLD: gate report binding mismatch")
        _need(release.get("release_version") == "thermal-g1-release-v1",
              "RELEASE_HOLD: invalid release version")
        try:
            first, second = (_document(raw, max_size=1048576) for raw in trace_raws)
            _need(first["run_status"] == second["run_status"] == "accepted" and
                  first["run_id"] == second["run_id"] == report["run_id"] and
                  first["trace_sequence_index"] == 0 and second["trace_sequence_index"] == 1 and
                  first["input_snapshot_id"] == second["input_snapshot_id"] == report["snapshot_id"] and
                  first["decision_id"] == second["decision_id"] == report["decision_id"] and
                  first["manifest_sha256"] == second["manifest_sha256"] == report["manifest_sha256"] and
                  first["interval"]["end_utc"] == second["interval"]["start_utc"],
                  "TRACE_HOLD: accepted trace identity/adjacency mismatch")
            for field in ("temperature", "humidity_ratio"):
                carry = second["initial_state"][field]
                pointer = f"/steps/{len(first['steps']) - 1}/state_end/{field}"
                _need(carry["previous_trace_sha256"] == hashes[0] and
                      carry["previous_trace_id"] == first["trace_id"] and
                      carry["previous_state_pointer"] == pointer and
                      carry["basis_ref"] == f"trace-sha256:{hashes[0]}#{pointer}" and
                      (carry["value"], carry["unit"]) ==
                      (first["steps"][-1]["state_end"][field]["value"],
                       first["steps"][-1]["state_end"][field]["unit"]),
                      "TRACE_HOLD: accepted carry mismatches final first bytes")
        except (KeyError, IndexError, TypeError) as exc:
            raise ThermalStoreHold("TRACE_HOLD: malformed accepted trace") from exc
        return report

    def publish_verified(self, tenant, *, report_raw, gate_signature, release_raw,
                         release_signature, trace_raws):
        _need(self._scope(tenant, "thermal_run_publish"), "ACCESS_HOLD: Run publication denied")
        report = self._check_packet(report_raw, gate_signature, release_raw,
                                    release_signature, trace_raws)
        _need(report["tenant_id"] == tenant,
              "REPORT_HOLD: signed tenant differs from publication tenant")
        hashes = tuple(map(_digest, trace_raws))
        with self.connect() as conn:
            snapshot = conn.execute(sql.SQL("""
                SELECT manifest_sha256 FROM {} WHERE tenant_id = %s AND snapshot_id = %s
            """).format(self._table("thermal_input_snapshots")),
                (tenant, report["snapshot_id"])).fetchone()
            _need(snapshot is not None and snapshot["manifest_sha256"] == report["manifest_sha256"],
                  "PIN_HOLD: missing or different immutable snapshot")
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, run_id, snapshot_id, manifest_sha256,
                    trace0_raw, trace0_sha256, trace1_raw, trace1_sha256,
                    release_raw, release_sha256, release_signature,
                    report_raw, report_sha256, gate_signature)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """).format(self._table("thermal_g1_runs")),
                (tenant, report["run_id"], report["snapshot_id"], report["manifest_sha256"],
                 trace_raws[0], hashes[0], trace_raws[1], hashes[1],
                 release_raw, _digest(release_raw), release_signature,
                 report_raw, _digest(report_raw), gate_signature))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND run_id = %s
            """).format(self._table("thermal_g1_runs")),
                (tenant, report["run_id"])).fetchone()
            _need(row is not None, "STORE_HOLD: publication row missing")
            _need(row["trace0_raw"] == trace_raws[0] and row["trace1_raw"] == trace_raws[1] and
                  row["report_raw"] == report_raw and row["gate_signature"] == gate_signature and
                  row["release_raw"] == release_raw and row["release_signature"] == release_signature,
                  "STORE_HOLD: conflicting immutable Run ID")
        return {"run_id": report["run_id"], "trace_sha256": hashes,
                "report_sha256": _digest(report_raw)}

    def get_run(self, tenant, run_id):
        if not self._scope(tenant, "thermal_run_read"):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND run_id = %s
            """).format(self._table("thermal_g1_runs")),
                (tenant, run_id)).fetchone()
        if row is None:
            return None
        _need(_digest(row["trace0_raw"]) == row["trace0_sha256"] and
              _digest(row["trace1_raw"]) == row["trace1_sha256"] and
              _digest(row["report_raw"]) == row["report_sha256"] and
              _digest(row["release_raw"]) == row["release_sha256"],
              "STORE_HOLD: Run byte integrity mismatch")
        report = self._check_packet(row["report_raw"], row["gate_signature"],
                                    row["release_raw"], row["release_signature"],
                                    (row["trace0_raw"], row["trace1_raw"]))
        _need(report["tenant_id"] == tenant and report["run_id"] == run_id and
              report["snapshot_id"] == row["snapshot_id"] and
              report["manifest_sha256"] == row["manifest_sha256"],
              "STORE_HOLD: Run index mismatch")
        return {"run_id": run_id, "trace_raws": (row["trace0_raw"], row["trace1_raw"]),
                "report": report, "report_raw": row["report_raw"],
                "release_raw": row["release_raw"], "recorded_at": row["recorded_at"]}
