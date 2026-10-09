"""Current original bytes and reviews must precede any downstream farm binding."""
from copy import deepcopy
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_climate_joint_input_evidence as model
import test_crop_climate_joint_time as reference

profiles=reference.profiles
KEY=b'owned-joint-input-evidence-test-key-32!'


def packet(directory,profiles,case=None,origin=None):
    case=reference.reference.CASES[6] if case is None else case
    origin=reference.origin() if origin is None else origin
    directory.mkdir(mode=0o700)
    source={'version':model.SOURCE_VERSION,**{k:case[k] for k in ('scenario','events','output_steps','step_seconds','step_count')},
        'time_origin':origin}
    raw=model._canonical(source);root=sha256(raw).hexdigest()
    original={'source.json':raw,'notice.txt':model._SOURCES['notice'].read_bytes(),
        **{name+'.json':profiles[name+'_profile'].raw_bytes for name in model.continuation.PROFILE_NAMES}}
    for name,data in original.items():
        p=directory/name;p.write_bytes(data);p.chmod(0o400)
    binding=model.clock.prepare_binding(reference.reference.context(profiles,case),origin=origin)
    review={'evidence_id':'owned-software-review-v1','reviewer_id':'owned-test-reviewer','decision_id':'owned-decision-v1',
        'source_sha256':root,'status':'accepted_for_software_validation','scope':model.SCOPE}
    return directory,root,binding,review


def authority(review,**kw):
    return model.JointInputEvidenceAuthority(integrity_key=kw.get('key',KEY),issuer_id=kw.get('issuer','owned-test'),
        key_id=kw.get('key_id','owned-key-v1'),review_resolver=kw.get('resolver',lambda _:deepcopy(review)))


def issue(server,p):return server.issue(p[0],p[1],binding=p[2],review_id=p[3]['evidence_id'])
def verify(server,p,raw,**kw):return server.verify(p[0],kw.get('source',p[1]),raw,
    expected_context_sha256=kw.get('context',p[2]._context.root_sha256),expected_binding_sha256=kw.get('binding',p[2].sha256))


@pytest.fixture
def prepared(tmp_path,profiles):return packet(tmp_path/'inputs',profiles)


@pytest.mark.parametrize('index',range(9))
def test_original_program_and_time_preserved_issue_one_initial_rhs_then_verify_zero(profiles,tmp_path,monkeypatch,index):
    p=packet(tmp_path/'inputs',profiles,reference.reference.CASES[index]);server=authority(p[3]);calls=[]
    original=model.joint.evaluate_rhs
    def rhs(**kw):calls.append('initial');return original(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',rhs)
    before=len(os.listdir('/proc/self/fd'));raw=issue(server,p);assert calls==['initial']
    reference.forbid_numerics(monkeypatch)
    monkeypatch.setattr(model.continuation,'prepare_context',lambda **kw:pytest.fail('verification rebuilt context'))
    monkeypatch.setattr(model.clock,'prepare_binding',lambda *a,**kw:pytest.fail('verification rebuilt UTC binding'))
    receipt=verify(server,p,raw);assert receipt.record==model._record(p[2])
    assert receipt.evidence_sha256==sha256(raw).hexdigest() and not receipt.rights_or_gate_approval
    assert receipt.referenced_bytes==sum(f.stat().st_size for f in p[0].iterdir())
    copied=receipt.record;copied['program']['scenario']['plant_state']['leaf']['value']=0
    assert copied!=receipt.record and len(os.listdir('/proc/self/fd'))==before
    assert KEY not in raw and json.loads(raw)['payload']['G0_G4']=='not_assessed'


@pytest.mark.parametrize('kind',('source','growth','cohort','transport','exchange','notice','missing','extra','writable',
    'directory-mode','file-symlink','directory-symlink','ancestor-symlink','hardlink','FIFO','oversize'))
def test_current_source_storage_failures_reject_without_fd_leaks(prepared,tmp_path,kind):
    p=prepared;server=authority(p[3]);raw=issue(server,p);target=p[0]/'source.json';directory=p[0]
    if kind in ('source','growth','cohort','transport','exchange','notice'):
        target=p[0]/('notice.txt' if kind=='notice' else kind+'.json');target.chmod(0o600)
        target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
    elif kind=='missing':target.unlink()
    elif kind=='extra':(directory/'extra.json').write_bytes(b'[]')
    elif kind=='writable':target.chmod(0o600)
    elif kind=='directory-mode':directory.chmod(0o755)
    elif kind=='file-symlink':
        outside=tmp_path/'outside';outside.write_bytes(target.read_bytes());target.unlink();target.symlink_to(outside)
    elif kind=='directory-symlink':directory.rename(tmp_path/'original');directory.symlink_to(tmp_path/'original',target_is_directory=True)
    elif kind=='ancestor-symlink':
        parent=tmp_path/'link';parent.symlink_to(tmp_path,target_is_directory=True);p=(parent/'inputs',*p[1:])
    elif kind=='hardlink':os.link(target,tmp_path/'other-link')
    elif kind=='FIFO':target.unlink();os.mkfifo(target,mode=0o400)
    else:target.chmod(0o600);target.write_bytes(b' '*(model.MAX_SOURCE_BYTES+1));target.chmod(0o400)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(model.JointInputEvidenceHold):verify(server,p,raw)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',('mac','payload','version','scope','gate','QC','normalization','source-schema','timestamp',
    'seed','initial-rhs','profile','time','environment','extra','duplicate','nonfinite','noncanonical','oversize','context-sha','binding-sha','source-sha',
    'key','issuer','key-id'))
