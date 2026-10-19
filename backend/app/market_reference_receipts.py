"""Bounded current raw dependency fingerprints, without permission caching."""
from contextvars import ContextVar
from hashlib import sha256
from pathlib import Path

from psycopg import sql

from . import market_reference_bundle as bundles
from . import market_reference_row_readset as rows


MAX_KEYS = 128
MAX_BYTES = 1048576
VERSION = 'market-reference-receipts-v1/pg16/jsonb-array/epoch/raw-sha256'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_active = ContextVar('market_reference_receipts', default=None)
# Fixed catalog descriptors: name, built-in type OID, typmod, NOT NULL.
_TEXT, _HASH, _RAW, _TIME = (25, -1, True), (1042, 68, True), (17, -1, True), (1184, -1, True)
_SCHEMA = (
    ('market_source_records', (('tenant_id', *_TEXT), ('kind', *_TEXT), ('record_id', *_TEXT),
        ('revision', *_TEXT), ('job_id', 2950, -1, True), ('payload_raw', *_RAW),
        ('payload_sha256', *_HASH), ('store_version', *_TEXT), ('admission_kind', *_TEXT),
        ('admitted_by', *_TEXT), ('recorded_at', *_TIME))),
    ('market_candidate_inputs', (('tenant_id', *_TEXT), ('input_id', *_TEXT),
        ('revision', *_TEXT), ('payload_raw', *_RAW), ('payload_sha256', *_HASH), ('recorded_at', *_TIME))),
    ('market_candidate_pins', (('tenant_id', *_TEXT), ('candidate_id', *_HASH),
        ('scenario_id', *_TEXT), ('revision', *_TEXT), ('record_raw', *_RAW),
        ('record_sha256', *_HASH), ('scenario_raw', *_RAW), ('scenario_sha256', *_HASH),
        ('inputs_manifest_raw', *_RAW), ('inputs_manifest_sha256', *_HASH), ('recorded_at', *_TIME))),
    ('jobs', (('tenant_id', *_TEXT), ('job_id', 2950, -1, True), ('stage', *_TEXT),
        ('input_sha256', *_HASH), ('input_bytes', *_RAW), ('idempotency_key', *_TEXT),
        ('state', *_TEXT), ('attempt_count', 23, -1, True), ('max_attempts', 23, -1, True),
        ('next_attempt_at', *_TIME), ('cancel_requested', 16, -1, True),
        ('lease_token', 25, -1, False), ('lease_until', 1184, -1, False),
        ('reason', 3802, -1, False), ('created_at', *_TIME), ('updated_at', *_TIME))),
)


def _need(value):
    if not value:
        raise ValueError('current raw dependency receipts unavailable')


