"""Read confirmed joint job progress without calculating or accepting checkpoints."""
from copy import deepcopy
from contextlib import contextmanager, ExitStack, nullcontext
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID
import json
import os

from psycopg import sql

from . import crop_greenhouse_solar_execution_worker as worker
from . import api_contracts as jobs_public
from . import api_crop_greenhouse_solar_replay as public
from . import api_crop_greenhouse_solar_execution as wire
from .runtime_roles import RolePolicyHold

checkpoints = worker.checkpoints
storage = worker.results
custody = checkpoints.custody
VERSION = wire.VERSION
MAX_RESPONSE_BYTES = wire.MAX_RESPONSE_BYTES
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES = {'worker': worker, 'job_projection': jobs_public, 'joint_projection': public, 'execution_projection': wire}
_DEPENDENCIES = {k: sha256(Path(m.__file__).read_bytes()).hexdigest() for k, m in _MODULES.items()}
_FIXED = (VERSION, MAX_RESPONSE_BYTES, CODE_SHA256, storage._canonical(_DEPENDENCIES))
ExecutionCounts = wire.SolarExecutionCounts
ExecutionCheckpoint = wire.SolarExecutionCheckpoint
ExecutionResult = wire.SolarExecutionResult
ExecutionRead = wire.SolarExecutionRead


class SolarExecutionQueryHold(ValueError):
    pass


class SolarExecutionQueryPending(ValueError):
    pass


def _need(value):
    if not value: raise SolarExecutionQueryHold('solar execution query unavailable')


