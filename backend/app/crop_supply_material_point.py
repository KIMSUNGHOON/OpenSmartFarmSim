"""Source-bound explicit new-organ proposals; no schedule or checkpoint adoption."""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import time

from . import crop_supply_forcing_threshold_state as candidate
from . import crop_supply_morphology_point_core as material
from . import crop_supply_morphology_repeat_point_books as point_books

owner,base,kernel=candidate.owner,candidate.base,candidate.kernel
VERSION='supply-season-material-point-research-v1'
POLICY='explicit-compatible-seed-on-active-forcing-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
FLAGS=base.FLAGS
q,x,need,raw,digest=base.q,base.x,base._need,base._raw,base._hash
INPUT_MAX=128*1024


def _code():
    candidate._code()
    need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,
         'CODE_HOLD: unchanged current-source material arithmetic required')


def _entity(timeline,sequence,threshold):
    value={k:deepcopy(timeline[k])for k in ('shoot_id','development_origin_id','schedule_id','started_at')}
    value.update(sequence=sequence,birth_age_exact=deepcopy(threshold));return value


def _source(s,current):
    manifest=s.origin.manifest;binding_sha=manifest['initial_binding']['sha256']
    binding=json.loads(s.origin.source_witnesses[binding_sha][0]);source=binding['stem_selection']['source_state']
    timeline=source['timeline_state'];schedule=current['numeric']['schedule']
    need(schedule['source_schedule_id']==timeline['schedule_id']
         and s.math_basis['shoot_base_temperature']==timeline['base_temperature']['value'],
         'SOURCE_HOLD: actual original shoot timeline and base required')
    spacing=x(timeline['phyllochron_exact'],'degC_day')
    need(type(schedule['next_sequence'])is int and spacing>0
         and schedule['next_sequence']==schedule['consumed_sequence']+1
         and x(schedule['next_threshold_exact'],'degC_day')==x(schedule['consumed_threshold_exact'],'degC_day')+spacing,
         'EVENT_HOLD: actual first unconsumed schedule item required')
    previous=material.source_ids._digest(_entity(timeline,schedule['consumed_sequence'],schedule['consumed_threshold_exact']))
    need(schedule['consumed_event_id']=='shoot-event:'+previous,'SOURCE_HOLD: original consumed event identity required')
    entity=_entity(timeline,schedule['next_sequence'],schedule['next_threshold_exact']);identifier=material.source_ids._digest(entity)
    event={'entity':entity,'source_event_id':'shoot-event:'+identifier,'internode_event_id':'shoot-event:'+identifier+'/internode',
           'leaf_event_id':'shoot-event:'+identifier+'/leaf','internode_id':'internode:'+identifier,
           'leaf_id':'leaf:'+material.source_ids._digest({**entity,'organ':'leaf','slot':0}),
           'sequence':schedule['next_sequence'],'threshold_exact':deepcopy(schedule['next_threshold_exact'])}
    p=s.math_basis['seed']['program'];organs=s.math_basis['seed']['organs']
    past={row['event_id']for rows in organs.values()if type(rows)is list for row in rows if 'event_id'in row}
    need(not past.intersection(event[k]for k in ['source_event_id','internode_event_id','leaf_event_id'])
         and event['internode_id']not in {v['compartment_id']for v in p['stem_root_compartments']}
         and event['leaf_id']not in {v['leaf_id']for v in p['leaves']},'EVENT_HOLD: next source IDs must be unused')
    return {'initial_binding_sha256':binding_sha,'timeline':deepcopy(timeline),
            'emergence_profile':deepcopy(source['emergence_profile']),'event':event,
            'parent_internode_ids':[v['compartment_id']for v in p['stem_root_compartments']if v['kind']=='internode']}


@contextmanager
def _session(handle):
    _code();need(type(handle)is owner.Handle and handle._token is owner._TOKEN,'CONTEXT_HOLD: genuine forcing owner required')
    with owner._session(handle._definition,handle._workspace)as s:
        cursor,current=owner._restore(s,handle.cursor_sha256)
        need(raw(cursor,base.CURRENT_MAX)==handle._cursor and raw(current,base.CURRENT_MAX)==handle._current
             and raw(s.basis)==handle._basis,'CONTEXT_HOLD: unchanged current handle bytes required')
        source=_source(s,current);owner._check(s);yield s,current,source


def _failure(handle,error,progress=None,authority=None):
    return {**FLAGS,'schema_version':'supply-season-material-point-result-v1','model_version':VERSION,'code_sha256':CODE_SHA256,
            'status':'hold','hold':base._reason(error),'progress':deepcopy(progress or{'stage':'source_admission'}),
            'after_state':None,'authority_hold':authority,
            'historical_cursor_sha256':handle.cursor_sha256 if type(handle)is owner.Handle else None,
            'checkpoint_issued':False,'history_committed':False,'material_consumed':False}


