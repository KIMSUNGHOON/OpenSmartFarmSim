"""Immutable owned leaf population results; query/export are separate boundaries."""
from pathlib import Path
from hashlib import sha256

from . import crop_leaf_population as population
from .crop_leaf_stem_binding import MODEL_VERSION as BINDING_VERSION,LeafStemBindingHold,bind_leaf_population_to_stored_stem
from .crop_declared_leaf_births import MODEL_VERSION as BIRTH_VERSION,DeclaredLeafBirthHold
from .crop_leaf_artifact_reader import MAX,MODEL_VERSIONS,SOURCE_PATHS as LEAF_SOURCE_PATHS,DISPLAY_POLICY,_rights,_exact
from .crop_leaf_artifact_producer import _forcing,_seconds
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need
from .crop_morphology_artifact_reader import _canonical,_closed,_hash,_id,_parse,PROGRAM_MAX,ROOT_MAX,RESULT_MAX
from .crop_rational_morphology_artifact_reader import read_rational_morphology_manifest


MODEL_VERSION='leaf-population-artifact-producer-research-v1'
SOURCE_PATHS=tuple(dict.fromkeys((*LEAF_SOURCE_PATHS,*(f'backend/app/{name}.py' for name in (
    'crop_declared_leaf_births','crop_leaf_population','crop_leaf_stem_binding','crop_leaf_population_artifact_producer')))))
POPULATION_DISPLAY_POLICY={**DISPLAY_POLICY,'leaf_count':'declared_initial_and_births_only'}
POPULATION_MODEL_VERSIONS={**MODEL_VERSIONS,'births':BIRTH_VERSION,'population':population.MODEL_VERSION,
                           'binding':BINDING_VERSION,'producer':MODEL_VERSION}
ROOT_CONSTANTS={'schema_version':'leaf-population-research-artifact-v1','status':'completed_software_fixture',
    'scope':'software_research_only','claim_scope':'synthetic_crop_math_only','gates':'not_assessed',
    'time_kind':'synthetic_model_clock_not_observation','parameter_scope':'synthetic_software_fixture_only',
    'model_versions':POPULATION_MODEL_VERSIONS,'display_policy':POPULATION_DISPLAY_POLICY}


def _digest(value):return sha256(_canonical(value)).hexdigest()


