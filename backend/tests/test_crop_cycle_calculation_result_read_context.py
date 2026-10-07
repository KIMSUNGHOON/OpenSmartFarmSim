from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app import crop_cycle_calculation_result_read_context as query
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_calculation_context as engine
from test_crop_cycle_calculation_result_evidence import case, authority
from test_crop_cycle_artifact import PROFILES, NOTICE


def prepared(tmp_path, name='empty-entry', held=False):
    args, summary, index=case(tmp_path,name,held)
    server=authority();raw=server.issue(*args)
    pages={}
    with engine.open_calculation_context(args[2],args[3],args[4],authority=server.input_authority) as context:
        with artifact.open_artifact(args[0],args[1],context,notice_raw=NOTICE) as reader:
            for kind in ('samples','events'):
                pages[kind]=[reader.page(kind,start,limit) for limit in (1,2,8)
                    for start in range(summary['counts'][kind]+1)]
    return args+(raw,),server,summary,index,pages


def open_query(args,server):
    return query.open_calculation_result_read_context(*args,authority=server)


@pytest.mark.parametrize('name',['empty-entry','full-removal-reentry','positive-tail'])
def test_original_pages_UTC_counts_and_math_manifest_without_parser_or_RHS(tmp_path,monkeypatch,name):
    args,server,summary,index,pages=prepared(tmp_path,name)
    def forbidden(*a,**k):pytest.fail('query repeated original parsing or RHS')
    for module,name in ((artifact,'open_artifact'),(inputs,'open_input_packet'),(engine.legacy,'prepare_context'),(engine,'open_calculation_context'),(artifact._Files,'_load_prefix'),(artifact,'_validate_delta'),(engine,'advance_chunk'),(engine.short._Evaluator,'rhs')):
        monkeypatch.setattr(module,name,forbidden)
    before=len(os.listdir('/proc/self/fd'))
    with open_query(args,server) as reader:
        assert type(reader) is query.CalculationResultReadContext and not isinstance(reader,artifact.ArtifactReader)
        assert reader.summary==summary and reader.manifest==summary['manifest']
        assert reader.context_record['manifest']==summary['manifest']
        assert reader.identity['read_context_version']==query.VERSION
        assert reader.identity['math_context_sha256']==engine._hash(summary['manifest'])
        assert reader.identity['evidence_sha256']==sha256(args[-1]).hexdigest()
        assert reader.rights_or_gate_approval is False
        for kind,expected in pages.items():
            for page in expected:
                limit=1 if len(page['records'])<=1 else len(page['records'])
                assert reader.page(kind,page['start'],limit)==page
        reader.recheck()
        assert len(reader._cache)<=2
    assert reader.closed and reader._cache=={} and len(os.listdir('/proc/self/fd'))==before


def test_numeric_hold_and_confirmed_past_are_identical(tmp_path):
    args,server,summary,index,pages=prepared(tmp_path,held=True)
    with open_query(args,server) as reader:
        assert summary['status']=='hold' and reader.summary==summary
        for kind in ('samples','events'):
            for start in range(summary['counts'][kind]+1):
                assert reader.page(kind,start,1)==pages[kind][start]


def test_actual_small_byte_budget_preserves_records_progress_and_exact_boundary(tmp_path):
    args,server,summary,index,pages=prepared(tmp_path,'positive-tail')
    with open_query(args,server) as reader:
        original=reader.page('samples',0,2)
        assert len(original['records'])==2
        first={**original,'next':1,'records':original['records'][:1]}
        cap=len(artifact._canonical(first))
        short=reader.page('samples',0,2,max_bytes=cap)
        assert short==first and len(artifact._canonical(short))==cap
        following=reader.page('samples',short['next'],1)
        assert following['records']==original['records'][1:]
    with open_query(args,server) as reader:
        with pytest.raises(query.CalculationResultReadContextHold):reader.page('samples',0,2,max_bytes=cap-1)
        assert reader.closed


@pytest.mark.parametrize('values',[
    ('other',0,1,2097152),('samples',-1,1,2097152),('samples',True,1,2097152),
    ('samples',999,1,2097152),('samples',0,0,2097152),('samples',0,65,2097152),
    ('events',0,9,2097152),('events',0,True,2097152),('samples',0,1,0),
    ('samples',0,1,2097153),('samples',0,1,True)])
def test_bad_queries_close_without_publishing(tmp_path,values):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server)
    with pytest.raises(query.CalculationResultReadContextHold):reader.page(*values[:3],max_bytes=values[3])
    assert reader.closed and len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['blob','input','HEAD','writable','hardlink','symlink','replacement','mode'])