def describe_material_source(handle):
    try:
        with _session(handle)as(s,current,source):
            out={**FLAGS,'schema_version':'supply-season-material-source-v1','model_version':VERSION,'code_sha256':CODE_SHA256,
                 'status':'source_described','definition_sha256':s.definition_ref,'cursor_sha256':handle.cursor_sha256,
                 'source_current_sha256':digest(current),'effective_rights':deepcopy(s.rights),**source,'schedule_consumed':False}
            out['descriptor_sha256']=digest(out);raw(out);owner._check(s);_code();return out
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:return _failure(handle,error)


FIELDS={'schema_version','input_id','origin','policy','parameter_source','parameter_revision','reviewer',
        'definition_sha256','cursor_sha256','pending_page_sha256','candidate_sha256','initial_binding_sha256',
        'at_elapsed_seconds_exact','source_event_id','source_threshold_sequence','source_threshold_exact',
        'parent_internode_id','model_floor_area','internode','leaf','rights','parameter_provenance'}


def _parameters(value):
    return {k:value[k]for k in ['parameter_source','parameter_revision','model_floor_area','internode','leaf']}


def _units(value):
    result={}
    def visit(v,path):
        if type(v)is dict:
            if set(v)=={'value','unit'}:result[path]=v['unit']
            else:
                for k,item in v.items():visit(item,path+'.'+k if path else k)
    visit(value,'');return result


def _provenance(v):
    p=v['parameter_provenance']
    base.reader._closed(p,{'product_id','source_url','observed_at','published_at','available_at','retrieved_at','vintage','revision','qc','units','raw_sha256','reviewer'})
    need(p['product_id']==v['input_id']and p['revision']==v['parameter_revision']and p['reviewer']==v['reviewer']
         and p['observed_at']is None and p['published_at']is None and p['qc']=='software_fixture_only',
         'SOURCE_HOLD: explicit own-synthetic parameter provenance required')
    for name in ['product_id','vintage','revision','reviewer']:base.reader._id(p[name])
    need(type(p['source_url'])is str and 1<=len(p['source_url'])<=2048
         and p['source_url'].startswith(('https://','http://','urn:')),'SOURCE_HOLD: parameter source URL/product URI required')
    need(base.reader._utc(p['available_at'])<=base.reader._utc(p['retrieved_at']),
         'TIME_HOLD: parameter availability must precede retrieval')
    parameters=_parameters(v)
    need(p['units']==_units(parameters)and p['raw_sha256']==digest(parameters),
         'SOURCE_HOLD: exact declared parameter units/raw identity required')


def _head(s,current,source,value,pending_page):
    base.reader._closed(value,FIELDS)
    need(value['schema_version']=='supply-season-material-point-input-v1'and value['origin']=='synthetic'
         and value['policy']==POLICY and value['parameter_source']=='own_declared_synthetic_assumptions',
         'SCOPE_HOLD: explicit compatible synthetic material declaration required')
    for key in ['input_id','parameter_revision','reviewer','parent_internode_id']:base.reader._id(value[key])
    for key in ['definition_sha256','cursor_sha256','pending_page_sha256','candidate_sha256','initial_binding_sha256']:base.reader._hash(value[key])
    need(value['definition_sha256']==s.definition_ref and value['pending_page_sha256']==pending_page
         and value['initial_binding_sha256']==source['initial_binding_sha256'],
         'SOURCE_HOLD: actual definition/pending/initial binding required')
    owner._rights(value['rights']);need(value['rights']['use'],'RIGHTS_HOLD: material use required')
    _provenance(value);event=source['event']
    need(value['source_event_id']==event['source_event_id']and type(value['source_threshold_sequence'])is int
         and value['source_threshold_sequence']==event['sequence']and value['source_threshold_exact']==event['threshold_exact'],
         'EVENT_HOLD: actual first unconsumed event required')
    need(value['parent_internode_id']in source['parent_internode_ids'],'PARENT_HOLD: existing actual internode parent required')
    p=s.math_basis['seed']['program']
    need(material.arithmetic._quantity(value['model_floor_area'],'m2_floor')==p['model_floor_area']['value'],
         'BASIS_HOLD: actual common floor required')