def _utc(value):
    _need(type(value) is datetime and value.tzinfo is not None)
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _same(left, right):
    if type(left) is not type(right): return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    if type(left) in (tuple, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


class SolarExecutionQuery:
    def __init__(self, checkpoint_store, result_store):
        try:
            _need(type(checkpoint_store) is checkpoints.SolarExecutionCheckpointStore
                and type(result_store) is storage.SolarResultStore
                and checkpoint_store.jobs is result_store.jobs and checkpoint_store.server is result_store.server)
            self.checkpoints, self.results = checkpoint_store, result_store
            self.jobs, self.server = checkpoint_store.jobs, checkpoint_store.server
            self._fixed = self._pointers(); self._binding()
        except Exception: raise SolarExecutionQueryHold('solar execution query authority unavailable') from None

    def _pointers(self):
        return (self.checkpoints, self.checkpoints._pointers(), self.results,
                self.results._pointers(), self.jobs, self.server)

    def _binding(self):
        _need(self._pointers() == self._fixed
            and (VERSION, MAX_RESPONSE_BYTES, CODE_SHA256, storage._canonical(_DEPENDENCIES)) == _FIXED
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and {k: sha256(Path(m.__file__).read_bytes()).hexdigest() for k, m in _MODULES.items()} == _DEPENDENCIES)
        _need(wire.MAX_CHECKPOINT_EVENTS == checkpoints.MAX_EVENTS
            and wire.INPUT_VERSION == checkpoints.execution.INPUT_VERSION
            and wire.SOURCE_VERSION == custody.farms.evidence.SOURCE_VERSION
            and wire.RIGHTS_VERSION == custody.farms.RIGHTS_VERSION)
        _need(set(wire.SolarExecutionResultFarm.model_fields) == set(public.Farm.model_fields))
        self.checkpoints._binding(); self.results._binding()

    def _guard(self, tenant):
        self._binding(); self.results._guard(tenant)
        if not self.jobs._has_scope(tenant, 'metadata'):
            raise PermissionError('solar execution query access denied')
        self._binding()

    def _current(self, tenant, value, raw, binding_raw):
        self._guard(tenant)
        directory, evidence = self.checkpoints.admission._resolve(tenant, value['request'])
        farms = self.server.binding.farms
        ref = value['request']['farm']
        scope = (farms.registration_read_scope(tenant, ref['scenario_id'], ref['scenario_revision'],
            ref['registration_sha256']) if farms._registration_read.get() is None else nullcontext())
        with scope:
            self.server.binding.current(tenant, raw, directory, evidence, binding_raw, write=False)
        self._guard(tenant)

    def _bundle(self, conn, tenant, job_id):
        job = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(self.jobs._table('jobs')), (tenant, job_id)).fetchone()
        if job is None: return None
        if (job['stage'] != 'simulation' or
                json.loads(self.jobs._verified_input(job)).get('input_version') != checkpoints.execution.INPUT_VERSION):
            return None
        latest = self.checkpoints._history(conn, tenant, job)
        links = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND kind=%s LIMIT 2')
            .format(self.jobs._table('job_events')), (tenant, job_id, worker.RESULT_EVENT_KIND)).fetchall()
        pubs = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s LIMIT 2')
            .format(self.jobs._table('job_publications')), (tenant, job_id)).fetchall()
        outcomes = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s ORDER BY attempt LIMIT 4')
            .format(self.jobs._table('attempt_outcomes')), (tenant, job_id)).fetchall()
        terminal = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s '
            "AND kind IN ('succeeded','hold','failed','canceled') LIMIT 2").format(self.jobs._table('job_events')),
            (tenant, job_id, job['attempt_count'])).fetchall()
        return job, latest, links, pubs, outcomes, terminal

    def _capture_checkpoint(self, tenant, raw, binding_raw, job, latest, retained):
        root = custody.files.job_store._open_directory_nofollow(self.server.directory)
        try: exists = custody.files._exists(root, custody._intent_id(tenant, json.loads(raw)))
        finally: os.close(root)
        if not exists:
            _need(latest is None)
            return 'none', None, None, None, ()
        with ExitStack() as opened:
            try: session, _ = opened.enter_context(self.results._session(tenant, raw))
            except custody.SolarCustodyPending:
                return 'unavailable', None, None, None, ()
            _need(session.binding_raw == binding_raw)
            if not custody.files._exists(session.artifact, 'HEAD'):
                _need(latest is None)
                return 'none', None, None, None, ()
            sequence = latest['reason']['publication_sequence'] if latest else 1
            progress = session.progress()
            snapshot, proof = self.checkpoints._snapshot(session, progress, sequence, job['input_sha256'])
            self.checkpoints._descendant(session, latest, snapshot, proof)
            if latest is None or snapshot['head_sha256'] != latest['reason']['head_sha256']:
                return 'unavailable', None, None, None, ()
            _need(snapshot == latest['reason'])
            selected = {k: snapshot[k] for k in ('head_sha256', 'proof_sha256', 'artifact_sha256',
                'status', 'steps', 'planned_steps', 'counts', 'computed_through_utc', 'publication_sequence',
                'provenance_sha256', 'rights_or_gate_approval')}
            selected['checkpoint_recorded_at'] = _utc(latest['recorded_at'])
            directories = []
            for descriptor in (session.root, session.intent, session.proofs, session.artifact):
                witness = os.dup(descriptor)
                retained.callback(os.close, witness)
                info = os.fstat(witness)
                directories.append((witness, info.st_dev, info.st_ino))
            return 'current', selected, progress, snapshot, tuple(directories)

    @contextmanager
    def _checkpoint(self, tenant, raw, binding_raw, job, latest):
        with ExitStack() as retained:
            status, selected, progress, snapshot, directories = self._capture_checkpoint(
                tenant, raw, binding_raw, job, latest, retained)
            yield status, selected
            if status != 'current':
                return
            try:
                with self.results._session(tenant, raw) as (session, _):
                    _need(session.binding_raw == binding_raw)
                    for (_, device, inode), descriptor in zip(directories,
                            (session.root, session.intent, session.proofs, session.artifact), strict=True):
                        info = os.fstat(descriptor)
                        _need((info.st_dev, info.st_ino) == (device, inode))
                    current = session.progress()
                    if current != progress:
                        after, proof = self.checkpoints._snapshot(session, current,
                            snapshot['publication_sequence'], job['input_sha256'])
                        self.checkpoints._descendant(session, {'reason':snapshot}, after, proof)
                        raise SolarExecutionQueryPending('solar checkpoint advanced during read')
            except custody.SolarCustodyPending:
                raise SolarExecutionQueryPending('solar checkpoint busy during response') from None

    def _terminal(self, conn, tenant, value, binding_raw, bundle):
        job, latest, links, pubs, outcomes, terminal = bundle
        _need(len(links) <= 1 and len(pubs) <= 1 and len(outcomes) <= 3 and len(terminal) <= 1)
        numeric = job['state'] == 'succeeded' or (job['state'] == 'hold' and job['reason'] == {'code': 'solar_numerical_hold', 'kind': 'hold'})
        if not numeric:
            _need(not links and not pubs)
            return None, None
        _need(latest is not None and len(links) == len(terminal) == 1)
        state = job['state']; status = 'completed' if state == 'succeeded' else 'hold'
        code = 'completed' if state == 'succeeded' else 'solar_numerical_hold'
        reason = None if state == 'succeeded' else {'code': code, 'kind': 'hold'}
        _need(job['reason'] == reason and terminal[0]['kind'] == state and terminal[0]['reason'] == reason)
        current = [o for o in outcomes if o['attempt'] == job['attempt_count']]
        _need(len(current) == 1 and current[0]['state'] == state and current[0]['reason'] == reason
            and current[0]['termination_reason'] == code and current[0]['decision_id'] is None)
        link = links[0]['reason']
        _need(type(link) is dict and type(link.get('result_id')) is str)
        row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
            .format(self.jobs._table(storage.schema.TABLE)), (tenant, link['result_id'])).fetchone()
        packet = self.results._row(row, tenant, value['request']['farm'])
        progress = packet['policies']['server_progress']; checkpoint = latest['reason']
        fields = ('head_sha256', 'proof_sha256', 'artifact_sha256', 'intent_sha256',
            'context_sha256', 'time_binding_sha256', 'header_sha256', 'source_sha256',
            'custody_code_sha256', 'provenance_sha256', 'rights_or_gate_approval', 'steps', 'planned_steps', 'counts', 'status')
        _need(storage._canonical(packet['binding']) == binding_raw and progress['status'] == status
            and packet['policies']['resolver_version'] == self.server.input_resolver.version
            and all(progress[k] == checkpoint[k] for k in fields)
            and progress['times']['last_confirmed']['at'] == checkpoint['computed_through_utc'])
        expected = {'schema_version': '1', 'publication_version': worker.VERSION,
            'result_link_version': worker.RESULT_LINK_VERSION, 'status': status,
            'job_id': str(job['job_id']), 'stage': 'simulation', 'attempt': job['attempt_count'],
            'input_sha256': job['input_sha256'], 'result_id': row['result_id'],
            'artifact_sha256': row['payload_sha256'], 'artifact_size': len(row['payload_raw']),
            'root_sha256': progress['artifact_sha256'], 'head_sha256': progress['head_sha256'],
            'proof_sha256': progress['proof_sha256'], 'checkpoint_event_id': str(latest['event_id']),
            'worker_code_sha256': worker.CODE_SHA256, 'scope': custody.SCOPE, 'G0_G4': 'not_assessed',
            'provenance_sha256': progress['provenance_sha256'], 'rights_or_gate_approval': False}
        _need(storage._canonical(link) == storage._canonical(expected)
            and links[0]['attempt'] == job['attempt_count'] and len(storage._canonical(link)) <= checkpoints.MAX_BYTES)
        if state == 'succeeded':
            _need(len(pubs) == 1 and storage._canonical(pubs[0]['manifest']) == storage._canonical(expected) and pubs[0]['attempt'] == job['attempt_count']
                and pubs[0]['artifact_sha256'] == row['payload_sha256'] and pubs[0]['artifact_size'] == len(row['payload_raw'])
                and pubs[0]['decision_id'] is None)
        else: _need(not pubs)
        farm = {k: packet['farm'][k] for k in public.Farm.model_fields}
        return {'result_id': row['result_id'], 'farm': farm, 'status': status,
            'provenance_sha256': progress['provenance_sha256'], 'rights_or_gate_approval': False}, deepcopy(row)

    def read(self, tenant, job_id):
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except Exception: raise ValueError('solar execution query request rejected') from None
        try:
            self._guard(tenant)
            with self.jobs.connect() as conn:
                conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                bundle = self._bundle(conn, tenant, job_id)
                if bundle is None:
                    self._guard(tenant); return None
                job, latest = bundle[:2]
                if job['stage'] != 'simulation' or json.loads(self.jobs._verified_input(job)).get('input_version') != checkpoints.execution.INPUT_VERSION:
                    self._guard(tenant); return None
                value, raw, binding_raw = self.checkpoints._input(tenant, job)
                self._current(tenant, value, raw, binding_raw)
                if latest:
                    p = latest['reason']; source = value['request']['input']
                    _need(p['farm_binding_sha256'] == value['farm_binding_sha256']
                        and all(p[k] == source[k] for k in ('source_sha256', 'context_sha256', 'time_binding_sha256')))
                with self._checkpoint(tenant, raw, binding_raw, job, latest) as (status, checkpoint):
                    result, registered = self._terminal(conn, tenant, value, binding_raw, bundle)
                    self._current(tenant, value, raw, binding_raw)
                    with self.jobs.connect() as probe:
                        probe.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                        if not _same(self._bundle(probe, tenant, job_id), bundle):
                            raise SolarExecutionQueryPending('solar execution changed during read')
                        if registered is not None:
                            current = probe.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
                                .format(self.jobs._table(storage.schema.TABLE)), (tenant, registered['result_id'])).fetchone()
                            _need(_same(current, registered))
                        observed = probe.execute('SELECT clock_timestamp() AS observed_at').fetchone()['observed_at']
                    self._current(tenant, value, raw, binding_raw)
                    data = ExecutionRead.model_validate({'version': VERSION, 'scope': custody.SCOPE, 'G0_G4': 'not_assessed',
                        'rights_or_gate_approval': False, 'job': jobs_public.public_job_status(job), 'cancel_requested': job['cancel_requested'],
                        'observed_at': _utc(observed), 'checkpoint_status': status, 'checkpoint': checkpoint,
                        'result': result if status == 'current' else None})
                    wire = storage._canonical(data.model_dump(mode='json'))
                    _need(1 <= len(wire) <= MAX_RESPONSE_BYTES)
            self._current(tenant, value, raw, binding_raw)
            return wire
        except custody.SolarCustodyPending:
            raise SolarExecutionQueryPending('solar checkpoint busy during read') from None
        except (PermissionError, RolePolicyHold, SolarExecutionQueryPending): raise
        except Exception: raise SolarExecutionQueryHold('solar execution query unavailable') from None
