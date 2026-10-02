"""Signed, append-only MarketContext unavailability reports for a known decision."""

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .market_runtime import connect_market, validate_market_identity


_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")
_DOMAIN = b"market-hold-v1\0"
_MISSING = ("market_source_rights", "market_source_vintage",
            "market_source_qc", "approved_market_snapshot")
_SCOPE_KEYS = {"tenant_id", "snapshot_id", "decision_context_id", "candidate_ids",
               "sales_start_utc", "sales_end_utc", "scope_version"}
_REPORT_KEYS = {"report_version", "hold_report_id", "tenant_id", "snapshot_id",
                "decision_context_id", "context_sha256", "decision_at_utc",
                "claim_mode", "decision_time_kind", "evaluation_status", "status",
                "evaluated_at_utc", "review_at_utc", "scope", "reasons",
                "missing_evidence", "reviewed_source_ids", "rights"}


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(raw):
    return sha256(raw).hexdigest()


def _name(value):
    return type(value) is str and _NAME.fullmatch(value) is not None


def _time(value):
    _need(type(value) is str and _UTC.fullmatch(value), "market hold UTC time invalid")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("market hold UTC calendar date invalid") from exc


def _scope(value, tenant, snapshot, context_id):
    _need(type(value) is dict and set(value) == _SCOPE_KEYS and
          (value["tenant_id"], value["snapshot_id"], value["decision_context_id"]) ==
          (tenant, snapshot, context_id) and _name(value["scope_version"]),
          "market hold scope is not server bound")
    candidates = value["candidate_ids"]
    _need(type(candidates) is list and 1 <= len(candidates) <= 20 and
          all(_name(item) for item in candidates) and len(set(candidates)) == len(candidates),
          "market hold candidate scope invalid")
    _need(_time(value["sales_start_utc"]) < _time(value["sales_end_utc"]),
          "market hold sales period invalid")
    return value


