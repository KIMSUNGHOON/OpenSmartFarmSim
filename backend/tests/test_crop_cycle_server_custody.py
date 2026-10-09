"""Signed execution files only; registered-farm SCRAM checks are separate."""
from copy import deepcopy
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_cycle_server_custody as custody
from app import crop_cycle_artifact as artifact
from app import crop_cycle_stream_execution as engine
from test_crop_cycle_artifact import CASES,PROFILES,NOTICE,program,context,read_all

KEY=b'own-synthetic-cycle-file-signing-key-01'
BUDGET={'max_steps':10000,'max_transitions':128}


@pytest.fixture
def journal_setup(tmp_path):
    reader,ctx=context(tmp_path/'input',program())
    root=tmp_path/'server';root.mkdir(mode=0o700)
    request={'study_id':'own-study','revision':'r1','input':{'root_sha256':reader.root_sha256}}
    raw=custody._canonical(request);binding=custody._canonical({'scope':'unregistered_synthetic_file_test','request':request})
    identity=custody._intent_id('own-tenant',request)
    directory=root/identity;directory.mkdir(mode=0o700)
    with reader:
        yield root,directory,ctx,raw,binding


def open_journal(setup,*,create=True,key=KEY,current=None):
    root,directory,ctx,raw,binding=setup
    root_fd=custody._open_directory_nofollow(root);intent_fd=custody._open_directory_nofollow(directory)
    try:
        journal=custody._Journal(root_fd,intent_fd,ctx,binding,'own-tenant',raw,'own-resolver-v1',key,
            current or (lambda:binding),notice_raw=NOTICE,create=create)
    except BaseException:
        os.close(intent_fd);os.close(root_fd);raise
    journal._test_fds=(root_fd,intent_fd)
    return journal


def close_journal(journal):
    journal.close()
    for fd in journal._test_fds:os.close(fd)


def test_first_head_is_signed_before_selection_and_complete_retry_has_no_rhs(journal_setup,monkeypatch):
    journal=open_journal(journal_setup)
    try:
        zero=json.loads(journal.inspect())
        assert zero['steps']==zero['commit_count']==0 and zero['status']=='yielded'
        proof=(journal_setup[1]/'proofs'/(zero['head_sha256']+'.json')).read_bytes()
        assert sha256(proof).hexdigest()==zero['proof_sha256']
        done=journal.advance(BUDGET);value=json.loads(done)
        assert value['status']=='completed' and value['artifact_sha256']
        def forbidden(*args,**kwargs):pytest.fail('read or complete retry ran RHS')
        monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)
        assert journal.advance(BUDGET)==journal.inspect()==done
        rows=journal.page(done,'samples',0,2)
        assert rows['records'][0]['at']==journal_setup[2].start_at
    finally:close_journal(journal)
    fresh=open_journal(journal_setup,create=False)
    try:assert fresh.inspect()==done
    finally:close_journal(fresh)


@pytest.mark.parametrize('kind',['signature','parent','head','intent','version','extra','bool-sequence','missing'])
def test_changed_selected_proof_is_rejected_before_any_rhs(journal_setup,kind,monkeypatch):
    journal=open_journal(journal_setup)
    try:value=json.loads(journal.advance(BUDGET))
    finally:close_journal(journal)
    path=journal_setup[1]/'proofs'/(value['head_sha256']+'.json')
    if kind=='missing':path.unlink()
    else:
        envelope=json.loads(path.read_bytes());body=envelope['payload']
        if kind=='signature':envelope['signature']='0'*64
        if kind=='parent':body['parent']['proof_sha256']='0'*64
        if kind=='head':body['head']['commit_count']=0
        if kind=='intent':body['intent_sha256']='0'*64
        if kind=='version':body['version']='other'
        if kind=='extra':body['filesystem_path']='/tmp/external'
        if kind=='bool-sequence':body['sequence']=True
        if kind!='signature':envelope=json.loads(custody._signed(body,KEY,custody.PROOF_DOMAIN))
        path.chmod(0o600);path.write_bytes(custody._canonical(envelope));path.chmod(0o400)
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a:pytest.fail('bad proof ran RHS'))
    with pytest.raises(custody.CycleCustodyHold):open_journal(journal_setup,create=False)


