"""Resolve an atomic thermal completion to its existing verified public Run."""

from hashlib import sha256
import json
import re

from .api_thermal import RUN_ID_PATTERN, project_thermal_run
from .jobs import canonical_input_bytes
from .thermal_simulation_worker import SimulationInput


def read_job_run(jobs, runs, tenant, job_id):
    if not (jobs._has_scope(tenant, 'metadata') and jobs._has_scope(tenant, 'artifact') and
            runs._scope(tenant, 'thermal_run_read')):
        raise PermissionError('job Run access denied')
    job = jobs.get_job(tenant, job_id)
    if job is None or job['tenant_id'] != tenant:
        return None
    if job['job_id'] != job_id:
        raise ValueError('job Run identity differs')
    if job['stage'] != 'simulation' or job['state'] != 'succeeded':
        return None
    publication = jobs.get_publication(tenant, job_id)
    if (publication is None or type(publication.get('artifact_size')) is not int or
            not 1 <= publication['artifact_size'] <= 4096):
        raise ValueError('job Run completion missing')
    raw = jobs.read_artifact(tenant, job_id)
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
        raise ValueError('job Run completion missing')
    receipt = json.loads(raw)
    if type(receipt) is not dict or raw != canonical_input_bytes(receipt):
        raise ValueError('job Run receipt invalid')
    if receipt.get('receipt_version') != 'thermal-simulation-result-v1':
        return None
    run_id = receipt.get('run_id')
    if type(run_id) is not str or not re.fullmatch(RUN_ID_PATTERN, run_id):
        raise ValueError('job Run reference invalid')
    value = SimulationInput(input_version='thermal-simulation-input-v1',
        snapshot_id=receipt.get('snapshot_id'), review_job_id=receipt.get('review_job_id'))
    input_hash = sha256(canonical_input_bytes(value.model_dump(mode='json'))).hexdigest()
    digest = sha256(raw).hexdigest()
    manifest = {'schema_version': '1', 'job_id': str(job_id), 'stage': 'simulation',
        'input_sha256': input_hash, 'attempt': job['attempt_count'], 'artifact_sha256': digest}
    if (job['input_sha256'] != input_hash or publication['tenant_id'] != tenant or
            publication['job_id'] != job_id or publication['attempt'] != job['attempt_count'] or
            publication['decision_id'] is not None or publication['artifact_sha256'] != digest or
            publication['artifact_size'] != len(raw) or
            canonical_input_bytes(publication['manifest']) != canonical_input_bytes(manifest)):
        raise ValueError('job Run publication differs')
    stored = runs.get_run(tenant, run_id)
    if stored is None:
        raise ValueError('job Run record missing')
    report = stored['report']
    expected = {'receipt_version': 'thermal-simulation-result-v1', 'status': 'accepted',
        'claim_scope': 'synthetic_thermal_replay_only', 'run_id': report['run_id'],
        'snapshot_id': report['snapshot_id'], 'review_job_id': report['review_job_id'],
        'decision_context_id': report['decision_context_id'], 'decision_id': report['decision_id'],
        'trace_sha256': [sha256(trace).hexdigest() for trace in stored['trace_raws']],
        'report_sha256': sha256(stored['report_raw']).hexdigest()}
    if report['tenant_id'] != tenant or receipt != expected:
        raise ValueError('job Run report differs')
    return project_thermal_run(stored)[0]
