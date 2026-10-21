"""Compute-free manifest validation; frame projection is a separate next slice."""
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
