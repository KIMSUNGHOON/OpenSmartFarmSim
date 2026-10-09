"""Recheck stored replay references through actual stores on one audited connection."""

from contextlib import contextmanager

from psycopg import sql

from .break_even_replay import BreakEvenReplayEvidence, ReplayRead, _MAX_READS, _value_hash
from .break_even_store import BreakEvenStore, _READ_METHODS
from .market_candidate_store import MarketCandidateStore
from .market_hold_store import MarketHoldStore
from .market_source_store import MarketSourceStore, _name
from .runtime_roles import RolePolicyHold, audit_runtime_roles
from .thermal_run_store import ThermalRunStore


_SOURCE = {
    'get_joint_shock': ('joint_shock', False),
    'get_joint_shock_pin': ('joint_shock', True),
    'get_input_rights': ('input_rights', False),
    'get_settlement_applicability': ('settlement_applicability', False),
    'get_settlement_evidence': ('settlement_evidence', False),
    'get_prior_batch_cost': ('prior_batch_cost', False),
}


def _candidate_value(candidates, source, conn, tenant, method, args):
    value = candidates._candidate_in_transaction(conn, tenant, *args)
    if value is None:
        if method == 'get_market_candidate':
            return None
        return source._read_in_transaction(conn, tenant, 'economic_scenario', *args,
            pin=method == 'get_economic_scenario_pin')
    record, scenario = value
    if method == 'get_market_candidate':
        return record
    if method == 'get_economic_scenario':
        return scenario
    return {'tenant_id': scenario['tenant_id'], 'scenario_id': args[0],
        'scenario_revision': args[1], 'decision_at': scenario['decision_at'],
        'payload_sha256': record['economic_scenario_sha256'],
        'immutable_job_input_ref': record['immutable_job_input_ref'],
        'immutable_job_input_sha256': record['immutable_job_input_sha256'], 'immutable': True}


def _input_value(candidates, source, conn, tenant, input_id, revision):
    if (candidates._tenant('market_candidate_read') != tenant or
            source._tenant('market_source_read') != tenant or
            not _name(input_id) or not _name(revision)):
        return None
    row = conn.execute(sql.SQL('''
        WITH candidate AS (
            SELECT tenant_id,input_id,revision,payload_raw,payload_sha256
            FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s
        )
        SELECT 'candidate' AS read_kind, tenant_id, input_id AS record_id,
            revision,payload_raw,payload_sha256,NULL AS job_id,NULL AS store_version,
            NULL AS admission_kind,NULL AS admitted_by,NULL AS source_job_stage,
            NULL AS source_job_input_bytes,NULL AS source_job_input_sha256
        FROM candidate
        UNION ALL
        SELECT 'source',source.tenant_id,source.record_id,source.revision,
            source.payload_raw,source.payload_sha256,source.job_id,source.store_version,
            source.admission_kind,source.admitted_by,job.stage,job.input_bytes,job.input_sha256
        FROM {} AS source LEFT JOIN {} AS job
            ON job.tenant_id=source.tenant_id AND job.job_id=source.job_id
        WHERE source.tenant_id=%s AND source.kind='economic_input'
            AND source.record_id=%s AND source.revision=%s
            AND NOT EXISTS (SELECT 1 FROM candidate)
    ''').format(candidates._table('market_candidate_inputs'),
        source._table('market_source_records'), source._table('jobs')),
        (tenant, input_id, revision, tenant, input_id, revision)).fetchone()
    if row is None:
        return None
    if row['read_kind'] == 'candidate':
        return candidates._checked_input({'tenant_id': row['tenant_id'],
            'input_id': row['record_id'], 'revision': row['revision'],
            'payload_raw': row['payload_raw'], 'payload_sha256': row['payload_sha256']})
    row['kind'] = 'economic_input'
    job_row = {'stage': row['source_job_stage'], 'input_bytes': row['source_job_input_bytes'],
        'input_sha256': row['source_job_input_sha256']}
    return source._verified(conn, row, job_row=job_row).model_dump(mode='python')