class MarketHoldStore:
    """Configured server authority; API clients may supply only a report ID."""

    def __init__(self, dsn, schema, *, context_store, scope_resolver,
                 principal_provider, signing_key, runtime_identity=None):
        if (not callable(getattr(context_store, "get_decision_context", None)) or
                not callable(scope_resolver) or not callable(principal_provider) or
                type(signing_key) is not bytes or len(signing_key) < 32):
            raise ValueError("market hold needs trusted server dependencies")
        validate_market_identity(schema, runtime_identity)
        self.runtime_identity = runtime_identity
        self.dsn, self.schema = dsn, schema
        self._context_store = context_store
        self._scope_resolver = scope_resolver
        self._principal_provider = principal_provider
        self._key = signing_key

    def connect(self):
        if self.runtime_identity is not None:
            return connect_market(self.dsn, self.runtime_identity)
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _table(self):
        return sql.SQL("{}.market_hold_reports").format(sql.Identifier(self.schema))

    def _principal(self, tenant, scope):
        try:
            principal = self._principal_provider()
            scopes = principal.get("scopes") if isinstance(principal, dict) else None
            return bool(_name(tenant) and isinstance(principal, dict) and
                        principal.get("authenticated") is True and
                        principal.get("tenant_id") == tenant and
                        isinstance(scopes, (tuple, list, set, frozenset)) and
                        all(type(item) is str for item in scopes) and scope in scopes)
        except Exception:
            return False

    def tenant_is_authenticated(self, tenant):
        return self._principal(tenant, "market_hold_context_read")

    def _context(self, tenant, snapshot, context_id, *, conn=None):
        try:
            value = (self._context_store.get_decision_context(tenant, snapshot, context_id)
                     if conn is None else self._context_store._decision_context_in_transaction(
                         conn, tenant, snapshot, context_id))
        except Exception as exc:
            raise ValueError("trusted decision context unavailable") from exc
        _need(type(value) is dict and
              (value.get("tenant_id"), value.get("snapshot_id"),
               value.get("decision_context_id")) == (tenant, snapshot, context_id) and
              type(value.get("context_sha256")) is str and
              _DIGEST.fullmatch(value["context_sha256"]) is not None and
              value.get("claim_mode") in ("ex_ante", "ex_post_replay") and
              value.get("decision_time_kind") in ("actual", "hypothetical"),
              "trusted decision context mismatch")
        _time(value["decision_at_utc"])
        return value

    def _signature(self, raw):
        return hmac.new(self._key, _DOMAIN + raw, sha256).hexdigest()

    @staticmethod
    def _intent(context, scope):
        return _digest(_canonical({"report_version": "market-hold-v1",
            "context_sha256": context["context_sha256"], "scope": scope,
            "evaluation_status": "not_evaluated"}))

    def _verified(self, row, *, conn=None):
        _need(type(row["payload_raw"]) is bytes and
              _digest(row["payload_raw"]) == row["payload_sha256"] and
              hmac.compare_digest(self._signature(row["payload_raw"]), row["signature"]),
              "market hold integrity mismatch")
        try:
            payload = json.loads(row["payload_raw"])
            _need(_canonical(payload) == row["payload_raw"],
                  "market hold canonical bytes differ")
        except (ValueError, TypeError, UnicodeError) as exc:
            raise ValueError("market hold payload invalid") from exc
        _need(type(payload) is dict and set(payload) == _REPORT_KEYS and
              payload["report_version"] == "market-hold-v1" and
              payload["status"] == "hold" and
              payload["evaluation_status"] == "not_evaluated" and
              payload["review_at_utc"] is None and
              payload["reviewed_source_ids"] == [] and
              payload["rights"] == {"safe_summary": "allowed", "raw": "restricted"} and
              payload["reasons"] == ["market_g0_not_evaluated"] and
              payload["missing_evidence"] == list(_MISSING) and
              all(_name(payload[key]) for key in
                  ("tenant_id", "snapshot_id", "decision_context_id", "hold_report_id")) and
              type(payload["context_sha256"]) is str and
              _DIGEST.fullmatch(payload["context_sha256"]) is not None and
              (payload["tenant_id"], payload["snapshot_id"],
               payload["decision_context_id"], payload["hold_report_id"]) ==
              (row["tenant_id"], row["snapshot_id"],
               row["decision_context_id"], row["hold_report_id"]),
              "market hold report binding mismatch")
        _time(payload["evaluated_at_utc"])
        context = self._context(row["tenant_id"], row["snapshot_id"],
                                row["decision_context_id"], conn=conn)
        _need(all(payload[key] == context[key] for key in
                  ("decision_at_utc", "claim_mode", "decision_time_kind",
                   "context_sha256")), "market hold decision context changed")
        _scope(payload["scope"], row["tenant_id"], row["snapshot_id"],
               row["decision_context_id"])
        _need(self._intent(context, payload["scope"]) == row["intent_sha256"],
              "market hold creation intent changed")
        return payload

    def issue_not_evaluated(self, tenant, snapshot_id, context_id):
        _need(self._principal(tenant, "market_hold_issue"),
              "market hold issue authority denied")
        context = self._context(tenant, snapshot_id, context_id)
        try:
            scope = json.loads(_canonical(self._scope_resolver(
                tenant, snapshot_id, context_id)))
        except Exception as exc:
            raise ValueError("trusted market scope unavailable") from exc
        _scope(scope, tenant, snapshot_id, context_id)
        intent = self._intent(context, scope)
        payload = {"report_version": "market-hold-v1", "hold_report_id": str(uuid4()),
                   "tenant_id": tenant, "snapshot_id": snapshot_id,
                   "decision_context_id": context_id,
                   "context_sha256": context["context_sha256"],
                   "decision_at_utc": context["decision_at_utc"],
                   "claim_mode": context["claim_mode"],
                   "decision_time_kind": context["decision_time_kind"],
                   "evaluation_status": "not_evaluated", "status": "hold",
                   "evaluated_at_utc": datetime.now(timezone.utc).isoformat(
                       timespec="microseconds").replace("+00:00", "Z"),
                   "review_at_utc": None, "scope": scope,
                   "reasons": ["market_g0_not_evaluated"],
                   "missing_evidence": list(_MISSING), "reviewed_source_ids": [],
                   "rights": {"safe_summary": "allowed", "raw": "restricted"}}
        raw = _canonical(payload)
        _need(len(raw) <= 16384, "market hold report too large")
        with self.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, hold_report_id, snapshot_id,
                    decision_context_id, intent_sha256, payload_raw, payload_sha256, signature)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (tenant_id, intent_sha256) DO NOTHING
            """).format(self._table()),
                (tenant, payload["hold_report_id"], snapshot_id, context_id,
                 intent, raw, _digest(raw), self._signature(raw)))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND intent_sha256=%s
            """).format(self._table()), (tenant, intent)).fetchone()
        _need(row is not None, "market hold write was not committed")
        result = self._verified(row)
        _need(result["scope"] == scope, "market hold retry scope changed")
        return result

    def _report_row(self, conn, tenant, report_id):
        return conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id=%s AND hold_report_id=%s
        """).format(self._table()), (tenant, report_id)).fetchone()

    def _by_id(self, tenant, report_id, *, conn=None):
        if not _name(report_id):
            return None
        if conn is None:
            with self.connect() as owned:
                row = self._report_row(owned, tenant, report_id)
        else:
            row = self._report_row(conn, tenant, report_id)
        return self._verified(row, conn=conn) if row is not None else None

    def get_market_hold_report(self, report_id):
        return self._market_hold_report(report_id)

    def _market_hold_report(self, report_id, *, conn=None):
        try:
            principal = self._principal_provider()
            tenant = principal.get("tenant_id") if isinstance(principal, dict) else None
        except Exception:
            return None
        if not self._principal(tenant, "market_hold_context_read"):
            return None
        payload = self._by_id(tenant, report_id, conn=conn)
        if payload is None:
            return None
        try:
            current_scope = json.loads(_canonical(self._scope_resolver(
                tenant, payload["snapshot_id"], payload["decision_context_id"])))
            _scope(current_scope, tenant, payload["snapshot_id"],
                   payload["decision_context_id"])
        except Exception as exc:
            raise ValueError("trusted market scope unavailable") from exc
        _need(current_scope == payload["scope"],
              "market hold evaluation scope changed")
        return {"hold_report_id": payload["hold_report_id"],
                "tenant_id": payload["tenant_id"],
                "decision_at": _time(payload["decision_at_utc"]),
                "reasons": tuple(payload["reasons"]),
                "missing_evidence": tuple(payload["missing_evidence"]),
                "decision_context_id": payload["decision_context_id"],
                "snapshot_id": payload["snapshot_id"],
                "claim_mode": payload["claim_mode"],
                "decision_time_kind": payload["decision_time_kind"]}

    def get_decision_context(self, tenant, snapshot_id, context_id):
        return self._decision_context(tenant, snapshot_id, context_id)

    def _decision_context(self, tenant, snapshot_id, context_id, *, conn=None):
        if not self._principal(tenant, "market_hold_context_read"):
            return None
        return self._context(tenant, snapshot_id, context_id, conn=conn)

    def get_public_report(self, tenant, report_id):
        if not self._principal(tenant, "market_hold_read"):
            return None
        payload = self._by_id(tenant, report_id)
        if payload is None:
            return None
        return {"hold_report_id": payload["hold_report_id"], "status": "hold",
                "reasons": payload["reasons"],
                "missing_evidence": payload["missing_evidence"]}
