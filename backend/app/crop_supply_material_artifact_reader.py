"""Project a selected stored material window without importing crop equations."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from math import isfinite
import json

from . import crop_supply_morphology_artifact_reader as legacy
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need

MAX=legacy.MAX
q,x=legacy.projection.q,legacy.projection.x
raw=legacy._canonical
digest=legacy._digest
FLAGS={**legacy.FLAGS,'schema_version':'supply-material-research-artifact-v1','claim_scope':'stored_synthetic_material_window_only'}
NUMERIC_FLAGS={k:FLAGS[k]for k in ['scope','G0_G4','R2']}
SOURCE_PATHS=(*legacy.SOURCE_PATHS,*('backend/app/'+n+'.py'for n in [
    'crop_supply_season','crop_supply_forcing_interval','crop_supply_forcing_owner','crop_supply_forcing_threshold',
    'crop_supply_forcing_threshold_state','crop_supply_threshold_state_books','crop_supply_material_point',
    'crop_supply_material_proof','crop_supply_material_owner','crop_supply_material_artifact_reader','crop_supply_material_artifact_producer']),
    'research/export-leaf-funded-birth-replay.py','research/export-material-replay.py')
LOADED={name:sha256(Path(__file__).with_name(name+'.py').read_bytes()).hexdigest()for name in ['crop_supply_material_artifact_reader']}
ROOT_FIELDS={*FLAGS,'code_sha256','source','blob_groups','before_geometry_diagnostics','effective_rights','window','terminal','frames','notice'}


def _pins():
    r=Path(__file__).resolve().parents[2]
    pins={n:sha256((r/n).read_bytes()).hexdigest()for n in SOURCE_PATHS}
    _need(all(pins['backend/app/'+n+'.py']==v for n,v in LOADED.items()),'CODE_HOLD: original loaded material reader required')
    return pins


def _rights(value):
    legacy._closed(value,{'use','display','redistribute'})
    _need(all(type(v)is bool for v in value.values())and value['use'],'RIGHTS_HOLD: explicit current use required')
    return value


def _fence(store,manifest,raws):
    _need(_pins()==manifest['code_sha256'],'CODE_HOLD: unchanged material artifact sources required')
    store._guard();store._usage()
    for h,(b,meta)in raws.items():legacy._read(store,h,raws,maximum=max(MAX,len(b)))



def _vector(value,size):
    _need(type(value)is list and len(value)==size and all(type(v)is float and isfinite(v)for v in value),
        'STATE_HOLD: complete finite binary64 stored vector required')
    return tuple(value)


def _combine(before,rows,weights,dt):
    result=[]
    for i,start in enumerate(before):
        delta=dt*sum((w*Fraction(row[i])for w,row in zip(weights,rows,strict=True)),Fraction(0))
        exact=Fraction(start)+delta;value=float(exact)
        _need(isfinite(value)and(exact==0 or value!=0)and(delta==0 or value!=start),
            'NUMERIC_HOLD: finite represented stored change required')
        result.append(value)
    return result


def _stored_step(before,after,page,kind,basis):
    a=before if kind=='base'else before['numeric'];b=after if kind=='base'else after['numeric']
    if page['kind']=='forcing_switch':
        for name in ['at','last_confirmed','branch_steps','schedule','event_sequence','branch_integrated_transfers',
            'lifetime_transfers_exact','point_totals_exact','branch_ledgers','global_ledgers','transfer_origins']:
            if name=='last_confirmed':
                _need(raw(a[name]['state'])==raw(b[name]['state']),'STATE_HOLD: forcing switch must preserve stocks')
            else:_need(raw(a[name])==raw(b[name]),'STATE_HOLD: zero-time forcing must preserve '+name)
        return
    _need(page['kind']==('step'if kind=='base'else'interval'),'HISTORY_HOLD: actual stored interval operation required')
    trace=page['interval']if kind=='base'else page['evidence']['interval']if kind=='forcing'else page['evidence']
    left=x(a['at']['elapsed_seconds_exact'],'s');right=x(b['at']['elapsed_seconds_exact'],'s');dt=right-left
    _need(dt>0 and trace['left_elapsed_seconds_exact']==q(left,'s')and trace['right_elapsed_seconds_exact']==q(right,'s')
        and trace['step_seconds_exact']==q(dt,'s'),'TIME_HOLD: exact stored interval time required')
    y=_vector(a['last_confirmed']['state'],len(a['last_confirmed']['state']));rows=trace['stages']
    _need(type(rows)is list and len(rows)==4,'TRACE_HOLD: four original stages required')
    order=trace['flux_order'];names=[v['name']for v in order]
    _need(len(set(names))==len(names)and set(names)==set(a['branch_integrated_transfers'])==set(b['branch_integrated_transfers']),
        'TRACE_HOLD: exact original flux inventory required')
    rates=[];flows=[];previous=None
    for label,offset,row in zip(['k1','k2','k3','k4'],[Fraction(0),dt/2,dt/2,dt],rows,strict=True):
        expected=list(y)if previous is None else _combine(y,[previous],[Fraction(1)],offset)
        _need(row['stage']==label and row['at_elapsed_seconds_exact']==q(left+offset,'s')and raw(row['state'])==raw(expected),
            'TRACE_HOLD: exact stored stage order/time/state required')
        previous=_vector(row['rates'],len(y));rates.append(previous);flows.append(_vector(row['flux'],len(order)))
    weights=[Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6)]
    end=_combine(y,rates,weights,dt)
    _need(raw(end)==raw(b['last_confirmed']['state'])==raw(trace['endpoint']['state']),
        'TRACE_HOLD: confirmed state must equal stored RK4 endpoint')
    initial=_vector([a['branch_integrated_transfers'][k]['value']for k in names],len(names))
    final=_combine(initial,flows,weights,dt)
    for name,unit,value,start in zip(names,[v['unit']for v in order],final,initial,strict=True):
        _need(raw(b['branch_integrated_transfers'][name])==raw({'value':value,'unit':unit})
            and x(b['lifetime_transfers_exact'][name],unit)==x(a['lifetime_transfers_exact'][name],unit)+Fraction(value)-Fraction(start),
            'BALANCE_HOLD: exact stored accumulator and lifetime increment required')
    numeric_basis=basis if kind=='base'else basis['arithmetic_basis']if kind=='forcing'else basis['numeric_basis']
    air=Fraction(b['branch_integrated_transfers']['indoor_air_temperature_time']['value'])-Fraction(a['branch_integrated_transfers']['indoor_air_temperature_time']['value'])
    schedule=deepcopy(a['schedule']);schedule['age_exact']=q(x(schedule['age_exact'],'degC_day')+(air-Fraction(numeric_basis['shoot_base_temperature'])*dt)/86400,'degC_day')
    _need(raw(schedule)==raw(b['schedule'])and type(b['branch_steps'])is int and b['branch_steps']==a['branch_steps']+1
        and raw(a['point_totals_exact'])==raw(b['point_totals_exact'])and a['transfer_origins']==b['transfer_origins'],
        'CLOCK_HOLD: exact stored clock and unchanged material origins required')


def _material_phase(current,seed,forcing_definition):
    n=current['numeric'];at=x(current['at']['elapsed_seconds_exact'],'s');grid=Fraction(seed['original_numerical']['step_seconds'])
    index=current['span_index'];spans=forcing_definition['spans']
    _need(type(index)is int and 0<=index<len(spans),'FORCING_HOLD: actual active span required')
    span=spans[index]['span'];begin=x(span['start'],'s');end=x(span['end'],'s');stop=x(forcing_definition['stop_at'],'s')
    phase=current['phase'];initial_at=x(seed['initial_sample']['at']['elapsed_seconds_exact'],'s')
    _need(begin<=at<=end and ((phase=='material_after'and at==initial_at)
        or(phase=='forcing_after'and at==begin)
        or(phase=='forcing_before'and index<len(spans)-1 and at==end)
        or(phase=='declared_end'and index==len(spans)-1 and at==stop)
        or(phase=='original_grid_endpoint'and at%grid==0 and at<end)),
        'ORDER_HOLD: phase must match actual source forcing/grid boundary')
    _need(type(n['branch_steps'])is int and n['branch_steps']>=0 and type(n['grid_index'])is int and n['grid_index']==at//grid
        and n['grid_remainder_exact']==q(at-(at//grid)*grid,'s')and n['next_grid_endpoint_exact']==q((at//grid+1)*grid,'s')
        and n['active_input_sha256']==digest({k:span[k]for k in ['forcing','fruit_entry']}),
        'TIME_HOLD: original grid and active forcing required')
    legacy._closed(n['branch_ledgers'],set(seed['global_ledgers']));legacy._closed(n['global_ledgers'],set(seed['global_ledgers']))
    for name,row in n['global_ledgers'].items():
        unit=row['residual_exact']['unit'];old=seed['global_ledgers'][name];local=n['branch_ledgers'][name]
        _need(x(row['residual_exact'],unit)==x(old['residual_exact'],unit)+x(local['residual_exact'],unit)
            and x(row['budget_exact'],unit)==x(old['budget_exact'],unit)+x(local['budget_exact'],unit),
            'BALANCE_HOLD: original global plus exact branch residual/budget required')


def _walk(obj,kind,reference,definition_sha,code):
    chain=[];seen=set();basis_sha=None
    while True:
        legacy._hash(reference);_need(reference not in seen and len(seen)<256,'CAPACITY_HOLD: bounded acyclic stored lineage required');seen.add(reference)
        c=obj(reference,kind);legacy._closed(c,{'schema_version',*NUMERIC_FLAGS,'code_sha256','definition_sha256','basis_sha256','current_sha256','previous_cursor_sha256','history_page_sha256'})
        schema={'base':'supply-season','forcing':'supply-forcing-owner','material':'supply-material'}[kind]
        _need(c['schema_version']==schema+'-cursor-v1'and c['definition_sha256']==definition_sha and c['code_sha256']==code
              and all(c[k]==v for k,v in NUMERIC_FLAGS.items()),'CONTEXT_HOLD: actual stored cursor source/version/scope required')
        if basis_sha is None:basis_sha=c['basis_sha256']
        _need(c['basis_sha256']==basis_sha,'SOURCE_HOLD: one immutable selected basis required')
        basis=obj(c['basis_sha256'],kind);current=obj(c['current_sha256'],kind)
        _need(current['schema_version']=={'base':'supply-season-current-v1','forcing':'supply-forcing-owner-current-v1','material':'supply-material-current-v1'}[kind]
            and all(current[k]==v for k,v in NUMERIC_FLAGS.items()),'SCOPE_HOLD: original current schema and claims required')
        if kind!='base':
            _need(current['definition_sha256']==definition_sha and current['code_sha256']==code,'CODE_HOLD: actual current family code required')
        previous=c['previous_cursor_sha256'];page=None
        if c['history_page_sha256']is not None:page=obj(c['history_page_sha256'],kind)
        if previous is not None:
            parent=obj(previous,kind)
            _need(page is not None and page['previous_cursor_sha256']==previous and page['before_current_sha256']==parent['current_sha256']
                and page['after_current_sha256']==c['current_sha256'],'HISTORY_HOLD: exact current/page/previous references required')
            _stored_step(obj(parent['current_sha256'],kind),current,page,kind,basis)
        elif kind=='material':
            _need(page is not None and page['kind']=='material_adoption'and page['after_current_sha256']==c['current_sha256'],
                  'HISTORY_HOLD: actual first adoption page required')
        else:_need(page is None,'HISTORY_HOLD: actual first source cursor required')
        chain.append((reference,c,current,page))
        if previous is None:break
        reference=previous
    return list(reversed(chain)),basis


def _graph(manifest,obj,original):
    source=manifest['source'];legacy._closed(source,{'original_root','source_frame_index','base','forcing','material'})
    for kind in ['base','forcing','material']:legacy._closed(source[kind],{'definition_sha256','cursor_sha256'})
    index=source['source_frame_index'];_need(type(index)is int and 0<=index<len(original['frames']),'INDEX_HOLD: actual original source frame required')
    definitions={k:obj(source[k]['definition_sha256'],k)for k in ['base','forcing','material']}
    codes={k:manifest['code_sha256']['backend/app/'+n+'.py']for k,n in [('base','crop_supply_season'),('forcing','crop_supply_forcing_owner'),('material','crop_supply_material_owner')]}
    chains={};bases={}
    for kind in ['base','forcing','material']:
        d=definitions[kind]
        _need(d['code_sha256']==codes[kind]and all(d[k]==v for k,v in NUMERIC_FLAGS.items()),'CODE_HOLD: current definition code/scope required')
        chains[kind],bases[kind]=_walk(obj,kind,source[kind]['cursor_sha256'],source[kind]['definition_sha256'],codes[kind])
    bd,fd,md=[definitions[k]for k in ['base','forcing','material']]
    _need(bd['source']=={'artifact_sha256':source['original_root']['sha256'],'frame_index':index}
        and fd['source']==source['base']and md['source']==source['forcing'],'SOURCE_HOLD: original selected source lineage required')
    _need(bd['schema_version']=='supply-season-definition-v1'and fd['schema_version']=='supply-forcing-definition-v1'
        and md['schema_version']=='supply-material-definition-v1','SCOPE_HOLD: exact component definitions required')
    original_context=obj(original['frames'][index]['context_sha256'],'original')
    _need(raw(bases['base']['seed'])==raw(original_context['descriptor']['seed'])
        and bases['base']['source_checkpoint_sha256']==original['frames'][index]['checkpoint_sha256'],
        'SOURCE_HOLD: unchanged original selected basis required')
    base_current=chains['base'][-1][2];force_current=chains['forcing'][-1][2]
    _need(bases['forcing']['source']==source['base']and bases['forcing']['source_current_sha256']==digest(base_current)
        and raw(bases['forcing']['arithmetic_basis'])==raw(bases['base']), 'SOURCE_HOLD: actual forcing source basis required')
    pending=obj(md['pending_page_sha256'],'forcing');point=obj(md['point_sha256'],'material')
    _need(pending['previous_cursor_sha256']==source['forcing']['cursor_sha256']and pending['definition_sha256']==source['forcing']['definition_sha256']
        and pending['result']['status']=='awaiting_material'and pending['result']['current']is None,
        'SOURCE_HOLD: actual pending source interval required')
    _need(point['code_sha256']==manifest['code_sha256']['backend/app/crop_supply_material_point.py']
        and md['proof_code_sha256']==manifest['code_sha256']['backend/app/crop_supply_material_proof.py']
        and point['status']=='point_ready'and point['calculation_sha256']==md['expected_point_sha256']
        and point['calculation_sha256']==digest({k:v for k,v in point.items()if k!='calculation_sha256'})
        and raw(point['inputs'])==raw(md['inputs'])and point['source_current_sha256']==digest(force_current)
        and point['cursor_sha256']==source['forcing']['cursor_sha256']and point['definition_sha256']==source['forcing']['definition_sha256']
        and point['pending_page_sha256']==md['pending_page_sha256']and point['at']==point['before_dense']['at'],
        'POINT_HOLD: original source-bound calculated point required')
    grants=[_rights(bd['rights']),_rights(fd['rights']),_rights(md['inputs']['rights'])]
    _need(type(fd['spans'])is list and 1<=len(fd['spans'])<=128,'CAPACITY_HOLD: bounded original forcing plan required')
    grants.extend(_rights(v['rights'])for v in fd['spans'])
    grants.append({'use':True,'display':True,'redistribute':original['redistribution_authorized']})
    rights={k:all(v[k]for v in grants)for k in ['use','display','redistribute']}
    _need(rights==point['effective_rights']==manifest['effective_rights'],'RIGHTS_HOLD: exact source/plan/material grants AND required')
    material_basis=bases['material'];seed=material_basis['numeric_basis']['seed']
    _need(material_basis['source']==source['forcing']and material_basis['point_sha256']==md['point_sha256']
        and material_basis['source_current_sha256']==digest(force_current),'SOURCE_HOLD: actual material basis origin required')
    mapping={'program':'after_program','organs':'after_organs','costs':'after_costs','state_layout':'after_state_layout',
        'birth_bases':'after_birth_baselines','geometry_baselines':'after_geometry_baselines','global_ledgers':'post_point_global_ledgers_preview',
        'lifetime_transfers_exact':'post_point_lifetime_transfers_exact_preview','point_totals_exact':'post_point_point_totals_exact_preview'}
    _need(all(raw(seed[k])==raw(point[v])for k,v in mapping.items()),'SOURCE_HOLD: exact actual post-point basis fields required')
    for kind,record in material_basis['origin_records'].items():
        _need(kind in ['physical','geometry']and obj(seed['transfer_origins'][kind],'material')==record
            and record['point_sha256']==md['point_sha256']and record['previous_origin_sha256']==force_current['numeric']['transfer_origins'][kind],
            'ORIGIN_HOLD: complete original and new stored origin links required')
    event=point['source_event'];schedule=seed['schedule']
    _need(schedule['consumed_event_id']==event['source_event_id']and type(schedule['consumed_sequence'])is int
        and schedule['consumed_sequence']==event['sequence']and schedule['next_sequence']==event['sequence']+1
        and schedule['age_exact']==point['before_dense']['shoot_age_exact']
        and seed['event_sequence']==force_current['numeric']['event_sequence']+1,'EVENT_HOLD: actual once-consumed source event required')
    return chains,bases,point,rights


def _frame(seed,snapshot,lifetime,geometry,accounts,*,index,phase,source_sha,cursor_sha,sequence,schedule,points,origins,state_kind):
    projected=legacy.projection.project(seed,snapshot,lifetime,geometry,accounts)
    return {**FLAGS,'schema_version':'supply-material-replay-frame-v1',**projected,'index':index,'phase':phase,'at':deepcopy(snapshot['at']),
        'source_sha256':source_sha,'source_cursor_sha256':cursor_sha,'event_sequence':sequence,'schedule':deepcopy(schedule),
        'point_totals_exact':deepcopy(points),'lifetime_transfers_exact':deepcopy(lifetime),'transfer_origins':deepcopy(origins),'state_kind':state_kind}


def _frames(manifest,chains,bases,point,forcing_definition):
    before=point['before_dense'];seed=bases['forcing']['arithmetic_basis']['seed'];schedule=deepcopy(point['source_schedule'])
    schedule['age_exact']=deepcopy(before['shoot_age_exact'])
    frames=[_frame(seed,{k:deepcopy(before[k])for k in ['at','state','derived']},before['pending_lifetime_transfers_exact'],
        manifest['before_geometry_diagnostics'],before['pending_global_ledgers'],index=0,phase='material_before',
        source_sha=digest(point),cursor_sha=None,sequence=before['event_sequence'],
        schedule=schedule,points=before['point_totals_exact'],origins=before['transfer_origins'],state_kind='dense_before_from_adopted_point')]
    seed=bases['material']['numeric_basis']['seed'];previous_at=x(before['at']['elapsed_seconds_exact'],'s')
    for i,(sha,c,current,page)in enumerate(chains['material'],1):
        _material_phase(current,seed,forcing_definition)
        n=current['numeric'];at=x(current['at']['elapsed_seconds_exact'],'s')
        _need(current['effective_rights']==manifest['effective_rights']and n['at']==current['at']==n['last_confirmed']['at']
            and current['at']['time_origin_utc']==before['at']['time_origin_utc']and at>=previous_at
            and n['schema_version']=='supply-material-numeric-v1'and n['code_sha256']==current['code_sha256']
            and n['event_sequence']==seed['event_sequence']and n['transfer_origins']==seed['transfer_origins']
            and n['point_totals_exact']==seed['point_totals_exact']and n['schedule']['consumed_event_id']==seed['schedule']['consumed_event_id'],
            'STATE_HOLD: original confirmed material state, origin, schedule and phase order required')
        _need(current['phase']in ['material_after','original_grid_endpoint','forcing_before','forcing_after','declared_end']
            and (i!=1 or current['phase']=='material_after'and n['last_confirmed']==seed['initial_sample']),
            'ORDER_HOLD: actual adopted first state and known phases required')
        frames.append(_frame(seed,n['last_confirmed'],n['lifetime_transfers_exact'],n['geometry_diagnostics'],n['global_ledgers'],
            index=i,phase=current['phase'],source_sha=c['current_sha256'],cursor_sha=sha,sequence=n['event_sequence'],
            schedule=n['schedule'],points=n['point_totals_exact'],origins=n['transfer_origins'],state_kind='confirmed_material_current'))
        previous_at=at
    return frames


def frame_descriptor(frame):
    b=raw(frame)
    return {k:deepcopy(frame[k])for k in ['index','phase','at','source_sha256','source_cursor_sha256','event_sequence']}|{'frame_sha256':sha256(b).hexdigest(),'bytes':len(b),'state_scalars':len(frame['snapshot']['state'])}


def _load(store,root_sha256,*,unpublished_raw=None):
    raws={};b=legacy._read(store,root_sha256,raws)if unpublished_raw is None else unpublished_raw
    _need(sha256(b).hexdigest()==root_sha256 and len(b)<=MAX,'HASH_HOLD: bounded original material root required')
    manifest=legacy._parse(b,MAX);legacy._closed(manifest,ROOT_FIELDS)
    _need(raw(manifest)==b and all(manifest[k]==v for k,v in FLAGS.items())and manifest['code_sha256']==_pins(),
          'CODE_HOLD: exact current material artifact code and scope required')
    groups=manifest['blob_groups'];legacy._closed(groups,{'original','base','forcing','material'});sets={};used={k:set()for k in groups}
    for kind,descriptors in groups.items():
        _need(type(descriptors)is list and 1<=len(descriptors)<=1024,'CAPACITY_HOLD: bounded selected source descriptors required')
        sets[kind]={v['sha256']for v in descriptors};_need(len(sets[kind])==len(descriptors),'SOURCE_HOLD: unique source descriptors required')
        for d in descriptors:legacy._source(store,d,raws,maximum=16*1024**2 if kind=='original'else MAX)
    def obj(sha,kind):
        _need(sha in sets[kind],'SOURCE_HOLD: reference outside actual selected group')
        used[kind].add(sha);value=legacy._parse(raws[sha][0],MAX)
        _need(raw(value)==raws[sha][0],'SOURCE_HOLD: original canonical stored record required');return value
    original,_,old_raws=legacy._load(store,manifest['source']['original_root']['sha256'])
    _need(sets['original']==set(old_raws),'SOURCE_HOLD: exact original source closure required')
    used['original']=set(old_raws)
    _need(manifest['source']['original_root']['bytes']==len(raw(original))and manifest['notice']==original['root_inputs']['license_notice'],
          'SOURCE_HOLD: original root and NOTICE identity required')
    chains,bases,point,rights=_graph(manifest,obj,original)
    _need(all(used[k]==sets[k]for k in groups),'SOURCE_HOLD: no unrelated archive records may enter replay')
    frames=_frames(manifest,chains,bases,point,obj(manifest['source']['forcing']['definition_sha256'],'forcing'))
    _need(raw(manifest['frames'])==raw([frame_descriptor(f)for f in frames]),'FRAME_HOLD: exact source-bound frame identities and quantities required')
    expected_window={'source_event_id':point['source_event']['source_event_id'],'first_at':deepcopy(frames[0]['at']),
        'last_at':deepcopy(frames[-1]['at']),'covers_whole_season':False,'selection':'one_adopted_material_and_confirmed_remainder'}
    last=chains['material'][-1][2]
    expected_terminal={'status':'completed'if last['phase']=='declared_end'else'confirmed_prefix','hold':None,'scope':'declared_synthetic_forcing_plan_only'}
    _need(manifest['window']==expected_window and manifest['terminal']==expected_terminal,'SCOPE_HOLD: exact declared partial window required')
    _fence(store,manifest,raws);return manifest,frames,raws


def _read(directory,access,root_sha256,index):
    try:
        with MorphologyBlobStore(directory,access)as store:
            manifest,frames,raws=_load(store,root_sha256)
            _need(manifest['effective_rights']['display'],'RIGHTS_HOLD: current display permission required')
            if index is None:result=deepcopy(manifest)
            else:
                _need(type(index)is int and 0<=index<len(frames),'INDEX_HOLD: actual frame index required')
                result={**deepcopy(frames[index]),'artifact_sha256':root_sha256}
            _need(len(raw(result))<=MAX,'CAPACITY_HOLD: bounded replay response required');_fence(store,manifest,raws);return result
    except MorphologyArtifactHold:raise
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError,RecursionError):
        raise MorphologyArtifactHold('ARTIFACT_HOLD: invalid or unavailable original material artifact')from None


def read_material_manifest(directory,access,root_sha256):return _read(directory,access,root_sha256,None)


def read_material_frame(directory,access,root_sha256,*,index):return _read(directory,access,root_sha256,index)