def test_unsigned_actual_writer_delta_cannot_be_adopted(journal_setup,monkeypatch):
    journal=open_journal(journal_setup)
    try:head=json.loads(journal.inspect())['head_sha256']
    finally:close_journal(journal)
    with artifact.open_writer(journal_setup[1]/'artifact',head,journal_setup[2],notice_raw=NOTICE) as writer:
        writer.advance({'max_steps':1,'max_transitions':1})
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a:pytest.fail('unsigned head ran RHS'))
    with pytest.raises(custody.CycleCustodyHold):open_journal(journal_setup,create=False)


def test_signature_from_another_key_and_noncanonical_envelope_are_held(journal_setup):
    journal=open_journal(journal_setup)
    try:value=json.loads(journal.inspect())
    finally:close_journal(journal)
    with pytest.raises(custody.CycleCustodyHold):open_journal(journal_setup,create=False,key=b'other-synthetic-cycle-key-00000000')
    path=journal_setup[1]/'proofs'/(value['head_sha256']+'.json');path.chmod(0o600)
    path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
    with pytest.raises(custody.CycleCustodyHold):open_journal(journal_setup,create=False)


@pytest.mark.parametrize('kind',['symlink','fifo','hardlink','mode','extra-file'])
def test_private_file_types_modes_and_unknown_files_are_rejected(journal_setup,tmp_path,kind):
    journal=open_journal(journal_setup)
    try:value=json.loads(journal.inspect())
    finally:close_journal(journal)
    path=journal_setup[1]/'proofs'/(value['head_sha256']+'.json')
    if kind in ('symlink','fifo'):path.unlink()
    if kind=='symlink':path.symlink_to(tmp_path/'foreign')
    if kind=='fifo':os.mkfifo(path,0o400)
    if kind=='hardlink':os.link(path,tmp_path/'foreign-proof')
    if kind=='mode':path.chmod(0o644)
    if kind=='extra-file':(journal_setup[1]/'artifact'/'unknown').write_bytes(b'foreign')
    with pytest.raises(custody.CycleCustodyHold):open_journal(journal_setup,create=False)


def test_sparse_orphan_budget_stops_before_next_rhs(journal_setup,monkeypatch):
    journal=open_journal(journal_setup)
    try:
        path=journal_setup[1]/'artifact'/('.blob-'+'0'*32+'.tmp')
        with path.open('wb') as handle:handle.truncate(artifact.LIMITS['directory_bytes'])
        path.chmod(0o600)
        monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a:pytest.fail('over-budget RHS'))
        with pytest.raises(custody.CycleCustodyHold):journal.advance(BUDGET)
    finally:close_journal(journal)


def test_mid_compute_rights_withdrawal_leaves_previous_signed_head(journal_setup,monkeypatch):
    permitted=True
    def current():
        if not permitted:raise custody.CycleCustodyHold('withdrawn synthetic provider')
        return journal_setup[-1]
    journal=open_journal(journal_setup,current=current)
    try:
        before=json.loads(journal.inspect())
        original=engine.advance_chunk
        def changed(*args,**kwargs):
            nonlocal permitted
            result=original(*args,**kwargs);permitted=False;return result
        monkeypatch.setattr(engine,'advance_chunk',changed)
        with pytest.raises(custody.CycleCustodyHold):journal.advance(BUDGET)
        head=json.loads((journal_setup[1]/'artifact'/'HEAD').read_bytes())
        assert head['commit_count']==0 and sha256(artifact._canonical(head)).hexdigest()==before['head_sha256']
    finally:close_journal(journal)


