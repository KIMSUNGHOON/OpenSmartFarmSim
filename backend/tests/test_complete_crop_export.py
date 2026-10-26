from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from app import crop_complete_artifact_producer as producer
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from test_crop_complete_artifact import artifact as private_artifact,binding_prepared,sources,profiles,ACCESS,TOLERANCE
from test_crop_funded_complete_prefix import finish,segment
from test_crop_funded_fractional_birth_point import inputs as point_inputs

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('complete_export',ROOT/'research/export-complete-crop-replay.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)


@pytest.fixture(scope='module')
def public_artifact(private_artifact,tmp_path_factory,profiles):
    base=tmp_path_factory.mktemp('public-complete');old=private_artifact[3][0]['context'];selection=old.value['source']['candidate']['selection']
    manifest=json.loads((old._leaf_directory/selection['leaf_root_sha256']).read_bytes())
    inputs=json.loads((old._leaf_directory/manifest['sources']['inputs']['sha256']).read_bytes())
    inputs['rights'].update(declaration_id='own-public-complete-export-test',revision='public-v1',redistribute=True)
    model.reader.leaf._inputs(producer.model.crop._canonical(inputs))
    lr=produce_funded_leaf_artifact(base/'leaf',ACCESS,inputs_raw=producer.model.crop._canonical(inputs),**profiles)
    pc=producer.model.crop.birth.prepare_fractional_birth_context(base/'leaf',old._stem_directory,ACCESS,
        leaf_root_sha256=lr,stem_root_sha256=selection['stem_root_sha256'],stem_start_index=0,bracket_index=0,time_tolerance_seconds_exact=TOLERANCE)
    value=point_inputs(pc);value['events'][0]['attachment_internode_id']=producer.model.binding.describe_fractional_internode(pc)['internode_id']
    context=producer.model.crop.prepare_context(point_context=pc,inputs=value)
    segments=[segment(context,finish(context,producer.model.crop.start(context)))];directory=base/'blobs'
    root=producer.produce_complete_crop_artifact(directory,ACCESS,segments=segments)
    packet=model.reader.read_complete_crop_packet(directory,ACCESS,root);model._grants(packet)
    return directory,root,packet


def test_original_blobs_packet_notice_frames_and_identical_second_output(public_artifact,tmp_path):
    directory,root,packet=public_artifact;first,second=tmp_path/'first',tmp_path/'second'
    one=model.export(directory,root,first);two=model.export(directory,root,second)
    assert one==two and one['frames']==69
    assert {p.name:p.read_bytes()for p in first.iterdir()}=={p.name:p.read_bytes()for p in second.iterdir()}
    m=json.loads((first/'index.json').read_bytes())
    assert m['schema_version']=='complete-crop-public-fixture-v1'and m['G0_G4']=='not_assessed'and m['R2']=='not_approved'
    assert m['basis']==packet['basis']and (first/m['packet']['path']).read_bytes()==model.reader._canonical(packet)
    assert m['notice']['path']=='NOTICE.txt'and m['root']['sha256']==root
    for d in m['blobs']:
        raw=(first/d['path']).read_bytes();assert raw==(directory/d['sha256']).read_bytes()and len(raw)==d['bytes']
    for index,d in enumerate(m['frames']):
        raw=(first/d['path']).read_bytes();dto=json.loads(raw)
        assert len(raw)==d['bytes']and sha256(raw).hexdigest()==d['sha256']
        assert dto=={'schema_version':'complete-crop-public-frame-v1','artifact_sha256':root,'index':index,'frame':packet['frames'][index]}
        assert d['checkpoint_sha256']==packet['frames'][index]['evidence']['checkpoint_sha256']
    assert sum(d['checkpoint_sha256']is None for d in m['frames'])==1


def test_actual_private_false_rejected_before_creating_output(private_artifact,tmp_path):
    directory,root,packet,_=private_artifact;output=tmp_path/'private'
    assert packet['basis']['initial_bindings']['rights']['redistribute']is False
    before={p.name:p.read_bytes()for p in directory.iterdir()}
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):model.export(directory,root,output)
    assert not output.exists()and before=={p.name:p.read_bytes()for p in directory.iterdir()}


