"""Compute-free manifest validation and original stored leaf population frames."""
from .crop_morphology_artifact_io import MorphologyBlobStore,_need
from .crop_morphology_artifact_reader import _canonical,_closed,_hash,_id,_parse,_quantity,_utc,PROGRAM_MAX
from .crop_leaf_artifact_reader import (MAX,MODEL_VERSIONS,SOURCE_PATHS as LEAF_SOURCE_PATHS,DISPLAY_POLICY,
                                       _program as _initial_program,_rights,_exact,_clock,_curve)
from .crop_rational_morphology_artifact_reader import _load_manifest as _stem_manifest


SOURCE_PATHS=tuple(dict.fromkeys((*LEAF_SOURCE_PATHS,*(f'backend/app/{name}.py' for name in (
    'crop_declared_leaf_births','crop_leaf_population','crop_leaf_stem_binding','crop_leaf_population_artifact_producer')))))
POPULATION_DISPLAY_POLICY={**DISPLAY_POLICY,'leaf_count':'declared_initial_and_births_only'}
POPULATION_MODEL_VERSIONS={**MODEL_VERSIONS,'births':'declared-leaf-births-research-v1',
    'population':'declared-leaf-population-research-v1','binding':'stored-leaf-stem-attachment-binding-research-v1',
    'producer':'leaf-population-artifact-producer-research-v1'}
ROOT_CONSTANTS={'schema_version':'leaf-population-research-artifact-v1','status':'completed_software_fixture',
    'scope':'software_research_only','claim_scope':'synthetic_crop_math_only','gates':'not_assessed',
    'time_kind':'synthetic_model_clock_not_observation','parameter_scope':'synthetic_software_fixture_only',
    'model_versions':POPULATION_MODEL_VERSIONS,'display_policy':POPULATION_DISPLAY_POLICY}
ROOT_FIELDS=set(ROOT_CONSTANTS)|{'program_sha256','program_bytes','program_rights','stem_artifact_sha256','stem_program_sha256',
    'code_sha256','time_origin_utc','initial_at_elapsed_seconds_exact','initial_state_sha256','terminal_state_sha256','samples'}
EVENT_KEYS={'leaf_id','attachment_internode_id','emerged_elapsed_seconds_exact','base_temperature','curve','normalization','initial_area'}


def _seconds(at,origin):
    delta=_utc(at)-_utc(origin);return delta.days*86400+delta.seconds


def _program(p,stem_program):
    _closed(p,{'schema_version','origin','program_id','rights','stem','initialization','births','display_policy'})
    _need(p['schema_version']=='leaf-population-software-program-v1' and p['origin']=='synthetic'
          and p['display_policy']==POPULATION_DISPLAY_POLICY,'SCOPE_HOLD: supported population input required')
    _id(p['program_id']);_rights(p['rights']);_closed(p['initialization'],{'input_id','initial_inventory'});_id(p['initialization']['input_id'])
    legacy={'schema_version':'leaf-software-program-v1','origin':'synthetic','program_id':p['program_id'],
        'rights':p['rights'],'stem':p['stem'],'initialization':p['initialization']['initial_inventory'],'display_policy':DISPLAY_POLICY}
    meta=_initial_program(legacy);timeline=stem_program['initial_state']['timeline_state'];origin=timeline['started_at']
    start=_exact(meta['initial_at_elapsed_seconds_exact'],'s');end=_seconds(stem_program['segments'][-1]['end_utc'],origin)
    _need(meta['time_origin_utc']==origin and start==_seconds(timeline['at'],origin),'TIME_HOLD: population and original stem start differ')
    seen={d['leaf_id'] for d in meta['declared_leaves']};events=p['births']
    _need(type(events) is list and len(seen)+len(events)<=512,'CAPACITY_HOLD: bounded full population required')
    previous=start
    for event in events:
        _closed(event,EVENT_KEYS);_id(event['leaf_id']);_id(event['attachment_internode_id']);birth=_exact(event['emerged_elapsed_seconds_exact'],'s')
        _need(start<birth<=end and birth>=previous and event['leaf_id'] not in seen,'STATE_HOLD: ordered unique population births required')
        previous=birth;seen.add(event['leaf_id']);_curve(event['curve']);_quantity(event['initial_area'],'m2',positive=True)
        _need(event['normalization']=='zero_lower_asymptote_sigmoid_v1','MODEL_HOLD: explicit population normalization required')
        _clock({'origin':'synthetic','age_basis':'since_leaf_emergence','temperature_basis':'indoor_air_piecewise_constant',
            'leaf_id':event['leaf_id'],'time_origin_utc':origin,'emerged_elapsed_seconds_exact':event['emerged_elapsed_seconds_exact'],
            'at_elapsed_seconds_exact':event['emerged_elapsed_seconds_exact'],'base_temperature':event['base_temperature'],
            'age_exact':{'numerator':'0','denominator':'1','unit':'degC_day'}})
    return meta


