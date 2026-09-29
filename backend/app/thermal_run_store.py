"""Immutable PostgreSQL snapshots and atomic two-trace thermal G1 publication."""

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_GATE_DOMAIN = b"thermal-g1-gate-v1\0"
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


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


def _time(value):
    _need(type(value) is str and _UTC.fullmatch(value), "TIME_HOLD: invalid UTC")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ThermalStoreHold("TIME_HOLD: invalid UTC calendar date") from exc


def _context(raw, signature, verifier):
    context = _document(raw)
    required = {"context_version", "tenant_id", "snapshot_id", "decision_context_id",
                "decision_at_utc", "claim_mode", "decision_time_kind", "authority_id",
                "issued_at_utc", "planning_event_sha256"}
    _need(set(context) == required and context["context_version"] == "decision-context-v1" and
          all(type(context[key]) is str and bool(context[key]) for key in
              ("tenant_id", "snapshot_id", "decision_context_id", "authority_id")) and
          context["claim_mode"] in ("ex_ante", "ex_post_replay") and
          context["decision_time_kind"] in ("actual", "hypothetical") and
          type(context["planning_event_sha256"]) is str and
          _DIGEST.fullmatch(context["planning_event_sha256"]) and
          _time(context["decision_at_utc"]) is not None and
          _time(context["issued_at_utc"]) is not None,
          "CONTEXT_HOLD: malformed decision context")
    _need(type(signature) is str and 1 <= len(signature) <= 1024,
          "SIGNATURE_HOLD: missing context signature")
    try:
        attestation = verifier(raw, signature) if callable(verifier) else None
    except Exception as exc:
        raise ThermalStoreHold("SIGNATURE_HOLD: context verifier failed") from exc
    _need(type(attestation) is dict and set(attestation) ==
          {"authority_id", "planning_event_sha256", "decision_at_utc", "decision_time_kind"} and
          attestation["authority_id"] == context["authority_id"] and
          attestation["planning_event_sha256"] == context["planning_event_sha256"] and
          attestation["decision_at_utc"] == context["decision_at_utc"] and
          attestation["decision_time_kind"] == context["decision_time_kind"],
          "SIGNATURE_HOLD: untrusted decision context")
    return context


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
        CREATE TABLE {}.decision_contexts (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            decision_context_id text NOT NULL CHECK (length(decision_context_id) BETWEEN 1 AND 200),
            snapshot_id text NOT NULL CHECK (length(snapshot_id) BETWEEN 1 AND 200),
            context_raw bytea NOT NULL CHECK (octet_length(context_raw) BETWEEN 1 AND 16384),
            context_sha256 char(64) NOT NULL,
            context_signature text NOT NULL CHECK (length(context_signature) BETWEEN 1 AND 1024),
            authority_id text NOT NULL CHECK (length(authority_id) BETWEEN 1 AND 200),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, decision_context_id),
            UNIQUE (tenant_id, snapshot_id, decision_context_id),
            CHECK (context_sha256 = encode(sha256(context_raw), 'hex')),
            CHECK (((convert_from(context_raw, 'UTF8')::jsonb->>'tenant_id') = tenant_id) IS TRUE),
            CHECK (((convert_from(context_raw, 'UTF8')::jsonb->>'decision_context_id') = decision_context_id) IS TRUE),
            CHECK (((convert_from(context_raw, 'UTF8')::jsonb->>'snapshot_id') = snapshot_id) IS TRUE),
            CHECK (((convert_from(context_raw, 'UTF8')::jsonb->>'authority_id') = authority_id) IS TRUE)
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.thermal_g1_runs (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            run_id text NOT NULL CHECK (length(run_id) BETWEEN 1 AND 200),
            snapshot_id text NOT NULL,
            decision_context_id text NOT NULL,
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
            FOREIGN KEY (tenant_id, snapshot_id, decision_context_id)
                REFERENCES {}.decision_contexts (tenant_id, snapshot_id, decision_context_id),
            CHECK (trace0_sha256 = encode(sha256(trace0_raw), 'hex')),
            CHECK (trace1_sha256 = encode(sha256(trace1_raw), 'hex')),
            CHECK (release_sha256 = encode(sha256(release_raw), 'hex')),
            CHECK (report_sha256 = encode(sha256(report_raw), 'hex')),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'run_status') = 'accepted') IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'run_status') = 'accepted') IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'run_id') = run_id) IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'run_id') = run_id) IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'decision_context_id') = decision_context_id) IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'decision_context_id') = decision_context_id) IS TRUE),
            CHECK (((convert_from(report_raw, 'UTF8')::jsonb->>'decision_context_id') = decision_context_id) IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'decision_at_utc') =
                    (convert_from(trace1_raw, 'UTF8')::jsonb->>'decision_at_utc')) IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'review_at_utc') =
                    (convert_from(trace1_raw, 'UTF8')::jsonb->>'review_at_utc')) IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'claim_mode') =
                    (convert_from(report_raw, 'UTF8')::jsonb->>'claim_mode')) IS TRUE),
            CHECK (((convert_from(trace0_raw, 'UTF8')::jsonb->>'trace_sequence_index') = '0') IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb->>'trace_sequence_index') = '1') IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb#>>
                '{{initial_state,temperature,previous_trace_sha256}}') = trace0_sha256) IS TRUE),
            CHECK (((convert_from(trace1_raw, 'UTF8')::jsonb#>>
                '{{initial_state,humidity_ratio,previous_trace_sha256}}') = trace0_sha256) IS TRUE)
        )
    """).format(namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_thermal_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'thermal snapshot and Run are immutable'; END
        $$
    """).format(namespace))
    for table in ("thermal_input_snapshots", "decision_contexts", "thermal_g1_runs"):
        conn.execute(sql.SQL("""
            CREATE TRIGGER thermal_immutable BEFORE UPDATE OR DELETE ON {}.{}
            FOR EACH ROW EXECUTE FUNCTION {}.reject_thermal_change()
        """).format(namespace, sql.Identifier(table), namespace))


