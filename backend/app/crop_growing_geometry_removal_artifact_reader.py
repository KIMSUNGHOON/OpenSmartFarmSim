"""Trusted phase-aware stored replay; imports no crop calculation modules."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_growing_geometry_artifact_reader as base
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need
from .crop_morphology_artifact_reader import _canonical,_closed,_hash,_id,_parse

MAX=base.MAX
CHECKPOINT_MAX=base.CHECKPOINT_MAX
EXTRA_NAMES=('crop_growing_geometry_leaf_removal_point','crop_growing_geometry_post_removal_context',
    'crop_growing_geometry_removal_next_interval','crop_rational_morphology_clock',
    'crop_growing_geometry_removal_artifact_reader','crop_growing_geometry_removal_artifact_producer')
SOURCE_PATHS=tuple(dict.fromkeys((*base.SOURCE_PATHS,*(f'backend/app/{name}.py'for name in EXTRA_NAMES))))
SOURCE_NAMES={*base.SOURCE_NAMES,'point_inputs','point_result','post_context','post_program','post_seed','post_snapshot'}
ROOT_CONSTANTS={**base.ROOT_CONSTANTS,'schema_version':'growing-geometry-removal-research-artifact-v1',
    'claim_scope':'synthetic_growing_geometry_removal_replay_only'}
ROOT_FIELDS={*ROOT_CONSTANTS,'input_id','source_rights','time_origin_utc','sources','code_sha256',
    'parent_context_sha256','post_context_sha256','point_calculation_sha256','initial_state_sha256','terminal_state_sha256',
    'event_step_index','samples'}
DESCRIPTOR_FIELDS={*base.DESCRIPTOR_FIELDS,'phase','global_step_index'}
POINT_FIELDS={'schema_version','input_id','origin','context_sha256','checkpoint_sha256','at_elapsed_seconds_exact','mass_basis','events'}
OUTFLOW_UNITS={'carbohydrate':'mg_CH2O/m2_floor','capacity':'J/m2_floor/K','sensible_energy':'J/m2_floor'}
SEED_FIELDS={'last_confirmed','active_original_curve_invariant','original_curve_invariant','original_initial_area_receipts',
    'original_interval_transfers','point_outflows','removed_last_states','segment_integrated_transfers'}
POINT_VERSION='growing-geometry-leaf-removal-point-research-v1'
POST_VERSION='growing-geometry-post-removal-context-research-v1'
POST_SNAPSHOT='growing-geometry-post-removal-snapshot-v1'
ENGINE_VERSION='growing-geometry-removal-next-interval-research-v1'
ENGINE_CHECKPOINT='growing-geometry-post-removal-continuation-checkpoint-v1'


class RemovalArtifactHold(MorphologyArtifactHold):
    pass


def _digest(value):return sha256(_canonical(value)).hexdigest()


def _pins():
    root=Path(__file__).resolve().parents[2]
    try:return {name:sha256((root/name).read_bytes()).hexdigest()for name in SOURCE_PATHS}
    except OSError:raise RemovalArtifactHold('CODE_HOLD: required removal source unavailable')from None


def _parent_inputs(inputs):
    value={k:v for k,v in inputs.items()if k not in ('event_step_index','point_inputs')}
    value['schema_version']='growing-geometry-artifact-input-v1';return value


def _inputs(raw):
    v=_parse(raw,MAX)
    _closed(v,{'schema_version','input_id','origin','rights','time_origin_utc','step_seconds','step_count','program','event_step_index','point_inputs'})
    _need(v['schema_version']=='growing-geometry-removal-artifact-input-v1','SCOPE_HOLD: explicit removal artifact input required')
    base._inputs(_canonical(_parent_inputs(v)))
    event=v['event_step_index'];p=v['program'];n=len(p['leaves'])
    _need(type(event)is int and 0<=event<=v['step_count']and (v['step_count']+2)*(115+4*n)<=32768,
        'CAPACITY_HOLD: bounded complete event timeline required')
    _need(p['capacity_outflow']['value']==0 and p['scenario']['removals']['leaf']['value']==0,
        'DUPLICATE_REMOVAL_HOLD: continuous leaf/capacity outflow requires attribution')
    x=v['point_inputs'];_closed(x,POINT_FIELDS)
    _need(x['schema_version']=='growing-geometry-leaf-removal-point-input-v1'and x['origin']=='synthetic',
        'SCOPE_HOLD: original synthetic removal input required')
    _id(x['input_id']);_hash(x['context_sha256']);_hash(x['checkpoint_sha256'])
    _need(x['at_elapsed_seconds_exact']==base._offset(v['step_seconds'],event),'TIME_HOLD: original exact event grid required')
    basis=x['mass_basis'];_closed(basis,{'origin','evidence_level','evidence_id','model_floor_area','leaves'})
    _need(basis['origin']=='synthetic'and basis['evidence_level']=='assumed','SCOPE_HOLD: explicit assumed current masses required')
    _id(basis['evidence_id']);base._q(basis['model_floor_area'],'m2_floor')
    _need(basis['model_floor_area']==p['model_floor_area'],'BASIS_HOLD: same footprint required')
    records=basis['leaves'];_need(type(records)is list and len(records)==n,'MASS_HOLD: complete current leaf distribution required')
    masses={}
    for leaf,row in zip(p['leaves'],records,strict=True):
        _closed(row,{'leaf_id','carbohydrate'});base._q(row['carbohydrate'],'mg_CH2O')
        _need(row['leaf_id']==leaf['leaf_id']and row['carbohydrate']['value']>0,'MASS_HOLD: original positive leaf masses required')
        masses[row['leaf_id']]=row['carbohydrate']
    events=x['events'];_need(type(events)is list and 1<=len(events)<n,'EMPTY_CANOPY_HOLD: nonempty partial removal batch required')
    ids=set();removed=set()
    for row in events:
        _closed(row,{'event_id','leaf_id','carbohydrate','capacity','sensible_energy','outgoing_temperature'})
        _id(row['event_id']);_id(row['leaf_id'])
        _need(row['event_id']not in ids and row['leaf_id']in masses and row['leaf_id']not in removed,
            'EVENT_HOLD: original unique leaf/event required')
        for k,unit in {'carbohydrate':'mg_CH2O','capacity':'J/m2_floor/K','sensible_energy':'J/m2_floor','outgoing_temperature':'degC'}.items():base._q(row[k],unit)
        _need(row['carbohydrate']==masses[row['leaf_id']]and row['capacity']['value']>0,'MASS_HOLD: original current leaf removal required')
        ids.add(row['event_id']);removed.add(row['leaf_id'])
    return v


def _sample(sample,p,index,dt):
    _closed(sample,{'step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes'})
    _need(type(sample['step_index'])is int and sample['step_index']==index and type(sample['elapsed_seconds'])is float
        and sample['elapsed_seconds']==index*float(dt),'TIME_HOLD: original float sample coordinate required')
    base._state(sample['state'],p);base._block(sample['derived'],base.DERIVED_UNITS,normalized=True)
    for name in ('curve_residuals','curve_invariant_changes'):
        rows=sample[name];_need(type(rows)is list and len(rows)==len(p['leaves']),'FORMAT_HOLD: original leaf diagnostics required')
        for row in rows:base._q(row,'m2',normalized=True)


def _budgets(cp,p,*,global_=False):
    units={**base.BALANCE_UNITS,**{f'leaf_age_{i}':'degC_day'for i in range(len(p['leaves']))}}
    prefix='global_'if global_ else''
    for name in ('balance_residuals','balance_budgets'):base._block(cp[prefix+name],units,normalized=True)
    _need(all(cp[prefix+'balance_budgets'][k]['value']>=0 and abs(cp[prefix+'balance_residuals'][k]['value'])<=cp[prefix+'balance_budgets'][k]['value']for k in units),
        'QC_HOLD: recorded removal residual exceeds budget')


def _post_sources(m,raws,inputs,p,c,seed,before,pins):
    point=_parse(raws['point_result'],MAX);x=inputs['point_inputs'];cut=inputs['event_step_index']
    fields={'model_version','code_sha256','input_sha256','context_sha256','checkpoint_sha256','parent_identity',
        'original_program_sha256','original_seed_sha256','inputs','at_elapsed_seconds_exact','time_coordinate','before','after',
        'removed_last_states','original_curve_invariant','original_initial_area_receipts','original_interval_transfers','point_outflows',
        'event_balances','balances','continuation_checkpoint','scope','claim_scope','G0_G4','calculation_sha256'}
    _closed(point,fields)
    _need(point['model_version']==POINT_VERSION and point['code_sha256']==pins['backend/app/crop_growing_geometry_leaf_removal_point.py']
        and point['context_sha256']==m['parent_context_sha256']==x['context_sha256']
        and point['checkpoint_sha256']==m['samples'][cut]['checkpoint_sha256']==x['checkpoint_sha256']
        and point['input_sha256']==m['sources']['point_inputs']['sha256']and _canonical(x)==raws['point_inputs']
        and point['inputs']==x and point['parent_identity']==c['identity']
        and point['original_program_sha256']==m['sources']['program']['sha256']and point['original_seed_sha256']==m['sources']['seed']['sha256']
        and point['calculation_sha256']==m['point_calculation_sha256']==_digest({k:v for k,v in point.items()if k!='calculation_sha256'}),
        'HASH_HOLD: original point/source binding differs')
    _need(point['scope']=='software_research_only'and point['claim_scope']=='synthetic_independent_area_leaf_removal_point_only'
        and point['G0_G4']=='not_assessed'and point['continuation_checkpoint']is False
        and point['time_coordinate']=='same_elapsed_instant_no_UTC_no_advance'
        and point['at_elapsed_seconds_exact']==base._offset(inputs['step_seconds'],cut)and point['before']==before['last_confirmed'],
        'SCOPE_HOLD: original instantaneous point required')
    removed={r['leaf_id']for r in x['events']};keep=[i for i,l in enumerate(p['leaves'])if l['leaf_id']not in removed]
    active={**p,'leaves':[p['leaves'][i]for i in keep]};ids=[p['leaves'][i]['leaf_id']for i in keep]
    after=point['after'];_closed(after,{'state','leaf_ids','leaf_area_index','capacity','canopy_temperature','original_leaf_indices'})
    base._state(after['state'],active)
    for name,unit in {'leaf_area_index':'m2_leaf/m2_floor','capacity':'J/m2_floor/K','canopy_temperature':'degC'}.items():base._q(after[name],unit,normalized=True)
    y=before['last_confirmed']['state'];z=after['state'];n=len(p['leaves'])
    _need(after['leaf_ids']==ids and after['original_leaf_indices']==keep and z[:1]==y[:1]and z[2:105]==y[2:105]
        and z[106:108]==y[106:108]and z[108:108+len(keep)]==[y[108+i]for i in keep]
        and z[108+len(keep):]==[y[108+n+i]for i in keep],'HASH_HOLD: original active state mapping differs')
    base._block(point['point_outflows'],OUTFLOW_UNITS,normalized=True)
    units={'carbon':'mg_CH2O/m2_floor','remaining_mass':'mg_CH2O/m2_floor','capacity':'J/m2_floor/K','sensible_energy':'J/m2_floor'}
    _closed(point['balances'],units)
    for name,unit in units.items():
        row=point['balances'][name];_closed(row,{'residual','budget'})
        for v in row.values():base._q(v,unit,normalized=True)
        _need(row['budget']['value']>=0 and abs(row['residual']['value'])<=row['budget']['value'],'QC_HOLD: original point balance')
    _need(point['original_curve_invariant']==seed['evaluation']['curve_residuals']
        and point['original_initial_area_receipts']==seed['initial_area_receipts']
        and point['original_interval_transfers']==before['integrated_transfers'],'HASH_HOLD: original point anchors/ledger differ')
    balances=point['event_balances']
    _need(type(balances)is list and len(balances)==len(x['events']),'FORMAT_HOLD: complete event diagnostics required')
    for record,event in zip(balances,x['events'],strict=True):
        _closed(record,{'event_id','capacity','energy'});_need(record['event_id']==event['event_id'],'HASH_HOLD: original event diagnostic differs')
        for name,unit in (('capacity','J/m2_floor/K'),('energy','J/m2_floor')):
            row=record[name];_closed(row,{'residual','budget'})
            for q in row.values():base._q(q,unit,normalized=True)
            _need(row['budget']['value']>=0 and abs(row['residual']['value'])<=row['budget']['value'],'QC_HOLD: original event diagnostic')
    expected_removed=[{'leaf_id':e['leaf_id'],'thermal_age':{'value':y[108+next(i for i,l in enumerate(p['leaves'])if l['leaf_id']==e['leaf_id'])],'unit':'degC_day'},
        'area':{'value':y[108+n+next(i for i,l in enumerate(p['leaves'])if l['leaf_id']==e['leaf_id'])],'unit':'m2'}}for e in x['events']]
    _need(point['removed_last_states']==expected_removed,'HASH_HOLD: original removed last states differ')
    pc=_parse(raws['post_context'],MAX);ps=_parse(raws['post_seed'],MAX);ap=_parse(raws['post_program'],MAX)
    _closed(pc,{'identity','parent_context_sha256','original_request_sha256','original_program_sha256','original_seed_sha256',
        'point_input_sha256','point_calculation_sha256','parent_checkpoint_sha256','point_sha256','program_sha256','seed_sha256',
        'at_elapsed_seconds_exact','original_leaf_indices','numerical','state_layout'})
    _closed(ps,SEED_FIELDS)
    identity={'model_version':POST_VERSION,'code_sha256':pins['backend/app/crop_growing_geometry_post_removal_context.py'],
        'point_version':POINT_VERSION,'point_code_sha256':pins['backend/app/crop_growing_geometry_leaf_removal_point.py'],
        'parent_identity':c['identity'],'state_schema':POST_SNAPSHOT}
    _need(pc['identity']==identity and m['post_context_sha256']==m['sources']['post_context']['sha256']
        and pc['parent_context_sha256']==m['parent_context_sha256']
        and all(pc['original_'+k+'_sha256']==m['sources'][k]['sha256']for k in ('request','program','seed'))
        and pc['point_input_sha256']==m['sources']['point_inputs']['sha256']and pc['point_calculation_sha256']==point['calculation_sha256']
        and pc['parent_checkpoint_sha256']==m['samples'][cut]['checkpoint_sha256']and pc['point_sha256']==m['sources']['point_result']['sha256']
        and pc['program_sha256']==m['sources']['post_program']['sha256']and pc['seed_sha256']==m['sources']['post_seed']['sha256'],
        'HASH_HOLD: original post-context bindings differ')
    _need(sum(map(len,(raws['point_result'],raws['post_program'],raws['post_seed'],raws['post_context'])))+m['samples'][cut]['checkpoint_bytes']<=MAX,
        'CAPACITY_HOLD: post-context combined bytes exceeded')
    _need(ap==active and _canonical(pc['original_leaf_indices'])==_canonical(keep)and _canonical(after['original_leaf_indices'])==_canonical(keep)
        and pc['at_elapsed_seconds_exact']==x['at_elapsed_seconds_exact']
        and _canonical(pc['numerical'])==_canonical({**c['numerical'],'event_global_step_index':cut,'remaining_steps':inputs['step_count']-cut})
        and pc['state_layout']=={**c['state_layout'],'leaf_ids':ids},'FORMAT_HOLD: original post program/layout/grid differs')
    _sample(ps['last_confirmed'],active,cut,inputs['step_seconds'])
    _need(ps['last_confirmed']['state']==z and ps['original_curve_invariant']==seed['evaluation']['curve_residuals']
        and ps['active_original_curve_invariant']==[seed['evaluation']['curve_residuals'][i]for i in keep]
        and ps['original_initial_area_receipts']==seed['initial_area_receipts']and ps['original_interval_transfers']==before['integrated_transfers']
        and ps['point_outflows']==point['point_outflows']and ps['removed_last_states']==point['removed_last_states']
        and all(ps['last_confirmed'][k]==[before['last_confirmed'][k][i]for i in keep]for k in ('curve_residuals','curve_invariant_changes')),
        'HASH_HOLD: original post seed/state/anchors/ledgers differ')
    for name,key in (('leaf_area_index','leaf_area_index'),('canopy_capacity','capacity'),('canopy_temperature','canopy_temperature')):
        _need(ps['last_confirmed']['derived'][name]==after[key],'HASH_HOLD: original post derived differs')
    base._block(ps['segment_integrated_transfers'],base.FLUX_UNITS,normalized=True)
    _need(all(q['value']==0 for q in ps['segment_integrated_transfers'].values()),'HASH_HOLD: segment must start at zero')
    snapshot={'version':POST_SNAPSHOT,'context_sha256':m['post_context_sha256'],'phase':'after_removal_before_next_step',
        'segment_step_index':0,'original_global_step_index':cut,'at_elapsed_seconds_exact':x['at_elapsed_seconds_exact'],**ps,
        'scope':'software_research_only','claim_scope':'synthetic_post_removal_context_only','G0_G4':'not_assessed'}
    _need(_canonical(snapshot)==raws['post_snapshot'],'HASH_HOLD: original post snapshot differs')
    return active,pc,ps


def _post_checkpoint(raw,d,m,p,seed,context,previous_prefix):
    cp=_parse(raw,CHECKPOINT_MAX)
    fields={'context_sha256','original_global_step_index','phase','segment_step_index','at_elapsed_seconds_exact','last_confirmed',
        'active_original_curve_invariant','original_interval_transfers','point_outflows','segment_integrated_transfers','event_snapshot_sha256',
        'original_curve_invariant_sha256','original_initial_area_receipts_sha256','removed_last_states_sha256','scope','G0_G4','version',
        'engine_identity','global_step_index','output_cursor','output_prefix_sha256','balance_residuals','balance_budgets',
        'global_balance_residuals','global_balance_budgets','claim_scope'}
    _closed(cp,fields);local=d['index']-m['event_step_index']-1;index=d['global_step_index']
    identity={'model_version':ENGINE_VERSION,'code_sha256':m['code_sha256']['backend/app/crop_growing_geometry_removal_next_interval.py'],
        'post_context_code_sha256':m['code_sha256']['backend/app/crop_growing_geometry_post_removal_context.py']}
    _need(cp['version']==ENGINE_CHECKPOINT and cp['engine_identity']==identity and cp['context_sha256']==m['post_context_sha256']
        and cp['scope']=='software_research_only'and cp['claim_scope']=='synthetic_post_removal_joint_continuation_only'and cp['G0_G4']=='not_assessed'
        and type(cp['segment_step_index'])is int and cp['segment_step_index']==local
        and type(cp['global_step_index'])is int and cp['global_step_index']==index
        and type(cp['original_global_step_index'])is int and cp['original_global_step_index']==m['event_step_index']
        and type(cp['output_cursor'])is int and cp['output_cursor']==local+1
        and cp['phase']==d['phase']and cp['at_elapsed_seconds_exact']==d['elapsed_seconds_exact'],'HASH_HOLD: original interval identity/time differs')
    for key in ('active_original_curve_invariant','original_interval_transfers','point_outflows'):
        _need(cp[key]==seed[key],'HASH_HOLD: changed immutable source/point ledger')
    for key in ('original_curve_invariant','original_initial_area_receipts','removed_last_states'):
        _need(cp[key+'_sha256']==_digest(seed[key]),'HASH_HOLD: changed original source reference')
    _need(cp['event_snapshot_sha256']==m['sources']['post_snapshot']['sha256'],'HASH_HOLD: original event snapshot differs')
    _sample(cp['last_confirmed'],p,index,context['numerical']['step_seconds'])
    base._block(cp['segment_integrated_transfers'],base.FLUX_UNITS,normalized=True);_budgets(cp,p);_budgets(cp,p,global_=True)
    if local==0:
        _need(cp['last_confirmed']==seed['last_confirmed']and cp['segment_integrated_transfers']==seed['segment_integrated_transfers'],
            'HASH_HOLD: original interval initial sample differs')
        previous_prefix=_digest({'context_sha256':m['post_context_sha256'],'engine_identity':identity})
    prefix=_digest({'previous':previous_prefix,'sample':cp['last_confirmed']})
    _need(cp['output_prefix_sha256']==prefix and _digest(cp['last_confirmed'])==d['sample_sha256']
        and _digest(cp['last_confirmed']['state'])==d['state_sha256'],'HASH_HOLD: original interval sample/prefix differs')
    return cp,prefix


def _graph(store,m):
    _closed(m,ROOT_FIELDS);_need(all(_canonical(m[k])==_canonical(v)for k,v in ROOT_CONSTANTS.items()),'SCOPE_HOLD: supported removal replay required')
    pins=_pins();_need(m['code_sha256']==pins,'CODE_HOLD: stored removal source version differs');_closed(m['sources'],SOURCE_NAMES)
    raws={name:base._source(store,d)for name,d in m['sources'].items()}
    for name,expected in {**base.PROFILE_SHA,'license_notice':base.NOTICE_SHA}.items():
        _need(m['sources'][name]['sha256']==expected,'PROFILE_HOLD: original reference/notice bytes required')
    inputs=_inputs(raws['inputs']);cut=inputs['event_step_index'];dt=inputs['step_seconds'];count=inputs['step_count']
    _need(m['input_id']==inputs['input_id']and m['source_rights']==inputs['rights']and m['time_origin_utc']==inputs['time_origin_utc']
        and type(m['event_step_index'])is int and m['event_step_index']==cut,'HASH_HOLD: original removal identity/rights/epoch differs')
    parent_m={**m,'context_sha256':m['parent_context_sha256']}
    p,c,seed=base._context(parent_m,raws,_parent_inputs(inputs),pins)
    descriptors=m['samples'];_need(type(descriptors)is list and len(descriptors)==count+2,'FORMAT_HOLD: complete phase timeline required')
    previous=None;pre_prefix=_digest([]);post_prefix=None;checkpoints=[];active=pc=ps=None
    for i,d in enumerate(descriptors):
        _closed(d,DESCRIPTOR_FIELDS);global_i=i if i<=cut else i-1
        phase='before_removal'if i<=cut else'after_removal_before_next_step'if i==cut+1 else'post_removal_interval'
        _need(type(d['index'])is int and d['index']==i and type(d['global_step_index'])is int and d['global_step_index']==global_i
            and d['phase']==phase and d['elapsed_seconds_exact']==base._offset(dt,global_i)
            and d['previous_checkpoint_sha256']==previous,'HASH_HOLD: original order/phase/time/chain differs')
        for k in ('checkpoint_sha256','sample_sha256','state_sha256'):_hash(d[k])
        raw=base._source(store,{'sha256':d['checkpoint_sha256'],'bytes':d['checkpoint_bytes']},maximum=CHECKPOINT_MAX);raws['checkpoint_'+str(i)]=raw
        if i<=cut:
            cp,pre_prefix=base._checkpoint(raw,{**d,'index':global_i},parent_m,p,seed,pre_prefix)
        else:
            if i==cut+1:active,pc,ps=_post_sources(m,raws,inputs,p,c,seed,checkpoints[-1],pins)
            cp,post_prefix=_post_checkpoint(raw,d,m,active,ps,pc,post_prefix)
        _need(cp['last_confirmed']['elapsed_seconds']==float(Fraction.from_float(float(dt))*global_i),
            'TIME_HOLD: original exact/float coordinate differs')
        checkpoints.append(cp);previous=d['checkpoint_sha256']
    _need(m['terminal_state_sha256']==descriptors[-1]['state_sha256'],'HASH_HOLD: terminal state differs')
    return inputs,p,c,seed,active,pc,ps,checkpoints,raws


def _fence(store,m,raws):
    _need(_pins()==m['code_sha256'],'CODE_HOLD: source changed before return');_inputs(raws['inputs'])
    for raw in raws.values():_need(store.get(sha256(raw).hexdigest(),maximum=MAX)==raw,'HASH_HOLD: original replay evidence changed')
    _need(_pins()==m['code_sha256'],'CODE_HOLD: source changed during final read')


def _read(directory,access,root_sha256,index):
    try:
        _hash(root_sha256)
        with MorphologyBlobStore(directory,access)as store:
            raw=store.get(root_sha256,maximum=MAX);m=_parse(raw,MAX)
            inputs,p,c,seed,active,pc,ps,checkpoints,raws=_graph(store,m)
            if index is None:result=deepcopy(m)
            else:
                _need(type(index)is int and 0<=index<len(checkpoints),'INDEX_HOLD: stored removal frame required')
                cp=checkpoints[index];sample=cp['last_confirmed'];y=sample['state'];d=m['samples'][index];after=index>inputs['event_step_index']
                program=active if after else p;layout=pc['state_layout']if after else c['state_layout'];n=len(program['leaves'])
                original_indices=pc['original_leaf_indices']if after else list(range(n))
                result={**ROOT_CONSTANTS,'schema_version':'growing-geometry-removal-replay-frame-v1','artifact_sha256':root_sha256,
                    'input_id':m['input_id'],'input_sha256':m['sources']['inputs']['sha256'],'parent_context_sha256':m['parent_context_sha256'],
                    'post_context_sha256':m['post_context_sha256'],'point_calculation_sha256':m['point_calculation_sha256'],
                    **{k:d[k]for k in ('index','global_step_index','phase','checkpoint_sha256','sample_sha256','state_sha256')},
                    'at':{'time_origin_utc':m['time_origin_utc'],'elapsed_seconds_exact':d['elapsed_seconds_exact']},
                    'elapsed_seconds':sample['elapsed_seconds'],'leaf_ids':layout['leaf_ids'],'state_layout':layout,
                    'leaves':[{'leaf_id':leaf['leaf_id'],'thermal_age':{'value':y[108+j],'unit':'degC_day'},
                        'area':{'value':y[108+n+j],'unit':'m2'},'curve_sha256':_digest(leaf['curve']),
                        'initial_area_receipt':seed['initial_area_receipts'][original_indices[j]]}for j,leaf in enumerate(program['leaves'])],
                    'sample':sample,'source_rights':inputs['rights'],
                    'plant':{k:{'value':y[j],'unit':unit}for j,(k,unit)in enumerate(base.PLANT_UNITS.items())},
                    'cohorts':{k:[{'value':v,'unit':unit}for v in y[5+j*50:55+j*50]]for j,(k,unit)in enumerate(base.COHORT_UNITS.items())},
                    'climate':{k:{'value':y[105+j],'unit':unit}for j,(k,unit)in enumerate(base.CLIMATE_UNITS.items())},
                    'original_curve_invariant':seed['evaluation']['curve_residuals'],
                    'active_original_curve_invariant':ps['active_original_curve_invariant']if after else seed['evaluation']['curve_residuals'],
                    'removed_last_states':ps['removed_last_states']if after else None,
                    'original_interval_transfers':cp['original_interval_transfers']if after else cp['integrated_transfers'],
                    'point_outflows':cp['point_outflows']if after else None,
                    'segment_integrated_transfers':cp['segment_integrated_transfers']if after else None,
                    'segment_balance_residuals':cp['balance_residuals']if after else None,
                    'segment_balance_budgets':cp['balance_budgets']if after else None,
                    'global_balance_residuals':cp['global_balance_residuals']if after else cp['balance_residuals'],
                    'global_balance_budgets':cp['global_balance_budgets']if after else cp['balance_budgets']}
                result=deepcopy(result);_need(len(_canonical(result))<=MAX,'CAPACITY_HOLD: bounded frame DTO required')
            raws['root']=raw;_fence(store,m,raws);return result
    except(MorphologyArtifactHold,OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError)as error:
        if isinstance(error,MorphologyArtifactHold):raise RemovalArtifactHold(str(error))from None
        raise RemovalArtifactHold('FORMAT_HOLD: invalid stored removal graph')from None


def read_removal_manifest(directory,access,root_sha256):return _read(directory,access,root_sha256,None)


def read_removal_frame(directory,access,root_sha256,*,index):
    _need(type(index)is int,'INDEX_HOLD: integer frame index required');return _read(directory,access,root_sha256,index)