def read_leaf_population_manifest(directory,access,root_sha256):
    with MorphologyBlobStore(directory,access) as store:
        raw=store.get(root_sha256,maximum=MAX);manifest=_parse(raw,MAX);_closed(manifest,ROOT_FIELDS)
        _need(_canonical(manifest)==raw and all(manifest[k]==v for k,v in ROOT_CONSTANTS.items()),'MODEL_HOLD: supported population manifest required')
        _closed(manifest['code_sha256'],SOURCE_PATHS)
        for value in manifest['code_sha256'].values():_hash(value)
        raw=store.get(manifest['program_sha256'],maximum=MAX)
        _need(type(manifest['program_bytes']) is int and len(raw)==manifest['program_bytes'],'HASH_HOLD: population program bytes differ')
        p=_parse(raw,MAX);_need(_canonical(p)==raw,'FORMAT_HOLD: canonical population program required')
        stem=_stem_manifest(store,manifest['stem_artifact_sha256']);stem_raw=store.get(stem['program_sha256'],maximum=PROGRAM_MAX)
        meta=_program(p,_parse(stem_raw,PROGRAM_MAX))
        _need(manifest['program_rights']==p['rights'] and manifest['stem_artifact_sha256']==p['stem']['artifact_sha256']
              and manifest['stem_program_sha256']==p['stem']['program_sha256']==stem['program_sha256']
              and manifest['time_origin_utc']==meta['time_origin_utc']
              and manifest['initial_at_elapsed_seconds_exact']==meta['initial_at_elapsed_seconds_exact'],
              'HASH_HOLD: population program or original stem metadata differ')
        _hash(manifest['initial_state_sha256']);previous=manifest['initial_state_sha256'];samples=manifest['samples']
        _need(type(samples) is list and len(samples)==len(stem['samples']),'FORMAT_HOLD: complete population descriptor chain required')
        for index,(descriptor,original) in enumerate(zip(samples,stem['samples'],strict=True)):
            _closed(descriptor,{'index','at','result_sha256','result_bytes','binding_sha256','binding_bytes',
                                'input_state_sha256','state_sha256','input_sha256','stem_result_sha256'})
            _need(type(descriptor['index']) is int and descriptor['index']==index and descriptor['at']==original['at']
                  and descriptor['stem_result_sha256']==original['result_sha256'] and descriptor['input_state_sha256']==previous,
                  'HASH_HOLD: original population/stem sample chain differs')
            for key in ['result_bytes','binding_bytes']:
                _need(type(descriptor[key]) is int and 0<descriptor[key]<=MAX,'CAPACITY_HOLD: bounded population sample required')
            for key in ['result_sha256','binding_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256']:_hash(descriptor[key])
            previous=descriptor['state_sha256']
        _need(manifest['terminal_state_sha256']==previous,'HASH_HOLD: terminal population chain differs')
        return manifest


def _digest(value):
    from hashlib import sha256
    return sha256(_canonical(value)).hexdigest()


