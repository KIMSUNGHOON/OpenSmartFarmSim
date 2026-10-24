from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json,os

import pytest

from app import crop_growing_geometry_removal_artifact_producer as producer
from app import crop_growing_geometry_removal_artifact_reader as reader
from app import crop_growing_geometry_post_removal_context as post
from app import crop_growing_geometry_removal_next_interval as engine
from app import crop_growing_geometry_continuation as parent
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore,MorphologyArtifactHold
from test_growing_geometry_leaf_removal_point import profiles,CASES,declaration

ACCESS=ContentAccess(os.geteuid(),os.getegid())


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def inputs(profiles,case=0,*,event=2,count=4,dt=.125,indices=(0,)):
    p=deepcopy(CASES[case]['program']);p['capacity_outflow']['value']=0
    ctx=parent.prepare_context(program=p,step_seconds=dt,step_count=count,**profiles);cp=parent.start(ctx)
    if event:cp=parent.advance_chunk(ctx,cp,event)['checkpoint']
    return {'schema_version':'growing-geometry-removal-artifact-input-v1','input_id':p['input_id'],'origin':'synthetic',
        'program':p,'step_seconds':dt,'step_count':count,'event_step_index':event,'point_inputs':declaration(ctx,cp,indices),
        'time_origin_utc':'2026-10-01T00:00:00Z','rights':{'declaration_id':'own-removal-research-fixture','revision':'v1',
            'declared_at_utc':'2026-10-24T12:00:50Z','ownership_asserted':True,
            **dict.fromkeys(('access','store','use','transform','display'),True),'redistribute':False}}


@pytest.mark.parametrize('case',range(6))
def test_all_frames_preserve_original_CP_bytes_quantities_and_phase(tmp_path,profiles,case):
    source=inputs(profiles,case);raw=encoded(source);directory=tmp_path/'blobs'
    root=producer.produce_removal_artifact(directory,ACCESS,inputs_raw=raw,**profiles)
    manifest=reader.read_removal_manifest(directory,ACCESS,root);assert len(manifest['samples'])==6
    assert manifest['source_rights']==source['rights']and manifest['source_rights']['redistribute']is False
    ctx=parent.prepare_context(program=source['program'],step_seconds=.125,step_count=4,**profiles);cp=parent.start(ctx);original=[]
    for i in range(3):
        if i:cp=parent.advance_chunk(ctx,cp,1)['checkpoint']
        original.append(cp._raw)
    current=post.prepare_context(parent_context=ctx,raw_parent_checkpoint=cp._raw,expected_parent_sha256=cp.sha256,inputs=source['point_inputs'])
    later=engine.start(current);after=[later._raw]
    for _ in range(2):later=engine.advance_chunk(current,later,1)['checkpoint'];after.append(later._raw)
    with MorphologyBlobStore(directory,ACCESS)as store:
        assert store.get(manifest['sources']['inputs']['sha256'],maximum=reader.MAX)==raw
        for i,expected in enumerate([*original,*after]):
            d=manifest['samples'][i];assert store.get(d['checkpoint_sha256'],maximum=reader.CHECKPOINT_MAX)==expected
            frame=reader.read_removal_frame(directory,ACCESS,root,index=i);cp=json.loads(expected);sample=cp['last_confirmed'];n=3 if i<=2 else 2
            assert frame['sample']==sample and frame['checkpoint_sha256']==sha256(expected).hexdigest()
            assert frame['global_step_index']==(i if i<=2 else i-1)
            assert frame['phase']==('before_removal'if i<=2 else'after_removal_before_next_step'if i==3 else'post_removal_interval')
            assert frame['elapsed_seconds']==sample['elapsed_seconds']
            assert frame['leaf_ids']==['own-leaf-0','own-leaf-1','own-leaf-2']if i<=2 else frame['leaf_ids']==['own-leaf-1','own-leaf-2']
            for j,leaf in enumerate(frame['leaves']):
                assert leaf['thermal_age']=={'value':sample['state'][108+j],'unit':'degC_day'}
                assert leaf['area']=={'value':sample['state'][108+n+j],'unit':'m2'}
                original_index=j if i<=2 else j+1
                assert leaf['initial_area_receipt']==json.loads(ctx._seed)['initial_area_receipts'][original_index]
                assert leaf['curve_sha256']==sha256(encoded(json.loads(ctx._program)['leaves'][original_index]['curve'])).hexdigest()
            for j,key in enumerate(reader.base.CLIMATE_UNITS):assert frame['climate'][key]['value']==sample['state'][105+j]
            for j,key in enumerate(reader.base.PLANT_UNITS):assert frame['plant'][key]['value']==sample['state'][j]
            assert frame['point_outflows']is None if i<=2 else frame['point_outflows']==cp['point_outflows']
            assert frame['segment_integrated_transfers']is None if i<=2 else frame['segment_integrated_transfers']==cp['segment_integrated_transfers']
    before=reader.read_removal_frame(directory,ACCESS,root,index=2);after=reader.read_removal_frame(directory,ACCESS,root,index=3)
    assert before['at']==after['at']and before['phase']!=after['phase']
    assert producer.produce_removal_artifact(tmp_path/'repeat',ACCESS,inputs_raw=raw,**profiles)==root


