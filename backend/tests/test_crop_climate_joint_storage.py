"""Confirmed joint states must survive actual immutable files and fresh reads."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_climate_joint_storage as model
import test_crop_climate_joint_time as reference

profiles=reference.profiles
FRESH_PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)))


def test_smoke_exact_sample_and_event_pages(profiles,tmp_path):
    c=reference.reference.model;ctx=reference.reference.context(profiles);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,128)
    b=model.clock.prepare_binding(ctx,origin=reference.origin());bound=reference.bind(b,before,chunk)
    with model._Files(tmp_path) as storage:
        storage._acquire()
        for kind in ('samples','events'):
            d=storage._pages(kind,bound['source'][kind],bound['times'][kind])
            assert storage._records(kind,d,b.manifest,ctx.program)==(bound['source'][kind],bound['times'][kind])
            assert all((tmp_path/(row['sha256']+'.json')).stat().st_size<=2*1024**2 for row in d)


def prepared(profiles,case=None,budget=3):
    c=reference.reference.model;ctx=reference.reference.context(profiles,case);cp=c.start(ctx);initial=cp;chunks=[]
    while True:
        chunk=c.advance_chunk(ctx,cp,budget);chunks.append(chunk);cp=chunk['checkpoint']
        if chunk['status']!='yielded':break
    return model.clock.prepare_binding(ctx,origin=reference.origin()),initial,chunks


def write(directory,binding,initial,chunks):
    with model.create_writer(directory,binding,initial) as writer:
        for chunk in chunks:writer.append(chunk,expected_chunk_sha256=model.clock.source_chunk_sha256(binding._context,chunk))
        return writer.finalize()


def all_rows(reader,kind):
    rows=[];n=reader.summary['counts'][kind]
    while len(rows)<n:rows.extend(reader.page(kind,start=len(rows))['records'])
    return rows


def test_smoke_full_writer_reader_exact_without_numerics(profiles,tmp_path,monkeypatch):
    binding,initial,chunks=prepared(profiles);reference.forbid_numerics(monkeypatch)
    artifact=write(tmp_path,binding,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as reader:
        assert reader.summary['checkpoint']['sha256']==chunks[-1]['checkpoint'].sha256
        for kind in ('samples','events'):
            expected=[v for chunk in chunks for v in chunk[kind]];rows=all_rows(reader,kind)
            assert [r['value'] for r in rows]==expected
            assert [r['time']['at'] for r in rows]==[model.clock.at_index(binding,r['step_index']) for r in expected]


def test_smoke_fresh_reader_constructs_no_model_context_or_rhs(profiles,tmp_path):
    binding,initial,chunks=prepared(profiles);artifact=write(tmp_path,binding,initial,chunks)
    script='''import json,sys
from app import crop_climate_joint_storage as m
c=m.continuation
def forbidden(*a,**kw):raise AssertionError('fresh reader constructed/recomputed physical state')
c.prepare_context=c.start=c.restore_checkpoint=c.advance_chunk=c.driver.joint.evaluate_rhs=c.driver.short.integrate=c.driver.management.apply_management=forbidden
with m.open_artifact(sys.argv[1],sys.argv[2]) as r:
 print(json.dumps({'summary':r.summary,'samples':r.page('samples')['records'],'events':r.page('events')['records']}))
'''
    r=subprocess.run([sys.executable,'-B','-c',script,str(tmp_path),artifact],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,
        env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    found=json.loads(r.stdout)
    assert found['summary']['counts']=={'samples':3,'events':3}
    assert [v['value'] for v in found['samples']]==[v for chunk in chunks for v in chunk['samples']]
    assert [v['value'] for v in found['events']]==[v for chunk in chunks for v in chunk['events']]


@pytest.mark.parametrize('index',range(9))
@pytest.mark.parametrize('budget',(1,7,128))
def test_all_original_programs_and_chunk_groups_survive_actual_files(profiles,tmp_path,monkeypatch,index,budget):
    binding,initial,chunks=prepared(profiles,reference.reference.CASES[index],budget)
    saved=[model.clock._source(binding._context,c)[0] for c in chunks]
    reference.forbid_numerics(monkeypatch);artifact=write(tmp_path,binding,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as reader:
        assert reader.summary['checkpoint']['value']==chunks[-1]['checkpoint'].value
        for kind in ('samples','events'):
            assert [r['value'] for r in all_rows(reader,kind)]==[v for c in chunks for v in c[kind]]
        assert reader.page('samples',start=reader.summary['counts']['samples'])['records']==[]
    assert [model.clock._source(binding._context,c)[0] for c in chunks]==saved


@pytest.mark.parametrize('position',(0,1,3,6))
def test_writer_closes_and_resumes_exact_checkpoint_at_initial_events_or_final(profiles,tmp_path,monkeypatch,position):
    b,initial,chunks=prepared(profiles);reference.forbid_numerics(monkeypatch)
    with model.create_writer(tmp_path,b,initial) as w:
        for chunk in chunks[:position]:w.append(chunk,expected_chunk_sha256=model.clock.source_chunk_sha256(b._context,chunk))
        head=w.head_sha256;cp=w.checkpoint
    with model.open_writer(tmp_path,head,b,cp) as w:
        for chunk in chunks[position:]:w.append(chunk,expected_chunk_sha256=model.clock.source_chunk_sha256(b._context,chunk))
        artifact=w.finalize()
    with model.open_artifact(tmp_path,artifact) as r:
        assert r.summary['checkpoint']['sha256']==chunks[-1]['checkpoint'].sha256
        assert [v['value'] for v in all_rows(r,'events')]==[v for c in chunks for v in c['events']]


@pytest.mark.parametrize('phase',('before','after'))
def test_actual_sigkill_on_first_commit_head_preserves_a_resumable_prefix(profiles,tmp_path,phase):
    b,initial,chunks=prepared(profiles);source=model.clock._source(b._context,chunks[0])[0]
    pack=tmp_path/'input.json';pack.write_text(json.dumps({'source':source,'digest':model.clock.source_chunk_sha256(b._context,chunks[0])}))
    directory=tmp_path/'artifact';directory.mkdir()
    script='''import json,os,signal,sys
import test_crop_climate_joint_storage as t
from app import crop_climate_joint_storage as m
p=json.loads(open(sys.argv[1]).read());c=m.continuation;ctx=t.reference.reference.context(t.profiles.__wrapped__());initial=c.start(ctx)
b=m.clock.prepare_binding(ctx,origin=t.reference.origin());s=p['source'];s['checkpoint']=c.restore_checkpoint(ctx,c._canonical(s['checkpoint']['value']),expected_sha256=s['checkpoint']['sha256'])
publish=m.ArtifactWriter._publish_head
def cut(self,head):
 if head['commit_count']==1 and sys.argv[3]=='before':os.kill(os.getpid(),signal.SIGKILL)
 publish(self,head)
 if head['commit_count']==1 and sys.argv[3]=='after':os.kill(os.getpid(),signal.SIGKILL)
m.ArtifactWriter._publish_head=cut
with m.create_writer(sys.argv[2],b,initial) as w:w.append(s,expected_chunk_sha256=p['digest'])
'''
    p=subprocess.run([sys.executable,'-B','-c',script,str(pack),str(directory),phase],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,
        env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    assert p.returncode==-9,p.stderr.decode()
    raw=(directory/'HEAD').read_bytes();head=json.loads(raw);n=int(phase=='after');assert head['commit_count']==n and head['artifact_sha256'] is None
    cp=initial if n==0 else chunks[0]['checkpoint']
    with model.open_writer(directory,sha256(raw).hexdigest(),b,cp) as w:
        for chunk in chunks[n:]:w.append(chunk,expected_chunk_sha256=model.clock.source_chunk_sha256(b._context,chunk))
        artifact=w.finalize()
    with model.open_artifact(directory,artifact) as r:
        assert [x['value'] for x in all_rows(r,'samples')]==[x for c in chunks for x in c['samples']]


@pytest.mark.parametrize('failure',('last-event','first-event','interval'))
def test_real_hold_writes_only_confirmed_values_and_fresh_failed_times(profiles,tmp_path,monkeypatch,failure):
    case=deepcopy(reference.reference.CASES[6 if failure!='interval' else 0])
    if failure=='interval':case['scenario']['forcing']['canopy_external_heat']['value']=1e7
    else:case['events'][-1 if failure=='last-event' else 0]['event']['values']['leaf']['value']=50000
    b,initial,chunks=prepared(profiles,case);reference.forbid_numerics(monkeypatch);artifact=write(tmp_path,b,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as r:
        assert r.summary['status']=='hold' and r.summary['checkpoint'] is None
        assert r.summary['last_confirmed']==chunks[-1]['last_confirmed'] and r.summary['hold']==chunks[-1]['hold']
        assert r.summary['times']['hold']['at']==model.clock.at_index(b,chunks[-1]['hold']['step_index'])
        for kind in ('samples','events'):assert [x['value'] for x in all_rows(r,kind)]==[x for c in chunks for x in c[kind]]


def paths(directory,artifact):
    head=json.loads((directory/'HEAD').read_bytes());root=json.loads((directory/(artifact+'.json')).read_bytes())
    header=json.loads((directory/(head['header_sha256']+'.json')).read_bytes())
    commit=json.loads((directory/(root['commits'][0]+'.json')).read_bytes())
    return {'head':directory/'HEAD','root':directory/(artifact+'.json'),'header':directory/(head['header_sha256']+'.json'),
        'context':directory/(header['context_blob_sha256']+'.json'),'commit':directory/(root['commits'][0]+'.json'),
        'sample':directory/(commit['pages']['samples'][0]['sha256']+'.json'),'event':directory/(commit['pages']['events'][0]['sha256']+'.json')}


@pytest.mark.parametrize('target',('head','root','header','context','commit','sample','event'))
def test_changed_stored_bytes_reject_and_close_all_fds(profiles,tmp_path,target):
    b,initial,chunks=prepared(profiles);artifact=write(tmp_path,b,initial,chunks);p=paths(tmp_path,artifact)[target]
    p.chmod(0o600);p.write_bytes(p.read_bytes()+b' ');before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,artifact)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',('symlink','fifo','missing','oversize'))
def test_selected_page_file_types_sizes_and_late_mutation_reject(profiles,tmp_path,kind):
    b,initial,chunks=prepared(profiles);artifact=write(tmp_path,b,initial,chunks);p=paths(tmp_path,artifact)['sample']
    with model.open_artifact(tmp_path,artifact) as r:
        raw=p.read_bytes();p.unlink()
        if kind=='symlink':target=tmp_path/'redirect';target.write_bytes(raw);p.symlink_to(target)
        elif kind=='fifo':os.mkfifo(p)
        elif kind=='oversize':
            with p.open('wb') as f:f.truncate(2*1024**2+1)
        with pytest.raises(model.JointStorageHold):r.page('samples')
        assert r.closed


@pytest.mark.parametrize('bad',(None,False,'','0'*64,'x'*64))
def test_trusted_root_digest_is_required(profiles,tmp_path,bad):
    b,initial,chunks=prepared(profiles);write(tmp_path,b,initial,chunks)
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,bad)


def test_stale_head_foreign_binding_checkpoint_and_unpublished_root_reject(profiles,tmp_path):
    b,initial,chunks=prepared(profiles)
    with model.create_writer(tmp_path,b,initial) as w:
        old=w.head_sha256;w.append(chunks[0],expected_chunk_sha256=model.clock.source_chunk_sha256(b._context,chunks[0]));current=w.head_sha256
    other=model.clock.prepare_binding(b._context,origin=reference.origin('2026-10-02T00:00:00Z'))
    for head,binding,cp in ((old,b,chunks[0]['checkpoint']),(current,other,chunks[0]['checkpoint']),(current,b,initial)):
        with pytest.raises(model.JointStorageHold):model.open_writer(tmp_path,head,binding,cp)
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,current)
    with model.open_writer(tmp_path,current,b,chunks[0]['checkpoint']) as w:
        with pytest.raises(model.JointStorageHold,match='terminal'):w.finalize()
        assert w.closed
    assert json.loads((tmp_path/'HEAD').read_bytes())['artifact_sha256'] is None


def test_second_writer_and_already_initialized_directory_reject_without_touching_original(profiles,tmp_path):
    b,initial,chunks=prepared(profiles)
    with model.create_writer(tmp_path,b,initial) as w:
        before=(tmp_path/'HEAD').read_bytes()
        with pytest.raises(model.JointStorageHold):model.create_writer(tmp_path,b,initial)
        assert not w.closed and (tmp_path/'HEAD').read_bytes()==before
    with pytest.raises(model.JointStorageHold):model.create_writer(tmp_path,b,initial)
    assert (tmp_path/'HEAD').read_bytes()==before


@pytest.mark.parametrize('operation',('bad-digest','changed-source','append-terminal','finalize-initial','closed'))
def test_invalid_operations_do_not_publish_new_heads(profiles,tmp_path,operation):
    b,initial,chunks=prepared(profiles,budget=128);w=model.create_writer(tmp_path,b,initial)
    if operation=='append-terminal':w.append(chunks[0],expected_chunk_sha256=model.clock.source_chunk_sha256(b._context,chunks[0]))
    if operation=='closed':w.close()
    raw=(tmp_path/'HEAD').read_bytes();digest=model.clock.source_chunk_sha256(b._context,chunks[0])
    if operation=='changed-source':chunks[0]['samples'][0]['plant_state']['leaf']['value']+=1
    with pytest.raises(model.JointStorageHold):
        if operation=='finalize-initial':w.finalize()
        else:w.append(chunks[0],expected_chunk_sha256='0'*64 if operation=='bad-digest' else digest)
    assert w.closed and (tmp_path/'HEAD').read_bytes()==raw


@pytest.mark.parametrize('start,limit,kind',((True,1,'samples'),(-1,1,'samples'),(4,1,'samples'),(0,0,'samples'),
    (0,65,'samples'),(0,9,'events'),(0,False,'samples'),(0,1,'unknown')))
def test_bounded_query_ranges(profiles,tmp_path,start,limit,kind):
    b,initial,chunks=prepared(profiles);artifact=write(tmp_path,b,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as r:
        with pytest.raises(model.JointStorageHold):r.page(kind,start=start,limit=limit)
        assert r.closed


@pytest.mark.parametrize('target',('code','dependency','limits'))
def test_current_storage_code_policy_change_rejects(profiles,tmp_path,monkeypatch,target):
    b,initial,chunks=prepared(profiles);artifact=write(tmp_path,b,initial,chunks)
    if target=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif target=='dependency':monkeypatch.setattr(model,'DEPENDENCY_SHA256',{})
    else:monkeypatch.setattr(model,'LIMITS',{**model.LIMITS,'samples_per_page':32})
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,artifact)


def test_directory_budget_counts_sparse_orphans_without_reading_them(profiles,tmp_path):
    b,initial,chunks=prepared(profiles)
    with (tmp_path/'orphan').open('wb') as f:f.truncate(512*1024**2+1)
    with pytest.raises(model.JointStorageHold,match='budget'):model.create_writer(tmp_path,b,initial)
    assert not (tmp_path/'HEAD').exists()


@pytest.mark.parametrize('target',('binding','checkpoint'))
def test_live_writer_cannot_switch_binding_or_checkpoint_between_commits(profiles,tmp_path,target):
    b,initial,chunks=prepared(profiles)
    with model.create_writer(tmp_path,b,initial) as w:
        raw=(tmp_path/'HEAD').read_bytes();chunk=chunks[0]
        if target=='binding':w.binding=model.clock.prepare_binding(b._context,origin=reference.origin('2026-10-02T00:00:00Z'))
        else:w.checkpoint=chunks[0]['checkpoint'];chunk=chunks[1]
        with pytest.raises(model.JointStorageHold):w.append(chunk,expected_chunk_sha256=model.clock.source_chunk_sha256(b._context,chunk))
        assert w.closed and (tmp_path/'HEAD').read_bytes()==raw


def test_maximum_first_chunk_is_paged_below_two_mib_without_changing_values(profiles,tmp_path,monkeypatch):
    case=deepcopy(reference.reference.CASES[0]);case.update(step_seconds=.0625,step_count=128,output_steps=list(range(129)),events=[])
    for i in range(128):
        e=deepcopy(reference.reference.reference.PREVIOUS['cases'][0]['event']);e['input_id']=f'synthetic-storage-max-{i}'
        case['events'].append({'step_index':i,'event':e})
    b,initial,chunks=prepared(profiles,case,128);reference.forbid_numerics(monkeypatch);artifact=write(tmp_path,b,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as r:
        assert r.summary['counts']=={'samples':129,'events':128}
        for kind in ('samples','events'):
            expected=[v for c in chunks for v in c[kind]];assert [v['value'] for v in all_rows(r,kind)]==expected
            assert all((tmp_path/(d['sha256']+'.json')).stat().st_size<=2*1024**2 for d in r._index[kind])
            for start in (0,len(expected)-1):assert len(model._canonical(r.page(kind,start=start)))<=2*1024**2