@pytest.mark.parametrize('kind',['source-mode','source-hardlink','source-directory','proof-directory'])
def test_source_privacy_and_stale_directory_handles_stop_before_rhs(journal_setup,tmp_path,monkeypatch,kind):
    journal=open_journal(journal_setup);calls=0;original=engine.advance_chunk
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1;return original(*args,**kwargs)
    monkeypatch.setattr(engine,'advance_chunk',counted)
    root,where,*_=journal_setup;input_path=root.parent/'input'
    if kind=='source-mode':(input_path/'root.json').chmod(0o666)
    if kind=='source-hardlink':os.link(input_path/'root.json',tmp_path/'foreign-input-alias')
    if kind=='source-directory':input_path.chmod(0o755)
    if kind=='proof-directory':
        (where/'proofs').rename(tmp_path/'detached-proofs');(where/'proofs').mkdir(mode=0o700)
    try:
        with pytest.raises(custody.CycleCustodyHold):journal.advance(BUDGET)
        assert calls==0
    finally:close_journal(journal)


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_six_actual_equation_results_remain_original_under_signed_publication(tmp_path,case,monkeypatch):
    from app import crop_plant_startup_integration as original
    expected=original.integrate_plant_startup(**case['program'],**PROFILES)
    reader,ctx=context(tmp_path/'input',case['program']);root=tmp_path/'server';root.mkdir(mode=0o700)
    request={'study_id':'own-study','revision':'r1','input':{'root_sha256':reader.root_sha256}}
    raw=custody._canonical(request);binding=custody._canonical({'scope':'unregistered_synthetic_file_test','request':request})
    where=root/custody._intent_id('own-tenant',request);where.mkdir(mode=0o700)
    with reader:
        journal=open_journal((root,where,ctx,raw,binding))
        try:
            while True:
                progress=journal.advance({'max_steps':17,'max_transitions':31})
                if json.loads(progress)['status']!='yielded':break
            monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a:pytest.fail('signed page invoked RHS'))
            assert json.loads(progress)['steps']==expected['steps']
            for kind,limit in (('samples',64),('events',8)):
                page=journal.page(progress,kind,0,limit)
                assert page['next']==page['total']
                assert artifact._canonical(page['records'])==artifact._canonical(expected[kind])
        finally:close_journal(journal)


def test_rights_withdrawn_during_page_read_prevent_returning_records(journal_setup,monkeypatch):
    permitted=True
    def current():
        if not permitted:raise custody.CycleCustodyHold('withdrawn synthetic display')
        return journal_setup[-1]
    journal=open_journal(journal_setup,current=current)
    try:
        progress=journal.advance(BUDGET);original=artifact.ArtifactReader.page
        def changed(*args,**kwargs):
            nonlocal permitted
            records=original(*args,**kwargs);permitted=False;return records
        monkeypatch.setattr(artifact.ArtifactReader,'page',changed)
        with pytest.raises(custody.CycleCustodyHold):journal.page(progress,'samples',0,1)
    finally:close_journal(journal)


def crash_advance(setup,phase):
    publish=artifact.ArtifactWriter._publish_head;put=custody._immutable
    def killed_put(parent,name,raw,maximum,prefix):
        if prefix=='.proof-' and json.loads(raw)['payload']['action']=='advance':
            if phase=='before-proof':os._exit(41)
            result=put(parent,name,raw,maximum,prefix)
            if phase=='after-proof':os._exit(42)
            return result
        return put(parent,name,raw,maximum,prefix)
    def killed_publish(writer,head):
        if phase=='before-head':os._exit(43)
        publish(writer,head)
        if phase=='after-head':os._exit(44)
    custody._immutable=killed_put;artifact.ArtifactWriter._publish_head=killed_publish
    journal=open_journal(setup,create=False)
    try:journal.advance({'max_steps':1,'max_transitions':1})
    finally:close_journal(journal)


@pytest.mark.parametrize('phase,code,commits',[('before-proof',41,1),('after-proof',42,1),
    ('before-head',43,1),('after-head',44,2)])