@pytest.mark.parametrize('event',[0,4])
@pytest.mark.parametrize('indices',[(0,),(0,2)])
def test_endpoint_events_and_multiple_removals_keep_same_exact_time(tmp_path,profiles,event,indices):
    source=inputs(profiles,event=event,indices=indices,dt=1/3)
    root=producer.produce_removal_artifact(tmp_path/'blob',ACCESS,inputs_raw=encoded(source),**profiles)
    before=reader.read_removal_frame(tmp_path/'blob',ACCESS,root,index=event)
    after=reader.read_removal_frame(tmp_path/'blob',ACCESS,root,index=event+1)
    exact=Fraction.from_float(1/3)*event
    assert after['at']['elapsed_seconds_exact']=={'numerator':str(exact.numerator),'denominator':str(exact.denominator),'unit':'s'}
    assert before['at']==after['at']and len(after['leaves'])==3-len(indices)


@pytest.fixture(scope='module')
def saved(tmp_path_factory,profiles):
    directory=tmp_path_factory.mktemp('removal-store')/'blobs';source=inputs(profiles)
    root=producer.produce_removal_artifact(directory,ACCESS,inputs_raw=encoded(source),**profiles)
    return directory,root


@pytest.mark.parametrize('permission',['ownership_asserted','access','store','use','transform','display'])
def test_denied_rights_before_parent_calculation(tmp_path,profiles,monkeypatch,permission):
    source=inputs(profiles);source['rights'][permission]=False
    def forbidden(*a,**k):raise AssertionError('rights must precede growth')
    monkeypatch.setattr(parent,'prepare_context',forbidden)
    with pytest.raises(MorphologyArtifactHold):producer.produce_removal_artifact(tmp_path/'bad',ACCESS,inputs_raw=encoded(source),**profiles)


@pytest.mark.parametrize('change',[
    lambda x:x.update(event_step_index=True),lambda x:x.update(event_step_index=-1),lambda x:x.update(event_step_index=5),
    lambda x:x.update(origin='measured'),lambda x:x.update(extra=True),lambda x:x['rights'].pop('redistribute'),
    lambda x:x['program']['capacity_outflow'].update(value=.001),
    lambda x:x['point_inputs']['events'].append(deepcopy(x['point_inputs']['events'][0])),
    lambda x:x['point_inputs']['events'][0]['capacity'].update(unit='J/K'),
    lambda x:x['point_inputs']['at_elapsed_seconds_exact'].update(numerator='2'),
])
def test_invalid_request_rejected_before_growth(tmp_path,profiles,monkeypatch,change):
    source=inputs(profiles);change(source)
    def forbidden(*a,**k):raise AssertionError('invalid request before growth')
    monkeypatch.setattr(parent,'prepare_context',forbidden)
    with pytest.raises(MorphologyArtifactHold):producer.produce_removal_artifact(tmp_path/'bad',ACCESS,inputs_raw=encoded(source),**profiles)


