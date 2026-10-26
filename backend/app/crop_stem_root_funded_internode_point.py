"""Declared internode material jump; crop-stem-root-funded-internode-point-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from . import crop_stem_root_initial_binding as binding
from . import crop_leaf_funded_birth_point as arithmetic

resume=binding.crop
short=resume.short
numeric=short.numeric
MASS=short.stock.part.source.MASS_UNIT
VERSION='stem-root-funded-internode-point-research-v1'
POLICY='explicit-new-internode-carbon-from-buffer-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES=2*1024**2
FIELDS={'schema_version','input_id','origin','policy','context_sha256','checkpoint_sha256',
        'initial_binding_sha256','at_elapsed_seconds_exact','model_floor_area','events','rights','reviewer'}


class InternodeBirthHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise InternodeBirthHold(reason)


def _canonical(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: 2MiB internode point input/output required')
    return raw


def _digest(value):return sha256(_canonical(value)).hexdigest()


def _pins():
    return {**binding._pins(),'backend/app/crop_leaf_funded_birth_point.py':arithmetic.CODE_SHA256,
            'backend/app/crop_stem_root_funded_internode_point.py':CODE_SHA256}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: original internode point required')
    binding._fence();arithmetic._fence();resume._fence()


def _cost(profiles):
    part=short.stock.part;profile=profiles['growth_profile']
    _need(type(profile)is part.source.ReferenceParameters and profile.sha256==part.source.PROFILE_SHA256==sha256(profile.raw_bytes).hexdigest(),
          'PROFILE_HOLD: original pinned growth profile required')
    cost=profile.values['cStemG']
    _need(type(cost)is float and cost>0 and cost==float(json.loads(profile.raw_bytes)['parameters']['cStemG']['value']),
          'PROFILE_HOLD: original cStemG growth cost required')
    return cost


def _rights(value):
    carbon=binding.carbon
    carbon._closed(value,{'declaration_id','revision','declared_at_utc','ownership_asserted','access','store','use','transform','display','redistribute'})
    for key in ('declaration_id','revision'):carbon._id(value[key])
    carbon._utc(value['declared_at_utc'])
    _need(all(value[k]is True for k in ('ownership_asserted','access','store','use','transform','display'))and type(value['redistribute'])is bool,
          'RIGHTS_HOLD: explicit synthetic point rights required')


def _jump(p,y,profiles,events):
    part=short.stock.part;rows=p['stem_root_compartments'];n=len(p['leaves']);offset=106+3*n
    _need(1<=len(events)<=512-len(rows),'CAPACITY_HOLD: nonempty events and at most512 resulting organs required')
    existing={r['compartment_id']for r in rows};parents={r['compartment_id']for r in rows if r['kind']=='internode'}
    used=set();new=[];receipts=[];event_ids=set()
    for event in events:
        arithmetic._closed(event,{'event_id','parent_internode_id','compartment'})
        for key in ('event_id','parent_internode_id'):part._id(event[key])
        _need(event['parent_internode_id']in parents,'PARENT_HOLD: actual pre-point internode parent required')
        row=event['compartment'];arithmetic._closed(row,{'compartment_id','kind',*short.STOCK_FIELDS});part._id(row['compartment_id'])
        _need(row['kind']=='internode'and row['compartment_id']not in existing|used and event['event_id']not in event_ids,
              'EVENT_HOLD: unique new internode and event IDs required')
        values={k:arithmetic._quantity(row[k],unit)for k,unit in short.STOCK_FIELDS.items()}
        _need(values['initial_carbon']>0 and values['sink_weight']>=0 and values['carbon_removal']>=0,
              'BIRTH_HOLD: positive declared initial carbon and nonnegative sink/removal required')
        item={'compartment_id':row['compartment_id'],'kind':'internode',
              **{k:numeric._q(value,short.STOCK_FIELDS[k])for k,value in values.items()}}
        used.add(row['compartment_id']);event_ids.add(event['event_id']);new.append(item)
        receipts.append({'event_id':event['event_id'],'parent_internode_id':event['parent_internode_id'],
            'compartment_id':item['compartment_id'],'initial_carbon':deepcopy(item['initial_carbon'])})
    cost=_cost(profiles)
    masses=[row['initial_carbon']['value']for row in new]
    structural,respiration,debit,buffer=arithmetic._fund(y[0],masses,cost)
    after=[buffer,*y[1:],*masses];after_program={**deepcopy(p),'stem_root_compartments':[*deepcopy(rows),*new]}
    rates,evaluation=short._evaluate(after_program,tuple(after),profiles)
    whole=lambda state:numeric._sum(state[0],*state[3:53],*state[106+2*n:])
    balances={'buffer':arithmetic._balance((buffer,-y[0],debit),MASS),
        'new_stock':arithmetic._balance((*masses,-structural),MASS),
        'whole_carbon':arithmetic._balance((whole(after),-whole(y),respiration),MASS)}
    for i,mass in enumerate(masses):balances['new_internode_'+str(i)]=arithmetic._balance((after[offset+len(rows)+i],-mass),MASS)
    return {'program':after_program,'state':after,'rates':rates,'evaluation':evaluation,'receipts':receipts,
            'structural':structural,'respiration':respiration,'debit':debit,'cost':cost,'balances':balances}


def apply_internode_births(context,raw_checkpoint,expected_sha256,crop_directory,stem_directory,access,*,
                          crop_root_sha256,stem_root_sha256,stem_start_index,binding_declaration,inputs):
    try:
        _fence();pins=_pins();arithmetic._closed(inputs,FIELDS)
        _need(type(inputs['events'])is list,'INPUT_HOLD: explicit event list required')
        raw=_canonical(inputs);v=json.loads(raw);part=short.stock.part;part._id(v['input_id']);part._id(v['reviewer']);_rights(v['rights'])
        _need(v['schema_version']=='stem-root-funded-internode-point-input-v1'and v['origin']=='synthetic'and v['policy']==POLICY,
              'POLICY_HOLD: explicit synthetic new internode structure required')
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
        jump=_jump(p,y,profiles,v['events'])
        after_program,after,rates,evaluation=(jump[k]for k in ('program','state','rates','evaluation'))
        receipts,structural,respiration,debit,balances=(jump[k]for k in ('receipts','structural','respiration','debit','balances'))
        sample=short._sample(saved['step_index'],manifest['numerical']['step_seconds'],after,evaluation,seed['evaluation']['curve_residuals'])
        _need(after[1:len(y)]==y[1:]and sample['derived']['canopy_capacity']==saved['last_confirmed']['derived']['canopy_capacity'],
              'STATE_HOLD: original non-buffer stocks/geometry/climate required')
        result={'model_version':VERSION,'policy':POLICY,'scope':'software_research_only','G0_G4':'not_assessed',
            'claim_scope':'synthetic_declared_new_internode_structural_allocation_at_current_checkpoint_only',
            'time_kind':'synthetic_model_clock_not_observation','timing_status':'declared_at_validated_checkpoint_not_threshold_detection',
            'code_sha256':CODE_SHA256,'source_code_sha256':pins,'context_sha256':context.root_sha256,'checkpoint_sha256':cp.sha256,
            'input_sha256':sha256(raw).hexdigest(),'inputs':v,'initial_binding':initial,'initial_binding_sha256':v['initial_binding_sha256'],
            'parent_manifest':manifest,'before_checkpoint':saved,'after_program':after_program,'after_sample':sample,
            'after_rates':list(rates),'after_state_layout':short._layout(after_program),'birth_receipts':receipts,
            'growth_cost':{'parameter':'cStemG','value':cost,'unit':'mg_CH2O/mg_CH2O','profile_sha256':profiles['growth_profile'].sha256},
            'point_flows':{name:numeric._q(value,MASS)for name,value in [('structural_carbon',structural),('growth_respiration',respiration),('buffer_debit',debit)]},
            'balances':balances,'point_capacity_and_sensible_change':'zero_no_leaf_or_climate_jump',
            'redistribution_authorized':initial['redistribution_authorized']and v['rights']['redistribute'],
            'checkpoint_validation_stage_evaluations':1,'after_stage_evaluations':1,'elapsed_steps_advanced':0,'checkpoint':None,
            'global_prefix_adoption':'pending_variable_inventory_continuation','geometry_and_automatic_emergence':'not_derived'}
        result['calculation_sha256']=_digest(result);_canonical(result)
        _need(binding.bind_initial_stem_carbon(context,crop_directory,stem_directory,access,**source_kw)==initial,
              'SOURCE_HOLD: original initial source changed before return')
        _need(resume._context(context)==(p,seed,manifest)and captured_context==(context._request,context._program,context._seed,context._manifest),
              'CONTEXT_HOLD: original point context required')
        _need({name:(profile.raw_bytes,dict(profile.values))for name,profile in profiles.items()}==profile_snapshot and _cost(profiles)==cost,
              'PROFILE_HOLD: original point profiles required')
        _need(_pins()==pins,'CODE_HOLD: point dependencies changed');_fence()
        return deepcopy(result)
    except InternodeBirthHold:raise
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise InternodeBirthHold(str(error))from None
