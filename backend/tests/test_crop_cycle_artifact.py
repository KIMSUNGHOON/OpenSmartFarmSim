from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app import crop_cycle_artifact as artifact
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_plant_startup_integration as original
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads((ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())['cases']
PROFILES={
    'growth_profile':ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile':ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile':ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}
NOTICE=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
BUDGET={'max_steps':17,'max_transitions':31}


def program(name='empty-entry'):
    return deepcopy(next(c['program'] for c in CASES if c['case_id']==name))


def context(path,p):
    p=deepcopy(p);anchors=p.pop('output_times')
    receipt=inputs.write_input_packet(path,**p,anchors=anchors,outputs=anchors,**PROFILES,program_id='own-synthetic-artifact-test')
    reader=inputs.open_input_packet(path,receipt['root_sha256'],**PROFILES)
    return reader,engine.prepare_context(reader,**PROFILES)


def calculate(path,ctx,budget=None):
    with artifact.create_writer(path,ctx,notice_raw=NOTICE) as writer:
        while writer.advance(budget or BUDGET)['status']=='yielded':pass
        return writer.finalize()


def read_all(reader,kind,limit):
    rows=[];start=0
    while True:
        page=reader.page(kind,start,limit);rows.extend(page['records'])
        assert len(artifact._canonical(page))<=artifact.LIMITS['page_bytes']
        start=page['next']
        if start==page['total']:return rows


@pytest.fixture(scope='module')
def originals():
    return {c['case_id']:original.integrate_plant_startup(**c['program'],**PROFILES) for c in CASES}


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_real_writer_reader_preserves_canonical_original_payload_without_read_rhs(tmp_path,case,originals,monkeypatch):
    inputs_reader,ctx=context(tmp_path/'inputs',case['program'])
    with inputs_reader:
        receipt=calculate(tmp_path/'artifact',ctx)
        def unexpected(*args):raise AssertionError('read must not integrate')
        monkeypatch.setattr(engine.short._Evaluator,'rhs',unexpected)
        monkeypatch.setattr(original,'integrate_plant_startup',unexpected)
        with artifact.open_artifact(tmp_path/'artifact',receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
            expected=originals[case['case_id']];summary=reader.summary
            for key in ('status','scope','steps','planned_steps'):assert summary[key]==expected[key]
            for kind in ('samples','events'):
                assert artifact._canonical(read_all(reader,kind,2))==artifact._canonical(expected[kind])
            assert summary['checkpoint']['phase']=='boundary-committed'
            summary['counts']['samples']=999
            assert reader.summary['counts']['samples']==len(expected['samples'])
            assert all(not name.endswith('.tmp') for name in os.listdir(tmp_path/'artifact'))


@pytest.mark.parametrize('kind',['entry','pre-onset','carbon-without-number','underflow','t0-event','event','fractional'])
def test_holds_preserve_only_original_confirmed_past(tmp_path,kind,monkeypatch):
    p=program('full-removal-reentry' if kind in ('t0-event','event') else 'night-smooth' if kind=='fractional' else 'empty-entry')
    initial=p['initial_state']['values']
    if kind=='entry':p['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value']=100
    if kind=='pre-onset':initial['temperature_sum']['value']=0
    if kind=='carbon-without-number':initial['fruit_carbohydrate'][0]['value']=1
    if kind=='underflow':initial['stem_root']['value']=5e-324
    if kind in ('t0-event','event'):p['events'][0 if kind=='t0-event' else 1]['removals']['values']['leaf']['value']=1e6
    if kind=='fractional':
        initial['buffer']['value']=1;p['output_times']=[p['output_times'][0],p['output_times'][-1]]
        p['solver']['max_step_seconds']=3599
    expected=original.integrate_plant_startup(**p,**PROFILES)
    input_reader,ctx=context(tmp_path/'inputs',p)
    with input_reader:
        receipt=calculate(tmp_path/'artifact',ctx)
        def unexpected(*args):raise AssertionError('RHS in hold read')
        monkeypatch.setattr(engine.short._Evaluator,'rhs',unexpected)
        with artifact.open_artifact(tmp_path/'artifact',receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
            actual={**reader.summary,'samples':read_all(reader,'samples',2),'events':read_all(reader,'events',2)}
            for key in ('status','scope','steps','planned_steps','hold','last_confirmed','samples','events'):
                assert artifact._canonical(actual[key])==artifact._canonical(expected[key])
            assert actual['checkpoint'] is None


def test_pending_event_checkpoint_survives_writer_close_and_resume_once(tmp_path):
    p=program('full-removal-reentry');input_reader,ctx=context(tmp_path/'inputs',p)
    with input_reader:
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            while writer._checkpoint['at']!=p['events'][1]['at']:
                writer.advance({'max_steps':1,'max_transitions':1})
            assert writer._checkpoint['phase']=='step-end' and writer._checkpoint['event_cursor']==1
            head=writer.head_sha256;before=[v.hex() for v in writer._checkpoint['y']]
        with artifact.open_writer(tmp_path/'artifact',head,ctx,notice_raw=NOTICE) as writer:
            assert [v.hex() for v in writer._checkpoint['y']]==before
            while writer.advance(BUDGET)['status']=='yielded':pass
            receipt=writer.finalize();assert writer.finalize()==receipt
            with pytest.raises(artifact.CycleArtifactRejected,match='terminal'):writer.advance(BUDGET)
        with artifact.open_artifact(tmp_path/'artifact',receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
            assert len(read_all(reader,'events',8))==3


def test_unpublished_root_partial_pages_and_atomic_head_failure_resume_from_committed_prefix(tmp_path,monkeypatch):
    input_reader,ctx=context(tmp_path/'inputs',program())
    with input_reader:
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            writer.advance({'max_steps':1,'max_transitions':1});head=writer.head_sha256;old=deepcopy(writer._checkpoint)
            publish=writer._publish_head
            def failed(value):raise OSError('injected before pointer replace')
            monkeypatch.setattr(writer,'_publish_head',failed)
            with pytest.raises(OSError):writer.advance(BUDGET)
            assert writer.closed and writer._checkpoint==old
            with artifact._Files(tmp_path/'artifact') as files:assert files._head()[1]==head
        with artifact.open_writer(tmp_path/'artifact',head,ctx,notice_raw=NOTICE) as writer:
            assert writer._checkpoint==old
            while writer.advance(BUDGET)['status']=='yielded':pass
            monkeypatch.setattr(writer,'_publish_head',failed)
            with pytest.raises(OSError):writer.finalize()
            root={'version':artifact.VERSION,'header_sha256':writer._head_value['header_sha256'],
                  'commits':writer._hashes,'status':'completed'}
            unpublished=artifact._hash(root)
            with pytest.raises(artifact.CycleArtifactRejected,match='published'):
                artifact.open_artifact(tmp_path/'artifact',unpublished,ctx,notice_raw=NOTICE)
            with artifact._Files(tmp_path/'artifact') as files:terminal_head=files._head()[1]
        with artifact.open_writer(tmp_path/'artifact',terminal_head,ctx,notice_raw=NOTICE) as writer:
            receipt=writer.finalize()
        with artifact.open_artifact(tmp_path/'artifact',receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
            assert reader.summary['status']=='completed'


def test_exclusive_writer_stale_head_and_notice_rejections(tmp_path):
    input_reader,ctx=context(tmp_path/'inputs',program())
    with input_reader:
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            head=writer.head_sha256
            with pytest.raises(artifact.CycleArtifactRejected,match='exclusive'):
                artifact.open_writer(tmp_path/'artifact',head,ctx,notice_raw=NOTICE)
            writer.advance(BUDGET);new=writer.head_sha256
        with pytest.raises(artifact.CycleArtifactRejected,match='HEAD'):
            artifact.open_writer(tmp_path/'artifact',head,ctx,notice_raw=NOTICE)
        with pytest.raises(artifact.CycleArtifactRejected,match='NOTICE'):
            artifact.open_writer(tmp_path/'artifact',new,ctx,notice_raw=b'wrong')
        with artifact.open_writer(tmp_path/'artifact',new,ctx,notice_raw=NOTICE):pass


@pytest.mark.parametrize('budget',[{},None,{'max_steps':True,'max_transitions':1},
    {'max_steps':1,'max_transitions':129},{'max_steps':0,'max_transitions':1}])
def test_chunk_resource_rejection_before_rhs(tmp_path,budget,monkeypatch):
    input_reader,ctx=context(tmp_path/'inputs',program())
    with input_reader,artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
        head=writer.head_sha256
        def unexpected(*args):raise AssertionError('RHS must not start')
        monkeypatch.setattr(engine,'advance_chunk',unexpected)
        with pytest.raises(artifact.CycleArtifactRejected):writer.advance(budget)
        assert writer.head_sha256==head


def test_closed_context_is_typed_artifact_rejection(tmp_path):
    input_reader,ctx=context(tmp_path/'inputs',program());input_reader.close()
    with pytest.raises(artifact.CycleArtifactRejected):artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE)
    assert not (tmp_path/'artifact').exists()


@pytest.mark.parametrize('key,bad',[('output_start',False),('event_start',0.0),('planned_steps',120.0)])
def test_boolean_or_float_delta_counter_is_rejected_before_publication(tmp_path,key,bad,monkeypatch):
    input_reader,ctx=context(tmp_path/'inputs',program())
    with input_reader,artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
        advance=engine.advance_chunk;head=writer.head_sha256
        def changed(*args):
            result=advance(*args);result[key]=bad;return result
        monkeypatch.setattr(engine,'advance_chunk',changed)
        with pytest.raises(artifact.CycleArtifactRejected):writer.advance({'max_steps':1,'max_transitions':1})
        assert writer.head_sha256==head


def test_failure_after_atomic_head_replace_poisoned_writer_requires_fresh_resume(tmp_path,monkeypatch):
    input_reader,ctx=context(tmp_path/'inputs',program())
    with input_reader:
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            publish=writer._publish_head
            def replaced_then_failed(head):
                publish(head);raise OSError('injected after durable replace')
            monkeypatch.setattr(writer,'_publish_head',replaced_then_failed)
            with pytest.raises(OSError):writer.advance({'max_steps':1,'max_transitions':1})
            assert writer.closed
        with artifact._Files(tmp_path/'artifact') as files:head,head_hash=files._head()
        with artifact.open_writer(tmp_path/'artifact',head_hash,ctx,notice_raw=NOTICE) as resumed:
            assert resumed._checkpoint['boundary_cursor']==1
            while resumed.advance(BUDGET)['status']=='yielded':pass
            receipt=resumed.finalize()
        with artifact.open_artifact(tmp_path/'artifact',receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
            assert len(read_all(reader,'samples',64))==3


def put_blob(path,value):
    raw=artifact._canonical(value);digest=sha256(raw).hexdigest()
    file=path/(digest+'.json')
    if file.exists():assert file.read_bytes()==raw
    else:file.write_bytes(raw)
    return digest


def rehash_terminal(path,receipt,change):
    root=json.loads((path/(receipt['artifact_sha256']+'.json')).read_bytes())
    original_terminal=root['commits'][-1]
    chunk=json.loads((path/(original_terminal+'.json')).read_bytes())
    change(chunk,root,path)
    terminal=put_blob(path,chunk)
    if terminal!=original_terminal:root['commits'][root['commits'].index(original_terminal)]=terminal
    digest=put_blob(path,root)
    head=json.loads((path/'HEAD').read_bytes())
    head.update(artifact_sha256=digest,latest_commit_sha256=terminal)
    os.chmod(path/'HEAD',0o600);(path/'HEAD').write_bytes(artifact._canonical(head))
    return digest


@pytest.fixture
def completed(tmp_path):
    source,ctx=context(tmp_path/'inputs',program('full-removal-reentry'))
    with source:
        path=tmp_path/'artifact';receipt=calculate(path,ctx,BUDGET)
        yield path,ctx,receipt


@pytest.mark.parametrize('kind',['counter-type','parent','prefix','clock','balance','budget','sample-count',
    'sample-time','sample-lai','event-removal','result-shape','root-status','root-order'])
def test_rehashed_semantic_root_commit_page_tampering_is_rejected_without_rhs(completed,kind,monkeypatch):
    path,ctx,receipt=completed
    def change(chunk,root,path):
        if kind=='counter-type':chunk['result']['event_start']=0.0
        if kind in ('parent','prefix','clock','balance'):
            cp=chunk['result']['checkpoint']
            if kind=='parent':cp['parent_sha256']='0'*64
            if kind=='prefix':cp['output_prefix_sha256']='0'*64
            if kind=='clock':cp['clock']['prefix']['numerator']='1'
            if kind=='balance':cp['y'][0]+=100
            engine._seal(cp)
        if kind=='budget':chunk['budget']['max_steps']=True
        if kind=='sample-count':chunk['pages']['samples'][0]['count']+=1
        if kind=='sample-time':chunk['pages']['samples'][0]['first_at']='2025-01-01T00:00:00Z'
        if kind in ('sample-lai','event-removal'):
            category='samples' if kind=='sample-lai' else 'events';descriptor=chunk['pages'][category][0]
            rows=json.loads((path/(descriptor['sha256']+'.json')).read_bytes())
            if kind=='sample-lai':rows[0]['lai']['value']+=1
            else:rows[0]['removed']['leaf']['value']+=1
            descriptor['sha256']=put_blob(path,rows)
        if kind=='result-shape':chunk['result']=None
        if kind=='root-status':root['status']='hold'
        if kind=='root-order':root['commits'].reverse()
    digest=rehash_terminal(path,receipt,change)
    def unexpected(*args):raise AssertionError('tamper validation must not integrate')
    monkeypatch.setattr(engine.short._Evaluator,'rhs',unexpected)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(artifact.CycleArtifactRejected):artifact.open_artifact(path,digest,ctx,notice_raw=NOTICE)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',['hash','symlink','fifo','oversize','missing','utf8','duplicates'])
def test_published_root_file_errors_are_typed_and_close_fd(completed,kind):
    path,ctx,receipt=completed;file=path/(receipt['artifact_sha256']+'.json')
    if kind=='hash':os.chmod(file,0o600);file.write_bytes(b'{}')
    if kind=='symlink':file.unlink();file.symlink_to(path/'HEAD')
    if kind=='fifo':file.unlink();os.mkfifo(file)
    if kind=='oversize':os.chmod(file,0o600);file.write_bytes(b' '* (artifact.LIMITS['root_bytes']+1))
    if kind=='missing':file.unlink()
    if kind in ('utf8','duplicates'):
        raw=b'\xff' if kind=='utf8' else b'{"x":1,"x":2}'
        digest=sha256(raw).hexdigest();(path/(digest+'.json')).write_bytes(raw)
        head=json.loads((path/'HEAD').read_bytes());head['artifact_sha256']=digest
        os.chmod(path/'HEAD',0o600);(path/'HEAD').write_bytes(artifact._canonical(head))
        receipt={**receipt,'artifact_sha256':digest}
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(artifact.CycleArtifactRejected):artifact.open_artifact(path,receipt['artifact_sha256'],ctx,notice_raw=NOTICE)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind,start,limit',[('samples',True,1),('samples',-1,1),('samples',999,1),
    ('samples',0,65),('events',0,9),('events',0,True),('unknown',0,1)])
def test_page_cursor_and_limits_are_typed(completed,kind,start,limit):
    path,ctx,receipt=completed
    with artifact.open_artifact(path,receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
        with pytest.raises(artifact.CycleArtifactRejected):reader.page(kind,start,limit)
        end=reader.page('samples',reader.summary['counts']['samples'],64)
        assert end['records']==[] and end['next']==end['total']
    with pytest.raises(artifact.CycleArtifactRejected):reader.page('samples',0,1)


def test_modified_selected_page_is_rehashed_each_read_and_only_one_page_cache(completed):
    path,ctx,receipt=completed
    with artifact.open_artifact(path,receipt['artifact_sha256'],ctx,notice_raw=NOTICE) as reader:
        first=reader.page('samples',0,1);first['records'][0]['state']['buffer']['value']=999
        assert reader.page('samples',0,1)['records'][0]['state']['buffer']['value']!=999
        assert len(reader._page_cache)==2
        file=path/(reader._index['samples'][0]['sha256']+'.json')
        os.chmod(file,0o600);file.write_bytes(b'[]')
        with pytest.raises(artifact.CycleArtifactRejected,match='HASH_HOLD'):reader.page('samples',0,1)


def test_commit_budget_fails_before_next_rhs(tmp_path,monkeypatch):
    source,ctx=context(tmp_path/'inputs',program())
    with source:
        monkeypatch.setitem(artifact.LIMITS,'commits',1)
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            writer.advance({'max_steps':1,'max_transitions':1});head=writer.head_sha256
            def unexpected(*args):raise AssertionError('RHS must not start')
            monkeypatch.setattr(engine,'advance_chunk',unexpected)
            with pytest.raises(artifact.CycleArtifactRejected,match='commit budget'):writer.advance(BUDGET)
            assert writer.head_sha256==head


def test_orphan_bytes_count_against_directory_budget_before_rhs(tmp_path,monkeypatch):
    source,ctx=context(tmp_path/'inputs',program())
    with source:
        monkeypatch.setitem(artifact.LIMITS,'directory_bytes',32768)
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            head=writer.head_sha256
            (tmp_path/'artifact'/'own-orphan.tmp').write_bytes(b' '*32768)
            def unexpected(*args):raise AssertionError('full directory must reject before RHS')
            monkeypatch.setattr(engine,'advance_chunk',unexpected)
            with pytest.raises(artifact.CycleArtifactRejected,match='RESOURCE_HOLD'):writer.advance(BUDGET)
            assert writer.head_sha256==head


def test_existing_directory_preserved_and_missing_resume_is_typed(tmp_path):
    source,ctx=context(tmp_path/'inputs',program())
    with source:
        path=tmp_path/'existing';path.mkdir();(path/'keep').write_text('original')
        with pytest.raises(artifact.CycleArtifactRejected):artifact.create_writer(path,ctx,notice_raw=NOTICE)
        assert (path/'keep').read_text()=='original'
        with pytest.raises(artifact.CycleArtifactRejected):artifact.open_writer(tmp_path/'missing','0'*64,ctx,notice_raw=NOTICE)
