"""One registration-owned connection across separate, freshly audited transactions."""
from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
from pathlib import Path

import psycopg
from psycopg.pq import TransactionStatus


_CURRENT = ContextVar('registration_connections', default=None)
_REQUEST = ContextVar('registration_connection_request', default=None)
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class ConnectionScopeHold(ValueError):
    pass


def _need(value):
    if not value:
        raise ConnectionScopeHold('registration connection scope unavailable')


def _profile(owner):
    from .job_store import JobStore
    from .market_source_store import MarketSourceStore
    from .thermal_run_store import ThermalRunStore
    jobs = owner.replay.jobs
    source = getattr(getattr(owner.replay.candidates, '_source', None), '_source', None)
    runs = owner.replay.thermal.runs
    stores = jobs, source, runs
    if (tuple(map(type, stores)) != (JobStore, MarketSourceStore, ThermalRunStore)
            or jobs.audit_runtime_grants is not True or jobs.runtime_identity is None):
        return None
    policy, kind = jobs.runtime_identity
    values = []
    for store, dsn, provider in ((jobs, jobs._dsn, jobs.principal_provider),
            (source, source.dsn, source._principal_provider),
            (runs, runs.dsn, runs._principal_provider)):
        identity = store.runtime_identity
        method = store.connect
        if (type(identity) is not tuple or len(identity) != 2 or identity[0] is not policy
                or identity[1] != kind or kind != 'authority' or dsn != jobs._dsn
                or store.schema != jobs.schema or provider is not jobs.principal_provider
                or getattr(method, '__self__', None) is not store
                or getattr(method, '__func__', None) is not type(store).connect
                or method.__func__.__module__ != type(store).__module__):
            return None
        values.append((store, dsn, store.schema, identity, provider, method.__func__, method.__func__.__code__))
    return stores, tuple(values), tuple(vars(policy).items()), jobs.audit_runtime_grants


def _client(conn):
    from datetime import date, datetime
    from decimal import Decimal
    from uuid import UUID
    from psycopg.adapt import PyFormat
    from psycopg.types.json import Jsonb
    loaders = tuple(conn.adapters.get_loader(oid, format) for oid in
        (16, 17, 20, 21, 23, 25, 26, 114, 700, 701, 1043, 1082, 1114, 1184, 1700, 2950, 3802)
        for format in (0, 1))
    dumpers = tuple(conn.adapters.get_dumper(kind, PyFormat.AUTO) for kind in
        (str, bytes, int, float, bool, Decimal, date, datetime, UUID, Jsonb))
    parameters = conn.info.get_parameters()
    return (conn.row_factory, conn.autocommit, conn.isolation_level, conn.read_only,
            conn.deferrable, conn.prepare_threshold, conn.prepared_max, loaders, dumpers,
            tuple((key, parameters.get(key)) for key in
                  ('host', 'hostaddr', 'port', 'dbname', 'user', 'options', 'require_auth')))


def _session(conn):
    return conn.execute("SELECT current_setting('default_transaction_isolation') AS isolation, "
        "current_setting('default_transaction_read_only') AS readonly, "
        "current_setting('default_transaction_deferrable') AS deferrable, "
        "current_setting('statement_timeout') AS timeout, current_setting('lock_timeout') AS lock_timeout, "
        "current_setting('search_path') AS search_path, current_setting('role') AS role, "
        "current_setting('row_security') AS row_security, pg_my_temp_schema() AS temp_schema, "
        "current_setting('TimeZone') AS timezone, current_setting('DateStyle') AS datestyle, "
        "current_setting('IntervalStyle') AS intervalstyle, current_setting('extra_float_digits') AS float_digits, "
        "current_setting('client_encoding') AS encoding, "
        "current_setting('standard_conforming_strings') AS strings, current_setting('bytea_output') AS bytea_output").fetchone()


def state():
    functions = (registration_connections, registration_connections.__wrapped__, read_connection,
        read_connection.__wrapped__, factory_connection, verify_owned_session, _profile, _client,
        _session, _need, _Frame.__init__, _Frame.check, _Frame.close)
    return (_CURRENT, _REQUEST, CODE_SHA256,
            tuple((fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__) for fn in functions))


