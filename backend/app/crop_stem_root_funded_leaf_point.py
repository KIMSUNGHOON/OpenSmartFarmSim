"""Declared leaf material jump; crop-stem-root-funded-leaf-point-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from . import crop_stem_root_funded_internode_point as stem

binding=stem.binding
arithmetic=stem.arithmetic
resume=stem.resume
short=stem.short
numeric=stem.numeric
MASS=stem.MASS
VERSION='stem-root-funded-leaf-point-research-v1'
POLICY='explicit-new-leaf-carbon-from-buffer-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2
FIELDS=set(stem.FIELDS)


class LeafBirthHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise LeafBirthHold(reason)


def _canonical(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: 2MiB individual-stock leaf point input/output required')
    return raw


def _digest(value):return sha256(_canonical(value)).hexdigest()


def _pins():
    return {**stem._pins(),'backend/app/crop_stem_root_funded_leaf_point.py':CODE_SHA256}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: original individual-stock leaf point required')
    stem._fence()


def _cost(profiles):
    part=short.stock.part;profile=profiles['growth_profile']
    _need(type(profile)is part.source.ReferenceParameters and profile.sha256==part.source.PROFILE_SHA256==sha256(profile.raw_bytes).hexdigest(),
          'PROFILE_HOLD: original pinned growth profile required')
    cost=profile.values['cLeafG']
    _need(type(cost)is float and cost>0 and cost==float(json.loads(profile.raw_bytes)['parameters']['cLeafG']['value']),
          'PROFILE_HOLD: original cLeafG growth cost required')
    return cost


def _jump(p,y,profiles,events,anchors):
    n=len(p['leaves']);part=short.stock.part
    _need(type(events)is list and 1<=len(events)<=512-n,'CAPACITY_HOLD: nonempty events and at most512 resulting leaves required')
    _need(len(anchors)==n,'STATE_HOLD: original current leaf anchors required')
    ids={row['leaf_id']for row in p['leaves']};used=set()
    parents={row['compartment_id']for row in p['stem_root_compartments']if row['kind']=='internode'}
    leaves=[];receipts=[];capacities=[];energies=[]
    k=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value'];floor=p['model_floor_area']['value']
    for event in events:
        arithmetic._closed(event,{'event_id','parent_internode_id','incoming_temperature','leaf'})
        for key in ('event_id','parent_internode_id'):part._id(event[key])
        _need(event['parent_internode_id']in parents,'PARENT_HOLD: actual pre-point internode required')
        leaf,receipt=arithmetic._new_leaf(event['leaf'])
        _need(leaf['leaf_id']not in ids and event['event_id']not in used,'EVENT_HOLD: unique new leaf and event IDs required')
        ids.add(leaf['leaf_id']);used.add(event['event_id'])
        incoming=arithmetic._quantity(event['incoming_temperature'],'degC');numeric._temperature(incoming)
        area=receipt['state']['area']['value']
        capacity=arithmetic._rounded(Fraction.from_float(k)*Fraction.from_float(area)/Fraction.from_float(floor))
        energy=arithmetic._rounded(Fraction.from_float(capacity)*(Fraction.from_float(incoming)-Fraction.from_float(ref)))
        _need(capacity>0,'CAPACITY_HOLD: positive incoming leaf capacity required')
        leaves.append(leaf);capacities.append(capacity);energies.append(energy)
        receipts.append({'event_id':event['event_id'],'parent_internode_id':event['parent_internode_id'],
            'initialization':receipt,'capacity_in':numeric._q(capacity,numeric.CAPACITY),'sensible_in':numeric._q(energy,numeric.ENERGY)})
    masses=[row['initial_carbon']['value']for row in leaves];cost=_cost(profiles)
    structural,respiration,debit,buffer=arithmetic._fund(y[0],masses,cost)
    capacity=arithmetic._rounded(sum(map(Fraction.from_float,capacities),Fraction(0)))
    energy=arithmetic._rounded(sum(map(Fraction.from_float,energies),Fraction(0)))
    after_u=arithmetic._rounded(Fraction.from_float(y[103])+Fraction.from_float(energy))
    _need(energy==0 or after_u!=y[103],'NUMERIC_HOLD: nonzero incoming heat lost')
    base=list(y[:106]);base[0],base[103]=buffer,after_u
    after=[*base,*y[106:106+n],*([0.]*len(leaves)),*y[106+n:106+2*n],
        *(row['initialization']['state']['area']['value']for row in receipts),*y[106+2*n:106+3*n],*masses,*y[106+3*n:]]
    after_program={**deepcopy(p),'leaves':[*deepcopy(p['leaves']),*leaves]}
    rates,evaluation=short._evaluate(after_program,tuple(after),profiles)
    gaps=[*deepcopy(anchors),*(numeric._q(0.,'m2')for _ in leaves)]
    before_capacity=numeric._multiply(k,numeric._divide(numeric._sum(*y[106+n:106+2*n]),floor))
    after_capacity=short._view(evaluation)['joint']['derived']['canopy_capacity']['value']
    whole=lambda state,count:numeric._sum(state[0],*state[3:53],*state[106+2*count:])
    balances={'buffer':arithmetic._balance((buffer,-y[0],debit),MASS),
        'new_stock':arithmetic._balance((*masses,-structural),MASS),
        'whole_carbon':arithmetic._balance((whole(after,n+len(leaves)),-whole(y,n),respiration),MASS),
        'sensible':arithmetic._balance((after_u,-y[103],-energy),numeric.ENERGY),
        'capacity':arithmetic._balance((after_capacity,-before_capacity,-capacity),numeric.CAPACITY)}
    for i,mass in enumerate(masses):balances['new_leaf_'+str(i)]=arithmetic._balance((after[106+2*(n+len(leaves))+n+i],-mass),MASS)
    return {'program':after_program,'state':after,'rates':rates,'evaluation':evaluation,'anchors':gaps,'receipts':receipts,
        'before_capacity':before_capacity,'structural':structural,'respiration':respiration,'debit':debit,'cost':cost,'balances':balances,
        'capacity':capacity,'energy':energy}


def apply_leaf_births(context,raw_checkpoint,expected_sha256,crop_directory,stem_directory,access,*,
                          crop_root_sha256,stem_root_sha256,stem_start_index,binding_declaration,inputs):
    try:
        _fence();pins=_pins();arithmetic._closed(inputs,FIELDS)
        _need(type(inputs['events'])is list,'INPUT_HOLD: explicit event list required')
        raw=_canonical(inputs);v=json.loads(raw);part=short.stock.part;part._id(v['input_id']);part._id(v['reviewer']);stem._rights(v['rights'])
        _need(v['schema_version']=='stem-root-funded-leaf-point-input-v1'and v['origin']=='synthetic'and v['policy']==POLICY,
              'POLICY_HOLD: explicit synthetic new leaf structure required')
        source_kw={'crop_root_sha256':crop_root_sha256,'stem_root_sha256':stem_root_sha256,'stem_start_index':stem_start_index,'declaration':binding_declaration}
        initial=binding.bind_initial_stem_carbon(context,crop_directory,stem_directory,access,**source_kw)
        _need(v['initial_binding_sha256']==_digest(initial),'SOURCE_HOLD: original complete initial binding required')
        cp=resume.restore_checkpoint(context,raw_checkpoint,expected_sha256=expected_sha256)
        p,seed,manifest=resume._context(context);saved=cp.value;y=saved['last_confirmed']['state']
        captured_context=(context._request,context._program,context._seed,context._manifest)
        _need(v['context_sha256']==context.root_sha256 and v['checkpoint_sha256']==cp.sha256,'HASH_HOLD: actual current context/checkpoint required')
        at=Fraction.from_float(manifest['numerical']['step_seconds'])*saved['step_index']
        _need(arithmetic.clock._seconds(v['at_elapsed_seconds_exact'])==at,'TIME_HOLD: exact current checkpoint time required')
        _need(arithmetic._quantity(v['model_floor_area'],'m2_floor')==p['model_floor_area']['value'],'BASIS_HOLD: original common footprint required')
        profiles=resume._profiles(context);cost=_cost(profiles)
        profile_snapshot={name:(profile.raw_bytes,deepcopy(dict(profile.values)))for name,profile in profiles.items()}
        jump=_jump(p,y,profiles,v['events'],seed['evaluation']['curve_residuals'])
        after_program,after,rates,evaluation=(jump[k]for k in ('program','state','rates','evaluation'))
        receipts,structural,respiration,debit,balances=(jump[k]for k in ('receipts','structural','respiration','debit','balances'))
        sample=short._sample(saved['step_index'],manifest['numerical']['step_seconds'],after,evaluation,jump['anchors'])
        n=len(p['leaves']);new_n=len(after_program['leaves'])
        _need(after[1:103]==y[1:103]and after[104:106]==y[104:106]and after[106+3*new_n:]==y[106+3*n:]and
              jump['before_capacity']==saved['last_confirmed']['derived']['canopy_capacity']['value'],
              'STATE_HOLD: original non-buffer/non-canopy scalar and stem/root stocks required')
        result={'model_version':VERSION,'policy':POLICY,'scope':'software_research_only','G0_G4':'not_assessed',
            'claim_scope':'synthetic_declared_new_leaf_structural_allocation_with_individual_stem_root_stocks_only',
            'time_kind':'synthetic_model_clock_not_observation','timing_status':'declared_at_validated_checkpoint_not_threshold_detection',
            'code_sha256':CODE_SHA256,'source_code_sha256':pins,'context_sha256':context.root_sha256,'checkpoint_sha256':cp.sha256,
            'input_sha256':sha256(raw).hexdigest(),'inputs':v,'initial_binding':initial,'initial_binding_sha256':v['initial_binding_sha256'],
            'parent_manifest':manifest,'before_checkpoint':saved,'after_program':after_program,'after_sample':sample,
            'after_rates':list(rates),'after_anchors':jump['anchors'],'after_state_layout':short._layout(after_program),'birth_receipts':receipts,
            'growth_cost':{'parameter':'cLeafG','value':cost,'unit':'mg_CH2O/mg_CH2O','profile_sha256':profiles['growth_profile'].sha256},
            'point_flows':{name:numeric._q(value,MASS)for name,value in [('structural_carbon',structural),('growth_respiration',respiration),('buffer_debit',debit)]}|{name:numeric._q(value,unit)for name,value,unit in [('capacity_in',jump['capacity'],numeric.CAPACITY),('sensible_in',jump['energy'],numeric.ENERGY)]},
            'balances':balances,'point_capacity_and_sensible_change':'declared_new_leaf_capacity_and_incoming_sensible_heat',
            'redistribution_authorized':initial['redistribution_authorized']and v['rights']['redistribute'],
            'checkpoint_validation_stage_evaluations':1,'after_stage_evaluations':1,'elapsed_steps_advanced':0,'checkpoint':None,
            'global_prefix_adoption':'pending_variable_inventory_continuation','geometry_and_automatic_emergence':'declared_leaf_area_only_no_carbon_supply_limited_geometry_or_threshold_detection'}
        result['calculation_sha256']=_digest(result);_canonical(result)
        _need(binding.bind_initial_stem_carbon(context,crop_directory,stem_directory,access,**source_kw)==initial,
              'SOURCE_HOLD: original initial source changed before return')
        _need(resume._context(context)==(p,seed,manifest)and captured_context==(context._request,context._program,context._seed,context._manifest),
              'CONTEXT_HOLD: original point context required')
        _need({name:(profile.raw_bytes,dict(profile.values))for name,profile in profiles.items()}==profile_snapshot and _cost(profiles)==cost,
              'PROFILE_HOLD: original point profiles required')
        _need(_pins()==pins,'CODE_HOLD: point dependencies changed');_fence()
        return deepcopy(result)
    except LeafBirthHold:raise
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise LeafBirthHold(str(error))from None