def _seeds(s,source,v):
    event=source['event'];a=material.arithmetic;part=material.source.stock.short.stock.part
    a._closed(v['internode'],{'declaration','initial_length','construction_cost'})
    row=v['internode']['declaration'];stock_fields=material.source.stock.short.STOCK_FIELDS
    a._closed(row,{'compartment_id','kind',*stock_fields});part._id(row['compartment_id'])
    need(row['compartment_id']==event['internode_id']and row['kind']=='internode','EVENT_HOLD: exact new internode ID/kind required')
    numbers={k:a._quantity(row[k],unit)for k,unit in stock_fields.items()}
    need(numbers['initial_carbon']>0 and numbers['sink_weight']>=0 and numbers['carbon_removal']==0,
         'SEED_HOLD: positive C/nonnegative sink/zero removal required')
    node={**deepcopy(row),**{k:material.numeric._q(value,stock_fields[k])for k,value in numbers.items()}}
    length=a._quantity(v['internode']['initial_length'],'m');cost=a._quantity(v['internode']['construction_cost'],'mg_CH2O/m_internode')
    profile=source['emergence_profile'];floor=s.math_basis['seed']['program']['model_floor_area']['value']
    need(0<=length<=profile['curve']['values']['maximum_length']['value'],'GEOMETRY_HOLD: bounded explicit seed length required')
    compatibility={'internode':material.compatibility(numbers['initial_carbon'],cost,length,floor,'m')}
    new_leaf=initialization=leaf_cost=temperature=None
    if v['leaf']is not None:
        packet=v['leaf'];a._closed(packet,{'declaration','incoming_temperature','construction_cost'})
        new_leaf,initialization=a._new_leaf(packet['declaration'])
        need(new_leaf['leaf_id']==event['leaf_id']and new_leaf['carbon_removal']['value']==0,
             'EVENT_HOLD: exact new leaf ID/zero removal required')
        temperature=a._quantity(packet['incoming_temperature'],'degC');material.numeric._temperature(temperature)
        leaf_cost=a._quantity(packet['construction_cost'],'mg_CH2O/m2_leaf')
        compatibility['leaf']=material.compatibility(new_leaf['initial_carbon']['value'],leaf_cost,initialization['state']['area']['value'],floor,'m2')
    return {'node':node,'length':length,'cost':cost,'profile':deepcopy(profile),'base_temperature':deepcopy(source['timeline']['base_temperature']),
            'leaf':new_leaf,'initialization':initialization,'leaf_cost':leaf_cost,'temperature':temperature,'compatibility':compatibility}