def _code_pins():
    root=Path(__file__).resolve().parents[2]
    try:return {name:sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError:raise MorphologyArtifactHold('CODE_HOLD: population source unavailable') from None


def _program(raw):
    p=_parse(raw,MAX);_closed(p,{'schema_version','origin','program_id','rights','stem','initialization','births','display_policy'})
    _need(p['schema_version']=='leaf-population-software-program-v1' and p['origin']=='synthetic'
          and p['display_policy']==POPULATION_DISPLAY_POLICY,'SCOPE_HOLD: supported owned population program required')
    _id(p['program_id']);_rights(p['rights']);_closed(p['stem'],{'artifact_sha256','program_sha256'})
    for value in p['stem'].values():_hash(value)
    _need(type(p['births']) is list and len(p['births'])<=512,'CAPACITY_HOLD: bounded population births required')
    return p


def produce_leaf_population_artifact(directory,access,*,stem_directory,program_raw):
    _need(Path(directory).resolve()!=Path(stem_directory).resolve(),'STORAGE_HOLD: separate population directory required')
    p=_program(program_raw);pins=_code_pins();old=read_rational_morphology_manifest(stem_directory,access,p['stem']['artifact_sha256'])
    _need(old['program_sha256']==p['stem']['program_sha256'],'HASH_HOLD: original stem program required')
    with MorphologyBlobStore(stem_directory,access) as original,MorphologyBlobStore(directory,access,write=True) as store:
        stem_raw=original.get(old['program_sha256'],maximum=PROGRAM_MAX);stem_program=_parse(stem_raw,PROGRAM_MAX)
        timeline=stem_program['initial_state']['timeline_state'];origin=timeline['started_at'];previous=timeline['at']
        try:
            state=population.initialize_leaf_population(inputs=p['initialization'])['state']
            _need(state['time_origin_utc']==origin and state['at_elapsed_seconds_exact']==_seconds(previous,origin),
                  'TIME_HOLD: initial population and original stem differ')
            seen={item['state']['clock_state']['leaf_id'] for item in state['initial_inventory_state']['leaves']}
            _need(len(seen)+len(p['births'])<=512,'CAPACITY_HOLD: 1-512 total declared population leaves required')
            last=_exact(state['at_elapsed_seconds_exact'],'s');end=_exact(_seconds(stem_program['segments'][-1]['end_utc'],origin),'s')
            for event in p['births']:
                initial=population._declared_initialization(event,origin);identifier=initial['clock_state']['leaf_id']
                birth=_exact(event['emerged_elapsed_seconds_exact'],'s')
                _need(_exact(state['at_elapsed_seconds_exact'],'s')<birth<=end and birth>=last and identifier not in seen,
                      'TIME_HOLD: ordered unique births inside original program required')
                seen.add(identifier);last=birth
        except (population.LeafPopulationHold,population.leaf.RationalLeafAreaHold) as exc:
            raise MorphologyArtifactHold(str(exc)) from None
        blobs=[(p['stem']['artifact_sha256'],ROOT_MAX),(old['program_sha256'],PROGRAM_MAX),
               *((d['result_sha256'],RESULT_MAX) for d in old['samples'])]
        for digest,maximum in blobs:
            _need(store.put(original.get(digest,maximum=maximum),maximum=maximum)==digest,'HASH_HOLD: original stem copy mismatch')
        program_sha=store.put(program_raw,maximum=MAX);initial_sha=_digest(state);samples=[]
        for index,descriptor in enumerate(old['samples']):
            _need(_code_pins()==pins,'CODE_HOLD: population source changed during calculation')
            start=_exact(state['at_elapsed_seconds_exact'],'s');end=_exact(_seconds(descriptor['at'],origin),'s');before=_digest(state)
            chosen=[event for event in p['births'] if start<_exact(event['emerged_elapsed_seconds_exact'],'s')<=end]
            try:
                result=population.advance_leaf_population(inputs={'input_id':_digest({'program_id':p['program_id'],'at':descriptor['at']}),
                    'state':state,'segments':_forcing(stem_program['segments'],origin,previous,descriptor['at']),'births':chosen})
                state=result['state'];binding=bind_leaf_population_to_stored_stem(directory,access,p['stem']['artifact_sha256'],
                                                                                index=index,population_state=state)
            except (population.LeafPopulationHold,LeafStemBindingHold,DeclaredLeafBirthHold) as exc:
                raise MorphologyArtifactHold(str(exc)) from None
            raw,bound=_canonical(result),_canonical(binding)
            result_sha=store.put(raw,maximum=MAX);binding_sha=store.put(bound,maximum=MAX)
            samples.append({'index':index,'at':descriptor['at'],'result_sha256':result_sha,'result_bytes':len(raw),
                'binding_sha256':binding_sha,'binding_bytes':len(bound),'input_state_sha256':before,'state_sha256':_digest(state),
                'input_sha256':result['input_sha256'],'stem_result_sha256':descriptor['result_sha256']})
            previous=descriptor['at']
        _need(len(state['new_leaves'])==len(p['births']),'STATE_HOLD: complete declared birth schedule required')
        _need(_code_pins()==pins,'CODE_HOLD: population source changed before completion')
        manifest={**ROOT_CONSTANTS,'program_sha256':program_sha,'program_bytes':len(program_raw),'program_rights':p['rights'],
            'stem_artifact_sha256':p['stem']['artifact_sha256'],'stem_program_sha256':old['program_sha256'],'code_sha256':pins,
            'time_origin_utc':origin,'initial_at_elapsed_seconds_exact':p['initialization']['initial_inventory']['at_elapsed_seconds_exact'],
            'initial_state_sha256':initial_sha,'terminal_state_sha256':_digest(state),'samples':samples}
        return store.put(_canonical(manifest),maximum=MAX)
