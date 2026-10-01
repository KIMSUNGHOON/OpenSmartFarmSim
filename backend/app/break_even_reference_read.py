"""Recheck stored replay references through actual stores on one audited connection."""

from .break_even_replay import BreakEvenReplayEvidence, ReplayRead, _MAX_READS, _value_hash
from .market_candidate_store import MarketCandidateStore
from .market_source_store import MarketSourceStore
from .runtime_roles import audit_runtime_roles


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
            elif method in ('get_market_candidate', 'get_economic_scenario', 'get_economic_scenario_pin'):
                value = _candidate_value(candidates, source, conn, tenant, method, args)
            elif method == 'get_economic_input':
                value = candidates._input_in_transaction(conn, tenant, *args)
                if value is None:
                    value = source._read_in_transaction(conn, tenant, 'economic_input', *args)
            elif method in _SOURCE:
                kind, pin = _SOURCE[method]
                source_args = args + ('single',) if method == 'get_prior_batch_cost' else args
                value = source._read_in_transaction(conn, tenant, kind, *source_args, pin=pin)
            else:
                value = getattr(store, method)(*args)
            if _value_hash(value) != item.value_sha256:
                raise ValueError('break-even replay dependency changed')
            check()
        audit_runtime_roles(conn, candidates.runtime_identity[0])
        check()
