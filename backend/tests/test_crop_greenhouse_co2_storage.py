"""Actual immutable109-state files, zero-replay readers and interrupted HEADs."""
from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from app import crop_greenhouse_co2_continuation as c
from app import crop_greenhouse_co2_time as clock
import test_crop_greenhouse_co2_continuation as producer
import test_crop_greenhouse_co2_time as times

profiles=producer.profiles;CASES=producer.CASES
FRESH_PYTHONPATH=producer.FRESH_PYTHONPATH


@pytest.fixture(scope='module')
def model():return import_module('app.crop_greenhouse_co2_storage')


def prepared(profiles,case=None,budget=7):
    ctx=producer.context(c,profiles,case);cp=initial=c.start(ctx);chunks=[]
    while True:
        r=c.advance_chunk(ctx,cp,budget);chunks.append(r);cp=r['checkpoint']
        if r['status']!='yielded':break
    return clock.prepare_binding(ctx,origin=times.origin()),initial,chunks


def write(model,directory,binding,initial,chunks):
    with model.create_writer(directory,binding,initial) as writer:
        for chunk in chunks:writer.append(chunk,expected_chunk_sha256=clock.source_chunk_sha256(binding._context,chunk))
        return writer.finalize()


def all_rows(reader,kind):
    rows=[];total=reader.summary['counts'][kind]
    while len(rows)<total:rows.extend(reader.page(kind,start=len(rows))['records'])
    return rows


def forbid(monkeypatch):
    times.forbid_numerics(monkeypatch)
    def forbidden(*args,**kwargs):pytest.fail('storage created context/time or started calculation')
    for target,name in ((c,'prepare_context'),(c,'start'),(clock,'prepare_binding')):monkeypatch.setattr(target,name,forbidden)