class ThermalRunStore:
    """Server-only raw snapshot and accepted Run store with scoped reads."""

    def __init__(self, dsn, schema, *, gate_key, release_verifier, principal_provider,
                 context_verifier=None, runtime_identity=None):
        if (type(gate_key) is not bytes or len(gate_key) < 32 or
                not callable(principal_provider)):
            raise ValueError("thermal store needs a gate key and principal provider")
        if runtime_identity is not None:
            from .runtime_roles import RuntimeLoginPolicy
            if (type(runtime_identity) is not tuple or len(runtime_identity) != 2 or
                    type(runtime_identity[0]) is not RuntimeLoginPolicy or runtime_identity[0].schema != schema or
                    runtime_identity[1] != "authority"):
                raise ValueError("thermal store requires the authority login profile")
        self.dsn, self.schema = dsn, schema
        self.runtime_identity = runtime_identity
        self._gate_key = gate_key
        self._release_verifier = release_verifier
        self._context_verifier = context_verifier
        self._principal_provider = principal_provider

    def connect(self):
        if self.runtime_identity is not None:
            from .runtime_login import connect_runtime
            from .runtime_roles import audit_runtime_roles
            policy, kind = self.runtime_identity
            conn = connect_runtime(self.dsn, policy, kind)
            try:
                audit_runtime_roles(conn, policy)
                conn.commit()
                return conn
            except Exception:
                conn.close()
                raise ThermalStoreHold("LOGIN_HOLD: runtime grants rejected") from None
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
        _need(all(type(raw) is bytes and 1 <= len(raw) <= 1048576 for raw in
                  (manifest_raw, weather_raw, thermal_raw)), "INPUT_HOLD: invalid snapshot bytes")
        with self.connect() as conn:
            return self._pin_snapshot_in_transaction(conn, tenant, manifest_raw, weather_raw, thermal_raw)

    def _pin_snapshot_in_transaction(self, conn, tenant, manifest_raw, weather_raw, thermal_raw):
        _need(self._scope(tenant, "thermal_snapshot_write"), "ACCESS_HOLD: snapshot write denied")
        raws = (manifest_raw, weather_raw, thermal_raw)
        _need(all(type(raw) is bytes and 1 <= len(raw) <= 1048576 for raw in raws),
              "INPUT_HOLD: invalid snapshot bytes")
        snapshot_id = snapshot_id_for(*raws)
        hashes = tuple(map(_digest, raws))
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

    def put_decision_context(self, tenant, context_raw, context_signature):
        """Persist a signed, immutable tenant/snapshot context for any product stage."""
        _need(self._scope(tenant, "decision_context_write"), "ACCESS_HOLD: context write denied")
        context = _context(context_raw, context_signature, self._context_verifier)
        _need(context["tenant_id"] == tenant, "CONTEXT_HOLD: context tenant differs")
        with self.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, decision_context_id, snapshot_id, context_raw,
                    context_sha256, context_signature, authority_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """).format(self._table("decision_contexts")),
                (tenant, context["decision_context_id"], context["snapshot_id"], context_raw,
                 _digest(context_raw), context_signature, context["authority_id"]))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND decision_context_id=%s
            """).format(self._table("decision_contexts")),
                (tenant, context["decision_context_id"])).fetchone()
            _need(row is not None and row["context_raw"] == context_raw and
                  row["context_signature"] == context_signature,
                  "CONTEXT_HOLD: conflicting immutable context ID")
        return context["decision_context_id"]

    def get_decision_context(self, tenant, snapshot_id, context_id):
        if not self._scope(tenant, "decision_context_read"):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND snapshot_id=%s AND decision_context_id=%s
            """).format(self._table("decision_contexts")),
                (tenant, snapshot_id, context_id)).fetchone()
        if row is None:
            return None
        context = _context(row["context_raw"], row["context_signature"], self._context_verifier)
        _need(context["tenant_id"] == tenant and context["snapshot_id"] == snapshot_id and
              context["decision_context_id"] == context_id and
              context["authority_id"] == row["authority_id"] and
              _digest(row["context_raw"]) == row["context_sha256"],
              "CONTEXT_HOLD: stored authority or context bytes differ")
        return {**context, "context_sha256": row["context_sha256"],
                "recorded_at": row["recorded_at"]}

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
              set(attestation) == {"authority_id", "reviewer", "review_evidence_raw",
                                   "issued_at_utc"} and
              type(attestation["authority_id"]) is str and attestation["authority_id"] and
              type(attestation["reviewer"]) is str and attestation["reviewer"] and
              type(attestation["review_evidence_raw"]) is bytes and
              1 <= len(attestation["review_evidence_raw"]) <= 1048576 and
              _digest(attestation["review_evidence_raw"]) == release.get("review_evidence_sha256") and
              attestation["authority_id"] == release.get("authority_id") and
              attestation["reviewer"] == release.get("reviewer") and
              attestation["issued_at_utc"] == release.get("issued_at_utc") and
              hmac.compare_digest(gate_signature, expected_gate),
              "SIGNATURE_HOLD: untrusted gate/release evidence")
        required = {"gate_version", "status", "tenant_id", "run_id", "snapshot_id", "decision_id",
                    "decision_context_id", "context_sha256", "review_at_utc",
                    "claim_mode", "decision_time_kind",
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
                  ("manifest_sha256", "code_sha256", "environment_sha256",
                   "context_sha256")) and
              type(report["decision_context_id"]) is str and bool(report["decision_context_id"]) and
              report["claim_mode"] in ("ex_ante", "ex_post_replay") and
              report["decision_time_kind"] in ("actual", "hypothetical") and
              _time(report["decision_at_utc"]) <= _time(report["review_at_utc"]),
              "REPORT_HOLD: gate report binding mismatch")
        _need(report["claim_mode"] == "ex_post_replay",
              "REPORT_HOLD: ex-ante lacks durable D-time evidence protocol")
        _need(release.get("release_version") == "thermal-g1-release-v1",
              "RELEASE_HOLD: invalid release version")
        _need(release.get("snapshot_id") == report["snapshot_id"] and
              release.get("context_sha256") == report["context_sha256"] and
              all(release.get(key) == report[key] for key in
                  ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")) and
              _time(release.get("reviewed_at_utc")) <= _time(release.get("issued_at_utc")) <=
                  _time(report["review_at_utc"]),
              "RELEASE_HOLD: release context differs from gate report")
        run_identity = {
            "decision_at_utc": report["decision_at_utc"],
            "decision_id": report["decision_id"],
            "decision_context_id": report["decision_context_id"],
            "claim_mode": report["claim_mode"],
            "decision_time_kind": report["decision_time_kind"],
            "review_at_utc": report["review_at_utc"],
            "input_snapshot_id": report["snapshot_id"],
            "manifest_sha256": report["manifest_sha256"],
            "model_version": "thermal-v1",
            "parameter_set_version": "synthetic-thermal-parameters-v1",
            "engine_version": "thermal-euler-v1",
            "unit_registry_version": "thermal-si-nws-v1",
        }
        _need(report["run_id"] == "synthetic-thermal-v1:" + _digest(_canonical(run_identity)),
              "REPORT_HOLD: contextual Run identity differs")
        try:
            first, second = (_document(raw, max_size=1048576) for raw in trace_raws)
            _need(first["run_status"] == second["run_status"] == "accepted" and
                  first["run_id"] == second["run_id"] == report["run_id"] and
                  first["trace_sequence_index"] == 0 and second["trace_sequence_index"] == 1 and
                  first["input_snapshot_id"] == second["input_snapshot_id"] == report["snapshot_id"] and
                  first["decision_id"] == second["decision_id"] == report["decision_id"] and
                  all(first[key] == second[key] == report[key] for key in
                      ("decision_context_id", "decision_at_utc", "review_at_utc",
                       "claim_mode", "decision_time_kind")) and
                  first["manifest_sha256"] == second["manifest_sha256"] == report["manifest_sha256"] and
                  all(first[key] == second[key] == expected for key, expected in
                      (("model_version", "thermal-v1"),
                       ("parameter_set_version", "synthetic-thermal-parameters-v1"),
                       ("engine_version", "thermal-euler-v1"),
                       ("unit_registry_version", "thermal-si-nws-v1"))) and
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
        with self.connect() as conn:
            return self._publish_verified_in_transaction(conn, tenant, report_raw=report_raw,
                gate_signature=gate_signature, release_raw=release_raw,
                release_signature=release_signature, trace_raws=trace_raws)

    def _publish_verified_in_transaction(self, conn, tenant, *, report_raw, gate_signature, release_raw,
                         release_signature, trace_raws):
        _need(self._scope(tenant, "thermal_run_publish"), "ACCESS_HOLD: Run publication denied")
        report = self._check_packet(report_raw, gate_signature, release_raw,
                                    release_signature, trace_raws)
        _need(report["tenant_id"] == tenant,
              "REPORT_HOLD: signed tenant differs from publication tenant")
        hashes = tuple(map(_digest, trace_raws))
        context_row = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id=%s AND snapshot_id=%s AND decision_context_id=%s
        """).format(self._table("decision_contexts")),
            (tenant, report["snapshot_id"], report["decision_context_id"])).fetchone()
        _need(context_row is not None and
              _digest(context_row["context_raw"]) == report["context_sha256"],
              "CONTEXT_HOLD: trusted context record missing")
        context = _context(context_row["context_raw"], context_row["context_signature"],
                           self._context_verifier)
        _need(context["tenant_id"] == tenant and
              context["snapshot_id"] == report["snapshot_id"] and
              all(context[key] == report[key] for key in
                  ("decision_context_id", "decision_at_utc", "claim_mode",
                   "decision_time_kind")) and
              context_row["recorded_at"] <= _time(report["review_at_utc"]) and
              context_row["recorded_at"] <=
                  _time(_document(release_raw)["issued_at_utc"]) and
              _time(context["issued_at_utc"]) <= _time(report["review_at_utc"]),
              "CONTEXT_HOLD: report differs from signed context")
        snapshot = conn.execute(sql.SQL("""
            SELECT manifest_sha256, recorded_at FROM {} WHERE tenant_id = %s AND snapshot_id = %s
        """).format(self._table("thermal_input_snapshots")),
            (tenant, report["snapshot_id"])).fetchone()
        _need(snapshot is not None and snapshot["manifest_sha256"] == report["manifest_sha256"] and
              snapshot["recorded_at"] <= _time(report["review_at_utc"]),
              "PIN_HOLD: missing or different immutable snapshot")
        conn.execute(sql.SQL("""
            INSERT INTO {} (tenant_id, run_id, snapshot_id, decision_context_id, manifest_sha256,
                trace0_raw, trace0_sha256, trace1_raw, trace1_sha256,
                release_raw, release_sha256, release_signature,
                report_raw, report_sha256, gate_signature)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """).format(self._table("thermal_g1_runs")),
            (tenant, report["run_id"], report["snapshot_id"],
             report["decision_context_id"], report["manifest_sha256"],
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
        with self.connect() as conn:
            context_row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND snapshot_id=%s AND decision_context_id=%s
            """).format(self._table("decision_contexts")),
                (tenant, row["snapshot_id"], row["decision_context_id"])).fetchone()
        _need(context_row is not None and
              _digest(context_row["context_raw"]) == report["context_sha256"],
              "CONTEXT_HOLD: stored context missing on read")
        context = _context(context_row["context_raw"], context_row["context_signature"],
                           self._context_verifier)
        _need(context["tenant_id"] == tenant and context["snapshot_id"] == row["snapshot_id"] and
              all(context[key] == report[key] for key in
                  ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")) and
              context_row["recorded_at"] <=
                  _time(_document(row["release_raw"])["issued_at_utc"]),
              "CONTEXT_HOLD: stored context differs on read")
        _need(report["tenant_id"] == tenant and report["run_id"] == run_id and
              report["snapshot_id"] == row["snapshot_id"] and
              report["decision_context_id"] == row["decision_context_id"] and
              report["manifest_sha256"] == row["manifest_sha256"],
              "STORE_HOLD: Run index mismatch")
        return {"run_id": run_id, "trace_raws": (row["trace0_raw"], row["trace1_raw"]),
                "report": report, "report_raw": row["report_raw"],
                "release_raw": row["release_raw"], "recorded_at": row["recorded_at"]}