def test_actual_process_exit_recovers_only_selected_signed_head(journal_setup,phase,code,commits):
    journal=open_journal(journal_setup)
    try:
        value=json.loads(journal.advance({'max_steps':1,'max_transitions':1}))
        assert value['commit_count']==1 and value['steps']==0
    finally:close_journal(journal)
    child=multiprocessing.get_context('fork').Process(target=crash_advance,args=(journal_setup,phase));child.start()
    try:child.join(30);assert not child.is_alive() and child.exitcode==code
    finally:
        if child.is_alive():child.kill();child.join(5)
    fresh=open_journal(journal_setup,create=False)
    try:
        value=json.loads(fresh.inspect());assert value['commit_count']==commits
        assert value['steps']==(1 if phase=='after-head' else 0)
        while json.loads(fresh.advance({'max_steps':17,'max_transitions':31}))['status']=='yielded':pass
        progress=fresh.inspect()
        from app import crop_plant_startup_integration as original
        expected=original.integrate_plant_startup(**program(),**PROFILES)
        for kind,limit in (('samples',64),('events',8)):
            assert artifact._canonical(fresh.page(progress,kind,0,limit)['records'])==artifact._canonical(expected[kind])
    finally:close_journal(fresh)


def test_initial_unsigned_computation_cannot_replace_known_zero_header(journal_setup,monkeypatch):
    journal=open_journal(journal_setup)
    try:
        journal.advance({'max_steps':1,'max_transitions':1})
    finally:close_journal(journal)
    (journal_setup[1]/'artifact'/'HEAD').unlink()
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a:pytest.fail('unknown initial files ran RHS'))
    with pytest.raises(custody.CycleCustodyHold):open_journal(journal_setup)


def test_known_zero_header_without_head_is_republished_and_no_fd_leak(journal_setup):
    journal=open_journal(journal_setup)
    try:zero=journal.inspect()
    finally:close_journal(journal)
    (journal_setup[1]/'artifact'/'HEAD').unlink()
    before=len(os.listdir('/proc/self/fd'))
    for _ in range(3):
        fresh=open_journal(journal_setup)
        try:assert fresh.inspect()==zero
        finally:close_journal(fresh)
    assert len(os.listdir('/proc/self/fd'))==before


def test_fresh_python_exec_restores_signed_vector_and_reads_without_rhs(journal_setup,tmp_path):
    journal=open_journal(journal_setup)
    try:
        journal.advance({'max_steps':7,'max_transitions':11});expected=[v.hex() for v in journal.writer._checkpoint['y']]
    finally:close_journal(journal)
    root,where,ctx,raw,binding=journal_setup;request_path=tmp_path/'child.json';response=tmp_path/'response.json'
    request_path.write_text(json.dumps({'root':str(root),'where':str(where),'input':str(root.parent/'input'),
        'root_sha256':ctx.reader.root_sha256,'request':raw.decode(),'binding':binding.decode(),'response':str(response)}))
    code="""import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tests'))
from test_crop_cycle_server_custody import open_journal,close_journal,BUDGET
from test_crop_cycle_artifact import PROFILES
from app import crop_cycle_input_stream as inputs,crop_cycle_stream_execution as engine
r=json.loads(Path(sys.argv[1]).read_bytes())
with inputs.open_input_packet(r['input'],r['root_sha256'],**PROFILES) as reader:
 ctx=engine.prepare_context(reader,**PROFILES)
 setup=(Path(r['root']),Path(r['where']),ctx,r['request'].encode(),r['binding'].encode())
 journal=open_journal(setup,create=False)
 try:
  before=[v.hex() for v in journal.writer._checkpoint['y']]
  while json.loads(journal.advance(BUDGET))['status']=='yielded':pass
  progress=journal.inspect()
  def forbidden(*a):raise AssertionError('exec read RHS')
  engine.short._Evaluator.rhs=forbidden
  samples=journal.page(progress,'samples',0,64)['records']
  Path(r['response']).write_text(json.dumps({'before':before,'progress':progress.decode(),'samples':samples}))
 finally:close_journal(journal)
"""
    child=subprocess.run([sys.executable,'-c',code,str(request_path)],capture_output=True,text=True,timeout=45)
    assert child.returncode==0,child.stderr[-2000:]
    result=json.loads(response.read_bytes());assert result['before']==expected
    fresh=open_journal(journal_setup,create=False)
    try:
        assert fresh.inspect().decode()==result['progress']
        assert fresh.page(fresh.inspect(),'samples',0,64)['records']==result['samples']
    finally:close_journal(fresh)


