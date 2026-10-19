"""Closed raw-row reads within an existing pure reference verification."""
from contextvars import ContextVar
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from psycopg import sql

from . import market_reference_bundle as bundles
from .market_source_store import _KINDS


MAX_KEYS = 128
MAX_BYTES = 1048576
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_active = ContextVar('market_reference_row_readset', default=None)
_SOURCE = ('tenant_id', 'kind', 'record_id', 'revision', 'job_id', 'payload_raw',
           'payload_sha256', 'store_version', 'admission_kind', 'admitted_by',
           'recorded_at', 'source_job_stage', 'source_job_input_bytes',
           'source_job_input_sha256')
_CANDIDATE = ('tenant_id', 'input_id', 'revision', 'payload_raw',
              'payload_sha256', 'recorded_at')


def _need(value):
    if not value:
        raise ValueError('current reference row readset unavailable')


def _keys(values, width):
    _need(type(values) is tuple and len(values) <= MAX_KEYS)
    for key in values:
        _need(type(key) is tuple and len(key) == width
              and all(type(v) is str and 1 <= len(v) <= 200
                      and v == v.strip() and all(ord(c) >= 32 for c in v) for v in key))
        if width == 3:
            _need(key[0] in _KINDS)
    _need(len(set(values)) == len(values))
    return values


