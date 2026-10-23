from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app import crop_leaf_appearance_artifact_reader as reader
from app import crop_leaf_appearance_artifact_producer as producer
from app import crop_leaf_population_artifact_reader as inner_reader
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_leaf_appearance_program import program, resumed_source, resumed_program
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, snapshot, exact
from test_crop_stored_shoot_leaf_birth_inputs import reference_area
from test_crop_stored_shoot_leaf_birth_inputs import zero_base_program, produce as produce_stem

MAX=2*1024**2


@pytest.fixture(scope='module')
def artifact(source,tmp_path_factory):
    directory=tmp_path_factory.mktemp('appearance-reader')/'blobs'
    root=producer.produce_leaf_appearance_artifact(directory,source[1],stem_directory=source[0],program_raw=canonical(program()))
    return directory,source[1],root


def documents(artifact):
    directory,access,root=artifact
    with MorphologyBlobStore(directory,access)as store:
        m=json.loads(store.get(root,maximum=MAX));p=json.loads(store.get(m['preparation_sha256'],maximum=MAX))
        s=json.loads(store.get(m['source_program_sha256'],maximum=MAX))
    return m,p,s


def forged(artifact,tmp_path,change,*,part='manifest',repair=True):
    directory=tmp_path/'forged';shutil.copytree(artifact[0],directory);access=artifact[1]
    m,p,s=documents(artifact)
    if part=='manifest':change(m)
    elif part=='preparation':
        change(p)
        if repair:
            for name in ['derivation','initial_bindings']:
                p[name+'_sha256']=sha256(canonical(p[name])).hexdigest()
        raw=canonical(p)
        with MorphologyBlobStore(directory,access,write=True)as store:m['preparation_sha256']=store.put(raw,maximum=MAX)
        m['preparation_bytes']=len(raw)
    elif part=='source':
        change(s);raw=canonical(s)
        with MorphologyBlobStore(directory,access,write=True)as store:m['source_program_sha256']=store.put(raw,maximum=MAX)
        m['source_program_bytes']=len(raw);m['program_rights']=s['rights']
    with MorphologyBlobStore(directory,access,write=True)as store:root=store.put(canonical(m),maximum=MAX)
    return directory,access,root


def test_original_manifest_and12_frames_preserve_every_numeric_field_and_metadata(artifact):
    before=snapshot(artifact[0]);m,prepared,p=documents(artifact)
    assert reader.read_leaf_appearance_manifest(*artifact)==m
    counts=[];areas=0
    for index in range(12):
        f=reader.read_leaf_appearance_frame(*artifact,index=index)
        old=inner_reader.read_leaf_population_frame(artifact[0],artifact[1],m['population_artifact_sha256'],index=index)
        assert f=={**old,'schema_version':'leaf-appearance-replay-frame-v1','artifact_sha256':artifact[2],
            'population_artifact_sha256':m['population_artifact_sha256'],'source_program_sha256':m['source_program_sha256'],
            'preparation_sha256':m['preparation_sha256'],'policy_sha256':prepared['derivation']['policy_sha256'],
            'leaf_profile_sha256':prepared['derivation']['leaf_profile_sha256'],'display_policy':p['display_policy']}
        assert len(canonical(f))<=MAX;counts.append(f['tracked_leaf_count']);areas+=len(f['leaves'])
    assert counts==[3,3,3,4,4,4,4,4,4,4,5,5] and areas==47 and snapshot(artifact[0])==before


@pytest.mark.parametrize('index',[True,False,-1,12,1.0,'1',None])
def test_explicit_integer_index(artifact,index):
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_frame(*artifact,index=index)


@pytest.mark.parametrize('field',['ownership_asserted','access','store','use','transform','display'])
def test_source_rights_rejection(artifact,tmp_path,field):
    value=forged(artifact,tmp_path,lambda p:p['rights'].__setitem__(field,False),part='source')
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_manifest(*value)