class _Frame:
    def __init__(self, owner, witness, profile):
        self.owner, self.witness, self.profile = owner, witness, profile
        self.conn = self.factory_args = self.client = self.session = None
        self.busy = self.failed = self.closed = False
        self.token = None
        self.state = state()

    def check(self):
        try:
            from .farm_registration_read_scope import _execution
            _need(not self.closed and not self.failed and _CURRENT.get() is self
                  and self.witness.active and not self.witness.failed
                  and self.witness.execution == _execution()
                  and self.owner._registration_read is self.witness.slot
                  and self.witness.slot.get() is self.witness
                  and state() == self.state
                  and _profile(self.owner) == self.profile
                  and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)
            _CURRENT.reset(self.token)
            self.token = _CURRENT.set(self)
            self.owner._guard(self.witness.args[0], self.witness.pointers, self.witness.scopes)
        except BaseException:
            self.failed = True
            if self.witness is not None:
                self.witness.failed = True
            raise

    def close(self):
        self.closed = True
        try:
            if self.conn is not None:
                self.conn.close()
        finally:
            self.conn = self.factory_args = self.client = self.session = None
            self.owner = self.witness = self.profile = None
            self.state = None


@contextmanager
def registration_connections(owner, witness):
    existing = _CURRENT.get()
    if existing is not None:
        existing.failed = True
        existing.witness.failed = True
        raise ConnectionScopeHold('nested registration connections unavailable')
    profile = _profile(owner)
    if profile is None:
        yield None
        return
    frame = _Frame(owner, witness, profile)
    frame.token = _CURRENT.set(frame)
    try:
        frame.check()
        yield frame
        if not witness.failed:
            frame.check()
    finally:
        try:
            _CURRENT.reset(frame.token)
        finally:
            frame.token = None
            frame.close()


def factory_connection(dsn, policy, kind, **kwargs):
    request = _REQUEST.get()
    if request is None:
        return psycopg.connect(dsn, **kwargs)
    frame, store, claimed = request
    frame.check()
    _need(not claimed and store in frame.profile[0] and frame.busy
          and policy is frame.profile[1][0][3][0] and kind == 'authority')
    request[2] = True
    arguments = dsn, tuple(kwargs.items())
    if frame.conn is None:
        frame.conn = psycopg.connect(dsn, **kwargs)
        frame.factory_args = arguments
        _need(type(frame.conn) is psycopg.Connection and not frame.conn.autocommit)
        frame.client = _client(frame.conn)
    else:
        _need(arguments == frame.factory_args and not frame.conn.closed
              and frame.conn.info.transaction_status == TransactionStatus.IDLE
              and _client(frame.conn) == frame.client)
    return frame.conn


def verify_owned_session(conn):
    request = _REQUEST.get()
    if request is None:
        return
    frame = request[0]
    frame.check()
    _need(conn is frame.conn and _client(conn) == frame.client)
    state = _session(conn)
    if frame.session is None:
        frame.session = state
    else:
        _need(state == frame.session)


@contextmanager
def read_connection(store):
    frame = _CURRENT.get()
    if frame is None:
        with store.connect() as conn:
            yield conn
        return
    frame.check()
    if store not in frame.profile[0] or frame.busy:
        try:
            with store.connect() as conn:
                yield conn
            frame.check()
        except BaseException:
            frame.failed = frame.witness.failed = True
            raise
        return
    frame.busy = True
    request = [frame, store, False]
    token = _REQUEST.set(request)
    conn = None
    try:
        try:
            conn = store.connect()
            _need(request[2] and conn is frame.conn)
        finally:
            _REQUEST.reset(token)
        yield conn
        frame.check()
        _need(_client(conn) == frame.client and _session(conn) == frame.session)
        conn.commit()
        _need(conn.info.transaction_status == TransactionStatus.IDLE)
    except BaseException:
        frame.failed = True
        frame.witness.failed = True
        if conn is not None and not conn.closed:
            try:
                conn.rollback()
            except Exception:
                pass
            finally:
                conn.close()
        raise
    finally:
        frame.busy = False
