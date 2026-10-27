"""Genuine repeated-organ contexts and grid resume; crop-organ-repeat-v1.md."""
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
from math import isfinite
from pathlib import Path
import json
from weakref import WeakKeyDictionary

from . import crop_organ_successor_point as material

legacy = material.resume
capture = legacy.capture

stock = capture.stock
numeric = stock.numeric
candidate = capture.candidate
Q, X, F = capture.Q, capture._fraction, Fraction.from_float
VERSION = 'individual-organ-repeat-continuation-research-v1'
CHECKPOINT_VERSION = 'repeat-individual-organ-continuation-checkpoint-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
MAX_CHECKPOINT_BYTES = capture.MAX_CHECKPOINT_BYTES
MAX_PROOF_BYTES = 16*1024**2
MAX_EVENTS = 512
AUXILIARY_SHA256 = {name:sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('crop_organ_repeat_events.py','crop_organ_repeat_proofs.py')}
_TOKEN = object()
_VERIFIED = WeakKeyDictionary()


class RepeatHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise RepeatHold(reason)


def _public(fn):
    @wraps(fn)
    def checked(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except RepeatHold:
            raise
        except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
            raise RepeatHold(str(error)) from None
    return checked


def _canonical(value):
    raw = stock._canonical(value)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 2MiB continuation context/response required')
    return raw


def _pins():
    pins = {**material._pins(),'backend/app/crop_organ_repeat.py':CODE_SHA256,
        **{'backend/app/'+name:h for name,h in AUXILIARY_SHA256.items()}}
    root = Path(__file__).resolve().parents[2]
    _need(all(sha256((root/name).read_bytes()).hexdigest() == h for name,h in pins.items()),
        'CODE_HOLD: original repeated-organ sources required')
    return pins


def _fence(context, data):
    descriptor = data['_descriptor']
    _need(type(context) is Context and context._token is _TOKEN
        and _canonical(descriptor) == context._raw and stock._hash(descriptor) == context.root_sha256,
        'CONTEXT_HOLD: original repeat context required')
    original = _authority(context._origin)
    _need(descriptor['origin_context_sha256'] == context._origin.root_sha256
        and data['point'] == original['point'] and data['source_snapshot'] == original['source_snapshot']
        and data['captured'] == descriptor['seed'] and data['initial_sample'] == descriptor['initial_sample']
        and data['initial_base'] == descriptor['initial_base'], 'SOURCE_HOLD: actual original authority and current seed required')
    _need(descriptor['receipt_sha256'] == [sha256(raw).hexdigest() for raw in context._receipts]
        and descriptor['source_code_sha256'] == _pins(), 'SOURCE_HOLD: original receipts/code required')


def _time(data, steps):
    saved = data['captured']; dt = F(saved['original_numerical']['step_seconds'])
    first_index = saved['original_grid_position']['completed_grid_index']; count = saved['original_numerical']['step_count']
    _need(type(steps) is int and 0 <= steps <= count-first_index, 'TIME_HOLD: original branch endpoint count required')
    return X(saved['at']['elapsed_seconds_exact']) if steps == 0 else dt*(first_index+steps)


def _sample(data, at, state, rhs):
    view = stock.short._view(rhs); gaps = deepcopy(view['curve_residuals'])
    return {'at':{'time_origin_utc':data['captured']['simulation_origin_utc'],'elapsed_seconds_exact':Q(at,'s')},
        'state':list(state),'derived':deepcopy(view['joint']['derived']),'curve_residuals':gaps,
        'curve_invariant_changes':[numeric._q(numeric._sum(q['value'],-a['value']),'m2') for q,a in zip(gaps,data['captured']['anchors'],strict=True)]}


def _clock(data, lifetime, at):
    saved = data['captured']; timeline = data['point']['before_candidate']['source_root_certificate']['source_timeline']
    age = X(timeline['age_exact'])+(X(lifetime['indoor_air_temperature_time'])-F(float(timeline['base_temperature']['value']))*at)/86400
    _need(age >= 0 and age < X(saved['schedule']['next_threshold_exact']), 'SCHEDULE_HOLD: nonnegative age before the first pending event required')
    return {**deepcopy(saved['schedule']),'age_exact':Q(age,'degC_day')}


def _books(context, data, sample, totals, steps, lifetime):
    saved = data['captured']; p = saved['program']; at = X(sample['at']['elapsed_seconds_exact'])
    duration = at-X(saved['at']['elapsed_seconds_exact']); initial = data['initial_sample']
    latent = context._source._root._profiles[-1].values['latent_heat']
    local = candidate._local(p,initial['state'],sample['state'],totals,initial['derived'],sample['derived'],duration,latent,steps)
    if steps == 0:
        _need(all(X(row['residual_exact']) == 0 for row in local.values()), 'BALANCE_HOLD: exact zero branch required')
        local = {name:{'residual_exact':row['residual_exact'],'budget_exact':Q(Fraction(0),row['budget_exact']['unit'])} for name,row in local.items()}
    root_p, root_seed, _ = stock.parent._context(context._source._root)
    a,b = tuple(map(F,root_seed['state'])),tuple(map(F,sample['state'])); n0 = len(root_p['leaves']); n = len(p['leaves'])
    m = len(p['stem_root_compartments']); t = {name:X(q) for name,q in lifetime.items()}; points = {name:X(q) for name,q in saved['point_totals_exact'].items()}
    first = stock.short._view(root_seed['evaluation'])['joint']['derived']
    rows = candidate._physical(p,a,b,t,first,sample['derived'],latent,n0,points)
    for i,base in enumerate(saved['birth_bases']['leaf']):
        elapsed = at-X(base['at_elapsed_seconds_exact']); _need(elapsed >= 0, 'TIME_HOLD: current state precedes leaf baseline')
        terms = (b[106+i]-X(base['thermal_age_exact']),
            -(t['indoor_air_temperature_time']-X(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*elapsed)/86400)
        rows[f'leaf_age_{i}'] = (terms,Fraction(0),Fraction(0),'degC_day')
    for label,start in [('leaf',106+2*n),('stem_root',106+3*n)]:
        for i,base in enumerate(saved['birth_bases'][label]):
            terms = (b[start+i]-F(base['carbon']['value']),-t[f'{label}_{i}_inflow'],t[f'{label}_{i}_maintenance'],t[f'{label}_{i}_removal'])
            rows[f'{label}_carbon_{i}'] = (terms,Fraction(0),Fraction(0),capture.point.MASS)
    rows['stem_root_carbon'] = ((sum(b[106+3*n:])-sum(a[106+3*n0:]),
        -sum(t[f'stem_root_{i}_inflow'] for i in range(m)),sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal'] for i in range(m)),
        -points['stem_structural_carbon']),Fraction(0),Fraction(0),capture.point.MASS)
    result = {}
    _need(set(rows) == set(local) == set(saved['global_ledgers']), 'BALANCE_HOLD: complete branch/global inventory required')
    for name,(terms,_,_,unit) in rows.items():
        residual = sum(terms,Fraction(0)); expected = X(saved['global_ledgers'][name]['residual_exact'])+X(local[name]['residual_exact'])
        budget = X(saved['global_ledgers'][name]['budget_exact'])+X(local[name]['budget_exact'])
        _need(residual == expected and abs(residual) <= budget, 'BALANCE_HOLD: exact captured plus branch '+name)
        result[name] = {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    return local,result


def _build(context, data, sample, totals, steps, link):
    saved = data['captured']; at = _time(data,steps); base = data['initial_base']
    _need(sample['at'] == {'time_origin_utc':saved['simulation_origin_utc'],'elapsed_seconds_exact':Q(at,'s')}, 'TIME_HOLD: actual original-grid endpoint required')
    units = stock.short._flux_units(saved['program'])
    branch = {name:numeric._q(v,unit) for (name,unit),v in zip(units.items(),totals,strict=True)}
    lifetime = {name:Q(X(saved['pending_lifetime_transfers_exact'][name])+F(q['value']),q['unit']) for name,q in branch.items()}
    source_segment = {name:Q(X(saved['pending_source_segment_transfers_exact'][name])+F(q['value']),q['unit']) for name,q in branch.items()}
    local,global_books = _books(context,data,sample,totals,steps,lifetime)
    if steps == 0:
        _need(link is None, 'PREFIX_HOLD: original captured prefix required'); prefix = base['output_prefix_sha256']
    else:
        stock.arithmetic._closed(link,{'previous_output_prefix_sha256','sample_sha256'})
        _need(stock.parent._digest(link['previous_output_prefix_sha256']) and link['sample_sha256'] == stock._hash(sample), 'PREFIX_HOLD: current sample link required')
        prefix = stock._prefix(link['previous_output_prefix_sha256'],sample,base['event_sequence'],'organ_repeat_grid_endpoint')
    return {'version':CHECKPOINT_VERSION,'model_version':VERSION,'source_code_sha256':_pins(),
        'context_sha256':context.root_sha256,'source_seed_sha256':stock._hash(base),
        'at':deepcopy(sample['at']),'grid_index':saved['original_grid_position']['completed_grid_index']+steps,
        'branch_steps':steps,'phase':'fractional_after_material_point' if steps == 0 else 'original_grid_endpoint',
        'event_sequence':base['event_sequence'],'schedule':_clock(data,lifetime,at),'last_confirmed':deepcopy(sample),
        'branch_integrated_transfers':branch,'lifetime_transfers_exact':lifetime,'source_segment_transfers_exact':source_segment,
        'point_totals_exact':deepcopy(saved['point_totals_exact']),'branch_ledgers':local,'global_ledgers':global_books,
        'output_cursor':base['output_cursor']+steps,'output_prefix_sha256':prefix,'output_prefix_link':deepcopy(link),
        'scope':'software_research_only','G0_G4':'not_assessed','time_kind':'synthetic_model_clock_not_observation',
        'redistribution_authorized':saved['redistribution_authorized']}


@dataclass(frozen=True, eq=False)
class Context:
    _origin: capture.Context = field(repr=False)
    _receipts: tuple = field(repr=False)
    _raw: bytes = field(repr=False)
    root_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)

    @property
    def _source(self): return self._origin._source


def _project(origin, descriptor):
    authority = _authority(origin)
    return {'_descriptor':descriptor,'captured':descriptor['seed'],
        'point':authority['point'],'source_snapshot':authority['source_snapshot'],
        'initial_sample':descriptor['initial_sample'],'initial_base':descriptor['initial_base']}


def _authority(origin):
    _need(type(origin) is capture.Context, 'CONTEXT_HOLD: genuine original capture authority required')
    authority = stock._parse(origin._raw,origin.root_sha256,capture.MAX_BYTES)
    capture._fence(origin,authority)
    for profile in stock.parent._profiles(origin._source._root).values():
        _need(vars(profile) == vars(type(profile)(profile.raw_bytes)),
            'PROFILE_HOLD: original complete reference parameter objects required')
    return authority


def _stamp(context):
    receipts = context._receipts
    _need(type(receipts) is tuple and 1 <= len(receipts) <= MAX_EVENTS
        and all(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES for raw in receipts)
        and sum(map(len,receipts)) <= MAX_PROOF_BYTES, 'CAPACITY_HOLD: bounded immutable material receipts required')
    return (context.root_sha256,context._origin.root_sha256,sha256(context._origin._raw).hexdigest(),
        tuple(sha256(raw).hexdigest() for raw in receipts),tuple(sorted(_pins().items())))


def _next_seed(origin, previous, result):
    after = result['after_program']; at = X(result['at']['elapsed_seconds_exact'])
    dense = result['before_candidate']['dense_candidate']; cp = result['before_candidate']['source_prefix']
    units = stock.short._flux_units(after); bases = deepcopy(previous['birth_bases'])
    pending = {name:deepcopy(dense['pending_lifetime_transfers_exact'].get(name,Q(Fraction(0),unit))) for name,unit in units.items()}
    segment = {name:deepcopy(dense['pending_source_segment_transfers_exact'].get(name,Q(Fraction(0),unit))) for name,unit in units.items()}
    authority = capture._context(origin); timeline = authority['point']['before_candidate']['source_root_certificate']['source_timeline']
    air = pending['indoor_air_temperature_time']; event = result['source_event']
    bases['stem_root'].append({'compartment_id':event['internode_id'],'kind':'internode',
        'at_elapsed_seconds_exact':deepcopy(result['at']['elapsed_seconds_exact']),
        'carbon':deepcopy(after['stem_root_compartments'][-1]['initial_carbon']),
        'air_temperature_integral_exact':deepcopy(air),'thermal_age_exact':Q(Fraction(0),'degC_day'),
        'base_temperature':deepcopy(timeline['base_temperature']),'basis_kind':'numerical_material_point_not_physical_emergence'})
    if result['inputs']['leaf'] is not None:
        leaf = after['leaves'][-1]
        bases['leaf'].append({'leaf_id':leaf['leaf_id'],'at_elapsed_seconds_exact':deepcopy(result['at']['elapsed_seconds_exact']),
            'carbon':deepcopy(leaf['initial_carbon']),'air_temperature_integral_exact':deepcopy(air),
            'thermal_age_exact':Q(Fraction(0),'degC_day'),'base_temperature':deepcopy(leaf['base_temperature']),
            'basis_kind':'numerical_material_point_not_physical_emergence'})
    points = deepcopy(cp['point_totals_exact'])
    for kind,part in result['flow_components'].items():
        for name,q in part.items(): points[name] = Q(X(points[name])+F(q['value']),q['unit'])
        name = ('stem' if kind == 'internode' else 'leaf')+'_structural_carbon'
        points[name] = Q(X(points[name])+F(part['structural_carbon']['value']),material.MASS)
    dt = F(previous['original_numerical']['step_seconds']); count = previous['original_numerical']['step_count']; completed = int(at//dt)
    _need(0 <= completed <= count and at <= dt*count, 'TIME_HOLD: original horizon required')
    _need((count-completed+1)*(len(result['after_state'])+2*len(after['leaves'])+9) <= 32768,
        'CAPACITY_HOLD: original remaining-scalar limit required')
    _need(len(after['leaves']) <= 512 and len(after['stem_root_compartments']) <= 512,
        'CAPACITY_HOLD: bounded individual inventories required')
    threshold = X(event['threshold_exact']); spacing = X(timeline['phyllochron_exact'])
    age = X(dense['shoot_age_exact']); _need(threshold <= age < threshold+spacing, 'PHASE_HOLD: next due event cannot be skipped')
    schedule = {'consumed_event_id':event['source_event_id'],'consumed_sequence':event['sequence'],
        'consumed_threshold_exact':deepcopy(event['threshold_exact']),'next_sequence':event['sequence']+1,
        'next_threshold_exact':Q(threshold+spacing,'degC_day'),'age_exact':deepcopy(dense['shoot_age_exact']),
        'source_schedule_id':timeline['schedule_id'],'policy':'next_source_event_once_no_threshold_snap',
        'age_basis':'numerical_air_integral_not_physical_emergence'}
    next_at = dt*(completed+1) if completed < count else None
    return {**deepcopy(previous),'parent_context_sha256':result['context_sha256'],
        'parent_checkpoint_sha256':result['checkpoint_sha256'],
        'program':deepcopy(after),'anchors':deepcopy(result['after_anchors']),'state_layout':stock.short._layout(after),
        'birth_bases':bases,'schedule':schedule,'at':deepcopy(result['at']),
        'original_grid_position':{'source_left_index':cp['grid_index'],'completed_grid_index':completed,
            'step_seconds_exact':Q(dt,'s'),'partial_interval_seconds_exact':Q(at-X(cp['at']['elapsed_seconds_exact']),'s'),
            'next_grid_index':completed+1 if next_at is not None else None,
            'next_grid_elapsed_seconds_exact':Q(next_at,'s') if next_at is not None else None,
            'remaining_to_next_grid_seconds_exact':Q(next_at-at if next_at is not None else Fraction(0),'s')},
        'pending_lifetime_transfers_exact':pending,'pending_source_segment_transfers_exact':segment,
        'new_point_components':deepcopy(result['flow_components']),'point_totals_exact':points,
        'global_ledgers':capture._global(origin._source,result,bases,pending,points,at),
        'redistribution_authorized':previous['redistribution_authorized'] and result['inputs']['rights']['redistribute']}


def _descriptor(origin, hashes, seed, result):
    cp = result['before_candidate']['source_prefix']; before = capture._sample(result,True); after = capture._sample(result)
    sequence = cp['event_sequence']+1
    prefix = stock._prefix(cp['output_prefix_sha256'],before,cp['event_sequence'],'fractional_before_material_point')
    prefix = stock._prefix(prefix,after,sequence,'fractional_after_material_point')
    base = {'version':'repeat-material-seed-checkpoint-v1','last_confirmed':after,'at':deepcopy(result['at']),
        'event_sequence':sequence,'output_cursor':cp['output_cursor']+2,'output_prefix_sha256':prefix}
    return {'version':'individual-organ-repeat-context-v1','source_code_sha256':_pins(),
        'origin_context_sha256':origin.root_sha256,'receipt_sha256':hashes,'seed':seed,
        'initial_sample':after,'initial_base':base}


def _derive(origin, receipts):
    from . import crop_organ_repeat_proofs as proofs
    _need(type(receipts) is tuple and 1 <= len(receipts) <= MAX_EVENTS
        and all(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES for raw in receipts)
        and sum(map(len,receipts)) <= MAX_PROOF_BYTES, 'CAPACITY_HOLD: bounded immutable material receipts required')
    authority = capture._context(origin); seed = authority['captured']; hashes = []; prior = None; descriptor = None
    for raw in receipts:
        digest = sha256(raw).hexdigest(); result = stock._parse(raw,digest,MAX_BYTES)
        cp = result['before_candidate']['source_prefix']
        if prior is None:
            legacy._shape(origin,authority,cp); current_context = origin; data = authority
        else:
            data = _project(origin,descriptor); _shape(prior,data,cp); current_context = prior
        proofs.validate(current_context,data,result,first=prior is None)
        seed = _next_seed(origin,seed,result); hashes.append(digest)
        descriptor = _descriptor(origin,list(hashes),seed,result)
        encoded = _canonical(descriptor)
        prior = Context(origin,receipts[:len(hashes)],encoded,sha256(encoded).hexdigest(),_TOKEN)
    return descriptor


def _context(context):
    _need(type(context) is Context and context._token is _TOKEN, 'CONTEXT_HOLD: genuine repeat context required')
    descriptor = stock._parse(context._raw,context.root_sha256,MAX_BYTES)
    stamp = _stamp(context)
    if _VERIFIED.get(context) != stamp:
        _need(_canonical(descriptor) == _canonical(_derive(context._origin,context._receipts)),
            'CONTEXT_HOLD: original source/receipt lineage and derived seed required')
        _VERIFIED[context] = stamp
    data = _project(context._origin,descriptor); _fence(context,data); return data


def _issue(origin, receipts):
    descriptor = _derive(origin,receipts); raw = _canonical(descriptor)
    context = Context(origin,receipts,raw,sha256(raw).hexdigest(),_TOKEN)
    _fence(context,_project(origin,descriptor)); _VERIFIED[context] = _stamp(context); return context


@_public
def adopt_first(origin_capture, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact, inputs):
    result = material.apply_successor_material_point(origin_capture,raw_checkpoint,expected_sha256=expected_sha256,
        time_tolerance_seconds_exact=time_tolerance_seconds_exact,inputs=inputs)
    return _issue(origin_capture,(_canonical(result),))


@_public
def adopt_successor(context, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact, inputs):
    from . import crop_organ_repeat_events as events
    _context(context)
    result = events.apply_material_point(context,raw_checkpoint,expected_sha256=expected_sha256,
        time_tolerance_seconds_exact=time_tolerance_seconds_exact,inputs=inputs)
    return _issue(context._origin,(*context._receipts,_canonical(result)))


@_public
def context_bytes(context): _context(context); return context._raw


@_public
def proof_bytes(context): _context(context); return context._receipts


@_public
def restore_context(origin_capture, raw_bytes, *, expected_sha256, receipt_bytes):
    stock._parse(raw_bytes,expected_sha256,MAX_BYTES)
    context = Context(origin_capture,receipt_bytes,raw_bytes,expected_sha256,_TOKEN)
    _context(context); return context


@dataclass(frozen=True)
class Checkpoint:
    _raw: bytes = field(repr=False)
    sha256: str
    context_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _seal(context, data, payload):
    raw = _canonical(payload)
    _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'CAPACITY_HOLD: 512KiB original-grid checkpoint required')
    _fence(context,data)
    return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


@_public
def start(context):
    data = _context(context)
    p = data['captured']['program']; sample = data['initial_sample']
    return _seal(context,data,_build(context,data,sample,(0.,)*len(stock.short._flux_units(p)),0,None))


def _shape(context, data, payload):
    p = data['captured']['program']; units = stock.short._flux_units(p); initial = data['initial_sample']
    template = _build(context,data,initial,(0.,)*len(units),0,None)
    stock.arithmetic._closed(payload,set(template)); steps = payload['branch_steps']; _time(data,steps)
    sample = payload['last_confirmed']; stock.arithmetic._closed(sample,set(initial))
    y = sample['state']; _need(type(y) is list and len(y) == len(initial['state']) and all(type(v) is float and isfinite(v) for v in y),
        'CHECKPOINT_HOLD: finite original-layout binary64 state required')
    rows = payload['branch_integrated_transfers']; stock.arithmetic._closed(rows,set(units))
    for name,unit in units.items(): stock.legacy._captured_quantity(rows[name],unit)
    totals = tuple(rows[name]['value'] for name in units)
    expected = _build(context,data,sample,totals,steps,payload['output_prefix_link'])
    _need(_canonical(payload) == _canonical(expected), 'CHECKPOINT_HOLD: current time/state/flow/clock/books/prefix identity required')
    if steps == 0: _need(_canonical(payload) == _canonical(template), 'CHECKPOINT_HOLD: original captured initial checkpoint required')
    return tuple(y),totals


def _validate(context, data, payload):
    y,totals = _shape(context,data,payload); p = data['captured']['program']
    rates,rhs = stock.short._evaluate(p,y,stock.parent._profiles(context._source._root))
    sample = _sample(data,_time(data,payload['branch_steps']),y,rhs)
    rebuilt = _build(context,data,sample,totals,payload['branch_steps'],payload['output_prefix_link'])
    _need(_canonical(payload) == _canonical(rebuilt), 'CHECKPOINT_HOLD: actual current RHS and captured invariants required')
    _fence(context,data)
    return y,totals,rates,rhs


def _raw_checkpoint(context, checkpoint):
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256 == context.root_sha256
        and type(checkpoint._raw) is bytes and 0 < len(checkpoint._raw) <= MAX_CHECKPOINT_BYTES
        and sha256(checkpoint._raw).hexdigest() == checkpoint.sha256, 'CHECKPOINT_HOLD: immutable matching continuation checkpoint required')
    return checkpoint._raw


@_public
def checkpoint_bytes(context, checkpoint):
    data = _context(context); raw = _raw_checkpoint(context,checkpoint)
    payload = stock._parse(raw,checkpoint.sha256,MAX_CHECKPOINT_BYTES); _shape(context,data,payload)
    _fence(context,data); return raw


@_public
def restore_checkpoint(context, raw_bytes, *, expected_sha256):
    data = _context(context); payload = stock._parse(raw_bytes,expected_sha256,MAX_CHECKPOINT_BYTES)
    _validate(context,data,payload); return _seal(context,data,payload)


def _step(p, state, totals, rates, rhs, profiles, step, progress):
    progress['stage'] = 'initial_flux'
    rows = [{'state':list(state),'rates':list(rates),'flux':list(stock.short._flux(p,state,rhs))}]
    for name,h in [('k2',step/2),('k3',step/2),('k4',step)]:
        progress['stage'] = name
        y = candidate.old._combine(state,(rates,),(Fraction(1),),h)
        progress['new_RHS_evaluations'] += 1; rates,rhs = stock.short._evaluate(p,y,profiles)
        rows.append({'state':list(y),'rates':list(rates),'flux':list(stock.short._flux(p,y,rhs))})
    progress['stage'] = 'endpoint'
    y = candidate.old._combine(state,tuple(row['rates'] for row in rows),candidate.old.RK4_WEIGHTS,step)
    cumulative = candidate.old._combine(totals,tuple(row['flux'] for row in rows),candidate.old.RK4_WEIGHTS,step)
    progress['new_RHS_evaluations'] += 1; rates,last = stock.short._evaluate(p,y,profiles)
    return y,cumulative,rates,last,rows


def _pending_event(data, payload, rows, cumulative, target):
    saved = data['captured']; timeline = data['point']['before_candidate']['source_root_certificate']['source_timeline']
    start = X(payload['at']['elapsed_seconds_exact']); step = target-start
    units = stock.short._flux_units(saved['program']); index = list(units).index('indoor_air_temperature_time')
    air = X(saved['pending_lifetime_transfers_exact']['indoor_air_temperature_time'])+F(cumulative[index])
    base = F(float(timeline['base_temperature']['value'])); threshold = X(saved['schedule']['next_threshold_exact'])
    represented = X(timeline['age_exact'])+(air-base*target)/86400-threshold
    event = candidate.interval.event
    polynomial = event._thermal_polynomial(tuple(F(row['state'][104]) for row in rows),step,base,X(payload['schedule']['age_exact']),threshold)
    _need(event._minimum_derivative(polynomial) > 0, 'MONOTONICITY_HOLD: original pending-threshold interval must be strictly increasing')
    ideal = event._value(polynomial,Fraction(1))
    _need((ideal >= 0) == (represented >= 0), 'ROUNDING_HOLD: cubic and represented endpoint disagree about the first pending event')
    if ideal < 0: return None
    entity = {key:deepcopy(timeline[key]) for key in ('shoot_id','development_origin_id','schedule_id','started_at')}
    entity.update(sequence=saved['schedule']['next_sequence'],birth_age_exact=deepcopy(saved['schedule']['next_threshold_exact']))
    digest = capture.point.source_ids._digest(entity)
    return {'status':'unrefined_original_interval_bracket','source_event_id':'shoot-event:'+digest,'internode_id':'internode:'+digest,
        'sequence':entity['sequence'],'threshold_exact':deepcopy(entity['birth_age_exact']),
        'left_elapsed_seconds_exact':Q(start,'s'),'right_elapsed_seconds_exact':Q(target,'s'),
        'left_age_exact':deepcopy(payload['schedule']['age_exact']),'represented_right_age_exact':Q(represented+threshold,'degC_day'),
        'polynomial_coefficients':[Q(q,'degC_day') for q in polynomial],'stages':deepcopy(rows),
        'schedule_consumed':False,'new_organs_created':False,'checkpoint_issued':False}


def _bounded_result(result):
    public = {**result,'checkpoint':result['checkpoint'].value if result['checkpoint'] is not None else None}
    _canonical(public); return result


@_public
def advance_chunk(context, checkpoint, step_budget):
    _need(type(step_budget) is int and 1 <= step_budget <= 128, 'BUDGET_HOLD: 1..128 original-grid endpoints required')
    data = _context(context); raw = _raw_checkpoint(context,checkpoint)
    payload = stock._parse(raw,checkpoint.sha256,MAX_CHECKPOINT_BYTES); state,totals,rates,rhs = _validate(context,data,payload)
    saved = data['captured']; p = saved['program']; dt = F(saved['original_numerical']['step_seconds'])
    end_index = saved['original_numerical']['step_count']; at = X(payload['at']['elapsed_seconds_exact'])
    _need(at < dt*end_index, 'COMPLETED_HOLD: original source horizon exhausted')
    profiles = stock.parent._profiles(context._source._root); samples = []; intervals = []; failure = None; pending = None
    progress = {'stage':'initial','new_RHS_evaluations':0}
    for _ in range(min(step_budget,end_index-payload['grid_index'])):
        target = dt*(payload['grid_index']+1); step = target-at
        try:
            y,cumulative,new_rates,last,rows = _step(p,state,totals,rates,rhs,profiles,step,progress)
            progress['stage'] = 'pending_event'
            pending = _pending_event(data,payload,rows,cumulative,target)
            if pending is not None:
                _canonical({'samples':samples,'last_confirmed':payload,'pending_event':pending})
                failure = {'reason':'NEXT_EVENT_HOLD: first pending event needs explicit candidate/material adoption',
                    'stage':'pending_event','target_elapsed_seconds_exact':Q(target,'s')}; break
            progress['stage'] = 'ledgers'
            sample = _sample(data,target,y,last)
            link = {'previous_output_prefix_sha256':payload['output_prefix_sha256'],'sample_sha256':stock._hash(sample)}
            proposed = _build(context,data,sample,cumulative,payload['branch_steps']+1,link)
            interval = {'left_elapsed_seconds_exact':Q(at,'s'),'right_elapsed_seconds_exact':Q(target,'s'),
                'step_seconds_exact':Q(step,'s'),'stage_sha256':[stock._hash(row) for row in rows]}
            progress['stage'] = 'publication'
            _canonical({'samples':[*samples,sample],'intervals':[*intervals,interval],'last_confirmed':proposed,'checkpoint':proposed})
            _seal(context,data,proposed)
            state,totals,rates,rhs,at,payload = y,cumulative,new_rates,last,target,proposed
            samples.append(sample); intervals.append(interval)
        except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
            failure = {'reason':str(error),'stage':progress['stage'],'target_elapsed_seconds_exact':Q(target,'s')}; pending = None; break
    _fence(context,data)
    return _bounded_result({'status':'hold' if failure else 'completed' if at == dt*end_index else 'yielded','hold':failure,
        'samples':samples,'intervals':intervals,'checkpoint':None if failure else _seal(context,data,payload),
        'last_confirmed':deepcopy(payload),'pending_event':pending,'checkpoint_validation_RHS_evaluations':1,
        'new_RHS_evaluations':progress['new_RHS_evaluations'],'scope':'software_research_only','G0_G4':'not_assessed'})
