"""Fresh SCRAM verifier; production modules only, no seed/pytest/HTTP app imports."""
from copy import deepcopy
from hashlib import sha256
import hmac
import importlib
import inspect
import json
from pathlib import Path
import sys

from psycopg import sql

from app import crop_morphology_farm_binding as model
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.thermal_scenario_store import ThermalScenarioStore
from app.api_market_source import _MarketSources
from app.research_registry import ResearchRegistry
from app.owned_research import OwnedResearchService
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.farm_replay_scenario import FarmReplayScenarioService
from app.farm_authoring_storage import FarmAuthoringService


def context_verifier(raw, signature):
    expected = hmac.new(b'synthetic-market-context-key-32bytes', b'decision-context-v1\0'+raw, sha256).hexdigest()
    if not hmac.compare_digest(signature, expected): return None
    value = json.loads(raw)
    return {k: value[k] for k in ('authority_id', 'planning_event_sha256', 'decision_at_utc', 'decision_time_kind')}


class Rights:
    policy_version = 'owned-morphology-input-rights-test-v1'

    def __call__(self, tenant, declaration, source, use):
        return tenant == 'tenant-1' and declaration['schema_version'] == model.RIGHTS_VERSION \
            and declaration['input_source_sha256'] == source and use in ('research_calculation', 'research_display')


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(t))).fetchone()['n']
            for t in ('jobs', 'job_events', 'crop_cycle_research_results', 'thermal_g1_runs'))


def main():
    p = json.loads(Path(sys.argv[1]).read_bytes()); policy = RuntimeLoginPolicy(**p['policy']); identity = (policy, 'authority')
    principal = p['principal']; principal['scopes'] = set(principal['scopes']); provider = lambda: principal
    kw = {'runtime_identity': identity, 'principal_provider': provider}; dsn = p['dsn']; schema = policy.schema
    jobs = JobStore(dsn, schema, Path(p['artifacts']), audit_runtime_grants=True, **kw)
    sources = MarketSourceStore(dsn, schema, **kw)
    runs = ThermalRunStore(dsn, schema, gate_key=b'synthetic-gate-key-32-bytes-long!', release_verifier=lambda *_: None,
        context_verifier=context_verifier, **kw)
    holds = MarketHoldStore(dsn, schema, context_store=runs, scope_resolver=lambda *_: dict(p['scope']),
        signing_key=b'synthetic-market-hold-key-32bytes!!', **kw)
    view = _MarketSources(sources, holds, principal_provider=provider); candidates = MarketCandidateStore(dsn, schema, view, **kw)
    registry = ResearchRegistry(p['registry_raw'].encode(), p['registry_sha256'])
    owned = OwnedResearchService(jobs, runs, registry, OwnedFixtureRegistry(Path(p['root'])), {next(iter(registry._scopes)): 'context-1'})
    replay = FarmReplayScenarioService(jobs, ThermalScenarioStore(runs, holds), candidates, registry, owned_research=owned)
    review = deepcopy(p['review'])
    authority = model.evidence.MorphologyInputEvidenceAuthority(integrity_key=Path(p['input_key_file']).read_bytes(),
        issuer_id=p['issuer_id'], key_id=p['key_id'], review_resolver=lambda _: deepcopy(review))
    service = model.MorphologyFarmBinding(FarmAuthoringService(replay), authority, input_rights=Rights())
    packet = {k: Path(v).read_bytes() for k, v in p['packet_files'].items()}; expected = Path(p['binding']).read_bytes()
    body = model.documents._canonical(p['body']); calls = {}
    for name in ['crop_rational_shoot_inventory', 'crop_rational_new_internodes', 'crop_rational_internode_length',
        'crop_rational_morphology_clock', 'crop_shoot_inventory', 'crop_new_internodes', 'crop_shoot_timeline',
        'crop_phytomer_emergence', 'crop_internode_length', 'crop_internode_length_change',
        'crop_morphology_thermal_clock', 'crop_internode_elongation', 'crop_rational_morphology_artifact_producer']:
        module = importlib.import_module('app.'+name)
        for key, fn in vars(module).copy().items():
            if inspect.isfunction(fn) and fn.__module__ == module.__name__ and not key.startswith('_'):
                label = name+'.'+key; calls[label] = 0
                def fail(*a, _label=label, **kw):
                    calls[_label] += 1
                    raise AssertionError('fresh invoked growth '+_label)
                setattr(module, key, fail)
    from app.cli_worker import CliWorker
    calls['CLI'] = 0
    def cli(*a, **kw):
        calls['CLI'] += 1
        raise AssertionError('fresh invoked CLI')
    CliWorker.run_once = cli
    before = counts(service)
    with jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    actual = service.current('tenant-1', body, expected, **packet)
    review['status'] = 'revoked'
    try:
        service.current('tenant-1', body, expected, **packet)
    except model.MorphologyFarmBindingHold:
        pass
    else:
        raise AssertionError('fresh current revocation accepted')
    assert counts(service) == before and not any(calls.values()) and actual == expected
    assert not any(n in sys.modules for n in ('pytest', 'app.api', 'test_market_signed_hold_integration'))
    print(json.dumps({'binding_sha256': sha256(actual).hexdigest(), 'actual_SCRAM': True, 'new_exec': True,
        'unchanged_original_binding': True, 'current_review_revocation_rejected': True, 'counts': before, 'calls': calls,
        'seed_pytest_HTTP_app_imports': 0}))


if __name__ == '__main__':
    main()