def test_exact_actual_writer_reader_without_context_or_numerics(model,profiles,tmp_path,monkeypatch):
    binding,initial,chunks=prepared(profiles);saved=[clock._source(binding._context,x)[0] for x in chunks]
    forbid(monkeypatch);artifact=write(model,tmp_path,binding,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as reader:
        assert reader.summary['checkpoint']['value']==chunks[-1]['checkpoint'].value
        for kind in ('samples','events'):
            expected=[v for chunk in chunks for v in chunk[kind]];rows=all_rows(reader,kind)
            assert [r['value'] for r in rows]==expected
            assert [r['time']['at'] for r in rows]==[clock.at_index(binding,v['step_index']) for v in expected]
        assert len(reader.summary['last_confirmed']['integrated_transfers'])==44
        assert len(reader.summary['last_confirmed']['event_totals'])==6
        assert len(reader.summary['last_confirmed']['balance_residuals'])==17
    assert [clock._source(binding._context,x)[0] for x in chunks]==saved


@pytest.mark.parametrize('case',CASES,ids=lambda x:x['case_id'])
@pytest.mark.parametrize('budget',(1,7,128))
def test_all_original_programs_and_chunk_groups_survive_files(model,profiles,tmp_path,monkeypatch,case,budget):
    b,initial,chunks=prepared(profiles,case,budget);forbid(monkeypatch);artifact=write(model,tmp_path,b,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as reader:
        assert reader.summary['status']=='completed' and reader.summary['checkpoint']['value']==chunks[-1]['checkpoint'].value
        for kind in ('samples','events'):assert [r['value'] for r in all_rows(reader,kind)]==[v for chunk in chunks for v in chunk[kind]]
        assert reader.page('samples',start=reader.summary['counts']['samples'])['records']==[]
        assert reader.summary['last_confirmed']['climate_state']['air_co2_mass']==chunks[-1]['last_confirmed']['climate_state']['air_co2_mass']


def test_fresh_reader_has_no_context_time_restore_physics_or_subprocess(model,profiles,tmp_path):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks)
    script='''import json,sys,subprocess,os
from app import crop_greenhouse_co2_storage as m
c=m.continuation;rhs=c.driver.stage.rhs;solar=rhs.solar_rhs
def forbidden(*args,**kw):raise AssertionError('fresh reader computed state/time or invoked child/CLI')
for target,name in ((c,'prepare_context'),(c,'start'),(m.clock,'prepare_binding'),(c,'advance_chunk'),(c,'restore_checkpoint'),(rhs,'evaluate_rhs'),(c.driver.stage.joint,'evaluate_rhs'),(c.driver.stage,'integrate'),(solar,'evaluate_rhs'),(solar.vent,'calculate_ventilation'),(solar.par.radiation,'calculate_par'),(solar.nir,'calculate_nir'),(rhs.gas,'density_to_ppm'),(rhs.net,'calculate_exchange'),(rhs.air,'evaluate_rhs'),(c.driver.management,'apply_management'),(subprocess,'run'),(subprocess,'Popen'),(os,'system')):setattr(target,name,forbidden)
with m.open_artifact(sys.argv[1],sys.argv[2]) as r:
 rows={}
 for kind in ('samples','events'):
  found=[]
  while len(found)<r.summary['counts'][kind]:found.extend(r.page(kind,start=len(found))['records'])
  rows[kind]=m._hash(found)
 print(json.dumps({'summary':m._hash(r.summary),'rows':rows,'forbidden_calls':0}))
'''
    completed=subprocess.run([sys.executable,'-B','-c',script,str(tmp_path),artifact],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    with model.open_artifact(tmp_path,artifact) as reader:
        expected={'summary':model._hash(reader.summary),'rows':{k:model._hash(all_rows(reader,k)) for k in ('samples','events')},'forbidden_calls':0}
    assert json.loads(completed.stdout)==expected


@pytest.mark.parametrize('position',(0,1,4,5,8,9,16,17))
def test_close_reopen_initial_forcing_event_and_final_positions(model,profiles,tmp_path,monkeypatch,position):
    b,initial,chunks=prepared(profiles,budget=1);forbid(monkeypatch)
    with model.create_writer(tmp_path,b,initial) as writer:
        for chunk in chunks[:position]:writer.append(chunk,expected_chunk_sha256=clock.source_chunk_sha256(b._context,chunk))
        head,cp=writer.head_sha256,writer.checkpoint
    with model.open_writer(tmp_path,head,b,cp) as writer:
        for chunk in chunks[position:]:writer.append(chunk,expected_chunk_sha256=clock.source_chunk_sha256(b._context,chunk))
        artifact=writer.finalize()
    with model.open_artifact(tmp_path,artifact) as reader:
        assert reader.summary['checkpoint']['sha256']==chunks[-1]['checkpoint'].sha256
        assert [v['value'] for v in all_rows(reader,'events')]==[v for chunk in chunks for v in chunk['events']]


@pytest.mark.parametrize('phase',('before','after'))
def test_actual_sigkill_before_or_after_head_preserves_selected_prefix_and_orphans(model,profiles,tmp_path,phase):
    b,initial,chunks=prepared(profiles);pack=tmp_path/'input.json'
    pack.write_text(json.dumps({'source':clock._source(b._context,chunks[0])[0],'digest':clock.source_chunk_sha256(b._context,chunks[0])}))
    directory=tmp_path/'artifact';directory.mkdir(mode=0o700)
    script='''import json,os,signal,sys
import test_crop_greenhouse_co2_storage as t
from app import crop_greenhouse_co2_storage as m
p=json.loads(open(sys.argv[1]).read());c=m.continuation;ctx=t.producer.context(c,t.profiles.__wrapped__());initial=c.start(ctx)
b=m.clock.prepare_binding(ctx,origin=t.times.origin());s=p['source'];s['checkpoint']=c.restore_checkpoint(ctx,c._canonical(s['checkpoint']['value']),expected_sha256=s['checkpoint']['sha256'])
publish=m.ArtifactWriter._publish_head
def cut(self,head):
 if head['commit_count']==1 and sys.argv[3]=='before':os.kill(os.getpid(),signal.SIGKILL)
 publish(self,head)
 if head['commit_count']==1 and sys.argv[3]=='after':os.kill(os.getpid(),signal.SIGKILL)
m.ArtifactWriter._publish_head=cut
with m.create_writer(sys.argv[2],b,initial) as w:w.append(s,expected_chunk_sha256=p['digest'])
'''
    run=subprocess.run([sys.executable,'-B','-c',script,str(pack),str(directory),phase],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    assert run.returncode==-9,run.stderr.decode()
    raw=(directory/'HEAD').read_bytes();head=json.loads(raw);n=int(phase=='after')
    assert head['commit_count']==n and head['artifact_sha256'] is None
    preserved={p.name:p.read_bytes() for p in directory.glob('*.json')};cp=initial if n==0 else chunks[0]['checkpoint']
    with model.open_writer(directory,sha256(raw).hexdigest(),b,cp) as writer:
        for chunk in chunks[n:]:writer.append(chunk,expected_chunk_sha256=clock.source_chunk_sha256(b._context,chunk))
        artifact=writer.finalize()
    assert preserved and all((directory/name).read_bytes()==value for name,value in preserved.items())
    with model.open_artifact(directory,artifact) as reader:assert [r['value'] for r in all_rows(reader,'samples')]==[v for chunk in chunks for v in chunk['samples']]


@pytest.mark.parametrize('failure',('first-event','last-event','forcing','interval','step-balance','event-balance'))
def test_real_and_injected_holds_store_original_failed_times_only(model,profiles,tmp_path,monkeypatch,failure):
    case=deepcopy(producer.reference.BY_ID['weather-multiple'])
    if failure in ('first-event','last-event'):case['events'][0 if failure=='first-event' else -1]['event']['values']['leaf']['value']=1e15
    elif failure=='forcing':case['forcing_program'][2]['solar']['values']['outdoor_global_radiation']['value']=-1
    elif failure=='interval':case['forcing_program'][0]['co2']['forcing']['external_co2_flux']['value']=-10000
    elif failure=='step-balance':
        old=c.driver.stage.integrate
        def corrupt(**kw):
            r=old(**kw);r['integrated_transfers']['photosynthesis']['value']+=1;return r
        monkeypatch.setattr(c.driver.stage,'integrate',corrupt)
    else:
        old=c.driver.management.apply_management
        def corrupt(**kw):
            r=old(**kw);r['removed']['canopy_sensible_energy']['value']+=1;return r
        monkeypatch.setattr(c.driver.management,'apply_management',corrupt)
    b,initial,chunks=prepared(profiles,case);assert chunks[-1]['status']=='hold'
    forbid(monkeypatch);artifact=write(model,tmp_path,b,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as reader:
        result=reader.summary;assert result['status']=='hold' and result['checkpoint'] is None
        assert result['last_confirmed']==chunks[-1]['last_confirmed'] and result['hold']==chunks[-1]['hold']
        assert result['times']['hold']['at']==clock.at_index(b,result['hold']['step_index'])
        for kind in ('samples','events'):assert [r['value'] for r in all_rows(reader,kind)]==[v for chunk in chunks for v in chunk[kind]]


def paths(directory,artifact):
    head=json.loads((directory/'HEAD').read_bytes());root=json.loads((directory/(artifact+'.json')).read_bytes())
    header=json.loads((directory/(head['header_sha256']+'.json')).read_bytes());commit=json.loads((directory/(root['commits'][0]+'.json')).read_bytes())
    return {'head':directory/'HEAD','root':directory/(artifact+'.json'),'header':directory/(head['header_sha256']+'.json'),
        'context':directory/(header['context_blob_sha256']+'.json'),'commit':directory/(root['commits'][0]+'.json'),
        'sample':directory/(commit['pages']['samples'][0]['sha256']+'.json'),'event':directory/(commit['pages']['events'][0]['sha256']+'.json')}


@pytest.mark.parametrize('target',('head','root','header','context','commit','sample','event'))
def test_changed_selected_bytes_reject_and_release_fds(model,profiles,tmp_path,target):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks);p=paths(tmp_path,artifact)[target]
    p.chmod(0o600);p.write_bytes(p.read_bytes()+b' ');before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,artifact)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',('symlink','fifo','missing','oversize','mode','hardlink'))
def test_late_selected_file_change_rejects_and_closes(model,profiles,tmp_path,kind):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks);p=paths(tmp_path,artifact)['sample']
    with model.open_artifact(tmp_path,artifact) as reader:
        raw=p.read_bytes();p.unlink()
        if kind=='symlink':target=tmp_path/'redirect';target.write_bytes(raw);p.symlink_to(target)
        elif kind=='fifo':os.mkfifo(p)
        elif kind=='oversize':
            with p.open('wb') as f:f.truncate(2*1024**2+1)
        elif kind=='mode':p.write_bytes(raw);p.chmod(0o777)
        elif kind=='hardlink':target=tmp_path/'extra-link';target.write_bytes(raw);target.chmod(0o400);os.link(target,p)
        with pytest.raises(model.JointStorageHold):reader.page('samples')
        assert reader.closed


def test_permission_change_during_read_and_private_directory_lock_modes(model,profiles,tmp_path,monkeypatch):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks);p=paths(tmp_path,artifact)['sample'];inode=p.stat().st_ino
    with model.open_artifact(tmp_path,artifact) as reader:
        original=model._secure;changed=[]
        def mutate(fd,**kw):
            info=original(fd,**kw)
            if info.st_ino==inode and not changed:p.chmod(0o777);changed.append(True)
            return info
        monkeypatch.setattr(model,'_secure',mutate)
        with pytest.raises(model.JointStorageHold):reader.page('samples')
        assert changed and reader.closed
    monkeypatch.setattr(model,'_secure',original)
    directory=tmp_path/'bad-directory';directory.mkdir(mode=0o777);directory.chmod(0o777)
    with pytest.raises(model.JointStorageHold):model.create_writer(directory,b,initial)
    directory.chmod(0o700);lock=directory/'.writer-lock';lock.write_bytes(b'');lock.chmod(0o777)
    with pytest.raises(model.JointStorageHold):model.create_writer(directory,b,initial)
    assert not (directory/'HEAD').exists()


