"""Closed public quantities from registered synthetic harvest reads."""
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import AfterValidator, BeforeValidator, Field, StrictFloat, StrictInt, model_validator

from .api_crop_replay import _Public, Digest, Name, UtcStamp
from .thermal_run_store import _canonical

VERSION='crop-harvest-replay-v1'
MAX_RESPONSE_BYTES=2*1024**2
MAX_ROWS=262144
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
_FIXED=VERSION,MAX_RESPONSE_BYTES,MAX_ROWS,CODE_SHA256
RESULT_ID_PATTERN=r'^crop-harvest-registered-result-v1:[0-9a-f]{64}$'
ResultID=Annotated[str,Field(strict=True,pattern=RESULT_ID_PATTERN)]
ParentID=Annotated[str,Field(strict=True,pattern=r'^crop-cycle-verified-result-v1:[0-9a-f]{64}$')]
Index=Annotated[int,Field(strict=True,ge=0,le=MAX_ROWS)]
Text=Annotated[str,Field(strict=True,min_length=1,max_length=128),AfterValidator(lambda v:v if v.isprintable() else _fail())]
U=TypeVar('U')
C=Literal['mg_CH2O/m2_floor'];N=Literal['fruits_equivalent/m2_floor']
DM=Literal['kg_DM/m2_floor'];FW=Literal['kg_FW/m2_floor']
Purpose=Literal['harvest','thinning','disposal','sampling']


class HarvestProjectionHold(ValueError):
    """No displayable public harvest arithmetic."""


def _fail():raise HarvestProjectionHold('harvest research display unavailable')


def _need(condition):
    if not condition:_fail()


def _false(value):
    _need(type(value) is bool and value is False);return value


FalseValue=Annotated[Literal[False],BeforeValidator(_false)]


def _number(value):
    _need(type(value) in (int,float) and isfinite(value));return value


Number=Annotated[StrictInt|StrictFloat,AfterValidator(_number)]


def _second(value):
    _need(len(value)==20);return value


At=Annotated[UtcStamp,AfterValidator(_second)]


class Quantity(_Public,Generic[U]):
    value: Number
    unit: U

    @model_validator(mode='after')
    def nonnegative(self):
        _need(self.value>=0);return self


class Rational(_Public):
    numerator: Annotated[str,Field(strict=True,pattern=r'^(?:0|-?[1-9][0-9]*)$',max_length=2048)]
    denominator: Annotated[str,Field(strict=True,pattern=r'^[1-9][0-9]*$',max_length=2048)]

    def fraction(self):return Fraction(int(self.numerator),int(self.denominator))

    @model_validator(mode='after')
    def canonical(self):
        value=self.fraction();_need(str(value.numerator)==self.numerator and str(value.denominator)==self.denominator)
        return self


class SignedRationalQuantity(_Public,Generic[U]):
    value: Number
    unit: U
    exact: Rational

    @model_validator(mode='after')
    def rounded(self):
        fraction=self.exact.fraction();_need(float(fraction)==self.value and (fraction==0 or self.value!=0))
        return self


class RationalQuantity(SignedRationalQuantity[U],Generic[U]):
    @model_validator(mode='after')
    def nonnegative(self):
        _need(self.value>=0);return self


class Quantities(_Public):
    carbohydrate: RationalQuantity[C]
    number: RationalQuantity[N]
    dry_matter: RationalQuantity[DM]
    fresh_matter: RationalQuantity[FW]


class Source(_Public):
    result_id: ParentID
    payload_sha256: Digest
    input_root_sha256: Digest
    artifact_sha256: Digest
    math_manifest_sha256: Digest
    source_status: Literal['completed','hold']


class Farm(_Public):
    scenario_id: Name
    scenario_revision: Name
    registration_sha256: Digest
    crop_id: Name


class Dependencies(_Public):
    current_query: Digest
    canonical_json: Digest


class Population(_Public):
    population_id: Text
    scope: Literal['all_model_fruit_cohorts']
    basis: Literal['m2_floor']
    basis_evidence_id: Text