def test_cached_page_never_masks_current_physical_change(tmp_path,change):
    args,server,_,index,_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server);reader.page('samples',0,1)
    target=args[0]/(index['samples'][0]['sha256']+'.json')
    if change=='input':target=args[2]/'root.json'
    if change=='HEAD':target=args[0]/'HEAD'
    if change in ('blob','input','HEAD'):
        raw=target.read_bytes();target.chmod(0o600);target.write_bytes(raw+b' ');target.chmod(0o400)
    elif change=='writable':target.chmod(0o600)
    elif change=='hardlink':os.link(target,tmp_path/'other-link')
    elif change=='symlink':
        moved=tmp_path/'moved';target.rename(moved);target.symlink_to(moved)
    elif change=='replacement':
        args[0].rename(tmp_path/'old-result');shutil.copytree(tmp_path/'old-result',args[0])
    else:args[0].chmod(0o755)
    with pytest.raises(query.CalculationResultReadContextHold):reader.page('samples',0,1)
    assert reader.closed and reader._cache=={} and len(os.listdir('/proc/self/fd'))==before


def test_change_after_actual_page_read_is_rejected_before_return(tmp_path,monkeypatch):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server);original=reader._load
    def changed(*a,**k):
        value=original(*a,**k);path=args[2]/'root.json'
        path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
        return value
    monkeypatch.setattr(reader,'_load',changed)
    with pytest.raises(query.CalculationResultReadContextHold):reader.page('samples',0,1)
    assert reader.closed and len(os.listdir('/proc/self/fd'))==before


def test_caller_mutations_do_not_change_cached_facts_or_rows(tmp_path):
    args,server,summary,_,_=prepared(tmp_path)
    with open_query(args,server) as reader:
        expected=reader.page('samples',0,1);copy=reader.page('samples',0,1)
        copy['records'][0]['at']='changed'
        facts=reader.summary;facts['counts']['samples']=999
        context=reader.context_record;context['seed'][0]+=1
        identity=reader.identity;identity['scope']='changed'
        assert reader.page('samples',0,1)==expected and reader.summary==summary
        assert reader.context_record!=context and reader.identity!=identity


@pytest.mark.parametrize('change',['input','result','authority'])
def test_summary_never_publishes_cached_facts_after_current_change(tmp_path,change):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server)
    if change=='authority':server.key_id='rotated-key'
    else:
        path=args[2]/'root.json' if change=='input' else args[0]/'HEAD'
        path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
    with pytest.raises(query.CalculationResultReadContextHold):_ = reader.summary
    assert reader.closed and len(os.listdir('/proc/self/fd'))==before


def test_original_calculation_engine_rejects_this_query_type(tmp_path):
    args,server,*_=prepared(tmp_path)
    with open_query(args,server) as reader:
        with pytest.raises(ValueError):engine.start(reader)


def test_context_entry_failure_closes_an_already_open_descriptor(tmp_path,monkeypatch):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server)
    changed=tmp_path/'changed.py';changed.write_text('own source changed before entry')
    monkeypatch.setattr(query,'__file__',str(changed))
    with pytest.raises(query.CalculationResultReadContextHold):reader.__enter__()
    try:
        assert reader.closed and len(os.listdir('/proc/self/fd'))==before
    finally:
        reader.close()


@pytest.mark.parametrize('which',['proof','authority','source','closed'])
def test_proof_authority_code_and_closed_state_fail_with_FD_cleanup(tmp_path,monkeypatch,which):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    if which=='proof':
        with pytest.raises(query.CalculationResultReadContextHold):open_query(args[:-1]+(b'{}',),server)
    elif which=='authority':
        with pytest.raises(query.CalculationResultReadContextHold):open_query(args,object())
    else:
        reader=open_query(args,server)
        if which=='closed':reader.close();reader.close()
        else:
            other=tmp_path/'changed.py';other.write_text('own changed result query')
            monkeypatch.setattr(query,'__file__',str(other))
        with pytest.raises(query.CalculationResultReadContextHold):reader.page('samples')
        assert reader.closed
    assert len(os.listdir('/proc/self/fd'))==before