@pytest.mark.parametrize('grant',['leaf','stem','initial'])
@pytest.mark.parametrize('late',[False,True])
def test_current_and_late_public_grants_hold(public_artifact,tmp_path,monkeypatch,grant,late):
    directory,root,_=public_artifact;output=tmp_path/'held';load=model.reader._load;calls=[]
    def changed(*a,**k):
        m,p,raws=load(*a,**k);calls.append(1)
        if len(calls)==(2 if late else 1):
            rights=p['basis']['initial_bindings']['rights']if grant=='initial'else p['basis']['source_rights'][grant]
            rights['redistribute']=False
        return m,p,raws
    monkeypatch.setattr(model.reader,'_load',changed)
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):model.export(directory,root,output)
    assert len(calls)==(2 if late else 1)
    assert not (output/'index.json').exists()
    if not late:assert not output.exists()


@pytest.mark.parametrize('kind',['source','ancestor','descendant','relative','symlink','existing'])
def test_unsafe_and_existing_paths_hold(public_artifact,tmp_path,kind):
    directory,root,_=public_artifact;output=tmp_path/'target'
    if kind=='source':output=directory
    elif kind=='ancestor':output=directory.parent
    elif kind=='descendant':output=directory/'child'
    elif kind=='relative':output=Path('relative-complete-export')
    elif kind=='symlink':output.symlink_to(directory,target_is_directory=True)
    else:output.mkdir()
    with pytest.raises((OSError,ValueError)):model.export(directory,root,output)


@pytest.mark.parametrize('failure',['frame','publish','directory','output','source','code'])
def test_prepublication_faults_have_no_index(public_artifact,tmp_path,monkeypatch,failure):
    directory,root,_=public_artifact;output=tmp_path/'partial'
    if failure in ('frame','directory'):
        write=model._Output.write
        def fail(self,name,raw):
            if name=='frame-3.json':
                if failure=='frame':raise OSError('injected frame failure')
                output.rename(tmp_path/'displaced');output.mkdir(mode=0o750)
            return write(self,name,raw)
        monkeypatch.setattr(model._Output,'write',fail)
    elif failure=='publish':
        def fail(*a,**k):raise OSError('injected publication failure')
        monkeypatch.setattr(model._Output,'publish',fail)
    elif failure=='output':
        verify=model._Output.verify;calls=[]
        def fail(self,descriptors):
            calls.append(1)
            if len(calls)==2:(output/'frame-0.json').write_bytes(b'corrupt')
            return verify(self,descriptors)
        monkeypatch.setattr(model._Output,'verify',fail)
    else:
        owner,name=(model.reader,'_load')if failure=='source'else(model,'_fence');original=getattr(owner,name);calls=[]
        def fail(*a,**k):
            calls.append(1)
            if len(calls)==2:raise MorphologyArtifactHold('injected late '+failure)
            return original(*a,**k)
        monkeypatch.setattr(owner,name,fail)
    with pytest.raises((OSError,ValueError)):model.export(directory,root,output)
    assert output.exists()
    if failure in ('source','code'):assert len(calls)==2
    assert not (output/'index.json').exists()


def test_no_equations_database_cli_or_network_during_export(public_artifact,tmp_path,monkeypatch):
    import socket,subprocess,psycopg
    def forbidden(*a,**k):raise AssertionError('external effect or growth calculation')
    for owner,name in [(producer.model,'bind_complete_trajectory'),(producer.model.crop,'advance_chunk'),
        (producer.model.binding.point,'calculate_internode_length_point'),(subprocess,'Popen'),(socket,'socket'),(psycopg,'connect')]:monkeypatch.setattr(owner,name,forbidden)
    assert model.export(public_artifact[0],public_artifact[1],tmp_path/'read-only')['frames']==69
