from copy import deepcopy
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_cycle_calculation_result_evidence as evidence
from app import crop_cycle_input_evidence as input_evidence
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_calculation_context as engine
from test_crop_cycle_artifact import PROFILES, NOTICE, program
from test_crop_cycle_input_stream import write

KEY = b'owned-result-evidence-test-key-32-bytes!'
INPUT_KEY = b'owned-input-evidence-test-key-32-bytes!'


def input_authority():
    return input_evidence.InputEvidenceAuthority(PROFILES, NOTICE, integrity_key=INPUT_KEY,
        issuer_id='owned-input-test', key_id='input-v1')


def authority(key=KEY, issuer='owned-result-test', key_id='result-v1'):
    return evidence.CalculationResultEvidenceAuthority(input_authority(), integrity_key=key,
        issuer_id=issuer, key_id=key_id)


def case(tmp_path, name='empty-entry', held=False):
    raw=program(name)
    if held:
        raw['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value']=100
    input_directory, result_directory = tmp_path/'inputs', tmp_path/'artifact'
    root=write(input_directory, raw)['root_sha256']
    for path in input_directory.iterdir():path.chmod(0o400)
    input_raw=input_authority().issue(input_directory, root)
    with engine.open_calculation_context(input_directory, root, input_raw, authority=input_authority()) as original:
        with artifact.create_writer(result_directory, original, notice_raw=NOTICE) as writer:
            while writer.advance({'max_steps':17, 'max_transitions':31})['status']=='yielded':pass
            receipt=writer.finalize()
        with artifact.open_artifact(result_directory, receipt['artifact_sha256'], original, notice_raw=NOTICE) as parsed:
            expected=parsed.summary; index=deepcopy(parsed._index)
    args=(result_directory, receipt['artifact_sha256'], input_directory, root, input_raw)
    return args, expected, index


@pytest.mark.parametrize('name',['empty-entry','full-removal-reentry','positive-tail'])
def test_actual_terminal_QC_then_current_bytes_without_parser_or_RHS(tmp_path, monkeypatch, name):
    args, expected, index=case(tmp_path, name)
    server=authority(); before=len(os.listdir('/proc/self/fd'))
    calls=[]; original=artifact.open_artifact
    def checked(*a,**k):
        calls.append('original-terminal-QC');return original(*a,**k)
    monkeypatch.setattr(artifact,'open_artifact',checked)
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('receipt ran RHS'))
    raw=server.issue(*args)
    assert calls==['original-terminal-QC']
    for module, name in ((artifact,'open_artifact'),(artifact,'_validate_delta'),
                         (artifact._Files,'_load_prefix'),(inputs,'open_input_packet'),
                         (engine.legacy,'prepare_context'),(engine,'open_calculation_context')):
        monkeypatch.setattr(module,name,lambda *a,**k:pytest.fail('verify repeated original parser'))
    verified=server.verify(*args,raw)
    assert type(verified) is evidence.VerifiedCalculationResultEvidence
    assert verified.summary==expected and verified.index==index
    assert verified.context['manifest']==expected['manifest']
    assert verified.identity['artifact_sha256']==args[1]
    assert verified.identity['math_context_sha256']==engine._hash(expected['manifest'])
    original=input_authority().verify(args[2],args[3],args[4]).context
    validation=verified.context['manifest']['input_validation']
    assert validation['validated_context_sha256']==original['context_sha256']
    assert validation['evidence_sha256']==sha256(args[4]).hexdigest()
    assert verified.context['context_sha256']!=original['context_sha256']
    for key in original:
        if key not in ('manifest','context_sha256'):assert verified.context[key]==original[key]
    assert verified.evidence_sha256==sha256(raw).hexdigest()
    assert verified.rights_or_gate_approval is False
    copied=verified.summary;copied['counts']['samples']=999
    assert copied!=verified.summary
    copied=verified.index;copied['samples'].clear()
    assert copied!=verified.index
    copied=verified.context;copied['seed'][0]+=1
    assert copied!=verified.context
    assert len(os.listdir('/proc/self/fd'))==before