def _reference_value(store, candidates, source, conn, tenant, method, args):
    if method in ('get_market_candidate', 'get_economic_scenario', 'get_economic_scenario_pin'):
        return _candidate_value(candidates, source, conn, tenant, method, args)
    if method == 'get_economic_input':
        return _input_value(candidates, source, conn, tenant, *args)
    if method in _SOURCE:
        kind, pin = _SOURCE[method]
        source_args = args + ('single',) if method == 'get_prior_batch_cost' else args
        return source._read_in_transaction(conn, tenant, kind, *source_args, pin=pin)
    if method in ('get_market_hold_report', 'get_decision_context'):
        holds = candidates._source._holds
        contexts = holds._context_store
        if (type(holds) is not MarketHoldStore or type(contexts) is not ThermalRunStore or
                any(value.runtime_identity != candidates.runtime_identity or
                    value.schema != candidates.schema or value.dsn != candidates.dsn or
                    value._principal_provider is not candidates._principal_provider
                    for value in (holds, contexts))):
            raise RuntimeError('break-even reference stores rejected')
        if method == 'get_market_hold_report':
            return holds._market_hold_report(*args, conn=conn)
        return holds._decision_context(*args, conn=conn)
    return getattr(store, method)(*args)


class _MarketReferences:
    def __init__(self, store, candidates, source, conn, tenant, check):
        self._store, self._candidates, self._source = store, candidates, source
        self._conn, self._tenant, self._check = conn, tenant, check
        self._open = True

    def _guard(self):
        if not self._open:
            raise ValueError('break-even reference read window closed')
        self._check()
        if (self._store._tenant('break_even_read') != self._tenant or
                self._candidates._tenant('market_candidate_read') != self._tenant or
                self._source._tenant('market_source_read') != self._tenant):
            raise PermissionError('break-even reference access denied')

    def tenant_is_authenticated(self, tenant):
        self._guard()
        return tenant == self._tenant and self._candidates.tenant_is_authenticated(tenant) is True

    def __getattr__(self, method):
        if method not in _READ_METHODS:
            raise AttributeError(method)
        def read(*args):
            self._guard()
            value = _reference_value(self._store, self._candidates, self._source,
                self._conn, self._tenant, method, args)
            self._guard()
            return value
        return read


@contextmanager
def current_market_references(store, tenant, *, check):
    if type(store) is not BreakEvenStore or not callable(check):
        raise ValueError('break-even reference stores rejected')
    check()
    candidates = store._source
    source = candidates._source._source
    if type(candidates) is not MarketCandidateStore or type(source) is not MarketSourceStore:
        raise ValueError('break-even reference stores rejected')
    try:
        with candidates.connect() as conn:
            references = _MarketReferences(store, candidates, source, conn, tenant, check)
            try:
                references._guard()
                yield references
                references._guard()
                audit_runtime_roles(conn, candidates.runtime_identity[0])
                references._guard()
            finally:
                try:
                    references._guard()
                finally:
                    references._open = False
    except RolePolicyHold:
        raise RuntimeError('break-even source unavailable') from None


def recheck_replay_dependencies(store, evidence, *, check):
    if type(evidence) is not BreakEvenReplayEvidence or not callable(check):
        raise ValueError('break-even replay dependency check rejected')
    recheck_replay_reads(store, evidence.tenant_id, evidence.reads, check=check)


def recheck_replay_reads(store, tenant, reads, *, check, plan_row=None):
    if (not callable(check) or type(reads) is not tuple or not 1 <= len(reads) <= _MAX_READS
            or any(type(item) is not ReplayRead for item in reads)
            or [(item.method, item.args) for item in reads] != sorted(set((item.method, item.args) for item in reads))):
        raise ValueError('break-even replay observations rejected')
    candidates = store._source
    source = candidates._source._source
    if type(candidates) is not MarketCandidateStore or type(source) is not MarketSourceStore:
        raise ValueError('break-even replay dependency stores rejected')
    plan_value = None
    if plan_row is not None:
        _, plan, _ = store._checked(plan_row)
        if plan.tenant_id != tenant:
            raise ValueError('break-even replay plan tenant differs')
        plan_value = plan.model_dump(mode='json')
    check()
    with candidates.connect() as conn:
        for item in reads:
            check()
            if (store._tenant('break_even_read') != tenant or
                    candidates._tenant('market_candidate_read') != tenant or
                    source._tenant('market_source_read') != tenant):
                raise PermissionError('break-even replay dependency access denied')
            method, args = item.method, item.args
            if method == 'get_break_even_plan' and plan_value is not None:
                if args != (plan_value['plan_id'],):
                    raise ValueError('break-even replay plan identity differs')
                value = plan_value
            else:
                value = _reference_value(store, candidates, source, conn, tenant, method, args)
            if _value_hash(value) != item.value_sha256:
                raise ValueError('break-even replay dependency changed')
            check()
        audit_runtime_roles(conn, candidates.runtime_identity[0])
        check()