@pytest.mark.parametrize('change',[
    lambda m:m.update(G0_G4='approved'),lambda m:m.update(status='failed'),lambda m:m.update(extra=1),
    lambda m:m['source_rights'].update(redistribute=True),lambda m:m['sources'].pop('license_notice'),
    lambda m:m.update(parent_context_sha256='0'*64),lambda m:m.update(post_context_sha256='0'*64),
    lambda m:m.update(point_calculation_sha256='0'*64),lambda m:m['samples'].pop(),
    lambda m:m['samples'][3].update(phase='before_removal'),lambda m:m['samples'][3].update(global_step_index=3),
    lambda m:m['samples'][3]['elapsed_seconds_exact'].update(numerator='2'),
    lambda m:m['samples'][3].update(previous_checkpoint_sha256=None),
    lambda m:m['samples'][3].update(checkpoint_bytes=True),lambda m:m['samples'][3].update(sample_sha256='0'*64),
    lambda m:m['display_policy'].update(geometry_authority='derived_SLA'),
])
def test_rehashed_root_closed_scope_sources_order_time_and_phase(saved,change):
    directory,root=saved;m=reader.read_removal_manifest(directory,ACCESS,root);change(m)
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:changed=store.put(encoded(m),maximum=reader.MAX)
    with pytest.raises(MorphologyArtifactHold):reader.read_removal_manifest(directory,ACCESS,changed)


@pytest.mark.parametrize('index',[-1,6,True,None,'0',1.5])
def test_bad_index(saved,index):
    with pytest.raises(MorphologyArtifactHold):reader.read_removal_frame(saved[0],ACCESS,saved[1],index=index)


def test_no_compute_no_write_and_detached_views(saved,monkeypatch):
    def forbidden(*a,**k):raise AssertionError('reader cannot calculate or write')
    for module in (parent,post,engine):
        for name in ('prepare_context','start','advance_chunk','restore_checkpoint','_context'):
            if hasattr(module,name):monkeypatch.setattr(module,name,forbidden)
    monkeypatch.setattr(post.point,'apply_removals',forbidden);monkeypatch.setattr(MorphologyBlobStore,'put',forbidden)
    frame=reader.read_removal_frame(saved[0],ACCESS,saved[1],index=3);same=deepcopy(frame);frame['leaves'].clear();frame['source_rights']['display']=False
    assert reader.read_removal_frame(saved[0],ACCESS,saved[1],index=3)==same


def test_current_and_late_file_rights_and_FD(saved,monkeypatch):
    directory,root=saved;m=reader.read_removal_manifest(directory,ACCESS,root);digest=m['sources']['inputs']['sha256'];file=directory/digest
    before=len(os.listdir('/proc/self/fd'));file.chmod(0o600)
    try:
        with pytest.raises(MorphologyArtifactHold):reader.read_removal_manifest(directory,ACCESS,root)
    finally:file.chmod(0o640)
    original=MorphologyBlobStore.get;calls=[]
    def late(self,key,**kwargs):
        raw=original(self,key,**kwargs)
        if key==digest and not calls:calls.append(1);file.chmod(0o600)
        return raw
    monkeypatch.setattr(MorphologyBlobStore,'get',late)
    try:
        with pytest.raises(MorphologyArtifactHold):reader.read_removal_manifest(directory,ACCESS,root)
    finally:file.chmod(0o640)
    assert len(os.listdir('/proc/self/fd'))==before


