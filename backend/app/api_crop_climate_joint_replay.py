"""Closed projection of original joint quantities; custody authorizes the read."""
from datetime import datetime, timezone
from hashlib import sha256
from fractions import Fraction
from math import isfinite
from pathlib import Path
import re
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, create_model, model_validator

from .api_crop_replay import _Public, Digest, Name, UtcStamp
from . import crop_climate_joint_result_store as storage

server = storage.server
continuation = server.continuation
driver = continuation.driver
joint = driver.joint
VERSION = 'joint-crop-climate-replay-v1'
RESULT_ID_PATTERN = r'^joint-crop-climate-result-v1:[0-9a-f]{64}$'
MAX_RESPONSE_BYTES = 2*1024**2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class ProjectionHold(ValueError):
    """No publishable projection of this original research result."""


def _need(condition):
    if not condition: raise ProjectionHold('joint crop climate display unavailable')


def _float(value):
    _need(type(value) is float and isfinite(value)); return value


Float = Annotated[float, BeforeValidator(_float)]
Index = Annotated[int, Field(strict=True, ge=0, le=4096)]
_quantities = {}


def _block(name, units, *, arrays=False):
    fields = {}
    for key, unit in units.items():
        if unit not in _quantities:
            _quantities[unit] = create_model('JointQuantity'+str(len(_quantities)), __base__=_Public,
                value=(Float, ...), unit=(Literal[unit], ...))
        cls = _quantities[unit]
        fields[key] = (Annotated[list[cls], Field(min_length=50, max_length=50)] if arrays else cls, ...)
    return create_model(name, __base__=_Public, **fields)


Plant = _block('JointPlant', joint.SCALAR_BLOCKS['plant_state'])
Cohorts = _block('JointCohorts', joint.ARRAY_BLOCKS['cohort_state'], arrays=True)
Climate = _block('JointClimate', joint.CLIMATE_UNITS)
Derived = _block('JointDerived', {'canopy_temperature': 'degC', 'leaf_area_index': 'm2_leaf/m2_floor',
    'canopy_capacity': 'J/m2_floor/K', 'air_capacity': 'J/m2_floor/K',
    'air_vapor_pressure': 'Pa', 'canopy_temperature_rate': 'K/s'})
Transfers = _block('JointTransfers', driver.short.FLUX_UNITS)
EventTotals = _block('JointEventTotals', driver.EVENT_UNITS)
Balance = _block('JointBalance', {'carbohydrate': driver.short.MASS, 'number': driver.short.NUMBER,
    **dict.fromkeys(('canopy_sensible', 'air_sensible', 'reduced_energy'), driver.short.ENERGY),
    'vapor_and_water_boundaries': driver.short.WATER, 'crop_capacity': 'J/m2_floor/K'})
EventBalance = _block('JointEventBalance', {'carbohydrate': driver.short.MASS, 'number': driver.short.NUMBER,
    'canopy_sensible': driver.short.ENERGY, 'crop_capacity': 'J/m2_floor/K', 'temperature': 'K'})
Removed = create_model('JointRemoved', __base__=_Public,
    **{k: (v.annotation, ...) for k, v in EventTotals.model_fields.items() if k not in ('fruit_carbohydrate', 'fruit_number')},
    **{k: (v.annotation, ...) for k, v in Cohorts.model_fields.items()})
RemovedTotals = _block('JointRemovedTotals', {'carbohydrate': driver.short.MASS, 'number': driver.short.NUMBER})
Profiles = create_model('JointProfiles', __base__=_Public, **{k: (Digest, ...) for k in continuation.PROFILE_NAMES})
Components = create_model('JointComponents', __base__=_Public, **{k: (Digest, ...) for k in joint.COMPONENT_CODE_SHA256})


class State(_Public):
    plant_state: Plant
    cohort_state: Cohorts
    climate_state: Climate
    derived: Derived

    @model_validator(mode='after')
    def nonnegative_inventories(self):
        _need(all(getattr(self.plant_state, k).value >= 0 for k in ('buffer', 'leaf', 'stem_root', 'temperature_sum'))
            and all(q.value >= 0 for k in Cohorts.model_fields for q in getattr(self.cohort_state, k))
            and self.climate_state.air_vapor_mass.value >= 0
            and self.derived.leaf_area_index.value > 0 and self.derived.canopy_capacity.value > 0
            and self.derived.air_capacity.value > 0)
        return self


