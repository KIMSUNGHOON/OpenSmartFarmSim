"""Bind genuine repeat CPs to construction-limited growth and shared climate."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path
import json

from . import crop_organ_repeat as source
from . import crop_organ_fractional_clocks as clocks
from . import crop_internode_length as length
from . import crop_supply_morphology_stage as stage

VERSION='supply-limited-morphology-bound-stage-research-v1'
POLICY='marginal-construction-extension-v1'
MAX_BYTES=2*1024**2
MAX_INPUT_BYTES=128*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_SHA256={str(Path(m.__file__).resolve().relative_to(Path(__file__).resolve().parents[2])):
    sha256(Path(m.__file__).read_bytes()).hexdigest()for m in (stage,clocks,length,stage.elongation)}
SupplyMorphologyHold=stage.SupplyMorphologyHold
need=stage.need
F=Fraction.from_float
Q,X=source.Q,source.X


def _canonical(value,maximum=MAX_BYTES):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    need(len(raw)<=maximum,'CAPACITY_HOLD: bounded supply morphology input/output required')
    return raw


def _pins():
    pins={**source._pins(),**COMPONENT_SHA256,'backend/app/crop_supply_morphology_rhs.py':CODE_SHA256}
    root=Path(__file__).resolve().parents[2]
    need(all(sha256((root/name).read_bytes()).hexdigest()==h for name,h in pins.items()),'CODE_HOLD: original supply morphology sources required')
    return pins


def _parameters(value,context,checkpoint,program):
    part=source.stock.short.stock.part
    part._closed(value,{'schema_version','input_id','origin','policy','parameter_revision','parameter_source','reviewer','rights',
        'context_sha256','checkpoint_sha256','model_floor_area','leaves','internodes'})
    need(value['schema_version']=='supply-morphology-stage-input-v1'and value['origin']=='synthetic'and value['policy']==POLICY,
        'POLICY_HOLD: explicit synthetic construction policy required')
    need(value['parameter_source']=='own_declared_synthetic_assumptions','PARAMETER_SOURCE_HOLD: explicit own synthetic assumptions required')
    for key in ('input_id','parameter_revision','reviewer'):part._id(value[key])
    source.material.stem._rights(value['rights'])
    need(value['context_sha256']==context.root_sha256 and value['checkpoint_sha256']==checkpoint.sha256,
        'SOURCE_HOLD: actual current context/checkpoint parameter binding required')
    floor=part._number(value['model_floor_area'],'m2_floor')
    need(floor>0 and part._q(floor,'m2_floor')==program['model_floor_area'],'BASIS_HOLD: original common positive footprint required')
    result={};normalized=deepcopy(value)
    for name,key,unit,ids in [
        ('leaves','leaf_id','mg_CH2O/m2_leaf',[x['leaf_id']for x in program['leaves']]),
        ('internodes','compartment_id','mg_CH2O/m_internode',[x['compartment_id']for x in program['stem_root_compartments']if x['kind']=='internode'])]:
        rows=value[name];need(type(rows)is list and len(rows)==len(ids),'INVENTORY_HOLD: complete ordered geometry costs required')
        numbers=[]
        for row,identifier in zip(rows,ids,strict=True):
            part._closed(row,{key,'construction_cost'});need(row[key]==identifier,'IDENTITY_HOLD: original geometry cost identity/order required')
            cost=part._number(row['construction_cost'],unit);need(cost>0,'PARAMETER_HOLD: positive explicit construction cost required');numbers.append(cost)
        result[name]=numbers
        normalized[name]=[{key:identifier,'construction_cost':part._q(cost,unit)}for identifier,cost in zip(ids,numbers,strict=True)]
    normalized['model_floor_area']=part._q(floor,'m2_floor')
    return result,normalized


def _organs(context,data,payload):
    saved=data['captured'];p=saved['program'];binding=source.stock._source(context._source)
    selected=binding['stem_selection']['source_state'];initial={x['length_state']['clock_state']['internode_id']:x for x in selected['internodes']}
    internodes={identifier:{'lineage_kind':'selected_source_initial','parent_internode_id':None,'event_id':None,
        'material_event_sequence':None,'source_threshold_sequence':None,'source_node_sequence':node['sequence'],
        'source_clock':deepcopy(node['length_state']['clock_state']),'curve':deepcopy(node['length_state']['curve']),
        'legacy_anchor':deepcopy(node['length_state']['anchor'])}for identifier,node in initial.items()}
    leaves={}
    def register(kind,identifier,parent,event,sequence,origin,threshold_sequence=None):
        target=leaves if kind=='leaf'else internodes
        need(identifier not in target and parent in internodes,'LINEAGE_HOLD: unique actual child and existing parent required')
        target[identifier]={'lineage_kind':origin,'parent_internode_id':parent,'event_id':event,
            'material_event_sequence':sequence,'source_threshold_sequence':threshold_sequence}
        if kind=='internode':target[identifier].update(curve=deepcopy(selected['emergence_profile']['curve']),
            legacy_anchor={'requested_initial_length':deepcopy(selected['emergence_profile']['initial_length'])},source_clock=None)
    for sequence,receipt in enumerate(context._source.point_history,1):
        kind=receipt['kind'];key='leaf_id'if kind=='leaf'else'compartment_id'
        for event,item in zip(receipt['inputs']['events'],receipt['new_items'],strict=True):
            register(kind,item[key],event['parent_internode_id'],event['event_id'],sequence,'declared_source_material')
    first_sequence=len(context._source.point_history)+1
    need(payload['event_sequence']==first_sequence+len(context._receipts),'LINEAGE_HOLD: actual material-event count required')
    for sequence,receipt in enumerate([data['point'],*(json.loads(raw)for raw in context._receipts)],first_sequence):
        event=receipt['source_event'];inputs=receipt['inputs']
        register('internode',event['internode_id'],inputs['parent_internode_id'],event['internode_event_id'],sequence,'numerical_threshold_material',event['sequence'])
        if inputs['leaf']is not None:register('leaf',event['leaf_id'],event['internode_id'],event['leaf_event_id'],sequence,'numerical_threshold_material',event['sequence'])
    root_p,_,_=source.stock.parent._context(context._source._root)
    initial_leaves={row['leaf_id']for row in root_p['leaves']}
    need(set(leaves).isdisjoint(initial_leaves)and set(leaves)|initial_leaves=={x['leaf_id']for x in p['leaves']},
        'INVENTORY_HOLD: complete initial and material leaf identities required')
    need(set(internodes)=={x['compartment_id']for x in p['stem_root_compartments']if x['kind']=='internode'},
        'INVENTORY_HOLD: complete actual internode identities required')
    at=X(payload['at']['elapsed_seconds_exact']);air=X(payload['lifetime_transfers_exact']['indoor_air_temperature_time'])
    n=len(p['leaves']);y=payload['last_confirmed']['state'];leaf_rows=[];stem_rows=[];roots=[]
    for i,(item,base) in enumerate(zip(p['leaves'],saved['birth_bases']['leaf'],strict=True)):
        identifier=item['leaf_id'];need(identifier==base['leaf_id'],'IDENTITY_HOLD: ordered leaf baseline required')
        age=clocks._age(base,at,air);residual=F(y[106+i])-X(age);ledger=payload['global_ledgers']['leaf_age_'+str(i)]
        need(residual==X(ledger['residual_exact'])and abs(residual)<=X(ledger['budget_exact']),'CLOCK_HOLD: represented leaf age and original exact clock/budget required')
        meta=leaves.get(identifier,{'lineage_kind':'source_initial_leaf','parent_internode_id':None,'event_id':None,
            'material_event_sequence':None,'source_threshold_sequence':None})
        leaf_rows.append({'leaf_id':identifier,**deepcopy(meta),'attachment_status':'unbound_initial_leaf'if identifier in initial_leaves else'declared_material_parent_not_validated_anatomy',
            'baseline':deepcopy(base),'age_exact':age,'represented_age':stage.q(y[106+i],'degC_day'),
            'represented_minus_clock_exact':Q(residual,'degC_day'),'age_roundoff_budget_exact':deepcopy(ledger['budget_exact'])})
    for item,base in zip(p['stem_root_compartments'],saved['birth_bases']['stem_root'],strict=True):
        identifier=item['compartment_id'];need(identifier==base['compartment_id']and item['kind']==base['kind'],'IDENTITY_HOLD: ordered stem/root baseline required')
        if item['kind']=='root_system':
            need(base['thermal_age_exact']is None,'CLOCK_HOLD: no root thermal age');roots.append({'compartment_id':identifier,'age_exact':None});continue
        meta=internodes[identifier]
        if meta['source_clock']is not None:
            need(meta['source_clock']['age_exact']==base['thermal_age_exact']and meta['source_clock']['base_temperature']==base['base_temperature'],
                'CLOCK_HOLD: original selected internode clock required')
        age=clocks._age(base,at,air);represented=float(X(age));need(isfinite(represented)and represented>=0,'CLOCK_HOLD: representable nonnegative internode age required')
        receipt=length.calculate_internode_length_point(inputs={'input_id':identifier,'origin':'synthetic',
            'thermal_age_basis':'since_internode_emergence','age_exact':age,'curve':meta['curve']})
        residual=F(represented)-X(age);budget=F(ulp(represented))/2
        need(abs(residual)<=budget,'CLOCK_HOLD: correctly rounded internode branch age required')
        stem_rows.append({'compartment_id':identifier,**deepcopy(meta),'baseline':deepcopy(base),'age_exact':age,
            'represented_age':stage.q(represented,'degC_day'),'represented_minus_clock_exact':Q(residual,'degC_day'),
            'age_roundoff_budget_exact':Q(budget,'degC_day'),'legacy_length':receipt['length'],'legacy_length_point_sha256':receipt['input_sha256']})
    need(len(roots)==1,'INVENTORY_HOLD: exactly one root stock required')
    return {'leaves':leaf_rows,'internodes':stem_rows,'roots':roots}


def evaluate_bound_rhs(context,raw_checkpoint,*,expected_sha256,inputs):
    try:
        pins=_pins();raw=_canonical(inputs,MAX_INPUT_BYTES);value=json.loads(raw);data=source._context(context)
        checkpoint=source.restore_checkpoint(context,raw_checkpoint,expected_sha256=expected_sha256);payload=checkpoint.value;saved=data['captured'];p=saved['program']
        horizon=F(saved['original_numerical']['step_seconds'])*saved['original_numerical']['step_count']
        need(X(payload['at']['elapsed_seconds_exact'])<horizon,'HORIZON_HOLD: source checkpoint has no original time remaining')
        costs,normalized=_parameters(value,context,checkpoint,p);organs=_organs(context,data,payload)
        old_state=payload['last_confirmed']['state'];state=[*old_state,*[x['represented_age']['value']for x in organs['internodes']],*[x['legacy_length']['value']for x in organs['internodes']]]
        profiles=source.stock.parent._profiles(context._source._root)
        stage_inputs=_canonical({'program':p,'state':state,'organs':organs,'costs':costs})
        result=stage.evaluate(p,state,organs,costs,profiles)
        need(_canonical({'program':p,'state':state,'organs':organs,'costs':costs})==stage_inputs,
            'SOURCE_HOLD: immutable bound stage inputs required')
        out={'model_version':VERSION,'policy':POLICY,'source_code_sha256':pins,'profile_sha256':{k:profile.sha256 for k,profile in profiles.items()},
            'context_sha256':context.root_sha256,'checkpoint_sha256':checkpoint.sha256,'root_context_sha256':context._source._root.root_sha256,
            'parameter_input_sha256':sha256(raw).hexdigest(),'stage_input_sha256':sha256(stage_inputs).hexdigest(),
            'parameters':normalized,'organs':organs,'at':deepcopy(payload['at']),
            'source_binding':{k:deepcopy(saved[k])for k in ('source_context_sha256','source_checkpoint_sha256','parent_context_sha256','parent_checkpoint_sha256',
                'original_numerical','original_grid_position','simulation_origin_utc','development_origin_utc','anchors')},
            'source_checkpoint_metadata':{k:deepcopy(payload[k])for k in ('phase','grid_index','event_sequence','schedule','output_cursor','output_prefix_sha256','point_totals_exact','global_ledgers')},
            'state':state,'state_layout':{'original_prefix_length':len(old_state),'original':deepcopy(saved['state_layout']),
                'internode_ids':[x['compartment_id']for x in organs['internodes']],'appended_blocks':['thermal_age','length'],'appended_units':{'thermal_age':'degC_day','length':'m'}},
            'stage':result,'old_current_validation_RHS_evaluations':1,'new_shared_stage_RHS_evaluations':1,
            'new_component_evaluations':{'carbon':1,'leaf_partition':1,'stem_root_partition':1,'exchange':1,'area_energy':1,'leaf_potential':len(p['leaves']),'internode_potential':len(organs['internodes'])},
            'past_RHS_evaluations':0,'material_jumps':0,'leaf_initializations':0,'legacy_length_point_evaluations':len(organs['internodes']),
            'historical_geometry_carbon_compatibility':'not_assessed','maintenance_geometry_policy':'retain_geometry_no_current_fixed_mass_geometry_invariant',
            'unmapped_structural_inflow':'same_organ_stock_no_diameter_thickness_reserve_or_harvest_inference',
            'elapsed_seconds_advanced':Q(Fraction(0),'s'),'integrator_checkpoint':None,'scope':'software_research_only',
            'claim_scope':'synthetic_current_construction_limited_geometry_and_climate_rhs_only','G0_G4':'not_assessed',
            'redistribution_authorized':saved['redistribution_authorized']and value['rights']['redistribute']}
        out['calculation_sha256']=sha256(_canonical(out)).hexdigest();_canonical(out)
        source._fence(context,data)
        need(_pins()==pins and _canonical(inputs,MAX_INPUT_BYTES)==raw,'SOURCE_HOLD: original current code/parameters required before return')
        return deepcopy(out)
    except SupplyMorphologyHold:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise SupplyMorphologyHold(str(error))from None
