from copy import deepcopy
import json

import pytest

from app import crop_complete_artifact_producer as producer
from app import crop_complete_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyBlobStore, MorphologyArtifactHold
from test_crop_funded_fractional_stem_binding import prepared as binding_prepared, declaration
from test_crop_funded_event_time import sources, profiles, ACCESS, TOLERANCE
from test_crop_funded_complete_prefix import finish, segment


@pytest.fixture(scope='module')
def artifact(binding_prepared,tmp_path_factory):
    context=binding_prepared[1]
    segments=[segment(context,finish(context,producer.model.crop.start(context)))]
    segments[0]['initial_bindings']['rights']['redistribute']=False
    directory=tmp_path_factory.mktemp('complete-artifact')/'blobs'
    root=producer.produce_complete_crop_artifact(directory,ACCESS,segments=segments)
    packet=reader.read_complete_crop_packet(directory,ACCESS,root)
    return directory,root,packet,segments


def put(store,value):
    raw=reader._canonical(value)
    return {'sha256':store.put(raw,maximum=reader.MAX),'bytes':len(raw)}


def changed(artifact,change):
    directory,root,packet,_=artifact
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:
        manifest=json.loads(store.get(root,maximum=reader.MAX));packet=deepcopy(packet)
        change(manifest,packet)
        manifest['packet']=put(store,packet)
        manifest['frames']=[reader.frame_descriptor(i,frame)for i,frame in enumerate(packet['frames'])]
        return put(store,manifest)['sha256']


def test_actual_complete_packet_exact_values_and_deterministic_retry(artifact):
    directory,root,packet,segments=artifact
    assert producer.produce_complete_crop_artifact(directory,ACCESS,segments=segments)==root
    assert packet==producer.model.bind_complete_trajectory(segments)
    manifest=reader.read_complete_crop_manifest(directory,ACCESS,root)
    assert len(manifest['frames'])==69 and packet['frames'][-1]['at']['elapsed_seconds_exact']['numerator']=='512'
    assert manifest['G0_G4']=='not_assessed'and manifest['R2']=='not_approved'
    assert len(manifest['code_sha256'])==53
    assert packet['basis']['initial_bindings']['rights']['redistribute']is False
    for index in (0,1,33,34,68):
        value=reader.read_complete_crop_frame(directory,ACCESS,root,index=index)
        assert value['frame']==packet['frames'][index]
        state=value['snapshot']['state'];n=len(value['leaves'])
        for i,leaf in enumerate(value['leaves']):
            assert [leaf[k]['value']for k in ('thermal_age','area','carbohydrate')]==[state[107+i],state[107+n+i],state[107+2*n+i]]
    dense=[f for f in packet['frames']if f['evidence']['checkpoint']is None]
    assert len(dense)==1 and dense[0]['phase']=='before_birth'


@pytest.mark.parametrize('change',[
    lambda m,p:p['frames'][0]['at']['elapsed_seconds_exact'].update(numerator='1'),
    lambda m,p:p['frames'][0].update(phase='after_birth'),
    lambda m,p:p['frames'][0].update(output_prefix_sha256='0'*64),
    lambda m,p:p['frames'][0].update(quantities_storage='source_prefix_plus_dense_partial'),
    lambda m,p:p['frames'][-1]['leaves'][0].update(attachment_internode_id='synthetic-initial-1'),
    lambda m,p:p['frames'][-1]['leaves'][0].update(event_id='invented'),
    lambda m,p:p['frames'][-1]['shoot']['internodes'][0]['length'].update(value=.001),
    lambda m,p:p['frames'][-1]['shoot']['internodes'][0]['length'].update(unit='cm'),
    lambda m,p:p['basis']['initial_bindings'].update(reviewer=''),
    lambda m,p:p['basis']['initial_bindings']['rights'].update(display=False),
    lambda m,p:p['basis']['initial_bindings']['rights'].update(redistribute=1),
    lambda m,p:p['basis'].update(initial_leaf_history='verified'),
    lambda m,p:m['code_sha256'].update({'backend/app/crop_complete_artifact_reader.py':'0'*64}),
    lambda m,p:m['contexts'].clear(),
    lambda m,p:p['basis']['simulation_start_development_seconds_exact'].update(numerator='999999'),
    lambda m,p:p['frames'][-1]['shoot']['internodes'][0].update(sequence=100),
    lambda m,p:p['frames'][-1]['shoot']['internodes'][0].update(source_length_state_sha256='0'*64),
    lambda m,p:p['frames'][-1]['shoot']['internodes'][-1]['development_birth_seconds_exact'].update(numerator='0'),
])
def test_rehashed_inconsistent_packet_is_held(artifact,change):
    root=changed(artifact,change)
    with pytest.raises(reader.CompleteCropArtifactHold):
        reader.read_complete_crop_packet(artifact[0],ACCESS,root)


