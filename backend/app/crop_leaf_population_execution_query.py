"""Read only published leaf population jobs; never import numerical workers/producers."""
from datetime import datetime, timezone
from contextlib import nullcontext
from functools import wraps
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from psycopg import sql

from . import crop_leaf_population_execution as execution
from . import crop_leaf_population_execution_result as result
from .api_contracts import public_job_status


VERSION = 'leaf-population-execution-read-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
WORKER_SHA256 = sha256(Path(__file__).with_name('crop_leaf_population_execution_worker.py').read_bytes()).hexdigest()
_FLAGS = dict(execution.signed.FLAGS)


class LeafPopulationExecutionQueryHold(ValueError):
    """No current authorized, unchanged morphology job result is available."""


class LeafPopulationExecutionQueryPending(ValueError):
    """The stored execution changed while this response was being read."""


def _need(condition):
    if not condition:
        raise LeafPopulationExecutionQueryHold('leaf population execution query unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kw):
        try:
            return fn(*args, **kw)
        except (PermissionError, LeafPopulationExecutionQueryPending):
            raise
        except Exception:
            raise LeafPopulationExecutionQueryHold('leaf population execution query unavailable') from None
    return run


class LeafPopulationExecutionQuery:
    @_checked
    def __init__(self, service):
        _need(type(service) is execution.LeafPopulationExecutionService)
        self.service, self.jobs = service, service.jobs
        self._fixed = (service, service.jobs)
        self._binding()

    def _binding(self):
        _need((self.service, self.jobs) == self._fixed and self.jobs is self.service.jobs
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and sha256(Path(__file__).with_name('crop_leaf_population_execution_worker.py').read_bytes()).hexdigest() == WORKER_SHA256
            and VERSION == 'leaf-population-execution-read-v1' and execution.signed.FLAGS == _FLAGS)
        self.service._binding(); result._binding()

    def _guard(self, tenant):
        self._binding(); self.service.authority.farm_binding._guard(tenant, False)
        if not self.jobs._has_scope(tenant, 'metadata') or not self.jobs._has_scope(tenant, 'artifact'):
            raise PermissionError('leaf population execution query access denied')
        self._binding()

    def _bundle(self, tenant, job_id):
        with self.jobs.connect() as conn:
            job = conn.execute(sql.SQL("""SELECT j.*,
                (SELECT COALESCE(jsonb_agg(to_jsonb(x) ORDER BY x.attempt), '[]'::jsonb)
                 FROM (SELECT * FROM {} WHERE tenant_id=j.tenant_id AND job_id=j.job_id
                       ORDER BY attempt LIMIT 2) x) AS _query_publications,
                (SELECT COALESCE(jsonb_agg(to_jsonb(x) ORDER BY x.recorded_at,x.event_id), '[]'::jsonb)
                 FROM (SELECT * FROM {} WHERE tenant_id=j.tenant_id AND job_id=j.job_id
                       AND (kind=%s OR (attempt=j.attempt_count AND kind=ANY(%s)))
                       ORDER BY recorded_at,event_id LIMIT 8) x) AS _query_events,
                (SELECT COALESCE(jsonb_agg(to_jsonb(x)), '[]'::jsonb)
                 FROM (SELECT * FROM {} WHERE tenant_id=j.tenant_id AND job_id=j.job_id
                       AND attempt=j.attempt_count LIMIT 2) x) AS _query_outcomes,
                (SELECT COALESCE(jsonb_agg(to_jsonb(x)), '[]'::jsonb)
                 FROM (SELECT * FROM {} WHERE tenant_id=j.tenant_id AND job_id=j.job_id
                       AND attempt=j.attempt_count LIMIT 1) x) AS _query_invocations
                FROM {} j WHERE j.tenant_id=%s AND j.job_id=%s""").format(
                    self.jobs._table('job_publications'), self.jobs._table('job_events'),
                    self.jobs._table('attempt_outcomes'), self.jobs._table('attempt_invocations'), self.jobs._table('jobs')),
                (result.RESULT_EVENT_KIND, [result.START_EVENT_KIND, 'succeeded', 'hold', 'failed', 'canceled'], tenant, job_id)).fetchone()
        _need(job is not None and job['stage'] == 'simulation')
        pubs, events, outcomes, invocations = (job.pop(name) for name in
            ('_query_publications', '_query_events', '_query_outcomes', '_query_invocations'))
        self.jobs._verified_input(job)
        return job, pubs, events, outcomes, invocations

    def _intent(self, tenant, raw):
        self._binding()
        value = execution._verified_input(self.service.authority, raw, self.service.input_resolver.version)
        request = self.service.authority.farm_binding._request(execution.signed.reader._canonical(value['request']))
        return value, self.service._resolve(tenant, request)

    def _stored(self, tenant, result_sha256, view, index):
        authority = self.service.authority; signed = execution.signed; reader = signed.reader
        original = authority._load(tenant, result_sha256)
        payload, binding_raw, binding, packet = original; root = payload['numerical_root_sha256']
        manifest = reader.read_leaf_population_manifest(authority.directory, authority.access, root)
        signed._linked(manifest, binding, packet['program_raw'])
        common = {**_FLAGS, 'result_sha256': result_sha256, 'numerical_root_sha256': root,
            **{k: payload[k] for k in ('calculated_at', 'parent_job_id', 'parent_result_sha256',
                'parent_numerical_root_sha256', 'parent_calculated_at')},
            'study_id': payload['study_id'], 'revision': payload['revision'], 'farm': binding['request']['farm'],
            'profile_applicability': 'unvalidated_for_registered_crop', 'normalization': 'per_tracked_shoot',
            **{k: payload[k] for k in ('program_sha256', 'source_sha256', 'input_evidence_sha256', 'binding_sha256')}}
        proof = {**common, 'schema_version': 'leaf-population-signed-manifest-v1', 'manifest': manifest}
        frame = replay = None
        if view == 'frame':
            original_frame = reader.read_leaf_population_frame(authority.directory, authority.access, root, index=index)
            frame = {**common, 'schema_version': 'leaf-population-signed-frame-v1', 'frame': original_frame,
                'frame_sha256': sha256(reader._canonical(original_frame)).hexdigest()}
        if view == 'replay':
            replay = {'manifest': proof, 'frames': []}
            for sample_index in range(len(manifest['samples'])):
                replay['frames'].append(reader.read_leaf_population_frame(authority.directory, authority.access, root, index=sample_index))
                _need(len(reader._canonical(replay)) <= signed.RETURN_MAX)
        _need(authority._load(tenant, result_sha256) == original)
        return proof, frame, replay

    def _completed(self, tenant, bundle, value, view, index):
        job, pubs, events, outcomes, invocations = bundle
        _need(len(pubs) == len(outcomes) == 1 and not invocations and job['reason'] is None)
        pub, outcome = pubs[0], outcomes[0]
        raw = self.jobs.read_artifact(tenant, job['job_id']); link = result.read_link(raw, job)
        manifest = result.publication_manifest(job, raw, link['result_sha256'], WORKER_SHA256)
        _need(pub['attempt'] == job['attempt_count'] and pub['decision_id'] is None
            and pub['artifact_sha256'] == manifest['artifact_sha256'] and pub['artifact_size'] == len(raw)
            and pub['manifest'] == manifest and outcome['state'] == 'succeeded' and outcome['reason'] is None
            and outcome['decision_id'] is None and outcome['termination_reason'] == 'leaf_population_completed')
        starts = [e for e in events if e['kind'] == result.START_EVENT_KIND]
        links = [e for e in events if e['kind'] == result.RESULT_EVENT_KIND]
        terminals = [e for e in events if e['kind'] in ('succeeded', 'hold', 'failed', 'canceled')]
        _need(len(starts) == len(links) == len(terminals) == 1
            and links[0]['attempt'] == job['attempt_count'] and links[0]['reason'] == manifest
            and starts[0]['attempt'] == terminals[0]['attempt'] == job['attempt_count']
            and terminals[0]['kind'] == 'succeeded' and terminals[0]['reason'] is None)
        proof, frame, replay = self._stored(tenant, link['result_sha256'], view, index)
        _need(starts[0]['reason'] == {'execution_kind': 'deterministic_leaf_population', 'worker_code_sha256': WORKER_SHA256,
            'input_sha256': job['input_sha256'], 'planned_outputs': len(proof['manifest']['samples'])})
        request = value['request']
        _need(proof['binding_sha256'] == value['farm_binding_sha256']
            and proof['study_id'] == request['study_id'] and proof['revision'] == request['revision']
            and proof['farm'] == request['farm'] and proof['program_sha256'] == request['input']['program_sha256']
            and proof['source_sha256'] == request['input']['source_sha256']
            and proof['input_evidence_sha256'] == request['input']['evidence_sha256']
            and proof['parent_job_id'] == request['parent']['job_id']
            and proof['parent_result_sha256'] == request['parent']['result_sha256']
            and proof['parent_numerical_root_sha256'] == request['parent']['numerical_root_sha256'])
        return proof, frame, replay

    @_checked
    def read(self, tenant, job_id, *, view='status', index=None):
        _need(type(job_id) is str and str(UUID(job_id)) == job_id and view in ('status', 'manifest', 'frame', 'replay'))
        _need((view == 'frame' and type(index) is int and index >= 0) or (view != 'frame' and index is None))
        self._guard(tenant); before = self._bundle(tenant, job_id); job = before[0]
        original = self._intent(tenant, job['input_bytes']); value, packet = original
        farms = self.service.authority.farm_binding.parent_authority.farm_binding.farms
        ref = value['request']['farm']
        scope = (farms.registration_read_scope(tenant, ref['scenario_id'], ref['scenario_revision'],
            ref['registration_sha256']) if farms._registration_read.get() is None else nullcontext())
        with scope:
            proof = frame = replay = current = None
            if job['state'] == 'succeeded':
                proof, frame, replay = self._completed(tenant, before, value, view, index)
            else:
                _need(view == 'status' and not before[1]
                    and not any(e['kind'] in (result.RESULT_EVENT_KIND, 'succeeded') for e in before[2]))
                current = self.service.current_input(tenant, job['input_bytes'])
                _need(current[0] == value and current[2] == packet)
            self._guard(tenant)
            _need(self._intent(tenant, job['input_bytes']) == original)
            if current is not None:
                _need(self.service.current_input(tenant, job['input_bytes']) == current)
            after = self._bundle(tenant, job_id)
            if before != after:
                raise LeafPopulationExecutionQueryPending('leaf population execution changed; retry current read')
            self._guard(tenant)
            summary = None if proof is None else {k: proof[k] for k in ('result_sha256', 'numerical_root_sha256', 'calculated_at',
                'study_id', 'revision', 'farm', 'profile_applicability', 'binding_sha256', 'program_sha256',
                'source_sha256', 'input_evidence_sha256', 'normalization', 'parent_job_id',
                'parent_result_sha256', 'parent_numerical_root_sha256', 'parent_calculated_at')}
            response = {'schema_version': VERSION, **_FLAGS, 'observed_at': execution.signed.parent_signed._stamp(datetime.now(timezone.utc)),
                'job': public_job_status(job).model_dump(mode='json'), 'cancel_requested': job['cancel_requested'], 'result': summary,
                'manifest': proof if view == 'manifest' else None, 'frame': frame, 'replay': replay}
            _need(len(execution.signed.reader._canonical(response)) <= execution.signed.RETURN_MAX)
            return response