class Snapshot(State):
    step_index: Index
    elapsed_seconds: Float
    integrated_transfers: Transfers
    event_totals: EventTotals
    event_count: Annotated[int, Field(strict=True, ge=0, le=128)]
    balance_residuals: Balance
    balance_budgets: Balance
    phase: Literal['initial', 'step-end', 'boundary-after-event']


class Point(_Public):
    step_index: Index
    at: UtcStamp


class Sample(_Public):
    value: Snapshot
    time: Point


class EventState(State):
    input_sha256: Digest
    calculation_sha256: Digest


class Management(_Public):
    model_version: Literal['joint-crop-climate-management-research-v1']
    code_sha256: Digest
    rhs_code_sha256: Digest
    component_code_sha256: Components
    event_sha256: Digest
    calculation_sha256: Digest
    before_calculation_sha256: Digest
    after_calculation_sha256: Digest
    quantity_rule: Literal['cohort-decimal-rational-removal-v1']
    roundoff_rule: Literal['64-ulp-event-inventory-v1']
    time_coordinate: Literal['instantaneous_no_clock']
    before: EventState
    after: EventState
    profile_sha256: Profiles
    policy_sha256: Digest
    removed: Removed
    removed_totals: RemovedTotals
    balance_residuals: EventBalance
    balance_budgets: EventBalance
    scope: Literal['software_research_only']
    claim_scope: Literal['synthetic_joint_crop_climate_management_only']
    G0_G4: Literal['not_assessed']


class EventValue(_Public):
    step_index: Index
    elapsed_seconds: Float
    management: Management


class Event(_Public):
    value: EventValue
    time: Point


class Identity(_Public):
    engine_version: Literal['joint-crop-climate-continuation-research-v1']
    engine_code_sha256: Digest
    driver_code_sha256: Digest
    short_code_sha256: Digest
    management_code_sha256: Digest
    rhs_code_sha256: Digest
    component_code_sha256: Components
    policy_sha256: Digest
    profile_sha256: Profiles
    state_schema: Literal['crop-climate-stage-state-v1']
    physical_clock_contract: Literal['dynamic-canopy-temperature-history-rhs-v1']
    python_version: Annotated[str, Field(strict=True, max_length=40)]
    platform_machine: Annotated[str, Field(strict=True, max_length=100)]
    platform_system: Annotated[str, Field(strict=True, max_length=100)]
    byteorder: Literal['little', 'big']
    float_mant_dig: Literal[53]
    float_radix: Literal[2]


class Numerical(_Public):
    step_seconds: Float
    step_count: Annotated[int, Field(strict=True, ge=1, le=4096)]
    duration_seconds: Float
    method: Literal['single-step-shared-rk4-kernel-events-v1']
    quantity_rule: Literal['cohort-decimal-rational-removal-v1']
    roundoff_rule: Literal['64-ulp-per-step-and-event-global-ledger-v1']


class Manifest(_Public):
    identity: Identity
    program_sha256: Digest
    initial_rhs_sha256: Digest
    initial_calculation_sha256: Digest
    policy_sha256: Digest
    numerical: Numerical
    scope: Literal['software_research_only']
    clock_contract: Literal['elapsed-grid-shared-rk4-events-v1']


class TimeGrid(_Public):
    version: Literal['joint-crop-climate-time-binding-research-v1']
    time_rule: Literal['UTC_POSIX_integer_microseconds_decimal_step_v1']
    time_code_sha256: Digest
    start_utc: UtcStamp
    end_utc: UtcStamp
    step_seconds_decimal: Annotated[str, Field(strict=True, max_length=40)]
    step_microseconds: Annotated[int, Field(strict=True, ge=1, le=600000000)]
    step_count: Annotated[int, Field(strict=True, ge=1, le=4096)]