class Segment(_Public):
    segment_id: Text
    start_at: At
    end_at: At
    eta: Quantity[Literal['mg_DM/mg_CH2O']]
    dmc: Quantity[Literal['kg_DM/kg_FW']]

    @model_validator(mode='after')
    def bounds(self):
        _need(self.start_at<self.end_at and self.eta.value>0 and 0<self.dmc.value<=1);return self


class MassParameters(_Public):
    version: Literal['crop-removal-mass-parameters-v1']
    parameter_id: Text
    revision: Text
    origin: Literal['synthetic']
    evidence_level: Literal['assumed']
    evidence_id: Text
    available_at: At
    population: Population
    policy: Literal['constant_per_original_interval']
    sha256: Digest
    segment: Segment
    rounding: Literal['nearest_float64_from_exact_input_floats_per_row']


class TerminalPosition(_Public):
    samples: Annotated[list[Index],Field(min_length=2,max_length=2)]
    sample_sha256: Annotated[list[Digest],Field(min_length=2,max_length=2)]

    @model_validator(mode='after')
    def adjacent(self):
        _need(self.samples[1]==self.samples[0]+1);return self


class EventPosition(_Public):
    event: Index
    input_id: Annotated[str,Field(strict=True,min_length=1,max_length=MAX_RESPONSE_BYTES)]
    event_sha256: Digest


class Cohorts(_Public):
    fruit_carbohydrate: Annotated[list[Quantity[C]],Field(min_length=50,max_length=50)]
    fruit_number: Annotated[list[Quantity[N]],Field(min_length=50,max_length=50)]


class Removal(_Public):
    schema_version: Literal['crop-removal-ledger-v1']
    code_sha256: Digest
    dependency_sha256: Dependencies
    claim_scope: Literal['research_removal_math_only']
    rights_or_gate_approval: FalseValue
    row_id: Annotated[str,Field(strict=True,pattern=r'^crop-removal-ledger-v1:[0-9a-f]{64}$')]
    source: Source
    kind: Literal['model_terminal_outflow','explicit_fruit_removal']
    position: TerminalPosition|EventPosition
    start_at: At
    end_at: At
    carbohydrate: Quantity[C]
    number: Quantity[N]
    cohorts: Cohorts|None

    @model_validator(mode='after')
    def position_and_time(self):
        terminal=self.kind=='model_terminal_outflow'
        _need(isinstance(self.position,TerminalPosition) if terminal else isinstance(self.position,EventPosition))
        _need(self.start_at<self.end_at and self.cohorts is None if terminal else self.start_at==self.end_at and self.cohorts is not None)
        return self


class PerEquivalent(_Public):
    value: Number|None
    unit: Literal['kg_FW/fruit_equivalent']

    @model_validator(mode='after')
    def nonnegative(self):
        _need(self.value is None or self.value>=0);return self


class Mass(_Public):
    version: Literal['crop-removal-mass-v1']
    code_sha256: Digest
    dependency_sha256: Dependencies
    removal_sha256: Digest
    parameter_sha256: Digest
    segment_id: Text
    schema_version: Literal['crop-removal-mass-v1']
    row_id: Annotated[str,Field(strict=True,pattern=r'^crop-removal-mass-v1:[0-9a-f]{64}$')]
    claim_scope: Literal['synthetic_removal_mass_math_only']
    rights_or_gate_approval: FalseValue
    removal: Removal
    parameters: MassParameters
    dry_matter: Quantity[DM]
    fresh_matter: Quantity[FW]
    fresh_mass_per_equivalent: PerEquivalent


class AllocationDeclaration(_Public):
    version: Literal['crop-harvest-allocation-v1']
    allocation_id: Text
    revision: Text
    origin: Literal['synthetic']
    evidence_level: Literal['assumed']
    evidence_id: Text
    available_at: At
    source: Source
    population: Population
    mass_parameter_sha256: Digest
    policy: Literal['proportional_original_population']


