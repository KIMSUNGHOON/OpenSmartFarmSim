"""Research-only comparison of stored material time and declared cost coverage."""
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Annotated, Callable, Literal, NamedTuple
from uuid import UUID

from pydantic import AfterValidator, Field, model_validator

from . import crop_supply_material_quantities as quantities
from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyBlobStore
from .economic_contracts import untrusted_data
from .economic_cost_query import EconomicCostResultQuery, StoredCostResult
from .provenance import FrozenContract


VERSION = 'supply-material-resource-cost-scope-binding-v1'
REQUEST_VERSION = 'supply-material-resource-cost-scope-request-v1'
MAX_REQUEST_BYTES = 131072
MAX_RESULT_BYTES = 2097152
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_DEPENDENCY_FILES = ('crop_supply_material_quantities.py', 'economic_cost_query.py',
                     'economic_batch_query.py', 'content_access.py')
_DEPENDENCIES = tuple((name, sha256(Path(__file__).with_name(name).read_bytes()).hexdigest())
                      for name in _DEPENDENCY_FILES)
_UNIT_PAIRS = (('electricity', 'kWh_e', 'KRW/kWh_e'),
               ('fuel', 'L', 'KRW/L'), ('water', 'L', 'KRW/L'))
_PERIOD_KINDS = ('purchase', 'billing', 'usage')
_PRODUCT_HOLDS = ('farm_current_custody_unverified', 'resource_cost_declaration_unregistered',
                  'window_cost_allocation_not_established')
_TIME = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\Z', re.ASCII)


class MaterialCostScopeHold(ValueError):
    """The original selections and explicit resource declaration cannot be bound."""


def _need(condition):
    if not condition:
        raise MaterialCostScopeHold('material resource cost binding unavailable')


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def _parse_time(value):
    if type(value) is not str or _TIME.fullmatch(value) is None:
        raise ValueError('explicit bounded ISO time required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.utcoffset() is None:
        raise ValueError('aware time required')
    return parsed


def _time_text(value):
    _parse_time(value)
    return value


def _name(value):
    if not value or value.strip() != value:
        raise ValueError('explicit nonblank name required')
    return value


def _uuid(value):
    if str(UUID(value)) != value:
        raise ValueError('canonical UUID required')
    return value


Name = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_name)]
Digest = Annotated[str, Field(min_length=64, max_length=64, pattern=r'^[0-9a-f]{64}$')]
JobID = Annotated[str, AfterValidator(_uuid)]
TimeText = Annotated[str, AfterValidator(_time_text)]


class MaterialSourceProvenance(FrozenContract):
    source_ref: Name
    metadata_sha256: Digest
    published_at: TimeText | None
    available_at: TimeText | None


class _Declaration(FrozenContract):
    declaration_id: Name
    revision: Name
    origin: Literal['user']
    evidence_level: Literal['assumed']
    relation: Literal['independent_user_assumption']
    source_ref: Name
    assumption_scope: Name
    available_at: TimeText


class _Material(FrozenContract):
    root_sha256: Digest
    projection_code_sha256: Digest
    quantity_sha256: Digest
    first_frame: int = Field(ge=0, lt=512)
    last_frame: int = Field(ge=0, lt=512)

    @model_validator(mode='after')
    def ordered(self):
        if self.first_frame > self.last_frame:
            raise ValueError('ordered original frame selection required')
        return self


class _Economic(FrozenContract):
    job_id: JobID
    input_sha256: Digest
    artifact_sha256: Digest
    trace_id: Digest
    publication_id: JobID


class _Input(FrozenContract):
    input_id: Name
    revision: Name


class _Period(FrozenContract):
    kind: Literal['purchase', 'billing', 'usage']
    boundary: Literal['half_open']
    calendar: Literal['Asia/Seoul']
    start_at: TimeText
    end_at: TimeText

    @model_validator(mode='after')
    def positive(self):
        if _parse_time(self.start_at) >= _parse_time(self.end_at):
            raise ValueError('positive independent period required')
        return self