def test_separate_python_preserves_exact_first_page_and_closes(tmp_path):
    args,server,*_=prepared(tmp_path,'positive-tail')
    with open_query(args,server) as reader:expected=reader.page('samples',0,2)
    (tmp_path/'input-proof').write_bytes(args[4]);(tmp_path/'result-proof').write_bytes(args[5])
    code='''
from pathlib import Path
import os,sys,json
from test_crop_cycle_calculation_result_evidence import authority
from app.crop_cycle_calculation_result_read_context import open_calculation_result_read_context
from app import crop_cycle_calculation_result_evidence as evidence
def forbidden(*a,**k):raise AssertionError('fresh reader ran parser/context/QC/RHS')
for owner,name in ((evidence.inputs,'open_input_packet'),(evidence.calculation,'open_calculation_context'),
    (evidence.calculation.legacy,'prepare_context'),(evidence.artifact,'open_artifact'),
    (evidence.artifact._Files,'_load_prefix'),(evidence.artifact,'_validate_delta'),
    (evidence.calculation,'advance_chunk'),(evidence.calculation.short._Evaluator,'rhs')):
    setattr(owner,name,forbidden)
before=len(os.listdir('/proc/self/fd'))
with open_calculation_result_read_context(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]),sys.argv[4],Path(sys.argv[5]).read_bytes(),Path(sys.argv[6]).read_bytes(),authority=authority()) as reader:
    page=reader.page('samples',0,2)
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps(page,sort_keys=True))
'''
    env=dict(os.environ,PYTHONPATH=str(Path.cwd())+os.pathsep+str(Path.cwd()/'tests'))
    child=subprocess.run([sys.executable,'-c',code,*map(str,args[:4]),str(tmp_path/'input-proof'),str(tmp_path/'result-proof')],
        env=env,capture_output=True,timeout=30)
    assert child.returncode==0,(child.stdout+child.stderr).decode(errors='replace')
    assert json.loads(child.stdout)==expected


def test_current_HEAD_change_before_context_entry_closes_without_returning_handle(tmp_path):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server);path=args[0]/'HEAD'
    path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
    try:
        with pytest.raises(query.CalculationResultReadContextHold):reader.__enter__()
        assert reader.closed and not reader._cache
    finally:reader.close()
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('field',['VERSION','CODE_SHA256','DEPENDENCY_SHA256','MAX_PAGE_BYTES'])
def test_current_runtime_declarations_cannot_change_replay_identity_or_limits(tmp_path,monkeypatch,field):
    args,server,*_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server)
    monkeypatch.setattr(query,field,1 if field=='MAX_PAGE_BYTES' else {} if field=='DEPENDENCY_SHA256' else 'changed')
    try:
        with pytest.raises(query.CalculationResultReadContextHold):_ = reader.identity
        assert reader.closed and not reader._cache
    finally:reader.close()
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('fact',['summary','context_record','identity'])
def test_copied_fact_is_not_returned_after_input_change_during_decode(tmp_path,monkeypatch,fact):
    args,server,*_=prepared(tmp_path);reader=open_query(args,server)
    before=len(os.listdir('/proc/self/fd'))-1
    target=getattr(reader,{'summary':'_summary_raw','context_record':'_context_raw','identity':'_identity_raw'}[fact])
    original=inputs._json;changed=False
    def decode(raw):
        nonlocal changed
        value=original(raw)
        if raw==target and not changed:
            changed=True;path=args[2]/'root.json'
            path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
        return value
    monkeypatch.setattr(inputs,'_json',decode)
    with pytest.raises(query.CalculationResultReadContextHold):getattr(reader,fact)
    assert changed and reader.closed and not reader._cache
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['HEAD','page','source','authority'])
def test_current_changes_after_page_copy_close_before_return(tmp_path,monkeypatch,change):
    args,server,_,index,_=prepared(tmp_path);before=len(os.listdir('/proc/self/fd'))
    reader=open_query(args,server);original=reader._load
    def load(*a,**k):
        values=original(*a,**k)
        if change=='authority':server.key_id='changed'
        elif change=='source':
            path=tmp_path/'changed.py';path.write_text('own changed reader dependency')
            monkeypatch.setattr(query.evidence,'__file__',str(path))
        else:
            path=args[0]/('HEAD' if change=='HEAD' else index['samples'][0]['sha256']+'.json')
            path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
        return values
    monkeypatch.setattr(reader,'_load',load)
    with pytest.raises(query.CalculationResultReadContextHold):reader.page('samples',0,1)
    assert reader.closed and not reader._cache and len(os.listdir('/proc/self/fd'))==before


def test_old_read_authority_and_result_proof_do_not_enter_new_replay(tmp_path):
    from test_crop_cycle_result_evidence import case as old_case,authority as old_authority
    old_path=tmp_path/'old';old_path.mkdir();old_args,_,_=old_case(old_path);old_server=old_authority()
    old_raw=old_server.issue(*old_args)
    with pytest.raises(query.CalculationResultReadContextHold):open_query(old_args+(old_raw,),old_server)
    with pytest.raises(query.CalculationResultReadContextHold):open_query(old_args+(old_raw,),authority())