def test_root_metadata_rejection_has_storage_error_and_closes_fd(model,profiles,tmp_path,monkeypatch):
    b,initial,chunks=prepared(profiles);before=len(os.listdir('/proc/self/fd'))
    def denied(fd):raise ValueError('synthetic denied ACL metadata')
    monkeypatch.setattr(model.file_metadata,'_no_acl',denied)
    with pytest.raises(model.JointStorageHold):model.create_writer(tmp_path,b,initial)
    assert len(os.listdir('/proc/self/fd'))==before and not (tmp_path/'HEAD').exists()


@pytest.mark.parametrize('bad',(None,False,'','0'*64,'x'*64))
def test_trusted_root_is_required(model,profiles,tmp_path,bad):
    b,initial,chunks=prepared(profiles);write(model,tmp_path,b,initial,chunks)
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,bad)


def test_stale_head_foreign_binding_checkpoint_and_terminal_position(model,profiles,tmp_path):
    b,initial,chunks=prepared(profiles)
    with model.create_writer(tmp_path,b,initial) as writer:
        old=writer.head_sha256;writer.append(chunks[0],expected_chunk_sha256=clock.source_chunk_sha256(b._context,chunks[0]));current=writer.head_sha256
    other=clock.prepare_binding(b._context,origin=times.origin('2026-10-02T00:00:00Z'))
    for head,binding,cp in ((old,b,chunks[0]['checkpoint']),(current,other,chunks[0]['checkpoint']),(current,b,initial)):
        with pytest.raises(model.JointStorageHold):model.open_writer(tmp_path,head,binding,cp)
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,current)
    with model.open_writer(tmp_path,current,b,chunks[0]['checkpoint']) as writer:
        with pytest.raises(model.JointStorageHold):writer.finalize()
        assert writer.closed
    assert json.loads((tmp_path/'HEAD').read_bytes())['artifact_sha256'] is None