def test_missing_point_receipt_is_not_a_partial_success(artifact):
    directory,root,_,_=artifact
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:
        m=json.loads(store.get(root,maximum=reader.MAX));m['geometry_receipts'][-1][0]['sha256']='f'*64
        replacement=put(store,m)['sha256']
    with pytest.raises(reader.CompleteCropArtifactHold):reader.read_complete_crop_manifest(directory,ACCESS,replacement)


def test_rehashed_context_profile_drift_is_held(artifact):
    directory,root,_,_=artifact
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:
        m=json.loads(store.get(root,maximum=reader.MAX));ctx=json.loads(store.get(m['contexts'][0]['sha256'],maximum=reader.MAX))
        ctx['source']['profile_sha256']['growth_profile']='0'*64;m['contexts'][0]=put(store,ctx)
        replacement=put(store,m)['sha256']
    with pytest.raises(reader.CompleteCropArtifactHold,match='point/profile'):reader.read_complete_crop_manifest(directory,ACCESS,replacement)


def test_read_is_defensive_and_has_no_calculation_or_external_effect(artifact,monkeypatch):
    import socket,subprocess,psycopg
    directory,root,packet,_=artifact
    def forbidden(*a,**k):raise AssertionError('reader calculation/write/external effect')
    for owner,name in [(producer.model,'bind_complete_trajectory'),(producer.model.crop,'advance_chunk'),
        (producer.model.crop,'restore_checkpoint'),(producer.model.binding.point,'calculate_internode_length_point'),
        (MorphologyBlobStore,'put'),(socket,'socket'),(subprocess,'Popen'),(psycopg,'connect')]:monkeypatch.setattr(owner,name,forbidden)
    result=reader.read_complete_crop_packet(directory,ACCESS,root);result['frames'].clear()
    assert reader.read_complete_crop_packet(directory,ACCESS,root)==packet
    with pytest.raises(reader.CompleteCropArtifactHold):reader.read_complete_crop_frame(directory,ACCESS,root,index=True)


def test_current_code_and_late_file_policy_are_checked(artifact,monkeypatch):
    directory,root,_,_=artifact;pins=reader._pins()
    monkeypatch.setattr(reader,'_pins',lambda:{**pins,'backend/app/crop_complete_artifact_reader.py':'0'*64})
    with pytest.raises(reader.CompleteCropArtifactHold,match='CODE_HOLD'):reader.read_complete_crop_manifest(directory,ACCESS,root)
    monkeypatch.undo();original=reader._fence
    def late(store,m,raws):
        target=directory/m['packet']['sha256'];target.chmod(0o666)
        try:return original(store,m,raws)
        finally:target.chmod(0o640)
    monkeypatch.setattr(reader,'_fence',late)
    with pytest.raises(reader.CompleteCropArtifactHold):reader.read_complete_crop_manifest(directory,ACCESS,root)


def test_prepublication_failure_leaves_no_completed_root(artifact,tmp_path,monkeypatch):
    target=tmp_path/'partial';original=MorphologyBlobStore.put
    def fail_root(self,raw,*,maximum):
        try:value=json.loads(raw)
        except (ValueError,UnicodeError):value={}
        if isinstance(value,dict)and value.get('schema_version')==reader.FLAGS['schema_version']:raise MorphologyArtifactHold('injected root write failure')
        return original(self,raw,maximum=maximum)
    monkeypatch.setattr(MorphologyBlobStore,'put',fail_root)
    with pytest.raises(reader.CompleteCropArtifactHold,match='injected root'):
        producer.produce_complete_crop_artifact(target,ACCESS,segments=artifact[3])
    assert list(target.iterdir())
    for path in target.iterdir():
        try:value=json.loads(path.read_bytes())
        except (ValueError,UnicodeError):continue
        assert not isinstance(value,dict)or value.get('schema_version')!=reader.FLAGS['schema_version']


def test_loaded_code_must_match_current_file(artifact,tmp_path,monkeypatch):
    monkeypatch.setattr(reader,'CODE_SHA256','0'*64)
    with pytest.raises(reader.CompleteCropArtifactHold,match='CODE_HOLD'):reader.read_complete_crop_manifest(artifact[0],ACCESS,artifact[1])
    monkeypatch.undo();monkeypatch.setattr(producer,'CODE_SHA256','0'*64)
    with pytest.raises(reader.CompleteCropArtifactHold,match='CODE_HOLD'):
        producer.produce_complete_crop_artifact(tmp_path/'never-published',ACCESS,segments=artifact[3])
    assert not (tmp_path/'never-published').exists()