def apply_material_point(handle,pending_page_sha256,time_tolerance_seconds_exact,*,inputs,cancelled=None,wall_seconds=60):
    started=time.monotonic();progress={'stage':'admission','candidate_RHS_evaluations':0,'point_RHS_evaluations':0,
                                      'candidate_failed_RHS_count_unreported':False,'past_confirmed_intervals_reintegrated':0}
    try:
        _code();need(type(wall_seconds)is int and 1<=wall_seconds<=60 and(cancelled is None or callable(cancelled)),
                     'BUDGET_HOLD: bounded point controls required')
        input_raw=raw(inputs,INPUT_MAX);v=json.loads(input_raw);tolerance=q(x(time_tolerance_seconds_exact,'s'),'s')
        controls=base.AdvanceRequest(q(0,'s'),wall_seconds=wall_seconds,cancelled=cancelled)
        def interrupt():base._interrupt(controls,progress,started)
        interrupt()
        with _session(handle)as(s,current,source):
            _head(s,current,source,v,pending_page_sha256)
            need(v['cursor_sha256']==handle.cursor_sha256,'SOURCE_HOLD: actual current cursor required')
            seeds=_seeds(s,source,v);rights={k:s.rights[k]and v['rights'][k]for k in s.rights}
            need(len(s.math_basis['seed']['program']['leaves'])+int(seeds['leaf']is not None)<=512
                 and len(s.math_basis['seed']['program']['stem_root_compartments'])+1<=512
                 and len(s.math_basis['seed']['organs']['internodes'])+1<=512,'CAPACITY_HOLD: bounded resulting inventory required')
            admitted=raw({'basis':s.basis,'current':current,'source':source})
            owner._check(s)
        progress['stage']='candidate_calculation'
        result=candidate.calculate_threshold_state(handle,pending_page_sha256,tolerance,cancelled=cancelled,
                                                  wall_seconds=owner._remaining_wall(controls,started))
        rp=result['progress'];progress['candidate_RHS_evaluations']=rp['root_RHS_evaluations']+rp['new_RHS_evaluations']
        progress['candidate_failed_RHS_count_unreported']=rp['failed_root_RHS_count_unreported']
        need(result['status']=='candidate_ready',result.get('hold')or'CANDIDATE_HOLD: actual same-source state required')
        with _session(handle)as(s,current,source):
            try:
                progress['stage']='source_readmission'
                _head(s,current,source,v,pending_page_sha256)
                need(admitted==raw({'basis':s.basis,'current':current,'source':source}),
                     'SOURCE_HOLD: unchanged admitted source after standalone candidate calculation required')
                def fence():
                    interrupt();owner._check(s);_code();kernel._profiles(s.math_basis,s.profiles)
                    need(raw(inputs,INPUT_MAX)==input_raw,'SOURCE_HOLD: material input changed during calculation')
                fence()
                need(v['candidate_sha256']==result['calculation_sha256']and v['at_elapsed_seconds_exact']==result['at']['elapsed_seconds_exact']
                     and result['source_current_sha256']==digest(current),'SOURCE_HOLD: exact candidate/time/source required')
                selected=x(result['at']['elapsed_seconds_exact'],'s');index=current['span_index']
                need(index==len(s.spans)-1 or selected<x(s.spans[index]['end'],'s'),
                     'ORDER_HOLD: selected material time reaches forcing edge; refine the root bound before any point')
                age=x(result['dense_candidate']['shoot_age_exact'],'degC_day');threshold=x(source['event']['threshold_exact'],'degC_day')
                need(threshold<=age<threshold+x(source['timeline']['phyllochron_exact'],'degC_day'),
                     'EVENT_HOLD: first pending threshold only')
                index=current['span_index'];program=kernel._view(s.math_basis,s.spans[index]);data=kernel._data(s.math_basis,program,s.profiles)
                data['initial']={'organs':data['seed']['organs'],'state_layout':data['seed']['state_layout']}
                before=deepcopy(result['dense_candidate'])
                numbers={'dense_candidate':{**before,'global_ledgers':deepcopy(before['pending_global_ledgers'])},
                         'at':deepcopy(result['at']),'source_prefix':{'event_sequence':current['numeric']['event_sequence']}}
                def evaluate(p,y,organs,costs):
                    progress['stage']='material_stage';fence()
                    need(progress['point_RHS_evaluations']<2,'CAPACITY_HOLD: bounded point stage evaluations required')
                    snapshot=raw({'program':p,'state':y,'organs':organs,'costs':costs});progress['point_RHS_evaluations']+=1
                    value=material.stage.evaluate(p,y,organs,costs,s.profiles)
                    need(snapshot==raw({'program':p,'state':y,'organs':organs,'costs':costs}),
                         'SOURCE_HOLD: material stage changed numeric inputs')
                    fence();return value
                # Both reused operations are pure arithmetic: their context argument is unused.
                fence();jump=material.apply(None,data,numbers,v,source['event'],seeds,evaluate)
                progress['stage']='point_balances';preview=point_books.calculate(None,data,numbers,jump)
                p=jump['program'];layout={**deepcopy(data['seed']['state_layout']),'original':material.source.stock.short._layout(p),
                    'original_prefix_length':106+3*len(p['leaves'])+len(p['stem_root_compartments']),
                    'internode_ids':[row['compartment_id']for row in jump['organs']['internodes']]}
                progress['stage']='final_source_check';fence()
                out={**FLAGS,'schema_version':'supply-season-material-point-result-v1','model_version':VERSION,'code_sha256':CODE_SHA256,
                     'status':'point_ready','hold':None,'policy':POLICY,'definition_sha256':s.definition_ref,'cursor_sha256':handle.cursor_sha256,
                     'pending_page_sha256':pending_page_sha256,'source_current_sha256':digest(current),'candidate_sha256':result['calculation_sha256'],
                     'initial_binding_sha256':source['initial_binding_sha256'],'input_sha256':sha256(input_raw).hexdigest(),'inputs':v,
                     'effective_rights':rights,'root_certificate':result['root_certificate'],'before_dense':before,'source_event':source['event'],
                     'source_schedule':deepcopy(current['numeric']['schedule']),'source_transfer_origins':deepcopy(current['numeric']['transfer_origins']),
                     'at':deepcopy(result['at']),'after_program':p,'after_state':jump['state'],'after_rates':deepcopy(jump['evaluation']['rates']),
                     'after_stage':jump['evaluation'],'after_derived':deepcopy(jump['evaluation']['derived']),'after_organs':jump['organs'],
                     'after_costs':jump['costs'],'after_state_layout':layout,'seed_compatibility':seeds['compatibility'],
                     'new_birth_baselines':jump['new_birth_baselines'],'flow_components':jump['components'],'growth_costs':jump['growth_costs'],
                     'leaf_receipts':jump['leaf_receipts'],**preview,'point_order':['internode','leaf']if v['leaf']is not None else['internode'],
                     'candidate_RHS_evaluations':progress['candidate_RHS_evaluations'],'point_stage_RHS_evaluations':progress['point_RHS_evaluations'],
                     'progress':deepcopy(progress),'elapsed_seconds_advanced':q(0,'s'),'schedule_adoption':'not_performed',
                     'checkpoint_issued':False,'history_committed':False,'material_consumed':False}
                out['calculation_sha256']=digest(out);raw(out);fence();return out
            except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:
                authority=None
                try:owner._check(s);_code()
                except(OSError,ValueError,TypeError,KeyError)as late:authority=base._reason(late)
                return _failure(handle,error,progress,authority)
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError)as error:return _failure(handle,error,progress)