@pytest.mark.parametrize('change',['extra','schema','scope','display-bool','model','code-shape','code-link','source-size',
    'preparation-size','generated-size','count-bool','count','origin','initial-time','initial-state','terminal','stem','inner'])
def test_rehashed_manifest_projection_rejected(artifact,tmp_path,change):
    def mutate(m):
        if change=='extra':m['yield_kg']=100
        elif change=='schema':m['schema_version']='unknown'
        elif change=='scope':m['gates']='approved'
        elif change=='display-bool':m['display_policy']['petiole_rachis_area_excluded']=1
        elif change=='model':m['model_versions']['kind']='unknown'
        elif change=='code-shape':m['code_sha256']['not-a-source']='0'*64
        elif change=='code-link':m['code_sha256'][next(iter(m['code_sha256']))]='0'*64
        elif change=='source-size':m['source_program_bytes']=True
        elif change=='preparation-size':m['preparation_bytes']+=1
        elif change=='generated-size':m['generated_program_bytes']+=1
        elif change=='count-bool':m['sample_count']=True
        elif change=='count':m['sample_count']=11
        elif change=='origin':m['time_origin_utc']='2026-10-01T00:00:01Z'
        elif change=='initial-time':m['initial_at_elapsed_seconds_exact']=exact(1)
        elif change=='initial-state':m['initial_state_sha256']='0'*64
        elif change=='terminal':m['terminal_state_sha256']='0'*64
        elif change=='stem':m['stem_program_sha256']='0'*64
        else:m['population_artifact_sha256']='0'*64
    value=forged(artifact,tmp_path,mutate)
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_manifest(*value)


@pytest.mark.parametrize('change',['extra','scope','model','source-sha','input-sha','code','initial-state','initial-leaf',
    'initial-kind','initial-birth','generated-program','generated-sha','derivation-sha','initial-sha','derivation-extra',
    'derivation-index-bool','derivation-end','derivation-start-state','derivation-end-state','policy','policy-sha',
    'profile-sha','timeline-input','timeline-checkpoint','event-count','event-kind','event-sequence','event-age',
    'event-seconds','event-utc','event-parent','event-leaf','input-ID','forcing','forcing-extra','declaration'])
def test_rehashed_preparation_projection_rejected(artifact,tmp_path,change):
    def mutate(p):
        d=p['derivation']
        if change=='extra':p['yield_kg']=100
        elif change=='scope':p['gates']='approved'
        elif change=='model':p['model_versions']['kind']='unknown'
        elif change=='source-sha':p['source_program_sha256']='0'*64
        elif change=='input-sha':p['input_sha256']='0'*64
        elif change=='code':p['code_sha256'][next(iter(p['code_sha256']))]='0'*64
        elif change=='initial-state':p['initial_state_sha256']='0'*64
        elif change=='initial-leaf':p['initial_bindings'][0]['leaf_id']='other'
        elif change=='initial-kind':p['initial_bindings'][0]['kind']='generative'
        elif change=='initial-birth':p['initial_bindings'][0]['emerged_elapsed_seconds_exact']=exact(1)
        elif change=='generated-program':p['generated_program']['births'][0]['leaf_id']='other'
        elif change=='generated-sha':p['generated_program_sha256']='0'*64
        elif change=='derivation-sha':p['derivation_sha256']='0'*64
        elif change=='initial-sha':p['initial_bindings_sha256']='0'*64
        elif change=='derivation-extra':d['yield_kg']=100
        elif change=='derivation-index-bool':d['end_index']=True
        elif change=='derivation-end':d['end_elapsed_seconds_exact']=exact(86401)
        elif change=='derivation-start-state':d['start_state_sha256']='0'*64
        elif change=='derivation-end-state':d['end_state_sha256']='0'*64
        elif change=='policy':d['policy']['first_generative_sequence']=3
        elif change=='policy-sha':d['policy_sha256']='0'*64
        elif change=='profile-sha':d['leaf_profile_sha256']='0'*64
        elif change=='timeline-input':d['timeline_input_sha256']='0'*64
        elif change=='timeline-checkpoint':d['timeline_checkpoint']['next_sequence']+=1
        elif change=='event-count':d['events'].pop()
        elif change=='event-kind':d['events'][0]['kind']='generative'
        elif change=='event-sequence':d['events'][0]['sequence']+=1
        elif change=='event-age':d['events'][0]['thermal_age_exact']=exact(6,'degC_day')
        elif change=='event-seconds':d['events'][0]['elapsed_seconds_exact']=exact(1)
        elif change=='event-utc':d['events'][0]['utc_whole_second']='2026-10-01T00:00:01Z'
        elif change=='event-parent':d['events'][0]['attachment_internode_id']='other'
        elif change=='event-leaf':d['events'][0]['leaf_id']='other'
        elif change=='input-ID':d['leaf_inputs']['input_id']='other'
        elif change=='forcing':d['leaf_inputs']['segments'][0]['air_temperature']['value']=23
        elif change=='forcing-extra':d['leaf_inputs']['segments'][0]['rainfall']=0
        else:d['leaf_inputs']['births'][0]['initial_area']['value']*=2
    repair=change not in ['derivation-sha','initial-sha'];value=forged(artifact,tmp_path,mutate,part='preparation',repair=repair)
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_manifest(*value)


