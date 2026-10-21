"""Read only published morphology jobs; never import numerical workers/producers."""
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from psycopg import sql

from . import crop_morphology_execution as execution
from . import crop_morphology_execution_result as result
from .api_contracts import public_job_status


VERSION = 'morphology-execution-read-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
WORKER_SHA256 = sha256(Path(__file__).with_name('crop_morphology_execution_worker.py').read_bytes()).hexdigest()
_FLAGS = dict(execution.signed.reader.FLAGS)


class MorphologyExecutionQueryHold(ValueError):
    """No current authorized, unchanged morphology job result is available."""


class MorphologyExecutionQueryPending(ValueError):
    """The stored execution changed while this response was being read."""


def _need(condition):
    if not condition:
        raise MorphologyExecutionQueryHold('morphology execution query unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kw):
        try:
            return fn(*args, **kw)
        except (PermissionError, MorphologyExecutionQueryPending):
            raise
        except Exception:
            raise MorphologyExecutionQueryHold('morphology execution query unavailable') from None
    return run


class MorphologyExecutionQuery:
    @_checked
    def __init__(self, service):
        _need(type(service) is execution.MorphologyExecutionService)
        self.service, self.jobs = service, service.jobs
        self._fixed = (service, service.jobs)
        self._binding()

    def _binding(self):
        _need((self.service, self.jobs) == self._fixed and self.jobs is self.service.jobs
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and sha256(Path(__file__).with_name('crop_morphology_execution_worker.py').read_bytes()).hexdigest() == WORKER_SHA256
            and VERSION == 'morphology-execution-read-v1' and execution.signed.reader.FLAGS == _FLAGS)
        self.service._binding(); result._binding()

    def _guard(self, tenant):
        self._binding(); self.service.authority.farm_binding._guard(tenant, False)
        if not self.jobs._has_scope(tenant, 'metadata') or not self.jobs._has_scope(tenant, 'artifact'):
            raise PermissionError('morphology execution query access denied')
        self._binding()

    def _bundle(self, tenant, job_id):
        with self.jobs.connect() as conn:
            job = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                .format(self.jobs._table('jobs')), (tenant, job_id)).fetchone()
            _need(job is not None and job['stage'] == 'simulation')
            pubs = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s ORDER BY attempt LIMIT 2')
                .format(self.jobs._table('job_publications')), (tenant, job_id)).fetchall()
            events = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND '
                '(kind=%s OR (attempt=%s AND kind=ANY(%s))) ORDER BY recorded_at,event_id LIMIT 8')
                .format(self.jobs._table('job_events')), (tenant, job_id, result.RESULT_EVENT_KIND, job['attempt_count'],
                    [result.START_EVENT_KIND, 'succeeded', 'hold', 'failed', 'canceled'])).fetchall()
            outcomes = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s LIMIT 2')
                .format(self.jobs._table('attempt_outcomes')), (tenant, job_id, job['attempt_count'])).fetchall()
            invocations = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s LIMIT 1')
                .format(self.jobs._table('attempt_invocations')), (tenant, job_id, job['attempt_count'])).fetchall()
        self.jobs._verified_input(job)
        return job, pubs, events, outcomes, invocations

    def _completed(self, tenant, bundle, value):
        job, pubs, events, outcomes, invocations = bundle
        _need(len(pubs) == len(outcomes) == 1 and not invocations and job['reason'] is None)
        pub, outcome = pubs[0], outcomes[0]
        raw = self.jobs.read_artifact(tenant, job['job_id']); link = result.read_link(raw, job)
        manifest = result.publication_manifest(job, raw, link['result_sha256'], WORKER_SHA256)
        _need(pub['attempt'] == job['attempt_count'] and pub['decision_id'] is None
            and pub['artifact_sha256'] == manifest['artifact_sha256'] and pub['artifact_size'] == len(raw)
            and pub['manifest'] == manifest and outcome['state'] == 'succeeded' and outcome['reason'] is None
            and outcome['decision_id'] is None and outcome['termination_reason'] == 'morphology_completed')
        starts = [e for e in events if e['kind'] == result.START_EVENT_KIND]
        links = [e for e in events if e['kind'] == result.RESULT_EVENT_KIND]
        terminals = [e for e in events if e['kind'] in ('succeeded', 'hold', 'failed', 'canceled')]
        _need(len(starts) == len(links) == len(terminals) == 1
            and links[0]['attempt'] == job['attempt_count'] and links[0]['reason'] == manifest
            and terminals[0]['kind'] == 'succeeded' and terminals[0]['reason'] is None)
        proof = self.service.authority.read_manifest(tenant, link['result_sha256'])
        _need(starts[0]['reason'] == {'execution_kind': 'deterministic_morphology', 'worker_code_sha256': WORKER_SHA256,
            'input_sha256': job['input_sha256'], 'planned_outputs': len(proof['manifest']['samples'])})
        request = value['request']
        _need(proof['binding_sha256'] == value['farm_binding_sha256']
            and proof['study_id'] == request['study_id'] and proof['revision'] == request['revision']
            and proof['farm'] == request['farm'] and proof['program_sha256'] == request['input']['program_sha256']
            and proof['source_sha256'] == request['input']['source_sha256']
            and proof['input_evidence_sha256'] == request['input']['evidence_sha256'])
        return proof

    @_checked
    def read(self, tenant, job_id, *, view='status', index=None):
        _need(type(job_id) is str and str(UUID(job_id)) == job_id and view in ('status', 'manifest', 'frame', 'replay'))
        _need((view == 'frame' and type(index) is int and index >= 0) or (view != 'frame' and index is None))
        self._guard(tenant); before = self._bundle(tenant, job_id); job = before[0]
        original = self.service.current_input(tenant, job['input_bytes']); value = original[0]
        proof = self._completed(tenant, before, value) if job['state'] == 'succeeded' else None
        if proof is None:
            _need(not before[1] and not any(e['kind'] in (result.RESULT_EVENT_KIND, 'succeeded') for e in before[2]))
        _need(view == 'status' or proof is not None)
        frame = None; replay = None
        if view == 'frame':
            frame = self.service.authority.read_frame(tenant, proof['result_sha256'], index=index)
            _need(all(frame[k] == proof[k] for k in ('result_sha256', 'numerical_root_sha256', 'calculated_at',
                'binding_sha256', 'program_sha256', 'source_sha256', 'input_evidence_sha256')))
        if view == 'replay':
            frames = []
            for sample_index in range(len(proof['manifest']['samples'])):
                original_frame = execution.signed.reader.read_rational_morphology_frame(self.service.authority.directory,
                    self.service.authority.access, proof['numerical_root_sha256'], index=sample_index)
                frames.append(original_frame)
                _need(len(execution.signed.reader._canonical(frames)) <= execution.signed.RETURN_MAX)
            replay = {'manifest': proof, 'frames': frames}
        self._guard(tenant)
        _need(self.service.current_input(tenant, job['input_bytes']) == original)
        if proof is not None:
            _need(self.service.authority.read_manifest(tenant, proof['result_sha256']) == proof)
        after = self._bundle(tenant, job_id)
        if before != after:
            raise MorphologyExecutionQueryPending('morphology execution changed; retry current read')
        self._guard(tenant)
        summary = None if proof is None else {k: proof[k] for k in ('result_sha256', 'numerical_root_sha256', 'calculated_at',
            'study_id', 'revision', 'farm', 'profile_applicability', 'binding_sha256', 'program_sha256',
            'source_sha256', 'input_evidence_sha256')}
        response = {'schema_version': VERSION, **_FLAGS, 'observed_at': execution.signed._stamp(datetime.now(timezone.utc)),
            'job': public_job_status(job).model_dump(mode='json'), 'cancel_requested': job['cancel_requested'], 'result': summary,
            'manifest': proof if view == 'manifest' else None, 'frame': frame, 'replay': replay}
        _need(len(execution.signed.reader._canonical(response)) <= execution.signed.RETURN_MAX)
        return response