def test_second_writer_duplicate_create_and_sparse_budget_preserve_original(model,profiles,tmp_path):
    b,initial,chunks=prepared(profiles)
    with model.create_writer(tmp_path,b,initial) as writer:
        raw=(tmp_path/'HEAD').read_bytes()
        with pytest.raises(model.JointStorageHold):model.create_writer(tmp_path,b,initial)
        assert not writer.closed and (tmp_path/'HEAD').read_bytes()==raw
    with pytest.raises(model.JointStorageHold):model.create_writer(tmp_path,b,initial)
    assert (tmp_path/'HEAD').read_bytes()==raw
    directory=tmp_path/'oversize';directory.mkdir(mode=0o700)
    with (directory/'orphan').open('wb') as f:f.truncate(512*1024**2+1)
    with pytest.raises(model.JointStorageHold):model.create_writer(directory,b,initial)
    assert not (directory/'HEAD').exists()


@pytest.mark.parametrize('operation',('bad-digest','changed-source','append-terminal','finalize-initial','closed','binding','checkpoint'))
def test_invalid_operation_preserves_head_and_releases_handle(model,profiles,tmp_path,operation):
    b,initial,chunks=prepared(profiles,budget=128 if operation=='append-terminal' else 7);writer=model.create_writer(tmp_path,b,initial)
    if operation=='append-terminal':writer.append(chunks[0],expected_chunk_sha256=clock.source_chunk_sha256(b._context,chunks[0]))
    if operation=='closed':writer.close()
    chunk=chunks[0];raw=(tmp_path/'HEAD').read_bytes();digest=clock.source_chunk_sha256(b._context,chunk)
    if operation=='changed-source':chunk['samples'][0]['climate_state']['air_co2_mass']['value']+=1
    if operation=='binding':writer.binding=clock.prepare_binding(b._context,origin=times.origin('2026-10-02T00:00:00Z'))
    if operation=='checkpoint':writer.checkpoint=chunks[0]['checkpoint'];chunk=chunks[1];digest=clock.source_chunk_sha256(b._context,chunk)
    with pytest.raises(model.JointStorageHold):
        if operation=='finalize-initial':writer.finalize()
        else:writer.append(chunk,expected_chunk_sha256='0'*64 if operation=='bad-digest' else digest)
    assert writer.closed and (tmp_path/'HEAD').read_bytes()==raw