@pytest.mark.parametrize('target',['outer','source','preparation','generated','inner','stem','middle-result','middle-binding','middle-stem'])
def test_missing_or_changed_content_never_returns_frame(artifact,tmp_path,target):
    directory=tmp_path/'changed';shutil.copytree(artifact[0],directory);m,p,s=documents(artifact)
    address={'outer':artifact[2],'source':m['source_program_sha256'],'preparation':m['preparation_sha256'],
        'generated':m['generated_program_sha256'],'inner':m['population_artifact_sha256'],'stem':m['stem_artifact_sha256']}
    if target not in address:
        inner=json.loads((directory/m['population_artifact_sha256']).read_text())
        address[target]=inner['samples'][5][{'middle-result':'result_sha256','middle-binding':'binding_sha256','middle-stem':'stem_result_sha256'}[target]]
    (directory/address[target]).write_bytes(b'{}')
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_frame(directory,artifact[1],artifact[2],index=5)


@pytest.mark.parametrize('target',['source','preparation','unselected-result'])
def test_late_change_after_selected_frame_is_rejected(artifact,tmp_path,monkeypatch,target):
    directory=tmp_path/'late';shutil.copytree(artifact[0],directory);m,p,s=documents(artifact)
    inner=json.loads((directory/m['population_artifact_sha256']).read_text());original=inner_reader.read_leaf_population_frame;calls=[]
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        if kwargs['index']==5 and not calls:
            calls.append(1)
            digest=m['source_program_sha256'] if target=='source' else (
                m['preparation_sha256'] if target=='preparation' else inner['samples'][8]['result_sha256'])
            (directory/digest).write_bytes(b'{}')
        return result
    monkeypatch.setattr(inner_reader,'read_leaf_population_frame',changed)
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_frame(directory,artifact[1],artifact[2],index=5)
    assert calls==[1]


def test_mixed_initial_policy_and_internal_nonredistribution(source,tmp_path):
    p=program();p['rights']['redistribute']=False;p['policy']['first_generative_sequence']=1
    p['initialization']['initial_inventory']['leaves'].pop(1);directory=tmp_path/'mixed'
    root=producer.produce_leaf_appearance_artifact(directory,source[1],stem_directory=source[0],program_raw=canonical(p))
    assert reader.read_leaf_appearance_manifest(directory,source[1],root)['program_rights']['redistribute'] is False
    f=reader.read_leaf_appearance_frame(directory,source[1],root,index=11);assert f['tracked_leaf_count']==4