def test_numeric_hold_keeps_exact_confirmed_past_and_never_becomes_completion(tmp_path):
    args, expected, index=case(tmp_path, held=True)
    server=authority(); raw=server.issue(*args);verified=server.verify(*args,raw)
    assert expected['status']=='hold'
    assert verified.summary==expected and verified.index==index
    assert verified.summary['checkpoint'] is None
    assert verified.summary['hold']==expected['hold']


@pytest.mark.parametrize('change',['HEAD','root','blob','missing','extra','writable','hardlink',
    'file-symlink','directory-symlink','directory-mode','directory-replacement','writer-lock'])
def test_current_result_physical_changes_reject_and_close(tmp_path,change):
    args, _, _=case(tmp_path);server=authority();raw=server.issue(*args)
    directory=args[0];target=next(p for p in directory.iterdir() if p.name.endswith('.json') and p.stem!=args[1])
    if change=='HEAD':target=directory/'HEAD'
    if change=='root':target=directory/(args[1]+'.json')
    if change in ('HEAD','root','blob'):
        old=target.read_bytes();target.chmod(0o600);target.write_bytes(old+b' ');target.chmod(0o400)
    elif change=='missing':target.unlink()
    elif change=='extra':(directory/'unexpected.json').write_bytes(b'[]')
    elif change=='writable':target.chmod(0o600)
    elif change=='hardlink':os.link(target,tmp_path/'other-link')
    elif change=='file-symlink':
        outside=tmp_path/'outside';outside.write_bytes(target.read_bytes());target.unlink();target.symlink_to(outside)
    elif change=='directory-symlink':
        directory.rename(tmp_path/'original');directory.symlink_to(tmp_path/'original',target_is_directory=True)
    elif change=='directory-mode':directory.chmod(0o755)
    elif change=='directory-replacement':
        directory.rename(tmp_path/'old');directory.mkdir(mode=0o700)
    else:(directory/'.writer-lock').write_bytes(b'changed')
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['signature','wrong-key','wrong-id','wrong-issuer','version',
    'artifact','input','input-evidence','summary','index','context','duplicate','NaN','noncanonical','oversize'])
def test_untrusted_or_authenticated_invalid_result_proof_rejects(tmp_path,change):
    args, _, _=case(tmp_path);server=authority();raw=server.issue(*args);data=json.loads(raw)
    args=list(args)
    if change=='signature':data['hmac_sha256']='0'*64;raw=inputs._canonical(data)
    elif change=='wrong-key':server=authority(key=b'other-owned-result-key-32-bytes-long!')
    elif change=='wrong-id':server=authority(key_id='rotated')
    elif change=='wrong-issuer':server=authority(issuer='other')
    elif change=='artifact':args[1]='0'*64
    elif change=='input':args[3]='0'*64
    elif change=='input-evidence':args[4]=b'{}'
    elif change in ('version','summary','index','context'):
        payload=data['payload']
        if change=='version':payload['version']='unknown'
        elif change=='summary':payload['summary']['counts']['samples']+=1
        elif change=='index':payload['index']['samples'][0]['start']=9
        else:payload['context_sha256']='0'*64
        data['hmac_sha256']=hmac.new(KEY,evidence.DOMAIN+inputs._canonical(payload),'sha256').hexdigest()
        raw=inputs._canonical(data)
    elif change=='duplicate':raw=b'{"payload":{},"payload":{},"hmac_sha256":""}'
    elif change=='NaN':raw=b'{"payload":NaN,"hmac_sha256":""}'
    elif change=='noncanonical':raw+=b'\n'
    else:raw=b' '*(evidence.MAX_EVIDENCE_BYTES+1)
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)