Farm = create_model('JointFarm', __base__=_Public, **{k: (Digest if k == 'registration_sha256' else Name, ...)
    for k in storage.schema.FARM_KEYS if k != 'registration_job_id'})
Input = create_model('JointInput', __base__=_Public, **{k: (UtcStamp if k.endswith('_utc') else
    Digest if k.endswith('_sha256') else Name, ...) for k in storage.schema.INPUT_KEYS})
Artifact = create_model('JointArtifact', __base__=_Public,
    **{k: (Literal['completed', 'hold'] if k == 'status' else Annotated[str, Field(strict=True,
        pattern=r'^joint-crop-climate-storage-research-v1:[0-9a-f]{64}$')] if k == 'ref' else Digest, ...)
        for k in storage.schema.ARTIFACT_STRINGS},
    **{k: (Annotated[int, Field(strict=True, ge=lo, le=hi)], ...) for k, (lo, hi) in storage.schema.COUNTER_BOUNDS.items()})
Code = create_model('JointResultCode', __base__=_Public,
    **{k: (create_model('JointServerDependencies', __base__=_Public,
        **{n: (Digest, ...) for n in server.DEPENDENCY_SHA256}) if k == 'server_dependency_sha256' else Digest, ...)
        for k in storage.CODE})


class Reference(_Public):
    storage_status: Literal['stored_unpublished_research']
    claim_scope: Literal['synthetic_joint_crop_climate_math_only']
    G0_G4: Literal['not_assessed']
    input: Input
    artifact: Artifact
    code: Code
    payload_sha256: Digest
    normalization: Literal['per_m2_floor']
    profile_applicability: Literal['unvalidated_for_registered_crop']
    normalization_version: Literal['joint-shared-stage-float64-grid-v1']
    qc_version: Literal['joint-initial-rhs-schedule-utc-v1']
    input_evidence_version: Literal['joint-crop-climate-input-evidence-v1']
    model: Identity
    time_grid: TimeGrid
    last_confirmed: Point
    failed_boundary: Point | None


class Hold(_Public):
    reason_code: Annotated[str, Field(strict=True, pattern=r'^[A-Z][A-Z0-9_]{0,99}$')]
    phase: Literal['initial', 'interval', 'global-step-balance', 'event', 'global-event-balance']
    time_meaning: Literal['failed_grid_boundary']
    time: Point


class Summary(_Public):
    status: Literal['completed', 'hold']
    manifest: Manifest
    last_confirmed: Sample
    checkpoint_sha256: Digest | None
    hold: Hold | None


class SamplePage(_Public):
    kind: Literal['samples']
    offset: Index
    limit: Annotated[int, Field(strict=True, ge=1, le=64)]
    total: Annotated[int, Field(strict=True, ge=0, le=512)]
    next_offset: Index | None
    records: Annotated[list[Sample], Field(max_length=64)]


class EventPage(_Public):
    kind: Literal['events']
    offset: Index
    limit: Annotated[int, Field(strict=True, ge=1, le=8)]
    total: Annotated[int, Field(strict=True, ge=0, le=128)]
    next_offset: Index | None
    records: Annotated[list[Event], Field(max_length=8)]