def test_manifest_rights_boolean_is_not_numeric_projection(artifact,tmp_path):
    value=forged(artifact,tmp_path,lambda m:m['program_rights'].__setitem__('display',1))
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_manifest(*value)


def test_original_stem_source_pins_must_agree_with_outer_and_preparation(artifact,monkeypatch):
    original=reader.stem._load_manifest
    def changed(*args,**kwargs):
        value=deepcopy(original(*args,**kwargs));value['code_sha256'][next(iter(value['code_sha256']))]='0'*64
        return value
    monkeypatch.setattr(reader.stem,'_load_manifest',changed)
    with pytest.raises(reader.LeafAppearanceReadHold):reader.read_leaf_appearance_manifest(*artifact)


def test_no_new_vegetative_leaves_has_explicit_empty_births_and_original_three(source,tmp_path):
    p=program();p['policy']['first_generative_sequence']=3;p['policy']['vegetative_between_generative']=0
    p['leaf_profile']['base_temperature']['value']=5;p['leaf_profile']['curve']['values']['inflection_age']['value']=8
    directory=tmp_path/'no-new-leaves'
    root=producer.produce_leaf_appearance_artifact(directory,source[1],stem_directory=source[0],program_raw=canonical(p))
    assert reader.read_leaf_appearance_manifest(directory,source[1],root)['sample_count']==12
    assert [reader.read_leaf_appearance_frame(directory,source[1],root,index=i)['tracked_leaf_count']for i in range(12)]==[3]*12


def test_resumed_initial_leaf_uses_original_independent_clock_anchors(resumed_source,tmp_path):
    p=resumed_program(resumed_source);leaf=p['initialization']['initial_inventory']['leaves'][0]['initialization']
    leaf['clock_state']['base_temperature']['value']=10;leaf['clock_state']['age_exact']=exact(1,'degC_day')
    leaf['initial_area']['value']=reference_area(1,leaf);directory=tmp_path/'resumed'
    root=producer.produce_leaf_appearance_artifact(directory,resumed_source[1],stem_directory=resumed_source[0],program_raw=canonical(p))
    m=reader.read_leaf_appearance_manifest(directory,resumed_source[1],root)
    assert m['initial_at_elapsed_seconds_exact']==exact(7200) and m['sample_count']==11
    assert reader.read_leaf_appearance_frame(directory,resumed_source[1],root,index=10)['tracked_leaf_count']==5


def test_supported512_leaf_frame_remains_bounded_and_preserves_inner_values(tmp_path):
    parent=zero_base_program();timeline=parent['initial_state']['timeline_state']
    timeline['next_threshold_exact']=timeline['phyllochron_exact']={'numerator':'1','denominator':'509','unit':'degC_day'}
    parent['segments']=[{'start_utc':timeline['started_at'],'end_utc':'2026-10-02T00:00:00Z','air_temperature':{'value':1,'unit':'degC'}}]
    parent['output_times']=['2026-10-02T00:00:00Z'];source=produce_stem(tmp_path/'capacity-stem',parent)
    manifest=json.loads((source[0]/source[2]).read_bytes());p=program()
    p['stem']={'artifact_sha256':source[2],'program_sha256':manifest['program_sha256']}
    p['policy']['first_generative_sequence']=2**31-1;p['leaf_profile']['base_temperature']['value']=0
    for item in p['initialization']['initial_inventory']['leaves']:item['initialization']['clock_state']['base_temperature']['value']=0
    directory=tmp_path/'capacity-leaves'
    root=producer.produce_leaf_appearance_artifact(directory,source[1],stem_directory=source[0],program_raw=canonical(p))
    before=snapshot(directory);m=reader.read_leaf_appearance_manifest(directory,source[1],root)
    f=reader.read_leaf_appearance_frame(directory,source[1],root,index=0)
    old=inner_reader.read_leaf_population_frame(directory,source[1],m['population_artifact_sha256'],index=0)
    assert f['leaves']==old['leaves'] and f['stem']==old['stem'] and f['tracked_leaf_count']==512
    assert len(canonical(f))<=MAX and snapshot(directory)==before