def test_wrong_key_is_denied_before_reading_current_data(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);raw=authority().issue(*args);server=authority(key=b'another-owned-result-key-32-bytes!')
    monkeypatch.setattr(input_evidence.InputEvidenceAuthority,'verify',lambda *a,**k:pytest.fail('wrong key read input'))
    monkeypatch.setattr(evidence.files,'_read',lambda *a,**k:pytest.fail('wrong key read result'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)


def test_unknown_authenticated_version_is_denied_before_current_data(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);server=authority();data=json.loads(server.issue(*args))
    data['payload']['version']='unknown'
    data['hmac_sha256']=hmac.new(KEY,evidence.DOMAIN+inputs._canonical(data['payload']),'sha256').hexdigest()
    monkeypatch.setattr(input_evidence.InputEvidenceAuthority,'verify',lambda *a,**k:pytest.fail('unknown version read data'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,inputs._canonical(data))


def test_input_changed_during_result_byte_scan_does_not_return_old_facts(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);server=authority();raw=server.issue(*args);original=evidence._snapshot
    def changed(*a,**k):
        value=original(*a,**k);root=args[2]/'root.json'
        root.chmod(0o600);root.write_bytes(root.read_bytes()+b' ');root.chmod(0o400)
        return value
    monkeypatch.setattr(evidence,'_snapshot',changed)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)
    assert len(os.listdir('/proc/self/fd'))==before


def test_input_directory_replaced_during_result_scan_rejects_same_bytes(tmp_path,monkeypatch):
    import shutil
    args, _, _=case(tmp_path);server=authority();raw=server.issue(*args);original=evidence._snapshot
    def replaced(*a,**k):
        value=original(*a,**k);old=tmp_path/'old-input'
        args[2].rename(old);shutil.copytree(old,args[2]);return value
    monkeypatch.setattr(evidence,'_snapshot',replaced)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)
    assert len(os.listdir('/proc/self/fd'))==before


def test_preterminal_artifact_does_not_issue(tmp_path):
    input_directory=tmp_path/'inputs';root=write(input_directory,program())['root_sha256']
    for path in input_directory.iterdir():path.chmod(0o400)
    input_raw=input_authority().issue(input_directory,root)
    with engine.open_calculation_context(input_directory,root,input_raw,authority=input_authority()) as ctx:
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            writer.advance({'max_steps':1,'max_transitions':1})
    with pytest.raises(evidence.CalculationResultEvidenceHold):
        authority().issue(tmp_path/'artifact','0'*64,input_directory,root,input_raw)


def test_failed_actual_terminal_QC_never_issues_and_closes(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);before=len(os.listdir('/proc/self/fd'))
    def fail(*a,**k):raise artifact.CalculationArtifactHold('own failed QC')
    monkeypatch.setattr(artifact,'open_artifact',fail)
    with pytest.raises(evidence.CalculationResultEvidenceHold):authority().issue(*args)
    assert len(os.listdir('/proc/self/fd'))==before


def test_owned_result_is_checked_before_original_parser(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);(args[0]/'HEAD').chmod(0o600)
    monkeypatch.setattr(artifact,'open_artifact',lambda *a,**k:pytest.fail('unsafe result parsed'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):authority().issue(*args)


def test_result_changed_during_QC_does_not_issue(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);server=authority();original=artifact.open_artifact
    def changed(*a,**k):
        reader=original(*a,**k);head=args[0]/'HEAD'
        head.chmod(0o600);head.write_bytes(head.read_bytes()+b' ');head.chmod(0o400)
        return reader
    monkeypatch.setattr(artifact,'open_artifact',changed)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.issue(*args)
    assert len(os.listdir('/proc/self/fd'))==before


def test_changed_reader_source_on_disk_rejects_proof(tmp_path,monkeypatch):
    args, _, _=case(tmp_path);server=authority();raw=server.issue(*args)
    other=tmp_path/'changed.py';other.write_text('own changed artifact reader')
    monkeypatch.setattr(artifact,'__file__',str(other))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)