@pytest.mark.parametrize('start,limit,kind',((True,1,'samples'),(-1,1,'samples'),(6,1,'samples'),(0,0,'samples'),
    (0,65,'samples'),(0,9,'events'),(0,False,'samples'),(0,1,'unknown')))
def test_query_ranges_are_bounded(model,profiles,tmp_path,start,limit,kind):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks)
    with model.open_artifact(tmp_path,artifact) as reader:
        with pytest.raises(model.JointStorageHold):reader.page(kind,start=start,limit=limit)
        assert reader.closed


@pytest.mark.parametrize('dependency',('co2_rhs','gas','net','air_mass','solar_rhs','PAR','NIR','ventilation','calendar_helpers','file_store','notice'))
def test_changed_dependency_rejects_without_touching_original(model,profiles,tmp_path,monkeypatch,dependency):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks)
    path=model._SOURCES[dependency];digest=sha256(path.read_bytes()).hexdigest();changed=tmp_path/'changed-dependency';changed.write_bytes(path.read_bytes()+b'\n')
    monkeypatch.setitem(model._SOURCES,dependency,changed);before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,artifact)
    assert len(os.listdir('/proc/self/fd'))==before and sha256(path.read_bytes()).hexdigest()==digest


@pytest.mark.parametrize('target',('code','dependency','limits'))
def test_changed_current_code_or_limits_reject(model,profiles,tmp_path,monkeypatch,target):
    b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks)
    if target=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif target=='dependency':monkeypatch.setattr(model,'DEPENDENCY_SHA256',{})
    else:monkeypatch.setitem(model.LIMITS,'samples_per_page',32)
    with pytest.raises(model.JointStorageHold):model.open_artifact(tmp_path,artifact)