class JointReplay(_Public):
    schema_version: Literal['joint-crop-climate-replay-v1']
    result_id: Annotated[str, Field(strict=True, pattern=RESULT_ID_PATTERN)]
    recorded_at: UtcStamp
    study_id: Name
    revision: Name
    farm: Farm
    reference: Reference
    summary: Summary | None
    page: Annotated[SamplePage | EventPage, Field(discriminator='kind')] | None

    @model_validator(mode='after')
    def consistent(self):
        _need((self.summary is None) != (self.page is None))
        a = self.reference.artifact
        _need(a.ref == server.storage.VERSION + ':' + a.sha256
            and a.steps <= a.planned_steps and (a.status != 'completed' or a.steps == a.planned_steps))
        grid = self.reference.time_grid.model_dump(mode='json')
        dt = float(grid['step_seconds_decimal'])
        identity = self.reference.model.model_dump(mode='json')
        _need(self.reference.code.model_dump(mode='json') == storage.CODE
            and all(identity[k] == v for k, v in {'engine_code_sha256': continuation.CODE_SHA256,
                'driver_code_sha256': driver.CODE_SHA256, 'short_code_sha256': driver.short.CODE_SHA256,
                'management_code_sha256': driver.management.CODE_SHA256, 'rhs_code_sha256': joint.CODE_SHA256,
                'component_code_sha256': joint.COMPONENT_CODE_SHA256, 'profile_sha256': server.evidence._PROFILE_HASHES}.items()))
        _need(isfinite(dt) and dt > 0 and grid['step_count'] == a.planned_steps
            and grid['time_code_sha256'] == server.clock.CODE_SHA256
            and grid['step_microseconds'] == Fraction(grid['step_seconds_decimal'])*1000000
            and grid['start_utc'] == self.reference.input.start_utc
            and grid['end_utc'] == self.reference.input.end_utc == server.clock._at(grid, grid['step_count']))
        point = self.reference.last_confirmed
        _need(point.step_index == a.steps and point.at == server.clock._at(grid, a.steps)
            and (self.reference.failed_boundary is not None) == (a.status == 'hold'))
        failed = self.reference.failed_boundary
        if failed is not None:
            _need(a.steps <= failed.step_index and failed.at == server.clock._at(grid, failed.step_index))
        if self.summary is not None:
            s = self.summary
            _need(s.status == a.status and (s.hold is not None) == (a.status == 'hold')
                and (s.checkpoint_sha256 is None) == (a.status == 'hold')
                and s.manifest.identity == self.reference.model
                and continuation._hash(s.manifest.model_dump(mode='json')) == self.reference.input.context_sha256
                and s.manifest.numerical.step_seconds == dt and s.manifest.numerical.step_count == a.planned_steps
                and s.manifest.numerical.duration_seconds == dt*a.planned_steps)
            _point(s.last_confirmed.time.model_dump(mode='json'), s.last_confirmed.value.model_dump(mode='json'), grid, dt)
            _need(s.last_confirmed.value.step_index == a.steps)
            _need(s.last_confirmed.time == point and (s.hold is None or s.hold.time == failed))
        if self.page is not None:
            p = self.page; end = p.offset + len(p.records)
            _need(p.total == (a.sample_count if p.kind == 'samples' else a.event_count)
                and p.offset <= p.total and len(p.records) == min(p.limit, p.total-p.offset)
                and p.next_offset == (end if end < p.total else None))
            previous = -1
            for row in p.records:
                _point(row.time.model_dump(mode='json'), row.value.model_dump(mode='json'), grid, dt)
                _need(previous < row.value.step_index <= a.steps
                    and (failed is None or row.value.step_index < failed.step_index)); previous = row.value.step_index
        return self


def _parsed(cls, value):
    parsed = cls.model_validate(value)
    _need(storage._canonical(parsed.model_dump(mode='json')) == storage._canonical(value)); return parsed


def _point(time, value, grid, dt):
    _parsed(Point, time)
    _need(type(value['step_index']) is int and time['step_index'] == value['step_index']
        and type(value['elapsed_seconds']) is float and value['elapsed_seconds'] == value['step_index']*dt
        and time['at'] == server.clock._at(grid, value['step_index']))


