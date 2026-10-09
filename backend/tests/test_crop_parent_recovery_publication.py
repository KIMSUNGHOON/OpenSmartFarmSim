"""Recovery lineage contracts using private documents; native SCRAM proof is separate."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


@pytest.fixture
def owned(tmp_path, monkeypatch):
    helper = module('recovery_test', ROOT / 'research/crop-parent-recovery-publication.py')
    p = module('recovery_producer_test', ROOT / 'research/crop-harvest-parent-production.py')
    old_dir, new_dir = tmp_path / 'old', tmp_path / 'new'
    old_dir.mkdir(mode=0o700); new_dir.mkdir(mode=0o700)
    now = time.time_ns(); deadline = now + 600 * 10**9
    old_worker = {**p.supervisor.identity(os.getpid()), 'start_ticks': 1}
    old_pg = {'process': old_worker, 'data_directory': str(tmp_path / 'same-data')}
    config = {'input': {'root_sha256': 'a' * 64}, 'keys': {'server': str(tmp_path / 'server-key')},
              'request_file': str(tmp_path / 'request')}
    p.runtime.write_private(config['keys']['server'], b's' * 32)
    p.runtime.write_private(tmp_path / 'DB-key', b'd' * 32)
    farm = {'scenario_id': 'farm', 'scenario_revision': 'r1', 'registration_sha256': 'b' * 64, 'crop_id': 'crop'}
    request = {'farm': farm, 'input': {'root_sha256': 'a' * 64}}
    config['request_sha256'] = p.supervisor.immutable(Path(config['request_file']), request)
    config_path = tmp_path / 'config'; config_sha = p.supervisor.immutable(config_path, config)
    plan = {'steps': 120, 'counts': {'samples': 3, 'events': 3}}
    ref = {'steps': 120, 'counts': deepcopy(plan['counts'])}
    ref_path = tmp_path / 'reference'; ref_sha = p.supervisor.immutable(ref_path, ref)
    old = {'version': p.supervisor.VERSION, 'scope': p.supervisor.SCOPE, 'gates': 'not_assessed',
        'source_sha256': {'supervisor': 'source'}, 'boot_id': old_worker['boot_id'], 'python_version': 'fixture',
        'started_ns': now - 30 * 10**9, 'deadline_ns': deadline, 'config': str(config_path), 'config_sha256': config_sha,
        'input_root_sha256': 'a' * 64, 'DB_reference_file': 'dsn', 'budget': {'max_steps': 40, 'max_transitions': 48},
        'primary_RSS_limit_bytes': 512 * 1024**2, 'pipeline_RSS_limit_bytes': 1024**3,
        'log_limit_bytes': 1024**2, 'owned_pg': old_pg}
    old_sha = p.supervisor.immutable(old_dir / 'supervision.json', old)
    decl = {'version': p.publisher.VERSION, 'scope': p.publisher.SCOPE, 'code_sha256': p.publisher.CODE_SHA256,
        'source_sha256': {'publisher': 'source'}, 'supervision_directory': str(old_dir), 'supervision_sha256': old_sha,
        'DB_key_file': str(tmp_path / 'DB-key'), 'DB_key_sha256': sha256(b'd' * 32).hexdigest(),
        'input_root_sha256': 'a' * 64, 'plan': plan}
    decl_path = tmp_path / 'publication'; decl_sha = p.supervisor.immutable(decl_path, decl)
    preparation = {'version': p.coordinator.VERSION, 'gates': 'not_assessed', 'deadline_ns': deadline}
    prep_path = tmp_path / 'preparation'; prep_sha = p.supervisor.immutable(prep_path, preparation)
    e = {'version': p.coordinator.VERSION, 'preparation_file': str(prep_path), 'preparation_sha256': prep_sha,
        'preparation_deadline_ns': deadline, 'config_sha256': config_sha, 'publication_file': str(decl_path),
        'publication_sha256': decl_sha, 'reference_file': str(ref_path), 'reference_sha256': ref_sha,
        'plan': deepcopy(plan), 'farm': farm, 'input_root_sha256': 'a' * 64}
    e_path = tmp_path / 'execution'; e_sha = p.supervisor.immutable(e_path, e)
    first = {'supervision_sha256': old_sha, 'deadline_ns': deadline,
             'requested_at_utc': datetime.fromtimestamp((now - 10 * 10**9) / 1e9, timezone.utc).isoformat()}
    p.supervisor.immutable(old_dir / 'attempt-0001.request.json', first)
    p.supervisor.immutable(old_dir / 'attempt-0001.worker.json', old_worker)
    incident = {'version': 'owned-parent-interruption-v1', 'actual_pytest_exit': -15,
        'interrupted_HEAD_sha256': 'c' * 64, 'interrupted_steps': 40, 'interrupted_commit_count': 1,
        'original_completed_or_accepted': False, 'original_deadline_ns': deadline, 'deadline_not_extended': True,
        'private_material_sha256': {str(e_path): e_sha, str(decl_path): decl_sha, str(config_path): config_sha,
                                   str(ref_path): ref_sha, decl['DB_key_file']: decl['DB_key_sha256']}}
    incident_path = tmp_path / 'incident'; incident_sha = p.supervisor.immutable(incident_path, incident)
    new = {**old, 'started_ns': now - 10**9, 'deadline_ns': deadline - 10**9,
           'owned_pg': {'process': p.supervisor.identity(os.getpid()), 'data_directory': old_pg['data_directory']}}
    new_sha = p.supervisor.immutable(new_dir / 'supervision.json', new)
    checkpoint = {'steps': 40}
    resumed = {'stage': 'recovered', 'worker': old_worker, 'RHS_calls': 0, 'delta_QC_calls': 0,
        'progress': {'head_sha256': 'c' * 64, 'steps': 40, 'commit_count': 1}, 'checkpoint': checkpoint}
    log = p.canonical(resumed) + b'\n'; p.runtime.write_private(new_dir / 'attempt-0001.log', log)
    result = {'progress': {'status': 'completed', 'steps': 120, 'planned_steps': 120, 'counts': plan['counts']},
        'config_sha256': config_sha, 'deadline_ns': new['deadline_ns'], 'recovery_RHS_calls': 0,
        'actual_scram_used_password': True, 'FD_before_after': [4, 4], 'restored_checkpoint': checkpoint}
    result_sha = p.supervisor.immutable(new_dir / 'attempt-0001.result.json', result)
    request_sha = p.supervisor.immutable(new_dir / 'attempt-0001.request.json', {'supervision_sha256': new_sha})
    p.supervisor.immutable(new_dir / 'attempt-0001.worker.json', old_worker)
    receipt = {'supervision_sha256': new_sha, 'worker': old_worker, 'request_sha256': request_sha,
        'outcome': 'recorded', 'worker_returncode': 0, 'result': result, 'result_file': 'attempt-0001.result.json',
        'result_sha256': result_sha, 'log_sha256': sha256(log).hexdigest()}
    p.supervisor.immutable(new_dir / 'attempt-0001.receipt.json', receipt)
    for path in (e_path, decl_path, Path(decl['DB_key_file'])):
        os.utime(path, ns=(now - 20 * 10**9, now - 20 * 10**9))
    monkeypatch.setattr(p.supervisor, 'sources', lambda: {'supervisor': 'source'})
    monkeypatch.setattr(p.publisher, 'sources', lambda: {'publisher': 'source'})
    def configuration(path, expected):
        return helper.document(p, path, expected)
    def verified(directory, expected, **_):
        directory = Path(directory)
        value = helper.document(p, directory / 'supervision.json', expected)
        if value['deadline_ns'] <= time.time_ns(): raise ValueError('expired fixture')
        return directory, value
    monkeypatch.setattr(p.supervisor, 'configuration', configuration)
    monkeypatch.setattr(p.supervisor, 'verified', verified)
    monkeypatch.setattr(p.coordinator, 'checked', lambda path, expected: helper.document(p, path, expected))
    args = {'execution_path': e_path, 'execution_sha256': e_sha, 'incident_path': incident_path,
        'incident_sha256': incident_sha, 'recovery_directory': new_dir, 'recovery_sha256': new_sha,
        'output_directory': tmp_path / 'derived'}
    return helper, p, args, {'e': e, 'decl': decl, 'old': old, 'new': new, 'result': result,
        'receipt': receipt, 'incident': incident, 'first': first, 'old_worker': old_worker, 'now': now}


def rewrite(p, path, value):
    path = Path(path); path.chmod(0o600); path.write_bytes(p.canonical(value)); path.chmod(0o400)
    return sha256(path.read_bytes()).hexdigest()


def test_only_supervision_and_publication_references_change_and_old_inputs_stay_exact(owned, monkeypatch):
    helper, p, args, objects = owned
    old = {str(path): path.read_bytes() for path in Path(args['execution_path']).parent.rglob('*') if path.is_file()}
    monkeypatch.setattr(p.runtime.engine.short._Evaluator, 'rhs', lambda *_: pytest.fail('derivation ran RHS'))
    path, checksum = helper.derive(p, **args)
    value = helper.checked(p, path, checksum)
    candidate = json.loads(Path(value['publication']['file']).read_bytes())
    assert {k:v for k,v in candidate.items() if k not in ('supervision_directory','supervision_sha256')} == {
        k:v for k,v in objects['decl'].items() if k not in ('supervision_directory','supervision_sha256')}
    assert all(Path(name).read_bytes() == raw for name, raw in old.items())
    assert candidate['DB_key_file'] == objects['decl']['DB_key_file']
    with pytest.raises(FileExistsError): helper.derive(p, **args)


@pytest.mark.parametrize('fault', ['execution-sha', 'incident-sha', 'plan', 'farm', 'key', 'source', 'mtime',
    'old-result', 'old-live', 'deadline', 'budget', 'data-directory', 'input', 'status', 'RHS', 'SCRAM', 'FD'])
def test_faults_refuse_derivation_before_any_new_file(owned, fault):
    helper, p, args, o = owned
    if fault == 'execution-sha': args['execution_sha256'] = '0' * 64
    elif fault == 'incident-sha': args['incident_sha256'] = '0' * 64
    elif fault in ('plan', 'farm'):
        if fault == 'plan': o['e']['plan']['steps'] += 1
        else: o['e']['farm'] = {**o['e']['farm'], 'crop_id': 'different'}
        args['execution_sha256'] = rewrite(p, args['execution_path'], o['e'])
        o['incident']['private_material_sha256'][str(args['execution_path'])] = args['execution_sha256']
        args['incident_sha256'] = rewrite(p, args['incident_path'], o['incident'])
    elif fault == 'key': Path(o['decl']['DB_key_file']).chmod(0o600); Path(o['decl']['DB_key_file']).write_bytes(b'x'*32)
    elif fault == 'source':
        o['decl']['source_sha256'] = {}
        o['e']['publication_sha256'] = rewrite(p, o['e']['publication_file'], o['decl'])
        args['execution_sha256'] = rewrite(p, args['execution_path'], o['e'])
        o['incident']['private_material_sha256'].update({str(args['execution_path']):args['execution_sha256'],
            o['e']['publication_file']:o['e']['publication_sha256']})
        args['incident_sha256'] = rewrite(p, args['incident_path'], o['incident'])
    elif fault == 'mtime': os.utime(args['execution_path'], None)
    elif fault == 'old-result': p.supervisor.immutable(Path(o['decl']['supervision_directory'])/'attempt-0001.result.json', {})
    elif fault == 'old-live':
        o['old']['owned_pg']['process'] = p.supervisor.identity(os.getpid())
        old_sha = rewrite(p, Path(o['decl']['supervision_directory'])/'supervision.json', o['old'])
        o['decl']['supervision_sha256'] = old_sha
        o['e']['publication_sha256'] = rewrite(p, o['e']['publication_file'], o['decl'])
        args['execution_sha256'] = rewrite(p, args['execution_path'], o['e'])
        o['incident']['private_material_sha256'].update({str(args['execution_path']):args['execution_sha256'],
            o['e']['publication_file']:o['e']['publication_sha256']})
        args['incident_sha256'] = rewrite(p, args['incident_path'], o['incident'])
        for path in (args['execution_path'], o['e']['publication_file']): os.utime(path,ns=(o['now']-20*10**9,)*2)
        o['first']['supervision_sha256'] = old_sha
        rewrite(p, Path(o['decl']['supervision_directory'])/'attempt-0001.request.json', o['first'])
    elif fault in ('deadline', 'budget', 'data-directory', 'input'):
        if fault == 'deadline': o['new']['deadline_ns'] = o['old']['deadline_ns'] + 1
        elif fault == 'budget': o['new']['budget'] = {'max_steps': 41, 'max_transitions': 48}
        elif fault == 'data-directory': o['new']['owned_pg']['data_directory'] += '-other'
        else: o['new']['input_root_sha256'] = 'f'*64
        args['recovery_sha256'] = rewrite(p, Path(args['recovery_directory'])/'supervision.json',o['new'])
    else:
        if fault == 'status': o['result']['progress']['status'] = 'yielded'
        elif fault == 'RHS': o['result']['recovery_RHS_calls'] = 1
        elif fault == 'SCRAM': o['result']['actual_scram_used_password'] = False
        elif fault == 'FD': o['result']['FD_before_after'] = [4, 5]
        o['receipt']['result_sha256'] = rewrite(p, Path(args['recovery_directory'])/'attempt-0001.result.json', o['result'])
        rewrite(p, Path(args['recovery_directory'])/'attempt-0001.receipt.json', o['receipt'])
    with pytest.raises((ValueError, KeyError, OSError)): helper.derive(p, **args)
    assert not Path(args['output_directory']).exists()


def test_changed_original_or_derived_manifest_is_refused_after_derivation(owned):
    helper, p, args, _ = owned
    path, checksum = helper.derive(p, **args)
    value = helper.checked(p, path, checksum)
    candidate = json.loads(Path(value['publication']['file']).read_bytes()); candidate['plan']['steps'] += 1
    value['publication']['sha256'] = rewrite(p, value['publication']['file'], candidate)
    new_checksum = rewrite(p, path, value)
    with pytest.raises(ValueError): helper.checked(p, path, new_checksum)


@pytest.mark.parametrize('fault', ['head', 'delta-QC', 'worker', 'checkpoint'])
def test_changed_recovered_head_or_delta_QC_is_refused(owned, fault):
    helper, p, args, _ = owned
    log = Path(args['recovery_directory'])/'attempt-0001.log'
    value = json.loads(log.read_bytes())
    if fault == 'head': value['progress']['head_sha256'] = 'f'*64
    elif fault == 'delta-QC': value['delta_QC_calls'] = 1
    elif fault == 'worker': value['worker']['start_ticks'] += 1
    else: value['checkpoint']['steps'] += 1
    digest = rewrite(p, log, value)
    receipt_path = Path(args['recovery_directory'])/'attempt-0001.receipt.json'
    receipt = json.loads(receipt_path.read_bytes()); receipt['log_sha256'] = digest
    rewrite(p, receipt_path, receipt)
    with pytest.raises(ValueError): helper.derive(p, **args)
