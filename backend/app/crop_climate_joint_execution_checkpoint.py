"""Accept authenticated file checkpoints under the current simulation lease."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4
import json

from psycopg import sql
from psycopg.errors import QueryCanceled
from psycopg.types.json import Jsonb

from . import crop_climate_joint_execution as execution
from . import crop_climate_joint_server_custody as custody

VERSION = 'joint-crop-climate-execution-checkpoint-v1'
EVENT_KIND = 'joint_checkpoint_confirmed_v1'
MAX_BYTES = 8 * 1024
MAX_EVENTS = custody.storage.LIMITS['commits'] + 2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_CONTRACT = (VERSION, EVENT_KIND, MAX_BYTES, MAX_EVENTS, execution.CODE_SHA256)
_FIELDS = frozenset(('version', 'scope', 'G0_G4', 'publication_sequence', 'input_sha256',
    'head_sha256', 'proof_sha256', 'intent_sha256', 'farm_binding_sha256', 'source_sha256',
    'context_sha256', 'time_binding_sha256', 'header_sha256', 'artifact_sha256',
    'custody_code_sha256', 'execution_code_sha256', 'checkpoint_code_sha256',
    'custody_sequence', 'status', 'steps', 'planned_steps', 'counts', 'computed_through_utc'))


class JointCheckpointHold(ValueError):
    pass


class JointCheckpointLeaseLost(JointCheckpointHold):
    pass


def _need(value):
    if not value: raise JointCheckpointHold('joint checkpoint unavailable')


def _integer(value, high):
    _need(type(value) is int and 0 <= value <= high)


def _payload(value):
    _need(type(value) is dict and set(value) == _FIELDS
        and len(custody._canonical(value)) <= MAX_BYTES
        and value['version'] == VERSION and value['scope'] == custody.SCOPE
        and value['G0_G4'] == 'not_assessed'
        and value['custody_code_sha256'] == custody.CODE_SHA256
        and value['execution_code_sha256'] == execution.CODE_SHA256
        and value['checkpoint_code_sha256'] == CODE_SHA256)
    for key in _FIELDS:
        if key.endswith('_sha256'):
            _need(value[key] is None and key == 'artifact_sha256' or custody._digest(value[key]))
    _integer(value['publication_sequence'], MAX_EVENTS)
    _integer(value['custody_sequence'], MAX_EVENTS - 1)
    _need(1 <= value['publication_sequence'] <= value['custody_sequence'] + 1)
    for key in ('steps', 'planned_steps'): _integer(value[key], 2**63 - 1)
    _need(value['steps'] <= value['planned_steps'] and value['planned_steps'] > 0
        and type(value['counts']) is dict and set(value['counts']) == {'samples', 'events'}
        and value['status'] in ('ready', 'yielded', 'completed', 'hold'))
    for n in value['counts'].values(): _integer(n, 2**63 - 1)
    if value['status'] == 'ready': _need(value['computed_through_utc'] is None)
    else: execution.documents._time(value['computed_through_utc'])
    _need((value['artifact_sha256'] is not None) == (value['status'] in ('completed', 'hold')))
    if value['status'] == 'completed': _need(value['steps'] == value['planned_steps'])
    return value


class JointExecutionCheckpointStore:
    def __init__(self, admission, server):
        try:
            _need(type(admission) is execution.JointCropClimateExecutionService
                and type(server) is custody.JointServerCustody
                and server.binding is admission.binding and server.input_resolver is admission.input_resolver)
            self.admission, self.server, self.jobs = admission, server, admission.jobs
            self._fixed = self._pointers(); self._binding()
        except Exception: raise JointCheckpointHold('joint checkpoint authority unavailable') from None

    def _pointers(self):
        return (self.admission, self.admission._pointers(), self.server, self.server._pointers(), self.jobs)

    def _binding(self):
        self.admission._binding(); self.server._binding()
        _need(self._pointers() == self._fixed and self.admission.jobs is self.jobs
            and (VERSION, EVENT_KIND, MAX_BYTES, MAX_EVENTS, execution.CODE_SHA256) == _CONTRACT
            and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)

    def _guard(self, tenant):
        self._binding()
        if not self.jobs._has_scope(tenant, 'simulation_execute'):
            raise PermissionError('joint checkpoint access denied')
        self.admission.binding._guard(tenant, True)
        self._binding()
        if not self.jobs._has_scope(tenant, 'simulation_execute'):
            raise PermissionError('joint checkpoint access denied')

    def _lease(self, conn, tenant, job_id, attempt, token):
        try: row = self.jobs._locked_job(conn, tenant, job_id)
        except QueryCanceled:
            raise custody.JointCustodyPending('joint checkpoint job busy') from None
        if (not self.jobs._owns_live_lease(row, attempt, token) or row['stage'] != 'simulation'
                or row['cancel_requested']):
            raise JointCheckpointLeaseLost('joint checkpoint lease unavailable')
        return row

    def _input(self, tenant, row):
        raw = self.jobs._verified_input(row)
        value = execution.documents._document(raw, max_size=execution.MAX_INPUT_BYTES)
        _need(set(value) == {'input_version', 'request', 'farm_binding', 'farm_binding_sha256', 'input_resolver_version'}
            and value['input_version'] == execution.INPUT_VERSION
            and value['input_resolver_version'] == self.admission.input_resolver.version
            and execution.canonical_input_bytes(value) == raw)
        request_raw = execution.documents._canonical(value['request'])
        self.admission.binding._request(request_raw)
        binding_raw = execution.documents._canonical(value['farm_binding'])
        _need(sha256(binding_raw).hexdigest() == value['farm_binding_sha256']
            and value['farm_binding']['tenant_id'] == tenant
            and value['farm_binding']['request'] == value['request'])
        identity = execution.documents._canonical([value['request']['study_id'], value['request']['revision']])
        _need(row['idempotency_key'] == execution.INPUT_VERSION + ':' +
            sha256(execution.INTENT_DOMAIN + identity).hexdigest())
        return value, request_raw, binding_raw

    def _current(self, tenant, value, request_raw, binding_raw):
        self._guard(tenant)
        directory, evidence = self.admission._resolve(tenant, value['request'])
        self.admission.binding.current(tenant, request_raw, directory, evidence, binding_raw, write=True)
        self._guard(tenant)

    def _history(self, conn, tenant, job):
        rows = conn.execute(sql.SQL('SELECT event_id, attempt, reason, recorded_at FROM {} '
            'WHERE tenant_id=%s AND job_id=%s AND kind=%s LIMIT %s').format(self.jobs._table('job_events')),
            (tenant, job['job_id'], EVENT_KIND, MAX_EVENTS + 1)).fetchall()
        _need(len(rows) <= MAX_EVENTS)
        for row in rows:
            value = _payload(row['reason'])
            _need(value['input_sha256'] == job['input_sha256'] and type(row['attempt']) is int
                and 1 <= row['attempt'] <= job['attempt_count'])
        rows.sort(key=lambda r: r['reason']['publication_sequence'])
        _need([r['reason']['publication_sequence'] for r in rows] == list(range(1, len(rows) + 1))
            and len({r['reason']['head_sha256'] for r in rows}) == len(rows))
        for a, b in zip(rows, rows[1:]):
            _need(a['attempt'] <= b['attempt'] and a['reason']['custody_sequence'] < b['reason']['custody_sequence'])
        return rows[-1] if rows else None

    @contextmanager
    def _session(self, tenant, request_raw):
        error = None
        with self.server._open(tenant, request_raw, False) as opened:
            try: yield opened[0]
            except (JointCheckpointHold, custody.JointCustodyPending) as exc: error = exc
        if error is not None: raise error

    def _snapshot(self, session, progress, sequence, input_sha):
        value = json.loads(progress); head, digest, _ = session._load(); proof, proof_sha = session._proof(head)
        _need(digest == value['head_sha256'] and proof_sha == value['proof_sha256'])
        packet = {'version': VERSION, 'scope': custody.SCOPE, 'G0_G4': 'not_assessed',
            'publication_sequence': sequence, 'input_sha256': input_sha,
            **{k: value[k] for k in ('head_sha256', 'proof_sha256', 'intent_sha256',
                'source_sha256', 'context_sha256', 'time_binding_sha256', 'header_sha256',
                'artifact_sha256', 'custody_code_sha256', 'status', 'steps', 'planned_steps', 'counts')},
            'farm_binding_sha256': value['binding_sha256'], 'execution_code_sha256': execution.CODE_SHA256,
            'checkpoint_code_sha256': CODE_SHA256, 'custody_sequence': proof['sequence'],
            'computed_through_utc': None if value['times'] is None else value['times']['last_confirmed']['at']}
        return _payload(packet), proof

    def _descendant(self, session, previous, value, proof):
        if previous is None: return
        old = previous['reason']; p, digest = proof, value['proof_sha256']
        for _ in range(MAX_EVENTS):
            if p['sequence'] == old['custody_sequence']:
                _need(custody._head(p['head']) == old['head_sha256'] and digest == old['proof_sha256'])
                _need(old['steps'] <= value['steps'] and all(old['counts'][k] <= value['counts'][k] for k in old['counts']))
                return
            _need(p['sequence'] > old['custody_sequence'] and p['parent'] is not None)
            raw = custody.files._read(session.proofs, p['parent']['head_sha256'] + '.json', custody.LIMITS['proof_bytes'])
            parent = custody._checked(raw, self.server.integrity_key, custody.PROOF_DOMAIN, custody.LIMITS['proof_bytes'])
            _need(sha256(raw).hexdigest() == p['parent']['proof_sha256']
                and custody._head(parent['head']) == p['parent']['head_sha256']
                and parent['sequence'] == p['sequence'] - 1)
            p, digest = session._proof(parent['head'])
        raise JointCheckpointHold('joint checkpoint ancestry unavailable')

    @staticmethod
    def _record(row, job_id):
        return {'event_id': str(row['event_id']), 'job_id': str(job_id), 'attempt': row['attempt'],
            'recorded_at': row['recorded_at'].astimezone(timezone.utc), 'checkpoint': deepcopy(row['reason'])}

    def confirm(self, tenant, job_id, *, attempt, lease_token):
        try:
            _need(type(job_id) is str and str(UUID(job_id)) == job_id
                and type(attempt) is int and 1 <= attempt <= 3
                and type(lease_token) is str and 1 <= len(lease_token) <= 200)
            self._guard(tenant)
            with self.jobs.connect() as conn:
                job = self._lease(conn, tenant, job_id, attempt, lease_token)
                value, request_raw, binding_raw = self._input(tenant, job)
                self._current(tenant, value, request_raw, binding_raw)
                with self._session(tenant, request_raw) as session:
                    _need(session.binding_raw == binding_raw)
                    progress = session.progress(); previous = self._history(conn, tenant, job)
                    duplicate = previous is not None and previous['reason']['head_sha256'] == json.loads(progress)['head_sha256']
                    sequence = (previous['reason']['publication_sequence'] + int(not duplicate)) if previous else 1
                    packet, proof = self._snapshot(session, progress, sequence, job['input_sha256'])
                    self._descendant(session, previous, packet, proof)
                    self._lease(conn, tenant, job_id, attempt, lease_token)
                    if duplicate:
                        _need(custody._canonical(previous['reason']) == custody._canonical(packet))
                        row = previous
                    else:
                        row = conn.execute(sql.SQL('INSERT INTO {} '
                            '(tenant_id,job_id,event_id,attempt,kind,reason) VALUES (%s,%s,%s,%s,%s,%s) '
                            'RETURNING event_id,attempt,reason,recorded_at').format(self.jobs._table('job_events')),
                            (tenant, job_id, uuid4(), attempt, EVENT_KIND, Jsonb(packet))).fetchone()
                    self._current(tenant, value, request_raw, binding_raw)
                    _need(session.progress() == progress)
                    self._lease(conn, tenant, job_id, attempt, lease_token)
                    result = self._record(row, job_id)
            return result
        except PermissionError: raise PermissionError('joint checkpoint access denied') from None
        except (JointCheckpointLeaseLost, custody.JointCustodyPending): raise
        except Exception: raise JointCheckpointHold('joint checkpoint unavailable') from None