class _Cost(FrozenContract):
    category: Literal['variable', 'fixed']
    cost_id: Name
    cost_sha256: Digest
    quantity_input: _Input
    unit_cost_input: _Input
    resource_kind: Literal['electricity', 'fuel', 'water']
    period: _Period
    included_items: tuple[Name, ...] = Field(min_length=1, max_length=32)
    excluded_items: tuple[Name, ...] = Field(max_length=32)
    unknown_items: tuple[Name, ...] = Field(max_length=32)

    @model_validator(mode='after')
    def distinct_items(self):
        items = self.included_items + self.excluded_items + self.unknown_items
        if len(items) != len(set(items)):
            raise ValueError('distinct included excluded and unknown items required')
        return self


class MaterialCostScopeRequest(FrozenContract):
    schema_version: Literal['supply-material-resource-cost-scope-request-v1']
    declaration: _Declaration
    material: _Material
    economic: _Economic
    costs: tuple[_Cost, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode='after')
    def distinct_costs(self):
        if len(self.costs) != len({cost.cost_id for cost in self.costs}):
            raise ValueError('distinct original costs required')
        return self


def _utc_fraction(value):
    try:
        _need(type(value) is datetime and value.utcoffset() is not None)
        delta = value.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
        return Fraction(delta.days * 86400 + delta.seconds) + Fraction(delta.microseconds, 1_000_000)
    except (ValueError, TypeError, OverflowError):
        raise MaterialCostScopeHold('material resource cost time unavailable') from None


def _coverage(a, b, c, d):
    _need(all(type(v) is Fraction for v in (a, b, c, d)) and a <= b and c < d)
    if a == b:
        relation = ('point_before' if a < c else 'point_at_start' if a == c else
                    'point_inside' if a < d else 'point_at_end' if a == d else 'point_after')
        return {'relation': relation, 'coverage': 'point_covered' if c <= a < d else 'point_not_covered'}
    if b < c: relation = 'before'
    elif b == c: relation = 'meets'
    elif a > d: relation = 'after'
    elif a == d: relation = 'met_by'
    elif a == c: relation = 'starts' if b < d else 'equal' if b == d else 'started_by'
    elif b == d: relation = 'finished_by' if a < c else 'finishes'
    elif a < c: relation = 'overlaps' if b < d else 'contains'
    else: relation = 'during' if b < d else 'overlapped_by'
    coverage = ('whole_window' if c <= a and b <= d else
                'partial_window' if max(a, c) < min(b, d) else 'no_overlap')
    return {'relation': relation, 'coverage': coverage}


class _Program(NamedTuple):
    need: Callable
    parse_time: Callable
    utc: Callable
    coverage: Callable
    raw: Callable
    exact: Callable
    material_read: Callable
    material_raw: Callable
    cost_read: Callable
    cost_access: Callable
    guard: Callable
    pointers: Callable
    capture: Callable
    directory: Callable
    request_type: type
    provenance_type: type
    version: str
    code_sha256: str
    dependencies: tuple
    unit_pairs: tuple
    period_kinds: tuple
    product_holds: tuple
    request_cap: int
    result_cap: int


def _function(value):
    return getattr(value, '__func__', value)


def _exact(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator),
            'unit': 's_since_unix_epoch'}