def test_same_owned_keys_restart_in_separate_python_and_FD_cleanup(tmp_path):
    args, expected, _=case(tmp_path);raw=authority().issue(*args)
    result_proof=tmp_path/'result-proof.json';result_proof.write_bytes(raw)
    input_proof=tmp_path/'input-proof.json';input_proof.write_bytes(args[4])
    code='''
import os,sys
from pathlib import Path
from test_crop_cycle_calculation_result_evidence import authority
from app import crop_cycle_calculation_result_evidence as evidence
def forbidden(*a,**k):raise AssertionError('fresh verify constructed calculation/parser/QC/RHS')
evidence.calculation.open_calculation_context=forbidden
evidence.inputs.open_input_packet=forbidden
evidence.calculation.legacy.prepare_context=forbidden
evidence.artifact.open_artifact=forbidden
evidence.artifact._Files._load_prefix=forbidden
evidence.artifact._validate_delta=forbidden
evidence.calculation.short._Evaluator.rhs=forbidden
before=len(os.listdir('/proc/self/fd'))
checked=authority().verify(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]),sys.argv[4],Path(sys.argv[5]).read_bytes(),Path(sys.argv[6]).read_bytes())
assert checked.rights_or_gate_approval is False
assert len(os.listdir('/proc/self/fd'))==before
print(checked.summary['checkpoint']['checkpoint_sha256'])
'''
    env=dict(os.environ,PYTHONPATH=str(Path.cwd())+os.pathsep+str(Path.cwd()/'tests'))
    p=subprocess.run([sys.executable,'-c',code,str(args[0]),args[1],str(args[2]),args[3],str(input_proof),str(result_proof)],
        env=env,capture_output=True,timeout=30)
    assert p.returncode==0,(p.stdout+p.stderr).decode(errors='replace')
    assert p.stdout.decode().strip()==expected['checkpoint']['checkpoint_sha256']


@pytest.mark.parametrize('change',['validation','manifest-code','clock','state','output-start','event-start',
    'notice','scope','planned','inventory','snapshot-record','dependency','code','unknown-field','index-time','index-sha'])
def test_authenticated_metadata_must_match_original_stored_rows_and_provenance(tmp_path,change):
    args,_,_=case(tmp_path,'full-removal-reentry');server=authority();data=json.loads(server.issue(*args))
    payload=data['payload'];summary=payload['summary'];cp=summary['checkpoint']
    if change=='validation':summary['manifest']['input_validation']['validated_context_sha256']='0'*64
    elif change=='manifest-code':summary['manifest']['code_sha256']['stream_execution']='0'*64
    elif change=='clock':cp['clock']={}
    elif change=='state':cp['y'][0]+=0.1
    elif change=='output-start':summary['output_start']+=1
    elif change=='event-start':summary['event_start']+=1
    elif change=='notice':summary['notice_raw_utf8']='other notice'
    elif change=='scope':summary['scope']='approved'
    elif change=='planned':summary['planned_steps']=True
    elif change=='inventory':payload['snapshot']['inventory'].pop()
    elif change=='snapshot-record':payload['snapshot']['record_sha256']='0'*64
    elif change=='dependency':payload['dependency_sha256']['calculation_context']='0'*64
    elif change=='code':payload['evidence_code_sha256']='0'*64
    elif change=='unknown-field':payload['approved']=True
    elif change=='index-time':payload['index']['samples'][0]['last_at']='2100-01-01T00:00:00Z'
    else:payload['index']['samples'][0]['sha256']=args[1]
    cp['checkpoint_sha256']=inputs._hash({k:v for k,v in cp.items() if k!='checkpoint_sha256'})
    data['hmac_sha256']=hmac.new(KEY,evidence.DOMAIN+inputs._canonical(payload),'sha256').hexdigest()
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,inputs._canonical(data))
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['hold','confirmed-past'])
def test_authenticated_numeric_hold_metadata_cannot_be_rewritten(tmp_path,change):
    value=program('full-removal-reentry')
    value['events'][1]['removals']['values']['leaf']['value']=1e6
    directory=tmp_path/'inputs';root=write(directory,value)['root_sha256']
    for path in directory.iterdir():path.chmod(0o400)
    input_raw=input_authority().issue(directory,root)
    with engine.open_calculation_context(directory,root,input_raw,authority=input_authority()) as ctx:
        with artifact.create_writer(tmp_path/'artifact',ctx,notice_raw=NOTICE) as writer:
            while writer.advance({'max_steps':17,'max_transitions':31})['status']=='yielded':pass
            receipt=writer.finalize()
    args=(tmp_path/'artifact',receipt['artifact_sha256'],directory,root,input_raw)
    server=authority();raw=server.issue(*args);verified=server.verify(*args,raw)
    assert verified.summary['status']=='hold' and verified.summary['last_confirmed'] is not None
    data=json.loads(raw)
    if change=='hold':data['payload']['summary']['hold']={}
    else:data['payload']['summary']['last_confirmed']['at']='2100-01-01T00:00:00Z'
    data['hmac_sha256']=server._signature(data['payload'])
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,inputs._canonical(data))


