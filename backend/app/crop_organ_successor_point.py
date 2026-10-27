"""Successor material allocation; crop-organ-successor-point-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

from . import crop_organ_successor_candidate as candidate
from . import crop_rational_new_internodes as source_ids

resume, capture, stock = candidate.resume, candidate.capture, candidate.stock
point = capture.point
stem,leaf = stock.stem,stock.leaf
MASS = leaf.MASS
VERSION = 'individual-organ-successor-material-point-research-v1'
POLICY = 'source-next-threshold-explicit-structural-C-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
ID_CODE_SHA256 = sha256(Path(source_ids.__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
FIELDS = {'schema_version','input_id','origin','policy','context_sha256','checkpoint_sha256','candidate_sha256','initial_binding_sha256',
    'at_elapsed_seconds_exact','model_floor_area','source_event_id','source_threshold_sequence','source_threshold_exact',
    'parent_internode_id','internode','leaf','rights','reviewer'}
F = Fraction.from_float
Q = candidate.Q


class SuccessorPointHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:
        raise SuccessorPointHold(reason)


def _canonical(value):
    raw = stock._canonical(value)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB fractional point input/output required')
    return raw


def _pins():
    expected = {**candidate._pins(),'backend/app/crop_rational_new_internodes.py':ID_CODE_SHA256,
        'backend/app/crop_organ_successor_point.py':CODE_SHA256}
    root = Path(__file__).resolve().parents[2]
    actual = {name:sha256((root/name).read_bytes()).hexdigest() for name in expected}
    _need(actual == expected, 'CODE_HOLD: original fractional point and source ID code required')
    return actual


def _source_event(data, calculation):
    timeline = data['point']['before_candidate']['source_root_certificate']['source_timeline']
    schedule = calculation['source_prefix']['schedule']; bracket = calculation['source_interval']
    entity = {k:deepcopy(timeline[k]) for k in ('shoot_id','development_origin_id','schedule_id','started_at')}
    entity.update(sequence=schedule['next_sequence'],birth_age_exact=deepcopy(schedule['next_threshold_exact']))
    digest = source_ids._digest(entity)
    _need(bracket['sequence'] == entity['sequence'] and bracket['threshold_exact'] == entity['birth_age_exact']
        and bracket['source_event_id'] == 'shoot-event:'+digest and bracket['internode_id'] == 'internode:'+digest,
        'EVENT_HOLD: actual next unconsumed source entity required')
    age = resume.X(calculation['dense_candidate']['shoot_age_exact']); threshold = resume.X(entity['birth_age_exact'])
    spacing = resume.X(timeline['phyllochron_exact'])
    _need(spacing > 0 and threshold <= age < threshold+spacing,
        'PHASE_HOLD: another due source threshold cannot be skipped')
    return {'entity':entity,'source_event_id':'shoot-event:'+digest,'internode_event_id':'shoot-event:'+digest+'/internode',
        'leaf_event_id':'shoot-event:'+digest+'/leaf','internode_id':'internode:'+digest,
        'leaf_id':'leaf:'+source_ids._digest({**entity,'organ':'leaf','slot':0}),
        'sequence':entity['sequence'],'threshold_exact':deepcopy(entity['birth_age_exact']),
        'internode_identity_model_version':source_ids.MODEL_VERSION,
        'leaf_identity_policy':'one_optional_declared_leaf_per_numeric_source_event_research_v1'}


_balance, _components = point._balance, point._components


def apply_successor_material_point(context,raw_checkpoint,*,expected_sha256,time_tolerance_seconds_exact,inputs):
    try:
        pins = _pins(); leaf.arithmetic._closed(inputs,FIELDS); raw = _canonical(inputs); v = json.loads(raw)
        data = capture._context(context); saved = data['captured']; p = saved['program']
        for name in ('input_id','reviewer','parent_internode_id'):stock.short.stock.part._id(v[name])
        stem._rights(v['rights'])
        _need(v['schema_version'] == 'individual-organ-successor-material-point-input-v1' and v['origin'] == 'synthetic' and v['policy'] == POLICY,
              'POLICY_HOLD: explicit source-bound synthetic material point required')
        for name in ('context_sha256','checkpoint_sha256','candidate_sha256','initial_binding_sha256'):
            _need(stock.parent._digest(v[name]), 'HASH_HOLD: explicit canonical '+name+' required')
        _need(v['context_sha256'] == context.root_sha256 and v['checkpoint_sha256'] == expected_sha256,
              'HASH_HOLD: original current context/checkpoint required')
        _need(leaf.arithmetic._quantity(v['model_floor_area'],'m2_floor') == p['model_floor_area']['value'],
              'BASIS_HOLD: original common declared footprint required')
        tolerance = deepcopy(time_tolerance_seconds_exact)
        calculation = candidate.calculate_successor_candidate(context,raw_checkpoint,expected_sha256=expected_sha256,time_tolerance_seconds_exact=tolerance)
        _need(v['candidate_sha256'] == calculation['calculation_sha256'] and v['initial_binding_sha256'] == data['source_snapshot']['manifest']['initial_binding_sha256'],
              'HASH_HOLD: actual complete fractional candidate/source required')
        resume.X(v['at_elapsed_seconds_exact'])
        _need(v['at_elapsed_seconds_exact'] == calculation['at']['elapsed_seconds_exact'], 'TIME_HOLD: actual candidate exact time required')
        event = _source_event(data,calculation)
        _need(type(v['source_threshold_sequence']) is int and v['source_threshold_sequence'] == event['sequence']
              and v['source_threshold_exact'] == event['threshold_exact'] and v['source_event_id'] == event['source_event_id'],
              'EVENT_HOLD: original next source threshold/schedule/sequence required')
        past = {e['event_id'] for row in data['source_snapshot']['history'] for e in row['inputs']['events']}
        past.update(data['point']['source_event'][k] for k in ('source_event_id','internode_event_id','leaf_event_id'))
        _need(not past.intersection(event[k] for k in ('source_event_id','internode_event_id','leaf_event_id')),
              'EVENT_HOLD: logical source event already present in original history')
        _need(v['internode']['compartment_id'] == event['internode_id'], 'EVENT_HOLD: original canonical source internode ID required')
        parents = {row['compartment_id'] for row in p['stem_root_compartments'] if row['kind'] == 'internode'}
        _need(v['parent_internode_id'] in parents, 'PARENT_HOLD: actual current pre-point internode parent required')
        _need(event['internode_id'] not in {row['compartment_id'] for row in p['stem_root_compartments']},
              'EVENT_HOLD: canonical source internode already exists')
        leaf_packet = v['leaf']
        if leaf_packet is not None:
            leaf.arithmetic._closed(leaf_packet,{'incoming_temperature','declaration'})
            _need(leaf_packet['declaration']['leaf_id'] == event['leaf_id'] and event['leaf_id'] not in {row['leaf_id'] for row in p['leaves']},
                  'EVENT_HOLD: unique canonical source leaf required')
        before = calculation['dense_candidate']; y = before['state']; n = len(p['leaves']); old_m = len(p['stem_root_compartments'])
        profiles = stock.parent._profiles(context._source._root)
        stem_event = {'event_id':event['internode_event_id'],'parent_internode_id':v['parent_internode_id'],'compartment':v['internode']}
        first = stem._jump(p,y,profiles,[stem_event]); components = {'internode':_components(first,'internode')}
        after_program,after,rates,evaluation = (first[k] for k in ('program','state','rates','evaluation'))
        anchors = deepcopy(saved['anchors']); leaf_receipts = []; leaf_jump = None
        if leaf_packet is not None:
            leaf_event = {'event_id':event['leaf_event_id'],'parent_internode_id':event['internode_id'],
                'incoming_temperature':leaf_packet['incoming_temperature'],'leaf':leaf_packet['declaration']}
            leaf_jump = leaf._jump(after_program,after,profiles,[leaf_event],anchors)
            _need(leaf_jump['before_capacity'] == before['derived']['canopy_capacity']['value'], 'STATE_HOLD: original current canopy capacity required')
            after_program,after,rates,evaluation = (leaf_jump[k] for k in ('program','state','rates','evaluation'))
            anchors,leaf_receipts = leaf_jump['anchors'],leaf_jump['receipts']; components['leaf'] = _components(leaf_jump,'leaf')
        nn = len(after_program['leaves']); view = stock.short._view(evaluation); derived = view['joint']['derived']
        _need(after[1:103] == y[1:103] and after[104:106] == y[104:106]
              and after[106:106+n] == y[106:106+n] and after[106+nn:106+nn+n] == y[106+n:106+2*n]
              and after[106+2*nn:106+2*nn+n] == y[106+2*n:106+3*n]
              and after[106+3*nn:106+3*nn+old_m] == y[106+3*n:] and anchors[:n] == saved['anchors'],
              'STATE_HOLD: original non-target scalars/ages/areas/C/root inventory and D0 required')
        if leaf_packet is None:
            _need(after[103] == y[103] and derived['canopy_capacity'] == before['derived']['canopy_capacity'], 'STATE_HOLD: no leaf thermal jump without a leaf')
        units = {name:q['unit'] for name,q in components['internode'].items()}
        exact_flows = {name:sum((F(part[name]['value']) for part in components.values()),Fraction(0)) for name in units}
        flows = {name:stock.numeric._q(leaf.arithmetic._rounded(value),units[name]) for name,value in exact_flows.items()}
        a,b = tuple(map(F,y)),tuple(map(F,after)); C0 = point.candidate._carbon(a,n); C1 = point.candidate._carbon(b,nn)
        Ca = F(before['derived']['air_capacity']['value']); _need(Ca == F(derived['air_capacity']['value']), 'STATE_HOLD: original air capacity required')
        latent = F(profiles['exchange_profile'].values['latent_heat']); reference = F(p['scenario']['parameters']['reference_temperature']['value'])
        energy = lambda state:state[103]+Ca*(state[104]-reference)+latent*state[105]
        terms = {
            'buffer':([b[0],-a[0],*(F(part['buffer_debit']['value']) for part in components.values())],MASS),
            'whole_carbohydrate':([C1,-C0,*(F(part['growth_respiration']['value']) for part in components.values())],MASS),
            'new_internode':([b[-1],-F(first['structural'])],MASS),
            'stem_root_carbon':([sum(b[106+3*nn:]),-sum(a[106+3*n:]),-F(first['structural'])],MASS),
            'capacity':([F(derived['canopy_capacity']['value']),-F(before['derived']['canopy_capacity']['value']),-exact_flows['capacity_in']],stock.numeric.CAPACITY),
            'canopy_sensible':([b[103],-a[103],-exact_flows['sensible_in']],stock.numeric.ENERGY),
            'air_sensible':([Ca*b[104],-Ca*a[104]],stock.numeric.ENERGY),
            'vapor':([b[105],-a[105]],'kg_water/m2_floor'),
            'fruit_number':([sum(b[53:103]),-sum(a[53:103])],'fruits_equivalent/m2_floor'),
            'reduced_energy':([energy(b),-energy(a),-exact_flows['sensible_in']],stock.numeric.ENERGY)}
        if leaf_packet is not None:
            terms['new_leaf'] = ([b[106+2*nn+n],-F(leaf_jump['structural'])],MASS)
        balances = {name:_balance(values,unit) for name,(values,unit) in terms.items()}
        result = {'model_version':VERSION,'policy':POLICY,'code_sha256':CODE_SHA256,'source_code_sha256':pins,
            'scope':'software_research_only','time_kind':'synthetic_model_clock_not_observation','G0_G4':'not_assessed',
            'claim_scope':'source_bound_next_fractional_material_point_only_no_schedule_or_checkpoint_adoption',
            'context_sha256':context.root_sha256,'checkpoint_sha256':expected_sha256,'input_sha256':sha256(raw).hexdigest(),'inputs':v,
            'before_candidate_sha256':calculation['calculation_sha256'],'before_candidate':calculation,'source_event':event,
            'at':deepcopy(calculation['at']),'after_program':after_program,'after_state':after,'after_rates':list(rates),'after_derived':deepcopy(derived),
            'after_state_layout':stock.short._layout(after_program),'after_anchors':anchors,'after_curve_residuals':deepcopy(view['curve_residuals']),
            'after_curve_invariant_changes':[stock.numeric._q(stock.numeric._sum(q['value'],-anchor['value']),'m2') for q,anchor in zip(view['curve_residuals'],anchors,strict=True)],
            'internode_receipts':first['receipts'],'leaf_receipts':leaf_receipts,'flow_components':components,
            'point_flows':flows,'point_flows_exact':{name:Q(value,units[name]) for name,value in exact_flows.items()},'point_balances':balances,
            'point_order':['internode','leaf'] if leaf_packet is not None else ['internode'],
            'growth_costs':{'cStemG':first['cost'],**({'cLeafG':leaf_jump['cost']} if leaf_packet is not None else {}),
                'unit':'mg_CH2O/mg_CH2O','profile_sha256':profiles['growth_profile'].sha256},
            'redistribution_authorized':saved['redistribution_authorized'] and v['rights']['redistribute'],
            'initialization_scope':'only_declared_new_leaf_canonical_F0_no_existing_or_stem_geometry_initialization',
            'new_organ_age_basis':'since_this_numerical_material_point_not_exact_physical_emergence',
            'parent_link_scope':'declared_actual_inventory_link_not_validated_anatomical_axis_assignment',
            'past_intervals_reintegrated':0,'rhs_evaluations':38+(leaf_packet is not None),'elapsed_seconds_advanced':Q(Fraction(0),'s'),
            'schedule_adoption':'not_performed','integrator_checkpoint':None,'post_point_global_prefix_adoption':'not_performed',
            'geometry':'not_derived','effects':'read_only_stateless_same_before_input_repeats_identical_result'}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest(); _canonical(result)
        resume._fence(context,data)
        _need(_canonical(inputs) == raw, 'INPUT_HOLD: original explicit material inputs required before return')
        _need(_pins() == pins, 'CODE_HOLD: original point dependencies required before return')
        return deepcopy(result)
    except SuccessorPointHold:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise SuccessorPointHold(str(error)) from None
