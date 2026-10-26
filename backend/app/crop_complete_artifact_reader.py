"""Read trusted complete research packets without importing plant equations."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import fsum
from pathlib import Path

from . import crop_leaf_funded_birth_artifact_reader as leaf
from . import crop_rational_morphology_artifact_reader as stem
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need
from .crop_morphology_artifact_reader import _canonical,_closed,_hash,_id,_parse,_age,_quantity

MAX=2*1024**2
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
POINT_MAX=64*1024
MODEL_VERSION='funded-complete-source-prefix-fractional-geometry-research-v1'
CROP_VERSION='funded-fractional-original-grid-continuation-research-v1'
CP_VERSION='fractional-individual-leaf-checkpoint-v1'
POINT_VERSION='internode-logistic-length-point-research-v1'
BINDING_VERSION='funded-fractional-source-shoot-leaf-binding-research-v1'
EXTRAS=tuple('backend/app/'+name+'.py' for name in ('crop_funded_shoot_epochs','crop_funded_event_time',
    'crop_funded_event_state','crop_funded_fractional_birth_point','crop_funded_fractional_continuation',
    'crop_funded_fractional_stem_binding','crop_funded_complete_prefix'))
MODEL_SOURCE_PATHS=tuple(dict.fromkeys((*leaf.SOURCE_PATHS,*stem.SOURCE_PATHS,*EXTRAS)))
SOURCE_PATHS=(*MODEL_SOURCE_PATHS,'backend/app/crop_complete_artifact_reader.py','backend/app/crop_complete_artifact_producer.py')
FLAGS={'schema_version':'complete-crop-research-artifact-v1','scope':'software_research_only','G0_G4':'not_assessed',
    'R2':'not_approved','status':'completed_software_fixture','time_kind':'synthetic_model_clock_not_observation',
    'claim_scope':'stored_synthetic_complete_crop_geometry_only'}
ROOT_FIELDS={*FLAGS,'code_sha256','packet','contexts','source_blobs','geometry_receipts','frames'}
FRAME_FIELDS={'at','phase','event_sequence','output_cursor','output_prefix_sha256','program_sha256','shoot','leaves',
    'tracked_leaf_area','evidence','quantities_storage'}
CP_FIELDS={'version','context_sha256','at','grid_step_index','segment_steps','branch_steps','event_sequence','phase',
    'last_confirmed','output_cursor','output_prefix_sha256','segment_integrated_transfers','branch_integrated_transfers',
    'lifetime_integrated_transfers','branch_point_transfers','lifetime_point_transfers','branch_balance_residuals',
    'branch_balance_budgets','global_balance_residuals','global_balance_budgets','scope','G0_G4'}
CONTEXT_FIELDS={'version','code_sha256','source','original','program','anchors','branch_initial','base_lifetime_transfers',
    'base_prior_budgets','records','seed'}


class CompleteCropArtifactHold(MorphologyArtifactHold):
    pass


def _digest(value):return sha256(_canonical(value)).hexdigest()
def _frac(value):return Fraction(int(value['numerator']),int(value['denominator']))
def _pins():
    root=Path(__file__).resolve().parents[2]
    return {name:sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}


def _source(store,descriptor,raws,maximum=MAX):
    raw=leaf.stock._source(store,descriptor,maximum=maximum);raws[descriptor['sha256']]=raw
    return raw


def _snapshot(frame):
    cp=frame['evidence']['checkpoint']
    return frame['snapshot'] if cp is None else cp['last_confirmed']


def _flows(frame):
    cp=frame['evidence']['checkpoint']
    if cp is None:return frame['lifetime_integrated_transfers']
    return cp['lifetime_integrated_transfers'] if frame['evidence']['kind']=='fractional_checkpoint' else cp['integrated_transfers']


def _ledgers(frame):
    cp=frame['evidence']['checkpoint']
    if cp is None:return frame['ledgers']
    if frame['evidence']['kind']=='fractional_checkpoint':return {'balance_residuals':cp['global_balance_residuals'],'balance_budgets':cp['global_balance_budgets']}
    return {key:cp.get('global_'+key,cp[key]) for key in ('balance_residuals','balance_budgets')}


def point_request(packet,frame,node):
    if node['kind']=='selected_original':
        version=MODEL_VERSION if frame['evidence']['kind']=='original_funded_checkpoint' else BINDING_VERSION
        identity={'model':version,'source':packet['basis']['stem_source_state_sha256'],'id':node['internode_id']}
    else:identity={'model':BINDING_VERSION,'candidate':frame['shoot']['birth']['candidate_sha256'],'id':node['internode_id']}
    return {'input_id':_digest(identity),'origin':'synthetic','thermal_age_basis':'since_internode_emergence',
        'age_exact':deepcopy(node['age_exact']),'curve':leaf.stock._float_view(node['curve'])}


def frame_descriptor(index,frame):
    return {'index':index,'at':deepcopy(frame['at']),'phase':frame['phase'],'event_sequence':frame['event_sequence'],
        'output_cursor':frame['output_cursor'],'output_prefix_sha256':frame['output_prefix_sha256'],
        'frame_sha256':_digest(frame),'state_sha256':_digest(_snapshot(frame)['state']),
        'checkpoint_sha256':frame['evidence']['checkpoint_sha256']}


def _prefix(previous,sample,sequence,phase):
    return _digest({'previous':previous,'model_version':CROP_VERSION,'sample':sample,'event_sequence':sequence,'phase':phase})


def _qcs(residuals,budgets,program):
    units={**leaf.stock.BALANCE_UNITS,**{f'leaf_age_{i}':'degC_day' for i in range(len(program['leaves']))},
           **{f'leaf_carbon_{i}':'mg_CH2O/m2_floor' for i in range(len(program['leaves']))}}
    leaf.stock._block(residuals,units,normalized=True);leaf.stock._block(budgets,units,normalized=True)
    _need(all(budgets[k]['value']>=0 and abs(residuals[k]['value'])<=budgets[k]['value'] for k in units),'QC_HOLD: recorded complete ledger exceeds budget')


def _context(raw,model_pins,original,root_program,source_frame):
    value=_parse(raw,MAX);_closed(value,CONTEXT_FIELDS)
    expected={k:v for k,v in model_pins.items() if k not in EXTRAS[-2:]}
    _need(_canonical(value)==raw and value['version']==CROP_VERSION and value['code_sha256']==expected,'CODE_HOLD: original fractional context required')
    source=value['source'];_closed(source,{'version','candidate','program','anchors','past_event_ids','code_sha256','profile_sha256'})
    _need(source['version']=='funded-fractional-structural-birth-point-research-v1'
          and source['program']==source_frame['program'],'CONTEXT_HOLD: original captured source program required')
    _need(source['code_sha256']=={k:v for k,v in model_pins.items()if k not in EXTRAS[-3:]}
          and source['profile_sha256']==leaf.stock.PROFILE_SHA,'CODE_HOLD: original point/profile versions required')
    candidate=source['candidate'];_need(candidate['source_code_sha256']=={k:v for k,v in model_pins.items()if k not in EXTRAS[-4:]}
          and candidate['code_sha256']==model_pins['backend/app/crop_funded_event_state.py']
          and candidate['source_left_checkpoint_sha256']==_digest(source_frame['checkpoint']), 'SOURCE_HOLD: captured candidate source required')
    _need(value['original']==original,'SOURCE_HOLD: captured root/grid/birth bases required')
    program=deepcopy(source['program']);records=value['records'];_need(type(records)is list and 1<=len(records)<=511,'CAPACITY_HOLD: bounded fractional history required')
    for index,row in enumerate(records):
        _closed(row,{'inputs','input_sha256','at','new_leaves','receipts','point_flows','balances','branch_air_integral_at_birth',
            'lifetime_air_integral_at_birth','before_checkpoint_sha256','after_sample_sha256','after_program_sha256'})
        inputs=row['inputs'];keys={'schema_version','input_id','origin','policy','context_sha256','at_elapsed_seconds_exact','model_floor_area','events'}
        _closed(inputs,keys|({'candidate_sha256'}if index==0 else{'checkpoint_sha256'}))
        _need(inputs['schema_version']==('funded-fractional-birth-point-input-v1'if index==0 else'fractional-continuation-birth-input-v1')
              and inputs['origin']=='synthetic'and inputs['policy']==leaf.POLICY and row['input_sha256']==_digest(inputs), 'POINT_HOLD: original fractional point input required')
        _id(inputs['input_id']);stem._elapsed(row['at']);_need(row['at']==inputs['at_elapsed_seconds_exact'],'TIME_HOLD: original point time required')
        if index==0:
            _need(inputs['context_sha256']==_digest(source)and inputs['candidate_sha256']==_digest(candidate)
                  and row['at']==candidate['at']['elapsed_seconds_exact']
                  and row['before_checkpoint_sha256']==candidate['source_left_checkpoint_sha256'],'SOURCE_HOLD: original first point source required')
        _need(inputs['model_floor_area']==program['model_floor_area'] and len(row['new_leaves'])==len(inputs['events'])==len(row['receipts'])>=1,'POINT_HOLD: common floor/complete new leaves required')
        for new,event in zip(row['new_leaves'],inputs['events'],strict=True):
            _closed(event,{'event_id','attachment_internode_id','incoming_temperature','leaf'});_id(event['event_id']);_id(event['attachment_internode_id'])
            _need(new==leaf.stock._float_view(event['leaf']) and new['thermal_age']['value']==0 and new['initial_carbon']['value']>0,'POINT_HOLD: original new leaf declaration required')
        program['leaves'].extend(deepcopy(row['new_leaves']));leaf.stock._program(program)
        leaf.stock._block(row['point_flows'],leaf.POINT_UNITS,normalized=True)
        _closed(row['balances'],leaf.POINT_BALANCE_UNITS)
        for name,unit in leaf.POINT_BALANCE_UNITS.items():
            balance=row['balances'][name];_closed(balance,{'residual','budget'})
            for q in balance.values():leaf.stock._q(q,unit,normalized=True)
            _need(balance['budget']['value']>=0 and abs(balance['residual']['value'])<=balance['budget']['value'],'QC_HOLD: point residual exceeds budget')
        for key in ('before_checkpoint_sha256','after_sample_sha256','after_program_sha256'):_hash(row[key])
    _need(program==value['program'],'CONTEXT_HOLD: exact appended program required')
    _closed(value['seed'],{'sample','branch_base_transfers','branch_step_count','output_cursor','output_prefix_sha256'})
    _need(_digest(value['seed']['sample'])==records[-1]['after_sample_sha256']and _digest(program)==records[-1]['after_program_sha256'],'CONTEXT_HOLD: original after-point seed required')
    return value


def _initial(value,root_program):
    _closed(value,{'schema_version','input_id','origin','context_sha256','leaf_root_sha256','stem_root_sha256',
        'root_initial_state_sha256','model_floor_area','initial_attachments','rights','reviewer'})
    _need(value['schema_version']=='funded-fractional-initial-links-v1'and value['origin']=='synthetic'
          and value['model_floor_area']==root_program['model_floor_area'],'BASIS_HOLD: explicit synthetic initial links required')
    for key in ('input_id','reviewer'):_id(value[key])
    rights=value['rights'];_closed(rights,{'declaration_id','revision','declared_at_utc','ownership_asserted','access','store','use','transform','display','redistribute'})
    for key in ('declaration_id','revision'):_id(rights[key])
    stem._utc(rights['declared_at_utc'])
    _need(type(value['initial_attachments'])is list,'ATTACHMENT_HOLD: explicit initial link list required')
    for row in value['initial_attachments']:
        _closed(row,{'leaf_id','attachment_internode_id'})
        for v in row.values():_id(v)


def _leaf_metadata(program,source_frame,initial,records,dt):
    links={row['leaf_id']:row['attachment_internode_id']for row in initial['initial_attachments']};history={}
    for p,receipt,base in zip(source_frame['program']['leaves'],source_frame['creation_receipts'],source_frame['creation_bases'],strict=True):
        if receipt['kind']!='initial':
            event=receipt['value'];history[p['leaf_id']]=(event['attachment_internode_id'],'original_funded_point',event['event_id'],dt*base['step_index'])
    for record in records:
        for event in record['inputs']['events']:
            history[event['leaf']['leaf_id']]=(event['attachment_internode_id'],'fractional_branch_point',event['event_id'],_frac(record['at']))
    result=[]
    for p in program['leaves']:
        if p['leaf_id']in links:parent,kind,event,birth=links[p['leaf_id']],'explicit_preexisting_initial_link',None,None
        else:parent,kind,event,birth=history[p['leaf_id']]
        result.append({'leaf_id':p['leaf_id'],'attachment_internode_id':parent,'kind':kind,'event_id':event,
            'birth_at_elapsed_seconds_exact':None if birth is None else{'numerator':str(birth.numerator),'denominator':str(birth.denominator),'unit':'s'},
            'curve_sha256':_digest(p['curve'])})
    return result


def _geometry(store,descriptor,packet,frame,node,raws):
    raw=_source(store,descriptor,raws,POINT_MAX);receipt=_parse(raw,POINT_MAX)
    _closed(receipt,{'request','response'});request=point_request(packet,frame,node);response=receipt['response']
    _need(receipt['request']==request,'GEOMETRY_HOLD: original point request required')
    _closed(response,{'model_version','scope','claim_scope','gates','input_sha256','curve_sha256','age_exact','length'})
    _need(response['model_version']==POINT_VERSION and response['scope']=='software_research_only'
          and response['claim_scope']=='synthetic_crop_math_only'and response['gates']=='not_assessed','MODEL_HOLD: original point response required')
    _need(response['input_sha256']==node['point_input_sha256']==_digest({'model_version':POINT_VERSION,'inputs':request})
          and response['curve_sha256']==node['curve_sha256']==_digest({'rate_model_version':'internode-logistic-thermal-rate-research-v1','curve':request['curve']})
          and response['age_exact']==node['age_exact']and response['length']==node['length'],'GEOMETRY_HOLD: point receipt and rendered organ differ')
    _age(node['age_exact']);stem._curve(node['curve']);_quantity(node['length'],'m',positive=True)
    _need(node['length']['value']<=node['curve']['values']['maximum_length']['value'],'GEOMETRY_HOLD: length exceeds original curve maximum')


def _organ_sources(nodes,state,candidate,offset,original):
    fields={'internode_id','sequence','kind','development_birth_seconds_exact','age_exact','curve','curve_sha256',
        'length','point_input_sha256','source_length_state_sha256','initial_anchor'}
    _need(len(nodes)==len(state['internodes'])+(0 if original else 1),'STATE_HOLD: exact selected stem inventory required')
    for node in nodes:_closed(node,fields)
    for node,source in zip(nodes,state['internodes']):
        old=source['length_state']
        _need(node['internode_id']==old['clock_state']['internode_id']and node['sequence']==source['sequence']
              and node['kind']=='selected_original'and node['curve']==old['curve']and node['initial_anchor']==old['anchor']
              and node['source_length_state_sha256']==_digest(old)
              and node['development_birth_seconds_exact']==old['clock_state']['emerged_elapsed_seconds_exact'],
              'SOURCE_HOLD: original organ identity/curve/anchor required')
    if not original:
        node=nodes[-1];timeline=state['timeline_state'];identity={k:timeline[k]for k in ('shoot_id','development_origin_id','schedule_id','started_at')}
        identity.update(sequence=timeline['next_sequence'],birth_age_exact=timeline['next_threshold_exact'])
        _need(node['internode_id']=='internode:'+_digest(identity)and node['sequence']==timeline['next_sequence']
              and node['kind']=='numerical_threshold_birth'and node['source_length_state_sha256']is None
              and node['curve']==state['emergence_profile']['curve'],'SOURCE_HOLD: actual threshold-born organ required')
        stem._elapsed(node['development_birth_seconds_exact'])
        _need(_frac(node['development_birth_seconds_exact'])==offset+_frac(candidate['at']['elapsed_seconds_exact']),
              'TIME_HOLD: actual organ development birth required')


def _load(store,root):
    raws={};root_raw=store.get(root,maximum=MAX);raws[root]=root_raw;m=_parse(root_raw,MAX);_closed(m,ROOT_FIELDS)
    pins=_pins();_need(pins['backend/app/crop_complete_artifact_reader.py']==CODE_SHA256
          and all(m[k]==v for k,v in FLAGS.items())and m['code_sha256']==pins,'CODE_HOLD: current complete artifact version/code required')
    packet_raw=_source(store,m['packet'],raws);packet=_parse(packet_raw,MAX)
    _closed(packet,{'basis','status','segment_receipts','sample_scalars','frames','current_checkpoint_RHS_evaluations','past_ODE_or_clock_advances'})
    basis=packet['basis'];_closed(basis,{'model_version','scope','G0_G4','R2','code_sha256','source_selection','model_floor_area',
        'stem_source_state_sha256','development_origin_utc','simulation_start_development_seconds_exact','initial_bindings','source_rights',
        'equation_reference','new_stem_carbon_allocation','initial_leaf_history'})
    model_pins={k:pins[k]for k in MODEL_SOURCE_PATHS}
    _need(basis['model_version']==MODEL_VERSION and basis['code_sha256']==model_pins and basis['scope']=='software_research_only'
          and basis['G0_G4']=='not_assessed'and basis['R2']=='not_approved'and packet['status']=='completed_software_fixture','SCOPE_HOLD: complete synthetic packet required')
    _need(basis['new_stem_carbon_allocation']=='not_independently_allocated_in_aggregate_stem_pool'
          and basis['initial_leaf_history']=='explicit_carry_over_ages_and_links_not_verified_past_emergence','SCOPE_HOLD: scientific holds must remain explicit')
    selection=basis['source_selection'];leaf_root=selection['leaf_root_sha256'];stem_root=selection['stem_root_sha256']
    lm_raw=store.get(leaf_root,maximum=leaf.MAX);lm=_parse(lm_raw,leaf.MAX);inputs,root_program,_,seed,source_frames,_,source_raws=leaf._graph(store,lm)
    raws.update({sha256(raw).hexdigest():raw for raw in source_raws.values()});raws[leaf_root]=lm_raw
    sm=stem._load_manifest(store,stem_root);raws[stem_root]=store.get(stem_root,maximum=stem.ROOT_MAX)
    _need(all(lm['source_rights'][k]is True and sm['program_rights'][k]is True for k in ('use','display')),'RIGHTS_HOLD: current stored sources cannot be displayed')
    _need(basis['source_rights']=={'leaf':lm['source_rights'],'stem':sm['program_rights']}
          and basis['equation_reference']==sm['equation_reference'],'RIGHTS_HOLD: original source grants/notice required')
    stem_program_raw=store.get(sm['program_sha256'],maximum=stem.PROGRAM_MAX);raws[sm['program_sha256']]=stem_program_raw;stem_program=_parse(stem_program_raw,stem.PROGRAM_MAX)
    si=selection['stem_start_index'];_need(type(si)is int and -1<=si<len(sm['samples']),'INDEX_HOLD: actual stem selection required')
    if si==-1:state=stem_program['initial_state']
    else:
        d=sm['samples'][si];raw=store.get(d['result_sha256'],maximum=stem.RESULT_MAX);raws[d['result_sha256']]=raw;result=_parse(raw,stem.RESULT_MAX);state=result['state']
        _need(_digest(state)==d['state_sha256']and state['timeline_state']['at']==d['at'],'SOURCE_HOLD: actual selected stem state required')
    stem._state(state);_need(_digest(state)==basis['stem_source_state_sha256'],'SOURCE_HOLD: selected stem identity differs')
    _need(basis['model_floor_area']==root_program['model_floor_area']and basis['development_origin_utc']==state['timeline_state']['started_at'],'BASIS_HOLD: original floor/development epoch required')
    delta=stem._utc(state['timeline_state']['at'])-stem._utc(state['timeline_state']['started_at']);offset=Fraction(delta.days*86400+delta.seconds)
    stem._elapsed(basis['simulation_start_development_seconds_exact'])
    _need(_frac(basis['simulation_start_development_seconds_exact'])==offset,'TIME_HOLD: actual simulation/development epoch offset required')
    contexts={};_need(type(m['contexts'])is list and 1<=len(m['contexts'])<=511,'CAPACITY_HOLD: bounded contexts required')
    first_raw=_source(store,m['contexts'][0],raws);first=_parse(first_raw,MAX);candidate=first['source']['candidate'];left=candidate['source_root_certificate']['source_bracket']['left_frame_index']
    _need(type(left)is int and 0<=left<len(source_frames),'INDEX_HOLD: original selected left frame required')
    selected=source_frames[left];original={'root_sample':{'state':seed['state'],'derived':leaf.stock._derived(seed['evaluation'])},
        'root_leaf_ids':[x['leaf_id']for x in root_program['leaves']],'left_checkpoint':selected['checkpoint'],
        'source_birth_bases':selected['creation_bases'],'grid_step_seconds':float(inputs['step_seconds']),'grid_step_count':inputs['step_count']}
    for descriptor in m['contexts']:
        raw=_source(store,descriptor,raws);value=_context(raw,model_pins,original,root_program,selected);contexts[descriptor['sha256']]=value
    _need(len(contexts)==len(m['contexts'])==len(packet['segment_receipts']),'CONTEXT_HOLD: exact unique ordered contexts required')
    initial=basis['initial_bindings'];_initial(initial,root_program);_need(initial['context_sha256']==m['contexts'][0]['sha256']and initial['leaf_root_sha256']==leaf_root
          and initial['stem_root_sha256']==stem_root and initial['root_initial_state_sha256']==lm['initial_state_sha256'],'SOURCE_HOLD: original explicit initial links required')
    links=initial['initial_attachments'];_need([r['leaf_id']for r in links]==[x['leaf_id']for x in root_program['leaves']],'ATTACHMENT_HOLD: complete original root links required')
    rights=initial['rights'];_need(all(rights.get(k)is True for k in ('ownership_asserted','access','store','use','transform','display'))and type(rights.get('redistribute'))is bool,'RIGHTS_HOLD: explicit stored initial-link grants required')
    _need(basis['source_selection']==first['source']['candidate']['selection'],'SOURCE_HOLD: original selected source required')
    frames=packet['frames'];_need(type(frames)is list and len(frames)==len(m['frames'])==len(m['geometry_receipts']) and 1<=len(frames)<=512,'CAPACITY_HOLD: complete bounded frame index required')
    context_order=list(contexts);current_context=-1;previous=None;scalar=0;dense_count=0
    for i,(frame,descriptor,geometry) in enumerate(zip(frames,m['frames'],m['geometry_receipts'],strict=True)):
        evidence=frame['evidence'];kind=evidence['kind'];dense=kind=='checked_dense_candidate'
        _closed(frame,FRAME_FIELDS|({'snapshot','lifetime_integrated_transfers','lifetime_point_transfers','ledgers'}if dense else set()))
        _need(descriptor==frame_descriptor(i,frame)and type(frame['output_cursor'])is int and frame['output_cursor']==i+1,'SEQUENCE_HOLD: original indexed cursor/frame required')
        at=frame['at'];_closed(at,{'time_origin_utc','elapsed_seconds_exact'});stem._elapsed(at['elapsed_seconds_exact']);elapsed=_frac(at['elapsed_seconds_exact'])
        _need(at['time_origin_utc']==lm['time_origin_utc']==state['timeline_state']['at'],'TIME_HOLD: original source epoch required')
        cp=evidence['checkpoint']
        if kind=='original_funded_checkpoint':
            _closed(evidence,{'kind','source_frame_index','checkpoint_sha256','checkpoint'})
            _need(i<=left and evidence['source_frame_index']==i and cp==source_frames[i]['checkpoint']and evidence['checkpoint_sha256']==lm['samples'][i]['checkpoint_sha256'],'SOURCE_HOLD: original prefix checkpoint required')
            program=source_frames[i]['program'];_need(frame['phase']==lm['samples'][i]['phase']and frame['event_sequence']==lm['samples'][i]['event_sequence'],'SEQUENCE_HOLD: original source phase required')
            _need(at['elapsed_seconds_exact']==lm['samples'][i]['elapsed_seconds_exact']
                  and frame['output_prefix_sha256']==cp['output_prefix_sha256'],'TIME_HOLD: exact original source time/prefix required')
            _need(frame['quantities_storage']=='checkpoint','STATE_HOLD: original checkpoint authority required')
            metadata_source=source_frames[i];records=[]
        elif dense:
            _closed(evidence,{'kind','candidate_sha256','candidate','checkpoint_sha256','checkpoint'});dense_count+=1
            _need(i==left+1 and cp is None and evidence['checkpoint_sha256']is None and evidence['candidate']==candidate and evidence['candidate_sha256']==_digest(candidate),'SOURCE_HOLD: actual CP-less numerical candidate required')
            _need(frame['phase']=='before_birth'and frame['snapshot']=={k:first['branch_initial'][k]for k in ('state','derived','curve_residuals','curve_invariant_changes')},'STATE_HOLD: original dense before state required')
            program=first['source']['program'];_need(at==candidate['at'],'TIME_HOLD: original candidate time required')
            _need(frame['quantities_storage']=='source_prefix_plus_dense_partial','STATE_HOLD: explicit numerical candidate required')
            metadata_source=selected;records=[]
            expected_prefix=_prefix(previous['output_prefix_sha256'],first['branch_initial'],frame['event_sequence'],'before_birth')
            _need(frame['output_prefix_sha256']==expected_prefix,'PREFIX_HOLD: source-to-dense prefix differs')
        else:
            _need(kind=='fractional_checkpoint','MODEL_HOLD: known complete evidence kind required')
            _closed(evidence,{'kind','context_sha256','checkpoint_sha256','checkpoint'});_closed(cp,CP_FIELDS)
            _need(cp['version']==CP_VERSION and cp['scope']=='software_research_only'and cp['G0_G4']=='not_assessed'
                  and cp['context_sha256']==evidence['context_sha256']and _digest(cp)==evidence['checkpoint_sha256'],'HASH_HOLD: original fractional checkpoint required')
            _need(all(type(cp[k])is int and cp[k]>=0 for k in ('grid_step_index','segment_steps','branch_steps','event_sequence','output_cursor'))
                  and frame['quantities_storage']=='checkpoint','SEQUENCE_HOLD: typed original checkpoint counters required')
            if current_context<0 or evidence['context_sha256']!=context_order[current_context]:
                current_context+=1;_need(current_context<len(context_order)and evidence['context_sha256']==context_order[current_context],'CONTEXT_HOLD: original context order required')
                context=contexts[evidence['context_sha256']];record=context['records'][-1]
                _need(len(context['records'])==current_context+1 and cp['segment_steps']==0 and cp['last_confirmed']==context['seed']['sample'],'CONTEXT_HOLD: original point seed required')
                _need(packet['segment_receipts'][current_context]['context_sha256']==evidence['context_sha256'],'CONTEXT_HOLD: original segment receipt required')
                if current_context:
                    prior_context=contexts[context_order[current_context-1]]
                    _need(context['records'][:-1]==prior_context['records']and record['before_checkpoint_sha256']==previous['evidence']['checkpoint_sha256']
                          and record['inputs']['context_sha256']==context_order[current_context-1],'EVENT_HOLD: point must extend exact prior context/CP')
                leaf._receipts({'birth_receipts':record['receipts'],'after_sample':cp['last_confirmed']},record['inputs'],context['program'])
                expected_phase='after_birth';_need(at==previous['at']and frame['event_sequence']==previous['event_sequence']+(0 if current_context==0 else 1),'TIME_HOLD: exact same-time point sequence required')
            else:
                context=contexts[evidence['context_sha256']];_need(cp['segment_steps']==previous['evidence']['checkpoint']['segment_steps']+1,'SEQUENCE_HOLD: every branch integration step required');expected_phase='grid_endpoint'
                _need(elapsed>_frac(previous['at']['elapsed_seconds_exact'])and frame['event_sequence']==previous['event_sequence'],'TIME_HOLD: forward original grid required')
            _need(frame['phase']==cp['phase']==expected_phase and frame['event_sequence']==cp['event_sequence']and frame['output_cursor']==cp['output_cursor']and at==cp['at'],'SEQUENCE_HOLD: current raw CP and descriptor differ')
            _need(frame['output_prefix_sha256']==cp['output_prefix_sha256']==_prefix(previous['output_prefix_sha256'],cp['last_confirmed'],cp['event_sequence'],expected_phase),'PREFIX_HOLD: exact preceding fractional prefix required')
            program=context['program'];leaf.stock._block(cp['segment_integrated_transfers'],leaf.stock._flux_units(program),normalized=True)
            _need(cp['branch_steps']==context['seed']['branch_step_count']+cp['segment_steps'],'SEQUENCE_HOLD: original branch step lineage required')
            metadata_source=selected;records=context['records']
            for key in ('branch_integrated_transfers','lifetime_integrated_transfers'):leaf.stock._block(cp[key],leaf.stock._flux_units(program),normalized=True)
            for key in ('branch_point_transfers','lifetime_point_transfers'):leaf.stock._block(cp[key],leaf.POINT_UNITS,normalized=True)
            for prefix in ('branch','global'):_qcs(cp[prefix+'_balance_residuals'],cp[prefix+'_balance_budgets'],program)
            _need(cp['at']['elapsed_seconds_exact']==context['seed']['sample']['at']['elapsed_seconds_exact'] if cp['segment_steps']==0 else elapsed==Fraction.from_float(original['grid_step_seconds'])*(int(_frac(context['seed']['sample']['at']['elapsed_seconds_exact'])//Fraction.from_float(original['grid_step_seconds']))+cp['segment_steps']),'TIME_HOLD: original remainder grid coordinate required')
        snapshot=_snapshot(frame);leaf.stock._state(snapshot['state'],program);leaf.stock._block(snapshot['derived'],leaf.stock.DERIVED_UNITS,normalized=True)
        _need(frame['leaves']==_leaf_metadata(program,metadata_source,initial,records,Fraction.from_float(original['grid_step_seconds'])),
              'ATTACHMENT_HOLD: original ordered leaf event/parent history required')
        _need(frame['program_sha256']==_digest(program)and len(frame['leaves'])==len(program['leaves']),'STATE_HOLD: exact program/leaf inventory required')
        leaf.stock._block(_flows(frame),leaf.stock._flux_units(program),normalized=True);qcs=_ledgers(frame);_qcs(qcs['balance_residuals'],qcs['balance_budgets'],program)
        shoot=frame['shoot'];_closed(shoot,{'internodes','shoot_age_exact','birth','next_threshold_exact','tracked_axis_length'});_age(shoot['shoot_age_exact']);_age(shoot['next_threshold_exact'],positive=True)
        nodes=shoot['internodes'];_need(type(nodes)is list and 1<=len(nodes)<=512 and len(nodes)==len(geometry),'CAPACITY_HOLD: complete bounded geometry receipts required')
        _organ_sources(nodes,state,candidate,offset,kind=='original_funded_checkpoint')
        parents={node['internode_id']:node for node in nodes};_need(len(parents)==len(nodes),'STATE_HOLD: unique actual organ IDs required')
        for node,receipt in zip(nodes,geometry,strict=True):_geometry(store,receipt,packet,frame,node,raws)
        _quantity(shoot['tracked_axis_length'],'m',positive=True);_need(shoot['tracked_axis_length']['value']==fsum(node['length']['value']for node in nodes),'STATE_HOLD: original tracked axis sum required')
        n=len(frame['leaves']);y=snapshot['state']
        for j,(row,p)in enumerate(zip(frame['leaves'],program['leaves'],strict=True)):
            _closed(row,{'leaf_id','attachment_internode_id','kind','event_id','birth_at_elapsed_seconds_exact','curve_sha256'})
            _need(row['leaf_id']==p['leaf_id']and row['curve_sha256']==_digest(p['curve'])and row['attachment_internode_id']in parents,'ATTACHMENT_HOLD: exact actual leaf/curve/parent required')
            birth=Fraction(0)if row['birth_at_elapsed_seconds_exact']is None else _frac(row['birth_at_elapsed_seconds_exact'])
            _need(_frac(parents[row['attachment_internode_id']]['development_birth_seconds_exact'])<=_frac(basis['simulation_start_development_seconds_exact'])+birth<=_frac(basis['simulation_start_development_seconds_exact'])+elapsed,'ATTACHMENT_HOLD: parent must precede its leaf')
        _quantity(frame['tracked_leaf_area'],'m2',positive=True);_need(frame['tracked_leaf_area']['value']==fsum(y[107+n:107+2*n]),'STATE_HOLD: original tracked leaf area required')
        scalar+=len(y)+2*n+8;previous=frame
    _need(dense_count==1 and current_context+1==len(contexts)and scalar==packet['sample_scalars']<=32768
          and _frac(frames[0]['at']['elapsed_seconds_exact'])==0 and _frac(frames[-1]['at']['elapsed_seconds_exact'])==Fraction.from_float(original['grid_step_seconds'])*original['grid_step_count'],'INCOMPLETE_HOLD: complete original horizon/scalar budget required')
    _need(packet['past_ODE_or_clock_advances']==0,'SCOPE_HOLD: no past replay claim required')
    for descriptor in m['source_blobs']:_source(store,descriptor,raws,16*1024**2)
    return m,packet,raws


def _fence(store,m,raws):
    _need(m['code_sha256']==_pins()and m['code_sha256']['backend/app/crop_complete_artifact_reader.py']==CODE_SHA256,'CODE_HOLD: artifact dependencies changed before read return')
    for digest,raw in raws.items():_need(store.get(digest,maximum=max(MAX,len(raw)))==raw,'SOURCE_HOLD: original artifact source changed')
    _need(m['code_sha256']==_pins(),'CODE_HOLD: artifact dependencies changed during final fence')


def _read(directory,access,root,index,*,packet_only=False):
    try:
        _hash(root)
        with MorphologyBlobStore(directory,access)as store:
            m,packet,raws=_load(store,root)
            if packet_only:value=deepcopy(packet)
            elif index is None:value=deepcopy(m)
            else:
                _need(type(index)is int and 0<=index<len(packet['frames']),'INDEX_HOLD: actual complete frame index required')
                frame=deepcopy(packet['frames'][index]);snapshot=_snapshot(frame);n=len(frame['leaves']);y=snapshot['state']
                leaves=[{**row,'thermal_age':{'value':y[107+j],'unit':'degC_day'},'area':{'value':y[107+n+j],'unit':'m2'},
                    'carbohydrate':{'value':y[107+2*n+j],'unit':'mg_CH2O/m2_floor'}}for j,row in enumerate(frame['leaves'])]
                value={'schema_version':'complete-crop-replay-frame-v1','artifact_sha256':root,'index':index,'basis':deepcopy(packet['basis']),
                    'frame':frame,'snapshot':deepcopy(snapshot),'leaves':leaves,'lifetime_integrated_transfers':deepcopy(_flows(frame)),'ledgers':deepcopy(_ledgers(frame))}
            _fence(store,m,raws)
            return value
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise CompleteCropArtifactHold(str(error))from None


def read_complete_crop_manifest(directory,access,root_sha256):return _read(directory,access,root_sha256,None)


def read_complete_crop_packet(directory,access,root_sha256):return _read(directory,access,root_sha256,None,packet_only=True)


def read_complete_crop_frame(directory,access,root_sha256,*,index):return _read(directory,access,root_sha256,index)