@pytest.mark.parametrize('kind',['intents','root-bytes'])
def test_other_intents_count_toward_root_budget_before_rhs(journal_setup,monkeypatch,kind):
    journal=open_journal(journal_setup);calls=0;advance=engine.advance_chunk
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1;return advance(*args,**kwargs)
    monkeypatch.setattr(engine,'advance_chunk',counted);root=journal_setup[0]
    total=128 if kind=='intents' else 2
    for i in range(total):
        where=root/sha256(('other-owned-intent-'+str(i)).encode()).hexdigest();where.mkdir(mode=0o700)
        if kind=='root-bytes':
            directory=where/'artifact';directory.mkdir(mode=0o700)
            path=directory/('.blob-'+'0'*32+'.tmp')
            with path.open('wb') as handle:handle.truncate(artifact.LIMITS['directory_bytes'])
            path.chmod(0o600)
    try:
        with pytest.raises(custody.CycleCustodyHold):journal.advance(BUDGET)
        assert calls==0
    finally:close_journal(journal)


def test_context_code_and_notice_change_cannot_sign_another_delta(journal_setup,monkeypatch):
    journal=open_journal(journal_setup)
    try:
        monkeypatch.setattr(custody,'CODE_SHA256','0'*64)
        with pytest.raises(custody.CycleCustodyHold):journal.advance(BUDGET)
        monkeypatch.undo();journal.notice=b'foreign notice'
        with pytest.raises(custody.CycleCustodyHold):journal.advance(BUDGET)
    finally:close_journal(journal)


@pytest.mark.parametrize('kind',['pre-onset','late-event'])
def test_numeric_hold_signs_only_original_confirmed_past(tmp_path,kind,monkeypatch):
    from app import crop_plant_startup_integration as original
    p=program('full-removal-reentry' if kind=='late-event' else 'empty-entry')
    if kind=='pre-onset':p['initial_state']['values']['temperature_sum']['value']=0
    else:p['events'][1]['removals']['values']['leaf']['value']=1e6
    expected=original.integrate_plant_startup(**p,**PROFILES);assert expected['status']=='hold'
    reader,ctx=context(tmp_path/'input',p);root=tmp_path/'server';root.mkdir(mode=0o700)
    request={'study_id':'own-study','revision':'r1','input':{'root_sha256':reader.root_sha256}}
    raw=custody._canonical(request);binding=custody._canonical({'scope':'unregistered_synthetic_file_test','request':request})
    where=root/custody._intent_id('own-tenant',request);where.mkdir(mode=0o700)
    with reader:
        journal=open_journal((root,where,ctx,raw,binding))
        try:
            while True:
                progress=journal.advance({'max_steps':17,'max_transitions':31})
                if json.loads(progress)['status']!='yielded':break
            assert json.loads(progress)['status']=='hold' and json.loads(progress)['artifact_sha256']
            monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a:pytest.fail('hold replay ran RHS'))
            for key in ('hold','last_confirmed'):
                assert artifact._canonical(journal.writer._summary[key])==artifact._canonical(expected[key])
            for kind,limit in (('samples',64),('events',8)):
                assert artifact._canonical(journal.page(progress,kind,0,limit)['records'])==artifact._canonical(expected[kind])
        finally:close_journal(journal)
