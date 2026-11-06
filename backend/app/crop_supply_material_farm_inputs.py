"""Immutable owned synthetic inputs for an exact current Farm registration."""
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from functools import wraps
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re
from typing import NamedTuple
from types import MethodType
from uuid import UUID

from psycopg import sql

from . import crop_leaf_carbon_stock_artifact_reader as carbon
from . import crop_rational_morphology_artifact_reader as stem
from . import crop_result_store as permissions
from . import farm_authoring_storage as authored
from . import farm_inputs, jobs, runtime_roles, runtime_connection_scope
from .api_contracts import public_job_status
from .job_store import JobStore, JobIntentConflict

INPUT_VERSION = 'supply-material-owned-input-v1'
REQUEST_VERSION = 'supply-material-farm-input-request-v1'
RIGHTS_VERSION = 'supply-material-farm-input-rights-v1'
READ_SCOPES = permissions.READ_SCOPES
WRITE_SCOPES = permissions.WRITE_SCOPES
PRODUCE_SCOPES = WRITE_SCOPES + ('simulation_create',)
MAX_INPUT_BYTES = 65536
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_ROOT = Path(__file__).resolve().parents[2]
_PATHS = tuple(dict.fromkeys((*carbon.SOURCE_PATHS, *stem.SOURCE_PATHS,
    'backend/app/crop_supply_material_farm_inputs.py', 'backend/app/crop_result_store.py',
    'backend/app/farm_authoring_storage.py', 'backend/app/farm_inputs.py',
    'backend/app/farm_registration_read_scope.py', 'backend/app/runtime_connection_scope.py',
    'backend/app/runtime_roles.py', 'backend/app/api_contracts.py')))
_PINS = {p: sha256((_ROOT/p).read_bytes()).hexdigest() for p in _PATHS}
_TOKEN = object()
_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}\Z')
_TIME = re.compile(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)\Z')
_FARM_METHODS = tuple((name, getattr(authored.FarmAuthoringService, name)) for name in
    ('_binding', '_pointers', '_guard', '_find', '_prepare', '_read', '_read_registration',
     'read_registration', 'registration_read_scope'))


class MaterialFarmInputHold(ValueError):
    pass


def _need(value):
    if not value:
        raise MaterialFarmInputHold('owned material Farm input unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (PermissionError, JobIntentConflict, MaterialFarmInputHold):
            raise
        except Exception:
            raise MaterialFarmInputHold('owned material Farm input unavailable') from None
    return run


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
        allow_nan=False).encode('utf-8')


def _digest(value):
    return sha256(_raw(value)).hexdigest()


def _closed(value, keys):
    _need(type(value) is dict and set(value) == set(keys))


def _name(value):
    _need(type(value) is str and _NAME.fullmatch(value) is not None)


def _hash(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None)


def _uuid(value):
    _need(type(value) is str and str(UUID(value)) == value)


def _time(value):
    _need(type(value) is str and _TIME.fullmatch(value) is not None)
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    _need(result.utcoffset() is not None)
    return result.astimezone(timezone.utc)


def _stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _now():
    return datetime.now(timezone.utc)


def _utc_fraction(value):
    _need(type(value) is datetime and value.utcoffset() is not None)
    delta = value.astimezone(timezone.utc)-datetime(1970, 1, 1, tzinfo=timezone.utc)
    return Fraction(delta.days*86400+delta.seconds)+Fraction(delta.microseconds, 1000000)


def _q(value):
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 's'}


def _pairs(items):
    result = {}
    for key, value in items:
        _need(key not in result)
        result[key] = value
    return result