def test_partial_post_writer_never_publishes_completed_root(tmp_path,profiles,monkeypatch):
    source=inputs(profiles);original=MorphologyBlobStore.put;roots=[]
    def fail(self,raw,**kwargs):
        value=json.loads(raw)if raw.startswith(b'{')else{}
        if value.get('schema_version')=='growing-geometry-removal-research-artifact-v1':roots.append(raw)
        if value.get('version')==engine.CHECKPOINT_VERSION and value['segment_step_index']==1:raise OSError('injected write failure')
        return original(self,raw,**kwargs)
    monkeypatch.setattr(MorphologyBlobStore,'put',fail)
    with pytest.raises(MorphologyArtifactHold):producer.produce_removal_artifact(tmp_path/'partial',ACCESS,inputs_raw=encoded(source),**profiles)
    assert roots==[]


@pytest.mark.parametrize('name,change',[
    ('inputs',lambda x:x['rights'].update(display=False)),
    ('request',lambda x:x['leaves'][0]['initial_area'].update(unit='cm2')),
    ('program',lambda x:x['leaves'][0]['thermal_age'].update(value=1.0)),
    ('context',lambda x:x['identity'].update(engine_version='other')),
    ('point_inputs',lambda x:x['events'][0].update(leaf_id='missing')),
    ('point_result',lambda x:x['after']['state'].__setitem__(-1,.1)),
    ('post_program',lambda x:x['leaves'].reverse()),
    ('post_seed',lambda x:x['point_outflows']['carbohydrate'].update(value=0.0)),
    ('post_context',lambda x:x['identity'].update(code_sha256='0'*64)),
    ('post_snapshot',lambda x:x.update(segment_step_index=1)),
])
def test_rehashed_source_blob_cannot_break_original_bindings(saved,name,change):
    directory,root=saved;m=reader.read_removal_manifest(directory,ACCESS,root)
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:
        value=json.loads(store.get(m['sources'][name]['sha256'],maximum=reader.MAX));change(value);raw=encoded(value)
        m['sources'][name]={'sha256':store.put(raw,maximum=reader.MAX),'bytes':len(raw)}
        changed=store.put(encoded(m),maximum=reader.MAX)
    with pytest.raises(MorphologyArtifactHold):reader.read_removal_manifest(directory,ACCESS,changed)


@pytest.mark.parametrize('change',[
    lambda x:x.update(global_step_index=0),lambda x:x.update(segment_step_index=True),
    lambda x:x.update(phase='before_removal'),lambda x:x['point_outflows']['carbohydrate'].update(value=0.0),
    lambda x:x['engine_identity'].update(code_sha256='0'*64),
    lambda x:x['segment_integrated_transfers']['photosynthesis'].update(unit='mg_CH2O'),
    lambda x:x['global_balance_residuals']['carbohydrate'].update(value=999999.0),
    lambda x:x['last_confirmed']['state'].pop(),
    lambda x:x['last_confirmed']['derived']['leaf_area_index'].update(unit='m2'),
    lambda x:x.update(event_snapshot_sha256='0'*64),
])
def test_rehashed_post_checkpoint_still_has_closed_scope_units_and_source(saved,change):
    directory,root=saved;m=reader.read_removal_manifest(directory,ACCESS,root);d=m['samples'][4]
    with MorphologyBlobStore(directory,ACCESS,write=True)as store:
        value=json.loads(store.get(d['checkpoint_sha256'],maximum=reader.CHECKPOINT_MAX));change(value);raw=encoded(value)
        d['checkpoint_sha256']=store.put(raw,maximum=reader.CHECKPOINT_MAX);d['checkpoint_bytes']=len(raw)
        m['samples'][5]['previous_checkpoint_sha256']=d['checkpoint_sha256'];changed=store.put(encoded(m),maximum=reader.MAX)
    with pytest.raises(MorphologyArtifactHold):reader.read_removal_frame(directory,ACCESS,changed,index=4)


def test_late_source_code_change_never_returns_frame(saved,monkeypatch):
    original=reader._pins;calls=[]
    def late():
        calls.append(1);pins=original()
        if len(calls)>1:pins[next(iter(pins))]='0'*64
        return pins
    monkeypatch.setattr(reader,'_pins',late)
    with pytest.raises(MorphologyArtifactHold):reader.read_removal_frame(saved[0],ACCESS,saved[1],index=3)
    assert len(calls)>1