class AllocationFraction(_Public):
    value: Annotated[str,Field(strict=True,pattern=r'^(?:0(?:\.[0-9]{1,18})?|1(?:\.0{1,18})?)$')]
    unit: Literal['1']

    @model_validator(mode='after')
    def positive(self):
        _need(0<Fraction(self.value)<=1);return self


class TerminalSelector(_Public):
    kind: Literal['model_terminal_outflow']
    first_sample: Index
    last_sample: Index

    @model_validator(mode='after')
    def ordered(self):
        _need(self.first_sample<self.last_sample);return self


class EventSelector(_Public):
    kind: Literal['explicit_fruit_removal']
    event: Index


class Rule(_Public):
    assignment_id: Text
    selector: TerminalSelector|EventSelector
    purpose: Purpose
    fraction: AllocationFraction


class Observation(_Public):
    observation_id: Text
    origin: Literal['synthetic']
    evidence_level: Literal['assumed']
    evidence_id: Text
    available_at: At
    start_at: At
    end_at: At
    assignment_ids: Annotated[list[Text],Field(min_length=1,max_length=256)]
    fresh_matter: Quantity[FW]

    @model_validator(mode='after')
    def ordered(self):
        _need(self.start_at<=self.end_at and len(set(self.assignment_ids))==len(self.assignment_ids));return self


class AllocationParameters(AllocationDeclaration):
    rules: Annotated[list[Rule],Field(max_length=256)]
    observations: Annotated[list[Observation],Field(max_length=64)]


class Allocation(_Public):
    assignment_id: Text
    purpose: Purpose
    fraction: AllocationFraction
    quantities: Quantities


class Unassigned(_Public):
    fraction: RationalQuantity[Literal['1']]
    quantities: Quantities

    @model_validator(mode='after')
    def bounded(self):
        _need(self.fraction.value<=1);return self


class HarvestRow(_Public):
    version: Literal['crop-harvest-allocation-result-v1']
    code_sha256: Digest
    dependency_sha256: Dependencies
    mass_row_sha256: Digest
    allocation_sha256: Digest
    schema_version: Literal['crop-harvest-allocation-result-v1']
    row_id: Annotated[str,Field(strict=True,pattern=r'^crop-harvest-allocation-result-v1:[0-9a-f]{64}$')]
    claim_scope: Literal['synthetic_harvest_allocation_math_only']
    rights_or_gate_approval: FalseValue
    mass: Mass
    allocation_parameters: AllocationDeclaration
    allocations: Annotated[list[Allocation],Field(max_length=256)]
    unassigned: Unassigned
    rounding: Literal['nearest_float64_with_exact_rational_portions_of_stored_mass_row']


class Total(_Public):
    rows: Annotated[int,Field(strict=True,ge=0,le=MAX_ROWS*256)]
    quantities: Quantities

    @model_validator(mode='after')
    def empty(self):
        if self.rows==0:_need(all(q.exact.fraction()==0 for q in self.quantities.__dict__.values()))
        return self


class PurposeTotals(_Public):
    harvest: Total
    thinning: Total
    disposal: Total
    sampling: Total
    unassigned: Total


class KindTotals(_Public):
    model_terminal_outflow: PurposeTotals
    explicit_fruit_removal: PurposeTotals


class Comparison(_Public):
    observation: Observation
    status: Literal['compared_synthetic_fixture','incomplete_selected_window']
    modeled_fresh_matter: RationalQuantity[FW]|None
    observed_minus_modeled: SignedRationalQuantity[FW]|None

    @model_validator(mode='after')
    def availability(self):
        compared=self.status=='compared_synthetic_fixture'
        _need((self.modeled_fresh_matter is not None)==compared and (self.observed_minus_modeled is not None)==compared)
        if compared:
            _need(self.observed_minus_modeled.exact.fraction()==Fraction(self.observation.fresh_matter.value)-self.modeled_fresh_matter.exact.fraction())
        return self