class MaterialCostScopeBinding:
    def __init__(self, directory, access, root_sha256, cost_query, *, material_provenance):
        try:
            _need(type(self) is MaterialCostScopeBinding and type(access) is ContentAccess
                  and type(cost_query) is EconomicCostResultQuery
                  and type(material_provenance) is MaterialSourceProvenance)
            _need(type(root_sha256) is str and re.fullmatch('[0-9a-f]{64}', root_sha256) is not None)
            directory = Path(directory)
            _need(directory.is_absolute() and '..' not in directory.parts)
            self.directory, self.access, self.root_sha256 = directory, access, root_sha256
            self.cost_query = cost_query
            self.material_provenance = MaterialSourceProvenance.model_validate(untrusted_data(material_provenance))
            self._program = self._capture_program()
            self._fixed = self._program.pointers(self, self._program)
        except Exception:
            raise MaterialCostScopeHold('material resource cost binding unavailable') from None

    def _capture_program(self):
        return _Program(_need, _parse_time, _utc_fraction, _coverage, _raw, _exact,
            quantities.read_material_quantity_window, quantities.reader.raw,
            _function(self.cost_query.read), _function(self.cost_query._access), _function(self._guard),
            _function(self._pointers), _function(self._capture_program), _function(self._directory_identity),
            MaterialCostScopeRequest, MaterialSourceProvenance, VERSION, CODE_SHA256, _DEPENDENCIES,
            _UNIT_PAIRS, _PERIOD_KINDS, _PRODUCT_HOLDS, MAX_REQUEST_BYTES, MAX_RESULT_BYTES)

    def _directory_identity(self):
        with MorphologyBlobStore(self.directory, self.access) as store:
            info = os.fstat(store._fd)
            return info.st_dev, info.st_ino

    def _pointers(self, program):
        return (self.directory, self.access, self.root_sha256, self.cost_query,
            self.material_provenance, program.raw(self.material_provenance.model_dump(mode='json')),
            self.cost_query._pointers(), program.directory(self), self._program, program.capture(self))

    def _guard(self, tenant, program):
        program.need(program.pointers(self, program) == self._fixed
              and sha256(Path(__file__).read_bytes()).hexdigest() == program.code_sha256
              and tuple((name, sha256(Path(__file__).with_name(name).read_bytes()).hexdigest())
                        for name, _ in program.dependencies) == program.dependencies)
        program.cost_access(self.cost_query, tenant)
        program.need(program.pointers(self, program) == self._fixed
              and sha256(Path(__file__).read_bytes()).hexdigest() == program.code_sha256
              and tuple((name, sha256(Path(__file__).with_name(name).read_bytes()).hexdigest())
                        for name, _ in program.dependencies) == program.dependencies)

    def prepare(self, tenant, request_raw):
        program = self._program
        need = program.need
        try:
            program.guard(self, tenant, program)
            need(type(request_raw) is bytes and 1 <= len(request_raw) <= program.request_cap)
            value = json.loads(request_raw)
            need(type(value) is dict and program.raw(value) == request_raw)
            request = program.request_type.model_validate_json(request_raw)
            need(request.material.root_sha256 == self.root_sha256)
            window = {'first_frame': request.material.first_frame, 'last_frame': request.material.last_frame}
            material = program.material_read(self.directory, self.access, self.root_sha256, **window)
            material_raw = program.material_raw(material)
            need(sha256(material_raw).hexdigest() == request.material.quantity_sha256
                  and material['projection_code_sha256'] == request.material.projection_code_sha256
                  and material['source']['artifact_sha256'] == self.root_sha256
                  and all(material['window'][key] == expected for key, expected in window.items()))
            program.guard(self, tenant, program)
            stored = program.cost_read(self.cost_query, tenant, request.economic.job_id)
            need(type(stored) is StoredCostResult)
            envelope = json.loads(stored.raw)
            need(envelope['job_id'] == request.economic.job_id
                  and envelope['input_sha256'] == request.economic.input_sha256
                  and sha256(stored.raw).hexdigest() == request.economic.artifact_sha256
                  and envelope['result']['trace_id'] == stored.result.trace_id == request.economic.trace_id
                  and str(stored.publication_id) == request.economic.publication_id)
            program.guard(self, tenant, program)
            result = envelope['result']; ledger = result['base_result']['ledger']
            decision = program.utc(program.parse_time(ledger['decision_at']))
            need(program.utc(program.parse_time(request.declaration.available_at)) <= decision)

            def absolute(at):
                elapsed = at['elapsed_seconds_exact']
                need(elapsed['unit'] == 's')
                return (program.utc(program.parse_time(at['time_origin_utc']))
                        + Fraction(int(elapsed['numerator']), int(elapsed['denominator'])))

            a, b = (absolute(material['window'][key]) for key in ('start_at', 'end_at'))
            originals = {(line['category'], line['cost']['id']): line for line in result['lines']}
            rows = []
            for declared, reference in zip(request.costs, value['costs'], strict=True):
                line = originals.get((declared.category, declared.cost_id))
                need(line is not None)
                cost = line['cost']
                need(sha256(program.raw(cost)).hexdigest() == declared.cost_sha256
                      and {k: cost['quantity'][k] for k in ('input_id', 'revision')} == reference['quantity_input']
                      and {k: cost['unit_cost'][k] for k in ('input_id', 'revision')} == reference['unit_cost_input']
                      and (declared.resource_kind, cost['quantity']['unit'], cost['unit_cost']['unit']) in program.unit_pairs)
                c, d = (program.utc(program.parse_time(getattr(declared.period, key)))
                        for key in ('start_at', 'end_at'))
                rows.append({'reference': reference, 'original_line': line,
                    'amount_scope': 'original_cost_line_only', 'allocated_window_cost': None,
                    'temporal_relation': program.coverage(a, b, c, d),
                    'period_semantics_established': declared.period.kind,
                    'other_period_kinds_not_established': [kind for kind in program.period_kinds if kind != declared.period.kind]})
            selected = {cost.cost_id for cost in request.costs}
            unselected = [{'category': line['category'], 'cost_id': line['cost']['id'],
                'cost_sha256': sha256(program.raw(line['cost'])).hexdigest()}
                for line in result['lines'] if line['cost']['id'] not in selected]
            provenance = self.material_provenance.model_dump(mode='json')

            def availability(key):
                known = provenance[key]
                return ('unknown' if known is None else 'before_or_at_decision'
                        if program.utc(program.parse_time(known)) <= decision else 'after_decision')

            base = envelope['input']['base_input']
            economic = {**value['economic'], **{key: envelope[key] for key in
                ('result_sha256', 'code_sha256', 'environment_sha256')},
                'published_at': stored.published_at.isoformat(),
                **{key: base[key] for key in ('scenario_id', 'scenario_revision', 'scenario_sha256', 'scenario_source_job_id')},
                'decision_at': ledger['decision_at'], 'period_start': result['period_start'], 'period_end': result['period_end']}
            payload = {'schema_version': program.version, 'scope': 'software_research_only',
                'claim_scope': 'independent_user_resource_cost_scope_only', 'tenant_id': tenant,
                'request_sha256': sha256(request_raw).hexdigest(), 'declaration': value['declaration'],
                'material': {'quantity': material, 'quantity_sha256': request.material.quantity_sha256,
                    'provenance': provenance, 'temporal_support': {'kind': 'point' if a == b else 'interval',
                        'boundary': 'point' if a == b else 'half_open', 'start_utc_exact': program.exact(a), 'end_utc_exact': program.exact(b)}},
                'economic': economic, 'costs': rows, 'unselected_costs': unselected,
                'resource_kinds_not_selected': [kind for kind, _, _ in program.unit_pairs
                    if kind not in {cost.resource_kind for cost in request.costs}],
                'product_holds': list(program.product_holds),
                'as_of_decision': {'material_published_relation': availability('published_at'),
                    'material_available_relation': availability('available_at'), 'ex_ante_eligibility': 'not_established'},
                'code_sha256': program.code_sha256, 'dependency_sha256': dict(program.dependencies),
                'G0_G4': 'not_assessed', 'R2': 'not_approved'}
            payload['binding_id'] = sha256(program.raw(payload)).hexdigest()
            after = program.cost_read(self.cost_query, tenant, request.economic.job_id)
            need(type(after) is StoredCostResult and (after.raw, after.publication_id, after.published_at)
                  == (stored.raw, stored.publication_id, stored.published_at))
            current_material = program.material_read(self.directory, self.access, self.root_sha256, **window)
            need(program.material_raw(current_material) == material_raw)
            program.guard(self, tenant, program)
            encoded = program.raw(payload)
            need(1 <= len(encoded) <= program.result_cap)
            program.guard(self, tenant, program)
            return encoded
        except PermissionError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, OSError, ArithmeticError, RuntimeError, RecursionError):
            raise MaterialCostScopeHold('material resource cost binding unavailable') from None
