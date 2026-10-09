"""Actual current farm rights, signed producer files and independent exec resume."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg
import pytest

from app import crop_climate_joint_server_custody as model
from test_crop_climate_joint_farm_binding import authoring,farm_setup,profiles,login_database,login_scope
import test_crop_climate_joint_farm_binding as reference

pytestmark=reference.pytestmark
KEY=b'owned-joint-custody-test-secret-32-bytes!'


def save(name,value):
    directory=os.environ.get('OSSF_JOINT_CUSTODY_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())


@pytest.fixture(scope='module',autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup.json',{'schemas':schemas,'roles':roles});assert schemas==roles==0


class Resolver:
    version='owned-joint-custody-resolver-v1'
    def __init__(self,p,proof):self.p=p;self.proof=proof
    def __call__(self,tenant,source,proof):
        assert tenant=='tenant-1' and source==self.p[1] and proof==sha256(self.proof).hexdigest()
        return self.p[0],self.proof


@pytest.fixture
def setup(authoring,tmp_path,profiles,request,monkeypatch):
    case=None
    if getattr(request,'param',None)=='hold':
        case=deepcopy(reference.inputs.reference.reference.CASES[6]);case['events'][-1]['event']['values']['leaf']['value']=50000
    original=reference.inputs.packet
    with monkeypatch.context() as patch:
        if case is not None:patch.setattr(reference.inputs,'packet',lambda directory,profiles,origin=None:original(directory,profiles,case,origin))
        value=reference.build(authoring,tmp_path/'inputs',profiles)
    binding,body,p,proof,principal,rights=value
    root=tmp_path/'custody';root.mkdir(mode=0o700);resolver=Resolver(p,proof)
    custody=model.JointServerCustody(binding,root,input_resolver=resolver,integrity_key=KEY)
    return custody,reference._canonical(body),value


def progress(custody,raw,budget=128):return custody.advance('tenant-1',raw,budget=budget)


def locations(custody,raw):
    identity=model._intent_id('tenant-1',json.loads(raw));directory=custody.directory/identity
    return directory,directory/'artifact',directory/'proofs'


def measured(monkeypatch):
    c=model.continuation;calls={k:0 for k in ('prepare_context','start','restore','advance','RHS','step','event','prepare_binding')}
    for target,name,key in ((c,'prepare_context','prepare_context'),(c,'start','start'),(c,'restore_checkpoint','restore'),
            (c,'advance_chunk','advance'),(c.driver.joint,'evaluate_rhs','RHS'),(c.driver.short,'integrate','step'),
            (c.driver.management,'apply_management','event'),(model.clock,'prepare_binding','prepare_binding')):
        original=getattr(target,name)
        def record(*a,_original=original,_key=key,**kw):calls[_key]+=1;return _original(*a,**kw)
        monkeypatch.setattr(target,name,record)
    return calls


def fresh_pack(tmp_path,value,raw,custody):
    binding,body,p,proof,principal,_=value;replay=binding.farms.replay;scopes=[]
    for s in replay.registry._scopes.values():scopes.append({'tenant_id':s.tenant_id,'point':{'latitude':s.point[0],'longitude':s.point[1]},
        'period_start_utc':s.period_start_utc,'period_end_utc':s.period_end_utc,'goal_id':s.goal_id,'provider_ids':list(s.provider_ids)})
    registry_raw=reference._canonical({'registry_version':'research-registry-v1','registrations':scopes})
    assert sha256(registry_raw).hexdigest()==replay.registry.sha256
    proof_path=tmp_path/'proof.private.json';proof_path.write_bytes(proof);proof_path.chmod(0o400)
    pack={'policy':asdict(binding.jobs.runtime_identity[0]),'dsn':binding.jobs._dsn,'artifacts':str(binding.jobs.artifact_root),
        'principal':{**principal,'scopes':sorted(principal['scopes'])},'scope':replay.thermal.holds._scope_resolver(None,None,None),
        'registry_raw':registry_raw.decode(),'registry_sha256':replay.registry.sha256,'context_id':'context-1',
        'root':str(reference.inputs.reference.reference.ROOT),'review':p[3],'body':body,'proof':str(proof_path),
        'directory':str(p[0]),'custody':str(custody.directory),'expected_progress_sha256':sha256(raw).hexdigest()}
    path=tmp_path/'fresh.private.json';path.write_text(json.dumps(pack));path.chmod(0o600);return path


FRESH_SCRIPT=reference.FRESH_SCRIPT.split('calls={')[0]+'''
import test_crop_climate_joint_server_custody as u
from pytest import MonkeyPatch
packet=(Path(p['directory']),p['body']['input']['source_sha256'],None,review)
resolver=u.Resolver(packet,Path(p['proof']).read_bytes())
custody=u.model.JointServerCustody(service,p['custody'],input_resolver=resolver,integrity_key=u.KEY)
raw=t._canonical(p['body']);before=t.counts(service)
with MonkeyPatch.context() as patch:
 calls=u.measured(patch);saved=custody.inspect('tenant-1',raw)
 assert u.sha256(saved).hexdigest()==p['expected_progress_sha256'] and all(v==0 for v in calls.values())
 done=custody.advance('tenant-1',raw,budget=128);v=json.loads(done);assert v['status']=='completed'
 actual=dict(calls);again=custody.inspect('tenant-1',raw);assert done==again and calls==actual
 review['status']='revoked'
 try:custody.inspect('tenant-1',raw)
 except u.model.JointCustodyHold:pass
 else:raise AssertionError('fresh review revocation allowed')
 assert calls==actual
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
assert t.counts(service)==before
print(json.dumps({'progress':v,'calls':actual,'actual_scram':True,'counts_unchanged':True,'read_calls_zero':True,'review_revocation_rejected':True}))
'''


def test_normal_actual_producer_and_fresh_resume_zero_read_calls(setup,tmp_path,monkeypatch):
    custody,raw,value=setup;binding,body,p,proof,principal,rights=value;before=reference.counts(binding)
    c=model.continuation;expected=c.advance_chunk(p[2]._context,c.start(p[2]._context),128)
    with monkeypatch.context() as patch:
        calls=measured(patch);first=progress(custody,raw,1)
        first_calls=dict(calls);assert json.loads(first)['status']=='yielded' and json.loads(first)['steps']==0
        assert first_calls=={'prepare_context':1,'start':1,'restore':0,'advance':1,'RHS':4,'step':0,'event':1,'prepare_binding':1}
        assert custody.inspect('tenant-1',raw)==first and calls==first_calls
    path=fresh_pack(tmp_path,value,first,custody)
    child=subprocess.Popen([sys.executable,'-B','-c',FRESH_SCRIPT,str(path)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr=child.communicate(timeout=100);assert child.returncode==0,stderr.decode();fresh=json.loads(stdout)
    assert fresh['calls']=={'prepare_context':1,'start':0,'restore':1,'advance':1,'RHS':87,'step':16,'event':2,'prepare_binding':1}
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch);done=custody.inspect('tenant-1',raw);v=json.loads(done)
        assert v==fresh['progress'] and progress(custody,raw)==done
        assert v['checkpoint']['sha256']==expected['checkpoint'].sha256 and v['last_confirmed']==expected['last_confirmed']
        assert v['counts']=={'samples':3,'events':3} and v['G0_G4']=='not_assessed'
        rows={kind:custody.page('tenant-1',raw,done,kind)['records'] for kind in ('samples','events')}
        for kind in rows:
            assert [r['value'] for r in rows[kind]]==expected[kind]
            assert [r['time']['at'] for r in rows[kind]]==[model.clock.at_index(p[2],r['step_index']) for r in expected[kind]]
        assert all(n==0 for n in calls.values())
        with pytest.raises(model.JointCustodyHold):custody.page('tenant-1',raw,first,'samples')
    directory,artifact,proofs=locations(custody,raw)
    signed=[json.loads(f.read_bytes()) for f in proofs.glob('*.json')]
    assert sorted(x['payload']['sequence'] for x in signed)==[0,1,2,3]
    assert reference.counts(binding)==before and before[2:]==(0,0)
    save('normal.json',{'first':json.loads(first),'first_calls':first_calls,'final':v,'rows':rows,
        'fresh':{**fresh,'PID':child.pid,'actual_exit':child.returncode,'fresh_exec':True},'counts_before_after':[before,reference.counts(binding)],
        'signed_intent':json.loads((directory/'intent.json').read_bytes()),'signed_heads':signed,
        'proof_sequences':[0,1,2,3],'progress_bytes':len(done),'original_checkpoint_sha256':expected['checkpoint'].sha256})


def test_current_rights_inputs_requests_and_locks(setup,monkeypatch):
    custody,raw,value=setup;binding,body,p,proof,principal,rights=value;done=progress(custody,raw)
    before=reference.counts(binding);checked=[];directory,artifact,proofs=locations(custody,raw)
    calls=reference.forbid(monkeypatch)
    for scope in reference.READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError):custody.inspect('tenant-1',raw)
        principal['scopes'].add(scope);checked.append(scope)
    principal['scopes'].remove('crop_result_write');assert custody.inspect('tenant-1',raw)==done
    with pytest.raises(PermissionError):progress(custody,raw)
    principal['scopes'].add('crop_result_write')
    with pytest.raises(PermissionError):custody.inspect('foreign',raw)
    rights.allowed=False
    with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',raw)
    rights.allowed=True;p[3]['status']='revoked'
    with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',raw)
    p[3]['status']='accepted_for_software_validation'
    with monkeypatch.context() as patch:
        patch.setattr(binding.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
        with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',raw)
    for bad in (b'',b' '+raw,b'{"x":1,"x":2}',b'{"x":NaN}',b'\xff'):
        with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',bad)
    for field in ('source_sha256','context_sha256','time_binding_sha256','evidence_sha256'):
        changed=deepcopy(body);changed['input'][field]='0'*64
        if field=='source_sha256':changed['rights']['input_source_sha256']='0'*64
        with pytest.raises(model.JointCustodyConflict):custody.inspect('tenant-1',reference._canonical(changed))
    for budget in (None,True,0,-1,129,1.0,'1'):
        with pytest.raises(model.JointCustodyHold):progress(custody,raw,budget)
    root_fd=model.files.job_store._open_directory_nofollow(custody.directory)
    lock=model.files._file(root_fd,'.custody-lock',lock=True)
    try:
        with pytest.raises(model.JointCustodyPending):custody.inspect('tenant-1',raw)
    finally:os.close(lock);os.close(root_fd)
    source=p[0]/'source.json';original=source.read_bytes();source.chmod(0o600);source.write_bytes(original+b' ');source.chmod(0o400)
    with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',raw)
    source.chmod(0o600);source.write_bytes(original);source.chmod(0o400)
    assert custody.inspect('tenant-1',raw)==done and reference.counts(binding)==before and all(v==0 for v in calls.values())
    quota=custody.directory.parent/'quota';quota.mkdir(mode=0o700)
    capped=model.JointServerCustody(binding,quota,input_resolver=custody.input_resolver,integrity_key=KEY)
    for i in range(model.LIMITS['root_intents']):(quota/sha256(str(i).encode()).hexdigest()).mkdir(mode=0o700)
    with pytest.raises(model.JointCustodyHold):progress(capped,raw)
    assert len([p for p in quota.iterdir() if p.is_dir()])==model.LIMITS['root_intents']
    save('rights.json',{'scopes':checked,'revoked_rights_review_source_rejected':True,'foreign_tenant_rejected':True,
        'request_conflicts':4,'invalid_budgets':7,'raw_rejections':5,'root_intent_limit_checked_before_mkdir':True,
        'live_lock_pending':True,'read_calls':calls,'counts_unchanged':True})


def test_signed_files_tampering_and_late_publication_rejection(setup,monkeypatch):
    custody,raw,value=setup;binding,body,p,proof,principal,rights=value;first=progress(custody,raw,1)
    directory,artifact,proofs=locations(custody,raw);head=json.loads((artifact/'HEAD').read_bytes())
    commit=json.loads((artifact/(head['latest_commit_sha256']+'.json')).read_bytes())
    paths={'intent':directory/'intent.json','proof':proofs/(sha256((artifact/'HEAD').read_bytes()).hexdigest()+'.json'),
        'HEAD':artifact/'HEAD','commit':artifact/(head['latest_commit_sha256']+'.json'),
        'sample':artifact/(commit['pages']['samples'][0]['sha256']+'.json')}
    checked=[];fd_before=len(os.listdir('/proc/self/fd'))
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch)
        for name,path in paths.items():
            old=path.read_bytes();path.chmod(0o600);path.write_bytes(old+b' ');path.chmod(0o400)
            with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',raw)
            path.chmod(0o600);path.write_bytes(old);path.chmod(0o400);checked.append(name)
        for name in ('intent','proof'):
            path=paths[name];old=path.read_bytes();envelope=json.loads(old);envelope['hmac_sha256']='0'*64
            path.chmod(0o600);path.write_bytes(model._canonical(envelope));path.chmod(0o400)
            with pytest.raises(model.JointCustodyHold):custody.inspect('tenant-1',raw)
            path.chmod(0o600);path.write_bytes(old);path.chmod(0o400);checked.append(name+'-canonical-HMAC')
        assert custody.inspect('tenant-1',raw)==first and all(n==0 for n in calls.values())
    original=model.files._immutable
    def withdraw(parent,name,data,maximum,prefix):
        result=original(parent,name,data,maximum,prefix)
        if prefix=='.proof-':rights.allowed=False
        return result
    with monkeypatch.context() as patch:
        patch.setattr(model.files,'_immutable',withdraw)
        with pytest.raises(model.JointCustodyHold):progress(custody,raw,8)
    rights.allowed=True
    after=json.loads(custody.inspect('tenant-1',raw));original=json.loads(first)
    assert {k:v for k,v in after.items() if k not in ('storage_bytes','file_count')}=={k:v for k,v in original.items() if k not in ('storage_bytes','file_count')}
    assert after['storage_bytes']>original['storage_bytes'] and after['file_count']>original['file_count']
    assert len(os.listdir('/proc/self/fd'))==fd_before
    save('tamper.json',{'changed_files':checked,'late_rights_withdrawal_rejected_before_HEAD':True,'original_HEAD_preserved':True,'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))]})


@pytest.mark.parametrize('setup',['hold'],indirect=True)
def test_real_producer_hold_has_original_failed_time_without_trial_rows(setup,monkeypatch):
    custody,raw,value=setup;p=value[2];done=progress(custody,raw);v=json.loads(done)
    assert v['status']=='hold' and v['checkpoint'] is None and v['steps']==16
    assert v['counts']=={'samples':2,'events':2} and v['hold']['step_index']==16
    assert v['last_confirmed']['phase']=='step-end' and v['times']['hold']['at']=='2026-10-01T00:00:32.123456Z'
    calls=reference.forbid(monkeypatch);assert custody.inspect('tenant-1',raw)==done and progress(custody,raw)==done
    rows={kind:custody.page('tenant-1',raw,done,kind)['records'] for kind in ('samples','events')}
    assert all(r['value']['step_index']<16 for kind in rows for r in rows[kind])
    assert all(v==0 for v in calls.values())
    save('hold.json',{'progress':v,'rows':rows,'read_calls':calls,'failed_trial_not_published':True})