class HarvestSummary(_Public):
    schema_version: Literal['crop-harvest-allocation-summary-v1']
    code_sha256: Digest
    claim_scope: Literal['synthetic_harvest_allocation_math_only']
    rights_or_gate_approval: FalseValue
    source: Source
    allocation_sha256: Digest
    allocation_parameters: AllocationParameters
    row_count: Index
    row_chain_sha256: Digest
    totals_by_kind_and_purpose: KindTotals
    observation_comparisons: Annotated[list[Comparison],Field(max_length=64)]
    rounding: Literal['nearest_float64_with_exact_rational_sum_of_portions']


class QueryDependencies(_Public):
    registry: Digest
    artifact: Digest
    crop_query: Digest


class Reference(_Public):
    storage_status: Literal['stored_unpublished_research']
    claim_scope: Literal['synthetic_harvest_allocation_math_only']
    scope: Literal['software_research_only']
    gates: Literal['not_assessed']
    temporal_provenance: Literal['synthetic_research_program']
    rights_or_gate_approval: FalseValue
    parent_result_id: ParentID
    source: Source
    payload_sha256: Digest
    artifact_sha256: Digest
    row_count: Index
    row_chain_sha256: Digest
    mass_parameter_sha256: Digest
    allocation_parameter_sha256: Digest
    publication_code_sha256: Digest
    registry_schema_code_sha256: Digest
    artifact_code_sha256: Digest
    query_version: Literal['crop-harvest-registered-current-query-v1']
    query_code_sha256: Digest
    query_dependency_sha256: QueryDependencies
    projection_code_sha256: Digest


class HarvestPage(_Public):
    offset: Index
    limit: Annotated[int,Field(strict=True,ge=1,le=64)]
    total: Index
    next_offset: Index|None
    records: Annotated[list[HarvestRow],Field(max_length=64)]

    @model_validator(mode='after')
    def bounds(self):
        stop=self.offset+len(self.records)
        _need(self.offset<=stop<=self.total and len(self.records)==min(self.limit,self.total-self.offset)
            and self.next_offset==(stop if stop<self.total else None))
        return self


class HarvestReplay(_Public):
    schema_version: Literal['crop-harvest-replay-v1']
    result_id: ResultID
    recorded_at: UtcStamp
    farm: Farm
    reference: Reference
    summary: HarvestSummary|None
    page: HarvestPage|None

    @model_validator(mode='after')
    def one_view(self):
        _need((self.summary is None)!=(self.page is None))
        _need(self.reference.parent_result_id==self.reference.source.result_id)
        if self.summary is not None:
            _need(self.summary.source==self.reference.source and self.summary.row_count==self.reference.row_count
                and self.summary.row_chain_sha256==self.reference.row_chain_sha256
                and self.summary.allocation_sha256==self.reference.allocation_parameter_sha256)
        else:_need(self.page.total==self.reference.row_count)
        return self


def _hash(value):return sha256(_canonical(value)).hexdigest()


def _profile(profile,packet):
    _need(profile['source']==packet['source'] and profile['mass_parameter_sha256']==packet['parameters']['mass_sha256']
        and _hash(profile)==packet['parameters']['allocation_sha256'])
    rules={};edges={};events={}
    for rule in profile['rules']:
        name=rule['assignment_id'];_need(name not in rules);rules[name]=rule
        weight=Fraction(rule['fraction']['value']);selector=rule['selector']
        if selector['kind']=='model_terminal_outflow':
            left,right=selector['first_sample'],selector['last_sample']
            edges[left]=edges.get(left,Fraction(0))+weight;edges[right]=edges.get(right,Fraction(0))-weight
        else:
            event=selector['event'];events[event]=events.get(event,Fraction(0))+weight;_need(events[event]<=1)
    running=Fraction(0)
    for edge in sorted(edges):running+=edges[edge];_need(0<=running<=1)
    _need(running==0);seen=set();linked=set()
    for obs in profile['observations']:
        _need(obs['observation_id'] not in seen);seen.add(obs['observation_id'])
        for name in obs['assignment_ids']:
            _need(name in rules and name not in linked and rules[name]['purpose']=='harvest');linked.add(name)
    return rules