class _Receipts:
    def __init__(self, owner, tenant, source_keys, candidate_keys, pin_keys):
        from .market_candidate_store import MarketCandidateStore
        _need(type(owner) is MarketCandidateStore and type(tenant) is str and 1 <= len(tenant) <= 200)
        self.owner, self.tenant = owner, tenant
        self.keys = (rows._keys(source_keys, 3), rows._keys(candidate_keys, 2), rows._keys(pin_keys, 2))
        _need(1 <= sum(map(len, self.keys)) <= MAX_KEYS)
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
        self.receipts = self.catalog = None
        self.fixed = self._pointers()

    def _pointers(self):
        methods = (self.owner._shared_profile, self.owner._shared_reader, self.owner._reference_reader,
                   self.owner._held_binding, self.owner._table, self.source._table,
                   self.bundle.check, self.bundle.guard, self._check, self._guard,
                   self._catalog, self._read, self._receipt, self._close, rows._keys, _query)
        return (self.owner, self.tenant, self.keys, self.bundle, self.reader, self.conn, self.source,
                self.binding[:2], self.slot, _active, MAX_KEYS, MAX_BYTES, VERSION, CODE_SHA256, _SCHEMA,
                tuple((getattr(m, '__self__', None), getattr(m, '__func__', m)) for m in methods))

    def _check(self):
        try:
            _need(self.active and not self.failed and self.slot is _active and self.slot.get() is self
                  and self.token is not None and (MAX_KEYS, MAX_BYTES) == (128, 1048576)
                  and self._pointers() == self.fixed
                  and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
                  and sha256(Path(rows.__file__).read_bytes()).hexdigest() == rows.CODE_SHA256)
            self.slot.reset(self.token)
            self.token = self.slot.set(self)
            _need(self.owner._shared_profile(self.binding[:2]) is not None
                  and self.owner._source._source is self.source and not self.conn.closed
                  and self.owner._tenant('market_candidate_read') == self.tenant)
            self.bundle.check(self.owner, self.tenant)
        except Exception:
            self.failed = True
            raise

    def _guard(self):
        self._check()
        try:
            current = self.bundle.guard(self.owner, self.tenant)
            _need(current is not None and len(current) == len(self.reader) == 2
                  and all(a is b for a, b in zip(current, self.reader)))
        except Exception:
            self.failed = True
            raise

    def _catalog(self):
        values = self.conn.execute('''
            SELECT c.relname,c.oid,c.relkind,c.relrowsecurity,a.attname,a.atttypid,
                a.atttypmod,a.attnotnull,a.attgenerated,a.attidentity,
                current_setting('server_version_num') AS producer,
                current_setting('server_encoding') AS encoding
            FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid
            WHERE n.nspname=%s AND c.relname=ANY(%s) AND a.attnum>0 AND NOT a.attisdropped
            ORDER BY c.relname,a.attnum
        ''', (self.owner.schema, [name for name, _ in _SCHEMA])).fetchall()
        observed = {name: [] for name, _ in _SCHEMA}
        descriptors = []
        for row in values:
            _need(row['relkind'] == 'r' and not row['relrowsecurity']
                  and row['attgenerated'] == row['attidentity'] == ''
                  and row['encoding'] == 'UTF8' and 160000 <= int(row['producer']) < 170000)
            observed[row['relname']].append(tuple(row[k] for k in ('attname','atttypid','atttypmod','attnotnull')))
            descriptors.append(tuple(row.values()))
        _need(all(tuple(observed[name]) == fields for name, fields in _SCHEMA))
        return int(values[0]['producer']), tuple(descriptors)

    def _read(self):
        self._guard()
        catalog = self._catalog()
        if self.catalog is None:
            self.catalog = catalog
        _need(catalog == self.catalog)
        domain = (VERSION + '\0' + str(catalog[0]) + '\0').encode()
        params = (MAX_BYTES, domain, self.tenant,
                  *([key[i] for key in self.keys[0]] for i in range(3)),
                  *([key[i] for key in self.keys[1]] for i in range(2)),
                  *([key[i] for key in self.keys[2]] for i in range(2)))
        values = self.conn.execute(_query(self), params).fetchall()
        _need(len(values) <= sum(map(len, self.keys)))
        result, seen, total = tuple({k: None for k in keys} for keys in self.keys), set(), 0
        for value in values:
            category = value['category']
            _need(type(category) is int and 0 <= category <= 2 and value['ok'] is True)
            key = ((value['kind'], value['identity'], value['revision']) if category == 0
                   else (value['identity'], value['revision']))
            size, receipt = value['bytes'], value['receipt']
            _need(key in result[category] and (category, key) not in seen
                  and type(size) is int and 0 < size <= MAX_BYTES
                  and type(receipt) is bytes and len(receipt) == 32)
            seen.add((category, key));total += size
            _need(total <= MAX_BYTES)
            result[category][key] = receipt
        _need(self._catalog() == catalog)
        self._guard()
        return result

    def source_receipt(self, conn, tenant, kind, identity, revision):
        return self._receipt(0, conn, tenant, (kind, identity, revision))

    def candidate_receipt(self, conn, tenant, identity, revision):
        return self._receipt(1, conn, tenant, (identity, revision))

    def pin_receipt(self, conn, tenant, identity, revision):
        return self._receipt(2, conn, tenant, (identity, revision))

    def _receipt(self, category, conn, tenant, key):
        try:
            self._check()
            _need(conn is self.conn and tenant == self.tenant and self.receipts is not None
                  and key in self.receipts[category])
            return self.receipts[category][key]
        except Exception:
            self.failed = True
            raise

    def _close(self):
        self.active = False
        self.receipts = self.catalog = self.reader = self.conn = self.fixed = None
        if self.token is not None:
            self.slot.reset(self.token)
            self.token = None