def _event(row, identity):
    _need(type(row) is dict and set(row) == {'value', 'time'} and set(row['value']) == {'step_index', 'elapsed_seconds', 'management'})
    m = row['value']['management']
    _need(type(m) is dict and set(m) == set(Management.model_fields) | {'event'}
        and m['code_sha256'] == driver.management.CODE_SHA256 and m['rhs_code_sha256'] == joint.CODE_SHA256
        and m['component_code_sha256'] == identity['component_code_sha256']
        and m['profile_sha256'] == identity['profile_sha256'] and m['policy_sha256'] == identity['policy_sha256'])
    copied = {k: v for k, v in m.items() if k != 'event'}
    _need(continuation._hash(m['event']) == m['event_sha256']
        and continuation._hash({k: m[k] for k in ('model_version', 'code_sha256', 'rhs_code_sha256',
            'component_code_sha256', 'event_sha256', 'before_calculation_sha256', 'after_calculation_sha256',
            'quantity_rule', 'roundoff_rule', 'time_coordinate')}) == m['calculation_sha256'])
    for key in ('before', 'after'):
        s = m[key]; _need(type(s) is dict and set(s) == {'scenario', 'derived', 'input_sha256', 'calculation_sha256'})
        _need(type(s['scenario']) is dict and set(s['scenario']) == {'input_id', 'origin', *joint.SCALAR_BLOCKS, *joint.ARRAY_BLOCKS})
        copied[key] = {**{k: s[k] for k in ('derived', 'input_sha256', 'calculation_sha256')},
            **{k: s['scenario'][k] for k in ('plant_state', 'cohort_state', 'climate_state')}}
        _need(copied[key]['calculation_sha256'] == m[key+'_calculation_sha256'])
    return {'time': row['time'], 'value': {**{k: row['value'][k] for k in ('step_index', 'elapsed_seconds')}, 'management': copied}}


def _public_bytes(projected):
    try:
        storage._pins()
        _need(type(projected) is JointReplay and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and MAX_RESPONSE_BYTES == server.storage.LIMITS['page_bytes'] == 2*1024**2)
        checked = _parsed(JointReplay, projected.model_dump(mode='json'))
        raw = checked.model_dump_json().encode(); _need(1 <= len(raw) <= MAX_RESPONSE_BYTES); return raw
    except Exception: raise ProjectionHold('joint crop climate display unavailable') from None