def _fraction(quantity):
    return Fraction(int(quantity['exact']['numerator']),int(quantity['exact']['denominator']))


def _row_checks(row,packet,profile,harvest):
    mass=row['mass'];removal=mass['removal'];parameters=mass['parameters']
    for item in (row,mass,removal):
        _need(item['code_sha256']==harvest.CODE_SHA256 and item['dependency_sha256']==harvest.DEPENDENCY_SHA256)
    _need(removal['source']==packet['source'] and mass['parameter_sha256']==parameters['sha256']==packet['parameters']['mass_sha256']
        and row['allocation_sha256']==packet['parameters']['allocation_sha256']
        and row['allocation_parameters']=={k:v for k,v in profile.items() if k not in ('rules','observations')}
        and parameters['population']==profile['population'] and mass['segment_id']==parameters['segment']['segment_id']
        and mass['removal_sha256']==_hash(removal) and row['mass_row_sha256']==_hash(mass))
    for item,keys in ((removal,('code_sha256','dependency_sha256','source','kind','position')),
            (mass,('version','code_sha256','dependency_sha256','removal_sha256','parameter_sha256','segment_id')),
            (row,('version','code_sha256','dependency_sha256','mass_row_sha256','allocation_sha256'))):
        identity={k:item[k] for k in keys}
        if item is removal:identity={'version':removal['schema_version'],**identity}
        _need(item['row_id']==item['schema_version']+':'+_hash(identity))
    segment=parameters['segment'];start,end=removal['start_at'],removal['end_at']
    _need(segment['start_at']<=start<=end<=segment['end_at'])
    _need((mass['fresh_mass_per_equivalent']['value'] is None)==(removal['number']['value']==0))
    if removal['cohorts'] is not None:
        from math import fsum
        _need(fsum(q['value'] for q in removal['cohorts']['fruit_carbohydrate'])==removal['carbohydrate']['value']
            and fsum(q['value'] for q in removal['cohorts']['fruit_number'])==removal['number']['value'])
    applies=[]
    for rule in profile['rules']:
        selector=rule['selector']
        if selector['kind']!=removal['kind']:continue
        if (selector['first_sample']<=removal['position']['samples'][0]<selector['last_sample']
                if removal['kind']=='model_terminal_outflow' else selector['event']==removal['position']['event']):applies.append(rule)
    _need(len(applies)==len(row['allocations']))
    weights=[]
    for part,rule in zip(row['allocations'],applies,strict=True):
        _need({k:part[k] for k in ('assignment_id','purpose','fraction')}=={k:rule[k] for k in ('assignment_id','purpose','fraction')})
        weights.append(Fraction(part['fraction']['value']))
    weights.append(_fraction(row['unassigned']['fraction']));_need(sum(weights,Fraction(0))==1)
    original={'carbohydrate':removal['carbohydrate'],'number':removal['number'],
        'dry_matter':mass['dry_matter'],'fresh_matter':mass['fresh_matter']}
    for part,weight in zip(row['allocations']+[row['unassigned']],weights,strict=True):
        for name,q in original.items():_need(_fraction(part['quantities'][name])==Fraction(q['value'])*weight)


def _public_bytes(projected):
    _need(type(projected) is HarvestReplay)
    checked=HarvestReplay.model_validate(projected.model_dump(mode='python'))
    raw=checked.model_dump_json().encode();_need(0<len(raw)<=MAX_RESPONSE_BYTES);return raw