def _query(reader):
    source = reader.source._table('market_source_records')
    jobs = reader.source._table('jobs')
    candidate = reader.owner._table('market_candidate_inputs')
    pin = reader.owner._table('market_candidate_pins')
    return sql.SQL('''
        WITH settings AS (SELECT %s::bigint AS cap,%s::bytea AS domain,%s::text AS tenant),
        receipt_keys AS MATERIALIZED (
            SELECT 0 AS category,s.kind,s.record_id AS identity,s.revision,
                pg_column_size(s)::bigint+octet_length(s.payload_raw)
                    +coalesce(octet_length(j.input_bytes),0)+coalesce(pg_column_size(j.stage),0)
                    +coalesce(pg_column_size(j.input_sha256),0) AS bytes
            FROM {source} s JOIN unnest(%s::text[],%s::text[],%s::text[])
                k(kind,record_id,revision) USING(kind,record_id,revision)
                LEFT JOIN {jobs} j ON j.tenant_id=s.tenant_id AND j.job_id=s.job_id WHERE s.tenant_id=(SELECT tenant FROM settings)
            UNION ALL
            SELECT 1,NULL,s.input_id,s.revision,pg_column_size(s)::bigint+octet_length(s.payload_raw)
            FROM {candidate} s JOIN unnest(%s::text[],%s::text[]) k(input_id,revision)
                USING(input_id,revision) WHERE s.tenant_id=(SELECT tenant FROM settings)
            UNION ALL
            SELECT 2,NULL,s.scenario_id,s.revision,pg_column_size(s)::bigint+octet_length(s.record_raw)
                +octet_length(s.scenario_raw)+octet_length(s.inputs_manifest_raw)
            FROM {pin} s JOIN unnest(%s::text[],%s::text[]) k(scenario_id,revision)
                USING(scenario_id,revision) WHERE s.tenant_id=(SELECT tenant FROM settings)
        ), budget AS (SELECT coalesce(sum(bytes),0)<=(SELECT cap FROM settings) AS ok FROM receipt_keys)
        SELECT k.*,b.ok,CASE WHEN b.ok THEN sha256((SELECT domain FROM settings)||
            sha256(convert_to(jsonb_build_array(0,s.tenant_id,s.kind,s.record_id,s.revision,s.job_id,
                s.payload_sha256,s.store_version,s.admission_kind,s.admitted_by,extract(epoch from s.recorded_at),
                j.stage,j.input_sha256,j.input_bytes IS NULL)::text,'UTF8'))||sha256(s.payload_raw)||
            sha256(coalesce(j.input_bytes,''::bytea))) END AS receipt
        FROM receipt_keys k JOIN {source} s ON k.category=0 AND s.kind=k.kind
            AND s.record_id=k.identity AND s.revision=k.revision AND s.tenant_id=(SELECT tenant FROM settings)
            LEFT JOIN {jobs} j ON j.tenant_id=s.tenant_id AND j.job_id=s.job_id CROSS JOIN budget b
        UNION ALL
        SELECT k.*,b.ok,CASE WHEN b.ok THEN sha256((SELECT domain FROM settings)||
            sha256(convert_to(jsonb_build_array(1,s.tenant_id,s.input_id,s.revision,s.payload_sha256,
                extract(epoch from s.recorded_at))::text,'UTF8'))||sha256(s.payload_raw)) END
        FROM receipt_keys k JOIN {candidate} s ON k.category=1 AND s.input_id=k.identity
            AND s.revision=k.revision AND s.tenant_id=(SELECT tenant FROM settings) CROSS JOIN budget b
        UNION ALL
        SELECT k.*,b.ok,CASE WHEN b.ok THEN sha256((SELECT domain FROM settings)||
            sha256(convert_to(jsonb_build_array(2,s.tenant_id,s.candidate_id,s.scenario_id,s.revision,
                s.record_sha256,s.scenario_sha256,s.inputs_manifest_sha256,extract(epoch from s.recorded_at))::text,'UTF8'))||
            sha256(s.record_raw)||sha256(s.scenario_raw)||sha256(s.inputs_manifest_raw)) END
        FROM receipt_keys k JOIN {pin} s ON k.category=2 AND s.scenario_id=k.identity
            AND s.revision=k.revision AND s.tenant_id=(SELECT tenant FROM settings) CROSS JOIN budget b
    ''').format(source=source,jobs=jobs,candidate=candidate,pin=pin)


def verify_receipts(owner, tenant, source_keys, candidate_keys, pin_keys, consume):
    """Finish only after fresh exact dependency receipts agree around the callback."""
    existing = _active.get()
    if existing is not None:
        existing.failed = True
        raise ValueError('nested current raw dependency receipts unavailable')
    _need(callable(consume))
    reader = _Receipts(owner, tenant, source_keys, candidate_keys, pin_keys)
    reader.token = _active.set(reader)
    try:
        reader.receipts = reader._read()
        _need(consume(reader) is None)
        _need(reader._read() == reader.receipts)
    finally:
        reader._close()