def test_domain_hold_never_returns_completed_root(tmp_path,profiles,monkeypatch):
    source=inputs(profiles);original=MorphologyBlobStore.put;roots=[]
    def watched(self,raw,**kwargs):
        value=json.loads(raw)if raw.startswith(b'{')else{}
        if value.get('schema_version')=='growing-geometry-removal-research-artifact-v1':roots.append(raw)
        return original(self,raw,**kwargs)
    monkeypatch.setattr(MorphologyBlobStore,'put',watched)
    monkeypatch.setattr(engine,'advance_chunk',lambda *a,**k:{'status':'hold','checkpoint':None,'hold':{'reason':'INJECTED_DOMAIN_HOLD'}})
    with pytest.raises(MorphologyArtifactHold,match='CALCULATION_HOLD'):producer.produce_removal_artifact(tmp_path/'hold',ACCESS,inputs_raw=encoded(source),**profiles)
    assert roots==[]


@pytest.mark.parametrize('raw',[b'{}',b'\xff',b'{"x":NaN}',b'{"x":1,"x":1}',b' '*(2*1024**2+1)])
def test_invalid_raw_request_bytes(tmp_path,profiles,raw):
    with pytest.raises(MorphologyArtifactHold):producer.produce_removal_artifact(tmp_path/'invalid',ACCESS,inputs_raw=raw,**profiles)


def test_late_producer_code_change_never_returns_completed_root(tmp_path,profiles,monkeypatch):
    source=inputs(profiles);original=reader._pins;calls=[]
    def late():
        calls.append(1);pins=original()
        if len(calls)>=9:pins[next(iter(pins))]='0'*64
        return pins
    monkeypatch.setattr(reader,'_pins',late)
    with pytest.raises(MorphologyArtifactHold):producer.produce_removal_artifact(tmp_path/'late-code',ACCESS,inputs_raw=encoded(source),**profiles)
    assert len(calls)>=9
    for file in (tmp_path/'late-code').iterdir():
        raw=file.read_bytes()
        if raw.startswith(b'{'):assert json.loads(raw).get('schema_version')!='growing-geometry-removal-research-artifact-v1'


def test_current_raw_profile_corruption_is_rejected(saved):
    directory,root=saved;m=reader.read_removal_manifest(directory,ACCESS,root);file=directory/m['sources']['growth_profile']['sha256'];raw=file.read_bytes()
    try:
        file.write_bytes(raw+b' ')
        with pytest.raises(MorphologyArtifactHold):reader.read_removal_manifest(directory,ACCESS,root)
    finally:file.write_bytes(raw)


def test_512_leaf_source_stores_and_reads_the_original_subset(tmp_path,profiles):
    source=inputs(profiles,event=0,count=1);p=source['program']
    p['leaves']=[{**deepcopy(p['leaves'][0]),'leaf_id':f'own-{i}'}for i in range(512)];p['model_floor_area']['value']=512
    k=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value']
    p['scenario']['climate_state']['canopy_sensible_energy']['value']=k*.25*(20-ref)
    ctx=parent.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);cp=parent.start(ctx)
    source['point_inputs']=declaration(ctx,cp)
    root=producer.produce_removal_artifact(tmp_path/'boundary',ACCESS,inputs_raw=encoded(source),**profiles)
    before=reader.read_removal_frame(tmp_path/'boundary',ACCESS,root,index=0)
    after=reader.read_removal_frame(tmp_path/'boundary',ACCESS,root,index=2)
    assert len(before['leaves'])==512 and len(after['leaves'])==511
    assert after['leaf_ids']==[f'own-{i}'for i in range(1,512)]
    assert len(after['sample']['state'])==108+2*511
    assert after['leaves'][0]['initial_area_receipt']==before['leaves'][1]['initial_area_receipt']
    assert len(encoded(after))<=reader.MAX
