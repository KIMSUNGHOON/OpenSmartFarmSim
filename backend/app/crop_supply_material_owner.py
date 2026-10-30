"""Local material lineage with immutable current/history and original-grid resume."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import json
import time

from . import crop_supply_material_proof as proof
from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyBlobStore

point,forcing,base,kernel=proof.point,proof.forcing,proof.base,proof.kernel
q,x,need,raw,digest=base.q,base.x,base._need,base._raw,base._hash
get,put=base._get,base._put
FLAGS=base.FLAGS
VERSION='supply-material-owner-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
PROOF_SHA256=proof.CODE_SHA256
_TOKEN=object()


@dataclass(frozen=True)
class CursorRef:
    sha256:str


@dataclass(frozen=True)
class Workspace:
    forcing_workspace:forcing.Workspace
    archive_directory:Path
    access:ContentAccess


@dataclass(frozen=True)
class Handle:
    cursor_sha256:str
    _current:bytes=field(repr=False)
    _basis:bytes=field(repr=False)
    _cursor:bytes=field(repr=False)
    _definition:str=field(repr=False)
    _workspace:Workspace=field(repr=False)
    _token:object=field(repr=False)

    @property
    def current(self):return json.loads(self._current)

    @property
    def basis(self):return json.loads(self._basis)


@dataclass(frozen=True)
class Outcome:
    status:str
    handle:Handle|None
    hold:str|None
    progress:dict
    emitted:list
    pending:dict|None=None
    historical_cursor_sha256:str|None=None
    authority_hold:str|None=None


def _code():
    point._code()
    need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
         and sha256(Path(proof.__file__).read_bytes()).hexdigest()==PROOF_SHA256,
         'CODE_HOLD: unchanged material owner/proof required')


def _workspace(ws):
    need(type(ws)is Workspace and type(ws.forcing_workspace)is forcing.Workspace and type(ws.access)is ContentAccess,
         'STORAGE_HOLD: explicit material workspace required')
    old=ws.forcing_workspace;root=old.source_workspace
    need(Path(ws.archive_directory).resolve()not in {Path(old.archive_directory).resolve(),Path(root.archive_directory).resolve(),Path(root.source_directory).resolve()},
         'STORAGE_HOLD: separate material archive required')


def _derive(parent,current,source,value,definition_ref):
    basis=deepcopy(parent.math_basis);seed=basis['seed'];event=value['source_event'];before=value['before_dense']
    for target,key in [('program','after_program'),('organs','after_organs'),('costs','after_costs'),('state_layout','after_state_layout'),
        ('birth_bases','after_birth_baselines'),('geometry_baselines','after_geometry_baselines'),('global_ledgers','post_point_global_ledgers_preview'),
        ('lifetime_transfers_exact','post_point_lifetime_transfers_exact_preview'),('point_totals_exact','post_point_point_totals_exact_preview')]:seed[target]=deepcopy(value[key])
    seed['initial_sample']={k:deepcopy(value[v])for k,v in [('at','at'),('state','after_state'),('derived','after_derived')]}
    schedule=deepcopy(current['numeric']['schedule']);spacing=x(source['timeline']['phyllochron_exact'],'degC_day')
    schedule.update(consumed_event_id=event['source_event_id'],consumed_sequence=event['sequence'],consumed_threshold_exact=deepcopy(event['threshold_exact']),
        next_sequence=event['sequence']+1,next_threshold_exact=q(x(event['threshold_exact'],'degC_day')+spacing,'degC_day'),
        age_exact=deepcopy(before['shoot_age_exact']),policy='material_owner_event_once_no_threshold_snap')
    seed['schedule']=schedule;seed['event_sequence']=current['numeric']['event_sequence']+1
    records={kind:{'schema_version':'supply-material-'+kind+'-origins-v1','previous_origin_sha256':current['numeric']['transfer_origins'][kind],
        'point_sha256':digest(value),'baselines':deepcopy(seed['birth_bases'if kind=='physical'else'geometry_baselines'])}for kind in ['physical','geometry']}
    seed['transfer_origins']={k:digest(v)for k,v in records.items()}
    seed['output_cursor']=current['output_cursor']+2
    seed['output_prefix_sha256']=digest({'source':current['output_prefix_sha256'],'point_sha256':digest(value),
        'before_sha256':digest(before),'after_sha256':digest(seed['initial_sample']),'definition_sha256':definition_ref,'model_version':VERSION})
    at=x(value['at']['elapsed_seconds_exact'],'s');grid=Fraction(seed['original_numerical']['step_seconds'])
    seed['original_grid_position']={'completed_grid_index':int(at//grid),'at_original_grid':at%grid==0,
        'next_grid_index':int(at//grid)+1,'next_grid_elapsed_seconds_exact':q((at//grid+1)*grid,'s'),
        'remaining_to_next_grid_seconds_exact':q((at//grid+1)*grid-at,'s')}
    basis['schema_version']='supply-material-numeric-basis-v1'
    return basis,records


@contextmanager
def _session(definition_ref,workspace):
    _code();_workspace(workspace)
    with MorphologyBlobStore(workspace.archive_directory,workspace.access,write=True)as store:
        s=SimpleNamespace(archive=store,archive_witnesses={},workspace=workspace,definition_ref=definition_ref)
        s.definition=get(s,definition_ref);d=s.definition
        base.reader._closed(d,{'schema_version',*FLAGS,'code_sha256','proof_code_sha256','source','pending_page_sha256',
            'time_tolerance_seconds_exact','inputs','expected_point_sha256','point_sha256'})
        need(d['schema_version']=='supply-material-definition-v1'and d['code_sha256']==CODE_SHA256 and d['proof_code_sha256']==PROOF_SHA256
             and all(d[k]==v for k,v in FLAGS.items()),'SCOPE_HOLD: exact material definition required')
        base.reader._closed(d['source'],{'definition_sha256','cursor_sha256'})
        with forcing._session(d['source']['definition_sha256'],workspace.forcing_workspace)as parent:
            _,current=forcing._restore(parent,d['source']['cursor_sha256'])
            source=point._source(parent,current);value=get(s,d['point_sha256'])
            need(d['inputs']['cursor_sha256']==d['source']['cursor_sha256'],'SOURCE_HOLD: actual forcing cursor required')
            proof.verify(parent,current,source,d,value)
            basis,records=_derive(parent,current,source,value,definition_ref)
            s.parent=parent;s.source_current=current;s.point=value;s.math_basis=basis;s.origins=records;s.profiles=parent.profiles
            s.basis={'schema_version':'supply-material-owner-basis-v1','source':deepcopy(d['source']),
                'source_current_sha256':digest(current),'point_sha256':d['point_sha256'],'numeric_basis':basis,'origin_records':records}
            s.spans=parent.spans;s.grid=Fraction(basis['seed']['original_numerical']['step_seconds']);s.stop=parent.stop
            s.rights=deepcopy(value['effective_rights']);s.basis_raw=raw(s.basis);yield s


def _check(s):
    _code();forcing._check(s.parent)
    need(digest(s.definition)==s.definition_ref and s.math_basis==s.basis['numeric_basis']
         and digest(s.point)==s.definition['point_sha256']and digest(s.source_current)==s.basis['source_current_sha256']
         and raw(s.basis)==s.basis_raw,
         'SOURCE_HOLD: unchanged admitted material source required')
    for key in list(s.archive_witnesses):get(s,key)
    s.archive._guard();s.archive._usage()


def _numeric(s,state,totals,derived,steps,at,index):
    m=proof.math_view(s.math_basis,s.spans[index],s.profiles)
    local,global_books,diagnostics,lifetime=kernel._books(m,state,totals,derived,steps,at)
    if steps==0:
        need(at==x(s.point['at']['elapsed_seconds_exact'],'s')and all(x(v['residual_exact'],v['residual_exact']['unit'])==0 for v in local.values()),
             'BALANCE_HOLD: exact zero-duration post-point branch required')
        local={k:{'residual_exact':deepcopy(v['residual_exact']),'budget_exact':q(0,v['budget_exact']['unit'])}for k,v in local.items()}
        for k,v in global_books.items():need(v['residual_exact']==s.math_basis['seed']['global_ledgers'][k]['residual_exact'],'BALANCE_HOLD: zero branch must preserve global residual')
        global_books=deepcopy(s.math_basis['seed']['global_ledgers'])
    seed=s.math_basis['seed'];position=int(at//s.grid)
    return {**FLAGS,'schema_version':'supply-material-numeric-v1','code_sha256':CODE_SHA256,
        'at':{'time_origin_utc':seed['initial_sample']['at']['time_origin_utc'],'elapsed_seconds_exact':q(at,'s')},
        'branch_steps':steps,'grid_index':position,'grid_remainder_exact':q(at-position*s.grid,'s'),
        'next_grid_endpoint_exact':q((position+1)*s.grid,'s'),'active_input_sha256':digest({k:s.spans[index][k]for k in ['forcing','fruit_entry']}),
        'phase':'material_after'if steps==0 else'original_grid_endpoint'if at%s.grid==0 else'forcing_interval_endpoint',
        'schedule':base._clock(m,totals,at),'event_sequence':seed['event_sequence'],
        'last_confirmed':{'at':deepcopy(seed['initial_sample']['at'])if steps==0 else{'time_origin_utc':seed['initial_sample']['at']['time_origin_utc'],'elapsed_seconds_exact':q(at,'s')},'state':list(state),'derived':deepcopy(derived)},
        'branch_integrated_transfers':{k:{'value':v,'unit':unit}for(k,unit),v in zip(m.units.items(),totals,strict=True)},
        'lifetime_transfers_exact':{k:q(v,m.units[k])for k,v in lifetime.items()},'point_totals_exact':deepcopy(seed['point_totals_exact']),
        'branch_ledgers':local,'global_ledgers':global_books,'geometry_diagnostics':diagnostics,'transfer_origins':deepcopy(seed['transfer_origins'])}


def _initial(s):
    seed=s.math_basis['seed'];index=s.source_current['span_index'];m=proof.math_view(s.math_basis,s.spans[index],s.profiles)
    sample=seed['initial_sample'];n=_numeric(s,tuple(sample['state']),(0.,)*len(m.units),sample['derived'],0,x(sample['at']['elapsed_seconds_exact'],'s'),index)
    return {**FLAGS,'schema_version':'supply-material-current-v1','code_sha256':CODE_SHA256,'definition_sha256':s.definition_ref,
        'effective_rights':deepcopy(s.rights),'numeric':n,'at':deepcopy(n['at']),'span_index':index,'phase':'material_after',
        'integration_count':0,'output_cursor':seed['output_cursor'],'output_prefix_sha256':seed['output_prefix_sha256']}


def _cursor(s,current_sha,previous=None,page=None):
    return {**FLAGS,'schema_version':'supply-material-cursor-v1','code_sha256':CODE_SHA256,'definition_sha256':s.definition_ref,
        'basis_sha256':digest(s.basis),'current_sha256':current_sha,'previous_cursor_sha256':previous,'history_page_sha256':page}


def _adoption_page(s,after_sha):
    return {'schema_version':'supply-material-history-page-v1','kind':'material_adoption','source':deepcopy(s.definition['source']),
        'source_current_sha256':digest(s.source_current),'after_current_sha256':after_sha,'point_sha256':s.definition['point_sha256']}


def _handle(s,sha,cursor,current):
    return Handle(sha,raw(current,base.CURRENT_MAX),raw(s.basis),raw(cursor,base.CURRENT_MAX),s.definition_ref,s.workspace,_TOKEN)


def _restore(s,sha):
    selected=selected_current=None;seen=set()
    while True:
        need(sha not in seen and len(seen)<256,'CAPACITY_HOLD: bounded acyclic material history required');seen.add(sha)
        cursor=get(s,sha,base.CURRENT_MAX);current=get(s,cursor['current_sha256'],base.CURRENT_MAX)
        need(cursor==_cursor(s,digest(current),cursor['previous_cursor_sha256'],cursor['history_page_sha256'])
             and get(s,cursor['basis_sha256'])==s.basis,'HISTORY_HOLD: exact material cursor and basis required')
        _shape(s,current)
        if selected is None:selected,selected_current=cursor,current
        if cursor['previous_cursor_sha256']is None:
            need(raw(current)==raw(_initial(s))and get(s,cursor['history_page_sha256'])==_adoption_page(s,digest(current)),
                 'HISTORY_HOLD: complete actual first material adoption required');break
        previous=get(s,cursor['previous_cursor_sha256'],base.CURRENT_MAX);before=get(s,previous['current_sha256'],base.CURRENT_MAX);_shape(s,before)
        page=get(s,cursor['history_page_sha256']);kind=page['kind'];evidence=page['evidence']
        need(page==_page(cursor['previous_cursor_sha256'],previous['current_sha256'],digest(current),kind,evidence),
             'HISTORY_HOLD: exact linked material history page required')
        if kind=='forcing_switch':
            index=forcing._switch_index(s,before)
            need(index is not None and evidence==_switch_evidence(before,index)
                 and current==_switch(s,before,index,current['numeric']['last_confirmed']['derived']),
                 'ORDER_HOLD: exact zero-time forcing switch required')
        else:
            need(kind=='interval','HISTORY_HOLD: known material history operation required')
            _verify_interval(s,before,current,evidence)
        sha=cursor['previous_cursor_sha256']
    for record in s.origins.values():need(get(s,digest(record))==record,'ORIGIN_HOLD: exact new origin record required')
    return selected,selected_current


def open_material(cursor_ref,definition_ref,workspace):
    need(type(cursor_ref)is CursorRef,'CONTEXT_HOLD: actual material cursor reference required')
    with _session(definition_ref,workspace)as s:
        cursor,current=_restore(s,cursor_ref.sha256);_check(s)
        return _handle(s,cursor_ref.sha256,cursor,current)


def adopt_material(handle,pending_page_sha256,time_tolerance_seconds_exact,*,inputs,expected_point_sha256,workspace,cancelled=None,wall_seconds=60):
    started=time.monotonic();progress={'stage':'admission','proposal_RHS_evaluations':0,'records_emitted':0,'bytes_emitted':0}
    try:
        _code();_workspace(workspace)
        need(type(handle)is forcing.Handle and handle._token is forcing._TOKEN and handle._workspace==workspace.forcing_workspace,
             'CONTEXT_HOLD: genuine forcing source in actual workspace required')
        base.reader._hash(expected_point_sha256);snapshot=raw(inputs,point.INPUT_MAX);v=json.loads(snapshot)
        controls=base.AdvanceRequest(q(0,'s'),wall_seconds=wall_seconds,cancelled=cancelled)
        need(type(wall_seconds)is int and 1<=wall_seconds<=60 and(cancelled is None or callable(cancelled)),'BUDGET_HOLD: bounded adoption controls required')
        base._interrupt(controls,progress,started)
        result=point.apply_material_point(handle,pending_page_sha256,time_tolerance_seconds_exact,inputs=v,cancelled=cancelled,
            wall_seconds=forcing._remaining_wall(controls,started))
        progress['proposal_RHS_evaluations']=result['progress'].get('candidate_RHS_evaluations',0)+result['progress'].get('point_RHS_evaluations',0)
        need(result['status']=='point_ready',result.get('hold')or'POINT_HOLD: actual material proposal required')
        need(result['calculation_sha256']==expected_point_sha256,'POINT_HOLD: expected source-bound calculation hash required')
        d={**FLAGS,'schema_version':'supply-material-definition-v1','code_sha256':CODE_SHA256,'proof_code_sha256':PROOF_SHA256,
            'source':{'definition_sha256':handle._definition,'cursor_sha256':handle.cursor_sha256},
            'pending_page_sha256':pending_page_sha256,'time_tolerance_seconds_exact':q(x(time_tolerance_seconds_exact,'s'),'s'),
            'inputs':v,'expected_point_sha256':expected_point_sha256,'point_sha256':digest(result)}
        base._interrupt(controls,progress,started);need(raw(inputs,point.INPUT_MAX)==snapshot,'SOURCE_HOLD: caller material inputs changed')
        with MorphologyBlobStore(workspace.archive_directory,workspace.access,write=True)as store:
            store.put(raw(result),maximum=base.PAGE_MAX);definition=store.put(raw(d),maximum=base.PAGE_MAX)
        with _session(definition,workspace)as s:
            current=_initial(s);current_sha=digest(current);page=_adoption_page(s,current_sha);cursor=_cursor(s,current_sha,None,digest(page))
            progress['stage']='publication';base._interrupt(controls,progress,started);_check(s)
            put(s,s.basis)
            for record in s.origins.values():put(s,record)
            put(s,current,base.CURRENT_MAX);put(s,page);sha=put(s,cursor,base.CURRENT_MAX)
            base._interrupt(controls,progress,started);_check(s);need(raw(inputs,point.INPUT_MAX)==snapshot,'SOURCE_HOLD: caller inputs changed before return')
            progress.update(records_emitted=1,bytes_emitted=sum(len(raw(v))for v in [current,page,cursor]))
            return Outcome('adopted',_handle(s,sha,cursor,current),None,deepcopy(progress),[deepcopy(current)])
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
        return Outcome('hold',None,base._reason(error),deepcopy(progress),[],historical_cursor_sha256=handle.cursor_sha256 if type(handle)is forcing.Handle else None)


def _compose(s,before,numeric,index,phase,integrated):
    count=before['integration_count']+int(integrated)
    return {**deepcopy(before),'numeric':deepcopy(numeric),'at':deepcopy(numeric['at']),'span_index':index,
        'phase':phase,'integration_count':count,'output_cursor':before['output_cursor']+1,
        'output_prefix_sha256':digest({'previous':before['output_prefix_sha256'],'numeric_sha256':digest(numeric),
            'definition_sha256':s.definition_ref,'phase':phase,'span_index':index,'integration_count':count,'model_version':VERSION})}


def _shape(s,current):
    base.reader._closed(current,{'schema_version',*FLAGS,'code_sha256','definition_sha256','effective_rights','numeric','at',
        'span_index','phase','integration_count','output_cursor','output_prefix_sha256'})
    need(current['schema_version']=='supply-material-current-v1'and current['code_sha256']==CODE_SHA256
         and current['definition_sha256']==s.definition_ref and current['effective_rights']==s.rights
         and all(current[k]==v for k,v in FLAGS.items()),'CONTEXT_HOLD: exact material current scope/source/rights required')
    n=current['numeric'];index=current['span_index'];at=x(current['at']['elapsed_seconds_exact'],'s')
    need(type(index)is int and s.source_current['span_index']<=index<len(s.spans)
         and all(type(current[k])is int and current[k]>=0 for k in ['integration_count','output_cursor'])
         and current['integration_count']<=128 and type(n['branch_steps'])is int and n['branch_steps']==current['integration_count'],
         'STATE_HOLD: actual bounded material counters required')
    m=proof.math_view(s.math_basis,s.spans[index],s.profiles);base.reader._closed(n['branch_integrated_transfers'],set(m.units))
    totals=base._vector([n['branch_integrated_transfers'][k]['value']for k in m.units],len(m.units))
    state=base._vector(n['last_confirmed']['state'],len(s.math_basis['seed']['initial_sample']['state']))
    derived=n['last_confirmed']['derived'];base.reader._closed(derived,set(s.math_basis['seed']['initial_sample']['derived']))
    for name,v in derived.items():
        base.reader._closed(v,{'value','unit'});base._vector([v['value']],1)
        need(v['unit']==s.math_basis['seed']['initial_sample']['derived'][name]['unit'],'UNIT_HOLD: actual derived unit required')
    need(current['at']==n['at']and raw(n)==raw(_numeric(s,state,totals,derived,n['branch_steps'],at,index)),
         'STATE_HOLD: exact material numeric/account projection required')
    need(x(s.point['at']['elapsed_seconds_exact'],'s')<=at<=s.stop
         and x(s.spans[index]['start'],'s')<=at<=x(s.spans[index]['end'],'s')
         and x(n['schedule']['age_exact'],'degC_day')<x(n['schedule']['next_threshold_exact'],'degC_day'),
         'TIME_HOLD: covered state before next unconsumed threshold required')
    phase=current['phase'];base.reader._hash(current['output_prefix_sha256'])
    need((phase=='material_after'and current==_initial(s))
         or(phase=='forcing_after'and at==x(s.spans[index]['start'],'s'))
         or(phase=='forcing_before'and index<len(s.spans)-1 and at==x(s.spans[index]['end'],'s'))
         or(phase=='declared_end'and at==s.stop and index==len(s.spans)-1)
         or(phase=='original_grid_endpoint'and at%s.grid==0 and at<x(s.spans[index]['end'],'s')),
         'ORDER_HOLD: actual material/forcing/grid phase required')


def _switch(s,before,index,derived):
    n=before['numeric'];m=proof.math_view(s.math_basis,s.spans[index],s.profiles)
    numeric=_numeric(s,tuple(n['last_confirmed']['state']),tuple(n['branch_integrated_transfers'][k]['value']for k in m.units),
        derived,n['branch_steps'],x(n['at']['elapsed_seconds_exact'],'s'),index)
    for name in ['at','schedule','branch_integrated_transfers','lifetime_transfers_exact','point_totals_exact','branch_ledgers','global_ledgers','transfer_origins','geometry_diagnostics']:
        need(numeric[name]==n[name],'BALANCE_HOLD: forcing switch must preserve '+name)
    return _compose(s,before,numeric,index,'forcing_after',False)


def _switch_evidence(before,index):
    return {'span_index':index,'at':deepcopy(before['at']),'state_sha256':digest(before['numeric']['last_confirmed']['state']),
        'point_transfers_added':False,'producer_code_sha256':CODE_SHA256}


def _verify_interval(s,before,after,trace):
    need(forcing._switch_index(s,before)is None and before['phase']!='declared_end','ORDER_HOLD: active forcing interval required')
    index=before['span_index'];right=forcing._right(s,before);m=proof.math_view(s.math_basis,s.spans[index],s.profiles)
    state,totals,schedule=proof.trace_values(m,before['numeric'],trace,right)
    need(x(schedule['age_exact'],'degC_day')<x(schedule['next_threshold_exact'],'degC_day'),'EVENT_HOLD: cannot skip material threshold')
    numeric=_numeric(s,state,totals,after['numeric']['last_confirmed']['derived'],before['numeric']['branch_steps']+1,right,index)
    need(after==_compose(s,before,numeric,index,forcing._interval_phase(s,index,right),True),
         'CHECKPOINT_HOLD: exact state/accounts/prefix from saved interval required')


def _page(previous,before_sha,after_sha,kind,evidence):
    return {'schema_version':'supply-material-history-page-v1','kind':kind,'previous_cursor_sha256':previous,
        'before_current_sha256':before_sha,'after_current_sha256':after_sha,'evidence':evidence}


def _publish(s,confirmed,cursor,new,kind,evidence,request,progress,started):
    current_sha=digest(new);page=_page(confirmed.cursor_sha256,cursor['current_sha256'],current_sha,kind,evidence)
    proposed=_cursor(s,current_sha,confirmed.cursor_sha256,digest(page));cost=sum(len(raw(v))for v in [new,page,proposed])
    if progress['bytes_emitted']+cost>request.byte_budget:return None
    progress['stage']='publication';base._interrupt(request,progress,started);_check(s)
    put(s,new,base.CURRENT_MAX);put(s,page);sha=put(s,proposed,base.CURRENT_MAX)
    base._interrupt(request,progress,started);_check(s)
    progress['records_emitted']+=1;progress['bytes_emitted']+=cost
    return _handle(s,sha,proposed,new),proposed


def advance(handle,request,*,material=None):
    started=time.monotonic();p={'stage':'admission','steps_attempted':0,'records_emitted':0,'bytes_emitted':0,
        'current_validation_RHS_evaluations':0,'new_RHS_evaluations':0,'forcing_switch_RHS_evaluations':0,'past_intervals_reintegrated':0}
    confirmed=None;emitted=[]
    try:
        need(type(handle)is Handle and handle._token is _TOKEN,'CONTEXT_HOLD: genuine material owner required')
        with _session(handle._definition,handle._workspace)as s:
            cursor,current=_restore(s,handle.cursor_sha256)
            need(raw(cursor,base.CURRENT_MAX)==handle._cursor and raw(current,base.CURRENT_MAX)==handle._current
                 and raw(s.basis)==handle._basis,'CONTEXT_HOLD: unchanged material handle bytes required');confirmed=handle
            try:
                need(material is None,'MATERIAL_HOLD: a consumed source event cannot be applied again')
                stop=forcing._request(s,current,request);status='yielded';pending=None
                while True:
                    base._interrupt(request,p,started);_check(s)
                    if p['records_emitted']>=request.record_budget:break
                    index=forcing._switch_index(s,current);used=p['current_validation_RHS_evaluations']+p['new_RHS_evaluations']
                    if index is not None:
                        if used+1>request.rhs_budget:break
                        m=proof.math_view(s.math_basis,s.spans[index],s.profiles)
                        rhs=base._rhs(m,tuple(current['numeric']['last_confirmed']['state']),request,p,started,'current_validation')
                        p['forcing_switch_RHS_evaluations']+=1
                        new=_switch(s,current,index,rhs['derived']);kind='forcing_switch';evidence=_switch_evidence(current,index)
                    else:
                        at=x(current['at']['elapsed_seconds_exact'],'s')
                        if at>=stop or p['steps_attempted']>=request.step_budget or used+5>request.rhs_budget:break
                        index=current['span_index'];right=forcing._right(s,current);need(right<=stop,'TIME_HOLD: cannot split canonical remainder')
                        m=proof.math_view(s.math_basis,s.spans[index],s.profiles);m.dt=right-at;n=current['numeric']
                        p['steps_attempted']+=1
                        first=base._rhs(m,tuple(n['last_confirmed']['state']),request,p,started,'current_validation')
                        need(first['derived']==n['last_confirmed']['derived'],'STATE_HOLD: unchanged-input actual current RHS required')
                        state,totals,rhs,trace,schedule=base._step(m,n,first,request,p,started)
                        if x(schedule['age_exact'],'degC_day')>=x(schedule['next_threshold_exact'],'degC_day'):
                            page={'schema_version':'supply-material-pending-page-v1','definition_sha256':s.definition_ref,
                                'previous_cursor_sha256':confirmed.cursor_sha256,'interval':trace,'schedule':schedule,'material_consumed':False}
                            cost=len(raw(page))
                            if p['bytes_emitted']+cost>request.byte_budget:break
                            base._interrupt(request,p,started);_check(s);sha=put(s,page);base._interrupt(request,p,started);_check(s)
                            pending={'page_sha256':sha,'material_consumed':False,'reason':'EVENT_HOLD: next material needs a separate admitted point'}
                            p['records_emitted']+=1;p['bytes_emitted']+=cost;status='awaiting_material';break
                        numeric=_numeric(s,state,totals,rhs['derived'],n['branch_steps']+1,right,index)
                        new=_compose(s,current,numeric,index,forcing._interval_phase(s,index,right),True);kind='interval';evidence=trace
                    published=_publish(s,confirmed,cursor,new,kind,evidence,request,p,started)
                    if published is None:break
                    confirmed,cursor=published;current=new
                    emitted.append({'cursor_sha256':confirmed.cursor_sha256,'current_sha256':cursor['current_sha256'],
                        'at':deepcopy(new['at']),'phase':new['phase'],'span_index':new['span_index']})
                base._interrupt(request,p,started);_check(s)
                if current['phase']=='declared_end':status='completed'
                p['requested_stop_reached']=x(current['at']['elapsed_seconds_exact'],'s')==stop and forcing._switch_index(s,current)is None
                return Outcome(status,confirmed,None,deepcopy(p),emitted,pending)
            except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
                authority=None
                try:_check(s)
                except(OSError,ValueError,TypeError,KeyError)as late:authority=base._reason(late);confirmed=None;emitted=[]
                return Outcome('hold',confirmed,base._reason(error),deepcopy(p),emitted,historical_cursor_sha256=handle.cursor_sha256,authority_hold=authority)
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
        return Outcome('hold',None,base._reason(error),deepcopy(p),[],historical_cursor_sha256=handle.cursor_sha256 if type(handle)is Handle else None)