def _parse(raw):
    _need(type(raw) is bytes and 0 < len(raw) <= MAX_INPUT_BYTES)
    value = json.loads(raw, object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    _need(type(value) is dict and _raw(value) == raw)
    count = 0
    def visit(item, depth):
        nonlocal count
        count += 1
        _need(depth <= 64 and count <= 32768)
        if type(item) is dict:
            for child in item.values(): visit(child, depth+1)
        elif type(item) is list:
            for child in item: visit(child, depth+1)
    visit(value, 0)
    return value


def _quantity(value, unit):
    _closed(value, ('value', 'unit'))
    number = value['value']
    _need(value['unit'] == unit and type(number) in (int, float) and isfinite(number))
    return Fraction(number)


@_checked
def _request(raw):
    value = _parse(raw)
    _closed(value, ('schema_version', 'study_id', 'revision', 'farm', 'source', 'rights', 'provenance'))
    _need(value['schema_version'] == REQUEST_VERSION)
    for key in ('study_id', 'revision'): _name(value[key])
    ref = value['farm']
    _closed(ref, ('scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id', 'zone_id'))
    _hash(ref['registration_sha256'])
    for key in ('scenario_id', 'scenario_revision', 'crop_id', 'zone_id'): _name(ref[key])
    source = value['source']
    _closed(source, ('carbon_stock_inputs', 'stem_program', 'stem_start_index',
        'individual_program', 'numerical', 'tracking_basis', 'profile_sha256'))
    original = carbon._inputs(_raw(source['carbon_stock_inputs']))
    stem._program(source['stem_program'])
    index = source['stem_start_index']
    _need(type(index) is int and -1 <= index < len(source['stem_program']['output_times']))
    _need(source['profile_sha256'] == carbon.PROFILE_SHA)
    _closed(source['profile_sha256'], carbon.PROFILE_SHA)
    numerical = source['numerical']
    _closed(numerical, ('step_seconds', 'step_count'))
    dt, count = numerical['step_seconds'], numerical['step_count']
    _need(type(dt) in (int, float) and isfinite(dt) and dt > 0 and type(count) is int
        and 1 <= count <= 4096 and Fraction(dt)*count <= 600)
    program = source['individual_program']; aggregate = original['program']
    _closed(program, (*aggregate, 'stem_root_stock_policy', 'stem_root_compartments'))
    _need(program['stem_root_stock_policy'] == 'stem-root-stocks-uniform-maintenance-explicit-removal-v1')
    adapter = json.loads(_raw(program))
    rows = adapter.pop('stem_root_compartments'); adapter.pop('stem_root_stock_policy')
    _closed(adapter['scenario']['plant_state'], set(aggregate['scenario']['plant_state'])-{'stem_root'})
    _closed(adapter['scenario']['removals'], set(aggregate['scenario']['removals'])-{'stem_root'})
    for block in ('plant_state', 'removals'):
        adapter['scenario'][block]['stem_root'] = aggregate['scenario'][block]['stem_root']
    _need(_raw(adapter) == _raw(aggregate) and type(rows) is list and 1 <= len(rows) <= 512)
    identifiers = set(); roots = 0
    for row in rows:
        _closed(row, ('compartment_id', 'kind', 'initial_carbon', 'sink_weight', 'carbon_removal'))
        _name(row['compartment_id']); _need(row['compartment_id'] not in identifiers)
        identifiers.add(row['compartment_id']); _need(row['kind'] in ('root_system', 'internode'))
        roots += row['kind'] == 'root_system'
        for name, unit in (('initial_carbon', 'mg_CH2O/m2_floor'), ('sink_weight', '1'),
                ('carbon_removal', 'mg_CH2O/m2_floor/s')):
            _need(_quantity(row[name], unit) >= 0)
    _need(roots == 1 and (count+1)*(106+5*len(program['leaves'])+len(rows)+9) <= 32768)
    basis = source['tracking_basis']
    _closed(basis, ('kind', 'shoot_id', 'model_floor_area', 'tracked_shoot_count'))
    _name(basis['shoot_id'])
    _need(basis['kind'] == 'one_tracked_shoot_on_declared_model_floor_research_v1'
        and basis['model_floor_area'] == program['model_floor_area']
        and type(basis['tracked_shoot_count']) is dict
        and set(basis['tracked_shoot_count']) == {'value', 'unit'}
        and type(basis['tracked_shoot_count']['value']) is int
        and basis['tracked_shoot_count'] == {'value': 1, 'unit': 'tracked_shoot'}
        and basis['shoot_id'] == source['stem_program']['initial_state']['timeline_state']['shoot_id'])
    rights = value['rights']; grants = ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')
    _closed(rights, ('schema_version', 'declaration_id', 'revision', *grants,
        'redistribute', 'available_at', 'reviewer'))
    _need(rights['schema_version'] == RIGHTS_VERSION and all(rights[k] is True for k in grants)
        and rights['redistribute'] is False)
    for key in ('declaration_id', 'revision', 'reviewer'): _name(rights[key])
    provenance = value['provenance']
    _closed(provenance, ('origin', 'product_id', 'source_ref', 'revision', 'observed_at',
        'published_at', 'available_at', 'retrieved_at', 'qc', 'reviewer'))
    for key in ('product_id', 'source_ref', 'revision', 'reviewer'): _name(provenance[key])
    _need(provenance['origin'] == 'own_declared_synthetic_assumptions'
        and provenance['product_id'] == value['study_id'] and provenance['revision'] == value['revision']
        and provenance['reviewer'] == rights['reviewer']
        and provenance['observed_at'] is None and provenance['published_at'] is None
        and provenance['qc'] == 'software_contract_only_not_farm_measurements')
    available = _time(rights['available_at'])
    for declaration in (original['rights'], source['stem_program']['rights']):
        _need(_time(declaration['declared_at_utc']) <= available)
    _need(available <= _time(provenance['available_at']) <= _time(provenance['retrieved_at']))
    return value


@contextmanager
def _scope(farms, tenant, ref):
    _farm_dispatch(farms)
    args = (tenant, ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
    current = farms._registration_read.get()
    if current is None:
        with _FARM_METHODS[-1][1](farms, *args): yield
    else:
        _need(current.args == args)
        yield


def _farm_dispatch(farms):
    for name, original in _FARM_METHODS:
        current = getattr(farms, name)
        _need(type(current) is MethodType and current.__self__ is farms and current.__func__ is original)


@dataclass(frozen=True, eq=False)
class VerifiedMaterialFarmInput:
    _input: bytes = field(repr=False)
    _request: bytes = field(repr=False)
    _witness: bytes = field(repr=False)
    _token: object = field(repr=False)

    @property
    def input_bytes(self):
        _need(self._token is _TOKEN)
        return self._input

    @property
    def request(self):
        _need(self._token is _TOKEN)
        return json.loads(self._request)

    @property
    def witness(self):
        _need(self._token is _TOKEN)
        return json.loads(self._witness)


class _Program(NamedTuple):
    capture: object
    pointers: object
    guard: object
    find: object
    registration: object
    content: object
    read: object
    farm_read: object
    farm_find: object
    farm_pointers: object
    farm_guard: object


def _namespace():
    names = (_namespace, _farm_dispatch, _need, _raw, _digest, _closed, _name, _hash, _uuid, _time, _stamp, _now,
        _utc_fraction, _q, _pairs, _parse, _quantity, _request, _request.__wrapped__, _scope,
        _scope.__wrapped__, carbon._inputs, carbon._program, stem._program,
        jobs.canonical_input_bytes, runtime_connection_scope.read_connection,
        authored.FarmAuthoringService.read_registration, authored.FarmAuthoringService._guard,
        JobStore._verified_input, JobStore.submit, JobStore._event,
        VerifiedMaterialFarmInput.input_bytes.fget, VerifiedMaterialFarmInput.request.fget,
        VerifiedMaterialFarmInput.witness.fget,
        MaterialFarmInputService.submit, MaterialFarmInputService.submit.__wrapped__,
        MaterialFarmInputService.current, MaterialFarmInputService.current.__wrapped__,
        *(fn for _, fn in _FARM_METHODS))
    return (tuple((fn, fn.__code__) for fn in names), _TOKEN, _Program, VerifiedMaterialFarmInput,
        INPUT_VERSION, REQUEST_VERSION, RIGHTS_VERSION, READ_SCOPES, WRITE_SCOPES, PRODUCE_SCOPES,
        MAX_INPUT_BYTES, jobs.MAX_INPUT_BYTES, CODE_SHA256, tuple(sorted(_PINS.items())), tuple(_PATHS),
        tuple(sorted(carbon.PROFILE_SHA.items())), carbon.NOTICE_SHA,
        permissions.READ_SCOPES, permissions.WRITE_SCOPES, datetime, timezone, Decimal, Fraction,
        json.loads, json.dumps, sha256, Path, _FARM_METHODS, MethodType)


class MaterialFarmInputService:
    @_checked
    def __init__(self, farms):
        _need(type(self) is MaterialFarmInputService and type(farms) is authored.FarmAuthoringService)
        self.farms, self.jobs = farms, farms.replay.jobs
        self._program = self.__program = MaterialFarmInputService._capture_program(self)
        self._namespace = _namespace()
        self._fixed = self.__program.pointers(self, self.__program)
        self.__program.guard(self, self.__program, None, ())

    def _capture_program(self):
        _farm_dispatch(self.farms)
        own = tuple(getattr(getattr(self, name), '__func__', getattr(self, name)) for name in
            ('_capture_program', '_pointers', '_guard', '_find', '_registration', '_content', '_read'))
        originals = dict(_FARM_METHODS)
        return _Program(*own, *(originals[name] for name in
            ('read_registration', '_find', '_pointers', '_guard')))

    def _pointers(self, program):
        methods = tuple((fn, fn.__code__) for fn in (*program.capture(self),
            getattr(self.submit, '__func__', self.submit), getattr(self.current, '__func__', self.current)))
        farms, job = self.farms, self.jobs
        return (farms, program.farm_pointers(farms), job, job.principal_provider, job._dsn, job.schema,
            job.runtime_identity, repr(vars(job.runtime_identity[0])), job.audit_runtime_grants, self._program, methods,
            _namespace(), tuple(sha256((_ROOT/p).read_bytes()).hexdigest() for p in _PATHS))

    def _guard(self, program, tenant, scopes):
        _need(type(self) is MaterialFarmInputService and self._namespace == _namespace()
            and program.pointers(self, program) == self._fixed and self.jobs is self.farms.replay.jobs
            and type(self.jobs) is JobStore and self.jobs.audit_runtime_grants is True
            and _PINS['backend/app/crop_supply_material_farm_inputs.py'] == CODE_SHA256
            and {p: sha256((_ROOT/p).read_bytes()).hexdigest() for p in _PATHS} == _PINS
            and READ_SCOPES == permissions.READ_SCOPES and WRITE_SCOPES == permissions.WRITE_SCOPES
            and PRODUCE_SCOPES == WRITE_SCOPES+('simulation_create',)
            and MAX_INPUT_BYTES == jobs.MAX_INPUT_BYTES == 65536)
        policy, kind = self.jobs.runtime_identity
        _need(type(policy) is runtime_roles.RuntimeLoginPolicy and kind == 'authority'
            and policy.crop_cycle_result_storage is True)
        if tenant is not None:
            if not all(self.jobs._has_scope(tenant, scope) for scope in scopes):
                raise PermissionError('owned material Farm input access denied')
            program.farm_guard(self.farms, tenant, self._fixed[1], scopes)

    def _find(self, program, tenant, *, key=None, job_id=None):
        with runtime_connection_scope.read_connection(self.jobs) as conn:
            if job_id is None:
                row = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND stage='collection' AND idempotency_key=%s")
                    .format(self.jobs._table('jobs')), (tenant, key)).fetchone()
            else:
                row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                    .format(self.jobs._table('jobs')), (tenant, job_id)).fetchone()
        if row is not None: self.jobs._verified_input(row)
        return row

    def _registration(self, program, tenant, request):
        ref = request['farm']
        program.guard(self, program, tenant, READ_SCOPES)
        record = program.farm_read(self.farms, tenant, ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
        farm = record['farm']; crop = next((c for c in farm.crops if c.crop_id == ref['crop_id']), None)
        program.guard(self, program, tenant, READ_SCOPES)
        row = program.farm_find(self.farms, tenant, ref['scenario_id'], ref['scenario_revision'])
        _need(crop is not None and row is not None and farm.facility.zone_id == ref['zone_id']
            and row['input_sha256'] == ref['registration_sha256'])
        begin = datetime.combine(farm.period_start, time(), farm_inputs.KST)
        end = datetime.combine(farm.period_end+timedelta(days=1), time(), farm_inputs.KST)
        result = {'registration_job_id': str(row['job_id']), 'registration_sha256': row['input_sha256'],
            'farm_sha256': sha256(farm_inputs.canonical_farm_inputs(farm)).hexdigest(),
            'rights_sha256': _digest(record['user_rights_declaration'].model_dump(mode='json')),
            'source_binding_sha256': _digest(record['binding']),
            'numeric_input_sha256': sha256(record['numeric_input_bytes']).hexdigest(),
            'crop_sha256': _digest(crop.model_dump(mode='json')),
            'facility_sha256': _digest(farm.facility.model_dump(mode='json')),
            'decision_at': _stamp(farm.decision_at), 'decision_context_id': farm.decision_context_id,
            'context_sha256': record['binding']['context_sha256'], 'snapshot_id': farm.snapshot_id,
            'calendar_utc': {'start': _stamp(begin), 'end': _stamp(end)},
            'occupancy_utc': {'start': _stamp(crop.occupancy.start), 'end': _stamp(crop.occupancy.end)}}
        return result, farm.facility.floor_area.model_dump(mode='json')

    def _content(self, program, tenant, request, reviewed_at):
        now = _now(); reviewed = _time(reviewed_at)
        _need(reviewed <= now and _time(request['provenance']['retrieved_at']) <= reviewed)
        registration, floor = program.registration(self, program, tenant, request)
        source = request['source']; c = source['carbon_stock_inputs']; s = source['stem_program']
        model_floor = source['individual_program']['model_floor_area']
        _need(floor['unit'] == 'm²' and Fraction(Decimal(floor['value'])) == _quantity(model_floor, 'm2_floor'))
        origin = c['time_origin_utc']; stem_begin = s['initial_state']['timeline_state']['at']
        selected = stem_begin if source['stem_start_index'] == -1 else s['output_times'][source['stem_start_index']]
        _need(_time(selected) == _time(origin))
        cd = Fraction(c['step_seconds'])*c['step_count']
        nd = Fraction(source['numerical']['step_seconds'])*source['numerical']['step_count']
        for window in (registration['calendar_utc'], registration['occupancy_utc']):
            left, right = (_utc_fraction(_time(window[k])) for k in ('start', 'end'))
            at = _utc_fraction(_time(origin))
            _need(left <= at < right and at+cd <= right and at+nd <= right
                and left <= _utc_fraction(_time(stem_begin)) < _utc_fraction(_time(s['output_times'][-1])) <= right)
        dates = {'rights_available_at': request['rights']['available_at'],
            'provenance_available_at': request['provenance']['available_at'],
            'provenance_retrieved_at': request['provenance']['retrieved_at'],
            'carbon_rights_declared_at_utc': c['rights']['declared_at_utc'],
            'stem_rights_declared_at_utc': s['rights']['declared_at_utc']}
        _need(all(_time(v) <= now for v in dates.values()))
        formats = ('leaf-carbon-stock-artifact-input-v1', 'morphology-software-program-v2',
            'stem-root-stock-program-interface-v1')
        components = {key: {'format_id': version, 'sha256': _digest(source[key]), 'bytes': len(_raw(source[key]))}
            for key, version in zip(('carbon_stock_inputs', 'stem_program', 'individual_program'), formats, strict=True)}
        components.update(numerical=source['numerical'], tracking_basis_sha256=_digest(source['tracking_basis']))
        return {'schema_version': 'supply-material-farm-input-content-witness-v1', 'farm': request['farm'],
            'registration': registration, 'components': components,
            'normalization': {'mapping_version': 'same_registered_single_zone_floor_v1',
                'farm_floor_area': floor, 'model_floor_area': model_floor, 'tracking_basis': source['tracking_basis']},
            'time_scope': {'model_origin_utc': origin, 'carbon_duration_seconds_exact': _q(cd),
                'individual_duration_seconds_exact': _q(nd), 'stem_program_start_utc': stem_begin,
                'stem_program_end_utc': s['output_times'][-1], 'selected_stem_at_utc': selected,
                'declared_dates': dates, 'assumption_mode': 'supplemental_ex_post_synthetic_material_assumptions',
                'declared_availability_vs_farm_decision': 'before_or_at' if _time(request['provenance']['available_at']) <=
                    _time(registration['decision_at']) else 'after', 'ex_ante_validity': 'not_established'},
            'rights_policy': {'version': RIGHTS_VERSION, 'effective_rights': {'use': True, 'display': True, 'redistribute': False}},
            'implementation': {'authority_version': INPUT_VERSION, 'code_sha256': dict(_PINS),
                'profile_sha256': dict(carbon.PROFILE_SHA), 'notice_sha256': carbon.NOTICE_SHA},
            'server_review_at': reviewed_at}

    def _read(self, program, tenant, job_id, expected):
        program.guard(self, program, tenant, READ_SCOPES)
        row = program.find(self, program, tenant, job_id=job_id)
        _need(row is not None and row['stage'] == 'collection' and row['state'] == 'queued'
            and not row['cancel_requested'] and row['attempt_count'] == 0 and row['input_sha256'] == expected)
        raw = self.jobs._verified_input(row); value = _parse(raw)
        _closed(value, ('input_version', 'tenant_id', 'request', 'content_witness', 'content_witness_sha256'))
        _need(value['input_version'] == INPUT_VERSION and value['tenant_id'] == tenant
            and jobs.canonical_input_bytes(value) == raw)
        request = _request(_raw(value['request']))
        content = program.content(self, program, tenant, request, value['content_witness']['server_review_at'])
        _need(_raw(content) == _raw(value['content_witness']) and _digest(content) == value['content_witness_sha256'])
        program.guard(self, program, tenant, READ_SCOPES)
        fresh = program.find(self, program, tenant, job_id=job_id)
        _need(fresh is not None and fresh['stage'] == 'collection' and fresh['state'] == 'queued'
            and not fresh['cancel_requested'] and fresh['attempt_count'] == 0
            and fresh['input_sha256'] == expected and self.jobs._verified_input(fresh) == raw
            and fresh['created_at'] == row['created_at'])
        program.guard(self, program, tenant, READ_SCOPES)
        witness = {'schema_version': 'supply-material-farm-input-resolved-witness-v1', 'tenant_id': tenant,
            'owned_input': {'job_id': str(row['job_id']), 'input_version': INPUT_VERSION,
                'input_sha256': row['input_sha256'], 'created_at': _stamp(row['created_at']),
                'stage': row['stage'], 'state': row['state']},
            'content_witness_sha256': value['content_witness_sha256'], 'content_witness': content}
        return VerifiedMaterialFarmInput(raw, _raw(request), _raw(witness), _TOKEN)

    @_checked
    def current(self, tenant, job_id, expected_input_sha256):
        p = self.__program
        p.guard(self, p, tenant, READ_SCOPES); _uuid(job_id); _hash(expected_input_sha256)
        row = p.find(self, p, tenant, job_id=job_id)
        _need(row is not None)
        request = _request(_raw(_parse(self.jobs._verified_input(row))['request']))
        with _scope(self.farms, tenant, request['farm']):
            result = p.read(self, p, tenant, job_id, expected_input_sha256)
            p.guard(self, p, tenant, READ_SCOPES)
            return result

    @_checked
    def submit(self, tenant, request_raw):
        p = self.__program
        p.guard(self, p, tenant, WRITE_SCOPES); request = _request(request_raw)
        key = INPUT_VERSION+':'+_digest([request['study_id'], request['revision']])
        with _scope(self.farms, tenant, request['farm']):
            previous = p.find(self, p, tenant, key=key)
            if previous is not None:
                value = _parse(self.jobs._verified_input(previous))
                if _raw(value.get('request')) != request_raw:
                    raise JobIntentConflict('owned material Farm input revision conflict')
                p.read(self, p, tenant, str(previous['job_id']), previous['input_sha256'])
                reviewed_at = value['content_witness']['server_review_at']
            else:
                reviewed_at = _stamp(_now())
            content = p.content(self, p, tenant, request, reviewed_at)
            value = {'input_version': INPUT_VERSION, 'tenant_id': tenant, 'request': request,
                'content_witness': content, 'content_witness_sha256': _digest(content)}
            raw = jobs.canonical_input_bytes(value)
            def verify():
                p.guard(self, p, tenant, WRITE_SCOPES)
                _need(_raw(p.content(self, p, tenant, request, reviewed_at)) == _raw(content)
                    and jobs.canonical_input_bytes(value) == raw)
                p.guard(self, p, tenant, WRITE_SCOPES)
            verify()
            try:
                row = self.jobs.submit(tenant, 'collection', value, key, commit_guard=verify)
            except JobIntentConflict:
                p.guard(self, p, tenant, WRITE_SCOPES)
                winner = p.find(self, p, tenant, key=key)
                if winner is None or _raw(_parse(self.jobs._verified_input(winner)).get('request')) != request_raw:
                    raise
                checked = p.read(self, p, tenant, str(winner['job_id']), winner['input_sha256'])
                raw = checked.input_bytes
                value = _parse(raw)
                content = value['content_witness']
                reviewed_at = content['server_review_at']
                row = winner
            verify()
            checked = p.read(self, p, tenant, str(row['job_id']), row['input_sha256'])
            _need(checked.input_bytes == raw)
            p.guard(self, p, tenant, WRITE_SCOPES)
            return public_job_status(row)