def _leaf_state(current,initial,origin,at):
    from sys import float_info
    from .crop_leaf_artifact_reader import CLOCK_KEYS
    _closed(current,{'model_version','clock_state','area_state','clock_anchor'})
    _need(current['model_version']==MODEL_VERSIONS['leaf_state'],'MODEL_HOLD: supported stored leaf state required')
    clock,anchor_clock,area=current['clock_state'],current['clock_anchor'],current['area_state'];_clock(clock);_clock(anchor_clock)
    _need(anchor_clock==initial['clock_state'] and all(clock[k]==anchor_clock[k] for k in CLOCK_KEYS-{'at_elapsed_seconds_exact','age_exact'})
          and clock['time_origin_utc']==origin and clock['at_elapsed_seconds_exact']==at,'STATE_HOLD: original leaf clock anchor required')
    now,first=(_exact(q['at_elapsed_seconds_exact'],'s') for q in [clock,anchor_clock])
    age,initial_age=(_exact(q['age_exact'],'degC_day') for q in [clock,anchor_clock])
    _need(now>=first and age>=initial_age and (now!=first or age==initial_age),'TIME_HOLD: current leaf predates original checkpoint')
    _closed(area,{'model_version','origin','thermal_age_basis','normalization','leaf_id','curve','curve_sha256','age_exact','area','anchor'})
    _need(area['model_version']==MODEL_VERSIONS['area'] and area['origin']=='synthetic'
          and area['thermal_age_basis']=='since_leaf_emergence' and area['normalization']==initial['normalization']=='zero_lower_asymptote_sigmoid_v1'
          and area['leaf_id']==clock['leaf_id'] and area['age_exact']==clock['age_exact'],'STATE_HOLD: original leaf area identity required')
    curve_sha=_curve(initial['curve'])
    _need(_curve(area['curve'])==area['curve_sha256']==curve_sha,'HASH_HOLD: original declared leaf curve required')
    anchor=area['anchor'];_closed(anchor,{'leaf_id','age_exact','curve_sha256','requested_area','canonical_area'})
    for q in [area['area'],anchor['requested_area'],anchor['canonical_area']]:_quantity(q,'m2',positive=True)
    _need(anchor['leaf_id']==clock['leaf_id'] and anchor['age_exact']==anchor_clock['age_exact']
          and anchor['curve_sha256']==curve_sha and anchor['requested_area']==initial['initial_area'],
          'STATE_HOLD: original requested leaf area receipt required')
    _need(float_info.min<=anchor['canonical_area']['value']<=area['area']['value']<=area['curve']['values']['maximum_area']['value'],
          'STATE_HOLD: normal monotone bounded stored leaf area required')
    return {'leaf_id':clock['leaf_id'],'emerged_elapsed_seconds_exact':clock['emerged_elapsed_seconds_exact'],
            'age_exact':clock['age_exact'],'area':area['area'],'curve_sha256':curve_sha}


def _population_leaves(result,program,manifest,stem,index):
    from .crop_morphology_artifact_reader import FLAGS
    _closed(result,{'model_version',*FLAGS,'input_sha256','state','tracked_leaf_count','new_leaf_count','tracked_leaf_area'})
    _need(result['model_version']==POPULATION_MODEL_VERSIONS['population'] and all(result[k]==v for k,v in FLAGS.items()),
          'MODEL_HOLD: supported stored population result required')
    _hash(result['input_sha256']);state=result['state']
    _closed(state,{'model_version','time_origin_utc','at_elapsed_seconds_exact','initial_inventory_state','new_leaves','birth_inventory'})
    origin=manifest['time_origin_utc'];elapsed=_seconds(stem['at'],origin);at=state['at_elapsed_seconds_exact']
    _need(state['model_version']==POPULATION_MODEL_VERSIONS['population'] and state['time_origin_utc']==stem['time_origin_utc']==origin
          and _exact(at,'s')==elapsed,'TIME_HOLD: original population/stem UTC required')
    initial=state['initial_inventory_state'];source=program['initialization']['initial_inventory']
    _closed(initial,{'model_version','origin','time_origin_utc','at_elapsed_seconds_exact','initial_inventory','leaves'})
    _need(initial['model_version']==MODEL_VERSIONS['inventory'] and initial['origin']=='synthetic'
          and initial['time_origin_utc']==origin and initial['at_elapsed_seconds_exact']==at,'STATE_HOLD: initial population scope mismatch')
    refs=[{'leaf_id':q['initialization']['clock_state']['leaf_id'],'attachment_internode_id':q['attachment_internode_id']} for q in source['leaves']]
    _need(initial['initial_inventory']=={'at_elapsed_seconds_exact':source['at_elapsed_seconds_exact'],'leaf_attachments':refs}
          and type(initial['leaves']) is list and len(initial['leaves'])==len(refs),'STATE_HOLD: original initial leaf inventory required')
    leaves=[]
    for item,declared in zip(initial['leaves'],source['leaves'],strict=True):
        _closed(item,{'attachment_internode_id','state'})
        _need(item['attachment_internode_id']==declared['attachment_internode_id'],'STATE_HOLD: original initial leaf attachment required')
        leaves.append({'attachment_internode_id':item['attachment_internode_id'],**_leaf_state(item['state'],declared['initialization'],origin,at)})
    events=[event for event in program['births'] if _exact(event['emerged_elapsed_seconds_exact'],'s')<=elapsed]
    _need(type(state['new_leaves']) is list and len(state['new_leaves'])==len(events),'STATE_HOLD: complete declared births at selected UTC required')
    inventory=[]
    for item,event in zip(state['new_leaves'],events,strict=True):
        _closed(item,{'declaration','declaration_sha256','state'});digest=_digest(event)
        _need(item['declaration_sha256']==_digest(item['declaration'])==digest,'HASH_HOLD: original birth declaration required')
        inventory.append({'leaf_id':event['leaf_id'],'declaration_sha256':digest})
        clock={'origin':'synthetic','age_basis':'since_leaf_emergence','temperature_basis':'indoor_air_piecewise_constant',
            'leaf_id':event['leaf_id'],'time_origin_utc':origin,'emerged_elapsed_seconds_exact':event['emerged_elapsed_seconds_exact'],
            'at_elapsed_seconds_exact':event['emerged_elapsed_seconds_exact'],'base_temperature':event['base_temperature'],
            'age_exact':{'numerator':'0','denominator':'1','unit':'degC_day'}}
        declaration={'clock_state':clock,**{k:event[k] for k in ['curve','normalization','initial_area']}}
        leaves.append({'attachment_internode_id':event['attachment_internode_id'],**_leaf_state(item['state'],declaration,origin,at)})
    _need(state['birth_inventory']==inventory,'STATE_HOLD: original birth inventory required')
    previous=_exact(manifest['initial_at_elapsed_seconds_exact'],'s') if index==0 else _seconds(manifest['samples'][index-1]['at'],origin)
    new_count=sum(previous<_exact(event['emerged_elapsed_seconds_exact'],'s')<=elapsed for event in events)
    _need(type(result['new_leaf_count']) is int and result['new_leaf_count']==new_count and type(result['tracked_leaf_count']) is int
          and result['tracked_leaf_count']==len(leaves),'STATE_HOLD: original selected leaf counts required')
    _quantity(result['tracked_leaf_area'],'m2',positive=True);parents={q['internode_id']:q for q in stem['internodes']}
    for item in leaves:
        parent=parents.get(item['attachment_internode_id'])
        _need(parent is not None and _exact(parent['emerged_elapsed_seconds_exact'],'s')<=_exact(item['emerged_elapsed_seconds_exact'],'s')<=elapsed,
              'ATTACHMENT_HOLD: leaf absent from or preceding original stem')
    return leaves


