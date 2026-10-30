"""Local research owner for fixed forcing plans and immutable numerical history."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass,field
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import time
from types import SimpleNamespace
import json

from . import crop_supply_season as base
from . import crop_supply_forcing_interval as kernel
from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyBlobStore

VERSION = 'supply-forcing-owner-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FLAGS = base.FLAGS
MAX_INTERVALS = 128
MAX_OPERATIONS = 256
raw,digest,q,x,need = base._raw,base._hash,base.q,base.x,base._need
get,put = base._get,base._put
_TOKEN = object()
CURRENT_FIELDS = {'schema_version',*FLAGS,'code_sha256','definition_sha256','effective_rights','numeric',
                  'at','span_index','phase','integration_count','output_cursor','output_prefix_sha256'}


@dataclass(frozen=True)
class SourceRef:
    definition_sha256: str
    cursor_sha256: str


@dataclass(frozen=True)
class CursorRef:
    sha256: str


@dataclass(frozen=True)
class Workspace:
    source_workspace: base.Workspace
    archive_directory: Path
    access: ContentAccess


@dataclass(frozen=True)
class Handle:
    cursor_sha256: str
    _current: bytes = field(repr=False)
    _basis: bytes = field(repr=False)
    _cursor: bytes = field(repr=False)
    _definition: str = field(repr=False)
    _workspace: Workspace = field(repr=False)
    _token: object = field(repr=False)

    @property
    def current(self):return json.loads(self._current)

    @property
    def basis(self):return json.loads(self._basis)


@dataclass(frozen=True)
class Outcome:
    status: str
    handle: Handle | None
    hold: str | None
    failed_stage: str | None
    pending: dict | None
    progress: dict
    emitted: list
    historical_cursor_sha256: str | None = None
    authority_hold: str | None = None


def _code():
    kernel._code()
    need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256,
         'CODE_HOLD: unchanged forcing owner required')


def _rights(value):
    base.reader._closed(value, {'use','display','redistribute'})
    need(all(type(v) is bool for v in value.values()), 'RIGHTS_HOLD: explicit boolean grants required')
    return value


def _provenance(value, span):
    base.reader._closed(value, {'product_id','source_url','observed_at','published_at','available_at','retrieved_at',
                               'vintage','revision','units','qc','raw_sha256','reviewer'})
    for key in ('product_id','vintage','revision','reviewer'):
        need(type(value[key]) is str and 1 <= len(value[key]) <= 256, 'SOURCE_HOLD: explicit synthetic provenance required')
    need(type(value['source_url']) is str and 1 <= len(value['source_url']) <= 2048
         and value['source_url'].startswith(('https://','http://','urn:')),
         'SOURCE_HOLD: source URL or own synthetic product URI required')
    need(value['observed_at'] is None and value['published_at'] is None
         and value['qc'] == 'software_fixture_only', 'SCOPE_HOLD: no observed/forecast approval from a synthetic span')
    available, retrieved = base.reader._utc(value['available_at']),base.reader._utc(value['retrieved_at'])
    need(available <= retrieved, 'TIME_HOLD: source availability must precede retrieval')
    units = {f'{block}.{name}':v['unit'] for block in ('forcing','fruit_entry') for name,v in span[block].items()}
    need(value['units'] == units and value['raw_sha256'] == digest(span), 'SOURCE_HOLD: exact span units/raw identity required')


def _definition_head(d):
    base.reader._closed(d, {'schema_version',*FLAGS,'source','code_sha256','kernel_code_sha256','partition','stop_at','spans','rights'})
    need(d['schema_version'] == 'supply-forcing-definition-v1' and all(d[k] == v for k,v in FLAGS.items()),
         'SCOPE_HOLD: synthetic forcing definition required')
    need(d['code_sha256'] == CODE_SHA256 and d['kernel_code_sha256'] == kernel.CODE_SHA256,
         'CODE_HOLD: exact owner and kernel versions required')
    need(d['partition'] == 'original_grid_and_declared_forcing_edges_v1', 'TIME_HOLD: fixed declared partition required')
    _rights(d['rights'])


def _plan(s):
    d=s.definition
    records=d['spans']
    need(type(records) is list and 1 <= len(records) <= 128, 'CAPACITY_HOLD: bounded forcing span plan required')
    s.grid=Fraction(s.math_basis['seed']['original_numerical']['step_seconds'])
    begin=x(s.source_current['at']['elapsed_seconds_exact'],'s');end=x(d['stop_at'],'s')
    need(s.grid > 0 and begin < end, 'TIME_HOLD: positive declared horizon required')
    previous=begin;extra=0;grants=[_rights(s.origin.definition['rights']),_rights(d['rights'])]
    for index,record in enumerate(records):
        base.reader._closed(record, {'span','rights','provenance'})
        value=record['span'];kernel._view(s.math_basis,value)
        left,right=x(value['start'],'s'),x(value['end'],'s')
        need(left == previous and left < right <= end, 'COVERAGE_HOLD: contiguous nonoverlapping exact spans required')
        if index < len(records)-1 and right%s.grid != 0:extra+=1
        previous=right;grants.append(_rights(record['rights']));_provenance(record['provenance'],value)
    need(previous == end, 'COVERAGE_HOLD: complete forcing horizon required')
    count=int(end//s.grid-begin//s.grid)+extra+int(end%s.grid != 0)
    need(1 <= count <= MAX_INTERVALS, 'CAPACITY_HOLD: bounded canonical integration plan required')
    s.rights={key:all(grant[key] for grant in grants) for key in ('use','display','redistribute')}
    need(s.rights['use'], 'RIGHTS_HOLD: source and every input must permit use')
    s.spans=[record['span'] for record in records];s.stop=end


@contextmanager
def _session(definition_ref, workspace):
    _code()
    need(type(workspace) is Workspace and type(workspace.source_workspace) is base.Workspace
         and type(workspace.access) is ContentAccess, 'STORAGE_HOLD: trusted source/new archive configuration required')
    old=workspace.source_workspace
    need(Path(workspace.archive_directory).resolve() not in
         (Path(old.source_directory).resolve(),Path(old.archive_directory).resolve()),
         'STORAGE_HOLD: new owner archive must be separate from source stores')
    with MorphologyBlobStore(workspace.archive_directory,workspace.access,write=True) as archive:
        s=SimpleNamespace(archive=archive,archive_witnesses={},definition_ref=definition_ref,workspace=workspace)
        archive._usage();s.definition=get(s,definition_ref)
        _definition_head(s.definition)
        source=s.definition['source'];base.reader._closed(source, {'definition_sha256','cursor_sha256'})
        # The unchanged v1 admission/restore validators run with real source refs,
        # held stores and original numerical definition. No old handle is invented.
        with base._session(source['definition_sha256'],old) as origin:
            _,current=base._restore(origin,source['cursor_sha256'])
            base._check(origin)
            s.origin=origin;s.source_current=current;s.math_basis=origin.basis;s.profiles=origin.profiles
            s.basis={'schema_version':'supply-forcing-owner-basis-v1','source':deepcopy(source),
                     'source_current_sha256':digest(current),'source_rights':deepcopy(origin.definition['rights']),
                     'source_arithmetic_code_sha256':base.CODE_SHA256,'arithmetic_basis':deepcopy(origin.basis)}
            _plan(s)
            yield s


def _check(s):
    _code();base._check(s.origin)
    need(digest(s.definition) == s.definition_ref
         and s.math_basis == s.basis['arithmetic_basis']
         and digest(s.source_current) == s.basis['source_current_sha256'],
         'SOURCE_HOLD: unchanged admitted in-memory source/definition required')
    for key in list(s.archive_witnesses):get(s,key)
    s.archive._guard();s.archive._usage()


def _initial(s):
    n=deepcopy(s.source_current)
    return {**FLAGS,'schema_version':'supply-forcing-owner-current-v1','code_sha256':CODE_SHA256,
            'definition_sha256':s.definition_ref,'effective_rights':deepcopy(s.rights),'numeric':n,'at':deepcopy(n['at']),
            'span_index':-1,'phase':'source_before_forcing','integration_count':0,'output_cursor':n['output_cursor'],
            'output_prefix_sha256':digest({'definition_sha256':s.definition_ref,'source':s.definition['source'],
                                         'source_current_sha256':digest(n),'model_version':VERSION})}


def _cursor(s,current_sha,basis_sha,previous=None,page=None):
    return {**FLAGS,'schema_version':'supply-forcing-owner-cursor-v1','code_sha256':CODE_SHA256,
            'definition_sha256':s.definition_ref,'basis_sha256':basis_sha,'current_sha256':current_sha,
            'previous_cursor_sha256':previous,'history_page_sha256':page}


def _handle(s,sha,cursor,current):
    return Handle(sha,raw(current,base.CURRENT_MAX),raw(s.basis),raw(cursor,base.CURRENT_MAX),s.definition_ref,s.workspace,_TOKEN)


def open_season(source_or_cursor_ref, definition_ref, workspace):
    with _session(definition_ref,workspace) as s:
        if type(source_or_cursor_ref) is SourceRef:
            need(vars(source_or_cursor_ref) == s.definition['source'], 'SOURCE_HOLD: actual selected v1 source required')
            basis_sha=put(s,s.basis);current=_initial(s);current_sha=put(s,current,base.CURRENT_MAX)
            cursor=_cursor(s,current_sha,basis_sha);sha=put(s,cursor,base.CURRENT_MAX)
        else:
            need(type(source_or_cursor_ref) is CursorRef, 'CONTEXT_HOLD: source or owner cursor reference required')
            sha=source_or_cursor_ref.sha256;cursor,current=_restore(s,sha)
        _check(s)
        return _handle(s,sha,cursor,current)


def _math(s,index):
    p=kernel._view(s.math_basis,s.spans[index]);data=kernel._data(s.math_basis,p,s.profiles)
    return SimpleNamespace(data=data,basis=s.math_basis,profiles=s.profiles,units=base.books.flux_units(p,data['organs']))


def _numeric(s,before,state,totals,derived,steps,at,index):
    m=_math(s,index)
    local,global_books,diagnostics,lifetime=kernel._books(m,state,totals,derived,steps,at)
    position=int(at//s.grid)
    result={**FLAGS,'schema_version':'supply-forcing-interval-state-v1','model_version':kernel.VERSION,
            'code_sha256':kernel.CODE_SHA256,
            **{k:deepcopy(before[k]) for k in base.NUMERIC_FIELDS if k not in ('output_cursor','output_prefix_sha256')},
            'at':{'time_origin_utc':before['at']['time_origin_utc'],'elapsed_seconds_exact':q(at,'s')},
            'branch_steps':steps,'grid_index':position,'grid_remainder_exact':q(at-position*s.grid,'s'),
            'next_grid_endpoint_exact':q((position+1)*s.grid,'s'),
            'active_input_sha256':digest({k:s.spans[index][k] for k in ('forcing','fruit_entry')}),
            'phase':'original_grid_endpoint' if at%s.grid == 0 else 'forcing_interval_endpoint',
            'schedule':base._clock(m,totals,at),
            'branch_integrated_transfers':{k:{'value':v,'unit':unit} for (k,unit),v in zip(m.units.items(),totals,strict=True)},
            'lifetime_transfers_exact':{k:q(v,m.units[k]) for k,v in lifetime.items()},
            'branch_ledgers':local,'global_ledgers':global_books,'geometry_diagnostics':diagnostics}
    result['last_confirmed']={'at':deepcopy(result['at']),'state':list(state),'derived':deepcopy(derived)}
    raw(result,base.CURRENT_MAX)
    return result


def _compose(s,before,numeric,index,phase,integrated):
    count=before['integration_count']+int(integrated)
    return {**FLAGS,'schema_version':'supply-forcing-owner-current-v1','code_sha256':CODE_SHA256,
            'definition_sha256':s.definition_ref,'effective_rights':deepcopy(s.rights),'numeric':deepcopy(numeric),
            'at':deepcopy(numeric['at']),'span_index':index,'phase':phase,'integration_count':count,
            'output_cursor':before['output_cursor']+1,
            'output_prefix_sha256':digest({'previous':before['output_prefix_sha256'],'definition_sha256':s.definition_ref,
               'numeric_sha256':digest(numeric),'span_index':index,'phase':phase,'integration_count':count,'model_version':VERSION})}


def _switch(s,before,index,derived):
    n=before['numeric'];m=_math(s,index)
    totals=tuple(n['branch_integrated_transfers'][k]['value'] for k in m.units)
    numeric=_numeric(s,n,tuple(n['last_confirmed']['state']),totals,derived,n['branch_steps'],x(n['at']['elapsed_seconds_exact'],'s'),index)
    for name in ('at','branch_steps','grid_index','event_sequence','schedule','branch_integrated_transfers',
                 'lifetime_transfers_exact','point_totals_exact','branch_ledgers','global_ledgers','transfer_origins','geometry_diagnostics'):
        need(numeric[name] == n[name], 'BALANCE_HOLD: forcing switch cannot change '+name)
    need(numeric['last_confirmed']['state'] == n['last_confirmed']['state'], 'STATE_HOLD: forcing switch must preserve stocks')
    return _compose(s,before,numeric,index,'forcing_after',False)


def _switch_index(s,current):
    if current['phase'] == 'source_before_forcing':return 0
    if current['phase'] == 'forcing_before':return current['span_index']+1
    return None


def _right(s,current):
    at=x(current['at']['elapsed_seconds_exact'],'s');span=s.spans[current['span_index']]
    return min((at//s.grid+1)*s.grid,x(span['end'],'s'),s.stop)


def _interval_phase(s,index,right):
    if right == s.stop:return 'declared_end'
    if right == x(s.spans[index]['end'],'s'):return 'forcing_before'
    return 'original_grid_endpoint'


def _shape(s,current):
    base.reader._closed(current,CURRENT_FIELDS)
    need(current['schema_version'] == 'supply-forcing-owner-current-v1'
         and current['code_sha256'] == CODE_SHA256 and current['definition_sha256'] == s.definition_ref
         and all(current[k] == v for k,v in FLAGS.items()) and current['effective_rights'] == s.rights,
         'CONTEXT_HOLD: exact forcing owner/definition/claims/rights required')
    n=current['numeric'];at=x(current['at']['elapsed_seconds_exact'],'s')
    need(current['at'] == n['at'] and n['last_confirmed']['at'] == n['at']
         and current['at']['time_origin_utc'] == s.source_current['at']['time_origin_utc']
         and x(s.source_current['at']['elapsed_seconds_exact'],'s') <= at <= s.stop,
         'TIME_HOLD: original origin and covered current state required')
    need(type(current['integration_count']) is int and 0 <= current['integration_count'] <= MAX_INTERVALS
         and type(current['output_cursor']) is int and type(current['span_index']) is int,
         'STATE_HOLD: bounded actual counters required')
    base.reader._hash(current['output_prefix_sha256'])
    if current['phase'] == 'source_before_forcing':
        need(current == _initial(s), 'SOURCE_HOLD: genuine unmodified source state required')
        return
    i=current['span_index']
    need(0 <= i < len(s.spans) and n['schema_version'] == 'supply-forcing-interval-state-v1'
         and n['code_sha256'] == kernel.CODE_SHA256 and n['model_version'] == kernel.VERSION
         and 'output_cursor' not in n and 'output_prefix_sha256' not in n,
         'STATE_HOLD: checked interval numeric format required')
    need(n['active_input_sha256'] == digest({k:s.spans[i][k] for k in ('forcing','fruit_entry')})
         and x(s.spans[i]['start'],'s') <= at <= x(s.spans[i]['end'],'s'),
         'FORCING_HOLD: actual current active span required')
    phase=current['phase']
    need((phase == 'forcing_after' and at == x(s.spans[i]['start'],'s'))
         or (phase == 'forcing_before' and i < len(s.spans)-1 and at == x(s.spans[i]['end'],'s'))
         or (phase == 'declared_end' and at == s.stop and i == len(s.spans)-1)
         or (phase == 'original_grid_endpoint' and at%s.grid == 0 and at < x(s.spans[i]['end'],'s')),
         'TIME_HOLD: actual ordered forcing/grid/end phase required')


def _switch_evidence(s,before,index):
    return {'span_index':index,'at':deepcopy(before['at']),
            'before_state_sha256':digest(before['numeric']['last_confirmed']['state']),
            'after_state_sha256':digest(before['numeric']['last_confirmed']['state']),
            'point_transfers_added':False,'producer_code_sha256':CODE_SHA256}


def _interval_evidence(s,before,trace):
    n=before['numeric'];span=s.spans[before['span_index']];active=n['active_input_sha256'];derived=n['last_confirmed']['derived']
    return {**FLAGS,'schema_version':'supply-forcing-interval-candidate-v1','model_version':kernel.VERSION,
            'code_sha256':kernel.CODE_SHA256,'arithmetic_code_sha256':base.CODE_SHA256,
            'component_code_sha256':dict(kernel._COMPONENTS),
            'input_sha256':digest({'basis':s.math_basis,'current':n,'span':span,'end':trace['right_elapsed_seconds_exact']}),
            'span_sha256':digest(span),'forcing_transition':{'at':deepcopy(n['at']),'changed':False,
                'previous_input_sha256':active,'active_input_sha256':active,
                'before_state_sha256':digest(n['last_confirmed']['state']),'after_state_sha256':digest(n['last_confirmed']['state']),
                'before_derived':deepcopy(derived),'after_derived':deepcopy(derived),'point_transfers_added':False},
            'interval':trace,'progress':{'stage':'endpoint','current_validation_RHS_evaluations':1,'new_RHS_evaluations':4},
            'checkpoint_issued':False,'history_committed':False,'material_consumed':False,'status':'interval_ready','pending':None}


def _verify_interval(s,before,after,evidence):
    need(_switch_index(s,before) is None and before['phase'] != 'declared_end', 'ORDER_HOLD: interval must follow an applied forcing')
    trace=evidence['interval'];left=x(before['at']['elapsed_seconds_exact'],'s');right=_right(s,before);h=right-left
    base.reader._closed(trace, {'left_elapsed_seconds_exact','right_elapsed_seconds_exact','step_seconds_exact','stages','endpoint','flux_order','shoot_clock_certificate'})
    need(trace['left_elapsed_seconds_exact'] == q(left,'s') and trace['right_elapsed_seconds_exact'] == q(right,'s')
         and trace['step_seconds_exact'] == q(h,'s'), 'TIME_HOLD: canonical fixed partition required')
    index=before['span_index'];m=_math(s,index);n=before['numeric'];y=tuple(n['last_confirmed']['state'])
    need(type(trace['stages']) is list and len(trace['stages']) == 4, 'TRACE_HOLD: actual four RK4 stages required')
    rates=[];flows=[];previous=None
    forced={'canopy_external':s.spans[index]['forcing']['canopy_external_heat']['value'],
            'air_external':s.spans[index]['forcing']['air_external_sensible_heat']['value'],
            'external_vapor':s.spans[index]['forcing']['air_external_vapor']['value'],
            'entry_number':s.spans[index]['fruit_entry']['fruit_number_inflow']['value']}
    names=list(m.units)
    for label,offset,row in zip(('k1','k2','k3','k4'),(Fraction(0),h/2,h/2,h),trace['stages'],strict=True):
        base.reader._closed(row, {'stage','at_elapsed_seconds_exact','state','rates','flux'})
        expected=y if previous is None else base.combine(y,(previous,),(Fraction(1),),offset)
        need(row['stage'] == label and row['at_elapsed_seconds_exact'] == q(left+offset,'s')
             and base._vector(row['state'],len(y)) == expected, 'TRACE_HOLD: exact stage state/time order required')
        previous=base._vector(row['rates'],len(y));rates.append(previous);flow=base._vector(row['flux'],len(m.units));flows.append(flow)
        need(all(flow[names.index(k)] == v for k,v in forced.items()), 'FORCING_HOLD: stage external/entry flux must use active view')
    weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    state=base.combine(y,tuple(rates),weights,h)
    totals=base.combine(tuple(n['branch_integrated_transfers'][k]['value'] for k in m.units),tuple(flows),weights,h)
    base.reader._closed(trace['endpoint'], {'state','rates','flux'})
    need(base._vector(trace['endpoint']['state'],len(y)) == state
         and trace['flux_order'] == [{'name':k,'unit':v} for k,v in m.units.items()], 'TRACE_HOLD: exact endpoint/flux order required')
    base._vector(trace['endpoint']['rates'],len(y));base._vector(trace['endpoint']['flux'],len(m.units))
    numeric=_numeric(s,n,state,totals,after['numeric']['last_confirmed']['derived'],n['branch_steps']+1,right,index)
    need(x(numeric['schedule']['age_exact'],'degC_day') < x(numeric['schedule']['next_threshold_exact'],'degC_day'),
         'EVENT_HOLD: stored interval cannot skip a material threshold')
    certificate=base.arithmetic._interval_clock(m.data,n,trace,numeric['schedule'])
    need(trace['shoot_clock_certificate'] == certificate and evidence == _interval_evidence(s,before,trace),
         'TRACE_HOLD: exact kernel/code/input/clock evidence required')
    need(after == _compose(s,before,numeric,index,_interval_phase(s,index,right),True),
         'CHECKPOINT_HOLD: exact interval state/accounts/phase/prefix required')


def _restore(s,cursor_sha):
    selected=selected_current=None;seen=set()
    while True:
        need(cursor_sha not in seen and len(seen) <= MAX_OPERATIONS, 'CAPACITY_HOLD: bounded acyclic owner history required')
        seen.add(cursor_sha);cursor=get(s,cursor_sha,base.CURRENT_MAX)
        base.reader._closed(cursor, {'schema_version',*FLAGS,'code_sha256','definition_sha256','basis_sha256','current_sha256','previous_cursor_sha256','history_page_sha256'})
        need(cursor == _cursor(s,cursor['current_sha256'],digest(s.basis),cursor['previous_cursor_sha256'],cursor['history_page_sha256'])
             and get(s,cursor['basis_sha256']) == s.basis, 'SOURCE_HOLD: actual owner source/basis/definition required')
        current=get(s,cursor['current_sha256'],base.CURRENT_MAX);_shape(s,current)
        if selected is None:selected,selected_current=cursor,current
        previous=cursor['previous_cursor_sha256']
        if previous is None:
            need(cursor['history_page_sha256'] is None and current == _initial(s), 'SOURCE_HOLD: complete actual source origin required')
            break
        parent=get(s,previous,base.CURRENT_MAX);before=get(s,parent['current_sha256'],base.CURRENT_MAX);_shape(s,before)
        page=get(s,cursor['history_page_sha256'])
        base.reader._closed(page, {'schema_version','kind','previous_cursor_sha256','before_current_sha256','after_current_sha256','evidence'})
        need(page['schema_version'] == 'supply-forcing-history-page-v1' and page['previous_cursor_sha256'] == previous
             and page['before_current_sha256'] == parent['current_sha256'] and page['after_current_sha256'] == cursor['current_sha256'],
             'HISTORY_HOLD: actual ordered current/page references required')
        if page['kind'] == 'forcing_switch':
            index=_switch_index(s,before)
            need(index is not None and page['evidence'] == _switch_evidence(s,before,index)
                 and current == _switch(s,before,index,current['numeric']['last_confirmed']['derived']),
                 'ORDER_HOLD: exact zero-time forcing switch required')
        else:
            need(page['kind'] == 'interval', 'HISTORY_HOLD: known owner history operation required')
            _verify_interval(s,before,current,page['evidence'])
        cursor_sha=previous
    return selected,selected_current


def _request(s,current,request):
    need(type(request) is base.AdvanceRequest, 'BUDGET_HOLD: explicit bounded request required')
    for name,maximum in [('step_budget',128),('rhs_budget',1024),('record_budget',128),('byte_budget',base.PAGE_MAX),('wall_seconds',60)]:
        value=getattr(request,name);need(type(value) is int and 1 <= value <= maximum, 'BUDGET_HOLD: bounded '+name+' required')
    need(request.cancelled is None or callable(request.cancelled), 'BUDGET_HOLD: trusted local cancellation probe required')
    stop=x(request.stop_at,'s');at=x(current['at']['elapsed_seconds_exact'],'s')
    need(at <= stop <= s.stop and (stop%s.grid == 0 or stop == at or any(stop == x(v['end'],'s') for v in s.spans)),
         'TIME_HOLD: requested stop must be a declared partition boundary')
    return stop


def _remaining_wall(request,started):
    remaining=request.wall_seconds-(time.monotonic()-started)
    need(remaining >= 1, 'WALL_HOLD: owner deadline has no complete kernel budget left')
    return min(60,int(remaining))


def _page(before_cursor,after_sha,kind,evidence):
    return {'schema_version':'supply-forcing-history-page-v1','kind':kind,
            'previous_cursor_sha256':before_cursor['sha256'],'before_current_sha256':before_cursor['current_sha256'],
            'after_current_sha256':after_sha,'evidence':evidence}


def _publish(s,confirmed,cursor,new,kind,evidence,request,progress,started):
    new_sha=digest(new);page=_page({'sha256':confirmed.cursor_sha256,'current_sha256':cursor['current_sha256']},new_sha,kind,evidence)
    proposed=_cursor(s,new_sha,cursor['basis_sha256'],confirmed.cursor_sha256,digest(page))
    cost=sum(len(raw(v)) for v in (new,page,proposed))
    if progress['bytes_emitted']+cost > request.byte_budget:return None
    progress['stage']='publication';base._interrupt(request,progress,started);_check(s)
    put(s,new,base.CURRENT_MAX);put(s,page);sha=put(s,proposed,base.CURRENT_MAX)
    base._interrupt(request,progress,started);_check(s)
    progress['records_emitted']+=1;progress['bytes_emitted']+=cost
    return _handle(s,sha,proposed,new),proposed


def advance(handle,request,*,material=None):
    started=time.monotonic()
    p={'stage':'admission','steps_attempted':0,'records_emitted':0,'bytes_emitted':0,'RHS_quota_reserved':0,
       'current_validation_RHS_evaluations':0,'new_RHS_evaluations':0,'forcing_switch_RHS_evaluations':0,
       'failed_interval_RHS_count_unreported':False,'past_intervals_reintegrated':0}
    confirmed=None;emitted=[]
    try:
        need(type(handle) is Handle and handle._token is _TOKEN, 'CONTEXT_HOLD: genuine forcing-owner handle required')
        with _session(handle._definition,handle._workspace) as s:
            cursor,current=_restore(s,handle.cursor_sha256)
            need(raw(cursor,base.CURRENT_MAX) == handle._cursor and raw(current,base.CURRENT_MAX) == handle._current
                 and raw(s.basis) == handle._basis, 'CONTEXT_HOLD: unchanged owner handle bytes required')
            confirmed=handle
            try:
                need(material is None, 'MATERIAL_HOLD: material adoption requires separate refinement/point owner')
                stop=_request(s,current,request);status='yielded';pending=None
                while True:
                    base._interrupt(request,p,started)
                    if p['records_emitted'] >= request.record_budget:break
                    index=_switch_index(s,current)
                    if index is not None:
                        if p['RHS_quota_reserved']+1 > request.rhs_budget:break
                        p['stage']='forcing_switch';_check(s);m=_math(s,index);n=current['numeric']
                        p['RHS_quota_reserved']+=1;p['forcing_switch_RHS_evaluations']+=1
                        view_hash=digest(m.data['program'])
                        rhs=base.stage.evaluate(m.data['program'],tuple(n['last_confirmed']['state']),m.data['organs'],m.data['costs'],s.profiles)
                        need(digest(m.data['program']) == view_hash, 'SOURCE_HOLD: unchanged switch program required')
                        new=_switch(s,current,index,rhs['derived']);kind='forcing_switch';evidence=_switch_evidence(s,current,index)
                    else:
                        at=x(current['at']['elapsed_seconds_exact'],'s')
                        if at >= stop or p['steps_attempted'] >= request.step_budget or p['RHS_quota_reserved']+5 > request.rhs_budget:break
                        p['stage']='interval_evaluation';_check(s);index=current['span_index'];right=_right(s,current)
                        need(right <= stop, 'TIME_HOLD: request must not split a canonical interval')
                        remaining=_remaining_wall(request,started)
                        p['steps_attempted']+=1;p['RHS_quota_reserved']+=5
                        try:
                            result=kernel.advance_interval(basis=s.math_basis,current=current['numeric'],profiles=s.profiles,
                                span=s.spans[index],end=q(right,'s'),cancelled=request.cancelled,wall_seconds=remaining)
                        except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError):
                            p['failed_interval_RHS_count_unreported']=True;raise
                        p['current_validation_RHS_evaluations']+=result['progress']['current_validation_RHS_evaluations']
                        p['new_RHS_evaluations']+=result['progress']['new_RHS_evaluations']
                        if result['status'] == 'awaiting_material':
                            pending={**result['pending'],'reason':'EVENT_HOLD: refine material threshold before further integration'}
                            order=right == x(s.spans[index]['end'],'s') and index < len(s.spans)-1
                            if order:pending['reason']='ORDER_HOLD: material bracket reaches forcing edge; refine its order'
                            page={'schema_version':'supply-forcing-pending-page-v1','definition_sha256':s.definition_ref,
                                  'previous_cursor_sha256':confirmed.cursor_sha256,'result':result,'reason':pending['reason']}
                            cost=len(raw(page))
                            if p['bytes_emitted']+cost > request.byte_budget:pending=None;break
                            p['stage']='pending_publication';base._interrupt(request,p,started);_check(s)
                            sha=put(s,page);base._interrupt(request,p,started);_check(s)
                            pending={**pending,'page_sha256':sha};p['records_emitted']+=1;p['bytes_emitted']+=cost
                            status='hold' if order else 'awaiting_material';break
                        need(result['status'] == 'interval_ready', 'STATE_HOLD: explicit checked interval result required')
                        new=_compose(s,current,result['current'],index,_interval_phase(s,index,right),True)
                        evidence={k:v for k,v in result.items() if k != 'current'};kind='interval'
                    published=_publish(s,confirmed,cursor,new,kind,evidence,request,p,started)
                    if published is None:break
                    confirmed,cursor=published;current=new
                    emitted.append({'cursor_sha256':confirmed.cursor_sha256,'current_sha256':cursor['current_sha256'],
                                    'at':deepcopy(new['at']),'phase':new['phase'],'span_index':new['span_index']})
                base._interrupt(request,p,started);_check(s)
                if current['phase'] == 'declared_end':status='completed'
                p['requested_stop_reached']=x(current['at']['elapsed_seconds_exact'],'s') == stop and _switch_index(s,current) is None
                reason=pending['reason'] if status == 'hold' and pending is not None else None
                return Outcome(status,confirmed,reason,p['stage'] if reason else None,pending,deepcopy(p),emitted)
            except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError) as error:
                first=base._reason(error);authority=None
                try:_check(s)
                except (OSError,ValueError,TypeError,KeyError) as late:
                    authority=base._reason(late);confirmed=None;emitted=[]
                return Outcome('hold',confirmed,first,p['stage'],None,deepcopy(p),emitted,handle.cursor_sha256,authority)
    except (OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError) as error:
        return Outcome('hold',None,base._reason(error),p['stage'],None,deepcopy(p),[],
                       handle.cursor_sha256 if type(handle) is Handle else None)