class _Rows:
    def __init__(self, owner, tenant, source_keys, candidate_keys):
        from .market_candidate_store import MarketCandidateStore
        _need(type(owner) is MarketCandidateStore and type(tenant) is str
              and 1 <= len(tenant) <= 200)
        self.owner, self.tenant = owner, tenant
        self.keys = (_keys(source_keys, 3), _keys(candidate_keys, 2))
        _need(1 <= sum(map(len, self.keys)) <= MAX_KEYS and _active.get() is None)
        self.bundle = owner._reference_bundle.get()
        _need(type(self.bundle) is bundles._Bundle)
        self.reader = self.bundle.guard(owner, tenant)
        _need(self.reader is not None)
        self.conn = self.reader[0]
        self.source = owner._source._source
        self.binding = owner._shared_profile()
        _need(self.binding is not None)
        self.active, self.failed, self.token = True, False, None
        self.slot = _active
        self.rows = None
        self.fixed = self._pointers()

    def _pointers(self):
        methods = (self.owner._shared_profile, self.owner._shared_reader,
                   self.owner._reference_reader, self.owner._held_binding,
                   self.bundle.guard, self.bundle.check, self.source._checked_job_input,
                   self.source._table, self.owner._table, self._load, self._read,
                   self._check, self._guard)
        return (self.owner, self.tenant, self.keys, self.bundle, self.reader, self.conn,
                self.source, self.binding[:2], self.slot, _active, MAX_KEYS, MAX_BYTES, CODE_SHA256,
                _SOURCE, _CANDIDATE,
                tuple((getattr(m, '__self__', None), getattr(m, '__func__', m)) for m in methods))

    def _check(self):
        try:
            _need(self.active and not self.failed and self.slot is _active and self.slot.get() is self
                  and self.token is not None and (MAX_KEYS, MAX_BYTES) == (128, 1048576)
                  and self._pointers() == self.fixed
                  and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)
            self.slot.reset(self.token)
            self.token = self.slot.set(self)
            _need(self.owner._shared_profile(self.binding[:2]) is not None
                  and self.owner._source._source is self.source
                  and not self.conn.closed and self.owner._tenant('market_candidate_read') == self.tenant)
            self.bundle.check(self.owner, self.tenant)
        except Exception:
            self.failed = True
            raise

    def _guard(self):
        try:
            self._check()
            reader = self.bundle.guard(self.owner, self.tenant)
            _need(reader is not None and len(reader) == len(self.reader) == 2
                  and all(a is b for a, b in zip(reader, self.reader)))
        except Exception:
            self.failed = True
            raise

    def _load(self, index):
        keys = self.keys[index]
        if not keys:
            return {}, 0
        fields = _SOURCE if index == 0 else _CANDIDATE
        # Suppress oversized raw values in SQL before client allocation.
        projection = sql.SQL(',').join(sql.SQL('CASE WHEN budget.ok THEN m.{} END AS {}')
            .format(sql.Identifier(name), sql.Identifier(name)) for name in fields)
        if index == 0:
            matched = sql.SQL('''
                SELECT s.*, j.stage AS source_job_stage,
                    j.input_bytes AS source_job_input_bytes,
                    j.input_sha256 AS source_job_input_sha256,
                    pg_column_size(s)::bigint + octet_length(s.payload_raw)
                        + coalesce(octet_length(j.input_bytes),0) + coalesce(pg_column_size(j.stage),0)
                        + coalesce(pg_column_size(j.input_sha256),0) AS bytes
                FROM {} s JOIN unnest(%s::text[],%s::text[],%s::text[])
                    k(kind,record_id,revision) USING(kind,record_id,revision)
                    LEFT JOIN {} j ON j.tenant_id=s.tenant_id AND j.job_id=s.job_id
                WHERE s.tenant_id=%s
            ''').format(self.source._table('market_source_records'), self.source._table('jobs'))
        else:
            matched = sql.SQL('''
                SELECT s.*, pg_column_size(s)::bigint + octet_length(s.payload_raw) AS bytes
                FROM {} s JOIN unnest(%s::text[],%s::text[]) k(input_id,revision)
                    USING(input_id,revision) WHERE s.tenant_id=%s
            ''').format(self.owner._table('market_candidate_inputs'))
        query = sql.SQL('''
            WITH m AS MATERIALIZED ({}),
            budget AS (SELECT coalesce(sum(bytes),0)<=%s AS ok FROM m)
            SELECT {}, m.bytes, budget.ok FROM m CROSS JOIN budget
        ''').format(matched, projection)
        params = (*([k[i] for k in keys] for i in range(len(keys[0]))), self.tenant, MAX_BYTES)
        values = self.conn.execute(query, params).fetchall()
        _need(len(values) <= len(keys))
        result, total = {}, 0
        for row in values:
            _need(row.pop('ok') is True)
            size = row.pop('bytes')
            _need(type(size) is int and 0 < size <= MAX_BYTES)
            total += size
            _need(total <= MAX_BYTES and row['tenant_id'] == self.tenant)
            key = tuple(row[k] for k in (('kind', 'record_id', 'revision')
                                         if index == 0 else ('input_id', 'revision')))
            _need(key in keys and key not in result)
            raw = row['payload_raw']
            _need(type(raw) is bytes and 1 <= len(raw) <= (65536 if index == 0 else 16384)
                  and sha256(raw).hexdigest() == row['payload_sha256'])
            if index == 0:
                job = {'stage': row['source_job_stage'], 'input_bytes': row['source_job_input_bytes'],
                       'input_sha256': row['source_job_input_sha256']}
                _need(self.source._checked_job_input(job) == raw)
            result[key] = row
        return {key: result.get(key) for key in keys}, total

    def _read(self):
        self._guard()
        source, a = self._load(0)
        candidates, b = self._load(1)
        _need(a + b <= MAX_BYTES)
        self._guard()
        return source, candidates

    def source_row(self, conn, tenant, kind, identity, revision):
        return self._row(0, conn, tenant, (kind, identity, revision))

    def candidate_row(self, conn, tenant, identity, revision):
        return self._row(1, conn, tenant, (identity, revision))

    def _row(self, index, conn, tenant, key):
        try:
            self._check()
            _need(conn is self.conn and tenant == self.tenant and self.rows is not None
                  and key in self.rows[index])
            return deepcopy(self.rows[index][key])
        except Exception:
            self.failed = True
            raise

    def _close(self):
        self.active = False
        self.rows = self.reader = self.conn = None
        self.fixed = None
        if self.token is not None:
            self.slot.reset(self.token)
            self.token = None


def verify_rows(owner, tenant, source_keys, candidate_keys, consume):
    """Return None only after the owned callback and fresh post-read comparison."""
    existing = _active.get()
    if existing is not None:
        existing.failed = True
        raise ValueError('nested current reference row readset unavailable')
    _need(callable(consume))
    rows = _Rows(owner, tenant, source_keys, candidate_keys)
    rows.token = _active.set(rows)
    try:
        rows.rows = rows._read()
        _need(consume(rows) is None)
        _need(rows._read() == rows.rows)
    finally:
        rows._close()