def read_leaf_population_frame(directory,access,root_sha256,*,index):
    from .crop_morphology_artifact_reader import FLAGS
    from .crop_rational_morphology_artifact_reader import read_rational_morphology_frame
    manifest=read_leaf_population_manifest(directory,access,root_sha256)
    _need(type(index) is int and 0<=index<len(manifest['samples']),'INDEX_HOLD: explicit bounded population frame index required')
    descriptor=manifest['samples'][index]
    with MorphologyBlobStore(directory,access) as store:
        program=_parse(store.get(manifest['program_sha256'],maximum=MAX),MAX)
        raw=store.get(descriptor['result_sha256'],maximum=MAX);result=_parse(raw,MAX)
        _need(len(raw)==descriptor['result_bytes'] and _canonical(result)==raw and _digest(result.get('state'))==descriptor['state_sha256']
              and result.get('input_sha256')==descriptor['input_sha256'],'HASH_HOLD: original stored population result required')
        stem=read_rational_morphology_frame(directory,access,manifest['stem_artifact_sha256'],index=index)
        leaves=_population_leaves(result,program,manifest,stem,index)
        binding={'model_version':POPULATION_MODEL_VERSIONS['binding'],**FLAGS,'population_state_sha256':descriptor['state_sha256'],
            'stem_artifact_sha256':manifest['stem_artifact_sha256'],'stem_result_sha256':stem['result_sha256'],'at':stem['at'],
            'time_origin_utc':manifest['time_origin_utc'],'at_elapsed_seconds_exact':result['state']['at_elapsed_seconds_exact'],
            'tracked_leaf_count':result['tracked_leaf_count'],'tracked_leaf_area':result['tracked_leaf_area'],
            'leaves':[{k:v for k,v in item.items() if k!='curve_sha256'} for item in leaves],'stem':stem}
        raw=store.get(descriptor['binding_sha256'],maximum=MAX)
        _need(len(raw)==descriptor['binding_bytes'] and raw==_canonical(binding),'HASH_HOLD: stored binding differs from original numeric result')
        frame={'schema_version':'leaf-population-replay-frame-v1',**FLAGS,'artifact_sha256':root_sha256,
            'result_sha256':descriptor['result_sha256'],'binding_sha256':descriptor['binding_sha256'],'input_sha256':result['input_sha256'],
            'index':index,'at':stem['at'],'time_origin_utc':manifest['time_origin_utc'],'tracked_leaf_count':result['tracked_leaf_count'],
            'tracked_leaf_area':result['tracked_leaf_area'],'leaves':leaves,'stem':stem}
        _need(len(_canonical(frame))<=MAX,'CAPACITY_HOLD: bounded population frame required');return frame