def project_harvest_result(value, *, view='summary', limit=None):
    """Project current-query values; this pure function grants no display authority."""
    from . import crop_harvest_current_query as current
    registry=current.registry;harvest=current.harvest
    try:
        _need((VERSION,MAX_RESPONSE_BYTES,MAX_ROWS,CODE_SHA256)==_FIXED
            and CODE_SHA256==sha256(Path(__file__).read_bytes()).hexdigest() and MAX_ROWS==registry.schema.MAX_ROWS)
        _need(type(value) is dict and set(value)=={'record','summary','page','identity'})
        record=value['record'];identity=value['identity']
        _need(type(record) is dict and set(record)=={'result_id','payload_raw','payload_sha256','recorded_at'}
            and type(record['payload_raw']) is bytes and sha256(record['payload_raw']).hexdigest()==record['payload_sha256']
            and type(record['recorded_at']) is datetime and record['recorded_at'].utcoffset() is not None)
        packet=registry._decode(record['payload_raw']);_need(record['result_id']==packet['result_id'])
        current._pins()
        _need(type(identity) is dict and identity.get('rights_or_gate_approval') is False and identity=={'version':current.VERSION,'code_sha256':current.CODE_SHA256,'dependency_sha256':current.DEPENDENCY_SHA256,
            'result_id':record['result_id'],'payload_sha256':record['payload_sha256'],
            'artifact_sha256':packet['artifact']['sha256'],'parent_source':packet['source'],'rights_or_gate_approval':False})
        summary=HarvestSummary.model_validate(value['summary']);stored=summary.model_dump(mode='json')
        _need(_canonical(stored)==_canonical(value['summary']) and stored['source']==packet['source']
            and stored['row_count']==packet['artifact']['row_count'] and stored['row_chain_sha256']==packet['artifact']['row_chain_sha256']
            and stored['allocation_sha256']==packet['parameters']['allocation_sha256'] and stored['code_sha256']==harvest.CODE_SHA256)
        profile=stored['allocation_parameters'];_profile(profile,packet)
        _need([c['observation'] for c in stored['observation_comparisons']]==profile['observations']
            and sum(v['unassigned']['rows'] for v in stored['totals_by_kind_and_purpose'].values())==stored['row_count'])
        page=None
        if view=='summary':_need(value['page'] is None and limit is None)
        else:
            selected=value['page'];_need(view=='records' and type(selected) is dict and set(selected)=={'start','next','total','records'}
                and all(type(selected[k]) is int for k in ('start','next','total')) and type(limit) is int
                and selected['next']==selected['start']+len(selected['records']) and selected['total']==stored['row_count'])
            page=HarvestPage(offset=selected['start'],limit=limit,total=selected['total'],
                next_offset=selected['next'] if selected['next']<selected['total'] else None,records=selected['records'])
            rows=page.model_dump(mode='json')['records'];_need(_canonical(rows)==_canonical(selected['records']))
            _need(len({r['row_id'] for r in rows})==len(rows))
            for row in rows:_row_checks(row,packet,profile,harvest)
            if page.offset==0 and len(rows)==page.total:
                _need(sha256(b''.join(_canonical(r)+b'\n' for r in rows)).hexdigest()==stored['row_chain_sha256'])
        reference=Reference(storage_status=packet['status'],claim_scope=packet['claim_scope'],scope='software_research_only',
            gates='not_assessed',temporal_provenance='synthetic_research_program',rights_or_gate_approval=False,
            parent_result_id=packet['parent_result_id'],source=packet['source'],payload_sha256=record['payload_sha256'],
            artifact_sha256=packet['artifact']['sha256'],row_count=stored['row_count'],row_chain_sha256=stored['row_chain_sha256'],
            mass_parameter_sha256=packet['parameters']['mass_sha256'],allocation_parameter_sha256=packet['parameters']['allocation_sha256'],
            **packet['code'],query_version=identity['version'],query_code_sha256=identity['code_sha256'],query_dependency_sha256=identity['dependency_sha256'],
            projection_code_sha256=CODE_SHA256)
        projected=HarvestReplay(schema_version=VERSION,result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
            farm=packet['farm'],reference=reference,summary=summary if page is None else None,page=page)
        _public_bytes(projected);return projected
    except Exception:raise HarvestProjectionHold('harvest research display unavailable') from None
