"""Immutable DB references to authenticated, currently permitted joint results."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import hmac
import json
from pathlib import Path
from uuid import UUID

from psycopg import sql

from . import crop_climate_joint_result_schema as schema
from . import crop_climate_joint_server_custody as server
from . import runtime_roles
from .crop_result_store import _name
from .thermal_run_store import _canonical, _document, _time

farms = server.farms
artifact = server.storage
VERSION = schema.VERSION
MAX_PACKET_BYTES = schema.MAX_METADATA_BYTES
DOMAIN = b'ossf-joint-crop-climate-result-v1\0'
LOCK_DOMAIN = b'ossf-joint-crop-climate-result-lock-v1\0'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SCHEMA_SHA256 = sha256(Path(schema.__file__).read_bytes()).hexdigest()
ROLE_SHA256 = sha256(Path(runtime_roles.__file__).read_bytes()).hexdigest()
CODE = {'storage_code_sha256': CODE_SHA256, 'schema_code_sha256': SCHEMA_SHA256,
    'runtime_roles_code_sha256': ROLE_SHA256, 'server_custody_code_sha256': server.CODE_SHA256,
    'server_dependency_sha256': server.DEPENDENCY_SHA256}
_CODE_RAW = _canonical(CODE)
_DECLARATIONS_RAW = _canonical([VERSION, MAX_PACKET_BYTES, DOMAIN.hex(), LOCK_DOMAIN.hex(),
    schema.VERSION, schema.TABLE, schema.FARM_KEYS, schema.INPUT_KEYS,
    schema.ARTIFACT_STRINGS, schema.COUNTER_BOUNDS, artifact.VERSION])


def _need(condition):
    if not condition: raise server.JointCustodyHold('joint research result unavailable')


def _closed(value, keys): _need(type(value) is dict and set(value) == set(keys))


def _integer(value, low, high): _need(type(value) is int and low <= value <= high)


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
        and sha256(Path(schema.__file__).read_bytes()).hexdigest() == SCHEMA_SHA256
        and sha256(Path(runtime_roles.__file__).read_bytes()).hexdigest() == ROLE_SHA256
        and _canonical(CODE) == _CODE_RAW
        and _canonical([VERSION, MAX_PACKET_BYTES, DOMAIN.hex(), LOCK_DOMAIN.hex(),
            schema.VERSION, schema.TABLE, schema.FARM_KEYS, schema.INPUT_KEYS,
            schema.ARTIFACT_STRINGS, schema.COUNTER_BOUNDS, artifact.VERSION]) == _DECLARATIONS_RAW)
    server._pins()


def _lock_key(tenant, study, revision):
    return int.from_bytes(sha256(LOCK_DOMAIN + _canonical([tenant, study, revision])).digest()[:8],
                          'big', signed=True)


def _progress(value):
    _closed(value, ('version', 'scope', 'G0_G4', 'intent_sha256', 'binding_sha256',
        'source_sha256', 'context_sha256', 'time_binding_sha256', 'custody_code_sha256',
        'head_sha256', 'proof_sha256', 'header_sha256', 'artifact_sha256', 'status',
        'commit_count', 'steps', 'planned_steps', 'counts', 'checkpoint', 'last_confirmed',
        'hold', 'times', 'storage_bytes', 'file_count'))
    _need(value['version'] == server.VERSION and value['scope'] == server.SCOPE
        and value['G0_G4'] == 'not_assessed' and value['custody_code_sha256'] == server.CODE_SHA256
        and value['status'] in ('completed', 'hold'))
    for key in ('intent_sha256', 'binding_sha256', 'source_sha256', 'context_sha256',
            'time_binding_sha256', 'custody_code_sha256', 'head_sha256', 'proof_sha256',
            'header_sha256', 'artifact_sha256'):
        _need(server._digest(value[key]))
    _closed(value['counts'], ('samples', 'events'))
    result = {'ref': artifact.VERSION + ':' + value['artifact_sha256'],
        'sha256': value['artifact_sha256'], 'header_sha256': value['header_sha256'],
        'status': value['status'], 'intent_sha256': value['intent_sha256'],
        'farm_binding_sha256': value['binding_sha256'], 'head_sha256': value['head_sha256'],
        'proof_sha256': value['proof_sha256'], 'sample_count': value['counts']['samples'],
        'event_count': value['counts']['events'],
        **{k: value[k] for k in ('steps', 'planned_steps', 'commit_count', 'storage_bytes', 'file_count')}}
    for key, bounds in schema.COUNTER_BOUNDS.items(): _integer(result[key], *bounds)
    _need(result['steps'] <= result['planned_steps']
        and (result['status'] != 'completed' or result['steps'] == result['planned_steps']))
    return result


def _packet(binding_raw, progress_raw, resolver_version):
    binding = json.loads(binding_raw); request = binding['request']; registration = binding['registration']
    source = binding['input']; crop = registration['crop']
    value = {'schema_version': VERSION, 'status': 'stored_unpublished_research',
        'claim_scope': server.SCOPE, 'G0_G4': 'not_assessed', 'tenant_id': binding['tenant_id'],
        'study_id': request['study_id'], 'revision': request['revision'],
        'farm': {'scenario_id': request['farm']['scenario_id'],
            'scenario_revision': request['farm']['scenario_revision'],
            **{k: registration[k] for k in ('registration_job_id', 'registration_sha256', 'zone_id')},
            'crop_id': crop['crop_id'], 'batch_id': crop['batch_id']},
        'input': {**{k: source[k] for k in schema.INPUT_KEYS if k not in ('start_utc', 'end_utc')},
            'start_utc': source['period']['start'], 'end_utc': source['period']['end']},
        'artifact': _progress(json.loads(progress_raw)), 'binding': binding,
        'policies': {'input_rights_version': binding['rights_policy_version'],
            'resolver_version': resolver_version, 'server_progress': json.loads(progress_raw)}, 'code': CODE}
    value['result_id'] = VERSION + ':' + sha256(_canonical(value)).hexdigest()
    raw = _canonical(value); _decode(raw); return raw


def _decode(raw):
    try:
        _pins(); value = _document(raw, max_size=MAX_PACKET_BYTES)
        _closed(value, ('schema_version', 'status', 'claim_scope', 'G0_G4', 'result_id',
            'tenant_id', 'study_id', 'revision', 'farm', 'input', 'artifact', 'binding', 'policies', 'code'))
        _need(value['schema_version'] == VERSION and value['status'] == 'stored_unpublished_research'
            and value['claim_scope'] == server.SCOPE and value['G0_G4'] == 'not_assessed' and value['code'] == CODE)
        _closed(value['farm'], schema.FARM_KEYS); _closed(value['input'], schema.INPUT_KEYS)
        binding = value['binding']
        _closed(binding, ('version', 'scope', 'G0_G4', 'tenant_id', 'request', 'registration',
            'input', 'rights_policy_version', 'binding_code_sha256', 'binding_dependency_sha256'))
        _need(binding['version'] == farms.VERSION and binding['scope'] == server.SCOPE
            and binding['G0_G4'] == 'not_assessed' and binding['binding_code_sha256'] == farms.CODE_SHA256
            and binding['binding_dependency_sha256'] == farms.DEPENDENCY_SHA256)
        request = binding['request']; registration = binding['registration']; source = binding['input']
        _closed(request, ('study_id', 'revision', 'farm', 'input', 'rights'))
        _closed(registration, ('registration_job_id', 'registration_sha256', 'farm_sha256',
            'source_binding_sha256', 'crop', 'zone_id', 'normalization', 'floor_area', 'profile_applicability'))
        _closed(source, ('source_sha256', 'program_id', 'period', 'context_sha256', 'time_binding_sha256',
            'evidence_sha256', 'initial_state_sha256', 'model_identity', 'review', 'normalization_version',
            'qc_version', 'input_evidence_version'))
        _closed(source['period'], ('start', 'end'))
        _need(source['normalization_version'] == farms.evidence.NORMALIZATION_VERSION
            and source['qc_version'] == farms.evidence.QC_VERSION
            and source['input_evidence_version'] == farms.evidence.VERSION
            and registration['normalization'] == 'per_m2_floor'
            and registration['profile_applicability'] == 'unvalidated_for_registered_crop')
        _need(all(_name(value[k]) and value[k] == v for k, v in (
            ('tenant_id', binding['tenant_id']), ('study_id', request['study_id']), ('revision', request['revision']))))
        farm = value['farm']; crop = registration['crop']
        _need(farm == {'scenario_id': request['farm']['scenario_id'],
            'scenario_revision': request['farm']['scenario_revision'],
            **{k: registration[k] for k in ('registration_job_id', 'registration_sha256', 'zone_id')},
            'crop_id': crop['crop_id'], 'batch_id': crop['batch_id']}
            and farm['crop_id'] == request['farm']['crop_id']
            and farm['registration_sha256'] == request['farm']['registration_sha256']
            and str(UUID(farm['registration_job_id'])) == farm['registration_job_id'])
        _need(value['input'] == {**{k: source[k] for k in schema.INPUT_KEYS if k not in ('start_utc', 'end_utc')},
            'start_utc': source['period']['start'], 'end_utc': source['period']['end']})
        for key in ('source_sha256', 'context_sha256', 'time_binding_sha256', 'evidence_sha256'):
            _need(server._digest(source[key]) and source[key] == request['input'][key])
        _need(request['input']['schema_version'] == farms.evidence.SOURCE_VERSION
            and _name(source['program_id']) and source['program_id'] == request['input']['program_id'])
        start, end = (_time(value['input'][k]) for k in ('start_utc', 'end_utc'))
        _need(all(type(value['input'][k]) is str and len(value['input'][k]) == 27
            for k in ('start_utc', 'end_utc')) and 0 < (end-start).total_seconds() <= 600)
        _closed(value['policies'], ('input_rights_version', 'resolver_version', 'server_progress'))
        policies = value['policies']; progress = policies['server_progress']
        _need(policies['input_rights_version'] == binding['rights_policy_version']
            and _name(policies['input_rights_version']) and _name(policies['resolver_version'])
            and value['artifact'] == _progress(progress)
            and progress['binding_sha256'] == sha256(_canonical(binding)).hexdigest()
            and all(progress[k] == source[k] for k in ('source_sha256', 'context_sha256', 'time_binding_sha256')))
        _need(value['result_id'] == VERSION + ':' + sha256(_canonical(
            {k: v for k, v in value.items() if k != 'result_id'})).hexdigest())
        return value
    except server.JointCustodyHold: raise
    except Exception: raise server.JointCustodyHold('joint research result unavailable') from None


class JointCropClimateResultStore:
    def __init__(self, custody, *, integrity_key):
        try:
            _need(type(custody) is server.JointServerCustody and type(integrity_key) is bytes
                and 32 <= len(integrity_key) <= 4096 and integrity_key != custody.integrity_key)
            self.server, self.jobs, self.integrity_key = custody, custody.binding.jobs, integrity_key
            self._fixed = self._pointers(); self._binding()
        except Exception: raise server.JointCustodyHold('joint research authority unavailable') from None

    def _pointers(self):
        return (self.server, self.server._pointers(), self.server.binding, self.jobs, self.integrity_key,
            self.jobs._dsn, self.jobs.schema, self.jobs.runtime_identity, self.jobs.audit_runtime_grants)

    def _binding(self):
        _pins(); _need(self._pointers() == self._fixed and self.jobs is self.server.binding.jobs)
        self.server._binding()
        _need(self.jobs.runtime_identity[0].crop_climate_joint_result_storage is True)

    def _guard(self, tenant, write=False):
        self._binding(); self.server.binding._guard(tenant, write)

    def _signature(self, raw): return hmac.new(self.integrity_key, DOMAIN + raw, 'sha256').hexdigest()

    def _columns(self, packet):
        return {**{k: packet[k] for k in ('tenant_id', 'study_id', 'revision', 'result_id')},
            **packet['farm'], **packet['input'],
            **{column: packet['artifact'][key] for key, column in schema.ARTIFACT_STRINGS.items()},
            **{k: packet['artifact'][k] for k in schema.COUNTER_BOUNDS},
            'registered_by': self.jobs.runtime_identity[0].roles['authority']}

    def _find(self, tenant, *, result_id=None, study_id=None, revision=None):
        with self.jobs.connect() as conn:
            table = self.jobs._table(schema.TABLE)
            if result_id is not None:
                return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
                    .format(table), (tenant, result_id)).fetchone()
            return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                .format(table), (tenant, study_id, revision)).fetchone()

    def _row(self, row, tenant, farm_ref):
        _need(row is not None and row['tenant_id'] == tenant and type(row['payload_raw']) is bytes
            and row['payload_sha256'] == sha256(row['payload_raw']).hexdigest()
            and type(row['integrity_signature']) is str
            and hmac.compare_digest(row['integrity_signature'], self._signature(row['payload_raw'])))
        packet = _decode(row['payload_raw'])
        request = self.server.binding._request(_canonical(packet['binding']['request']))
        _need(packet['tenant_id'] == tenant and request['farm'] == farm_ref
            and all(str(row[k]) == v if k == 'registration_job_id' else row[k] == v
                for k, v in self._columns(packet).items()))
        return packet

    @staticmethod
    def _record(row): return {k: row[k] for k in ('result_id', 'payload_raw', 'payload_sha256', 'recorded_at')}

    def _current(self, tenant, request_raw, session, progress_raw, *, write=False):
        self._guard(tenant, write)
        if write:
            request = self.server.binding._request(request_raw)
            directory, receipt = self.server.input_resolver(tenant, request['input']['source_sha256'],
                request['input']['evidence_sha256'])
            self.server.binding.current(tenant, request_raw, directory, receipt, session.binding_raw, write=True)
        _need(session.progress() == progress_raw)

    @contextmanager
    def _session(self, tenant, request_raw):
        pending = None
        with self.server._open(tenant, request_raw, False) as opened:
            try: yield opened
            except server.JointCustodyPending as exc: pending = exc
        if pending is not None: raise pending

    def put(self, tenant, request_raw):
        try:
            self._guard(tenant, True); request = self.server.binding._request(request_raw)
            with self._session(tenant, request_raw) as (session, _):
                progress = session.progress(); self._current(tenant, request_raw, session, progress, write=True)
                payload = _packet(session.binding_raw, progress, self.server.input_resolver.version)
                packet = _decode(payload)
                with self.jobs.connect() as conn:
                    acquired = conn.execute('SELECT pg_try_advisory_xact_lock(%s) AS acquired',
                        (_lock_key(tenant, request['study_id'], request['revision']),)).fetchone()['acquired']
                    if not acquired: raise server.JointCustodyPending('joint research registration busy')
                    values = {**self._columns(packet), 'payload_raw': payload,
                        'payload_sha256': sha256(payload).hexdigest(), 'integrity_signature': self._signature(payload)}
                    table = self.jobs._table(schema.TABLE)
                    conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING').format(table,
                        sql.SQL(',').join(map(sql.Identifier, values)),
                        sql.SQL(',').join(sql.Placeholder() for _ in values)), tuple(values.values()))
                    row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                        .format(table), (tenant, request['study_id'], request['revision'])).fetchone()
                    if row is None: raise server.JointCustodyConflict('joint research revision conflict')
                    self._row(row, tenant, request['farm'])
                    if row['payload_raw'] != payload: raise server.JointCustodyConflict('joint research revision conflict')
                    self._current(tenant, request_raw, session, progress, write=True)
                self._current(tenant, request_raw, session, progress, write=True)
                return self._record(row)
        except (PermissionError, server.JointCustodyConflict, server.JointCustodyPending): raise
        except Exception: raise server.JointCustodyHold('joint research registration unavailable') from None

    @contextmanager
    def _read(self, tenant, result_id, farm_ref):
        self._guard(tenant)
        _need(type(result_id) is str and result_id.startswith(VERSION + ':')
            and server._digest(result_id[len(VERSION)+1:]))
        row = self._find(tenant, result_id=result_id)
        if row is None:
            self._guard(tenant); yield None, None, None; return
        packet = self._row(row, tenant, farm_ref); request_raw = _canonical(packet['binding']['request'])
        with self.server._open(tenant, request_raw, False) as (session, _):
            _need(session.binding_raw == _canonical(packet['binding'])
                and packet['policies']['resolver_version'] == self.server.input_resolver.version)
            expected = server._canonical(packet['policies']['server_progress'])
            self._current(tenant, request_raw, session, expected)
            yield row, packet, session
            self._current(tenant, request_raw, session, expected)

    def get(self, tenant, result_id, farm_ref):
        try:
            with self._read(tenant, result_id, farm_ref) as (row, _, _):
                return None if row is None else self._record(row)
        except (PermissionError, server.JointCustodyConflict, server.JointCustodyPending): raise
        except Exception: raise server.JointCustodyHold('joint research read unavailable') from None

    def page(self, tenant, result_id, farm_ref, kind, start=0, limit=None):
        try:
            with self._read(tenant, result_id, farm_ref) as (row, packet, session):
                if row is None: return None
                with artifact.open_artifact(session.path, packet['artifact']['sha256']) as reader:
                    return reader.page(kind, start=start, limit=limit)
        except (PermissionError, server.JointCustodyConflict, server.JointCustodyPending): raise
        except Exception: raise server.JointCustodyHold('joint research page unavailable') from None

    def summary(self, tenant, result_id, farm_ref):
        try:
            with self._read(tenant, result_id, farm_ref) as (row, packet, session):
                if row is None: return None
                with artifact.open_artifact(session.path, packet['artifact']['sha256']) as reader:
                    value = deepcopy({**reader.summary, 'manifest': reader._context['manifest'],
                        'time_binding': reader._header['binding']})
                    _need(len(_canonical(value)) <= artifact.LIMITS['page_bytes'])
                    return value
        except (PermissionError, server.JointCustodyConflict, server.JointCustodyPending): raise
        except Exception: raise server.JointCustodyHold('joint research summary unavailable') from None