def project_joint_result(record, terminal, *, view='summary', page=None, limit=None):
    try:
        _need(type(record) is dict and set(record) == {'result_id', 'payload_raw', 'payload_sha256', 'recorded_at'}
            and type(record['payload_raw']) is bytes and sha256(record['payload_raw']).hexdigest() == record['payload_sha256']
            and type(record['recorded_at']) is datetime and record['recorded_at'].utcoffset() is not None)
        packet = storage._decode(record['payload_raw']); _need(record['result_id'] == packet['result_id'])
        progress = packet['policies']['server_progress']; source = packet['binding']['input']
        _need(type(terminal) is dict and set(terminal) == {'version', 'scope', 'G0_G4', 'artifact_sha256',
            'context_sha256', 'binding_sha256', 'status', 'counts', 'checkpoint', 'last_confirmed', 'hold', 'times', 'manifest', 'time_binding'}
            and terminal['version'] == server.storage.VERSION and terminal['scope'] == 'software_research_only'
            and terminal['G0_G4'] == 'not_assessed' and terminal['binding_sha256'] == source['time_binding_sha256']
            and all(storage._canonical(terminal[k]) == storage._canonical(progress[k]) for k in
                ('artifact_sha256', 'context_sha256', 'status', 'counts', 'checkpoint', 'last_confirmed', 'hold', 'times')))
        manifest = terminal['manifest']; _parsed(Manifest, manifest); identity = manifest['identity']
        _need(continuation._hash(manifest) == source['context_sha256'] and identity == source['model_identity']
            and identity['engine_code_sha256'] == continuation.CODE_SHA256 and identity['driver_code_sha256'] == driver.CODE_SHA256
            and identity['short_code_sha256'] == driver.short.CODE_SHA256 and identity['management_code_sha256'] == driver.management.CODE_SHA256
            and identity['rhs_code_sha256'] == joint.CODE_SHA256 and identity['component_code_sha256'] == joint.COMPONENT_CODE_SHA256
            and identity['profile_sha256'] == server.evidence._PROFILE_HASHES)
        grid = terminal['time_binding']; numerical = manifest['numerical']; dt = numerical['step_seconds']
        _need(continuation._hash(grid) == source['time_binding_sha256'] and grid['context_sha256'] == source['context_sha256']
            and grid['version'] == server.clock.VERSION and grid['time_rule'] == server.clock.TIME_RULE
            and grid['time_code_sha256'] == server.clock.CODE_SHA256 and grid['step_count'] == numerical['step_count'] == progress['planned_steps']
            and grid['start_utc'] == packet['input']['start_utc'] and grid['end_utc'] == packet['input']['end_utc']
            and numerical['duration_seconds'] == dt*numerical['step_count'] and 0 < numerical['duration_seconds'] <= 600)
        last = terminal['last_confirmed']; times = terminal['times']; _parsed(Snapshot, last)
        _point(times['last_confirmed'], last, grid, dt); _need(last['step_index'] == progress['steps'])
        held = terminal['hold']; cp = terminal['checkpoint']; hold = None
        if progress['status'] == 'hold':
            _need(cp is None and type(held) is dict and set(held) == {'step_index', 'elapsed_seconds', 'phase', 'reason'})
            _point(times['hold'], held, grid, dt)
            _need(type(held['reason']) is str and 0 < len(held['reason']) <= 4096)
            reason = held['reason'].partition(':')[0]
            hold = {'reason_code': reason if re.fullmatch(r'[A-Z][A-Z0-9_]{0,99}', reason) else 'CALCULATION_HOLD', 'phase': held['phase'],
                'time_meaning': 'failed_grid_boundary', 'time': times['hold']}
            _need(last['step_index'] <= held['step_index'])
        else:
            _need(held is None and times['hold'] is None and type(cp) is dict and set(cp) == {'sha256', 'value'}
                and continuation._hash(cp['value']) == cp['sha256'] and cp['value']['context_sha256'] == source['context_sha256']
                and cp['value']['next_index'] == numerical['step_count']+1 and cp['value']['last_confirmed'] == last
                and cp['value']['output_cursor'] == progress['counts']['samples'] and cp['value']['event_cursor'] == progress['counts']['events'])
        summary = _parsed(Summary, {'status': progress['status'], 'manifest': manifest,
            'last_confirmed': {'value': last, 'time': times['last_confirmed']},
            'checkpoint_sha256': None if cp is None else cp['sha256'], 'hold': hold})
        projected_page = None
        if view == 'summary': _need(page is None and limit is None)
        else:
            _need(view in ('samples', 'events') and type(page) is dict and set(page) == {'version', 'artifact_sha256', 'kind', 'start', 'total', 'records'}
                and page['version'] == server.storage.VERSION and page['artifact_sha256'] == packet['artifact']['sha256'] and page['kind'] == view
                and type(page['start']) is int and type(page['total']) is int and type(page['records']) is list
                and type(limit) is int and 1 <= limit <= (64 if view == 'samples' else 8))
            rows = page['records']; previous = -1
            for row in rows:
                _need(type(row) is dict and set(row) == {'value', 'time'}); value = row['value']
                _point(row['time'], value, grid, dt)
                _need(previous < value['step_index'] <= progress['steps'] and (held is None or value['step_index'] < held['step_index']))
                previous = value['step_index']
            rows = rows if view == 'samples' else [_event(r, identity) for r in rows]
            end = page['start'] + len(rows)
            projected_page = _parsed(SamplePage if view == 'samples' else EventPage,
                {'kind': view, 'offset': page['start'], 'limit': limit, 'total': page['total'],
                    'next_offset': end if end < page['total'] else None, 'records': rows})
        registration = packet['binding']['registration']
        value = JointReplay(schema_version=VERSION, result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z'),
            study_id=packet['study_id'], revision=packet['revision'], farm={k: packet['farm'][k] for k in Farm.model_fields},
            reference={'storage_status': packet['status'], 'claim_scope': packet['claim_scope'], 'G0_G4': packet['G0_G4'],
                'input': packet['input'], 'artifact': packet['artifact'], 'code': packet['code'], 'payload_sha256': record['payload_sha256'],
                **{k: registration[k] for k in ('normalization', 'profile_applicability')},
                **{k: source[k] for k in ('normalization_version', 'qc_version', 'input_evidence_version')},
                'model': identity, 'time_grid': {k: grid[k] for k in TimeGrid.model_fields},
                'last_confirmed': times['last_confirmed'], 'failed_boundary': times['hold']},
            summary=summary if view == 'summary' else None, page=projected_page)
        _public_bytes(value); return value
    except Exception: raise ProjectionHold('joint crop climate display unavailable') from None