def test_mixed_or_forged_signed_metadata_never_verifies(prepared,kind):
    p=prepared;server=authority(p[3]);raw=issue(server,p);v=json.loads(raw);payload=v['payload'];resign=True;kw={}
    if kind=='mac':v['hmac_sha256']='0'*64;resign=False
    elif kind=='payload':payload['review']['decision_id']='changed';resign=False
    elif kind in ('version','scope','gate','QC','normalization','source-schema','timestamp'):
        key={'gate':'G0_G4','QC':'qc_version','normalization':'normalization_version','source-schema':'source_schema','timestamp':'validated_at'}.get(kind,kind)
        payload[key]='unknown'
    elif kind=='seed':payload['record']['program']['scenario']['plant_state']['leaf']['value']+=1
    elif kind=='initial-rhs':payload['record']['initial_rhs']['scenario']['plant_state']['leaf']['value']+=1
    elif kind=='profile':payload['record']['manifest']['identity']['profile_sha256']['growth']='0'*64
    elif kind=='time':payload['record']['binding']['origin']['start_at']='2026-10-02T00:00:00Z'
    elif kind=='environment':payload['record']['manifest']['identity']['python_version']='0.0.0'
    elif kind=='extra':payload['extra']='unknown'
    elif kind=='duplicate':raw=b'{"payload":{},"payload":{}}'
    elif kind=='nonfinite':raw=b'{"payload":NaN}'
    elif kind=='noncanonical':raw=b' '+raw
    elif kind=='oversize':raw=b' '*(model.MAX_EVIDENCE_BYTES+1)
    elif kind.endswith('-sha'):kw[{'context-sha':'context','binding-sha':'binding','source-sha':'source'}[kind]]='0'*64
    elif kind=='key':server=authority(p[3],key=b'other-owned-test-joint-key-32-bytes!')
    elif kind=='issuer':server=authority(p[3],issuer='other-issuer')
    else:server=authority(p[3],key_id='other-key')
    if kind not in ('duplicate','nonfinite','noncanonical','oversize'):
        if resign:v['hmac_sha256']=hmac.new(KEY,model.DOMAIN+model._canonical(payload),'sha256').hexdigest()
        raw=model._canonical(v)
    with pytest.raises(model.JointInputEvidenceHold):verify(server,p,raw,**kw)


@pytest.mark.parametrize('field,value',(('status','revoked'),('scope','G0'),('source_sha256','0'*64),
    ('reviewer_id','different-reviewer'),('decision_id','different-decision'),('evidence_id','different-evidence')))
def test_current_review_changes_revoke_old_receipt(prepared,field,value):
    p=prepared;review=deepcopy(p[3]);server=authority(review);raw=issue(server,p);review[field]=value
    with pytest.raises(model.JointInputEvidenceHold):verify(server,p,raw)


@pytest.mark.parametrize('phase',('issue','verify'))
@pytest.mark.parametrize('change',('review','bytes','resolver-error','missing-review'))
def test_review_and_bytes_rechecked_before_return(prepared,phase,change):
    p=prepared;raw=issue(authority(p[3]),p);calls=[]
    def resolver(_):
        calls.append(1);review=deepcopy(p[3])
        if len(calls)==2:
            if change=='review':review['status']='revoked'
            elif change=='bytes':
                target=p[0]/'source.json';target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
            elif change=='resolver-error':raise RuntimeError('private detail must not appear')
            else:return None
        return review
    server=authority(p[3],resolver=resolver)
    with pytest.raises(model.JointInputEvidenceHold,match='^joint input validation evidence unavailable$'):
        issue(server,p) if phase=='issue' else verify(server,p,raw)


@pytest.mark.parametrize('change',('source-unit','source-origin','source-version','time','event','code-path','configuration','profiles'))
def test_invalid_issue_or_changed_authority_is_rejected(prepared,change,tmp_path,monkeypatch):
    p=prepared;server=authority(p[3]);raw=issue(server,p)
    if change in ('source-unit','source-origin','source-version','time','event'):
        target=p[0]/'source.json';v=json.loads(target.read_bytes())
        if change=='source-unit':v['scenario']['plant_state']['leaf']['unit']='wrong'
        elif change=='source-origin':v['scenario']['origin']='measured'
        elif change=='source-version':v['version']='unknown'
        elif change=='time':v['time_origin']['start_at']='2026-10-02T00:00:00Z'
        else:v['events'][0]['event']['values']['fruit_fraction'][0]['value']=2
        target.chmod(0o600);target.write_bytes(model._canonical(v));target.chmod(0o400)
        root=sha256(target.read_bytes()).hexdigest();review={**p[3],'source_sha256':root};p=(p[0],root,p[2],review);server=authority(review)
        with pytest.raises(model.JointInputEvidenceHold):issue(server,p)
    else:
        if change=='configuration':server.key_id='changed'
        elif change=='code-path':
            changed=tmp_path/'changed.py';changed.write_text('changed');monkeypatch.setattr(model.clock,'__file__',str(changed))
        else:
            changed=tmp_path/'changed-profile';changed.write_bytes(b'changed');monkeypatch.setitem(model._SOURCES,'rhs',changed)
        with pytest.raises(model.JointInputEvidenceHold):verify(server,p,raw)


