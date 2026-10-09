"""Derive an owned publication from its preserved pre-calculation declaration."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

VERSION = 'owned-parent-recovery-publication-v1'
SCOPE = 'owned_synthetic_interrupted_parent_only'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
CORE = ('contracts/crop-parent-recovery-publication-v1.md',
        'research/crop-parent-recovery-publication.py')
LEGACY_INCIDENT_FIELDS = set(('actual_pytest_exit cause config_and_original_authority_retained '
    'deadline_not_extended full_original_exit full_original_session interrupted_HEAD_sha256 '
    'interrupted_commit_count interrupted_steps observed_at_local offline_PG_sha256 '
    'original_completed_or_accepted original_deadline_ns preview_exit preview_original_session '
    'private_material_sha256 source_worktree_sha256 test_exit test_original_session').split())
INCIDENT_FIELDS = set(('version actual_pytest_exit interrupted_HEAD_sha256 interrupted_commit_count '
    'interrupted_steps original_completed_or_accepted original_deadline_ns deadline_not_extended '
    'private_material_sha256').split())


def need(value):
    if not value:
        raise ValueError('original interrupted parent lineage required')


def load_producer(source):
    source = Path(source).absolute()
    path = source / 'research/crop-harvest-parent-production.py'
    need(sha256(path.read_bytes()).hexdigest() ==
         '87096fd690ff777dca150213294c5c62d6e757ccf853ca5b41eea3e1a397db34')
    spec = importlib.util.spec_from_file_location('preserved_parent_producer', path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    value.coordinator.sources()
    return value


def sources():
    root = Path(__file__).resolve().parents[1]
    need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)
    return {name: sha256((root / name).read_bytes()).hexdigest() for name in CORE}


def document(p, path, expected, *, canonical=True):
    raw = p.runtime.private_bytes(path)
    need(sha256(raw).hexdigest() == expected)
    value = json.loads(raw)
    need(type(value) is dict)
    if canonical:
        need(p.canonical(value) == raw)
    return value


def gone(p, original):
    need(set(original) == {'pid', 'start_ticks', 'boot_id'} and
         type(original['pid']) is int and original['pid'] > 0 and
         type(original['start_ticks']) is int and original['start_ticks'] > 0)
    try:
        state = Path('/proc', str(original['pid']), 'stat').read_text().rsplit(')', 1)[1].split()[0]
        need(p.supervisor.identity(original['pid']) != original or state == 'Z')
    except (FileNotFoundError, ProcessLookupError):
        pass


def time_ns(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(parsed.utcoffset().total_seconds() == 0)
    delta = parsed - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 10**9 + delta.microseconds * 1000


def original(p, execution_path, execution_sha256, incident_path, incident_sha256):
    e = document(p, execution_path, execution_sha256)
    need(set(e) == set(('version preparation_file preparation_sha256 preparation_deadline_ns '
                       'config_sha256 publication_file publication_sha256 reference_file reference_sha256 '
                       'plan farm input_root_sha256').split()))
    incident = document(p, incident_path, incident_sha256, canonical=False)
    if incident.get('version') == 'owned-parent-interruption-v1':
        need(set(incident) == INCIDENT_FIELDS)
    else:
        need(set(incident) == LEGACY_INCIDENT_FIELDS)
    need(incident['actual_pytest_exit'] == -15 and
         incident['original_completed_or_accepted'] is False and incident['deadline_not_extended'] is True)
    need(type(incident['interrupted_steps']) is int and incident['interrupted_steps'] > 0)
    need(type(incident['interrupted_commit_count']) is int and incident['interrupted_commit_count'] > 0)
    material = incident['private_material_sha256']
    need(material[str(execution_path)] == execution_sha256)
    initial = p.coordinator.checked(e['preparation_file'], e['preparation_sha256'])
    need(e['version'] == p.coordinator.VERSION and
         incident['original_deadline_ns'] == e['preparation_deadline_ns'] == initial['deadline_ns'])
    decl = document(p, e['publication_file'], e['publication_sha256'])
    need(material[e['publication_file']] == e['publication_sha256'])
    need(set(decl) == p.publisher.FIELDS and decl['version'] == p.publisher.VERSION and
         decl['scope'] == p.publisher.SCOPE and decl['code_sha256'] == p.publisher.CODE_SHA256 and
         decl['source_sha256'] == p.publisher.sources())
    old_dir = Path(decl['supervision_directory'])
    old = document(p, old_dir / 'supervision.json', decl['supervision_sha256'])
    need(old['version'] == p.supervisor.VERSION and old['scope'] == p.supervisor.SCOPE and
         old['gates'] == 'not_assessed' and old['source_sha256'] == p.supervisor.sources())
    config = p.supervisor.configuration(old['config'], old['config_sha256'])
    need(material[old['config']] == e['config_sha256'] == old['config_sha256'])
    need(e['input_root_sha256'] == decl['input_root_sha256'] == old['input_root_sha256'] ==
         config['input']['root_sha256'])
    need(old['deadline_ns'] <= initial['deadline_ns'] and decl['plan'] == e['plan'])
    ref = document(p, e['reference_file'], e['reference_sha256'])
    need(material[e['reference_file']] == e['reference_sha256'])
    need(ref['steps'] == e['plan']['steps'] and ref['counts'] == e['plan']['counts'] and
         incident['interrupted_steps'] < e['plan']['steps'])
    request = document(p, config['request_file'], config['request_sha256'])
    need(request['farm'] == e['farm'] and request['input']['root_sha256'] == e['input_root_sha256'])
    key = p.runtime.private_bytes(decl['DB_key_file'])
    need(len(key) == 32 and sha256(key).hexdigest() == decl['DB_key_sha256'] and
         material[decl['DB_key_file']] == decl['DB_key_sha256'] and
         key != p.runtime.private_bytes(config['keys']['server']))
    attempts = sorted(old_dir.glob('attempt-*.request.json'))
    need(0 < len(attempts) < 9999)
    for index, path in enumerate(attempts):
        _, attempt = p.supervisor.read_json(path)
        prefix = path.name.removesuffix('.request.json')
        need(attempt['supervision_sha256'] == decl['supervision_sha256'] and
             attempt['deadline_ns'] == old['deadline_ns'])
        _, worker = p.supervisor.read_json(old_dir / (prefix + '.worker.json'))
        gone(p, worker)
        receipt = old_dir / (prefix + '.receipt.json')
        result = old_dir / (prefix + '.result.json')
        if index == len(attempts) - 1:
            need(not receipt.exists() and not result.exists())
        else:
            _, r = p.supervisor.read_json(receipt)
            need(r['supervision_sha256'] == decl['supervision_sha256'] and
                 r['request_sha256'] == p.supervisor.digest(path) and r['worker'] == worker and
                 r['log_sha256'] == p.supervisor.digest(old_dir / (prefix + '.log')) and
                 r['result_file'] == result.name)
            if r['result_sha256'] is not None:
                need(p.supervisor.digest(result) == r['result_sha256'])
            else:
                need(not result.exists())
            need((r.get('result') or {}).get('progress', {}).get('status') != 'completed')
    _, first = p.supervisor.read_json(attempts[0])
    first_ns = time_ns(first['requested_at_utc'])
    need(all(Path(path).stat().st_mtime_ns < first_ns
             for path in (execution_path, e['publication_file'], decl['DB_key_file'])))
    need(old['owned_pg'] is not None)
    gone(p, old['owned_pg']['process'])
    return e, decl, old, incident


def recovered(p, e, old, incident, directory, expected):
    directory, new = p.supervisor.verified(directory, expected)
    unchanged = ('version', 'scope', 'gates', 'boot_id', 'python_version', 'source_sha256',
                 'config', 'config_sha256', 'input_root_sha256', 'DB_reference_file', 'budget',
                 'primary_RSS_limit_bytes', 'pipeline_RSS_limit_bytes', 'log_limit_bytes')
    need(all(new[k] == old[k] for k in unchanged))
    need(old['started_ns'] < new['started_ns'] < new['deadline_ns'] <= old['deadline_ns'])
    need(new['owned_pg'] is not None and
         new['owned_pg']['data_directory'] == old['owned_pg']['data_directory'] and
         new['owned_pg']['process'] != old['owned_pg']['process'])
    p.supervisor.history(directory, expected)
    receipts = sorted(directory.glob('attempt-*.receipt.json')); need(bool(receipts))
    _, receipt = p.supervisor.read_json(receipts[-1])
    result = receipt.get('result') or {}; progress = result.get('progress') or {}
    need(receipt['outcome'] == 'recorded' and receipt['worker_returncode'] == 0 and
         progress.get('status') == 'completed' and progress.get('steps') == e['plan']['steps'] and
         progress.get('planned_steps') == e['plan']['steps'] and progress.get('counts') == e['plan']['counts'])
    need(result['config_sha256'] == new['config_sha256'] and result['deadline_ns'] == new['deadline_ns'] and
         result['recovery_RHS_calls'] == 0 and result['actual_scram_used_password'] is True and
         result['FD_before_after'][0] == result['FD_before_after'][1])
    prefix = receipts[0].name.removesuffix('.receipt.json')
    log = p.runtime.private_bytes(directory / (prefix + '.log'))
    first = json.loads(log.splitlines()[0])
    need(first['stage'] == 'recovered' and first['RHS_calls'] == first['delta_QC_calls'] == 0)
    need(first['progress']['head_sha256'] == incident['interrupted_HEAD_sha256'] and
         first['progress']['steps'] == first['checkpoint']['steps'] == incident['interrupted_steps'] and
         first['progress']['commit_count'] == incident['interrupted_commit_count'])
    _, first_receipt = p.supervisor.read_json(receipts[0])
    need(first_receipt['result']['restored_checkpoint'] == first['checkpoint'] and
         first_receipt['worker'] == first['worker'])
    gone(p, receipt['worker'])
    return new, receipts[-1], p.supervisor.digest(receipts[-1])


def derive(p, *, execution_path, execution_sha256, incident_path, incident_sha256,
           recovery_directory, recovery_sha256, output_directory):
    pins = sources()
    e, decl, old, incident = original(p, execution_path, execution_sha256, incident_path, incident_sha256)
    new, receipt, receipt_sha = recovered(p, e, old, incident, recovery_directory, recovery_sha256)
    out = Path(output_directory).absolute(); out.mkdir(mode=0o700); p.supervisor.directory(out)
    candidate = {**decl, 'supervision_directory': str(Path(recovery_directory).absolute()),
                 'supervision_sha256': recovery_sha256}
    publication = out / 'publication.json'; publication_sha = p.supervisor.immutable(publication, candidate)
    run = {**e, 'publication_file': str(publication), 'publication_sha256': publication_sha}
    execution = out / 'execution.json'; run_sha = p.supervisor.immutable(execution, run)
    p.coordinator.execution(execution, run_sha)
    need(original(p, execution_path, execution_sha256, incident_path, incident_sha256) == (e, decl, old, incident))
    need(sources() == pins)
    manifest = {'version': VERSION, 'scope': SCOPE, 'gates': 'not_assessed', 'source_sha256': pins,
        'original_execution': {'file': str(execution_path), 'sha256': execution_sha256},
        'interruption': {'file': str(incident_path), 'sha256': incident_sha256},
        'recovery': {'directory': str(recovery_directory), 'sha256': recovery_sha256},
        'completed_receipt': {'file': str(receipt), 'sha256': receipt_sha},
        'publication': {'file': str(publication), 'sha256': publication_sha},
        'execution': {'file': str(execution), 'sha256': run_sha},
        'original_preparation_deadline_ns': e['preparation_deadline_ns'],
        'new_deadline_ns': new['deadline_ns'], 'derivation_RHS_publication_proof_calls': 0}
    path = out / 'recovery.json'; checksum = p.supervisor.immutable(path, manifest)
    return path, checksum


def checked(p, path, expected):
    value = document(p, path, expected)
    need(value['version'] == VERSION and value['scope'] == SCOPE and value['gates'] == 'not_assessed' and
         value['source_sha256'] == sources())
    original_ref, incident_ref = value['original_execution'], value['interruption']
    e, decl, old, incident = original(p, original_ref['file'], original_ref['sha256'],
                                    incident_ref['file'], incident_ref['sha256'])
    new, receipt, receipt_sha = recovered(p, e, old, incident, value['recovery']['directory'],
                                        value['recovery']['sha256'])
    need(value['completed_receipt'] == {'file': str(receipt), 'sha256': receipt_sha})
    candidate = document(p, value['publication']['file'], value['publication']['sha256'])
    run = document(p, value['execution']['file'], value['execution']['sha256'])
    need(candidate == {**decl, 'supervision_directory': str(Path(value['recovery']['directory']).absolute()),
                        'supervision_sha256': value['recovery']['sha256']})
    need(run == {**e, 'publication_file': value['publication']['file'], 'publication_sha256': value['publication']['sha256']})
    need(value['original_preparation_deadline_ns'] == e['preparation_deadline_ns'] and
         value['new_deadline_ns'] == new['deadline_ns'] and value['derivation_RHS_publication_proof_calls'] == 0)
    p.coordinator.execution(value['execution']['file'], value['execution']['sha256'])
    return value
