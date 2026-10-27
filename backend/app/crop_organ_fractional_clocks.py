"""Read current exact organ clocks; crop-organ-fractional-clocks-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_organ_fractional_continuation as resume

capture = resume.capture
stock = resume.stock
Q, X, F = resume.Q, resume.X, Fraction.from_float
VERSION = 'fractional-individual-organ-current-clocks-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2


class OrganClockHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise OrganClockHold(reason)


def _canonical(value):
    raw = stock._canonical(value)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB organ clock response required')
    return raw


def _pins():
    pins = {**resume._pins(),'backend/app/crop_organ_fractional_clocks.py':CODE_SHA256}
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original current organ clocks required')
    return pins


def _age(base, at, air):
    _need(base['at_elapsed_seconds_exact']['unit'] == 's' and base['air_temperature_integral_exact']['unit'] == 'degC_s'
        and base['thermal_age_exact']['unit'] == 'degC_day' and base['base_temperature']['unit'] == 'degC',
        'UNIT_HOLD: original exact time/air/age/temperature baseline required')
    elapsed = at-X(base['at_elapsed_seconds_exact'])
    _need(elapsed >= 0, 'TIME_HOLD: current time precedes the original organ baseline')
    value = X(base['thermal_age_exact'])+(air-X(base['air_temperature_integral_exact'])-F(float(base['base_temperature']['value']))*elapsed)/86400
    _need(value >= 0, 'AGE_HOLD: signed thermal age is negative; no clipping permitted')
    return Q(value,'degC_day')


def _lineages(context, data, binding, payload):
    initial = {node['length_state']['clock_state']['internode_id']:{'lineage_kind':'selected_source_initial',
        'event_id':None,'material_event_sequence':None,'source_node_sequence':node['sequence'],'source_threshold_sequence':None,
        'parent_internode_id':None,'source_clock':deepcopy(node['length_state']['clock_state'])}
        for node in binding['stem_selection']['source_state']['internodes']}
    leaves = {}; internodes = dict(initial)
    for sequence,row in enumerate(context._source.point_history,1):
        target = leaves if row['kind'] == 'leaf' else internodes
        key = 'leaf_id' if row['kind'] == 'leaf' else 'compartment_id'
        for event,item in zip(row['inputs']['events'],row['new_items'],strict=True):
            _need(item[key] not in target, 'IDENTITY_HOLD: unique actual source material lineage required')
            target[item[key]] = {'lineage_kind':'declared_source_material','event_id':event['event_id'],
                'material_event_sequence':sequence,'source_node_sequence':None,'source_threshold_sequence':None,
                'parent_internode_id':event['parent_internode_id'],'source_clock':None}
    event = data['point']['source_event']; v = data['point']['inputs']
    _need(event['internode_id'] not in internodes, 'IDENTITY_HOLD: new numerical internode required')
    internodes[event['internode_id']] = {'lineage_kind':'numerical_threshold_material','event_id':event['internode_event_id'],
        'material_event_sequence':payload['event_sequence'],'source_node_sequence':event['sequence'],'source_threshold_sequence':event['sequence'],
        'parent_internode_id':v['parent_internode_id'],'source_clock':None}
    if v['leaf'] is not None:
        _need(event['leaf_id'] not in leaves, 'IDENTITY_HOLD: new numerical leaf required')
        leaves[event['leaf_id']] = {'lineage_kind':'numerical_threshold_material','event_id':event['leaf_event_id'],
            'material_event_sequence':payload['event_sequence'],'source_node_sequence':event['sequence'],'source_threshold_sequence':event['sequence'],
            'parent_internode_id':event['internode_id'],'source_clock':None}
    root_p,_,_ = stock.parent._context(context._source._root)
    initial_leaves = {row['leaf_id'] for row in root_p['leaves']}
    return internodes,leaves,initial_leaves


def derive_current_organ_clocks(context, raw_checkpoint, *, expected_sha256):
    try:
        pins = _pins(); data = capture._context(context)
        before = (context._raw,context.root_sha256,context._token,context._source)
        source_snapshot = capture.clock._snapshot(context._source)
        checkpoint = resume.restore_checkpoint(context,raw_checkpoint,expected_sha256=expected_sha256)
        payload = checkpoint.value; saved = data['captured']; p = saved['program']
        binding = stock._source(context._source); timeline = binding['stem_selection']['source_state']['timeline_state']
        at = X(payload['at']['elapsed_seconds_exact']); air_q = payload['lifetime_transfers_exact']['indoor_air_temperature_time']; air = X(air_q)
        shoot_base = {'at_elapsed_seconds_exact':Q(Fraction(0),'s'),'thermal_age_exact':deepcopy(timeline['age_exact']),
            'air_temperature_integral_exact':Q(Fraction(0),'degC_s'),'base_temperature':deepcopy(timeline['base_temperature'])}
        shoot_age = _age(shoot_base,at,air)
        _need(shoot_age == payload['schedule']['age_exact'], 'CLOCK_HOLD: actual current shoot clock required')
        stem_meta,leaf_meta,initial_leaves = _lineages(context,data,binding,payload)
        expected_ids = {row['compartment_id'] for row in p['stem_root_compartments'] if row['kind'] == 'internode'}
        _need(set(stem_meta) == expected_ids and set(leaf_meta)|initial_leaves == {row['leaf_id'] for row in p['leaves']}
            and not set(leaf_meta).intersection(initial_leaves), 'IDENTITY_HOLD: complete actual current organ lineages required')
        internodes = []; roots = []
        for item,base in zip(p['stem_root_compartments'],saved['birth_bases']['stem_root'],strict=True):
            identifier = item['compartment_id']; _need(identifier == base['compartment_id'], 'IDENTITY_HOLD: ordered original stock baseline required')
            if item['kind'] == 'root_system':
                roots.append({'compartment_id':identifier,'kind':'root_system','age_exact':None,'age_basis':'not_defined_for_root_system'}); continue
            meta = stem_meta[identifier]; initial = meta['lineage_kind'] == 'selected_source_initial'
            if initial:
                _need(meta['source_clock']['age_exact'] == base['thermal_age_exact']
                    and meta['source_clock']['base_temperature'] == base['base_temperature'], 'CLOCK_HOLD: original selected node clock required')
            else: _need(meta['parent_internode_id'] in expected_ids, 'PARENT_HOLD: actual declared internode parent required')
            internodes.append({'compartment_id':identifier,'kind':'internode',**deepcopy(meta),'baseline':deepcopy(base),
                'age_exact':_age(base,at,air),'age_basis':'selected_initial_internode_clock' if initial else 'since_'+meta['lineage_kind']+'_point',
                'physiological_emergence':'not_established'})
        leaves = []
        for i,(item,base) in enumerate(zip(p['leaves'],saved['birth_bases']['leaf'],strict=True)):
            identifier = item['leaf_id']; _need(identifier == base['leaf_id'], 'IDENTITY_HOLD: ordered original leaf baseline required')
            meta = leaf_meta.get(identifier); age = _age(base,at,air); represented = payload['last_confirmed']['state'][106+i]
            residual = F(represented)-X(age); ledger = payload['global_ledgers'][f'leaf_age_{i}']
            _need(residual == X(ledger['residual_exact']) and abs(residual) <= X(ledger['budget_exact']),
                'BALANCE_HOLD: exact represented leaf age minus its own clock and original budget required')
            if meta is not None: _need(meta['parent_internode_id'] in expected_ids, 'PARENT_HOLD: actual declared leaf parent required')
            leaves.append({'leaf_id':identifier,'state_leaf_index':i,'baseline':deepcopy(base),'age_exact':age,
                'represented_age':stock.numeric._q(represented,'degC_day'),'represented_minus_clock_exact':Q(residual,'degC_day'),
                'age_roundoff_budget_exact':deepcopy(ledger['budget_exact']),
                'age_basis':'declared_initial_leaf_age' if meta is None else 'since_'+meta['lineage_kind']+'_point',
                'lineage_kind':'source_initial_leaf' if meta is None else meta['lineage_kind'],
                'attachment':{'status':'unbound_initial_leaf' if meta is None else 'declared_material_parent_not_validated_anatomy',
                    'parent_internode_id':None if meta is None else meta['parent_internode_id'],
                    'event_id':None if meta is None else meta['event_id']}})
        start,origin = capture.clock.stem._utc(timeline['at']),capture.clock.stem._utc(timeline['started_at'])
        _need(timeline['at'] == saved['simulation_origin_utc'] == payload['at']['time_origin_utc'] and start >= origin,
            'TIME_HOLD: original selected simulation/development origins required')
        delta = start-origin; offset = Fraction(delta.days*86400+delta.seconds)+Fraction(delta.microseconds,1000000)
        result = {'model_version':VERSION,'code_sha256':CODE_SHA256,'source_code_sha256':pins,'scope':'software_research_only',
            'time_kind':'synthetic_model_clock_not_observation','G0_G4':'not_assessed','claim_scope':'current_numerical_clocks_and_declared_lineage_only',
            'context_sha256':context.root_sha256,'checkpoint_sha256':checkpoint.sha256,'root_context_sha256':context._source._root.root_sha256,
            'source_context_sha256':context._source.root_sha256,'initial_binding_sha256':context._source.manifest['initial_binding_sha256'],
            'at':deepcopy(payload['at']),'development_origin_utc':timeline['started_at'],'simulation_origin_utc':timeline['at'],
            'simulation_start_development_elapsed_seconds_exact':Q(offset,'s'),'development_elapsed_seconds_exact':Q(offset+at,'s'),
            **{name:deepcopy(payload[name]) for name in ('grid_index','branch_steps','event_sequence','phase','output_cursor','output_prefix_sha256')},
            'air_temperature_integral_exact':deepcopy(air_q),'shoot':{'age_exact':shoot_age,'baseline':shoot_base,'source_timeline':deepcopy(timeline),
                'schedule':deepcopy(payload['schedule'])},'internodes':internodes,'leaves':leaves,'root_systems':roots,
            'redistribution_authorized':payload['redistribution_authorized'],'checkpoint_validation_RHS_evaluations':1,
            'new_growth_steps':0,'point_execution':'not_performed','initialization':'not_performed','geometry_update':'not_performed',
            'initial_leaf_parent_inference':'not_performed','historical_forcing_scope':'selected_source_clock_not_reintegrated'}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest(); _canonical(result)
        resume._fence(context,data)
        _need((context._raw,context.root_sha256,context._token) == before[:3] and context._source is before[3]
            and capture.clock._snapshot(context._source) == source_snapshot and stock._source(context._source) == binding,
            'SOURCE_HOLD: original current context/source/rights required before return')
        _need(_pins() == pins, 'CODE_HOLD: original current clock dependencies required before return')
        return deepcopy(result)
    except OrganClockHold:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise OrganClockHold(str(error)) from None