def test_full_co2_initial_source_profiles_journal_and_copies_are_preserved(model,profiles,tmp_path,monkeypatch):
    b,initial,chunks=prepared(profiles);forbid(monkeypatch);artifact=write(model,tmp_path,b,initial,chunks)
    context=json.loads(paths(tmp_path,artifact)['context'].read_bytes())
    assert context['program']==b._context.program and context['initial_rhs']==json.loads(b._context._first)
    assert {'co2','solar_rhs','net_exchange','air_co2_rhs'}<=set(context['initial_rhs'])
    assert context['manifest']['identity']['journal_schema']=='joint-co2-solar-event-journal-v2'
    assert {'gas','net','air_mass','co2_rhs','solar_rhs','PAR','NIR','ventilation','calendar_helpers','file_store'}<=set(model.DEPENDENCY_SHA256)
    with model.open_artifact(tmp_path,artifact) as reader:
        before=reader.summary;copy=reader.summary;copy['last_confirmed']['climate_state']['air_co2_mass']['value']=0
        page=reader.page('samples');page['records'][0]['value']['plant_state']['leaf']['value']=0
        assert reader.summary==before and reader.page('samples')['records'][0]['value']==chunks[0]['samples'][0]
        assert reader.summary['last_confirmed']['forcing_step_index']==16


@pytest.mark.parametrize('direction',('solar-to-co2','co2-to-solar'))
def test_old_solar_artifacts_are_incompatible_and_unchanged(model,profiles,tmp_path,direction):
    import test_crop_greenhouse_solar_storage as old
    if direction=='solar-to-co2':
        b,initial,chunks=old.prepared(profiles);artifact=old.write(tmp_path,b,initial,chunks);reader=model
    else:
        b,initial,chunks=prepared(profiles);artifact=write(model,tmp_path,b,initial,chunks);reader=old.model
    raw=(tmp_path/'HEAD').read_bytes()
    with pytest.raises(reader.JointStorageHold):reader.open_artifact(tmp_path,artifact)
    assert (tmp_path/'HEAD').read_bytes()==raw


def test_maximum128_records_events_forcing_actual_page_and_response_caps(model,profiles,tmp_path,monkeypatch):
    case=deepcopy(CASES[0]);case.update(step_seconds=.0625,step_count=128,output_steps=list(range(129)),events=[])
    initial=case['forcing_program'][0];case['forcing_program']=[{**deepcopy(initial),'step_index':i} for i in range(129)]
    source=producer.reference.BY_ID['multiple']['events'][0]['event']
    for i in range(128):
        e=deepcopy(source);e['input_id']='co2-storage-max-'+str(i);e['values']['leaf']['value']=e['values']['stem_root']['value']=0
        for q in e['values']['fruit_fraction']:q['value']=0
        case['events'].append({'step_index':i,'event':e})
    b,initial,chunks=prepared(profiles,case,128);forbid(monkeypatch);artifact=write(model,tmp_path,b,initial,chunks)
    pages=[];responses=[]
    with model.open_artifact(tmp_path,artifact) as reader:
        assert reader.summary['counts']=={'samples':129,'events':128}
        for kind in ('samples','events'):
            expected=[v for chunk in chunks for v in chunk[kind]];assert [r['value'] for r in all_rows(reader,kind)]==expected
            pages.extend((tmp_path/(d['sha256']+'.json')).stat().st_size for d in reader._index[kind])
            for start in (0,len(expected)-1):responses.append(len(model._canonical(reader.page(kind,start=start))))
    assert max(pages)<=2*1024**2 and max(responses)<=2*1024**2
    print(json.dumps({'co2_storage_maximum':{'samples':129,'events':128,'forcing_rows':129,'largest_page_bytes':max(pages),'largest_response_bytes':max(responses),'stored_files':len(list(tmp_path.iterdir())),'stored_bytes':sum(p.stat().st_size for p in tmp_path.iterdir() if p.is_file())}}))
