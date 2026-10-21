"""Actual SCRAM signed-result reads without importing the morphology producer."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

from app import crop_morphology_signed_artifact as signed
from app.content_access import ContentAccess
from morphology_farm_fresh import (RuntimeLoginPolicy, JobStore, MarketSourceStore, ThermalRunStore, MarketHoldStore,
    _MarketSources, MarketCandidateStore, ResearchRegistry, OwnedResearchService, OwnedFixtureRegistry,
    FarmReplayScenarioService, ThermalScenarioStore, FarmAuthoringService, context_verifier, Rights, counts)
import os


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
    candidates = MarketCandidateStore(dsn, schema, _MarketSources(sources, holds, principal_provider=provider), **kw)
    registry = ResearchRegistry(p['registry_raw'].encode(), p['registry_sha256'])
    owned = OwnedResearchService(jobs, runs, registry, OwnedFixtureRegistry(Path(p['root'])), {next(iter(registry._scopes)): 'context-1'})
    replay = FarmReplayScenarioService(jobs, ThermalScenarioStore(runs, holds), candidates, registry, owned_research=owned)
    review = deepcopy(p['review'])
    authority = signed.farms.evidence.MorphologyInputEvidenceAuthority(integrity_key=Path(p['input_key_file']).read_bytes(),
        issuer_id=p['issuer_id'], key_id=p['key_id'], review_resolver=lambda _: deepcopy(review))
    binding = signed.farms.MorphologyFarmBinding(FarmAuthoringService(replay), authority, input_rights=Rights())
    config = p['signed']
    reader = signed.MorphologyArtifactAuthority(binding, directory=Path(config['directory']), access=ContentAccess(os.getuid(), os.getgid()),
        integrity_key=Path(config['key_file']).read_bytes(), issuer_id=config['issuer_id'], key_id=config['key_id'])
    forbidden = {'app.'+n for n in ['crop_rational_shoot_inventory', 'crop_rational_new_internodes', 'crop_rational_internode_length',
        'crop_rational_morphology_clock', 'crop_shoot_inventory', 'crop_new_internodes', 'crop_shoot_timeline',
        'crop_phytomer_emergence', 'crop_internode_length', 'crop_internode_length_change', 'crop_morphology_thermal_clock',
        'crop_internode_elongation', 'crop_rational_morphology_artifact_producer', 'crop_morphology_signed_producer']}
    assert not forbidden.intersection(sys.modules)
    calls = {name: 0 for name in sorted(forbidden)}
    class NoGrowth:
        def find_spec(self, fullname, *a, **kw):
            if fullname in forbidden:
                calls[fullname] += 1
                raise AssertionError('readonly imported growth')
            return None
    sys.meta_path.insert(0, NoGrowth())
    writes = {}
    for name in ('submit', 'publish', 'record_decision', '_insert_publication', '_event'):
        writes[name] = 0
        def blocked(*a, _name=name, **kw):
            writes[_name] += 1
            raise AssertionError('readonly wrote a job')
        setattr(JobStore, name, blocked)
    before = counts(binding)
    with jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    manifest = reader.read_manifest('tenant-1', config['result_sha256'])
    assert manifest['numerical_root_sha256'] == config['expected_numerical_root_sha256']
    assert manifest['calculated_at'] == config['expected_calculated_at']
    frames = []
    for index in (0, 11):
        result = reader.read_frame('tenant-1', config['result_sha256'], index=index)
        original = (Path(p['root'])/f'web/public/morphology-rational-replay/frame-{index}.json').read_bytes()
        assert signed.reader._canonical(result['frame']) == original and result['frame_sha256'] == sha256(original).hexdigest()
        assert result['calculated_at'] == manifest['calculated_at']; frames.append(result['frame_sha256'])
    review['status'] = 'revoked'
    try:
        reader.read_manifest('tenant-1', config['result_sha256'])
    except signed.MorphologySignedArtifactHold:
        pass
    else:
        raise AssertionError('fresh signed result reused revoked review')
    assert counts(binding) == before and not any(calls.values()) and not any(writes.values())
    assert not forbidden.intersection(sys.modules) and not any(n in sys.modules for n in ('pytest', 'app.api', 'test_market_signed_hold_integration'))
    print(json.dumps({'actual_SCRAM': True, 'fresh_exec': True, 'result_sha256': config['result_sha256'],
        'numerical_root_sha256': manifest['numerical_root_sha256'], 'calculated_at': manifest['calculated_at'],
        'original_frame_sha256': frames, 'new_growth_modules_imported': 0, 'blocked_import_calls': calls,
        'job_write_calls': writes, 'current_review_revocation_rejected': True, 'counts_before_after': [before, counts(binding)]}))


if __name__ == '__main__':
    main()