@pytest.mark.parametrize('key',[INPUT_KEY,b'',b'x'*31,b'x'*4097,'not-bytes'])
def test_result_key_is_bounded_and_separate_from_input_key(key):
    with pytest.raises(evidence.CalculationResultEvidenceHold):authority(key=key)


@pytest.mark.parametrize('declaration',['VERSION','DOMAIN','SCOPE','MAX_EVIDENCE_BYTES','CODE_SHA256','DEPENDENCY_SHA256'])
def test_runtime_declarations_are_pinned(tmp_path,monkeypatch,declaration):
    args,_,_=case(tmp_path);server=authority();raw=server.issue(*args)
    value=1 if declaration=='MAX_EVIDENCE_BYTES' else {} if declaration=='DEPENDENCY_SHA256' else 'changed'
    monkeypatch.setattr(evidence,declaration,value)
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*args,raw)
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.issue(*args)


def test_previous_proof_version_and_authority_remain_separate(tmp_path):
    from app import crop_cycle_result_evidence as old
    from test_crop_cycle_result_evidence import case as old_case,authority as old_authority
    old_path=tmp_path/'old';old_path.mkdir()
    old_args,_,_=old_case(old_path);old_raw=old_authority().issue(*old_args)
    args,_,_=case(tmp_path);server=authority();raw=server.issue(*args)
    with pytest.raises(evidence.CalculationResultEvidenceHold):server.verify(*old_args,old_raw)
    with pytest.raises(old.ResultEvidenceHold):old_authority().verify(*args,raw)
    assert old_authority().verify(*old_args,old_raw).summary['status']=='completed'
    with pytest.raises(evidence.CalculationResultEvidenceHold):
        evidence.CalculationResultEvidenceAuthority(old_authority(),integrity_key=KEY,issuer_id='owned',key_id='owned')


@pytest.mark.parametrize('operation',['issue','verify'])
@pytest.mark.parametrize('kind',['result-inode','input-bytes','source'])
def test_changes_during_snapshot_never_return_stale_facts(tmp_path,monkeypatch,operation,kind):
    import shutil
    args,_,_=case(tmp_path);server=authority();raw=server.issue(*args);original=evidence._snapshot
    changed=False
    def scan(*a,**k):
        nonlocal changed
        snapshot=original(*a,**k)
        if not changed:
            changed=True
            if kind=='result-inode':
                args[0].rename(tmp_path/'old-result');shutil.copytree(tmp_path/'old-result',args[0])
            elif kind=='input-bytes':
                path=args[2]/'root.json';path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
            else:
                path=tmp_path/'changed.py';path.write_text('owned changed source')
                monkeypatch.setattr(engine,'__file__',str(path))
        return snapshot
    monkeypatch.setattr(evidence,'_snapshot',scan)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):
        server.issue(*args) if operation=='issue' else server.verify(*args,raw)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('operation',['issue','verify'])
def test_valid_hash_orphan_is_not_adopted_as_verified_result(tmp_path,operation):
    args,_,_=case(tmp_path);server=authority();raw=server.issue(*args)
    orphan=b'{}';path=args[0]/(sha256(orphan).hexdigest()+'.json')
    path.write_bytes(orphan);path.chmod(0o400)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.CalculationResultEvidenceHold):
        server.issue(*args) if operation=='issue' else server.verify(*args,raw)
    assert len(os.listdir('/proc/self/fd'))==before