def test_fresh_reader_imports_no_numerical_models_and_no_DB_CLI_or_writes(artifact,tmp_path):
    script=r'''
import builtins,importlib.abc,json,os,pathlib,subprocess,sys
sys.path.insert(0,sys.argv[1]);directory=sys.argv[2];root=sys.argv[3]
blocked={'crop_leaf_appearance_artifact_producer','crop_leaf_appearance_preparation','crop_stored_shoot_leaf_birth_inputs',
'crop_phytomer_kind','crop_leaf_population_artifact_producer','crop_leaf_population','crop_declared_leaf_births',
'crop_rational_leaf_area','crop_leaf_inventory','crop_leaf_area_state','crop_leaf_area_change','crop_leaf_expansion',
'crop_shoot_timeline','crop_phytomer_emergence','crop_rational_new_internodes','crop_morphology_thermal_clock',
'crop_internode_elongation','crop_rational_morphology_artifact_producer','crop_rational_shoot_inventory'}
allowed={'crop_leaf_appearance_artifact_reader','crop_leaf_appearance_program','crop_leaf_population_artifact_reader',
'crop_leaf_artifact_reader','crop_morphology_artifact_io','crop_morphology_artifact_reader','crop_rational_morphology_artifact_reader'}
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('app.crop_')and fullname.rsplit('.',1)[-1]not in allowed:raise AssertionError('numerical import '+fullname)
sys.meta_path.insert(0,Block())
import psycopg
from app.content_access import ContentAccess
attempts=[]
def forbidden(*a,**k):attempts.append(1);raise AssertionError('DB/CLI/write forbidden')
psycopg.connect=forbidden;subprocess.run=forbidden;subprocess.Popen=forbidden
original_open=os.open
def readonly(path,flags,*a,**k):
 if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):forbidden()
 return original_open(path,flags,*a,**k)
os.open=readonly
original_builtin=builtins.open
def bopen(file,mode='r',*a,**k):
 if any(x in mode for x in 'wax+'):forbidden()
 return original_builtin(file,mode,*a,**k)
builtins.open=bopen
def audit(event,args):
 if event=='open' and ((type(args[1])is str and any(x in args[1]for x in 'wax+'))or(type(args[2])is int and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):forbidden()
 if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','socket.connect'}:forbidden()
sys.addaudithook(audit)
from app import crop_leaf_appearance_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyBlobStore
MorphologyBlobStore.put=forbidden
access=ContentAccess(os.getuid(),os.getgid());before=len(os.listdir('/proc/self/fd'))
m=reader.read_leaf_appearance_manifest(directory,access,root);counts=[];areas=0;frames=[]
for i in range(m['sample_count']):
 f=reader.read_leaf_appearance_frame(directory,access,root,index=i);counts.append(f['tracked_leaf_count']);areas+=len(f['leaves']);frames.append(f)
assert counts==[3,3,3,4,4,4,4,4,4,4,5,5] and areas==47
assert before==len(os.listdir('/proc/self/fd')) and not attempts
print(json.dumps({'frames':12,'areas':47,'blocked_modules':len(blocked),'allowed_crop_reader_modules':sorted(allowed),
'numerical_imports':0,'DB_CLI_writes':0,'FD_preserved':True,'manifest':m,'frame_data':frames}))
'''
    before=snapshot(artifact[0]);env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    result=subprocess.run([sys.executable,'-B','-c',script,str(Path(__file__).resolve().parents[1]),str(artifact[0]),artifact[2]],
        env=env,capture_output=True,text=True,timeout=45)
    assert result.returncode==0,result.stderr;proof=json.loads(result.stdout)
    assert proof['frames']==12 and proof['areas']==47 and proof['numerical_imports']==proof['DB_CLI_writes']==0
    assert snapshot(artifact[0])==before