def test_fresh_python_verifies_without_context_setup_or_numerics(prepared,tmp_path):
    p=prepared;raw=issue(authority(p[3]),p);receipt=tmp_path/'receipt';receipt.write_bytes(raw)
    pack=tmp_path/'request';pack.write_text(json.dumps({'directory':str(p[0]),'source':p[1],
        'context':p[2]._context.root_sha256,'binding':p[2].sha256,'review':p[3],'receipt':str(receipt)}))
    script='''import json,sys
from pathlib import Path
import test_crop_climate_joint_input_evidence as t
m=t.model;p=json.loads(Path(sys.argv[1]).read_bytes());calls=[]
def forbidden(*a,**kw):calls.append(1);raise AssertionError('unexpected physical setup')
for target,name in ((m.continuation,'prepare_context'),(m.continuation,'start'),(m.continuation,'restore_checkpoint'),(m.continuation,'advance_chunk'),(m.joint,'evaluate_rhs'),(m.continuation.driver.short,'integrate'),(m.continuation.driver.management,'apply_management'),(m.clock,'prepare_binding')):setattr(target,name,forbidden)
result=t.authority(p['review']).verify(p['directory'],p['source'],Path(p['receipt']).read_bytes(),expected_context_sha256=p['context'],expected_binding_sha256=p['binding'])
print(json.dumps({'context':result.record['context_sha256'],'binding':result.record['binding_sha256'],'calls':len(calls),'gates':result.rights_or_gate_approval}))
'''
    child=subprocess.run([sys.executable,'-B','-c',script,str(pack)],capture_output=True,timeout=20,check=True)
    assert json.loads(child.stdout)=={'context':p[2]._context.root_sha256,'binding':p[2].sha256,'calls':0,'gates':False}


def test_current_runtime_environment_change_rejects_old_receipt(prepared,monkeypatch):
    server=authority(prepared[3]);raw=issue(server,prepared)
    monkeypatch.setattr(model.continuation.platform,'python_version',lambda:'different-runtime')
    with pytest.raises(model.JointInputEvidenceHold):verify(server,prepared,raw)


def test_invalid_initial_rhs_does_not_issue_or_leak_private_failure(prepared,monkeypatch):
    before=len(os.listdir('/proc/self/fd'))
    def fail(**kw):raise model.joint.JointClimateHold('private input detail')
    monkeypatch.setattr(model.joint,'evaluate_rhs',fail)
    with pytest.raises(model.JointInputEvidenceHold,match='^joint input validation evidence unavailable$'):
        issue(authority(prepared[3]),prepared)
    assert len(os.listdir('/proc/self/fd'))==before


def test_maximum_schedule_receipt_and_closed_source_bounds(profiles,tmp_path):
    case=deepcopy(reference.reference.CASES[6]);event=case['events'][0]['event']
    case.update(step_seconds=.125,step_count=511,output_steps=list(range(512)),events=[])
    for index in range(128):
        changed={**deepcopy(event),'input_id':f'synthetic-evidence-max-{index}'}
        case['events'].append({'step_index':index,'event':changed})
    p=packet(tmp_path/'inputs',profiles,case);server=authority(p[3]);raw=issue(server,p)
    assert len(raw)<=model.MAX_EVIDENCE_BYTES and (p[0]/'source.json').stat().st_size<=model.MAX_SOURCE_BYTES
    result=verify(server,p,raw)
    assert len(result.record['program']['events'])==128 and len(result.record['program']['output_steps'])==512


@pytest.mark.parametrize('change',('duplicate','nonfinite','noncanonical','extra','bool-step','bad-time'))
def test_changed_source_digest_does_not_bypass_schema_or_qc(prepared,change):
    directory,_,binding,review=prepared;target=directory/'source.json';v=json.loads(target.read_bytes())
    if change=='duplicate':raw=b'{"version":"one","version":"two"}'
    elif change=='nonfinite':raw=b'{"step_seconds":NaN}'
    elif change=='noncanonical':raw=b' '+target.read_bytes()
    else:
        if change=='extra':v['extra']='unexpected'
        elif change=='bool-step':v['step_seconds']=True
        else:v['time_origin']['start_at']='2026-10-01T00:00:00'
        raw=model._canonical(v)
    target.chmod(0o600);target.write_bytes(raw);target.chmod(0o400)
    root=sha256(raw).hexdigest();review={**review,'source_sha256':root}
    with pytest.raises(model.JointInputEvidenceHold):
        issue(authority(review),(directory,root,binding,review))
